from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from ..models.schemas import PredictRequest, PredictResponse, Remediation, RecipeAdjustment, StullCoordinates
from ..engine.umf import convert_recipe_to_umf
from ..engine.stull import calculate_stull
from ..agent.core import agent
from ..render.sdxl import renderer
from ..retrieval.knn import GlazyIndex
from ..config import settings

router = APIRouter(prefix="/api", tags=["predict"])


def _compute_physics_engine(umf_dict: dict) -> dict:
    fluxes = umf_dict.get("unity_molecular_formula", {}).get("fluxes", {})
    stabilizers = umf_dict.get("unity_molecular_formula", {}).get("stabilizers", {})
    formers = umf_dict.get("unity_molecular_formula", {}).get("formers", {})

    sio2 = formers.get("SiO2", 2.0)
    al2o3 = stabilizers.get("Al2O3", 0.3)
    na2o = fluxes.get("Na2O", 0.0)
    k2o = fluxes.get("K2O", 0.0)
    cao = fluxes.get("CaO", 0.0)
    mgo = fluxes.get("MgO", 0.0)

    cte = 5.0 + (na2o * 8.0) + (k2o * 6.0) + (cao * 4.0) + (mgo * 2.0) - (sio2 * 0.5) + (al2o3 * 0.3)
    cte = round(cte * 1e-6, 10)

    target = settings.target_cte_stoneware
    stress_delta = round(cte - target, 12)

    if stress_delta > 1.0e-6:
        risk_tier = "Extreme"
    elif stress_delta > 0.5e-6:
        risk_tier = "High"
    elif stress_delta > 0:
        risk_tier = "Moderate"
    else:
        risk_tier = "Low"

    stull = calculate_stull(sio2, al2o3)

    return {
        "cte": cte,
        "stress_delta": stress_delta,
        "crazing_risk_tier": risk_tier,
        "stull_coordinates": stull.model_dump(),
    }


def _mock_gnn_inference(umf_dict: dict) -> dict:
    sio2 = umf_dict.get("unity_molecular_formula", {}).get("formers", {}).get("SiO2", 2.0)
    al2o3 = umf_dict.get("unity_molecular_formula", {}).get("stabilizers", {}).get("Al2O3", 0.3)

    si_al_ratio = sio2 / max(al2o3, 0.01)
    if si_al_ratio > 8:
        surface_class = "glossy"
        surface_confidence = 0.85
    elif si_al_ratio > 5:
        surface_class = "satin"
        surface_confidence = 0.70
    else:
        surface_class = "matte"
        surface_confidence = 0.75

    return {
        "surface_class": surface_class,
        "surface_confidence": surface_confidence,
        "transparency_class": "transparent_clear",
        "transparency_confidence": 0.60,
        "color_family": "unknown",
        "color_confidence": 0.50,
    }


def _search_neighbours(umf_dict: dict) -> list[dict]:
    try:
        idx = GlazyIndex()
        umf_flat = {}
        groups = umf_dict.get("unity_molecular_formula", {})
        for g in ("fluxes", "stabilizers", "formers", "others"):
            umf_flat.update(groups.get(g, {}))
        umf_flat.update(umf_dict.get("calculated_ratios", {}))
        vector = idx.umf_dict_to_vector(umf_flat)
        return idx.search(vector, k=5)
    except Exception:
        return []


@router.post("/predict-glaze", response_model=PredictResponse)
async def predict_glaze(request: PredictRequest):
    try:
        recipe_dicts = [{"material": i.material, "percentage": i.percentage} for i in request.recipe]
        umf = convert_recipe_to_umf(recipe_dicts)
        umf_dict = umf.model_dump()

        physics_engine = _compute_physics_engine(umf_dict)
        gnn_inference = _mock_gnn_inference(umf_dict)
        neighbours = _search_neighbours(umf_dict)

        remediation_data = agent.analyze_and_remediate(umf_dict, physics_engine, gnn_inference, neighbours)
        remediation = Remediation(
            chemical_analysis=remediation_data.get("chemical_analysis", ""),
            recipe_adjustments=[
                RecipeAdjustment(**adj) for adj in remediation_data.get("recipe_adjustments", [])
            ],
            expected_new_cte=remediation_data.get("expected_new_cte", 0.0),
        )

        render_url = renderer.generate(gnn_inference)

        cte = physics_engine["cte"]
        risk_tier = physics_engine["crazing_risk_tier"]

        return PredictResponse(
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics={
                "original_cte": cte,
                "target_cte_max": settings.target_cte_stoneware,
                "crazing_risk": risk_tier,
                "finish": gnn_inference["surface_class"],
            },
            stull_coordinates=StullCoordinates(**physics_engine["stull_coordinates"]),
            remediation=remediation,
            render_output_url=render_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
