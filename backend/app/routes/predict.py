import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from ..models.schemas import PredictRequest, PredictResponse, Remediation, RecipeAdjustment, StullCoordinates, NeighbourInfo, OptimizerCandidate, GlazeMetrics
from ..engine.pipeline import compute_physics, search_neighbours, evaluate_recipe
from ..engine.umf import convert_recipe_to_umf
from ..models.xgb_predictor import xgb_predictor
from ..agent.core import get_agent
from ..optimizer.pareto import optimize
from ..render.sdxl import generate_glaze_image
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["predict"])


def _evaluate_candidate(candidate: list[dict]) -> dict:
    try:
        result = evaluate_recipe(candidate)
        return {
            "cte": result["cte"],
            "stress_delta": result["stress_delta"],
            "surface_class": result["surface_class"],
            "surface_confidence": result["surface_confidence"],
        }
    except Exception:
        return {"cte": 0.0, "stress_delta": 0.0, "surface_class": "unknown", "surface_confidence": 0.0}


@router.post("/predict-glaze", response_model=PredictResponse)
async def predict_glaze(request: PredictRequest):
    try:
        recipe_dicts = [{"material": i.material, "percentage": i.percentage} for i in request.recipe]
        umf = convert_recipe_to_umf(recipe_dicts)
        umf_dict = umf.model_dump()

        cone_min = float(request.target_cone)
        cone_max = float(request.target_cone)
        atmosphere = request.atmosphere

        physics_engine = compute_physics(umf_dict)
        neighbours = search_neighbours(umf_dict)

        ml_pred = xgb_predictor.predict(umf_dict, cone_min, cone_max, atmosphere)

        gnn_inference = {
            "surface_class": ml_pred["surface_class"],
            "surface_confidence": ml_pred["surface_confidence"],
            "transparency_class": ml_pred["transparency_class"],
            "transparency_confidence": ml_pred["transparency_confidence"],
            "color_family": ml_pred["color_family_class"],
            "color_confidence": ml_pred["color_family_confidence"],
        }

        try:
            candidates = optimize(
                recipe=recipe_dicts,
                eval_fn=_evaluate_candidate,
                target_surface=gnn_inference["surface_class"],
                target_cte_max=settings.target_cte_stoneware,
                max_candidates=3,
            )
            candidate_objects = [OptimizerCandidate(**c) for c in candidates]
        except Exception:
            candidate_objects = []

        try:
            agent = get_agent()
            remediation_data = agent.remediate_with_verification(
                umf=umf_dict,
                physics_engine=physics_engine,
                gnn_inference=gnn_inference,
                nearest_neighbours=neighbours,
                original_recipe=recipe_dicts,
                optimizer_candidates=candidates if candidate_objects else None,
                cone_min=cone_min,
                cone_max=cone_max,
                atmosphere=atmosphere,
            )
            remediation = Remediation(
                chemical_analysis=remediation_data.get("chemical_analysis", ""),
                recipe_adjustments=[
                    RecipeAdjustment(**adj) for adj in remediation_data.get("recipe_adjustments", [])
                ],
                expected_new_cte=remediation_data.get("expected_new_cte", 0.0),
                verification_summary=remediation_data.get("verification_summary", ""),
            )
        except Exception as e:
            logger.warning("Agent remediation failed: %s", e)
            remediation = Remediation(
                chemical_analysis=(
                    f"This glaze has a Si:Al ratio of {umf_dict.get('calculated_ratios', {}).get('silica_alumina_ratio', 'unknown')} "
                    f"and predicted {gnn_inference['surface_class']} surface. "
                    f"CTE stress delta: {physics_engine.get('stress_delta', 0):.2e}. "
                    f"To adjust, consider modifying flux ratios or silica content."
                ),
                recipe_adjustments=[],
                expected_new_cte=0.0,
                verification_summary="",
            )

        cte = physics_engine["cte"]
        crazing_risk = physics_engine["crazing_risk"]

        neighbour_objects = [NeighbourInfo(**n) for n in neighbours]

        return PredictResponse(
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics=GlazeMetrics(
                original_cte=cte,
                target_cte_max=settings.target_cte_stoneware,
                crazing_risk=crazing_risk,
                finish=gnn_inference["surface_class"],
                transparency=gnn_inference["transparency_class"],
                color_family=gnn_inference["color_family"],
            ),
            stull_coordinates=StullCoordinates(**physics_engine["stull_coordinates"]),
            remediation=remediation,
            render_output_url="",
            nearest_neighbours=neighbour_objects,
            optimizer_candidates=candidate_objects,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


class GenerateImageRequest(BaseModel):
    surface: str
    transparency: str
    color_family: str
    recipe: list[dict]


class GenerateImageResponse(BaseModel):
    image_url: str
    success: bool


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(req: GenerateImageRequest):
    try:
        image_url = await generate_glaze_image(
            surface=req.surface,
            transparency=req.transparency,
            color_family=req.color_family,
            recipe=req.recipe,
        )
        if image_url:
            return GenerateImageResponse(image_url=image_url, success=True)
        return GenerateImageResponse(image_url="", success=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
