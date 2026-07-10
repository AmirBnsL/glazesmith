"""Shared pipeline logic for glaze evaluation.

Extracts CTE computation, neighbour search, and recipe evaluation
out of predict.py so both routes and agent/tools can use them.
"""

from __future__ import annotations
from ..engine.stull import calculate_stull
from ..retrieval.knn import GlazyIndex
from ..config import settings
from .umf import convert_recipe_to_umf

_glazy_index: GlazyIndex | None = None


def _get_index() -> GlazyIndex:
    global _glazy_index
    if _glazy_index is None:
        _glazy_index = GlazyIndex()
        _glazy_index.load()
    return _glazy_index


def compute_physics(umf_dict: dict) -> dict:
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

    if stress_delta > 0:
        crazing_risk = min(stress_delta / (2 * target), 1.0)
    else:
        crazing_risk = 0.0

    stull = calculate_stull(sio2, al2o3)

    return {
        "cte": cte,
        "stress_delta": stress_delta,
        "crazing_risk": crazing_risk,
        "stull_coordinates": stull.model_dump(),
    }


def search_neighbours(umf_dict: dict, k: int = 10) -> list[dict]:
    try:
        idx = _get_index()
        umf_flat = {}
        groups = umf_dict.get("unity_molecular_formula", {})
        for g in ("fluxes", "stabilizers", "formers", "others"):
            umf_flat.update(groups.get(g, {}))
        vector = idx.umf_dict_to_vector(umf_flat)
        return idx.search(vector, k=k)
    except Exception:
        return []


def evaluate_recipe(recipe: list[dict], cone_min: float = 6.0, cone_max: float = 6.0, atmosphere: str = "oxidation") -> dict:
    umf = convert_recipe_to_umf(recipe)
    umf_dict = umf.model_dump()

    physics = compute_physics(umf_dict)
    neighbours = search_neighbours(umf_dict)

    from ..models.xgb_predictor import xgb_predictor
    ml_pred = xgb_predictor.predict(umf_dict, cone_min, cone_max, atmosphere)

    return {
        "umf": umf_dict,
        "cte": physics["cte"],
        "stress_delta": physics["stress_delta"],
        "crazing_risk": physics["crazing_risk"],
        "stull_coordinates": physics["stull_coordinates"],
        "surface_class": ml_pred["surface_class"],
        "surface_confidence": ml_pred["surface_confidence"],
        "transparency_class": ml_pred["transparency_class"],
        "transparency_confidence": ml_pred["transparency_confidence"],
        "color_family": ml_pred.get("color_family_class", "unknown"),
        "color_confidence": ml_pred.get("color_family_confidence", 0),
        "neighbours": neighbours[:5],
    }
