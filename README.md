# GlazeSmith

> Hybrid computational engine for evaluating and optimizing ceramic glaze stability.
> Built for the AMD Unicorn Track Hackathon — ROCm MI300X + Fireworks AI.

A 6-layer decoupled system: deterministic physics (CTE via Appen coefficients), XGBoost classification (surface/transparency/color), K-NN vector retrieval (nearest real-world neighbours), Pareto optimization, SDXL visualization, and LLM-based interpretation with a 2-pass verification loop.

## Architecture

| Layer | Component | What it does |
|-------|-----------|-------------|
| 1 | Deterministic Physics | CTE estimation via additive Appen coefficients, UMF normalization, Stull chart |
| 2 | XGBoost Classifiers | Surface finish (9-class), transparency (4-class), color family (9-class) |
| 2b | K-NN Retrieval | Cosine similarity search over 47-oxide UMF vectors for nearest real glazes |
| 3 | Pareto Optimizer | Constrained grid search minimizing Δ_stress while maximizing target surface |
| 4 | SDXL Renderer | Prompt builder for AI-generated glaze visualization |
| 5 | LLM Interpreter | DeepSeek-V4-Flash analysing results and suggesting verified adjustments |
| 6 | Verify Loop | Tests each LLM-suggested change through the real physics + ML pipeline |

See `ARCHITECTURE.md` for the full specification.

## Prerequisites

- Python 3.12+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) (Python package manager) — or use `pip`
- A Fireworks AI API key (set in `backend/.env`)

## Setup

### 1. Backend

```bash
cd backend

# Create virtual environment & install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

If using `pip` instead:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### 2. Environment Variables

Copy the template and add your API key:

```
# backend/.env
FIREWORKS_API_KEY=fw_your_key_here
```

### 3. Train ML Models

```bash
cd backend
source .venv/bin/activate
python -m backend.training.train_production
```

This trains three XGBoost classifiers (surface, transparency, color_family) and saves them to `backend/app/models/`.

### 4. Start the Backend Server

```bash
cd backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","device":"amd_rocm"}
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Docker Compose (GPU Required)

```bash
docker compose up --build
```

This requires AMD ROCm drivers for GPU passthrough. If you don't have a compatible GPU, run backend and frontend separately without Docker.

## API Reference

### `POST /api/predict-glaze`

Evaluates a glaze recipe and returns physics metrics, ML predictions, nearest neighbours, optimizer candidates, and LLM-generated remediation with verified adjustments.

**Request body:**

```json
{
  "target_cone": 6,
  "atmosphere": "oxidation",
  "clay_body": "stoneware",
  "recipe": [
    { "material": "Nepheline Syenite", "percentage": 30 },
    { "material": "Silica", "percentage": 30 },
    { "material": "EP Kaolin", "percentage": 20 },
    { "material": "Whiting", "percentage": 10 },
    { "material": "Zinc Oxide", "percentage": 10 }
  ]
}
```

**Response includes:**

| Field | Description |
|-------|------------|
| `metrics` | CTE, crazing risk, predicted surface/transparency/color |
| `stull_coordinates` | Alumina/silica ratio + Stull chart zone |
| `remediation.recipe_adjustments[]` | Each adjustment has `verified_cte`, `verified_surface`, `verified_crazing_risk` from real simulation + `recommendation` ("recommended" / "not_recommended") |
| `remediation.chemical_analysis` | Natural language analysis from LLM |
| `nearest_neighbours[]` | Top 10 most similar real glazes from the GlazyBench corpus |
| `optimizer_candidates[]` | Up to 3 pareto-optimized recipe variants |

Example:

```bash
curl -X POST http://localhost:8000/api/predict-glaze \
  -H "Content-Type: application/json" \
  -d '{"target_cone":6,"atmosphere":"oxidation","clay_body":"stoneware","recipe":[{"material":"Nepheline Syenite","percentage":30},{"material":"Silica","percentage":30},{"material":"EP Kaolin","percentage":20},{"material":"Whiting","percentage":10},{"material":"Zinc Oxide","percentage":10}]}'
```

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

## Project Structure

```
backend/
  app/
    agent/            LLM interpreter + verification loop (core.py, prompts.py, tools.py)
    engine/           Physics engine (pipeline.py, stull.py, umf.py)
    models/           XGBoost predictors + schemas
    optimizer/        Pareto grid search
    retrieval/        FAISS K-NN search
    render/           SDXL prompt builder
    routes/           FastAPI routes (predict.py)
  training/           Training script for XGBoost classifiers
  data/               GlazyBench corpus + materials database
frontend/
  src/                Next.js app with glaze recipe form, diagnostics, remediation display
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FIREWORKS_API_KEY` | — | Fireworks AI API key (required for LLM agent) |
| `FIREWORKS_BASE_URL` | `https://api.fireworks.ai/inference/v1` | Fireworks API endpoint |
| `LLM_MODEL` | `accounts/fireworks/models/deepseek-v4-flash` | Model for the LLM interpreter |
