import json
from openai import OpenAI
from ..config import settings
from .prompts import SYSTEM_PROMPT, build_analysis_prompt
from .tools import TOOL_DEFINITIONS


class FireworksAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.fireworks_base_url,
            api_key=settings.fireworks_api_key,
        )

    def analyze_and_remediate(self, umf: dict, gnn: dict) -> dict:
        prompt = build_analysis_prompt(umf, gnn)

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2048,
        )

        choice = response.choices[0]
        content = choice.message.content

        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        if choice.message.tool_calls:
            return self._execute_tool_chain(choice.message.tool_calls, prompt)

        return {
            "chemical_analysis": "Analysis completed, but structured output could not be parsed.",
            "recipe_adjustments": [],
            "expected_new_cte": 0.0,
        }

    def _execute_tool_chain(self, tool_calls: list, original_prompt: str) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": original_prompt},
        ]

        for tc in tool_calls:
            result = self._run_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        final = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2048,
        )

        try:
            return json.loads(final.choices[0].message.content)
        except (json.JSONDecodeError, TypeError, KeyError):
            return {
                "chemical_analysis": "Tool-assisted analysis completed.",
                "recipe_adjustments": [],
                "expected_new_cte": 0.0,
            }

    def _run_tool(self, name: str, args: dict) -> dict:
        if name == "calculate_cte":
            return self._calc_cte(args)
        if name == "fix_defect":
            return self._fix_defect(args)
        return {"result": "Tool executed"}

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
