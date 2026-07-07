from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from ..models.schemas import PredictRequest, PredictResponse, Remediation, RecipeAdjustment, StullCoordinates
from ..engine.umf import convert_recipe_to_umf
from ..engine.stull import calculate_stull
from ..agent.core import agent
from ..render.sdxl import renderer
from ..config import settings

router = APIRouter(prefix="/api", tags=["predict"])


def _mock_gnn_predict(umf_dict: dict) -> dict:
    """Mock GNN predictions until Teammate 2's model is ready."""
    sio2 = umf_dict.get("unity_molecular_formula", {}).get("formers", {}).get("SiO2", 2.0)
    al2o3 = umf_dict.get("unity_molecular_formula", {}).get("stabilizers", {}).get("Al2O3", 0.3)
    na2o = umf_dict.get("unity_molecular_formula", {}).get("fluxes", {}).get("Na2O", 0.2)
    k2o = umf_dict.get("unity_molecular_formula", {}).get("fluxes", {}).get("K2O", 0.1)

    cte = 5.0 + (na2o * 8.0) + (k2o * 6.0) - (sio2 * 0.5)
    crazing = min(max((cte - 6.0) / 3.0, 0.0), 1.0)

    si_al_ratio = sio2 / max(al2o3, 0.01)
    if si_al_ratio > 8:
        surface = "glossy"
    elif si_al_ratio > 5:
        surface = "satin"
    else:
        surface = "matte"

    return {
        "coefficient_of_thermal_expansion": round(cte * 1e-6, 10),
        "crazing_risk_probability": round(crazing, 3),
        "surface_finish_logits": [0.7, 0.15, 0.1, 0.05],
        "predicted_surface_class": surface,
        "transparency_class": "transparent_clear",
    }


@router.post("/predict-glaze", response_model=PredictResponse)
async def predict_glaze(request: PredictRequest):
    try:
        recipe_dicts = [{"material": i.material, "percentage": i.percentage} for i in request.recipe]
        umf = convert_recipe_to_umf(recipe_dicts)
        umf_dict = umf.model_dump()

        gnn_raw = _mock_gnn_predict(umf_dict)

        stull = calculate_stull(
            umf.unity_molecular_formula.formers.get("SiO2", 0),
            umf.unity_molecular_formula.stabilizers.get("Al2O3", 0),
        )

        remediation_data = agent.analyze_and_remediate(umf_dict, gnn_raw)
        remediation = Remediation(
            chemical_analysis=remediation_data.get("chemical_analysis", ""),
            recipe_adjustments=[
                RecipeAdjustment(**adj) for adj in remediation_data.get("recipe_adjustments", [])
            ],
            expected_new_cte=remediation_data.get("expected_new_cte", 0.0),
        )

        render_url = renderer.generate(gnn_raw)

        cte = gnn_raw["coefficient_of_thermal_expansion"]

        return PredictResponse(
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics={
                "original_cte": cte,
                "target_cte_max": settings.target_cte_stoneware,
                "crazing_risk": gnn_raw["crazing_risk_probability"],
                "finish": gnn_raw["predicted_surface_class"],
            },
            stull_coordinates=stull,
            remediation=remediation,
            render_output_url=render_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
