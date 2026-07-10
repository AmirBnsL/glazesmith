"""Agent tools for evaluating recipe adjustments.

Wraps the pipeline (UMF -> CTE -> XGBoost -> K-NN) so the LLM
can verify its own recipe suggestions through the real engine.
"""

from __future__ import annotations
from ..engine.pipeline import evaluate_recipe


def apply_adjustment(recipe: list[dict], adjustment: dict) -> list[dict] | None:
    """Apply a single LLM-proposed adjustment to the recipe.

    Returns the modified recipe (normalized to 100%), or None if the
    adjustment cannot be applied (e.g. unknown material to introduce).
    """
    mat_name = adjustment["material"]
    delta = adjustment["delta_percentage"]
    action = adjustment["action"]

    candidate = [dict(item) for item in recipe]

    if action == "increase":
        found = False
        for item in candidate:
            if item["material"].lower() == mat_name.lower():
                item["percentage"] = max(0.0, min(100.0, item["percentage"] + delta))
                found = True
                break
        if not found:
            return None

    elif action == "decrease":
        found = False
        for item in candidate:
            if item["material"].lower() == mat_name.lower():
                item["percentage"] = max(0.0, item["percentage"] - delta)
                found = True
                break
        if not found:
            return None

    elif action == "introduce":
        candidate.append({"material": mat_name, "percentage": delta})

    elif action == "remove":
        candidate = [item for item in candidate if item["material"].lower() != mat_name.lower()]

    else:
        return None

    return _normalize(candidate)


def _normalize(recipe: list[dict]) -> list[dict] | None:
    """Normalize recipe percentages to sum to 100."""
    if not recipe:
        return None
    total = sum(item["percentage"] for item in recipe)
    if abs(total - 100.0) < 0.01:
        return recipe
    if total <= 0:
        return None
    for item in recipe:
        item["percentage"] = round(item["percentage"] / total * 100, 1)
    return recipe


def verify_adjustment(recipe: list[dict], adjustment: dict, cone_min: float = 6.0, cone_max: float = 6.0, atmosphere: str = "oxidation") -> dict | None:
    """Apply an adjustment, run through the full pipeline, return verified metrics.

    Returns dict with verified results, or None if the adjustment is invalid.
    """
    modified = apply_adjustment(recipe, adjustment)
    if modified is None:
        return None

    try:
        result = evaluate_recipe(modified, cone_min, cone_max, atmosphere)
        return {
            "modified_recipe": modified,
            "verified_cte": result["cte"],
            "verified_stress_delta": result["stress_delta"],
            "verified_crazing_risk": result["crazing_risk"],
            "verified_surface": result["surface_class"],
            "verified_surface_confidence": result["surface_confidence"],
            "verified_transparency": result["transparency_class"],
            "verified_color": result["color_family"],
            "neighbours": result["neighbours"],
        }
    except Exception:
        return None
