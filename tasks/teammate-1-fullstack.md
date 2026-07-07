# Teammate 1: Full-Stack Engineer (Core & Integration)

## Role

Own the Next.js UI, FastAPI routing engine, UMF translation math, and tie the AI/ML outputs together.

## Core Tasks

### Day 1 — Frontend Setup & UMF Parser

- **Next.js spreadsheet grid:** Build the ingredient input table where users add raw materials (e.g., "Nepheline Syenite", "Silica 325") and set percentages. Must enforce total = 100%. Include a dynamic material dropdown with pre-loaded common materials.
- **Stull Triaxial Chart:** Implement a lightweight SVG/Canvas plot that maps SiO₂ vs Al₂O₃ coordinates. Update in real-time as recipe changes.
- **UMF Engine:** Write the pure Python utility in `backend/app/engine/umf.py` that parses raw material mass percentages into normalized molar oxide weights (fluxes = Na₂O + K₂O + CaO sum to 1.0). Include the material database with molecular weights and oxide analyses for 15+ common materials (Nepheline Syenite, Custer Feldspar, Silica, Whiting, EPK Kaolin, etc.).
- **Schema definition:** Lock the UMF JSON shape with the team.

#### Files to touch
- `frontend/src/components/RecipeGrid.tsx`
- `frontend/src/components/StullChart.tsx`
- `backend/app/engine/umf.py`
- `backend/app/engine/stull.py`
- `backend/app/models/schemas.py`

### Day 2 — API Handshake Orchestration

- **`/api/predict-glaze` endpoint:** Build the endpoint that receives the recipe payload, runs it through UMF engine, calls Teammate 2's GNN model (mock first), routes metrics to components.
- **Mock GNN outputs:** Hardcode realistic prediction values so Teammate 3 can test their Fireworks prompts before the real GNN is ready.
- **Diagnostics panel UI:** Build the React component showing CTE, crazing risk bar, surface finish, SiO₂:Al₂O₃ ratio, Stull zone classification.

#### Files to touch
- `backend/app/routes/predict.py`
- `backend/app/main.py`
- `frontend/src/components/Diagnostics.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`

### Day 3 — Consolidated Pipeline

- **Connect image generation:** Wire the SDXL render output (from Teammate 3) into the response pipeline. Display the generated image in `GlazePreview.tsx`.
- **Connect LLM remediation:** Display Fireworks AI structured remediation output in `Remediation.tsx`.
- **Aggregate response:** Build the unified response payload (Base64 image, text diagnostics, metrics) and ensure smooth client-side rendering.
- **Debounced sliders:** Implement debounced recipe editing so changing a slider automatically triggers a new prediction cycle.

#### Files to touch
- `frontend/src/components/GlazePreview.tsx`
- `frontend/src/components/Remediation.tsx`
- `frontend/src/app/page.tsx`
- `backend/app/routes/predict.py`

### Day 4 — Polish & States

- **Loading states:** Skeleton loaders for predictions, image generation spinner.
- **Error boundaries:** Graceful handling for invalid recipes (not summing to 100%, unknown materials).
- **Responsive layout:** Ensure the dashboard works on laptop and external monitors.
- **CSS polish:** Dark ceramic-themed UI consistent with the GlazeSmith brand.

## Deliverables

- Responsive web dashboard with:
  - Ingredient grid with material autocomplete
  - Real-time Stull chart SVG
  - Diagnostics panel (CTE, crazing risk, surface)
  - Glaze preview image panel
  - Remediation advice panel
- FastAPI `/api/predict-glaze` endpoint fully integrated
- Mock GNN data for offline development

## Schema Lock (agree Day 1)

```typescript
interface UnityMolecularFormula {
  fluxes: { Na2O: number; K2O: number; CaO: number; MgO: number };
  stabilizers: { Al2O3: number; Fe2O3: number };
  formers: { SiO2: number; B2O3: number };
}

interface GNNPrediction {
  coefficient_of_thermal_expansion: number;
  crazing_risk_probability: number;
  surface_finish_logits: number[];
  predicted_surface_class: string;
  transparency_class: string;
}
```
