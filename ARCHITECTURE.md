  # GlazeSmith — Architecture Specification
  
  > Hybrid computational engine for evaluating ceramic glaze stability.
  > Built for the AMD Unicorn Track Hackathon — powered by ROCm MI300X + Fireworks AI.
  
  ---
  
  ## System Overview
  
  GlazeSmith enforces a strict separation between deterministic thermodynamic math, neural material-property classification, empirical nearest-neighbour retrieval, algorithmic multi-objective optimization, and large language model translation. It combines six decoupled layers:
  
  - **Layer 1 — Deterministic Physics:** CTE estimation via additive empirical coefficients (Appen table), UMF normalization, Stull chart as SVG geometric rendering utility
  - **Layer 2 — Graph Neural Network:** Surface finish (9-class), transparency (4-class), and color family classification trained exclusively on GlazyBench labels
  - **Layer 2b — K-NN Vector Retrieval:** Cosine similarity search (Faiss/USearch) over the 47-oxide UMF vector against the GlazyBench corpus, returning the 5 nearest real-world neighbour recipes and their community annotations
  - **Layer 3 — Pareto Optimizer:** Constrained grid search over the top 3 primary variable inputs, minimizing Δ_stress while maximizing target surface class probability
  - **Layer 4 — Visual Compiler:** SDXL prompt builder conditioning on surface, transparency, and color predictions; output is an AI-generated visualization structurally consistent with predicted glaze phenotypes — not a physical fracture or CTE simulation
  - **Layer 5 — LLM Interpreter:** DeepSeek-V4-Flash communicating structured scientific explanations — not deriving predictions, but translating them
  
  ### Honest Scope
  
  | Capability | How it's computed | Basis |
  |-----------|------------------|-------|
  | CTE | Deterministic formula (Appen coefficients) | Known ceramic science |
  | Crazing risk tier | Δ_stress = glaze_CTE - clay_CTE mapped to Low/Moderate/High/Extreme | Heuristic threshold tiers |
  | Surface finish | GNN classification (9-class) | GlazyBench labels |
  | Transparency | GNN classification (4-class) | GlazyBench labels |
  | Color family | GNN classification (9-class) | GlazyBench labels |
  | K-NN neighbours | Cosine similarity on 47-oxide UMF vector | GlazyBench corpus |
  | Defect analysis | LLM explanation of GNN + heuristic + neighbour outputs | Communicated, not derived |
  
  ---
  
  ## Data Flow
  
  ```
  User Recipe
      │
      ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Layer 1: Deterministic Physics Module (UMF Engine)           │
  │  • Convert raw material masses → 47-oxide UMF array          │
  │  • Compute CTE via additive empirical coefficients │
  │  • Δ_stress = Estimated_Glaze_CTE - Clay_CTE                 │
  │  • Map crazing risk tier from Δ_stress thresholds            │
  │  • Stull chart SVG coordinates (geometric rendering utility) │
  └──────────────────────────┬───────────────────────────────────┘
                            │ [UMF array, CTE, Δ_stress, risk tier, Stull]
                            ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Layer 2: GNN Inference Module                                │
  │  • Formulate 47-oxide array as graph with Domain-Informed    │
  │    Adjacency Matrix (edges fixed by ceramic roles)           │
  │  • Classify surface (9-class), transparency (4-class), color │
  │  • Multi-task softmax + confidence score                     │
  │  • Compared against tabular baselines (XGBoost, CatBoost)    │
  └──────────────────────────┬───────────────────────────────────┘
                            │ [GNN class logits]
                            ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Layer 2b: K-NN Vector Retrieval Module                       │
  │  • Index GlazyBench formulations by 47-oxide UMF vector      │
  │  • Cosine similarity search (Faiss / USearch)                │
  │  • Return 5 nearest real-world neighbour recipes             │
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
                            │ [Optimized candidate recipe]
                            ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Layer 4: Visual Compiler (SDXL Prompt Builder)               │
  │  • Compile GNN classes + CTE data into conditioning prompt   │
  │  • SDXL generates 512×512 tile visualization                 │
  │  • Output is AI-generated visualization structurally         │
  │    consistent with predicted glaze phenotypes                │
  └──────────────────────────┬───────────────────────────────────┘
                            │ [Base64 render + metrics]
                            ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Layer 5: LLM Interpreter (DeepSeek-V4-Flash / Fireworks AI)  │
  │  • Receives: UMF, CTE, Δ_stress, risk tier, GNN classes,    │
  │    neighbour recipes, optimized candidate                    │
  │  • Role: communicative interpreter, not scientific predictor │
  │  • Outputs structured explanation + recipe adjustments JSON  │
  └──────────────────────────────────────────────────────────────┘
  ```
  
  ### Step-by-Step Pipeline
  
  1. **User inputs recipe** (raw materials + percentages) + firing params (cone, atmosphere, clay body)
  2. **UMF Engine** converts recipe → normalized 47-oxide UMF array + computes CTE + Δ_stress + maps crazing risk tier + Stull coordinates
  3. **GNN** classifies surface finish, transparency, color family from UMF graph via Domain-Informed Adjacency Matrix (trained on GlazyBench)
  4. **K-NN Retriever** queries the 47-oxide UMF vector against the GlazyBench index via cosine similarity → returns 5 nearest real-world neighbour recipes with community metadata
  5. **Pareto Optimizer** performs a constrained grid search over top 3 primary variable inputs to find alternative formulations
  6. **Prompt Compiler** builds SDXL conditioning prompt from GNN classes + CTE data
  7. **Stable Diffusion XL** generates visualization structurally consistent with predicted glaze phenotypes (2 sec, 20 steps, DPM++ SDE)
  8. **LLM Interpreter** receives full diagnostic payload → returns structured JSON with explanation + recipe adjustments
  9. **FastAPI aggregates** all outputs → single response payload → Next.js renders
  
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
  
  #### Physics Engine Outputs (Layer 1 — Deterministic)
  ```json
  {
    "physics_engine": {
      "cte": 8.64e-6,
      "target_cte_max": 7.30e-6,
      "stress_delta": 1.34e-6,
      "crazing_risk_tier": "High",
      "stull_coordinates": {
        "x_alumina": 0.336,
        "y_silica": 2.184,
        "classification_zone": "crazing_boundary"
      }
    }
  }
  ```
  
  #### GNN Inference Outputs (Layer 2 — Learned Classification)
  ```json
  {
    "gnn_inference": {
      "surface_class": "glossy",
      "surface_confidence": 0.88,
      "transparency_class": "transparent_clear",
      "transparency_confidence": 0.91,
      "color_family": "blue",
      "color_confidence": 0.72
    }
  }
  ```
  
  #### K-NN Retrieval Outputs (Layer 2b — Empirical Nearest Neighbours)
  ```json
  {
    "nearest_neighbours": [
      {
        "rank": 1,
        "cosine_similarity": 0.94,
        "recipe_name": "Blue Celadon Base",
        "surface": "glossy",
        "transparency": "translucent",
        "color_family": "blue",
        "community_notes": "Fires well at cone 6 ox, slight variation with iron content."
      },
      {
        "rank": 2,
        "cosine_similarity": 0.91,
        "recipe_name": "Chun Style Glaze",
        "surface": "glossy",
        "transparency": "opaque",
        "color_family": "blue",
        "community_notes": "Thick application recommended. Prone to pinholing if applied thin."
      }
    ]
  }
  ```
  
  #### Aggregated Response
  ```json
  {
    "status": "success",
    "timestamp": "2026-07-07T13:25:00Z",
    "physics_engine": {
      "cte": 8.64e-6,
      "target_cte_max": 7.30e-6,
      "stress_delta": 1.34e-6,
      "crazing_risk_tier": "High"
    },
    "stull_coordinates": {
      "x_alumina": 0.336,
      "y_silica": 2.184,
      "classification_zone": "crazing_boundary"
    },
    "gnn_inference": {
      "surface_class": "glossy",
      "surface_confidence": 0.88,
      "transparency_class": "transparent_clear",
      "transparency_confidence": 0.91,
      "color_family": "blue"
    },
    "nearest_neighbours": [
      {
        "rank": 1,
        "cosine_similarity": 0.94,
        "recipe_name": "Blue Celadon Base",
        "surface": "glossy",
        "transparency": "translucent",
        "color_family": "blue",
        "community_notes": "Fires well at cone 6 ox, slight variation with iron content."
      }
    ],
    "remediation": {
      "chemical_analysis": "The glaze is under tensile stress — CTE 8.64e-6 exceeds the stoneware target of 7.30e-6 by 1.34e-6, classified as High crazing risk tier. The GNN predicts a glossy surface consistent with the elevated SiO2:Al2O3 ratio of 6.5. The nearest empirical analogue (Blue Celadon Base, similarity 0.94) confirms this formulation space is viable with adjustments.",
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
  │   │   │   ├── umf.py       ← Layer 1: UMF conversion
  │   │   │   └── stull.py     ← Layer 1: Stull chart SVG geometry
  │   │   ├── physics/
  │   │   │   └── cte.py       ← Layer 1: Deterministic CTE (Appen)
  │   │   ├── models/
  │   │   │   ├── schemas.py   ← Pydantic request/response schemas
  │   │   │   └── dataset.py   ← GlazyBench loader
  │   │   ├── retrieval/
  │   │   │   └── knn.py       ← Layer 2b: Faiss/USearch K-NN index
  │   │   ├── agent/
  │   │   │   ├── core.py      ← Layer 5: LLM interpreter orchestrator
  │   │   │   ├── tools.py     ← Tool definitions for LLM
  │   │   │   └── prompts.py   ← Layer 5: System prompts
  │   │   ├── optimizer/
  │   │   │   └── pareto.py    ← Layer 3: Constrained grid search
  │   │   └── render/
  │   │       └── sdxl.py      ← Layer 4: SDXL inference + prompt
  │   └── training/
  │       ├── train_gnn.py     ← Layer 2: GNN training
  │       └── data_utils.py    ← Data preparation
  │
  ├── gnn/
  │   ├── train.py             ← GIN training entry point
  │   ├── model.py             ← GIN architecture
  │   ├── inference.py         ← Low-latency inference wrapper
  │   ├── adjacency.py         ← Domain-Informed Adjacency Matrix builder
  │   ├── baselines.py         ← XGBoost/CatBoost comparison
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
  │       │   ├── RecipeGrid.tsx     ← Ingredient spreadsheet
  │       │   ├── StullChart.tsx     ← SVG triaxial chart render
  │       │   ├── Diagnostics.tsx    ← CTE + crazing tier panel
  │       │   ├── Neighbours.tsx     ← K-NN neighbour recipes panel
  │       │   ├── GlazePreview.tsx   ← SDXL render display
  │       │   └── Remediation.tsx    ← LLM explanation display
  │       └── lib/
  │           ├── api.ts
  │           └── types.ts
  │
  ├── data/
  │   └── glazybench/          ← GlazyBench parquet + Faiss index
  │
  └── tasks/
      ├── teammate-1-fullstack.md
      ├── teammate-2-ml-engineer.md
      └── teammate-3-gen-ai-engineer.md
  ```
  
  ---
  
  ## Layer Details
  
  ### Layer 1: Deterministic Physics Module
  
  - **UMF Engine** (`engine/umf.py`): Converts raw material mass percentages → normalized 47-oxide Unity Molecular Formula (fluxes sum to 1.0). Supports 18+ ceramic materials with known oxide analyses.
  - **CTE Computation** (`physics/cte.py`): Computes CTE using additive empirical coefficients (Appen / Winkelmann & Schott tables). Δ_stress = Glaze_CTE - Clay_CTE. Outputs are deterministic — no ML involved.
  - **Crazing Risk Tier** (`physics/cte.py`): Δ_stress mapped to discrete heuristic tiers:
    - Δ_stress < 0.5e-6 → `"Low"`
    - 0.5e-6 ≤ Δ_stress < 1.0e-6 → `"Moderate"`
    - 1.0e-6 ≤ Δ_stress < 1.5e-6 → `"High"`
    - Δ_stress ≥ 1.5e-6 → `"Extreme"`
  - **Stull Chart** (`engine/stull.py`): SVG geometric rendering utility mapping SiO₂:Al₂O₃ ratio to Stull triaxial classification zone. This is a deterministic geometric mapping, not a predictive model.
  
  ### Layer 2: Graph Neural Network (GIN)
  
  Trained exclusively on GlazyBench label space:
  
  - **Input:** 7 oxide nodes × [mol%, role one-hot (4), atomic mass/100] features.
  - **Graph Topology:** Domain-Informed Adjacency Matrix. Edges are fixed and initialized based on established ceramic oxide roles — fluxes connect to formers, intermediates bridge pathways. This replaces the chemically arbitrary "fully connected" baseline.
  - **Architecture:** 3× GINConv (hidden_dim=128) + BatchNorm + Dropout(0.15) + global mean/max pooling
  - **Heads:**
    - 9-class Surface finish (Glossy, Semi-glossy, Satin, Matte, Dry Matte, Stony Matte, etc.)
    - 4-class Transparency (Opaque, Semi-opaque, Translucent, Transparent)
    - 9-class Color family (Black, Blue, Brown, Green, Orange, Pink, Red, White, Yellow)
  - **Training:** 50 epochs, AdamW (lr=1e-3), CrossEntropy loss
  - **Tabular baselines:** GNN performance compared against XGBoost and CatBoost on identical feature inputs, per GlazyBench paper methodology (Section 4.1.1)
  
  ### Layer 2b: K-NN Vector Retrieval Module
  
  - **Index:** All GlazyBench formulations indexed by their 47-oxide UMF vector
  - **Search:** Cosine similarity via Faiss (GPU) or USearch (CPU fallback)
  - **Return:** Top 5 nearest real-world neighbour recipes with:
    - Formulation and UMF vector
    - Surface/transparency/color metadata
    - Community firing notes from Glazy platform
  - **Purpose:** Bridges visual simulation with empirical ground truth. Provides ceramic artists with known working recipes chemically similar to their input.
  - **Build:** Index constructed offline during data preparation; loaded at server start.
  
  ### Layer 3: Pareto Optimizer Module
  
  - **Objective function:** Minimize Δ_stress while maximizing target surface class probability
  - **Search strategy:** Constrained Grid Search over the top 3 primary variable inputs (typically the materials contributing the largest oxide mass fractions). Unconstrained evolutionary search is avoided for latency reasons.
  - **Constraints:** Ingredient masses must sum to 100%, each ingredient within [0%, 100%]
  - **Latency target:** <200ms total for sequential physics evaluation + ONNX GNN inference across all grid points
  - **Output:** Top-3 alternative formulations with projected CTE, Δ_stress, and surface class
  
  ### Layer 4: Visual Compiler (SDXL)
  
  - **Model:** stabilityai/stable-diffusion-xl-base-1.0
  - **Scheduler:** DPMSolverMultistepScheduler (20 steps)
  - **Conditioning:** Dynamic prompt compiled from GNN surface/transparency classes + CTE data + colour family
  - **Resolution:** 512×512
  - **Latency target:** < 2 seconds on MI300X
  - **Memory:** ~7 GB VRAM (FP16)
  - **Honest scope:** The output is an AI-generated visualization structurally consistent with predicted glaze phenotypes. It is not a physical fracture simulation, a CTE field render, or a photorealistic prediction of fired results. Defect features (crack networks, pinholes) in the rendered image are visual correlates of high-risk indicators, not learned defect models.
  
  ### Layer 5: LLM Interpreter (DeepSeek-V4-Flash)
  
  - **Model:** DeepSeek-V4-Flash via Fireworks AI (serverless, $0.14/$0.28 per 1M tokens)
  - **Role:** Communicative interpreter only — never derives scientific predictions
  - **Inputs:** Original recipe, UMF data, physics engine outputs (CTE, Δ_stress, crazing risk tier, Stull zone), GNN classifications (surface, transparency, colour) + confidence scores, K-NN nearest neighbour recipes with community notes, Pareto-optimized candidate recipe
  - **Outputs:** Structured JSON with chemical explanation + material delta suggestions
  - **Mode:** JSON structured output via Fireworks `response_format: {"type": "json_object"}`
  - **System prompt:** Scientific communicator with ceramic chemistry knowledge; instructed to reference provided computed metrics and neighbour data rather than deriving inferences from raw chemistry
  
  ---
  
  ## Hardware Strategy
  
  | Component | Hardware | Notes |
  |-----------|----------|-------|
  | GNN inference | AMD MI300X (ROCm) | Co-located in VRAM alongside SDXL |
  | K-NN index (Faiss) | AMD MI300X (ROCm) or CPU | GPU Faiss if available, USearch CPU fallback |
  | SDXL inference | AMD MI300X (ROCm) | ~7 GB FP16, DPM++ scheduler |
  | LLM reasoning | Fireworks AI API | Serverless, no GPU needed |
  | Pareto optimizer | CPU | <200ms sequential evaluation |
  | Backend | CPU (FastAPI) | Stateless, handles routing |
  | Frontend | CPU (Next.js) | Static export or lightweight server |
  
  The MI300X's 192 GB HBM3 allows co-locating GNN + K-NN Faiss index + SDXL + preprocessing in VRAM simultaneously, eliminating model swap latency.
  
  ---
  
  ## Team Roles
  
  | Role | Person | Responsibilities |
  |------|--------|------------------|
  | Full-Stack Engineer | Teammate 1 | Next.js UI, FastAPI routes, UMF engine, Stull chart SVG, integration |
  | ML Engineer | Teammate 2 | GNN (surface/transparency/color), Domain-Informed Adjacency, GlazyBench, tabular baselines, Faiss index, ROCm training |
  | Gen AI Engineer | Teammate 3 | LLM interpreter prompts, SDXL pipeline, Pareto optimizer, K-NN retrieval module, image generation |
  
  ---
  
  ## Daily Sync Checkpoints
  
  | Day | Anchor | Purpose |
  |-----|--------|---------|
  | End of Day 1 | Schema Lock | Agree on decoupled physics + GNN + K-NN + response JSON shape |
  | End of Day 2 | API Mocking | Mock all 6 layers so each teammate can develop independently |
  | End of Day 3 | Hardware Co-Location | GNN + Faiss + SDXL together in VRAM, E2E test |
  | End of Day 4 | Freeze + Pitch | Code freeze, screen recording, submission |
