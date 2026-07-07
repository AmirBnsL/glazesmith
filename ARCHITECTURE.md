# GlazeSmith — Architecture Specification

> Hybrid computational engine for evaluating ceramic glaze stability.
> Built for the AMD Unicorn Track Hackathon — powered by ROCm MI300X + Fireworks AI.

---

## System Overview

GlazeSmith enforces a strict separation between deterministic thermodynamic math, neural material-property classification, algorithmic multi-objective optimization, and large language model translation. It combines five decoupled layers:

- **Layer 1 — Deterministic Physics:** CTE estimation via additive empirical coefficients (Appen table), UMF normalization, Stull chart mapping
- **Layer 2 — Graph Neural Network:** Surface finish (9-class), transparency (4-class), and color family classification trained on GlazyBench
- **Layer 3 — Pareto Optimizer:** Algorithmic multi-objective search for alternative formulations minimizing Δ_stress while maximizing target surface class
- **Layer 4 — Visual Compiler:** SDXL prompt builder conditioning on surface, transparency, and color predictions
- **Layer 5 — LLM Interpreter:** DeepSeek-V4-Flash communicating structured scientific explanations — not deriving predictions, but translating them

### Honest Scope

| Capability | How it's computed | Basis |
|-----------|------------------|-------|
| CTE | Deterministic formula (Appen coefficients) | Known ceramic science |
| Crazing risk | Δ_stress = glaze_CTE - clay_CTE | Heuristic threshold |
| Surface finish | GNN classification (9-class) | GlazyBench labels |
| Transparency | GNN classification (4-class) | GlazyBench labels |
| Color family | GNN classification (9-class) | GlazyBench labels |
| Defect analysis | LLM explanation of GNN + heuristic outputs | Communicated, not derived |

---

## Data Flow

```
User Recipe
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 1: Deterministic Physics Module (UMF Engine)           │
│  • Convert raw material masses → 47-oxide UMF array          │
│  • Compute Estimated CTE via additive empirical coefficients  │
│  • Δ_stress = Estimated_Glaze_CTE - Clay_CTE                 │
│  • Stull triaxial chart coordinates                           │
└──────────────────────────┬───────────────────────────────────┘
                           │ [UMF array, Estimated CTE, Δ_stress]
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 2: GNN Inference Module                                │
│  • Formulate 47-oxide array as graph (nodes = oxide species) │
│  • Classify surface (9-class), transparency (4-class), color │
│  • Multi-task softmax + confidence score                     │
│  • Compared against tabular baselines (XGBoost, CatBoost)    │
└──────────────────────────┬───────────────────────────────────┘
                           │ [Surface, transparency, color]
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 3: Pareto Optimizer Module                             │
│  • Multi-objective search for alternative formulations        │
│  • Minimize Δ_stress, maximize target surface probability     │
│  • Constrained: ingredient masses sum to 100%                │
└──────────────────────────┬───────────────────────────────────┘
                           │ [Optimized candidate recipe]
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 4: Visual Compiler (SDXL Prompt Builder)               │
│  • Compile GNN classes + CTE data into conditioning prompt   │
│  • SDXL generates photorealistic 512×512 tile image         │
│  • Note: visualization of surface phenotypes, not fracture   │
│    simulation                                                │
└──────────────────────────┬───────────────────────────────────┘
                           │ [Base64 render + metrics]
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 5: LLM Interpreter (DeepSeek-V4-Flash / Fireworks AI)  │
│  • Receives: UMF, Estimated CTE, Δ_stress, GNN classes,     │
│    optimized candidate recipe                                │
│  • Role: communicative interpreter, not scientific predictor │
│  • Outputs structured explanation + recipe adjustments JSON  │
└──────────────────────────────────────────────────────────────┘
```

### Step-by-Step Pipeline

1. **User inputs recipe** (raw materials + percentages) + firing params (cone, atmosphere, clay body)
2. **UMF Engine** converts recipe → normalized 47-oxide UMF array + computes Estimated CTE + Δ_stress
3. **GNN** classifies surface finish, transparency, color family from UMF graph (trained on GlazyBench)
4. **Pareto Optimizer** searches for alternative formulation minimizing Δ_stress while maximizing target surface class probability
5. **Prompt Compiler** builds SDXL conditioning prompt from GNN classes + CTE data
6. **Stable Diffusion XL** generates photorealistic fired tile image (2 sec, 20 steps, DPM++ SDE)
7. **LLM Interpreter** receives full diagnostic payload → returns structured JSON with explanation + recipe adjustments
8. **FastAPI aggregates** all outputs → single response payload → Next.js renders

---

## API Contract

### POST `/api/predict-glaze`

