# GlazeSmith — Architecture Specification

> AI agent for ceramic glaze formulation and defect diagnosis.
> Built for the AMD Unicorn Track Hackathon — powered by ROCm MI300X + Fireworks AI.

---

## System Overview

GlazeSmith is a hybrid AI system that predicts fired ceramic glaze properties from raw material recipes, diagnoses defects like crazing, generates photorealistic images of fired results, and suggests precise recipe adjustments. It combines:

- **Graph Neural Network (GNN)** — predicts CTE, crazing risk, surface finish from oxide structure
- **Stable Diffusion XL** — generates visual glaze renderings from predicted properties
- **Fireworks AI (Llama 3 70B)** — structured reasoning + recipe remediation via JSON schema mode
- **FastAPI orchestration** — coordinates all three models into a unified pipeline

---

## Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Next.js    │────▶│   FastAPI    │────▶│  UMF Engine  │
│  UI (React)  │◀────│  Backend     │◀────│ (Oxide Calc) │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐ ┌────────────┐ ┌──────────────┐
       │ GNN on   │ │ Fireworks  │ │ SDXL on      │
       │ ROCm     │ │ AI (Llama) │ │ ROCm         │
       │ Predict  │ │ Remediation│ │ Render Glaze │
       │ CTE/Risk │ │ + Analysis │ │ Image        │
       └──────────┘ └────────────┘ └──────────────┘
```

### Step-by-Step Pipeline

1. **User inputs recipe** (raw materials + percentages) + firing params (cone, atmosphere, clay body)
2. **UMF Engine** converts recipe → normalized Unity Molecular Formula matrix (fluxes = 1.0)
3. **GNN** predicts CTE, crazing probability, surface finish, transparency from UMF matrix
4. **Prompt Builder** compiles GNN metrics + UMF ratios into structured prompt for SDXL
5. **Stable Diffusion XL** generates photorealistic fired tile image (2 sec, 20 steps, DPM++ SDE)
6. **Fireworks AI** receives UMF + GNN metrics → returns structured JSON: analysis + deltas
7. **FastAPI aggregates** all outputs → single response payload → Next.js renders

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
    "coefficient_of_thermal_expansion": 8.64e-6,
    "crazing_risk_probability": 0.784,
    "surface_finish_logits": [0.88, 0.08, 0.03, 0.01],
    "predicted_surface_class": "glossy",
    "transparency_class": "transparent_clear"
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
    "crazing_risk": 0.784,
    "finish": "Glossy"
  },
  "stull_coordinates": {
    "x_alumina": 0.336,
    "y_silica": 2.184,
    "classification_zone": "crazing_boundary"
  },
  "remediation": {
    "explanation": "The glaze is crazing due to elevated CTE (8.64e-6)...",
    "remedy_recipe": [
      { "material": "Nepheline Syenite", "percentage": 44.0 },
      { "material": "Silica (Flint)", "percentage": 33.5 },
      { "material": "Whiting", "percentage": 15.0 },
      { "material": "EPK Kaolin", "percentage": 10.0 },
      { "material": "Gillespie Borate", "percentage": 4.0 }
    ]
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
│   │   │   ├── umf.py       ← UMF conversion (recipe → oxide matrix)
│   │   │   └── stull.py     ← Stull chart coordinate calculator
│   │   ├── models/
│   │   │   ├── schemas.py   ← Pydantic request/response schemas
│   │   │   └── dataset.py   ← GlazyBench loader
│   │   ├── agent/
│   │   │   ├── core.py      ← Fireworks AI agent orchestrator
│   │   │   ├── tools.py     ← Tool definitions for LLM
│   │   │   └── prompts.py   ← System prompts
│   │   └── render/
│   │       └── sdxl.py      ← Stable Diffusion XL inference
│   └── training/
│       ├── train_gnn.py     ← GNN training script
│       └── data_utils.py    ← Data preparation utilities
│
├── gnn/                     ← Teammate 2 workspace
│   ├── train.py             ← GIN training entry point
│   ├── model.py             ← GIN architecture definition
│   ├── inference.py         ← Low-latency inference wrapper
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
│       │   └── Remediation.tsx    ← LLM fix suggestions
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

## Neural Architecture

### GNN — Graph Isomorphism Network (GIN)

- **Input:** 7 oxide nodes × [mol%, role embedding, atomic mass] features
- **Edges:** Fully connected with edge features [bond type, electronegativity diff]
- **Layers:** 3× GINConv with BatchNorm + Dropout(0.15)
- **Heads:**
  - Regression: CTE (continuous, scaled 0–15 ×10⁻⁶/°C)
  - Binary: Crazing risk (0.0–1.0)
  - Multi-class: Surface finish (glossy/satin/matte/crystalline)
  - Multi-class: Transparency (clear/translucent/opaque)
- **Training:** 50 epochs, AdamW (lr=1e-3), MSE + CrossEntropy

### SDXL — Stable Diffusion XL

- **Model:** stabilityai/stable-diffusion-xl-base-1.0
- **Scheduler:** DPMSolverMultistepScheduler (20 steps)
- **Conditioning:** Dynamic prompt from GNN metrics (CTE, surface, crazing, color)
- **Resolution:** 512×512
- **Latency target:** < 2 seconds on MI300X
- **Memory:** ~7 GB VRAM (FP16)

### Fireworks AI Agent

- **Model:** Llama 3 70B (or DeepSeek V3)
- **Mode:** JSON structured output with strict schema enforcement
- **Tools:** predict_properties, fix_defect, calculate_cte, generate_glaze_image
- **System prompt:** Material science expert with oxide chemistry knowledge

---

## Hardware Strategy

| Component | Hardware | Notes |
|-----------|----------|-------|
| GNN inference | AMD MI300X (ROCm) | Keep in VRAM alongside SDXL |
| SDXL inference | AMD MI300X (ROCm) | 7 GB FP16, DPM++ scheduler |
| LLM reasoning | Fireworks AI API | Serverless, no GPU needed |
| Backend | CPU (FastAPI) | Stateless, handles routing |
| Frontend | CPU (Next.js) | Static export or lightweight server |

The MI300X's 192 GB HBM3 allows co-locating GNN + SDXL + preprocessing in VRAM simultaneously, eliminating model swap latency.

---

## Team Roles

| Role | Person | Responsibilities |
|------|--------|------------------|
| Full-Stack Engineer | Teammate 1 | Next.js UI, FastAPI routes, UMF engine, Stull chart, integration |
| ML Engineer | Teammate 2 | GNN architecture, GlazyBench data, ROCm training, inference |
| Gen AI Engineer | Teammate 3 | Fireworks AI prompts, JSON schema, SDXL pipeline, image generation |

---

## Daily Sync Checkpoints

| Day | Anchor | Purpose |
|-----|--------|---------|
| End of Day 1 | Schema Lock | Agree on normalized UMF JSON shape |
| End of Day 2 | API Mocking | Mock GNN outputs so T3 can test prompts |
| End of Day 3 | Hardware Co-Location | GNN + SDXL together in VRAM, E2E test |
| End of Day 4 | Freeze + Pitch | Code freeze, screen recording, submission |
