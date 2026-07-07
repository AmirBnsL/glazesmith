# Teammate 2: Material Science ML Engineer (GNN & Physics)

## Role

Own data engineering on GlazyBench, GNN architecture development, and local PyTorch deployment on AMD ROCm.

## Core Tasks

### Day 1 — Data Prep & Environment Setup

- **ROCm environment:** Verify PyTorch + ROCm 7.0 stack. Run `torch.cuda.is_available()` check. Install PyTorch Geometric (`torch-geometric`).
- **GlazyBench acquisition:** Clone dataset from Hugging Face (`glazy/glazybench`). Explore schema: recipes, oxide compositions, UMF matrices, firing params, property labels (CTE, crazing, surface, transparency, color).
- **UMF → PyTorch Geometric graph:** Write `gnn/data_utils.py` that converts each normalized UMF matrix into a `torch_geometric.data.Data` object:
  - Nodes: 7 oxide nodes (SiO₂, Al₂O₃, Na₂O, K₂O, CaO, MgO, Fe₂O₃) with features [mol%, role_one_hot, atomic_mass, electronegativity]
  - Edges: Fully connected, edge features [bond_type_one_hot, electronegativity_diff]
  - Targets: CTE (float), crazing (binary), surface (4-class), transparency (3-class)

#### Files to touch
- `gnn/model.py`
- `gnn/train.py`
- `backend/training/data_utils.py`

### Day 2 — GNN Architecture & Training

- **GIN architecture:** Implement a 3-layer Graph Isomorphism Network in `gnn/model.py`:
  - `GINConv` layers with MLP (hidden_dim=128)
  - BatchNorm after each conv
  - Dropout(0.15)
  - Global mean + max pooling
  - Multi-head output: regression head (CTE), binary head (crazing), 4-class head (surface)
- **Training loop:** Train for 50+ epochs on the GlazyBench split. Log loss per head. Use AdamW (lr=1e-3, weight_decay=1e-5). Track validation metrics.
- **Loss functions:** MSE for CTE, BCE for crazing, CrossEntropy for surface.

#### Files to touch
- `gnn/model.py`
- `gnn/train.py`

### Day 3 — Model Serialization & Inference Script

- **Export:** Save trained weights as `gnn/glaze_gnn_state.pt` (state dict only).
- **Inference wrapper:** Write `gnn/inference.py` that:
  - Loads weights into VRAM (on ROCm device)
  - Accepts raw UMF matrix (list of floats)
  - Builds the graph on-the-fly
  - Returns `[cte_float, crazing_prob, surface_logits]` in under 50ms
- **Integration:** Place the inference script where the FastAPI backend can import it (`backend/app/gnn_predict.py` or similar).
- **Validation:** Compare predictions against known glaze formulations (e.g., Leach 4321 Clear should have CTE ~6.5 ×10⁻⁶/°C).

#### Files to touch
- `gnn/inference.py`
- `backend/training/train_gnn.py`

### Day 4 — Testing & Robustness

- **Edge case tests:**
  - Pure SiO₂ (should be very low CTE, no crazing)
  - Pure Nepheline Syenite (should be high CTE, high crazing risk)
  - Extremely high Al₂O₃ (should predict matte surface)
- **Performance:** Benchmark inference speed. Target: <50ms per prediction on MI300X.
- **Consistency check:** Run 100 random formulations to ensure no NaN or out-of-range outputs.

## Deliverables

- `gnn/model.py` — GIN architecture definition
- `gnn/train.py` — Training script with ROCm support
- `gnn/inference.py` — Low-latency inference wrapper (<50ms)
- `gnn/glaze_gnn_state.pt` — Trained weights
- `backend/training/data_utils.py` — GlazyBench → PyG conversion
- Validation report showing CTE within ±10% of known formulations

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
  ├── Linear(256 → 1)  → CTE (regression)
  ├── Linear(256 → 1)  → Crazing (sigmoid binary)
  └── Linear(256 → 4)  → Surface (softmax 4-class)
```

## ROCm Setup

```bash
# Verify ROCm
rocm-smi
python -c "import torch; print(torch.cuda.is_available())"

# Install PyTorch Geometric
pip install torch_geometric
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.4.0+rocm6.3.html
```
