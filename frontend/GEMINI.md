# GlazeSmith — Gemini Working Rules

## Context
- AMD Unicorn Track hackathon project, team of 3, deadline today.
- This directory (cwd) is `frontend/` — Next.js (App Router) + TypeScript. Backend is a separate FastAPI/Python service in a sibling `backend/` dir — out of scope unless explicitly asked.
- Stack: Tailwind, shadcn/ui, React Three Fiber + drei (3D), Framer Motion (animation), next-themes (dark/light).

## Non-negotiables
- No second UI/component library. shadcn/ui only — no Tremor, MUI, AntD, Chakra.
- Don't touch the internal logic of `RecipeGrid.tsx`, `StullChart.tsx`, `Diagnostics.tsx`, `Neighbours.tsx`, `GlazePreview.tsx`, `Remediation.tsx` unless explicitly asked — only wrap/relocate them.
- Don't regenerate the flower asset or vase model with an image/3D generator — both are supplied files, reuse them as-is.
- No `OrbitControls` or drag interaction on the 3D vase — rotation is code-driven only.
- No hardcoded hex colors in components — use the CSS variables in `globals.css`.
- Don't invent product claims/copy — pull facts only from `README.md` / `ARCHITECTURE.md`, or ask.

## Working style
- If a build spec doc is attached (e.g. `FRONTEND_BUILD_SPEC.md`), it's the source of truth — read it fully before writing code, follow it exactly, including file paths.
- All paths in any spec doc are relative to this cwd (`frontend/`) unless stated otherwise.
- Prefer editing/moving existing files over recreating them from scratch.
- After finishing a section of a spec, self-check it against that doc's acceptance checklist before moving to the next section.
- If something is ambiguous and the doc doesn't resolve it: make the smallest reasonable assumption, state it in one line, keep going. Only stop and ask if it's genuinely blocking (e.g. a required asset is missing with no fallback).

## Before declaring anything done
- Run `npm run lint` and `tsc --noEmit` (or equivalent) — fix errors, don't hand back broken builds.
- Check the change against `prefers-reduced-motion` and mobile breakpoints, not just desktop.
- Walk the relevant acceptance checklist item by item.

## Output style
- No filler, no restating the task back, no "I'll now..." preambles.
- Report what changed and why, only where non-obvious. Skip narration of obvious steps.
- Terse code comments only where logic isn't self-evident (animation/physics math, non-obvious CSS).
