# GlazeSmith — Architecture Specification

> Hybrid computational engine for evaluating ceramic glaze stability.
> Built for the AMD Unicorn Track Hackathon — powered by ROCm MI300X + Fireworks AI.

---

## System Overview

GlazeSmith enforces a strict separation between deterministic thermodynamic math, neural material-property classification, empirical nearest-neighbour retrieval, algorithmic multi-objective optimization, and large language model translation. It combines seven decoupled layers:

- **Layer 1 — Deterministic Physics:** CTE estimation via additive empirical coefficients (Appen table), UMF normalization, Stull chart as geometric rendering utility
- **Layer 2 — XGBoost Classifiers:** Surface finish (14-class), transparency (4-class), and color family (14-class) classification trained on GlazyBench labels using 22 features (18 UMF oxides + 4 metadata)
- **Layer 2b — K-NN Vector Retrieval:** Cosine similarity search (Faiss) over the 18-oxide UMF vector against the GlazyBench corpus, returning the 10 nearest real-world neighbour recipes and their community annotations
- **Layer 3 — Pareto Optimizer:** Constrained grid search over the top 3 primary variable inputs, minimizing Δ_stress while maximizing target surface class probability
- **Layer 4 — Visual Compiler:** SDXL prompt builder conditioning on surface, transparency, and color predictions; output is an AI-generated visualization structurally consistent with predicted glaze phenotypes — not a physical fracture or CTE simulation
- **Layer 5 — LLM Interpreter:** DeepSeek-V4-Flash communicating structured scientific explanations — not deriving predictions, but translating them
- **Layer 6 — Verification Loop:** Each LLM-proposed recipe adjustment is run through the real physics + ML pipeline to produce verified CTE, surface, and crazing risk metrics before being shown to the user
- **Layer 7 — Interactive Chat:** Conversational turns grounded in the glaze diagnostic context; user can ask follow-up questions or request "what if" scenarios, with each proposed change verified through the real pipeline

### Honest Scope

| Capability | How it's computed | Basis |
|-----------|------------------|-------|
| CTE | Deterministic formula (Appen coefficients) | Known ceramic science |
| Crazing risk tier | Δ_stress = glaze_CTE - clay_CTE mapped to Low/Moderate/High/Extreme | Heuristic threshold tiers |
| Surface finish | XGBoost classification (14-class) | GlazyBench labels |
| Transparency | XGBoost classification (4-class) | GlazyBench labels |
| Color family | XGBoost classification (14-class) | GlazyBench labels |
| K-NN neighbours | Cosine similarity on 18-oxide UMF vector | GlazyBench corpus |
| Defect analysis | LLM explanation of XGBoost + heuristic + neighbour outputs | Communicated, not derived |
| Recipe verification | Each proposed adjustment run through the full pipeline | Real computation, not LLM prediction |
| Chat responses | LLM grounded in pre-computed diagnostics + verified adjustments | Communicated, not derived |

---

## Data Flow

