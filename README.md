# GlazeSmith

> Hybrid computational engine for evaluating ceramic glaze stability.
> Built for the AMD Unicorn Track Hackathon — AMD ROCm MI300X + Fireworks AI.

A 5-layer decoupled system: deterministic physics (CTE), graph neural network (surface/transparency/color), Pareto optimization, SDXL visualization, and LLM interpretation.

## Team

| Role | Person |
|------|--------|
| Full-Stack Engineer | Teammate 1 |
| ML Engineer | Teammate 2 |
| Gen AI Engineer | Teammate 3 |

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Visit http://localhost:3000
```

## Docs

- `ARCHITECTURE.md` — Full system specification (5-layer decoupled architecture)
- `tasks/teammate-1-fullstack.md` — Full-stack task brief
- `tasks/teammate-2-ml-engineer.md` — ML engineer task brief
- `tasks/teammate-3-gen-ai-engineer.md` — Gen AI engineer task brief
