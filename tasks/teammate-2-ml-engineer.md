# Teammate 2: Material Science ML Engineer (GNN & Data)

## Role

Own Layer 2 (GNN inference module) and Layer 1 physics integration. The GNN is trained strictly on GlazyBench's actual label space — surface finish, transparency, and color family. CTE and crazing are handled by deterministic physics (Layer 1), not ML.

## Core Tasks

### Day 1 — Data Prep & Environment Setup

- **ROCm environment:** Verify PyTorch + ROCm stack. Run `torch.cuda.is_available()`. Install PyTorch Geometric.
- **GlazyBench acquisition:** Clone from Hugging Face (`glazy/glazybench`). Explore schema: recipes, UMF matrices, firing params, property labels (surface, transparency, color). Note: GlazyBench does NOT contain CTE or crazing labels — those are handled by deterministic physics in Layer 1.
- **UMF → PyTorch Geometric graph:** Build graph conversion:
  - Nodes: 7 oxide nodes (SiO₂, Al₂O₃, Na₂O, K₂O, CaO, MgO, Fe₂O₃)
  - Features: [mol%, role_one_hot(4), atomic_mass/100]
  - Edges: Fully connected
  - Targets: Surface (9-class), transparency (4-class), color family (9-class)

#### Files to touch
- `gnn/model.py`
- `gnn/train.py`
- `backend/app/models/dataset.py`

### Day 2 — GNN Architecture & Training

- **GIN architecture** in `gnn/model.py`:
  - 3× GINConv (hidden_dim=128) + BatchNorm + Dropout(0.15)
  - Global mean + max pooling
  - Multi-head output: surface (9-class), transparency (4-class), color family (9-class)
  - **No CTE or crazing heads** — those are deterministic (Layer 1)
- **Training:** 50+ epochs on GlazyBench split. CrossEntropy loss per head. AdamW (lr=1e-3).
- **Tabular baselines:** Implement XGBoost and CatBoost baselines for comparison (per GlazyBench paper methodology, Section 4.1.1).

#### Files to touch
- `gnn/model.py`
- `gnn/train.py`
- `gnn/baselines.py`

### Day 3 — Model Serialization & Inference

- **Export:** Save trained weights as `gnn/glaze_gnn_state.pt`
- **Inference wrapper** (`gnn/inference.py`):
  - Loads weights into VRAM (ROCm device)
  - Accepts UMF array → builds graph → returns surface class + confidence, transparency class + confidence, color family
  - Target: <50ms per prediction on MI300X
- **CTE physics module:** Collaborate with Teammate 1 on `backend/app/physics/cte.py` for deterministic Appen-coefficient CTE estimation.

#### Files to touch
- `gnn/inference.py`
- `backend/app/physics/cte.py`

### Day 4 — Testing & Robustness

- **Edge case tests:**
  - Pure SiO₂ → should classify as glossy/transparent
  - High Al₂O₃ → should classify as matte/opaque
  - Known reference formulations (Leach 4321 Clear)
- **Consistency check:** 100 random formulations, verify no NaN or out-of-range outputs.
- **Benchmark:** GNN vs. XGBoost vs. CatBoost comparison table for the pitch.

## Deliverables

- `gnn/model.py` — GIN architecture (surface + transparency + color heads only)
- `gnn/train.py` — Training script with ROCm support
- `gnn/inference.py` — Low-latency inference wrapper (<50ms)
- `gnn/baselines.py` — XGBoost/CatBoost comparison baselines
- `gnn/glaze_gnn_state.pt` — Trained weights
- `backend/app/physics/cte.py` — Deterministic CTE estimation (with Teammate 1)

## GNN Architecture

```
Input: 7 nodes × 6 features
  │
  ▼
GINConv(6 → 128) + BatchNorm + ReLU + Dropout(0.15)
  │
  ▼
GINConv(128 → 128) + BatchNorm + ReLU + Dropout(0.15)
  │
  ▼
GINConv(128 → 128) + BatchNorm + ReLU
  │
  ▼
Global Mean + Max Pooling (concat → 256)
  │
  ├── Linear(256 → 9)   → Surface (softmax 9-class)
  ├── Linear(256 → 4)   → Transparency (softmax 4-class)
  └── Linear(256 → 9)   → Color family (softmax 9-class)
```

## GlazyBench Label Space (Source of Truth)

| Label | Type | Classes | Coverage |
|-------|------|---------|----------|
| Surface | Classification | 9 (Glossy, Semi-glossy, Satin, Matte, Dry Matte, Stony Matte, etc.) | 6,844 train / 3,730 test |
| Transparency | Classification | 4 (Opaque, Semi-opaque, Translucent, Transparent) | 6,584 train / 3,322 test |
| Color Family | Classification | 9 (Black, Blue, Brown, Green, Orange, Pink, Red, White, Yellow) | 12,175 train / 4,903 test |
| RGB Color | Regression | Continuous [0,255]³ | 12,175 train / 4,903 test |

**Not in GlazyBench (handled by deterministic physics):** CTE, crazing, shivering, pinholing, crawling

## ROCm Setup

```bash
# Verify ROCm
rocm-smi
python -c "import torch; print(torch.cuda.is_available())"

# Install PyTorch Geometric
pip install torch_geometric
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.4.0+rocm6.3.html
```
