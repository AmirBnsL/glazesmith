import json
import re
import time
from typing import Any
from openai import OpenAI, APIError, RateLimitError
from pydantic import ValidationError
from ..config import settings
from .prompts import SYSTEM_PROMPT, STRICT_PROMPT, build_analysis_prompt

MAX_RETRIES = 2
FALLBACK = {
    "chemical_analysis": "Analysis could not be completed due to a processing error. Please verify your recipe and try again.",
    "recipe_adjustments": [],
    "expected_new_cte": 0.0,
}


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
        self._validate_inputs(umf, physics_engine, gnn_inference, nearest_neighbours)

        prompt = build_analysis_prompt(umf, physics_engine, gnn_inference, nearest_neighbours)
        last_error = ""

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": STRICT_PROMPT if attempt > 0 else SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=2048,
                )

                result = self._parse_response(response)
                if result is not None:
                    return result

                last_error = "Malformed JSON response"

            except (APIError, RateLimitError) as e:
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1.5 ** (attempt + 1))

        return {
            **FALLBACK,
            "chemical_analysis": f"{FALLBACK['chemical_analysis']} Last error: {last_error}",
        }

    def _parse_response(self, response: Any) -> dict | None:
        choice = response.choices[0]
        content = choice.message.content

        if content:
            try:
                parsed = json.loads(content)
                return self._validate_output(parsed)
            except (json.JSONDecodeError, ValidationError, KeyError):
                pass

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


agent = FireworksAgent()
