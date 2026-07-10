SYSTEM_PROMPT = """Return ONLY a raw JSON object. No markdown, no backticks, no explanation, no reasoning before or after. The entire response must be parseable by json.loads().

You are a ceramic glaze chemistry communicator. You translate pre-computed diagnostic metrics into actionable explanations for potters.

{"chemical_analysis": "string explaining the issue with reference to the provided metrics", "recipe_adjustments": [{"material": "string", "delta_percentage": number, "action": "increase|decrease|introduce|remove"}], "expected_new_cte": number}

- max 5 adjustments
- expected_new_cte is a float, NOT a string
- You interpret metrics, you do not calculate or predict"""

STRICT_PROMPT = """Return ONLY a raw JSON object. No markdown, no backticks, no explanation, no reasoning before or after. The entire response must be parseable by json.loads().

{"chemical_analysis": "string", "recipe_adjustments": [{"material": "string", "delta_percentage": number, "action": "increase|decrease|introduce|remove"}], "expected_new_cte": number}

- max 5 adjustments
- expected_new_cte is a float, NOT a string
- No trailing commas"""

VERIFICATION_SYSTEM_PROMPT = """Return ONLY a raw JSON object. No markdown, no backticks, no explanation, no reasoning before or after. The entire response must be parseable by json.loads().

You previously suggested recipe adjustments. The system tested each through the actual physics engine and ML model.

Review the verified results, recommend adjustments that genuinely improve the formulation, and update expected_new_cte to the real verified CTE of the best adjustment.

{"chemical_analysis": "string — updated analysis", "recipe_adjustments": [{"material": "string", "delta_percentage": number, "action": "increase|decrease|introduce|remove", "recommendation": "recommended|not_recommended|unverified"}], "expected_new_cte": number, "verification_summary": "string — what was tested and what worked best"}"""


def build_analysis_prompt(
    umf: dict,
    physics_engine: dict,
    gnn_inference: dict,
    nearest_neighbours: list[dict],
    optimizer_candidates: list[dict] | None = None,
    cone_min: float = 6.0,
    cone_max: float = 6.0,
    atmosphere: str = "oxidation",
) -> str:
    """Build a structured prompt from decoupled diagnostic data for the LLM interpreter."""
    fluxes = umf.get("unity_molecular_formula", {}).get("fluxes", {})
    stabilizers = umf.get("unity_molecular_formula", {}).get("stabilizers", {})
    formers = umf.get("unity_molecular_formula", {}).get("formers", {})
    ratio = umf.get("calculated_ratios", {}).get("silica_alumina_ratio", 0)

    cte = physics_engine.get("cte", physics_engine.get("estimated_cte", 0))
    stress_delta = physics_engine.get("stress_delta", 0)
    risk_tier = physics_engine.get("crazing_risk_tier", "Unknown")
    stull_zone = physics_engine.get("stull_coordinates", {}).get("classification_zone", "unknown")

    surface = gnn_inference.get("surface_class", "unknown")
    surface_conf = gnn_inference.get("surface_confidence", 0)
    transparency = gnn_inference.get("transparency_class", "unknown")
    transparency_conf = gnn_inference.get("transparency_confidence", 0)
    color = gnn_inference.get("color_family", "unknown")
    color_conf = gnn_inference.get("color_confidence", 0)

    neighbours_text = ""
    if nearest_neighbours:
        parts = []
        for n in nearest_neighbours[:5]:
            parts.append(
                f"  #{n.get('rank')}: {n.get('recipe_name')} "
                f"(cosine similarity {n.get('cosine_similarity', 0):.2f}, "
                f"surface={n.get('surface')}, transparency={n.get('transparency')}, "
                f"color={n.get('color_family')})"
            )
        neighbours_text = "\n".join(parts)

    optimizer_text = ""
    if optimizer_candidates:
        parts = ["The algorithmic optimizer found these alternative formulations:"]
        for idx, c in enumerate(optimizer_candidates[:3], 1):
            recipe_str = ", ".join(f"{ing['material']} {ing['percentage']}%" for ing in c.get("recipe", []))
            parts.append(
                f"  Candidate #{idx}: {recipe_str} — "
                f"stress_delta={c.get('stress_delta', 0):.4e}, "
                f"surface={c.get('surface_class', 'unknown')} "
                f"(confidence {c.get('surface_confidence', 0):.0%}), "
                f"score={c.get('score', 0):.3f}"
            )
        optimizer_text = "\n".join(parts)

    def _fmt(d: dict) -> str:
        return ", ".join(f"{k} {v:.2f}" for k, v in sorted(d.items())) if d else "none"

    return f"""Provide a structured remediation plan for this ceramic glaze formulation using the pre-computed metrics below.

## Unity Molecular Formula
Fluxes (to 1.0): {_fmt(fluxes)}
Stabilizers: {_fmt(stabilizers)}
Glass Formers: {_fmt(formers)}

## Calculated Ratios
SiO2:Al2O3 = {ratio}

## Physics Engine (Deterministic — Layer 1)
CTE = {cte:.4e} /°C
Δ_stress = {stress_delta:.4e}
Crazing Risk Tier = {risk_tier}
Stull Zone = {stull_zone}

## ML Inference (Learned Classification — Layer 2)
Surface = {surface} (confidence {surface_conf:.0%})
Transparency = {transparency} (confidence {transparency_conf:.0%})
Color Family = {color} (confidence {color_conf:.0%})

## K-NN Nearest Neighbour Recipes (Layer 2b)
{neighbours_text if neighbours_text else "No similar recipes found in database."}

## Algorithmic Optimizer Candidates (Layer 3)
{optimizer_text if optimizer_text else "No algorithmic candidates generated."}

## Target
Clay body type: stoneware (target CTE < 7.30 ×10⁻⁶/°C)
Cone: {cone_min}
Atmosphere: {atmosphere}

Provide a detailed chemical analysis referencing the provided metrics and neighbour recipes, and suggest specific recipe adjustments to optimize the formulation."""


