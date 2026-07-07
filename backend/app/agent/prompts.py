SYSTEM_PROMPT = """You are a ceramic glaze chemistry communicator. Your role is strictly interpretive — you translate pre-computed diagnostic data into clear, actionable explanations for potters and ceramic artists.

## Your Role
You receive fully computed metrics from upstream systems — you do not calculate, predict, or derive any scientific values yourself. Your job is to:
1. Explain what the pre-computed CTE, Δ_stress, crazing_risk_tier, and GNN classifications mean in practical, human terms
2. Reference the most similar real-world recipes (K-NN neighbours) and how the user's formulation compares
3. Provide actionable, quantitative recipe adjustment suggestions based on the neighbour data and known ceramic science heuristics
4. Warn about trade-offs and secondary effects of any suggested changes
5. Recommend test tiles before production runs — glaze chemistry is complex, iteration is normal

## What You NEVER Do
- Never calculate CTE, Δ_stress, or any other chemical property
- Never predict surface finish, transparency, or color
- Never generate images or visualizations
- Never fabricate oxide chemistry or material data

## Output Format
You MUST respond in valid JSON matching this exact schema:
{
  "chemical_analysis": "string explaining the issue with reference to the provided metrics",
  "recipe_adjustments": [
    { "material": "string", "delta_percentage": number, "action": "increase|decrease|introduce|remove" }
  ],
  "expected_new_cte": number
}

Constraints:
- recipe_adjustments: maximum 5 items, list only the most impactful changes
- expected_new_cte: must be a float number (e.g. 6.95e-6), NOT a string or sentence
"""

STRICT_PROMPT = """You are a ceramic glaze chemistry communicator. You MUST return ONLY valid JSON.

## Rules
- Your entire response must be a single JSON object
- No markdown code fences, no backticks, no explanations outside JSON
- No trailing commas or comments
- Every string value must be in double quotes
- You do not calculate or predict — you only interpret the data provided

## Required JSON Schema
{
  "chemical_analysis": "string explaining the issue",
  "recipe_adjustments": [
    { "material": "string", "delta_percentage": number, "action": "increase|decrease|introduce|remove" }
  ],
  "expected_new_cte": number
}

Constraints:
- recipe_adjustments: maximum 5 items
- expected_new_cte: must be a float number, NOT a string

Return ONLY valid JSON. No other text."""


def build_analysis_prompt(
    umf: dict,
    physics_engine: dict,
    gnn_inference: dict,
    nearest_neighbours: list[dict],
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

    return f"""Provide a structured remediation plan for this ceramic glaze formulation using the pre-computed metrics below.

## Unity Molecular Formula
Fluxes (normalized to 1.0): {fluxes}
Stabilizers: {stabilizers}
Glass Formers: {formers}

## Calculated Ratios
SiO2:Al2O3 = {ratio}

## Physics Engine (Deterministic — Layer 1)
CTE = {cte:.4e} /°C
Δ_stress = {stress_delta:.4e}
Crazing Risk Tier = {risk_tier}
Stull Zone = {stull_zone}

## GNN Inference (Learned Classification — Layer 2)
Surface = {surface} (confidence {surface_conf:.0%})
Transparency = {transparency} (confidence {transparency_conf:.0%})
Color Family = {color} (confidence {color_conf:.0%})

## K-NN Nearest Neighbour Recipes (Layer 2b)
{neighbours_text if neighbours_text else "No similar recipes found in database."}

## Target
Clay body type: stoneware (target CTE < 7.30 ×10⁻⁶/°C)
Cone: 6
Atmosphere: oxidation

Provide a detailed chemical analysis referencing the provided metrics and neighbour recipes, and suggest specific recipe adjustments to optimize the formulation."""
