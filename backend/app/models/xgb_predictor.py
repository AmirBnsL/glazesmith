"""XGBoost predictor for glaze properties.

Loads 3 trained models + label encoders, exposes a predict() function
that converts UMF + metadata into surface/transparency/color predictions.
"""

from __future__ import annotations
import os
import pickle
import numpy as np
import xgboost as xgb

MODELS_DIR = os.path.join(os.path.dirname(__file__))
UMF_OXIDES = [
    "Al2O3", "B2O3", "BaO", "CaO", "Cr2O3", "Fe2O3", "K2O", "Li2O",
    "MgO", "Na2O", "P2O5", "PbO", "SiO2", "SnO2", "SrO", "TiO2", "ZnO", "ZrO2",
]
HEADS = ["surface", "transparency", "color_family"]


class XGBPredictor:
    def __init__(self):
        self.models: dict = {}
        self.label_encoders: dict = {}
        self._loaded = False

    def load(self, models_dir: str = MODELS_DIR):
        le_path = os.path.join(models_dir, "label_encoders.pkl")
        with open(le_path, "rb") as f:
            self.label_encoders = pickle.load(f)

        for head in HEADS:
            model_path = os.path.join(models_dir, f"xgb_{head}.pkl")
            with open(model_path, "rb") as f:
                self.models[head] = pickle.load(f)

        self._loaded = True

    def _build_features(self, umf_dict: dict, cone_min: float = 6.0, cone_max: float = 6.0, atmosphere: str = "oxidation") -> np.ndarray:
        parts = umf_dict.get("unity_molecular_formula", {})
        flat = {}
        for group in ("fluxes", "stabilizers", "formers", "others"):
            flat.update(parts.get(group, {}))

        vec = [flat.get(ox, 0.0) for ox in UMF_OXIDES]
        vec.append(1.0 if "oxidation" in (atmosphere or "").lower() else 0.0)
        vec.append(1.0 if "reduction" in (atmosphere or "").lower() else 0.0)
        vec.append(float(cone_min or 6.0))
        vec.append(float(min(cone_max or 6.0, 22)))
        return np.array([vec], dtype=np.float32)

    def predict(self, umf_dict: dict, cone_min: float = 6.0, cone_max: float = 6.0, atmosphere: str = "oxidation") -> dict:
        if not self._loaded:
            self.load()

        features = self._build_features(umf_dict, cone_min, cone_max, atmosphere)
        result = {}

        for head in HEADS:
            model = self.models[head]
            le = self.label_encoders[head]

            dmat = xgb.DMatrix(features)
            proba = model.predict(dmat)

            if proba.ndim > 1:
                pred_idx = int(np.argmax(proba, axis=1)[0])
                confidence = round(float(proba[0][pred_idx]), 4)
            else:
                pred_idx = int(proba[0])
                confidence = 0.0

            class_name = le.inverse_transform([pred_idx])[0]

            result[f"{head}_class"] = class_name
            result[f"{head}_confidence"] = confidence

        return result

    def predict_top_k(self, umf_dict: dict, head: str, k: int = 3, cone_min: float = 6.0, cone_max: float = 6.0, atmosphere: str = "oxidation") -> list[dict]:
        if not self._loaded:
            self.load()

        features = self._build_features(umf_dict, cone_min, cone_max, atmosphere)
        model = self.models[head]
        le = self.label_encoders[head]

        dmat = xgb.DMatrix(features)
        proba = model.predict(dmat)
        if proba.ndim == 1:
            proba = proba.reshape(1, -1)
        top_indices = np.argsort(proba[0])[::-1][:k]

        return [
            {"class": le.inverse_transform([idx])[0], "confidence": round(float(proba[0][idx]), 4), "rank": rank + 1}
            for rank, idx in enumerate(top_indices)
        ]


xgb_predictor = XGBPredictor()
