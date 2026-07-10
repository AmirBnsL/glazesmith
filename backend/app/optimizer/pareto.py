"""Constrained Grid Search Pareto Optimizer (Layer 3).

Identifies alternative formulations that balance low CTE-induced stress
against target surface finish confidence, using a constrained grid search
over the top N primary variable inputs.

Target: <200ms total for sequential evaluation across all grid points.
"""

from __future__ import annotations
from typing import Callable
from itertools import product

DEFAULT_STEPS = [-15, -10, -5, 0, 5, 10, 15]


def _identify_top_variables(recipe: list[dict], n_vars: int = 3) -> list[int]:
    """Return indices of ingredients to vary — at most n_vars, and at most N-1.

    Leaves at least one ingredient as a filler so the sum can be normalized to 100.
    Filters out ingredients with 0% to avoid empty grids.
    """
    n_ingredients = len(recipe)
    if n_ingredients == 0:
        return []
    n = min(n_vars, max(1, n_ingredients - 1))
    indexed = [(i, item["percentage"]) for i, item in enumerate(recipe) if item["percentage"] > 0]
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in indexed[:n]]


def _apply_change(pct: float, step: int) -> float:
    """Apply a relative step change to a percentage, clamped to [0, 100]."""
    return max(0.0, min(100.0, pct + pct * step / 100.0))


def _normalize_total(recipe: list[dict], var_indices: list[int], var_values: list[float]) -> list[dict]:
    """Build a candidate recipe by setting variable ingredients and scaling others to sum to 100."""
    candidate = [dict(item) for item in recipe]

    for idx, val in zip(var_indices, var_values):
        candidate[idx]["percentage"] = round(val, 1)

    current_total = sum(item["percentage"] for item in candidate)

    if abs(current_total - 100.0) < 0.01:
        return candidate

    non_var_indices = [i for i in range(len(candidate)) if i not in var_indices]
    non_var_current = sum(candidate[i]["percentage"] for i in non_var_indices)
    non_var_target = 100.0 - sum(var_values)

    if non_var_current > 0 and non_var_target > 0:
        scale = non_var_target / non_var_current
        for i in non_var_indices:
            candidate[i]["percentage"] = round(candidate[i]["percentage"] * scale, 1)
    elif non_var_target <= 0:
        for i in non_var_indices:
            candidate[i]["percentage"] = 0.0

    return candidate


def _compute_score(
    stress_delta: float,
    surface_class: str,
    surface_confidence: float,
    target_surface: str,
    target_cte_max: float,
    surface_weight: float = 1.0,
    stress_weight: float = 1.0,
) -> float:
    """Combined score: reward surface match, penalize crazing stress."""
    crazing_penalty = max(0, stress_delta) / max(target_cte_max, 1e-10)
    surface_match = 1.0 if surface_class == target_surface else 0.0
    return surface_weight * surface_match * surface_confidence - stress_weight * crazing_penalty


def _recipe_signature(recipe: list[dict]) -> str:
    """Create a unique string key for a recipe to deduplicate candidates."""
    return "|".join(f"{i['material']}:{i['percentage']:.1f}" for i in recipe)


def optimize(
    recipe: list[dict],
    eval_fn: Callable[[list[dict]], dict],
    target_surface: str = "glossy",
    target_cte_max: float = 7.30e-6,
    n_vars: int = 3,
    steps: list[int] | None = None,
    max_candidates: int = 3,
    surface_weight: float = 1.0,
    stress_weight: float = 1.0,
) -> list[dict]:
    """Run constrained grid search over top N primary variable inputs.

    Args:
        recipe: Input recipe as [{material, percentage}, ...].
        eval_fn: Evaluation function returning {"cte": float, "stress_delta": float,
                  "surface_class": str, "surface_confidence": float}.
        target_surface: Desired surface finish to optimize for.
        target_cte_max: Maximum CTE before crazing risk.
        n_vars: Number of ingredients to vary (default 3).
        steps: Relative percentage steps to search (default +-5/10/15).
        max_candidates: Number of candidates to return (default 3).
        surface_weight: Score weight for hitting target surface.
        stress_weight: Score weight for minimizing crazing stress.

    Returns:
        Top N candidate recipes with metrics, sorted by score descending.
    """
    steps = steps or DEFAULT_STEPS
    var_indices = _identify_top_variables(recipe, n_vars)

    if not var_indices:
        return []

    grids = []
    for recipe_idx in var_indices:
        base_pct = recipe[recipe_idx]["percentage"]
        if base_pct <= 0:
            continue
        grid = [_apply_change(base_pct, s) for s in steps]
        grid = sorted(set(round(g, 1) for g in grid if g > 0))
        if grid:
            grids.append(grid)

    if not grids:
        return []

    seen: set[str] = set()
    scored: list[dict] = []

    original_sig = _recipe_signature(recipe)

    for trial_values in product(*grids):
        candidate = _normalize_total(recipe, var_indices, list(trial_values))
        sig = _recipe_signature(candidate)

        if sig in seen:
            continue
        seen.add(sig)

        if sig == original_sig:
            continue

        try:
            result = eval_fn(candidate)
        except Exception:
            continue

        stress_delta = result.get("stress_delta", 0)
        surface_class = result.get("surface_class", "unknown")
        surface_confidence = result.get("surface_confidence", 0)

        score = _compute_score(
            stress_delta,
            surface_class,
            surface_confidence,
            target_surface,
            target_cte_max,
            surface_weight,
            stress_weight,
        )

        scored.append({
            "recipe": candidate,
            "stress_delta": stress_delta,
            "surface_class": surface_class,
            "surface_confidence": surface_confidence,
            "score": round(score, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_candidates]
