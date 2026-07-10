"""Download and cache GlazyBench dataset from Hugging Face.

The `AlpachinoNLP/GlazyBench` dataset (property_prediction config) contains
16,781 train + 4,903 test recipes with UMF vectors and surface/transparency/color targets.
Data is downloaded at most once and cached to data/glazybench/.
"""

from __future__ import annotations
import json
import os
import urllib.request
from typing import Any

HF_BASE = "https://huggingface.co/datasets/AlpachinoNLP/GlazyBench/resolve/main/property_prediction"

HF_FILES = {
    "train_recipes": ("train/recipes.json", "train_recipes"),
    "train_targets": ("train/targets.json", "train_targets"),
    "test_recipes": ("test/recipes.json", "test_recipes"),
    "test_targets": ("test/targets.json", "test_targets"),
}

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")

DATA_DIR = os.path.join(BASE_DIR, "property_prediction")

UMF_OXIDES = [
    "SiO2", "Al2O3", "B2O3", "Li2O", "Na2O", "K2O", "MgO", "CaO",
    "SrO", "BaO", "ZnO", "TiO2", "Fe2O3", "P2O5", "SnO2", "Cr2O3",
    "ZrO2", "PbO",
]

_LEGACY_PATHS: dict[str, str] = {}


def _download(url: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(f"Warning: could not download {url}: {e}")
        raise


def _local_path(key: str) -> str:
    rel_path, _ = HF_FILES[key]
    return os.path.join(DATA_DIR, rel_path)


def _remote_url(key: str) -> str:
    rel_path, _ = HF_FILES[key]
    return f"{HF_BASE}/{rel_path}"


def _resolve_path(key: str) -> str:
    """Return the best available local path for a dataset key."""
    path = _local_path(key)
    if os.path.exists(path):
        return path
    legacy = _LEGACY_PATHS.get(key)
    if legacy and os.path.exists(legacy):
        return legacy
    return path


def ensure_downloaded(force: bool = False) -> None:
    """Download all HF dataset files to local cache if not present.

    Args:
        force: Re-download even if cached.
    """
    for key in HF_FILES:
        dest = _local_path(key)
        legacy = _LEGACY_PATHS.get(key)
        if force or not os.path.exists(dest):
            if legacy and os.path.exists(legacy) and not force:
                continue
            _download(_remote_url(key), dest)


def load_json(key: str) -> list[dict]:
    """Load a dataset file by key, returning parsed JSON.

    Tries local cache first (both HF-named and legacy paths),
    downloads from Hugging Face only if nothing cached.
    """
    path = _resolve_path(key)
    if not os.path.exists(path):
        ensure_downloaded()
        path = _local_path(key)
    with open(path) as f:
        return json.load(f)


def load_train() -> tuple[list[dict], list[dict]]:
    """Load training recipes and targets.

    Returns:
        (recipes, targets) — each is a list of dicts from JSON.
    """
    recipes = load_json("train_recipes")
    targets = load_json("train_targets")
    return recipes, targets


def load_test() -> tuple[list[dict], list[dict]]:
    """Load test recipes and targets."""
    recipes = load_json("test_recipes")
    targets = load_json("test_targets")
    return recipes, targets


def load_merged(split: str = "train") -> list[dict]:
    """Load recipes and targets merged on 'id'.

    Args:
        split: "train" or "test"

    Returns:
        List of dicts with recipe fields + target fields merged.
    """
    if split == "train":
        recipes, targets = load_train()
    else:
        recipes, targets = load_test()

    target_map = {t["id"]: t for t in targets}
    merged = []
    for r in recipes:
        t = target_map.get(r["id"])
        if t is None:
            continue
        merged.append({**r, **{k: t[k] for k in t if k != "id"}})
    return merged


def umf_dict_to_vector(umf: dict[str, float]) -> list[float]:
    """Convert a UMF dict (e.g. {'SiO2': 2.184, ...}) to an 18-dim vector.

    Oxides not present in the dict default to 0.0.
    """
    return [umf.get(ox, 0.0) for ox in UMF_OXIDES]


def known_classes() -> dict[str, list[str]]:
    """Return the known class names for each prediction head.

    Extracted from the training targets. Useful for the mock GNN and validation.
    """
    _, targets = load_train()
    classes: dict[str, set[str | None]] = {
        "surface": set(),
        "transparency": set(),
        "color_family": set(),
    }
    for t in targets:
        for head in classes:
            val = t.get(head)
            if val is not None:
                classes[head].add(val)
    return {head: sorted(v for v in vals if v is not None) for head, vals in classes.items()}
