"""Tests for the K-NN Vector Retrieval Module (Layer 2b).

Run with: uv run pytest tests/test_retrieval.py -v
"""

import pytest
import os
import json


INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "data", "glazybench", "glazy_index.faiss",
)
METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "data", "glazybench", "glazy_metadata.json",
)


@pytest.fixture
def sample_umf():
    """A typical cone 6 clear glaze UMF vector."""
    return [2.184, 0.336, 0.0, 0.0, 0.245, 0.061, 0.0, 0.694, 0.0, 0.0, 0.0, 0.0, 0.002, 0.0, 0.0, 0.0, 0.0, 0.0]


@pytest.fixture
def high_flux_umf():
    """A high-alkali recipe UMF (high CTE, crazing risk)."""
    return [1.5, 0.2, 0.0, 0.0, 0.6, 0.2, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


class TestIndexExistence:
    def test_index_file_exists(self):
        assert os.path.exists(INDEX_PATH), f"Index not found at {INDEX_PATH}"
        assert os.path.getsize(INDEX_PATH) > 1000

    def test_metadata_file_exists(self):
        assert os.path.exists(METADATA_PATH), f"Metadata not found at {METADATA_PATH}"
        with open(METADATA_PATH) as f:
            data = json.load(f)
        assert len(data) > 10000, f"Expected >10000 records, got {len(data)}"


class TestGlazyIndex:
    def test_load_index(self):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        idx.load()
        assert idx._loaded
        assert idx.index is not None
        assert idx.index.ntotal > 10000

    def test_search_returns_5_neighbours(self, sample_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        results = idx.search(sample_umf, k=5)
        assert len(results) == 5

    def test_each_result_has_required_keys(self, sample_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        results = idx.search(sample_umf, k=5)
        for r in results:
            assert "rank" in r
            assert "cosine_similarity" in r
            assert "recipe_name" in r
            assert "surface" in r
            assert "transparency" in r
            assert "color_family" in r
            assert "community_notes" in r

    def test_cosine_similarity_is_positive(self, sample_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        results = idx.search(sample_umf, k=5)
        for r in results:
            assert 0 <= r["cosine_similarity"] <= 1.0

    def test_ranks_are_sequential(self, sample_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        results = idx.search(sample_umf, k=5)
        assert [r["rank"] for r in results] == [1, 2, 3, 4, 5]

    def test_different_umfs_return_different_results(self, sample_umf, high_flux_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        r1 = idx.search(sample_umf, k=3)
        r2 = idx.search(high_flux_umf, k=3)
        names1 = {r["recipe_name"] for r in r1}
        names2 = {r["recipe_name"] for r in r2}
        assert names1 != names2, "Two distinct UMFs should return different neighbours"

    def test_umf_dict_to_vector(self):
        from app.retrieval.knn import GlazyIndex, UMF_OXIDES

        idx = GlazyIndex()
        umf_dict = {"SiO2": 2.184, "Al2O3": 0.336, "Na2O": 0.245}
        vec = idx.umf_dict_to_vector(umf_dict)
        assert len(vec) == len(UMF_OXIDES)
        assert vec[UMF_OXIDES.index("SiO2")] == 2.184
        assert vec[UMF_OXIDES.index("Al2O3")] == 0.336
        assert vec[UMF_OXIDES.index("Na2O")] == 0.245
        # All other positions should be 0
        filled = {UMF_OXIDES.index("SiO2"), UMF_OXIDES.index("Al2O3"), UMF_OXIDES.index("Na2O")}
        assert all(vec[i] == 0.0 for i in range(len(UMF_OXIDES)) if i not in filled)

    def test_empty_umf_still_returns_results(self):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        empty = [0.0] * 18
        results = idx.search(empty, k=3)
        assert len(results) >= 1

    def test_lazy_load_on_first_search(self, sample_umf):
        from app.retrieval.knn import GlazyIndex

        idx = GlazyIndex(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
        assert not idx._loaded
        results = idx.search(sample_umf, k=1)
        assert idx._loaded
        assert len(results) == 1
