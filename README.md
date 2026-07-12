# GlazeSmith

Hybrid computational engine for evaluating and optimizing ceramic glaze stability — built for the **AMD Unicorn Track Hackathon**. GlazeSmith combines deterministic physics, machine learning, empirical retrieval, and an LLM agent with a 2-pass verification loop to diagnose glaze defects and suggest real, pipeline-verified recipe adjustments.

---

## What We Built

Ceramic glazes fail in predictable ways. A glaze that crazes (develops a network of fine cracks) does so because its coefficient of thermal expansion doesn't match the clay body it's fired on. A glaze that should be glossy but comes out matte is usually over-fluxed or under-silica'd. These are problems that ceramic chemists solve with math and tables — we automate the entire pipeline and add an AI agent on top.

**The core idea:** take a user's raw glaze recipe (materials + percentages), convert it through deterministic chemistry into a Unity Molecular Formula, compute thermal expansion stress, classify surface/transparency/color with trained ML models, find the nearest real-world analogues from a 16,781-recipe benchmark corpus, run a constrained Pareto optimizer over the formulation space, and then have an LLM interpreter explain what's happening and propose adjustments — each of which is automatically verified through the real physics + ML pipeline before being shown to the user. The user can then continue the conversation, asking follow-up questions or requesting "what if" scenarios that trigger new verifications.

**Data flow:** User recipe → UMF conversion → deterministic CTE + stress delta → XGBoost 3-head classification → Faiss K-NN neighbour search → Pareto grid search optimization → SDXL visualization → LLM interpreter proposes adjustments → real pipeline verifies each → LLM reviews verified results → user receives final recommendations with verified metrics. User can then chat interactively, with each turn grounding the LLM in the same diagnostic context and verifying any proposed changes through the pipeline.

## AMD Resource Usage

This project uses **Fireworks AI** as its LLM provider. Fireworks serves its models on **AMD Instinct MI300X GPUs**, which is how our LLM agent calls make use of AMD compute for this hackathon track.

- All LLM calls are made from the backend, in [`backend/`](./backend) — see `app/agent/core.py` for the Fireworks client and `app/agent/prompts.py` for the prompt construction.
- The Fireworks API key is supplied via `FIREWORKS_API_KEY` in `backend/.env`.
- The SDXL visualization service (`sdxl-service/`) is designed to run on AMD ROCm GPUs with 192 GB HBM3 (MI300X), enabling co-location of GNN inference, Faiss index, SDXL, and preprocessing in VRAM simultaneously.

## Main Code Path

| What | Where |
|---|---|
| Physics engine (CTE, stress delta, Stull chart) | `backend/app/engine/pipeline.py` — deterministic CTE computation + UMF conversion |
| UMF conversion (materials → 47-oxide formula) | `backend/app/engine/umf.py` — Unity Molecular Formula normalization |
| XGBoost classifiers (surface/transparency/color) | `backend/app/models/xgb_predictor.py` — 3-head predictor trained on GlazyBench |
| Faiss K-NN neighbour retrieval | `backend/app/retrieval/knn.py` — cosine similarity over 18-oxide UMF vectors |
| Pareto optimizer | `backend/app/optimizer/pareto.py` — constrained grid search over top-3 ingredients |
| SDXL visualization prompt builder | `backend/app/render/sdxl.py` — builds conditioning prompt from ML predictions |
| LLM interpreter + 2-pass verify loop | `backend/app/agent/core.py` — proposes adjustments, verifies through pipeline |
| Chat endpoint (interactive verification) | `backend/app/routes/chat.py` — conversational turns with on-demand verification |
| Production XGBoost training | `backend/training/train_production.py` — trains 3 classifiers with Optuna-tuned params |
| GlazyBench data loader | `backend/app/data/hf_loader.py` — downloads and caches HuggingFace dataset |
| Frontend UI | `frontend/src/app/page.tsx` — recipe input, diagnostics, remediation, chat panel |
| GNN experimental alternative | `gnn/model.py` — Graph Isomorphism Network for surface/CTE prediction (experimental) |

```
GlazeSmith/
├── backend/           FastAPI server — physics, ML, retrieval, optimizer, LLM agent, chat
│   ├── app/
│   │   ├── agent/     LLM interpreter + verification loop (core.py, prompts.py, tools.py)
│   │   ├── engine/    Physics engine (pipeline.py, stull.py, umf.py)
│   │   ├── models/    XGBoost predictors + Pydantic schemas
│   │   ├── optimizer/ Pareto grid search (pareto.py)
│   │   ├── retrieval/ Faiss K-NN search (knn.py)
│   │   ├── render/    SDXL prompt builder (sdxl.py)
│   │   ├── routes/    FastAPI routes (predict.py, chat.py)
│   │   └── data/      HuggingFace dataset loader
│   └── training/      XGBoost classifier training pipeline
├── frontend/          Next.js application — recipe form, diagnostics, remediation, chat
├── gnn/               Experimental GNN (Graph Isomorphism Network) module
├── sdxl-service/      Standalone SDXL image generation service
├── data/              GlazyBench Faiss index + materials database
├── notebooks/         Experiment notebooks (XGBoost baselines, GNN, MLP, cGAN)
├── scripts/           Data preparation scripts (Digitalfire scraper, materials finalization)
└── ARCHITECTURE.md    Full specification document
```

## External Services Used

