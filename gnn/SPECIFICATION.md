# GNN Module — Specification for Teammate 2 (ML Engineer)

## Purpose

Predict surface finish (9-class), transparency (4-class), and color family (9-class) from a glaze's Unity Molecular Formula (UMF). These predictions feed the LLM interpreter, SDXL prompt builder, and frontend diagnostics. **No CTE or crazing risk — those are computed deterministically by the physics engine (Layer 1).**

## Contract

### Input (from `backend/app/engine/umf.py`)

A dict with 7 oxides in UMF-normalized mole fractions (fluxes sum to 1.0):

```json
{
  "SiO2": 2.184, "Al2O3": 0.336, "Na2O": 0.245, "K2O": 0.061,
  "CaO": 0.694, "MgO": 0.082, "Fe2O3": 0.005
}
```

Mapped to graph: **7 nodes** with **7 features** each:

| # | Feature | Type |
|---|---------|------|
| 0 | mol% (UMF mole fraction) | float |
| 1–4 | role one-hot [former, stabilizer, flux, colorant] | {0,1} |
| 5 | atomic_mass / 100 | float |

### Output (JSON — exactly this shape)

```json
{
  "surface_class": "glossy",
  "surface_confidence": 0.88,
  "transparency_class": "translucent",
  "transparency_confidence": 0.91,
  "color_family": "blue",
  "color_confidence": 0.72
}
```

### Output Classes

| Head | Classes |
|------|---------|
| Surface (9) | Glossy, Semi-glossy, Satin, Satin-matte, Semi-matte, Matte, Smooth Matte, Dry Matte, Stony Matte |
| Transparency (4) | Opaque, Semi-opaque, Translucent, Transparent |
| Color Family (9) | Black, Blue, Brown, Green, Gray, Orange, Purple, Red, White, Yellow |

## Data

- **Labels**: `data/glazybench/targets.json` (16,781 records) — keys: `id`, `surface`, `transparency`, `color_family`, `color_rgb`, `cone`, `atmosphere`, `prediction_confidence`
- **Input UMFs**: `data/glazybench/recipes.json` (16,781 records) — keys: `id`, `umf` dict (8 oxides), `chemical_composition` (full oxide breakdown), `ingredients`, `cone`, `atmosphere`
- **Join key**: `id` field (identical across both files)
- No parquet file exists — use the JSON directly (write a `dataset.py` converter, or adapt `backend/app/models/dataset.py`)

## Model Architecture

```
GINConv(7→128) + BN + ReLU + Dropout(0.15)
GINConv(128→128) + BN + ReLU + Dropout(0.15)
GINConv(128→128) + BN + ReLU
GlobalMeanPool || GlobalMaxPool → concat(256)
  ├── Linear(256→9)  + LogSoftmax → Surface (9-class)
  ├── Linear(256→4)  + LogSoftmax → Transparency (4-class)
  └── Linear(256→9)  + LogSoftmax → Color Family (9-class)
```

### Required changes from current `model.py`
1. **Remove** `cte_head` and `crazing_head` (these belong to Layer 1 physics engine)
2. **Add** `transparency_head` (4-class) and `color_head` (9-class)
3. **Increase** `surface_head` from 4 → 9 classes, rename class list
4. **Implement** Domain-Informed Adjacency Matrix in `gnn/adjacency.py` (edges fixed by ceramic role, not fully-connected)

### Domain-Informed Adjacency (see ARCHITECTURE.md §Layer 2)

| Role | Oxides | Connects To |
|------|--------|-------------|
| Former | SiO2, B2O3 | All stabilizers, all fluxes |
| Stabilizer | Al2O3, Fe2O3 | All formers, all fluxes |
| Flux | Na2O, K2O, CaO, MgO, ZnO, Li2O, PbO | All formers, all stabilizers |

Implement as a fixed `edge_index` tensor in `adjacency.py`, not learned. This is a hard requirement from the architecture spec.

## Training

| Setting | Value |
|---------|-------|
| Loss | CrossEntropy per head, summed: `L_surface + L_transparency + L_color` |
| Optimizer | AdamW, lr=1e-3, weight_decay=1e-5 |
| Epochs | 100 (with early stopping, patience=10) |
| Batch | 64 |
| Split | 80/10/10 stratified by surface class |
| Device | CUDA (ROCm on MI300X) or CPU fallback |
| Evaluation | Per-class accuracy, macro F1, confusion matrix per head |

## Deliverables

| # | File | What |
|---|------|------|
| 1 | `gnn/model.py` | Updated with 3 correct heads (9/4/9), no CTE/crazing |
| 2 | `gnn/adjacency.py` | Fixed edge_index builder by ceramic role |
| 3 | `gnn/train.py` | Training script reading JSON files directly |
| 4 | `gnn/dataset.py` | Dataset class that loads JSON and builds PyG Data objects |
| 5 | `gnn/inference.py` | Updated wrapper returning the correct JSON shape |
| 6 | `gnn/glaze_gnn_state.pt` | Trained weights (output) |
| 7 | `gnn/baselines.py` | XGBoost/CatBoost comparison on same features |
| 8 | `gnn/requirements.txt` | PyTorch + PyG + xgboost + catboost + pandas + pyarrow |

## Integration

The backend at `backend/app/routes/predict.py` currently calls `_mock_gnn_inference()`. Once `gnn/glaze_gnn_state.pt` exists, the route will be updated to:

```python
from gnn.inference import GNNInference

gnn = GNNInference()
gnn.load("gnn/glaze_gnn_state.pt")
result = gnn.predict(umf_oxide_dict)
```

Make sure `GNNInference.predict()` returns the exact JSON shape from the contract above. See `backend/app/routes/predict.py:66-73` for the mock it will replace.

## Evaluation Criteria

| Criterion | Target |
|-----------|--------|
| Surface accuracy (top-1) | ≥72% |
| Transparency accuracy | ≥80% |
| Color family accuracy | ≥75% |
| Inference latency | <50ms per recipe |
| GNN outperforms XGBoost/CatBoost | By ≥3% macro F1 averaged across all 3 heads |
