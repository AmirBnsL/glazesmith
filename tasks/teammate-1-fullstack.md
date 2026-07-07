# Teammate 1: Full-Stack Engineer (Core & Integration)

## Role

Own the Next.js UI, FastAPI routing engine, Layer 1 deterministic physics module (UMF + CTE + Stull), Layer 2b K-NN neighbours panel integration, and orchestration of all 6 layers into a single aggregated response.

## Core Tasks

### Day 1 — Frontend Setup & UMF Parser

- **Next.js spreadsheet grid:** Ingredient input table with material dropdown + percentage fields. Enforce total = 100%.
- **Stull Triaxial Chart:** SVG/Canvas plot mapping SiO₂ vs Al₂O₃ coordinates. Update in real-time as recipe changes.
- **UMF Engine** (`engine/umf.py`): Parse raw material mass percentages → normalized oxide weights (fluxes sum to 1.0). Include material DB with 15+ common materials.
- **CTE Physics** (`physics/cte.py`): Deterministic CTE computation using Appen coefficients. Δ_stress = Glaze_CTE - Clay_CTE.
- **Schema definition:** Lock the decoupled response JSON shape (physics_engine vs gnn_inference + nearest_neighbours array) with the team.

#### Files to touch
- `frontend/src/components/RecipeGrid.tsx`
- `frontend/src/components/StullChart.tsx`
- `backend/app/engine/umf.py`
- `backend/app/engine/stull.py`
- `backend/app/physics/cte.py`
- `backend/app/models/schemas.py`
- `backend/app/retrieval/knn.py`

### Day 2 — API Handshake Orchestration

- **`/api/predict-glaze` endpoint:** Receives recipe → UMF engine → CTE estimate → GNN (mock first) → Pareto optimizer → SDXL render → LLM interpreter → aggregated response.
- **Mock GNN + CTE + K-NN:** Hardcode realistic values so Teammates 2 and 3 can test independently before real models are ready.
- **Diagnostics panel UI:** CTE, Δ_stress, crazing_risk_tier, surface class, transparency, Stull zone, confidence scores.
- **Neighbours panel UI:** Nearest real-world recipe names, similarity scores, surface/transparency/color community notes.

#### Files to touch
- `backend/app/routes/predict.py`
- `backend/app/main.py`
- `frontend/src/components/Diagnostics.tsx`
- `frontend/src/components/Neighbours.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`

### Day 3 — Consolidated Pipeline

- **Connect image generation:** Wire SDXL render output (Teammate 3) into response pipeline. Display in `GlazePreview.tsx`.
- **Connect LLM explanation:** Display LLM structured remediation in `Remediation.tsx`.
- **Connect Pareto candidate:** Show optimized alternative recipe alongside original.
- **Connect K-NN neighbours:** Display top 5 nearest real-world neighbour recipes with similarity scores and community notes in `Neighbours.tsx`.
- **Aggregate response:** Unified payload with base64 image, physics_engine (CTE, Δ_stress, crazing_risk_tier, Stull), gnn_inference (surface, transparency, color), nearest_neighbours array, remediation, candidate recipes.
- **Debounced sliders:** Auto-trigger prediction on recipe changes.

#### Files to touch
- `frontend/src/components/GlazePreview.tsx`
- `frontend/src/components/Remediation.tsx`
- `frontend/src/app/page.tsx`
- `backend/app/routes/predict.py`

### Day 4 — Polish & States

- **Loading states:** Skeleton loaders for predictions, image generation spinner.
- **Error boundaries:** Invalid recipes, unknown materials, API failures.
- **Responsive layout:** Dashboard works on laptop and external monitors.
- **CSS polish:** Dark ceramic-themed UI.

## Deliverables

- Responsive web dashboard with:
  - Ingredient grid with material autocomplete
  - Real-time Stull chart SVG
  - Diagnostics panel (CTE, Δ_stress, crazing_risk_tier, surface, transparency)
  - K-NN nearest neighbour recipes panel
  - Glaze preview image panel
  - Remediation explanation panel
  - Optimized candidate recipe panel
- FastAPI `/api/predict-glaze` endpoint fully integrated
- UMF Engine + CTE Physics + Stull Chart (Layer 1)

## Schema Lock (agree Day 1)

```typescript
interface UnityMolecularFormula {
  fluxes: { Na2O: number; K2O: number; CaO: number; MgO: number };
  stabilizers: { Al2O3: number; Fe2O3: number };
  formers: { SiO2: number; B2O3: number };
}

interface PhysicsEngine {
  cte: number;
  target_cte_max: number;
  stress_delta: number;
  crazing_risk_tier: "Low" | "Moderate" | "High" | "Extreme";
  stull_coordinates: {
    x_alumina: number;
    y_silica: number;
    classification_zone: string;
  };
}

interface GNNInference {
  surface_class: string;
  surface_confidence: number;
  transparency_class: string;
  transparency_confidence: number;
  color_family: string;
  color_confidence: number;
}

interface NeighbourRecipe {
  rank: number;
  cosine_similarity: number;
  recipe_name: string;
  surface: string;
  transparency: string;
  color_family: string;
  community_notes: string;
}
```
