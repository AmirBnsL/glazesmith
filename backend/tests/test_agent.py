"""Tests for the LLM interpreter agent (Layer 5).

Run with: uv run pytest tests/test_agent.py -v
Requires: FIREWORKS_API_KEY in .env at project root or in environment.
"""

import os
import inspect
import pytest


@pytest.fixture(autouse=True)
def _set_env():
    key = None
    # Try .env at project root (backend/../.env)
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("FIREWORKS_API_KEY="):
                    key = line.strip().split("=", 1)[1]
                    break
    if key:
        os.environ.setdefault("FIREWORKS_API_KEY", key)


class TestPrompts:
    def test_system_prompt_forbids_calculation(self):
        from app.agent.prompts import SYSTEM_PROMPT

        assert "do not calculate" in SYSTEM_PROMPT.lower()

    def test_strict_prompt_forbids_calculation(self):
        from app.agent.prompts import STRICT_PROMPT

        assert "do not calculate" in STRICT_PROMPT.lower()


class TestTools:
    def test_tools_file_removed(self):
        import importlib, sys
        spec = importlib.util.find_spec("app.agent.tools")
        assert spec is None, "tools.py should be removed — dead code"


class TestPromptBuilder:
    @pytest.fixture
    def sample_data(self):
        return {
            "umf": {
                "unity_molecular_formula": {
                    "fluxes": {"Na2O": 0.245, "K2O": 0.061, "CaO": 0.694},
                    "stabilizers": {"Al2O3": 0.336, "Fe2O3": 0.002},
                    "formers": {"SiO2": 2.184, "B2O3": 0.0},
                },
                "calculated_ratios": {"silica_alumina_ratio": 6.5},
            },
            "physics_engine": {
                "cte": 8.64e-6,
                "stress_delta": 1.34e-6,
                "crazing_risk_tier": "High",
                "stull_coordinates": {
                    "x_alumina": 0.336,
                    "y_silica": 2.184,
                    "classification_zone": "crazing_boundary",
                },
            },
            "gnn_inference": {
                "surface_class": "glossy",
                "surface_confidence": 0.88,
                "transparency_class": "transparent_clear",
                "transparency_confidence": 0.91,
                "color_family": "blue",
                "color_confidence": 0.72,
            },
            "nearest_neighbours": [
                {
                    "rank": 1,
                    "cosine_similarity": 0.94,
                    "recipe_name": "Blue Celadon Base",
                    "surface": "glossy",
                    "transparency": "translucent",
                    "color_family": "blue",
                }
            ],
        }

    def test_prompt_contains_cte(self, sample_data):
        from app.agent.prompts import build_analysis_prompt

        prompt = build_analysis_prompt(**sample_data)
        assert "CTE = 8.6400e-06" in prompt

    def test_prompt_contains_risk_tier(self, sample_data):
        from app.agent.prompts import build_analysis_prompt

        prompt = build_analysis_prompt(**sample_data)
        assert "Crazing Risk Tier = High" in prompt

    def test_prompt_contains_neighbour(self, sample_data):
        from app.agent.prompts import build_analysis_prompt

        prompt = build_analysis_prompt(**sample_data)
        assert "Blue Celadon Base" in prompt

    def test_prompt_contains_layer_annotations(self, sample_data):
        from app.agent.prompts import build_analysis_prompt

        prompt = build_analysis_prompt(**sample_data)
        assert "Layer 1" in prompt
        assert "Layer 2" in prompt
        assert "Layer 2b" in prompt


class TestAgentSignature:
    def test_signature_matches_decoupled_schema(self):
        from app.agent.core import FireworksAgent

        sig = inspect.signature(FireworksAgent.analyze_and_remediate)
        params = list(sig.parameters.keys())
        assert params == [
            "self",
            "umf",
            "physics_engine",
            "gnn_inference",
            "nearest_neighbours",
        ]

    def test_no_old_schema_keys_in_validation(self):
        from app.agent.core import FireworksAgent

        src = inspect.getsource(FireworksAgent._validate_inputs)
        assert "crazing_risk_probability" not in src
        assert "coefficient_of_thermal_expansion" not in src


@pytest.mark.live
class TestLiveAgent:
    """Requires FIREWORKS_API_KEY to be set."""

    @pytest.fixture
    def sample_data(self):
        return {
            "umf": {
                "unity_molecular_formula": {
                    "fluxes": {"Na2O": 0.245, "K2O": 0.061, "CaO": 0.694},
                    "stabilizers": {"Al2O3": 0.336, "Fe2O3": 0.002},
                    "formers": {"SiO2": 2.184, "B2O3": 0.0},
                },
                "calculated_ratios": {"silica_alumina_ratio": 6.5},
            },
            "physics_engine": {
                "cte": 8.64e-6,
                "stress_delta": 1.34e-6,
                "crazing_risk_tier": "High",
                "stull_coordinates": {
                    "x_alumina": 0.336,
                    "y_silica": 2.184,
                    "classification_zone": "crazing_boundary",
                },
            },
            "gnn_inference": {
                "surface_class": "glossy",
                "surface_confidence": 0.88,
                "transparency_class": "transparent_clear",
                "transparency_confidence": 0.91,
                "color_family": "blue",
                "color_confidence": 0.72,
            },
            "nearest_neighbours": [
                {
                    "rank": 1,
                    "cosine_similarity": 0.94,
                    "recipe_name": "Blue Celadon Base",
                    "surface": "glossy",
                    "transparency": "translucent",
                    "color_family": "blue",
                }
            ],
        }

    def test_e2e_returns_valid_remediation(self, sample_data):
        from app.agent.core import agent

        result = agent.analyze_and_remediate(**sample_data)
        assert "chemical_analysis" in result
        assert len(result["chemical_analysis"]) > 20
        assert "recipe_adjustments" in result
        assert len(result["recipe_adjustments"]) <= 5
        assert "expected_new_cte" in result
        assert isinstance(result["expected_new_cte"], (int, float))
        assert result["expected_new_cte"] > 0
