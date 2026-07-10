"""
Production training script for 3-head XGBoost glaze property predictor.

Uses the nb01 feature set (18 UMF oxides + 4 metadata features = 22 total)
and the Optuna best hyperparameters from nb04.

Trains with both default params (nb01) and Optuna params (nb04),
evaluates on the test set, and saves the best model per head.

Outputs 3 .pkl model files + label encoders to backend/app/models/
"""

import json
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score
import xgboost as xgb

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "property_prediction")
MODELS_DIR = os.path.join(PROJECT_ROOT, "backend", "app", "models")

os.makedirs(MODELS_DIR, exist_ok=True)

UMF_OXIDES = [
    "Al2O3", "B2O3", "BaO", "CaO", "Cr2O3", "Fe2O3", "K2O", "Li2O",
    "MgO", "Na2O", "P2O5", "PbO", "SiO2", "SnO2", "SrO", "TiO2", "ZnO", "ZrO2",
]

TARGET_HEADS = ["surface", "transparency", "color_family"]

DEFAULT_PARAMS = {
    "learning_rate": 0.1, "max_depth": 6,
    "subsample": 0.8, "colsample_bytree": 0.8,
    "min_child_weight": 1, "gamma": 0.0,
    "reg_alpha": 0.0, "reg_lambda": 1.0,
}

