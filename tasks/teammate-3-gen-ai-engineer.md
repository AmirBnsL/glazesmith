# Teammate 3: Generative & Cognitive Engineer (LLM & Diffusion)

## Role

Own remote Fireworks AI multi-agent orchestration and local Stable Diffusion XL conditioning prompt pipelines on AMD hardware.

## Core Tasks

### Day 1 — Prompt Engineering & Fireworks Setup

- **Fireworks AI workspace:** Create account, generate API key, configure `backend/app/config.py`. Test basic completion with Llama 3 70B / DeepSeek V3.
- **System prompt:** Write the material science expert prompt in `backend/app/agent/prompts.py`. Must instruct the LLM to act as a ceramic glaze chemist with deep knowledge of oxide interactions, CTE calculations, defect mechanisms, and recipe adjustment strategies.
- **Tool definitions:** Define the four tools the agent can call: `predict_properties`, `fix_defect`, `calculate_cte`, `generate_glaze_image`. Each must have clear parameter schemas.
- **Test conversations:** Run 5 test dialogs covering crazing, crawling, pinholing, and general recipe questions. Log responses.

#### Files to touch
- `backend/app/agent/prompts.py`
- `backend/app/agent/tools.py`
- `backend/app/agent/core.py`
- `backend/app/config.py`

### Day 2 — Structured Output Enforcement

- **JSON schema mode:** Implement Fireworks' `response_format` with `type: "json_schema"`. Build the exact schema the LLM must follow for remediation responses.
- **Structured remediation schema:**

```json
{
  "type": "object",
  "properties": {
    "chemical_analysis": {"type": "string"},
    "recipe_adjustments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "material": {"type": "string"},
          "delta_percentage": {"type": "number"},
          "action": {"type": "string", "enum": ["increase", "decrease", "introduce", "remove"]}
        },
        "required": ["material", "delta_percentage", "action"]
      }
    },
    "expected_new_cte": {"type": "number"}
  },
  "required": ["chemical_analysis", "recipe_adjustments", "expected_new_cte"]
}
```

- **Agent core:** Build the orchestrator in `backend/app/agent/core.py` that:
  - Receives UMF matrix + GNN metrics
  - Constructs the system prompt with material data injected
  - Calls Fireworks with JSON schema mode
  - Parses and validates the response
  - Returns structured remediation to the API route
- **Error handling:** If the LLM returns malformed JSON, retry once with a stricter prompt. If it fails again, return a fallback message.

#### Files to touch
- `backend/app/agent/core.py`
- `backend/app/agent/prompts.py`
- `backend/app/models/schemas.py`

### Day 3 — Local SDXL Latent Tuning

- **Model loading:** Deploy `stabilityai/stable-diffusion-xl-base-1.0` using Hugging Face `diffusers` on the AMD MI300X. Verify with a simple text-to-image test.
- **Dynamic prompt builder:** Write `backend/app/render/sdxl.py` that constructs hyper-descriptive prompts from GNN metrics. Example mapping:

| GNN Metric | Prompt Injection |
|------------|-----------------|
| CTE = 8.64e-6 | "high thermal expansion glaze surface" |
| Crazing = 0.78 | "hairline spiderweb crack network across surface" |
| Surface = glossy | "high-gloss reflective silicate glass matrix" |
| Color ≈ clear | "transparent colorless glass layer showing clay body beneath" |

- **Negative prompt:** "blurry, low resolution, clip art, 3D render, drawing, pristine surface, matte paint"
- **Inference params:** FP16, 20 steps, DPMSolverMultistepScheduler, guidance_scale=7.5, 512×512
- **Benchmark:** Measure inference time. Target < 2 seconds on MI300X.

#### Files to touch
- `backend/app/render/sdxl.py`
- `backend/requirements.txt`

### Day 4 — Image Acceleration & Inference Polish

- **Scheduler tuning:** Experiment with DPMSolverMultistepScheduler at 15–20 steps. Find the minimal step count that preserves visual quality.
- **Memory optimization:** Use `torch.compile` if available. Enable FP16. Clear cache between runs.
- **Fallback:** If SDXL is too slow (>3 sec), implement a fallback to a lighter model (e.g., SD 2.1 or Turbo).
- **Integration test:** Full pipeline test: recipe → UMF → GNN → SDXL → Fireworks → aggregated response. Measure total end-to-end time.
- **Batch caching:** Cache renders for identical recipes to avoid re-running SDXL.

## Deliverables

- `backend/app/agent/core.py` — Fireworks AI agent with structured JSON output
- `backend/app/agent/prompts.py` — Material science system prompt
- `backend/app/render/sdxl.py` — SDXL inference pipeline with dynamic prompt builder
- Structured remediation that always returns parseable JSON
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
    model="accounts/fireworks/models/llama-v3p1-70b-instruct",
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