#### Request
```json
{
  "target_cone": 6,
  "atmosphere": "oxidation",
  "clay_body": "stoneware_buff",
  "recipe": [
    { "material": "Nepheline Syenite", "percentage": 50.0 },
    { "material": "Silica (Flint)", "percentage": 25.0 },
    { "material": "Whiting (Calcium Carbonate)", "percentage": 15.0 },
    { "material": "EPK Kaolin", "percentage": 10.0 }
  ]
}
```

#### Internal UMF State
```json
{
  "unity_molecular_formula": {
    "fluxes": { "Na2O": 0.245, "K2O": 0.061, "CaO": 0.694 },
    "stabilizers": { "Al2O3": 0.336, "Fe2O3": 0.002 },
    "formers": { "SiO2": 2.184, "B2O3": 0.000 }
  },
  "calculated_ratios": { "silica_alumina_ratio": 6.50 }
}
```

#### GNN Predictions
```json
{
  "gnn_predictions": {
    "estimated_cte": 8.64e-6,
    "target_cte_max": 7.30e-6,
    "stress_delta": 1.34e-6,
    "crazing_risk": 0.784,
    "surface_class": "glossy",
    "surface_confidence": 0.88,
    "transparency_class": "transparent_clear",
    "transparency_confidence": 0.91,
    "color_family": "blue",
    "stull_zone": "crazing_boundary"
  }
}
```

#### Response
```json
{
  "status": "success",
  "timestamp": "2026-07-07T13:25:00Z",
  "metrics": {
    "original_cte": 8.64e-6,
    "target_cte_max": 7.30e-6,
    "stress_delta": 1.34e-6,
    "crazing_risk": 0.784,
    "surface": "Glossy",
    "surface_confidence": 0.88,
    "transparency": "Transparent Clear",
    "transparency_confidence": 0.91
  },
  "stull_coordinates": {
    "x_alumina": 0.336,
    "y_silica": 2.184,
    "classification_zone": "crazing_boundary"
  },
  "remediation": {
    "explanation": "The glaze is under tensile stress due to elevated CTE (8.64e-6 vs. target 7.30e-6)...",
    "recipe_adjustments": [
      { "material": "Nepheline Syenite", "delta_percentage": -6.0, "action": "decrease" },
      { "material": "Silica (Flint)", "delta_percentage": 8.5, "action": "increase" },
      { "material": "Gillespie Borate", "delta_percentage": 4.0, "action": "introduce" }
    ],
    "expected_new_cte": 7.10e-6
  },
  "render_output_url": "data:image/png;base64,..."
}
```

---

## Project Structure

```
glazesmith/
├── ARCHITECTURE.md          ← This file
├── README.md                ← Project overview
├── .gitignore
├── docker-compose.yml       ← Multi-container orchestration
│
├── backend/
│   ├── Dockerfile           ← ROCm PyTorch base image
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py          ← FastAPI entry point
│   │   ├── config.py        ← Settings + env vars
│   │   ├── routes/
│   │   │   └── predict.py   ← /api/predict-glaze endpoint
│   │   ├── engine/
│   │   │   ├── umf.py       ← Layer 1: UMF conversion + CTE estimation
│   │   │   └── stull.py     ← Layer 1: Stull chart coordinate calculator
│   │   ├── physics/
│   │   │   └── cte.py       ← Layer 1: Deterministic CTE (Appen coefficients)
│   │   ├── models/
│   │   │   ├── schemas.py   ← Pydantic request/response schemas
│   │   │   └── dataset.py   ← GlazyBench loader
│   │   ├── agent/
│   │   │   ├── core.py      ← Layer 5: LLM interpreter orchestrator
│   │   │   ├── tools.py     ← Tool definitions for LLM
│   │   │   └── prompts.py   ← Layer 5: System prompts (interpreter role)
│   │   ├── optimizer/
│   │   │   └── pareto.py    ← Layer 3: Pareto candidate search
│   │   └── render/
│   │       └── sdxl.py      ← Layer 4: SDXL inference + prompt builder
│   └── training/
│       ├── train_gnn.py     ← Layer 2: GNN training script
│       └── data_utils.py    ← Data preparation utilities
│
├── gnn/                     ← Teammate 2 workspace (Layer 2)
│   ├── train.py             ← GIN training entry point
│   ├── model.py             ← GIN architecture (surface + transparency heads)
│   ├── inference.py         ← Low-latency inference wrapper
│   ├── baselines.py         ← XGBoost/CatBoost comparison baselines
│   └── requirements.txt
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   └── globals.css
│       ├── components/
│       │   ├── RecipeGrid.tsx     ← Spreadsheet ingredient input
│       │   ├── StullChart.tsx     ← SVG triaxial chart
│       │   ├── Diagnostics.tsx    ← CTE + crazing metrics panel
│       │   ├── GlazePreview.tsx   ← SDXL render display
│       │   └── Remediation.tsx    ← LLM explanation display
│       └── lib/
│           ├── api.ts            ← API client
│           └── types.ts          ← TypeScript types
│
├── data/
│   └── glazybench/          ← GlazyBench parquet dataset
│
└── tasks/
    ├── teammate-1-fullstack.md
    ├── teammate-2-ml-engineer.md
    └── teammate-3-gen-ai-engineer.md
```

