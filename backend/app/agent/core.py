import json
import logging
import re
import time
from typing import Any
from openai import OpenAI, APIError, RateLimitError
from pydantic import ValidationError
from ..config import settings
from .prompts import SYSTEM_PROMPT, STRICT_PROMPT, VERIFICATION_SYSTEM_PROMPT, build_analysis_prompt, build_verification_prompt
from .tools import verify_adjustment

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class FireworksAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.fireworks_base_url,
            api_key=settings.fireworks_api_key,
        )

    def analyze_and_remediate(
        self,
        umf: dict,
        physics_engine: dict,
        gnn_inference: dict,
        nearest_neighbours: list[dict],
    ) -> dict:
        """Single-shot analysis (legacy, no verification)."""
        self._validate_inputs(umf, physics_engine, gnn_inference, nearest_neighbours)
        prompt = build_analysis_prompt(umf, physics_engine, gnn_inference, nearest_neighbours)
        return self._call_llm(prompt)

    def remediate_with_verification(
        self,
        umf: dict,
        physics_engine: dict,
        gnn_inference: dict,
        nearest_neighbours: list[dict],
        original_recipe: list[dict],
        optimizer_candidates: list[dict] | None = None,
        cone_min: float = 6.0,
        cone_max: float = 6.0,
        atmosphere: str = "oxidation",
    ) -> dict:
        """Two-pass verify loop.

        Pass 1: LLM proposes adjustments based on metrics.
        Verify:  Each adjustment is run through the real pipeline.
        Pass 2:  LLM reviews verified results and produces final recommendation.
        """
        self._validate_inputs(umf, physics_engine, gnn_inference, nearest_neighbours)

        prompt = build_analysis_prompt(
            umf, physics_engine, gnn_inference, nearest_neighbours,
            optimizer_candidates, cone_min, cone_max, atmosphere,
        )
        pass1_result = self._call_llm(prompt)

        if not pass1_result or "recipe_adjustments" not in pass1_result:
            return self._build_fallback_remediation(umf, physics_engine, gnn_inference)

        raw_adjustments = pass1_result.get("recipe_adjustments", [])
        if not isinstance(raw_adjustments, list):
            raw_adjustments = []

        verified_adjustments = []
        for adj in raw_adjustments[:5]:
            material = adj.get("material", "")
            delta = adj.get("delta_percentage", 0)
            action = adj.get("action", "")

            verified = verify_adjustment(
                original_recipe, adj,
                cone_min=cone_min, cone_max=cone_max, atmosphere=atmosphere,
            )

            entry = {
                "material": material,
                "delta_percentage": delta,
                "action": action,
                "recommendation": "unverified",
            }

            if verified:
                orig_cte = physics_engine.get("cte", 0)
                new_cte = verified["verified_cte"]
                improved = new_cte < orig_cte

                entry["verified_cte"] = verified["verified_cte"]
                entry["verified_surface"] = verified["verified_surface"]
                entry["verified_transparency"] = verified["verified_transparency"]
                entry["verified_crazing_risk"] = verified["verified_crazing_risk"]
                entry["recommendation"] = "recommended" if improved else "not_recommended"

            verified_adjustments.append(entry)

        original_data = {
            "umf": umf,
            "cte": physics_engine.get("cte", 0),
            "stress_delta": physics_engine.get("stress_delta", 0),
            "surface_class": gnn_inference.get("surface_class", "unknown"),
        }

        verify_prompt = build_verification_prompt(original_data, verified_adjustments, optimizer_candidates)
        pass2_result = self._call_llm(verify_prompt, is_verification=True)

        if not pass2_result:
            return self._build_verified_remediation(pass1_result, verified_adjustments, physics_engine)

        final_adjustments = pass2_result.get("recipe_adjustments", verified_adjustments)
        final_analysis = pass2_result.get("chemical_analysis", pass1_result.get("chemical_analysis", ""))
        final_cte = pass2_result.get("expected_new_cte", 0.0)
        verification_summary = pass2_result.get("verification_summary", "")

        adjustments = []
        for adj in final_adjustments:
            uid = (adj.get("material", ""), adj.get("action", ""), adj.get("delta_percentage", 0))
            matched = next((v for v in verified_adjustments if (v["material"], v["action"], v["delta_percentage"]) == uid), None)
            if matched:
                verified_fields = {k: v for k, v in matched.items()
                                   if k in ("verified_cte", "verified_surface", "verified_transparency", "verified_crazing_risk")}
                rec = adj.get("recommendation") or matched.get("recommendation", "unverified")
                adjustments.append({**adj, **verified_fields, "recommendation": rec})
            else:
                adjustments.append(adj)

        return {
            "chemical_analysis": final_analysis,
            "recipe_adjustments": adjustments,
            "expected_new_cte": final_cte,
            "verification_summary": verification_summary,
        }

    def _call_llm(self, prompt: str, is_verification: bool = False) -> dict | None:
        last_error = ""
        for attempt in range(MAX_RETRIES):
            try:
                system = VERIFICATION_SYSTEM_PROMPT if is_verification else (STRICT_PROMPT if attempt > 0 else SYSTEM_PROMPT)
                response = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                        max_tokens=8192,
                )

                finish = getattr(response.choices[0], "finish_reason", "unknown")
                usage = getattr(response, "usage", None)
                if usage:
                    logger.info(
                        "LLM call (verify=%s, attempt=%d): prompt=%d, completion=%d, total=%d, finish=%s",
                        is_verification, attempt, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens, finish,
                    )

                result = self._parse_response(response)
                if result is not None:
                    return result

                last_error = "Malformed JSON response"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1.5 ** (attempt + 1))

            except (APIError, RateLimitError) as e:
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1.5 ** (attempt + 1))

        logger.warning("LLM call failed after %d retries: %s", MAX_RETRIES, last_error)
        return None

    def _parse_response(self, response: Any) -> dict | None:
        choice = response.choices[0]
        content = choice.message.content or ""

        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            json_str = content[first_brace : last_brace + 1]
            try:
                parsed = json.loads(json_str)
                return self._validate_output(parsed)
            except (json.JSONDecodeError, ValidationError, KeyError):
                pass

        logger.warning(
            "Failed to parse JSON from LLM response (finish=%s). Raw start: %.200s",
            getattr(choice, "finish_reason", "unknown"),
            content[:200],
        )
        return None

    def _validate_inputs(
        self,
        umf: dict,
        physics_engine: dict,
        gnn_inference: dict,
        nearest_neighbours: list[dict],
    ) -> None:
        if not isinstance(umf, dict) or not isinstance(physics_engine, dict) or not isinstance(gnn_inference, dict):
            raise ValueError("umf, physics_engine, and gnn_inference must be dictionaries")
        if not isinstance(nearest_neighbours, list):
            raise ValueError("nearest_neighbours must be a list")

    def _validate_output(self, data: dict) -> dict:
        from ..models.schemas import Remediation, RecipeAdjustment

        adjustments_raw = data.get("recipe_adjustments", [])
        if not isinstance(adjustments_raw, list):
            adjustments_raw = []
        adjustments = []
        for adj in adjustments_raw[:5]:
            try:
                adjustments.append(RecipeAdjustment(**adj))
            except (ValidationError, TypeError):
                pass

        raw_cte = data.get("expected_new_cte", 0.0)
        if isinstance(raw_cte, str):
            match = re.search(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", str(raw_cte).replace("×10", "e").replace("−", "-"))
            raw_cte = float(match.group()) if match else 0.0
        else:
            raw_cte = float(raw_cte)

        validated = Remediation(
            chemical_analysis=str(data.get("chemical_analysis", "")),
            recipe_adjustments=adjustments,
            expected_new_cte=raw_cte,
        )

        return validated.model_dump()

    def _build_fallback_remediation(self, umf: dict, physics_engine: dict, gnn_inference: dict) -> dict:
        return {
            "chemical_analysis": (
                f"This glaze has a Si:Al ratio of {umf.get('calculated_ratios', {}).get('silica_alumina_ratio', 'unknown')} "
                f"and predicted {gnn_inference.get('surface_class', 'unknown')} surface. "
                f"CTE stress delta: {physics_engine.get('stress_delta', 0):.2e}. "
                f"To adjust, consider modifying flux ratios or silica content."
            ),
            "recipe_adjustments": [],
            "expected_new_cte": 0.0,
            "verification_summary": "",
        }

    def _build_verified_remediation(self, pass1: dict, verified: list[dict], physics: dict) -> dict:
        improved = [v for v in verified if v.get("recommendation") == "recommended"]
        best_cte = 0.0
        if improved:
            best_cte = improved[0].get("verified_cte", 0.0)

        return {
            "chemical_analysis": pass1.get("chemical_analysis", ""),
            "recipe_adjustments": verified,
            "expected_new_cte": best_cte,
            "verification_summary": f"Verified {len(verified)} adjustments: "
                                    f"{len(improved)} recommended, "
                                    f"{len(verified) - len(improved)} not recommended.",
        }


_agent_instance: FireworksAgent | None = None


def get_agent() -> FireworksAgent:
    global _agent_instance
    if _agent_instance is None:
        if not settings.fireworks_api_key:
            raise RuntimeError("Fireworks API key not configured. Set FIREWORKS_API_KEY in backend/.env")
        _agent_instance = FireworksAgent()
    return _agent_instance