```
User Recipe
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 1: Deterministic Physics Module (UMF Engine)           │
│  • Convert raw material masses → 18-oxide UMF array          │
│  • Compute CTE via additive empirical coefficients           │
│  • Δ_stress = Estimated_Glaze_CTE - Clay_CTE                 │
│  • Map crazing risk tier from Δ_stress thresholds            │
│  • Stull chart coordinates (geometric rendering utility)     │
└──────────────────────────┬───────────────────────────────────┘
                          │ [UMF array, CTE, Δ_stress, risk tier, Stull]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 2: XGBoost Classification Module                       │
│  • 18 UMF oxides + atmosphere one-hot + cone range = 22 feat │
│  • 3 independent models: surface (14), transparency (4),     │
│    color (14) — Optuna-tuned hyperparameters                 │
│  • Each model outputs class + confidence score               │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Class predictions + confidence]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 2b: K-NN Vector Retrieval Module                       │
│  • Index GlazyBench formulations by 18-oxide UMF vector      │
│  • Cosine similarity search (Faiss)                          │
│  • Return 10 nearest real-world neighbour recipes            │
│  • Include community firing notes + metadata                 │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Neighbour recipes + metadata]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 3: Pareto Optimizer Module                             │
│  • Constrained Grid Search over top 3 primary variables      │
│  • Minimize Δ_stress, maximize target surface probability    │
│  • Ingredient masses sum to 100%, each within [0, 100]      │
│  • Target: <200ms total sequential evaluation                │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Optimized candidate recipes]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 4: Visual Compiler (SDXL Prompt Builder)               │
│  • Compile XGBoost classes + CTE data into conditioning      │
│  • SDXL generates 512×512 tile visualization                 │
│  • Output is AI-generated visualization structurally         │
│    consistent with predicted glaze phenotypes                │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Base64 render + metrics]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 5: LLM Interpreter (DeepSeek-V4-Flash / Fireworks AI)  │
│  • Receives: UMF, CTE, Δ_stress, risk tier, XGBoost classes,│
│    neighbour recipes, optimized candidates                   │
│  • Role: communicative interpreter, not scientific predictor │
│  • Outputs structured explanation + recipe adjustments JSON  │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Proposed adjustments]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 6: Verification Loop                                   │
│  • Each proposed adjustment applied to recipe                │
│  • Modified recipe run through full pipeline (UMF→CTE→XGB)  │
│  • Verified CTE, surface, crazing risk attached to each adj  │
│  • LLM reviews verified results, labels "recommended" or not │
└──────────────────────────┬───────────────────────────────────┘
                          │ [Verified adjustments + analysis]
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Layer 7: Interactive Chat                                    │
│  • User asks follow-up questions or "what if" scenarios      │
│  • LLM grounded in full diagnostic context + history         │
│  • Proposed changes verified through Layer 6 pipeline        │
│  • Verified results returned inline in chat response         │
└──────────────────────────────────────────────────────────────┘
```

### Step-by-Step Pipeline

