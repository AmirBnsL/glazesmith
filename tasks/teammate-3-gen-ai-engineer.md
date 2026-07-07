# Teammate 3: Generative & Cognitive Engineer (LLM & Diffusion)

## Role

Own Layer 4 (SDXL visual compiler), Layer 5 (LLM interpreter), and Layer 3 (Pareto optimizer). The LLM's role is strictly a communicative interpreter — it translates structured diagnostic data into human-readable explanations, never deriving scientific predictions itself.

## Core Tasks

### Day 1 — LLM Interpreter Setup

- **Fireworks AI workspace:** Configure `backend/app/config.py` with DeepSeek-V4-Flash serverless endpoint. Verify basic completion + JSON mode.
- **System prompt:** Write the scientific communicator prompt in `backend/app/agent/prompts.py`. The LLM receives pre-computed metrics (Estimated CTE, Δ_stress, GNN surface/transparency class, Stull zone) and explains them to the user. It does NOT calculate chemistry or predict properties.
- **Tool definitions:** Define tools that assist explanation: `calculate_cte` (Appen lookup, deterministic), `fix_defect` (heuristic advice based on known ceramic science patterns), `estimate_delta` (suggest oxide adjustments).
- **Structured output schema:** Implement Fireworks `response_format` with `type: "json_schema"` for remediation responses:
  ```json
  {
    "chemical_analysis": "string explaining the issue referencing provided metrics",
    "recipe_adjustments": [
      { "material": "string", "delta_percentage": "number", "action": "increase|decrease|introduce|remove" }
    ],
    "expected_new_cte": "number"
  }
  ```

#### Files to touch
- `backend/app/agent/prompts.py`
- `backend/app/agent/tools.py`
- `backend/app/agent/core.py`
- `backend/app/config.py`

### Day 2 — Pareto Optimizer

- **Objective function:** Implement multi-objective search in `backend/app/optimizer/pareto.py`:
  - Minimize Δ_stress = |Estimated_CTE - Clay_CTE|
  - Maximize target surface class probability (from GNN)
- **Search strategy:** Grid search or simple genetic algorithm over ingredient percentages. Constraints: total = 100%, each ingredient ∈ [0, 100].
- **Output:** Top-3 alternative recipes with projected metrics.
- **Integration:** Optimizer receives UMF + GNN outputs, returns candidate recipes to the route.

#### Files to touch
- `backend/app/optimizer/pareto.py`

### Day 3 — Local SDXL Latent Tuning

- **Model loading:** Deploy `stabilityai/stable-diffusion-xl-base-1.0` using Hugging Face `diffusers` on AMD MI300X. Verify with simple text-to-image test.
- **Dynamic prompt builder:** Write `backend/app/render/sdxl.py` that constructs descriptive prompts from GNN surface/transparency predictions:
  - Surface = glossy → "high-gloss reflective silicate glass matrix"
  - Surface = stony matte → "rough micro-crystalline ceramic surface"
  - Crazing risk > 0.5 → "hairline crack network across glaze surface"
- **Negative prompt:** "blurry, low resolution, clip art, 3D render, drawing, pristine surface, matte paint"
- **Inference params:** FP16, 20 steps, DPMSolverMultistepScheduler, guidance_scale=7.5, 512×512
- **Honest scope:** Generated image visualizes predicted surface phenotypes — it does not simulate physical fracture or CTE behavior.
- **Benchmark:** Measure inference time. Target < 2 seconds on MI300X.

#### Files to touch
- `backend/app/render/sdxl.py`
- `backend/requirements.txt`

### Day 4 — Image Acceleration & E2E Integration

- **Scheduler tuning:** Experiment with DPMSolverMultistepScheduler at 15–20 steps. Find minimum step count preserving visual quality.
- **Memory optimization:** Use `torch.compile` if available. Enable FP16. Clear cache between runs.
- **Fallback:** If SDXL >3 sec, fall back to lighter model (SD 2.1 or Turbo).
- **Batch caching:** Cache renders for identical recipes to avoid re-running SDXL.
- **Integration test:** Full pipeline: recipe → UMF → CTE → GNN → Optimizer → SDXL → LLM → response.

## Deliverables

- `backend/app/agent/core.py` — LLM interpreter with structured JSON output
- `backend/app/agent/prompts.py` — Scientific communicator prompt (interpreter role, not predictor)
- `backend/app/render/sdxl.py` — SDXL inference pipeline with dynamic prompt builder
- `backend/app/optimizer/pareto.py` — Multi-objective formulation search
- Photorealistic glaze tile render under 2 seconds on MI300X

## Fireworks AI Quickstart

```bash
pip install openai
export FIREWORKS_API_KEY="your_key_here"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.fireworks.ai/inference/v1")

response = client.chat.completions.create(
    model="accounts/fireworks/models/deepseek-v4-flash",
    messages=[{"role": "user", "content": "Hello"}],
    response_format={"type": "json_object"},
    temperature=0.3,
)
```

## SDXL on ROCm Setup

```bash
pip install diffusers transformers accelerate torch
# SDXL loads in FP16 by default on ROCm
```
