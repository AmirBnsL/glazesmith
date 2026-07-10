"""
Unity Molecular Formula (UMF) Engine.

Reads material compositions from data/materials.json.
Converts raw material mass percentages into a normalized Unity Molecular Formula
where total fluxes sum to 1.0.

Algorithm (matches glaze-chem and Glazy methodology):
  1. For each material, compute moles of each oxide: (wt_pct / molecular_weight)
  2. Scale by recipe parts: moles × (parts / 100)
  3. Sum all moles across all materials
  4. Normalize: divide all mole values by Σ(flux_oxide_moles) → Σflux = 1
"""

import json
import os
from ..models.schemas import UMFAnalysis, UnityMolecularFormula, CalculatedRatios

_MATERIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "materials.json")

_MATERIALS_CACHE: dict[str, dict] | None = None

MOLECULAR_WEIGHTS: dict[str, float] = {
    "SiO2": 60.085, "Al2O3": 101.961, "B2O3": 69.620, "TiO2": 79.866,
    "Li2O": 29.881, "Na2O": 61.979, "K2O": 94.196,
    "MgO": 40.304, "CaO": 56.077, "SrO": 103.619, "BaO": 153.326,
    "ZnO": 81.379, "PbO": 223.200,
    "Fe2O3": 159.688, "FeO": 71.844,
    "P2O5": 141.945, "ZrO2": 123.223,
    "CoO": 74.932, "CuO": 79.545, "Cu2O": 143.091,
    "MnO": 70.937, "MnO2": 86.937,
    "Cr2O3": 151.990, "SnO2": 150.710,
    "NiO": 74.693, "CdO": 128.410,
}

FLUX_OXIDES = {"Li2O", "Na2O", "K2O", "CaO", "MgO", "SrO", "BaO", "ZnO", "PbO"}
STABILIZER_OXIDES = {"Al2O3", "B2O3", "Fe2O3", "Cr2O3"}
FORMER_OXIDES = {"SiO2"}
OTHER_OXIDES = {"TiO2", "ZrO2", "SnO2", "P2O5", "MnO", "MnO2", "FeO", "CoO", "CuO", "Cu2O", "NiO", "CdO"}

UMF_OXIDES = [
    "SiO2", "Al2O3", "B2O3", "Li2O", "Na2O", "K2O", "MgO", "CaO",
    "SrO", "BaO", "ZnO", "TiO2", "Fe2O3", "P2O5", "SnO2", "Cr2O3",
    "ZrO2", "PbO",
]

ALL_OXIDE_GROUPS = {
    "fluxes": FLUX_OXIDES,
    "stabilizers": STABILIZER_OXIDES,
    "formers": FORMER_OXIDES,
    "others": OTHER_OXIDES,
}


def load_materials(path: str | None = None) -> dict[str, dict]:
    global _MATERIALS_CACHE
    if _MATERIALS_CACHE is not None:
        return _MATERIALS_CACHE
    p = path or _MATERIALS_PATH
    if not os.path.exists(p):
        raise FileNotFoundError(f"Materials file not found: {p}")
    with open(p) as f:
        data = json.load(f)
    raw = data.get("materials", {})
    _MATERIALS_CACHE = {}
    for key, mat in raw.items():
        lower_key = key.lower()
        _MATERIALS_CACHE[lower_key] = mat
        aliases = mat.get("aliases", [])
        for alias in aliases:
            _MATERIALS_CACHE[alias.lower()] = mat
    return _MATERIALS_CACHE


def invalidate_cache():
    global _MATERIALS_CACHE
    _MATERIALS_CACHE = None


def recipe_to_umf(recipe: list[dict], materials: dict[str, dict] | None = None) -> UMFAnalysis:
    """Convert a recipe (material names + parts) to UMF.

    Args:
        recipe: list of {"material": str, "percentage": float}
        materials: optional material DB (loaded from file if None)

    Returns:
        UMFAnalysis with normalized UMF
    """
    if materials is None:
        materials = load_materials()

    total_moles: dict[str, float] = {}

    for item in recipe:
        mat_name = item["material"].strip().lower()
        parts = item["percentage"]
        mat = materials.get(mat_name)
        if mat is None:
            raise ValueError(f"Unknown material: '{item['material']}'")
        analysis = mat.get("analysis", {})
        for oxide, wt_pct in analysis.items():
            mw = MOLECULAR_WEIGHTS.get(oxide)
            if mw and wt_pct > 0:
                moles_from_mat = (parts / 100.0) * (wt_pct / mw)
                total_moles[oxide] = total_moles.get(oxide, 0) + moles_from_mat

    return _normalize_moles(total_moles)


def oxide_to_umf(oxide_wt_pct: dict[str, float]) -> UMFAnalysis:
    """Convert direct oxide weight percentages to UMF.

    Args:
        oxide_wt_pct: dict mapping oxide -> weight percent (e.g. {"SiO2": 60.0, "Al2O3": 12.0})

    Returns:
        UMFAnalysis with normalized UMF
    """
    total_moles: dict[str, float] = {}
    total_wt = sum(oxide_wt_pct.values())
    if total_wt == 0:
        raise ValueError("Oxide weight percentages sum to zero")

    for oxide, wt_pct in oxide_wt_pct.items():
        mw = MOLECULAR_WEIGHTS.get(oxide)
        if mw and wt_pct > 0:
            total_moles[oxide] = wt_pct / mw

    return _normalize_moles(total_moles)


def _normalize_moles(moles: dict[str, float]) -> UMFAnalysis:
    """Normalize mole dict to unity flux and return UMFAnalysis."""
    flux_sum = sum(moles.get(ox, 0.0) for ox in FLUX_OXIDES)
    if flux_sum == 0:
        flux_sum = 1.0

    norm = {ox: mol / flux_sum for ox, mol in moles.items()}

    grouped: dict[str, dict[str, float]] = {
        "fluxes": {},
        "stabilizers": {},
        "formers": {},
        "others": {},
    }
    for ox, val in sorted(norm.items()):
        if val < 0.0005:
            continue
        rounded = round(val, 4)
        if ox in FLUX_OXIDES:
            grouped["fluxes"][ox] = rounded
        elif ox in STABILIZER_OXIDES:
            grouped["stabilizers"][ox] = rounded
        elif ox in FORMER_OXIDES:
            grouped["formers"][ox] = rounded
        else:
            grouped["others"][ox] = rounded

    sio2 = norm.get("SiO2", 0.0)
    al2o3 = norm.get("Al2O3", 0.001)
    si_al_ratio = round(sio2 / al2o3, 2)

    has_others = bool(grouped["others"])
    return UMFAnalysis(
        unity_molecular_formula=UnityMolecularFormula(
            fluxes=grouped["fluxes"],
            stabilizers=grouped["stabilizers"],
            formers=grouped["formers"],
            others=grouped["others"],
        ),
        calculated_ratios=CalculatedRatios(silica_alumina_ratio=si_al_ratio),
    )


def convert_recipe_to_umf(recipe: list[dict]) -> UMFAnalysis:
    """Backward-compatible wrapper: material names (case-insensitive) + parts → UMF."""
    return recipe_to_umf(recipe)