1. **User inputs recipe** (raw materials + percentages) + firing params (cone, atmosphere, clay body)
2. **UMF Engine** converts recipe → normalized 18-oxide UMF array + computes CTE + Δ_stress + maps crazing risk tier + Stull coordinates
3. **XGBoost classifiers** predict surface finish, transparency, color family from 22-feature vector (18 UMF oxides + 4 metadata)
4. **K-NN Retriever** queries the 18-oxide UMF vector against the GlazyBench index via cosine similarity → returns 10 nearest real-world neighbour recipes with community metadata
5. **Pareto Optimizer** performs a constrained grid search over top 3 primary variable inputs to find alternative formulations
6. **Prompt Compiler** builds SDXL conditioning prompt from XGBoost classes + CTE data
7. **Stable Diffusion XL** generates visualization structurally consistent with predicted glaze phenotypes
8. **LLM Interpreter** receives full diagnostic payload → returns structured JSON with explanation + recipe adjustments
9. **Verification Loop** runs each adjustment through the real pipeline → verified metrics attached
10. **LLM reviews** verified results → final recommendation with real CTE/surface/crazing values
11. **FastAPI aggregates** all outputs → single response payload → Next.js renders
12. **Chat** (optional) — user continues conversation, each turn grounded in diagnostics and verified through pipeline

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
    { "material": "Silica (325 mesh)", "percentage": 25.0 },
    { "material": "Whiting", "percentage": 15.0 },
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
    "formers": { "SiO2": 2.184 }
  },
  "calculated_ratios": { "silica_alumina_ratio": 6.50 }
}
```

#### Physics Engine Outputs (Layer 1 — Deterministic)
```json
{
  "cte": 8.64e-6,
  "stress_delta": 1.34e-6,
  "crazing_risk": 0.67,
  "stull_coordinates": {
    "x_alumina": 0.336,
    "y_silica": 2.184,
    "classification_zone": "crazing_boundary"
  }
}
```

#### XGBoost Inference Outputs (Layer 2 — Learned Classification)
```json
{
  "surface_class": "glossy",
  "surface_confidence": 0.88,
  "transparency_class": "transparent_clear",
  "transparency_confidence": 0.91,
  "color_family": "blue",
  "color_confidence": 0.72
}
```

#### K-NN Retrieval Outputs (Layer 2b — Empirical Nearest Neighbours)
```json
{
  "nearest_neighbours": [
    {
      "rank": 1,
      "cosine_similarity": 0.94,
      "recipe_name": "Glazy #12345",
      "surface": "glossy",
      "transparency": "translucent",
      "color_family": "blue",
      "community_notes": "Cone 6, oxidation"
    }
  ]
}
```

#### Aggregated Response
```json
{
  "status": "success",
  "timestamp": "2026-07-12T13:25:00Z",
  "metrics": {
    "original_cte": 8.64e-6,
    "target_cte_max": 7.30e-6,
    "crazing_risk": 0.67,
    "finish": "glossy",
    "transparency": "transparent_clear",
    "color_family": "blue"
  },
  "stull_coordinates": {
    "x_alumina": 0.336,
    "y_silica": 2.184,
    "classification_zone": "crazing_boundary"
  },
  "nearest_neighbours": [ ... ],
  "optimizer_candidates": [
    {
      "recipe": [ ... ],
      "stress_delta": 0.42e-6,
      "surface_class": "glossy",
      "surface_confidence": 0.91,
      "score": 0.87
    }
  ],
  "remediation": {
    "chemical_analysis": "The glaze is under tensile stress — CTE 8.64e-6 exceeds the stoneware target of 7.30e-6 by 1.34e-6, classified as High crazing risk. The XGBoost model predicts a glossy surface consistent with the elevated SiO2:Al2O3 ratio of 6.5. The nearest empirical analogue (Glazy #12345, similarity 0.94) confirms this formulation space is viable with adjustments.",
    "recipe_adjustments": [
      {
        "material": "Nepheline Syenite",
        "delta_percentage": -6.0,
        "action": "decrease",
        "verified_cte": 7.82e-6,
        "verified_surface": "glossy",
        "verified_crazing_risk": 0.34,
        "recommendation": "recommended"
      }
    ],
    "expected_new_cte": 7.10e-6,
    "verification_summary": "Verified 3 adjustments: 2 recommended, 1 not recommended."
  }
}
```

### POST `/api/chat`

#### Request
```json
{
  "message": "What if I increase silica by 5%?",
  "history": [
    { "role": "assistant", "content": "The glaze is under tensile stress..." }
  ],
  "recipe": [
    { "material": "Nepheline Syenite", "percentage": 50.0 },
    { "material": "Silica (325 mesh)", "percentage": 25.0 }
  ],
  "context": {
    "metrics": { "original_cte": 8.64e-6, "finish": "glossy" },
    "stull_coordinates": { "classification_zone": "crazing_boundary" },
    "remediation": { "chemical_analysis": "...", "recipe_adjustments": [] },
    "nearest_neighbours": [],
    "optimizer_candidates": []
  }
}
```

#### Response
```json
{
  "reply": "Increasing silica by 5% would bring the CTE closer to the target. I've verified this through the pipeline...",
  "verified_adjustments": [
    {
      "material": "Silica (325 mesh)",
      "delta_percentage": 5.0,
      "action": "increase",
      "verified_cte": 7.45e-6,
      "verified_surface": "glossy",
      "verified_crazing_risk": 0.08,
      "recommendation": "recommended"
    }
  ],
  "verification_summary": "Verified 1 adjustment: 1 recommended, 0 not recommended."
}
```

---

## Project Structure

```
GlazeSmith/
├── ARCHITECTURE.md              ← This file
├── README.md                    ← Project overview
├── .env.example                 ← Environment variable template
├── Makefile                     ← Build/train/test shortcuts
├── docker-compose.yml           ← Multi-container orchestration
│
├── backend/
│   ├── Dockerfile               ← ROCm PyTorch base image
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── config.py            ← Settings + env vars (Pydantic)
│   │   ├── routes/
│   │   │   ├── predict.py       ← POST /api/predict-glaze
│   │   │   └── chat.py          ← POST /api/chat
│   │   ├── engine/
│   │   │   ├── pipeline.py      ← Shared evaluation pipeline
│   │   │   ├── umf.py           ← Layer 1: UMF conversion
│   │   │   └── stull.py         ← Layer 1: Stull chart geometry
│   │   ├── models/
│   │   │   ├── schemas.py       ← Pydantic request/response schemas
│   │   │   └── xgb_predictor.py ← Layer 2: XGBoost 3-head predictor
│   │   ├── retrieval/
│   │   │   └── knn.py           ← Layer 2b: Faiss K-NN index
│   │   ├── agent/
│   │   │   ├── core.py          ← Layers 5-6: LLM + verification loop
│   │   │   ├── tools.py         ← Pipeline tool for LLM verification
│   │   │   └── prompts.py       ← Layer 5: System prompts + context
│   │   ├── optimizer/
│   │   │   └── pareto.py        ← Layer 3: Constrained grid search
│   │   ├── render/
│   │   │   └── sdxl.py          ← Layer 4: SDXL prompt builder
│   │   └── data/
│   │       └── hf_loader.py     ← HuggingFace GlazyBench loader
│   └── training/
│       └── train_production.py  ← XGBoost classifier training
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx         ← Main UI with recipe, diagnostics, chat
│       │   └── globals.css
│       ├── components/
│       │   ├── RecipeGrid.tsx   ← Ingredient spreadsheet
│       │   ├── StullChart.tsx   ← SVG triaxial chart render
│       │   ├── Diagnostics.tsx  ← CTE + crazing tier panel
│       │   ├── Neighbours.tsx   ← K-NN neighbour recipes panel
│       │   ├── GlazePreview.tsx ← SDXL render display
│       │   ├── Remediation.tsx  ← LLM verified adjustments display
│       │   └── ChatPanel.tsx    ← Layer 7: Interactive chat UI
│       └── lib/
│           ├── api.ts           ← API client functions
│           └── types.ts         ← TypeScript interfaces
│
├── gnn/                         ← Experimental GNN module (alternative to XGBoost)
│   ├── model.py                 ← GlazeGNN architecture (GIN)
│   ├── inference.py             ← Low-latency inference wrapper
│   ├── train.py                 ← GIN training script
│   ├── SPECIFICATION.md         ← GNN module spec
│   └── requirements.txt
│
├── sdxl-service/                ← Standalone SDXL image generation
│   ├── app.py                   ← FastAPI SDXL service
│   ├── Dockerfile               ← ROCm base image
│   └── requirements.txt
│
├── data/
│   ├── materials.json           ← 77-material ceramic database
│   ├── glazybench/              ← Faiss index + metadata
│   └── property_prediction/     ← GlazyBench train/test splits
│
├── notebooks/
│   ├── 01_baseline_xgboost.ipynb
│   ├── 02_gnn_gin.ipynb
│   ├── 03_multitask_mlp.ipynb
│   ├── 04_xgboost_smote.ipynb
│   └── 05_cgan_sd15_condition_mlp.ipynb
│
├── scripts/
│   ├── scrape_digitalfire.py
│   ├── finalize_materials.py
│   └── cleanup_materials.py
│
└── tasks/
    ├── teammate-1-fullstack.md
    ├── teammate-2-ml-engineer.md
    └── teammate-3-gen-ai-engineer.md
