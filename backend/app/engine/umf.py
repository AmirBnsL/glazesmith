"""
Unity Molecular Formula (UMF) Engine.

Converts raw material mass percentages into a normalized Unity Molecular Formula
where total fluxes (Na2O + K2O + CaO + MgO...) sum to 1.0.
"""

from ..models.schemas import UMFAnalysis, UnityMolecularFormula, CalculatedRatios

# Material database: {name: {oxide: wt_fraction, ...}}
# Sources: Glazy, DigitalFire, ceramic material data sheets
MATERIAL_DB: dict[str, dict[str, float]] = {
    "Nepheline Syenite": {
        "SiO2": 0.600, "Al2O3": 0.240, "Na2O": 0.100, "K2O": 0.050, "CaO": 0.005, "MgO": 0.001, "Fe2O3": 0.001,
    },
    "Custer Feldspar": {
        "SiO2": 0.700, "Al2O3": 0.170, "K2O": 0.100, "Na2O": 0.030, "CaO": 0.005, "MgO": 0.001, "Fe2O3": 0.001,
    },
    "Potash Feldspar": {
        "SiO2": 0.650, "Al2O3": 0.180, "K2O": 0.120, "Na2O": 0.030, "CaO": 0.005, "Fe2O3": 0.002,
    },
    "Silica (Flint)": {
        "SiO2": 1.000,
    },
    "Silica (325 mesh)": {
        "SiO2": 1.000,
    },
    "Whiting (Calcium Carbonate)": {
        "CaO": 0.560, "SiO2": 0.010,
    },
    "Whiting": {
        "CaO": 0.560, "SiO2": 0.010,
    },
    "EPK Kaolin": {
        "SiO2": 0.460, "Al2O3": 0.380, "Fe2O3": 0.005, "TiO2": 0.015,
    },
    "Kaolin": {
        "SiO2": 0.460, "Al2O3": 0.380, "Fe2O3": 0.005, "TiO2": 0.015,
    },
    "Gillespie Borate": {
        "B2O3": 0.280, "CaO": 0.250, "SiO2": 0.100, "Al2O3": 0.020, "Na2O": 0.010,
    },
    "Gerstley Borate": {
        "B2O3": 0.300, "CaO": 0.260, "SiO2": 0.080, "Al2O3": 0.020, "MgO": 0.010, "Na2O": 0.005,
    },
    "Dolomite": {
        "CaO": 0.300, "MgO": 0.220, "SiO2": 0.010,
    },
    "Zinc Oxide": {
        "ZnO": 1.000,
    },
    "Red Iron Oxide": {
        "Fe2O3": 0.960,
    },
    "Titanium Dioxide": {
        "TiO2": 0.990,
    },
    "Bentonite": {
        "SiO2": 0.600, "Al2O3": 0.200, "Fe2O3": 0.030, "MgO": 0.020, "CaO": 0.010, "Na2O": 0.010,
    },
    "Lithium Carbonate": {
        "Li2O": 0.400,
    },
    "Spodumene": {
        "SiO2": 0.640, "Al2O3": 0.270, "Li2O": 0.080, "Na2O": 0.005, "Fe2O3": 0.005,
    },
}

# Molecular weights for oxide conversion (g/mol)
MOLECULAR_WEIGHTS: dict[str, float] = {
    "SiO2": 60.08, "Al2O3": 101.96, "Fe2O3": 159.69, "TiO2": 79.87,
    "CaO": 56.08, "MgO": 40.30, "K2O": 94.20, "Na2O": 61.98,
    "Li2O": 29.88, "B2O3": 69.62, "ZnO": 81.38, "PbO": 223.20,
}

FLUX_OXIDES = {"Na2O", "K2O", "CaO", "MgO", "ZnO", "Li2O", "PbO"}
STABILIZER_OXIDES = {"Al2O3", "Fe2O3"}
FORMER_OXIDES = {"SiO2", "B2O3"}


def recipe_to_oxide_weight(recipe: list[dict]) -> dict[str, float]:
    """Convert recipe material percentages to total oxide weight percentages."""
    oxide_totals: dict[str, float] = {}
    for item in recipe:
        material = item["material"]
        pct = item["percentage"] / 100.0
        analysis = MATERIAL_DB.get(material)
        if analysis is None:
            raise ValueError(f"Unknown material: {material}")
        for oxide, fraction in analysis.items():
            oxide_totals[oxide] = oxide_totals.get(oxide, 0.0) + pct * fraction
    return oxide_totals


def oxide_weight_to_moles(oxide_wt: dict[str, float]) -> dict[str, float]:
    """Convert oxide weight percentages to moles."""
    moles: dict[str, float] = {}
    for oxide, wt in oxide_wt.items():
        mw = MOLECULAR_WEIGHTS.get(oxide)
        if mw and wt > 0:
            moles[oxide] = wt / mw
    return moles


def normalize_umf(moles: dict[str, float]) -> UMFAnalysis:
    """Normalize to Unity Molecular Formula where total fluxes = 1.0."""
    flux_sum = sum(moles.get(ox, 0.0) for ox in FLUX_OXIDES)
    if flux_sum == 0:
        flux_sum = 1.0  # prevent div by zero
    norm = {ox: moles.get(ox, 0.0) / flux_sum for ox in moles}

    fluxes = {ox: round(norm.get(ox, 0.0), 3) for ox in sorted(FLUX_OXIDES) if norm.get(ox, 0.0) > 0.001}
    stabilizers = {ox: round(norm.get(ox, 0.0), 3) for ox in sorted(STABILIZER_OXIDES) if norm.get(ox, 0.0) > 0.001}
    formers = {ox: round(norm.get(ox, 0.0), 3) for ox in sorted(FORMER_OXIDES) if norm.get(ox, 0.0) > 0.001}

    sio2 = norm.get("SiO2", 0.0)
    al2o3 = norm.get("Al2O3", 0.001)
    si_al_ratio = round(sio2 / al2o3, 2)

    return UMFAnalysis(
        unity_molecular_formula=UnityMolecularFormula(
            fluxes=fluxes, stabilizers=stabilizers, formers=formers,
        ),
        calculated_ratios=CalculatedRatios(silica_alumina_ratio=si_al_ratio),
    )


def convert_recipe_to_umf(recipe: list[dict]) -> UMFAnalysis:
    """Full conversion: recipe → oxide wt% → moles → normalized UMF."""
    oxide_wt = recipe_to_oxide_weight(recipe)
    moles = oxide_weight_to_moles(oxide_wt)
    return normalize_umf(moles)