---

## Layer Details

### Layer 1: Deterministic Physics Module

- **UMF Engine** (`engine/umf.py`): Converts raw material mass percentages → normalized Unity Molecular Formula (fluxes sum to 1.0). Supports 18+ ceramic materials with known oxide analyses.
- **CTE Estimation** (`physics/cte.py`): Computes Estimated CTE using additive empirical coefficients (Appen / Winkelmann & Schott tables). Δ_stress = Estimated_Glaze_CTE - Clay_CTE.
- **Stull Chart** (`engine/stull.py`): Maps SiO₂:Al₂O₃ ratio to Stull triaxial classification zone (glossy, satin, matte, crazing boundary, etc.).

### Layer 2: Graph Neural Network (GIN)

Trained exclusively on GlazyBench label space:
- **Input:** 7 oxide nodes × [mol%, role embedding, atomic mass] features. Fully connected edges.
- **Architecture:** 3× GINConv (hidden_dim=128) + BatchNorm + Dropout(0.15) + global mean/max pooling
- **Heads:**
  - 9-class Surface finish (glossy, satin, matte, stony matte, etc.)
  - 4-class Transparency (opaque, semi-opaque, translucent, transparent)
  - 9-class Color family (black, blue, orange, etc.)
- **Training:** 50 epochs, AdamW (lr=1e-3), CrossEntropy loss
- **Note:** GNN is compared against tabular baselines (XGBoost, CatBoost) per GlazyBench paper methodology

### Layer 3: Pareto Optimizer Module

- **Objective function:** Minimize Δ_stress while maximizing target surface class probability
- **Search:** Genetic/evolutionary or grid search over formulation space
- **Constraints:** Ingredient masses must sum to 100%, each ingredient within [0%, 100%]
- **Output:** Optimized alternative recipe with projected metrics

### Layer 4: Visual Compiler (SDXL)

- **Model:** stabilityai/stable-diffusion-xl-base-1.0
- **Scheduler:** DPMSolverMultistepScheduler (20 steps)
- **Conditioning:** Dynamic prompt compiled from GNN surface/transparency classes + CTE data
- **Resolution:** 512×512
- **Latency target:** < 2 seconds on MI300X
- **Memory:** ~7 GB VRAM (FP16)
- **Honest scope:** The generated image is an informed visualization of surface phenotypes, not a physical fracture or CTE simulation.

### Layer 5: LLM Interpreter (DeepSeek-V4-Flash)

- **Model:** DeepSeek-V4-Flash via Fireworks AI (serverless)
- **Role:** Communicative interpreter only — never derives scientific predictions
- **Inputs:** Original recipe, UMF data, Estimated CTE + Δ_stress, GNN classifications, optimized candidate recipe
- **Outputs:** Structured JSON with chemical explanation + material delta suggestions
- **Mode:** JSON structured output with strict schema enforcement
- **System prompt:** Scientific communicator with ceramic chemistry knowledge

---

## Hardware Strategy

| Component | Hardware | Notes |
|-----------|----------|-------|
| GNN inference | AMD MI300X (ROCm) | Co-located in VRAM alongside SDXL |
| SDXL inference | AMD MI300X (ROCm) | 7 GB FP16, DPM++ scheduler |
| LLM reasoning | Fireworks AI API | Serverless, no GPU needed |
| Pareto optimizer | CPU | Lightweight search algorithm |
| Backend | CPU (FastAPI) | Stateless, handles routing |
| Frontend | CPU (Next.js) | Static export or lightweight server |

The MI300X's 192 GB HBM3 allows co-locating GNN + SDXL + preprocessing in VRAM simultaneously, eliminating model swap latency.

---

## Team Roles

| Role | Person | Responsibilities |
|------|--------|------------------|
| Full-Stack Engineer | Teammate 1 | Next.js UI, FastAPI routes, UMF engine, Stull chart, integration |
| ML Engineer | Teammate 2 | GNN (surface/transparency/color), GlazyBench, tabular baselines, ROCm training |
| Gen AI Engineer | Teammate 3 | LLM interpreter prompts, SDXL pipeline, Pareto optimizer, image generation |

---

## Daily Sync Checkpoints

| Day | Anchor | Purpose |
|-----|--------|---------|
| End of Day 1 | Schema Lock | Agree on UMF + GNN + response JSON shape |
| End of Day 2 | API Mocking | Mock GNN + CTE so all layers can be tested independently |
| End of Day 3 | Hardware Co-Location | GNN + SDXL together in VRAM, E2E test |
| End of Day 4 | Freeze + Pitch | Code freeze, screen recording, submission |