| Service | Purpose | Required? |
|---|---|---|
| [Fireworks AI](https://fireworks.ai) | LLM inference (DeepSeek-V4-Flash) on AMD Instinct GPUs — generates analysis and recipe adjustments | Yes |
| [HuggingFace](https://huggingface.co) | GlazyBench dataset — 16,781 glaze recipes with UMF vectors and surface/transparency/color labels | Auto-downloaded |

All keys are supplied via environment variables — see [Setup](#setup) below. No service is called from the frontend directly; all external API calls happen server-side in `backend/`.

## Features

- **Deterministic CTE computation** via additive Appen coefficients — no ML, pure physics
- **3-head XGBoost classification** for surface finish (14-class), transparency (4-class), and color family (14-class) trained on GlazyBench
- **Faiss K-NN retrieval** — finds the 10 most similar real-world glazes from a 16,781-recipe corpus using cosine similarity over 18-oxide UMF vectors
- **Pareto optimizer** — constrained grid search over the top-3 ingredients, minimizing thermal stress while targeting a specific surface finish
- **2-pass LLM verification loop** — the agent proposes adjustments, each is run through the real physics + ML pipeline, then the agent reviews the verified results
- **Interactive chat** — user can ask follow-up questions or request "what if" scenarios; each proposed change is verified through the real pipeline before being shown
- **SDXL visualization** — AI-generated ceramic glaze tile preview conditioned on ML predictions
- **77-material ceramic database** scraped from Digitalfire with complete oxide analyses

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python 3.12+), XGBoost, Faiss, Pydantic v2
- **LLM:** DeepSeek-V4-Flash via Fireworks AI (AMD Instinct GPUs)
- **Visualization:** Stable Diffusion XL (local GPU or SDXL service)
- **Data:** GlazyBench (HuggingFace), Digitalfire materials database

## Setup

### Prerequisites

- Python 3.12+
- Node.js 22+
- A Fireworks AI API key (set in `backend/.env`)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/GlazeSmith.git
cd GlazeSmith
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

```dotenv
FIREWORKS_API_KEY=fw_your_key_here
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
LLM_MODEL=accounts/fireworks/models/deepseek-v4-flash
```

### 3. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train ML models (XGBoost classifiers)
python -m backend.training.train_production

# Start the server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","device":"amd_rocm"}
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### 5. Run with Docker (optional)

```bash
docker compose up --build
```

Backend (FastAPI) → http://localhost:8000
Frontend (Next.js) → http://localhost:3000

Requires AMD ROCm drivers for GPU passthrough. Without a compatible GPU, run backend and frontend separately (SDXL visualization and GPU-accelerated training will be unavailable).

## Usage

1. Open http://localhost:3000 in your browser.
2. Enter a glaze recipe (materials + percentages) in the left sidebar.
3. Click **Run Prediction** to evaluate the recipe across all 7 layers.
4. View the diagnostics panel: CTE, crazing risk, surface/transparency/color predictions, Stull chart zone.
5. Review the AI Analysis: LLM-generated chemical explanation with verified recipe adjustments.
6. Check nearest neighbours: the 10 most similar real-world glazes from GlazyBench.
7. Ask the **Chat** follow-up questions: "why is my glaze crazing?", "what if I add more silica?", "how can I reduce the CTE?" — each proposed change is verified through the real pipeline.

## API Reference

### `POST /api/predict-glaze`

Evaluates a glaze recipe and returns physics metrics, ML predictions, nearest neighbours, optimizer candidates, and LLM-generated remediation with verified adjustments.

**Request:**

```json
{
  "target_cone": 6,
  "atmosphere": "oxidation",
  "clay_body": "stoneware_buff",
  "recipe": [
    { "material": "Nepheline Syenite", "percentage": 50 },
    { "material": "Silica (325 mesh)", "percentage": 25 },
    { "material": "Whiting", "percentage": 15 },
    { "material": "EPK Kaolin", "percentage": 10 }
  ]
}
```

### `POST /api/chat`

Interactive conversational turn. Takes a user message, conversation history, the current recipe, and the prediction context from a prior `/predict-glaze` call. Returns the LLM response and any proposed adjustments verified through the real pipeline.

**Request:**

```json
{
  "message": "What if I increase silica by 5%?",
  "history": [],
  "recipe": [
    { "material": "Nepheline Syenite", "percentage": 50 },
    { "material": "Silica (325 mesh)", "percentage": 25 },
    { "material": "Whiting", "percentage": 15 },
    { "material": "EPK Kaolin", "percentage": 10 }
  ],
  "context": { "metrics": {}, "stull_coordinates": {}, "remediation": {}, "nearest_neighbours": [], "optimizer_candidates": [] }
}
```

### `POST /api/generate-image`

Generates an SDXL visualization of the glaze based on its predicted surface, transparency, and color.

### `GET /health`

Returns server status.

## Retraining Models

To retrain from scratch after data changes:

```bash
cd backend
source .venv/bin/activate
python -m backend.training.train_production
```

Models and label encoders are saved to `backend/app/models/`.

## Originality

GlazeSmith was built from scratch by our team for the AMD Unicorn Track Hackathon. Third-party dependencies (Next.js, FastAPI, XGBoost, Faiss, Fireworks AI SDK, Stable Diffusion) are used as libraries and services only; all physics computation, ML pipeline design, prompt engineering, agent architecture, and UI were written by us for this submission.

## Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

## License

MIT License