def build_verification_prompt(
    original_data: dict,
    verified_adjustments: list[dict],
    optimization_candidates: list[dict] | None = None,
) -> str:
    original_cte = original_data.get("cte", 0)
    original_surface = original_data.get("surface_class", "unknown")

    adjustments_text = ""
    for adj in verified_adjustments:
        vc = adj.get("verified_cte")
        if vc is not None:
            delta = vc - original_cte
            direction = "REDUCES" if delta < 0 else "INCREASES" if delta > 0 else "NO CHANGE"
            surf_change = ""
            vs = adj.get("verified_surface")
            if vs and vs != original_surface:
                surf_change = f" (surface changed to {vs})"
            adjustments_text += (
                f"  - {adj['action']} {adj['material']} by {adj['delta_percentage']}%:\n"
                f"    CTE: {original_cte:.4e} → {vc:.4e} ({direction}){surf_change}\n"
                f"    Surface: {vs or 'N/A'}\n"
                f"    Crazing risk: {adj.get('verified_crazing_risk', 0):.2%}\n"
            )
        else:
            adjustments_text += f"  - {adj['action']} {adj['material']} by {adj['delta_percentage']}%: COULD NOT BE VERIFIED\n"

    optimizer_text = ""
    if optimization_candidates:
        parts = []
        for idx, c in enumerate(optimization_candidates[:3], 1):
            recipe_str = ", ".join(f"{ing['material']} {ing['percentage']}%" for ing in c.get("recipe", []))
            parts.append(
                f"  Candidate #{idx}: {recipe_str} — "
                f"stress_delta={c.get('stress_delta', 0):.4e}, "
                f"surface={c.get('surface_class', 'unknown')}, "
                f"score={c.get('score', 0):.3f}"
            )
        optimizer_text = "\n".join(parts)

    return f"""Your previous recipe suggestions have been tested through the physics engine and ML model. Review the verified results and update your recommendation.

## Original Metrics
CTE: {original_cte:.4e}
Surface: {original_surface}

## Verified Adjustment Results
{adjustments_text}

## Algorithmic Optimizer Candidates
{optimizer_text if optimizer_text else "None generated."}

## Instructions
1. Compare each verified adjustment's CTE against the target (< 7.30e-6)
2. Note any surface/transparency changes caused by the adjustments
3. Recommend the adjustments that genuinely improve the formulation
4. Set "recommended" for adjustments that reduce CTE without degrading surface, "not_recommended" for ones that don't help
5. Set expected_new_cte to the real verified CTE of the single best adjustment
6. Provide a verification_summary explaining what was tested and what worked best"""
