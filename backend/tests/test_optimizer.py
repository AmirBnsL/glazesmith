"""Tests for the Pareto Optimizer (Layer 3).

Run with: uv run pytest tests/test_optimizer.py -v
"""

from itertools import product

RECIPE = [
    {"material": "Nepheline Syenite", "percentage": 50.0},
    {"material": "Silica (Flint)", "percentage": 25.0},
    {"material": "Whiting (Calcium Carbonate)", "percentage": 15.0},
    {"material": "EPK Kaolin", "percentage": 10.0},
]

SMALL_RECIPE = [
    {"material": "Nepheline Syenite", "percentage": 60.0},
    {"material": "Silica (Flint)", "percentage": 40.0},
]


def _mock_cte_base(recipe: list[dict]) -> dict:
    """Deterministic mock: higher Na₂O sources → higher CTE."""
    ne_syenite = next(i["percentage"] for i in recipe if "Nepheline" in i["material"])
    silica = next(i["percentage"] for i in recipe if "Silica" in i["material"])
    cte = 6.0 + ne_syenite * 0.05 - silica * 0.02
    stress = cte - 7.30
    return {"cte": round(cte * 1e-6, 10), "stress_delta": round(stress * 1e-6, 10)}


def _mock_gnn_glossy(recipe: list[dict]) -> dict:
    """Mock GNN: returns glossy for high SiO₂/Al₂O₃ ratio, matte otherwise."""
    total_sio2 = 0
    total_al2o3 = 0.01
    for item in recipe:
        mat = item["material"]
        pct = item["percentage"]
        if "Silica" in mat or "Flint" in mat:
            total_sio2 += pct * 1.0
        if "Kaolin" in mat:
            total_sio2 += pct * 0.46
            total_al2o3 += pct * 0.38
        if "Nepheline" in mat:
            total_sio2 += pct * 0.60
            total_al2o3 += pct * 0.24
    ratio = total_sio2 / total_al2o3
    if ratio > 6:
        surface = "glossy"
        conf = 0.85
    elif ratio > 4:
        surface = "satin"
        conf = 0.70
    else:
        surface = "matte"
        conf = 0.75
    return {
        "surface_class": surface,
        "surface_confidence": conf,
        "transparency_class": "translucent",
    }


def _mock_cte_returns_zero(recipe: list[dict]) -> dict:
    return {"cte": 0.0, "stress_delta": 0.0}


def _mock_gnn_matte(recipe: list[dict]) -> dict:
    return {"surface_class": "matte", "surface_confidence": 0.80}


class TestIdentifyTopVariables:
    def test_returns_top_3_by_percentage(self):
        from app.optimizer.pareto import _identify_top_variables

        indices = _identify_top_variables(RECIPE)
        # 50, 25, 15 → indices 0, 1, 2
        assert indices == [0, 1, 2]

    def test_handles_small_recipe(self):
        from app.optimizer.pareto import _identify_top_variables

        indices = _identify_top_variables(SMALL_RECIPE)
        # max(1, N-1) = max(1, 1) = 1 variable, 1 filler
        assert len(indices) == 1

    def test_handles_single_ingredient(self):
        from app.optimizer.pareto import _identify_top_variables

        indices = _identify_top_variables([{"material": "SiO2", "percentage": 100.0}])
        assert len(indices) == 1

    def test_skips_zero_percentage(self):
        from app.optimizer.pareto import _identify_top_variables

        indices = _identify_top_variables([{"material": "A", "percentage": 0.0}])
        assert indices == []


class TestScore:
    def test_perfect_match_high_score(self):
        from app.optimizer.pareto import _compute_score

        score = _compute_score(
            stress_delta=0.0,
            surface_class="glossy",
            surface_confidence=0.9,
            target_surface="glossy",
            target_cte_max=7.30e-6,
        )
        assert score == 0.9

    def test_crazing_penalizes_score(self):
        from app.optimizer.pareto import _compute_score

        score_high_stress = _compute_score(
            stress_delta=3.0e-6,
            surface_class="glossy",
            surface_confidence=0.9,
            target_surface="glossy",
            target_cte_max=7.30e-6,
        )
        score_low_stress = _compute_score(
            stress_delta=0.5e-6,
            surface_class="glossy",
            surface_confidence=0.9,
            target_surface="glossy",
            target_cte_max=7.30e-6,
        )
        assert score_high_stress < score_low_stress

    def test_wrong_surface_drops_score(self):
        from app.optimizer.pareto import _compute_score

        correct = _compute_score(
            stress_delta=0.0,
            surface_class="glossy",
            surface_confidence=0.9,
            target_surface="glossy",
            target_cte_max=7.30e-6,
        )
        wrong = _compute_score(
            stress_delta=0.0,
            surface_class="matte",
            surface_confidence=0.9,
            target_surface="glossy",
            target_cte_max=7.30e-6,
        )
        assert correct > wrong


class TestOptimize:
    def test_returns_3_candidates(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        assert len(result) == 3

    def test_each_candidate_has_required_keys(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        for candidate in result:
            assert "recipe" in candidate
            assert "stress_delta" in candidate
            assert "surface_class" in candidate
            assert "surface_confidence" in candidate
            assert "score" in candidate

    def test_candidates_sum_to_100(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        for candidate in result:
            total = sum(i["percentage"] for i in candidate["recipe"])
            assert abs(total - 100.0) < 0.2

    def test_no_original_recipe_in_results(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        for candidate in result:
            assert candidate["recipe"] != RECIPE

    def test_sorted_by_score_descending(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        scores = [c["score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_target_surface_filters(self):
        from app.optimizer.pareto import optimize

        glossy = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy, target_surface="glossy")
        matte = optimize(RECIPE, _mock_cte_base, _mock_gnn_matte, target_surface="matte")
        # Different targets should produce different rankings
        assert glossy[0]["recipe"] != matte[0]["recipe"] or glossy[0]["score"] != matte[0]["score"]

    def test_handles_small_recipe(self):
        from app.optimizer.pareto import optimize

        result = optimize(SMALL_RECIPE, _mock_cte_base, _mock_gnn_glossy)
        assert 1 <= len(result) <= 3
        for c in result:
            assert abs(sum(i["percentage"] for i in c["recipe"]) - 100.0) < 0.2

    def test_handles_cte_fn_failure_gracefully(self):
        from app.optimizer.pareto import optimize

        def bad_cte(recipe):
            raise ValueError("CTE compute failed")

        result = optimize(RECIPE, bad_cte, _mock_gnn_glossy)
        assert result == []  # all candidates should fail gracefully

    def test_no_duplicate_candidates(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        sigs = set()
        for c in result:
            sig = "|".join(f"{i['material']}:{i['percentage']:.1f}" for i in c["recipe"])
            assert sig not in sigs
            sigs.add(sig)

    def test_candidates_have_materials_preserved(self):
        from app.optimizer.pareto import optimize

        result = optimize(RECIPE, _mock_cte_base, _mock_gnn_glossy)
        original_materials = {i["material"] for i in RECIPE}
        for c in result:
            candidate_materials = {i["material"] for i in c["recipe"]}
            assert candidate_materials == original_materials