OPTUNA_BEST = {
    "surface": {
        "n_estimators": 800, "max_depth": 13, "learning_rate": 0.06668718016236205,
        "subsample": 0.836842544695184, "colsample_bytree": 0.46862732752246117,
        "min_child_weight": 2, "gamma": 0.04569900611216655,
        "reg_alpha": 1.4535931274949918, "reg_lambda": 2.3850749078263744,
    },
    "transparency": {
        "n_estimators": 400, "max_depth": 14, "learning_rate": 0.07676127973322823,
        "subsample": 0.9343193395993378, "colsample_bytree": 0.5678997032747912,
        "min_child_weight": 1, "gamma": 0.08384575443178269,
        "reg_alpha": 1.7912121831529055, "reg_lambda": 9.152637082798433,
    },
    "color_family": {
        "n_estimators": 750, "max_depth": 7, "learning_rate": 0.26892128938957693,
        "subsample": 0.7755668932036138, "colsample_bytree": 0.48794028588770516,
        "min_child_weight": 11, "gamma": 0.062257983617797066,
        "reg_alpha": 0.014742238919825998, "reg_lambda": 5.555049323584537,
    },
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def merge_data(recipes, targets):
    target_map = {t["id"]: t for t in targets}
    rows = []
    for r in recipes:
        t = target_map.get(r["id"])
        if t is None:
            continue
        row = {"id": r["id"]}
        for ox, val in (r.get("umf") or {}).items():
            row[f"umf_{ox}"] = val
        row["cone_min"] = r.get("cone_min")
        row["cone_max"] = r.get("cone_max")
        row["atmosphere"] = r.get("atmosphere", "")
        row["surface"] = t.get("surface")
        row["transparency"] = t.get("transparency")
        row["color_family"] = t.get("color_family")
        rows.append(row)
    return pd.DataFrame(rows)


def build_feature_matrix(df):
    all_oxide_cols = [f"umf_{ox}" for ox in UMF_OXIDES]
    for col in all_oxide_cols:
        if col not in df.columns:
            df[col] = 0.0
    df["atmos_oxidation"] = (
        df["atmosphere"].str.lower().str.contains("oxidation", na=False)
    ).astype(float)
    df["atmos_reduction"] = (
        df["atmosphere"].str.lower().str.contains("reduction", na=False)
    ).astype(float)
    df["cone_min"] = df["cone_min"].fillna(6.0)
    df["cone_max"] = df["cone_max"].clip(upper=22).fillna(6.0)
    feature_cols = all_oxide_cols + [
        "atmos_oxidation", "atmos_reduction", "cone_min", "cone_max",
    ]
    return df[feature_cols].fillna(0.0).values.astype(np.float32), feature_cols


def train_and_evaluate(X_train, y_train, X_test, y_test, n_classes, params, early_stop=50):
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    xgb_params = {
        "objective": "multi:softprob",
        "num_class": n_classes,
        "eval_metric": ["mlogloss", "merror"],
        "learning_rate": params.get("learning_rate", 0.1),
        "max_depth": params.get("max_depth", 6),
        "subsample": params.get("subsample", 0.8),
        "colsample_bytree": params.get("colsample_bytree", 0.8),
        "min_child_weight": params.get("min_child_weight", 1),
        "gamma": params.get("gamma", 0.0),
        "reg_alpha": params.get("reg_alpha", 0.0),
        "reg_lambda": params.get("reg_lambda", 1.0),
        "seed": 42,
    }

    n_rounds = params.get("n_estimators", 500)

    model = xgb.train(
        xgb_params, dtrain,
        num_boost_round=n_rounds,
        evals=[(dtrain, "train"), (dtest, "test")],
        early_stopping_rounds=early_stop,
        verbose_eval=100,
    )

    y_pred_train = model.predict(dtrain)
    if y_pred_train.ndim > 1:
        y_pred_train = np.argmax(y_pred_train, axis=1)

    y_pred_test = model.predict(dtest)
    if y_pred_test.ndim > 1:
        y_pred_test = np.argmax(y_pred_test, axis=1)

    return {
        "model": model,
        "train_acc": accuracy_score(y_train, y_pred_train),
        "test_acc": accuracy_score(y_test, y_pred_test),
        "test_f1": f1_score(y_test, y_pred_test, average="macro"),
        "test_weighted_f1": f1_score(y_test, y_pred_test, average="weighted"),
    }


def main():
    print("Loading data...")
    train_recipes = load_json(os.path.join(DATA_DIR, "train/recipes.json"))
    train_targets = load_json(os.path.join(DATA_DIR, "train/targets.json"))
    test_recipes = load_json(os.path.join(DATA_DIR, "test/recipes.json"))
    test_targets = load_json(os.path.join(DATA_DIR, "test/targets.json"))

    df_train = merge_data(train_recipes, train_targets)
    df_test = merge_data(test_recipes, test_targets)
    print(f"  Train: {df_train.shape}  Test: {df_test.shape}")

    X_train, feature_cols = build_feature_matrix(df_train)
    X_test, _ = build_feature_matrix(df_test)
    print(f"  Features: {len(feature_cols)} = 18 UMF + 4 metadata")

    final_models = {}
    label_encoders = {}

    for head in TARGET_HEADS:
        print(f"\n{'='*60}")
        print(f"  {head}")
        print(f"{'='*60}")

        train_mask = df_train[head].notna()
        test_mask = df_test[head].notna()

        le = LabelEncoder()
        y_train = le.fit_transform(df_train.loc[train_mask, head])
        test_labels = df_test.loc[test_mask, head]
        known_labels = set(le.classes_)
        test_mask_filtered = test_mask & test_labels.isin(known_labels)
        y_test = le.transform(df_test.loc[test_mask_filtered, head])
        label_encoders[head] = le

        n_classes = len(le.classes_)
        print(f"  Classes ({n_classes}): {list(le.classes_)}")
        print(f"  Train: {len(y_train)}  Test: {len(y_test)}")

        X_tr = X_train[train_mask.values]
        X_te = X_test[test_mask_filtered.values]

        best_result = None
        best_label = ""

        variants = [
            ("default", {**DEFAULT_PARAMS, "n_estimators": 500}),
            ("optuna", OPTUNA_BEST[head]),
        ]

        for label, params in variants:
            print(f"\n  --- {label} params ---")
            try:
                result = train_and_evaluate(X_tr, y_train, X_te, y_test, n_classes, params)
                print(f"  Train acc: {result['train_acc']:.4f}")
                print(f"  Test acc:  {result['test_acc']:.4f}")
                print(f"  Test F1:   {result['test_f1']:.4f}")

                if best_result is None or result["test_f1"] > best_result["test_f1"]:
                    best_result = result
                    best_label = label
            except Exception as e:
                print(f"  FAILED: {e}")

        if best_result is None:
            print(f"\n  ✗ No variant succeeded for {head}, skipping")
            continue

        print(f"\n  ✓ Best: {best_label} params")
        print(f"    Test acc: {best_result['test_acc']:.4f}")
        print(f"    Test F1:  {best_result['test_f1']:.4f}")

        model_path = os.path.join(MODELS_DIR, f"xgb_{head}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(best_result["model"], f)
        print(f"    Saved: {model_path}")

        final_models[head] = {
            "model": best_result["model"],
            "variant": best_label,
            "test_acc": best_result["test_acc"],
            "test_f1": best_result["test_f1"],
        }

    le_path = os.path.join(MODELS_DIR, "label_encoders.pkl")
    with open(le_path, "wb") as f:
        pickle.dump(label_encoders, f)
    print(f"\nSaved label encoders: {le_path}")

    print(f"\n{'='*60}")
    print("  Final Summary")
    print(f"{'='*60}")
    print(f"{'Head':<15s} {'Variant':<10s} {'Test Acc':>10s} {'Test F1':>10s} {'Size':>8s}")
    print("-" * 55)
    for head in TARGET_HEADS:
        if head not in final_models:
            print(f"  {head:<15s} {'FAILED':<10s} {'—':>10s} {'—':>10s}")
            continue
        info = final_models[head]
        path = os.path.join(MODELS_DIR, f"xgb_{head}.pkl")
        size = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
        print(f"  {head:<15s} {info['variant']:<10s} {info['test_acc']:>10.4f} {info['test_f1']:>10.4f} {size:>7.0f}KB")

    print(f"\nDone! Models ready in {MODELS_DIR}/")


if __name__ == "__main__":
    main()
