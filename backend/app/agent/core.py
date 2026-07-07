import json
import time
from typing import Any
from openai import OpenAI, APIError, RateLimitError
from pydantic import ValidationError
from ..config import settings
from .prompts import SYSTEM_PROMPT, STRICT_PROMPT, build_analysis_prompt
from .tools import TOOL_DEFINITIONS
from ..models.schemas import Remediation, RecipeAdjustment

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

    def analyze_and_remediate(self, umf: dict, gnn: dict) -> dict:
        self._validate_inputs(umf, gnn)

        prompt = build_analysis_prompt(umf, gnn)
        last_error = ""

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": STRICT_PROMPT if attempt > 0 else SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
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
                validated = self._validate_output(parsed)
                return validated
            except (json.JSONDecodeError, ValidationError, KeyError):
                pass

        if choice.message.tool_calls:
            return self._execute_tool_chain(choice.message.tool_calls)

        return None

    def _execute_tool_chain(self, tool_calls: list) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments)
                result = self._run_tool(tc.function.name, args)
                messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })
            except (json.JSONDecodeError, KeyError) as e:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps({"error": str(e)}),
                })

        for attempt in range(MAX_RETRIES):
            try:
                final = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages + [{"role": "user", "content": "Now provide the final remediation in JSON format based on the tool results above."}],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=2048,
                )

                content = final.choices[0].message.content
                if content:
                    try:
                        parsed = json.loads(content)
                        return self._validate_output(parsed)
                    except (json.JSONDecodeError, ValidationError):
                        if attempt < MAX_RETRIES - 1:
                            messages.append({
                                "role": "user",
                                "content": "Your previous response was not valid JSON. Return ONLY valid JSON matching the schema.",
                            })
            except (APIError, RateLimitError) as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1.5 ** (attempt + 1))

        return dict(FALLBACK)

    def _validate_inputs(self, umf: dict, gnn: dict) -> None:
        if not isinstance(umf, dict) or not isinstance(gnn, dict):
            raise ValueError("UMF and GNN data must be dictionaries")

        if not gnn.get("coefficient_of_thermal_expansion"):
            gnn["coefficient_of_thermal_expansion"] = 7.0e-6
        if not gnn.get("predicted_surface_class"):
            gnn["predicted_surface_class"] = "glossy"
        if gnn.get("crazing_risk_probability") is None:
            gnn["crazing_risk_probability"] = 0.0

    def _validate_output(self, data: dict) -> dict:
        adjustments = [
            RecipeAdjustment(**adj) for adj in data.get("recipe_adjustments", [])
        ]

        validated = Remediation(
            chemical_analysis=str(data.get("chemical_analysis", "")),
            recipe_adjustments=adjustments,
            expected_new_cte=float(data.get("expected_new_cte", 0.0)),
        )

        return validated.model_dump()

    def _run_tool(self, name: str, args: dict) -> dict:
        if name == "calculate_cte":
            return self._calc_cte(args)
        if name == "fix_defect":
            return self._fix_defect(args)
        return {"result": f"Tool {name} executed"}

    def _calc_cte(self, args: dict) -> dict:
        factors = {"sio2": 0.8, "al2o3": 1.0, "k2o": 12.0, "na2o": 16.0, "cao": 13.0, "mgo": 6.0}
        total = sum(args.get(k, 0.0) for k in factors)
        if total == 0:
            return {"cte": 0.0}
        cte = sum(args.get(ox, 0.0) / total * 100 * factor for ox, factor in factors.items()) / 100
        return {"cte": round(cte, 2)}

    def _fix_defect(self, args: dict) -> dict:
        defect = args.get("defect", "")
        advice = {
            "crazing": "Increase SiO2 by 5-10%, reduce Na2O/K2O by 2-4%. Consider substituting spodumene for feldspar.",
            "crawling": "Reduce Al2O3 by 2-3%, increase flux content. Ensure bisque is clean and dust-free.",
            "pinholing": "Increase hold time at peak temperature. Add 1-2% B2O3 to reduce viscosity.",
            "blistering": "Reduce peak temperature by 1-2 cones. Reduce Fe2O3 content.",
            "shivering": "Reduce SiO2 by 3-5%, increase Na2O or K2O to raise CTE.",
        }
        return {"defect": defect, "advice": advice.get(defect, "Unknown defect")}


agent = FireworksAgent()