```

---

## Layer Details

### Layer 1: Deterministic Physics Module

- **UMF Engine** (`engine/umf.py`): Converts raw material mass percentages → normalized 18-oxide Unity Molecular Formula (fluxes sum to 1.0). Supports 77+ ceramic materials with known oxide analyses from the Digitalfire database. Uses `data/materials.json` for oxide compositions.
- **CTE Computation** (`engine/pipeline.py`): Computes CTE using additive empirical coefficients (Appen / Winkelmann & Schott tables). Δ_stress = Glaze_CTE - Clay_CTE. Outputs are deterministic — no ML involved.
- **Crazing Risk** (`engine/pipeline.py`): Δ_stress mapped to a continuous risk score: `min(Δ_stress / (2 × target_CTE), 1.0)`.
- **Stull Chart** (`engine/stull.py`): Geometric mapping of SiO₂:Al₂O₃ ratio to Stull triaxial classification zone (glossy, satin, matte, etc.). Deterministic geometric mapping, not a predictive model.

### Layer 2: XGBoost Classifiers (Production)

Three independently trained XGBoost classifiers, one per prediction head. This is the production classifier used in the live system.

- **Input:** 22 features = 18 UMF oxide mole fractions + atmosphere one-hot (2) + cone_min + cone_max
- **Models:** 3 separate XGBoost models trained with Optuna-tuned hyperparameters
- **Heads:**
  - Surface finish (14-class): Glossy, Semi-glossy, Satin, Matte, Dry Matte, Stony Matte, etc.
  - Transparency (4-class): Opaque, Semi-opaque, Translucent, Transparent
  - Color family (14-class): Black, Blue, Brown, Green, Gray, Orange, Purple, Red, White, Yellow, etc.
- **Training:** Optuna best hyperparameters per head, early stopping, CrossEntropy loss
- **Evaluation:** Per-class accuracy, macro F1, confusion matrix per head
- **Files:** `backend/app/models/xgb_predictor.py` (inference), `backend/training/train_production.py` (training)

### Layer 2 (Experimental): Graph Neural Network

An alternative GIN-based classifier exists in `gnn/` for experimental comparison. Uses 7 oxide nodes × 7 features with a Domain-Informed Adjacency Matrix. Not used in production — serves as a research alternative.

- **Architecture:** 3× GINConv (hidden_dim=128) + BatchNorm + Dropout(0.15) + global mean/max pooling
- **Heads:** Surface (9-class), CTE regression, Crazing probability
- **Spec:** `gnn/SPECIFICATION.md`

### Layer 2b: K-NN Vector Retrieval Module

- **Index:** All GlazyBench formulations (16,781 recipes) indexed by their 18-oxide UMF vector
- **Search:** Cosine similarity via Faiss (`IndexFlatIP` on L2-normalized vectors)
- **Return:** Top 10 nearest real-world neighbour recipes with:
  - Formulation and UMF vector
  - Surface/transparency/color metadata
  - Community firing notes from GlazyBench
- **Purpose:** Bridges visual simulation with empirical ground truth. Provides ceramic artists with known working recipes chemically similar to their input.
- **Build:** Auto-built from HuggingFace dataset on first load; cached to `data/glazybench/`.

### Layer 3: Pareto Optimizer Module

- **Objective function:** Minimize Δ_stress while maximizing target surface class probability
- **Search strategy:** Constrained Grid Search over the top 3 primary variable inputs (typically the materials contributing the largest oxide mass fractions). Unconstrained evolutionary search is avoided for latency reasons.
- **Constraints:** Ingredient masses must sum to 100%, each ingredient within [0%, 100%]
- **Latency target:** <200ms total for sequential physics evaluation + XGBoost inference across all grid points
- **Output:** Top-3 alternative formulations with projected CTE, Δ_stress, and surface class
- **Scoring:** `score = surface_weight × surface_match × surface_confidence - stress_weight × crazing_penalty`

### Layer 4: Visual Compiler (SDXL)

- **Model:** stabilityai/stable-diffusion-xl-base-1.0
- **Scheduler:** DPMSolverMultistepScheduler (30 steps, guidance_scale=7.5)
- **Conditioning:** Dynamic prompt compiled from XGBoost surface/transparency classes + CTE data + colour family + recipe ingredients
- **Resolution:** 512×512
- **Latency target:** < 2 seconds on MI300X
- **Memory:** ~7 GB VRAM (FP16)
- **Deployment:** Standalone FastAPI service (`sdxl-service/app.py`) with Docker, auto-downloads model on startup
- **Honest scope:** The output is an AI-generated visualization structurally consistent with predicted glaze phenotypes. It is not a physical fracture simulation, a CTE field render, or a photorealistic prediction of fired results.

### Layer 5: LLM Interpreter (DeepSeek-V4-Flash)

- **Model:** DeepSeek-V4-Flash via Fireworks AI (serverless, $0.14/$0.28 per 1M tokens)
- **Role:** Communicative interpreter only — never derives scientific predictions
- **Inputs:** Original recipe, UMF data, physics engine outputs (CTE, Δ_stress, crazing risk, Stull zone), XGBoost classifications (surface, transparency, colour) + confidence scores, K-NN nearest neighbour recipes with community notes, Pareto-optimized candidate recipes
- **Outputs:** Structured JSON with chemical explanation + material delta suggestions
- **Mode:** JSON structured output via Fireworks `response_format: {"type": "json_object"}`
- **System prompt:** Scientific communicator with ceramic chemistry knowledge; instructed to reference provided computed metrics and neighbour data rather than deriving inferences from raw chemistry

### Layer 6: Verification Loop

- **Purpose:** Ensures every LLM-proposed adjustment is grounded in real computation, not LLM hallucination
- **Process:**
  1. LLM proposes up to 5 adjustments (material, delta_percentage, action)
  2. Each adjustment applied to original recipe via `tools.py:apply_adjustment()`
  3. Modified recipe normalized to 100%
  4. Full pipeline re-run: UMF → CTE → XGBoost → K-NN via `pipeline.py:evaluate_recipe()`
  5. Verified metrics (CTE, surface, crazing risk) attached to each adjustment
  6. LLM reviews verified results in Pass 2 → labels "recommended" or "not_recommended"
- **Fallback:** If LLM fails, fallback remediation uses deterministic heuristic based on Si:Al ratio and CTE delta

### Layer 7: Interactive Chat

- **Endpoint:** `POST /api/chat`
- **Purpose:** Conversational interface on top of the agentic verify loop
- **Process:**
  1. User sends a message with conversation history + current glaze context
  2. LLM receives message grounded in full diagnostic data (CTE, surface, neighbours, optimizer candidates)
  3. If LLM proposes adjustments, they are verified through Layer 6 pipeline
  4. Verified results returned inline in chat response
  5. User can iterate: "try more silica", "what about borate?", "explain the crazing"
- **Context:** Full prediction context (metrics, stull, remediation, neighbours) injected into system prompt
- **History:** Last 20 messages retained for conversation context
- **Files:** `backend/app/routes/chat.py` (endpoint), `backend/app/agent/core.py:chat()` (method)

---

## Hardware Strategy

| Component | Hardware | Notes |
|-----------|----------|-------|
| XGBoost inference | CPU | <10ms per prediction, no GPU needed |
| K-NN index (Faiss) | AMD MI300X (ROCm) or CPU | GPU Faiss if available, CPU fallback |
| SDXL inference | AMD MI300X (ROCm) | ~7 GB FP16, DPM++ scheduler |
| LLM reasoning | Fireworks AI API | Serverless on AMD Instinct GPUs |
| Pareto optimizer | CPU | <200ms sequential evaluation |
| Backend | CPU (FastAPI) | Stateless, handles routing |
| Frontend | CPU (Next.js) | Static export or lightweight server |

The MI300X's 192 GB HBM3 allows co-locating K-NN Faiss index + SDXL + preprocessing in VRAM simultaneously, eliminating model swap latency. XGBoost inference runs entirely on CPU with negligible latency.

---

## Team Roles

| Role | Person | Responsibilities |
|------|--------|------------------|
| Full-Stack Engineer | Teammate 1 | Next.js UI, FastAPI routes, UMF engine, Stull chart, chat endpoint, integration |
| ML Engineer | Teammate 2 | XGBoost classifiers, GlazyBench, tabular baselines, Faiss index, GNN experimental module |
| Gen AI Engineer | Teammate 3 | LLM interpreter prompts, verification loop, SDXL pipeline, Pareto optimizer, chat context |

---

## Daily Sync Checkpoints

| Day | Anchor | Purpose |
|-----|--------|---------|
| End of Day 1 | Schema Lock | Agree on decoupled physics + XGBoost + K-NN + response JSON shape |
| End of Day 2 | API Mocking | Mock all layers so each teammate can develop independently |
| End of Day 3 | Hardware Co-Location | Faiss + SDXL together in VRAM, E2E test |
| End of Day 4 | Freeze + Pitch | Code freeze, screen recording, submission |
