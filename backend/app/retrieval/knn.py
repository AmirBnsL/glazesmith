"""K-NN Vector Retrieval Module (Layer 2b).

Retrieves the 5 nearest real-world GlazyBench recipes given an 18-oxide UMF vector,
using cosine similarity via Faiss.

Index is auto-built from the Hugging Face dataset on first load,
then cached to disk as a Faiss binary index.
"""

from __future__ import annotations
import json
import os
import numpy as np
import faiss

from ..data.hf_loader import (
    UMF_OXIDES,
    umf_dict_to_vector,
    load_merged,
    ensure_downloaded,
)

INDEX_FILENAME = "glazy_index.faiss"
METADATA_FILENAME = "glazy_metadata.json"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "glazybench")

DEFAULT_INDEX_PATH = os.path.join(DATA_DIR, INDEX_FILENAME)
DEFAULT_METADATA_PATH = os.path.join(DATA_DIR, METADATA_FILENAME)


def build_index_from_hf(
    index_path: str = DEFAULT_INDEX_PATH,
    metadata_path: str = DEFAULT_METADATA_PATH,
) -> None:
    """Build a Faiss cosine-similarity index from the HF dataset.

    Downloads data if not cached locally, then builds and saves
    the index + metadata file.
    """
    ensure_downloaded()
    records = load_merged("train")

    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    vectors = []
    metadata = []
    for rec in records:
        umf = rec.get("umf", {})
        if not umf:
            continue
        vec = umf_dict_to_vector(umf)
        vectors.append(vec)
        metadata.append({
            "id": rec["id"],
            "umf_vector": vec,
            "cone_min": rec.get("cone_min"),
            "cone_max": rec.get("cone_max"),
            "atmosphere": rec.get("atmosphere", ""),
            "surface": rec.get("surface"),
            "transparency": rec.get("transparency"),
            "color_family": rec.get("color_family"),
            "color_rgb": rec.get("color_rgb"),
            "recipe_name": f"Glazy #{rec['id']}",
        })

    if len(vectors) == 0:
        raise RuntimeError("No vectors extracted from HF dataset")

    xb = np.array(vectors, dtype=np.float32)
    faiss.normalize_L2(xb)
    dim = xb.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(xb)

    faiss.write_index(index, index_path)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    print(f"Built Faiss index: {len(vectors)} vectors, dim={dim}")
    print(f"  Index: {index_path}")
    print(f"  Metadata: {metadata_path}")


class GlazyIndex:
    """Faiss-based K-NN index for GlazyBench UMF vector retrieval.

    On first load, if no cached index exists, it is automatically
    built from the Hugging Face dataset (downloads data if needed).
    """

    def __init__(
        self,
        index_path: str = DEFAULT_INDEX_PATH,
        metadata_path: str = DEFAULT_METADATA_PATH,
        auto_build: bool = True,
    ):
        self.index: faiss.Index | None = None
        self.metadata: list[dict] = []
        self._loaded = False
        self._index_path = index_path
        self._metadata_path = metadata_path
        self._auto_build = auto_build

    def load(self) -> None:
        if self._loaded:
            return

        if not os.path.exists(self._index_path) or not os.path.exists(self._metadata_path):
            if self._auto_build:
                build_index_from_hf(self._index_path, self._metadata_path)
            else:
                missing = []
                if not os.path.exists(self._index_path):
                    missing.append(self._index_path)
                if not os.path.exists(self._metadata_path):
                    missing.append(self._metadata_path)
                raise FileNotFoundError(
                    f"GlazyBench index not found. Run build_index_from_hf() first. "
                    f"Missing: {missing}"
                )

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

            def _safe(s: str | None, default: str = "") -> str:
                if s is None or str(s).lower() in ("none", "null", "unknown", ""):
                    return default
                return str(s)

            results.append({
                "rank": rank,
                "cosine_similarity": round(float(dist), 4),
                "recipe_name": meta.get("recipe_name", f"Glazy #{meta['id']}"),
                "surface": _safe(meta.get("surface")),
                "transparency": _safe(meta.get("transparency")),
                "color_family": _safe(meta.get("color_family")),
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
        return umf_dict_to_vector(umf_dict)


glazy_index = GlazyIndex()
