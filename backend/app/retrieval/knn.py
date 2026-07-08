"""K-NN Vector Retrieval Module (Layer 2b).

Retrieves the 5 nearest real-world GlazyBench recipes given an 18-oxide UMF vector,
using cosine similarity via Faiss.
"""

from __future__ import annotations
import json
import os
import numpy as np
import faiss

UMF_OXIDES = [
    "SiO2", "Al2O3", "B2O3", "Li2O", "Na2O", "K2O", "MgO", "CaO",
    "SrO", "BaO", "ZnO", "TiO2", "Fe2O3", "P2O5", "SnO2", "Cr2O3",
    "ZrO2", "PbO",
]

DEFAULT_INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "data", "glazybench", "glazy_index.faiss",
)
DEFAULT_METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "data", "glazybench", "glazy_metadata.json",
)


class GlazyIndex:
    """Faiss-based K-NN index for GlazyBench UMF vector retrieval."""

    def __init__(self, index_path: str = DEFAULT_INDEX_PATH, metadata_path: str = DEFAULT_METADATA_PATH):
        self.index: faiss.Index | None = None
        self.metadata: list[dict] = []
        self._loaded = False
        self._index_path = index_path
        self._metadata_path = metadata_path

    def load(self) -> None:
        if self._loaded:
            return
        if not os.path.exists(self._index_path):
            raise FileNotFoundError(f"Faiss index not found at {self._index_path}")
        if not os.path.exists(self._metadata_path):
            raise FileNotFoundError(f"Metadata not found at {self._metadata_path}")

        self.index = faiss.read_index(self._index_path)
        with open(self._metadata_path) as f:
            self.metadata = json.load(f)

        self._loaded = True

    def search(self, umf_vector: list[float], k: int = 5) -> list[dict]:
        """Query the index for k nearest neighbours by cosine similarity.

        Args:
            umf_vector: 18-oxide UMF vector in UMF_OXIDES order.
            k: Number of neighbours to return (default 5).

        Returns:
            List of dicts with rank, cosine_similarity, surface, transparency,
            color_family, recipe_name, community_notes.
        """
        if not self._loaded:
            self.load()

        if self.index is None:
            return []

        query = np.array([umf_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        distances, indices = self.index.search(query, k)

        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]

            results.append({
                "rank": rank,
                "cosine_similarity": round(float(dist), 4),
                "recipe_name": meta.get("recipe_name", f"Glazy #{meta['id']}"),
                "surface": meta.get("surface", ""),
                "transparency": meta.get("transparency", ""),
                "color_family": meta.get("color_family", ""),
                "community_notes": self._build_notes(meta),
            })

        return results

    def _build_notes(self, meta: dict) -> str:
        parts = []
        cone_min = meta.get("cone_min")
        cone_max = meta.get("cone_max")
        if cone_min or cone_max:
            parts.append(f"Cone {cone_min}-{cone_max}")
        atmosphere = meta.get("atmosphere")
        if atmosphere:
            parts.append(atmosphere)
        if not parts:
            parts.append("GlazyBench formulation")
        return ", ".join(parts)

    def umf_dict_to_vector(self, umf_dict: dict) -> list[float]:
        """Convert a UMF dict (e.g. {'SiO2': 2.184, ...}) to 18-dim vector."""
        return [umf_dict.get(ox, 0.0) for ox in UMF_OXIDES]


glazy_index = GlazyIndex()
