# GlazeSmith — Frontend Build Spec (Hero + Dashboard + About)

**Audience:** Your editor is already scoped to the `frontend/` directory (that's your working root) for the AMD Unicorn Track hackathon Next.js + TypeScript codebase. Every path in this doc is written relative to that root — e.g. `public/models/vase.glb` means `<your cwd>/public/models/vase.glb`, not a `frontend/` subfolder inside it. Read this whole file before writing code. Do not deviate from the locked decisions in Section 0 — they've already been debated and settled.

**Current repo state (verify before assuming anything further):**
```
. (your cwd, = frontend/)
  3D/                 ← check contents first — may already hold vase/model work in progress
  reference/           ← check contents first — may already hold reference assets
  src/
    app/
      globals.css       ← default/near-empty, no design tokens yet
      layout.tsx        ← default scaffold
      page.tsx          ← default scaffold
    components/          ← flat, stub/placeholder files, no styling or 3D/animation work yet
      Diagnostics.tsx
      GlazePreview.tsx
      Neighbours.tsx
      RecipeGrid.tsx
      Remediation.tsx
      StullChart.tsx
    lib/
      api.ts
      types.ts
  Dockerfile
  next.config.ts
  package.json / package-lock.json
  tsconfig.json
```
There is **no `components/ui/`, no `components.json`, no `lib/utils.ts`** — shadcn/ui has not been initialized. Nothing described below exists yet; this is a from-zero visual build. Ignore any older README/architecture doc claims that a UI library, bento grid, or design system is already in place — they described a stale plan, not the current repo.

Reference image: the founder sketched the target layout by hand (pen on paper). Treat that sketch as the literal source of truth for layout/composition. This doc translates it into an exact build plan.

---

## 0. Locked decisions (do not re-litigate)

1. **This is one single-page app, not a marketing site + separate app.** Three vertically stacked sections on `/`: `#hero`, `#app` (the real working dashboard — recipe grid, physics, GNN, K-NN, optimizer, render, remediation), `#about`. Nav "App" and "About" buttons are smooth-scroll anchors, not route changes.
2. **Dashboard UI system: shadcn/ui, initialized fresh.** Its Card/Badge/Tabs/Separator primitives are dashboard-grade and it composes cleanly with Tailwind (already present via `create-next-app`). Do **not** add Tremor, MUI, AntD, or any second component system — under a hackathon deadline, two design systems fighting over Tailwind config is a bigger risk than shadcn's marginal chart limitations. If a chart is ever needed later, `recharts` (which shadcn's own chart blocks wrap) is the fallback — don't reach for it unless a component explicitly requires it.
3. **Flower asset: reuse the provided PNG, don't generate new ones.** The reference flower image is already a clean flat-illustration asset with a transparent background — regenerating it via an image model adds risk (style drift, licensing, latency) for zero benefit. Save it to `public/assets/flower.png`. It has no stem, so stems/vines are hand-built inline SVG (Section 4) in a sage green — this also satisfies the "green trunks" requirement from the sketch, which the reference PNG doesn't cover.
4. **Vase: 3D via GLTF, not a static image.** The founder is supplying `vase.glb` — check `3D/` first, it may already be there. Save/confirm it at `public/models/vase.glb`. Render with `@react-three/fiber` + `@react-three/drei`, always auto-rotating, never user-draggable (no OrbitControls — the sketch explicitly shows ambient rotation, not an interactive control).
5. **Clouds/fog: CSS only, no image assets.** Layered blurred pastel blobs, animated drift. Cheaper, resolution-independent, and easy to theme for dark mode.
6. **Setup, in order:**
   ```bash
   # 1. shadcn/ui (adds components.json, lib/utils.ts, CSS variables in globals.css, base Tailwind wiring)
   npx shadcn@latest init
   npx shadcn@latest add card badge button separator tabs

   # 2. everything else this spec needs
   npm install three @react-three/fiber @react-three/drei framer-motion next-themes
   ```
   Run `shadcn init` first — it rewrites `globals.css` with its own CSS-variable scaffold, and you want the design tokens in Section 1 layered on top of that, not fighting a later overwrite. `next-themes` drives dark/light mode (`class` strategy — matches shadcn's variable pattern).

---

## 1. Design tokens

Follow the sketch's own direction exactly — dreamy, pastel, hand-illustrated, ceramic. Don't default to generic dark-mode-SaaS or cream/terracotta styling.

### Color (light mode)
| Token | Hex | Use |
|---|---|---|
| `--bg-dream` | `#FDF1F5` | Page base background (light dreamy pink) |
| `--bg-dream-2` | `#FBE4EC` | Secondary background / section transitions |
| `--cloud` | `#FFFFFF` | Fog blobs (used at low opacity + heavy blur) |
| `--flower-petal` | `#F28DA0` | Petal pink (matches reference asset) |
| `--flower-center` | `#FBC94C` | Flower center yellow |
| `--stem-green` | `#7C9473` | Stems / trunks / leaves (muted sage, not a bright cartoon green) |
| `--glaze-glass` | `rgba(255,255,255,0.35)` | Glassmorphic panel fill in the app section |
| `--ink` | `#3A2530` | Primary text (warm near-black, not pure black — keeps the palette cohesive) |
| `--ink-soft` | `#6E5560` | Secondary text |

### Color (dark mode)
| Token | Hex | Use |
|---|---|---|
| `--bg-dream` | `#20141B` | Page base (deep plum, not pure black) |
| `--bg-dream-2` | `#2C1B24` | Secondary background |
| `--cloud` | `#4A2E3D` | Fog blobs in dark mode (muted rose-plum, not white) |
| `--flower-petal` | `#E27C93` | Slightly desaturated for dark bg |
| `--flower-center` | `#F0BE4A` | — |
| `--stem-green` | `#5F7859` | — |
| `--glaze-glass` | `rgba(30,18,25,0.45)` | Glass panel fill |
| `--ink` | `#F5E9EE` | Primary text |
| `--ink-soft` | `#C9AFB9` | Secondary text |

Implement as CSS variables on `:root` and `.dark` in `globals.css`, exactly like shadcn's existing variable pattern — extend it, don't replace it.

### Type
- **Display / headings:** `Fraunces` (variable, use optical size + soft-serif warmth — it reads as handmade/ceramic, not corporate). Weight 500–600 for headings, occasional italic for accent words.
- **Body / UI:** `Plus Jakarta Sans` — clean, rounded terminals, pairs well with Fraunces without competing.
- **Signature accent (use sparingly, one place only):** the "GlazeSmith" wordmark in the navbar rendered in a hand-lettered/marker webfont (e.g. `Caveat` or `Kalam`), as a nod to the original pen sketch. Do **not** reuse this font anywhere else — it's the one deliberate flourish, not a system font.

Load via `next/font/google` in `layout.tsx`.

### Shape / effect language
- Corner radius: `rounded-2xl` (16px) for cards/panels, `rounded-full` for pills/buttons — soft, matches the hand-drawn rounded boxes in the sketch.
- Glass panels: `backdrop-blur-xl bg-[var(--glaze-glass)] border border-white/40 dark:border-white/10 shadow-[0_8px_32px_rgba(242,141,160,0.15)]`
- No hard drop shadows anywhere — everything soft, diffused, consistent with "glaze/glossy" material language.

---

## 2. File/asset layout

Reorganize the existing flat `src/components/` into subfolders as part of this work, and add the new files below. Move the six existing component files into `components/dashboard/` unchanged (content untouched, just relocated) — don't rewrite their internals, that's separate work happening in parallel.

```
. (your cwd, = frontend/)
  public/
    models/
      vase.glb                  ← confirm/copy from 3D/ if it's there; if genuinely absent, build VaseCanvas against a placeholder cube, don't block on it
    assets/
      flower.png                ← reference flower image, save as-is (transparent bg)
  src/
    app/
      layout.tsx                 ← fonts, ThemeProvider, globals.css import
      page.tsx                   ← composes <Navbar/> <Hero/> <AppDashboard/> <About/>
      globals.css                ← shadcn base (from init) + design tokens from Section 1 layered on top
    components/
      ui/                        ← generated by `shadcn add`, don't hand-edit
      layout/
        Navbar.tsx
        ThemeToggle.tsx
      hero/
        Hero.tsx
        VaseCanvas.tsx            ← R3F canvas + GLTF loader + auto-rotate
        CloudBackground.tsx       ← CSS fog blobs
        FlowerScatter.tsx         ← positions + vines
        FlowerVine.tsx            ← single flower + SVG stem, reusable
      dashboard/
        AppDashboard.tsx          ← section wrapper, glass bg, grid layout
        DashboardBackground.tsx   ← blurred gradient + faint flower texture behind glass panels
        GlassPanel.tsx            ← shared Card wrapper (Section 5)
        RecipeGrid.tsx, StullChart.tsx, Diagnostics.tsx,
        Neighbours.tsx, GlazePreview.tsx, Remediation.tsx
                   ← moved from the old flat components/ path, contents untouched.
                     Wrap them in GlassPanel (Section 5) without editing their internals.
      about/
        About.tsx
    lib/
      utils.ts                   ← added by shadcn init
      api.ts, types.ts            ← existing, untouched
```

---

## 3. Navbar

Fixed/sticky, top of page, transitions from transparent to a translucent blurred bar on scroll (Framer Motion or a scroll listener toggling a class — either is fine).

Layout, left to right:
- **Left:** "GlazeSmith" wordmark in the hand-lettered accent font (Section 1), `text-2xl`, `--ink` color. Small flower glyph (reuse `flower.png`, ~20px) inline before or after the wordmark as a logomark — matches the vine doodle the founder drew next to the logo in the sketch.
- **Right, as a cluster:**
  - `App` — text link, smooth-scrolls to `#app`
  - `About` — pill button (`rounded-full border px-4 py-1.5`), smooth-scrolls to `#about` — matches the pill shape drawn in the sketch
  - `ThemeToggle` — icon-only button, sun/moon icon (use `lucide-react`'s `Sun`/`Moon`, already a shadcn dependency), toggles `next-themes`

```tsx
// Smooth scroll — no extra library needed
const scrollTo = (id: string) =>
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
```

Height: `h-16`, horizontal padding matching page container (`px-6 md:px-12`), `z-50`.

---

## 4. Hero section (`#hero`)

Full viewport height (`min-h-screen`), background `--bg-dream`, `relative overflow-hidden` so the cloud/flower layers can bleed off-edge.

**Layer stack (back to front):**
1. `CloudBackground` — 3–4 absolutely-positioned blurred ellipses using `--cloud`, `blur-3xl`, opacity 0.4–0.7, sizes ~500–800px, slow independent drift animation (translate ±20px over 15–20s, `ease-in-out infinite alternate`, staggered delays so they don't move in sync). Pure CSS/Framer Motion, no JS canvas needed.
2. `FlowerScatter` — flower+vine clusters positioned in the corners, mirroring the sketch: a 3-flower vine curling from the top-left corner near the logo, a 2-flower cluster on a branch in the right-middle area. See Section 4a for the vine SVG approach. Keep these outside the vase's visual footprint — they frame it, they don't cover it.
3. `VaseCanvas` — centered, roughly 400×500px on desktop, the visual anchor of the hero. See Section 4b.
4. Hero copy — optional, minimal: a short line under/beside the vase (e.g. product name + one-line description). Keep it small — the vase is the hero, not a headline. Don't add a big display headline that competes with the 3D piece; that would contradict the sketch, which has almost no hero text.

### 4a. `FlowerVine.tsx` — flower + hand-drawn stem

Each flower instance = `flower.png` (sized via `width`/`height`, `rotate-[Ndeg]` per instance for organic variety) + an inline SVG curved stem drawn behind it in `--stem-green`, stroke width ~3, rounded linecap, with 1–2 small leaf shapes (simple pointed-oval `<path>`) branching off. Example skeleton for one stem:

```tsx
<svg width="120" height="160" viewBox="0 0 120 160" className="absolute -z-10">
  <path
    d="M60 160 C 40 120, 70 90, 50 40"
    stroke="var(--stem-green)"
    strokeWidth="3"
    strokeLinecap="round"
    fill="none"
  />
  <path
    d="M50 100 C 35 95, 25 105, 20 120"
    stroke="var(--stem-green)"
    strokeWidth="2.5"
    strokeLinecap="round"
    fill="none"
  />
</svg>
```
Vary the curve control points per instance so the vine feels hand-drawn, not copy-pasted. Cluster 2–3 `FlowerVine` instances together with slightly different scales/rotations to build the corner groupings from the sketch.

Give the whole cluster a very slow idle bob (Framer Motion, `y: [0, -6, 0]`, 4–6s loop, staggered per flower) — ambient life, not attention-grabbing.

### 4b. `VaseCanvas.tsx` — 3D rotating vase

```tsx
"use client";
import { Canvas } from "@react-three/fiber";
import { useGLTF, Environment, ContactShadows } from "@react-three/drei";
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

function Vase() {
  const ref = useRef<THREE.Group>(null);
  const { scene } = useGLTF("/models/vase.glb");
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.35; // slow, constant
  });
  return <primitive ref={ref} object={scene} scale={1.4} position={[0, -0.5, 0]} />;
}

export default function VaseCanvas() {
  return (
    <Canvas camera={{ position: [0, 0.5, 4], fov: 40 }} className="!absolute inset-0">
      <ambientLight intensity={0.6} />
      <directionalLight position={[3, 4, 2]} intensity={1.2} color="#FFF3F7" />
      <Environment preset="studio" />
      <Vase />
      <ContactShadows position={[0, -1.4, 0]} opacity={0.25} blur={2.5} />
    </Canvas>
  );
}
```

Notes:
- `Environment preset="studio"` gives the vase soft reflective highlights — this is the one place a literal "glaze" material cue pays off (glossy specular response), so don't skip it or swap to a flat/unlit material.
- No `OrbitControls` — rotation is code-driven only, per Section 0.4.
- Wrap `useGLTF` in a `<Suspense fallback={...}>` (a simple pulsing placeholder shape or skeleton) one level up in `Hero.tsx`, since the GLB may not be present yet at build time.
- `useGLTF.preload("/models/vase.glb")` once the file exists.

---

## 5. App / Dashboard section (`#app`)

This is the real product surface — everything from `teammate-1-fullstack.md`'s component list lives here. This spec only covers **shell, layout, and background** — it does not touch the internal logic of `RecipeGrid`, `StullChart`, `Diagnostics`, `Neighbours`, `GlazePreview`, `Remediation`. Wrap each in a shared glass `Card` shell; don't restyle their internals.

### Background (`DashboardBackground.tsx`)
"Glossy/blurry to symbolize glaze" — implement as:
1. Section background gradient: `--bg-dream-2` to `--bg-dream`, diagonal.
2. 2–3 large soft color blobs (reuse the cloud-blob technique from Hero, but smaller and more saturated — pull from `--flower-petal` and a complementary soft lavender) at `blur-3xl`, low opacity, positioned behind the grid.
3. 4–6 instances of `flower.png` scattered at **very low opacity (0.08–0.15) and larger scale (150–250px)**, no stems needed here — these read as ambient texture, not focal elements, matching the "blurry bg with flowers" note in the sketch. Do not let them overlap card content at meaningful opacity — they sit strictly behind the glass panels.

### Grid layout
Match the sketch's bento composition — a labeled top row of 3, a bottom row of 3 with a wider center panel:

```
┌─────────────┬─────────────┬─────────────┐
│ RecipeGrid   │ StullChart   │ Diagnostics  │   row 1: 3 equal columns
│ (+ "Add      │              │              │
│  ingredient" │              │              │
│  pill below) │              │              │
├─────────┬────┴────────┬─────┴────────┤
│Neighbour│ GlazePreview  │ Remediation  │   row 2: 1fr / 1.6fr / 1fr
└─────────┴───────────────┴──────────────┘
```

```tsx
<section id="app" className="relative py-24 px-6 md:px-12">
  <DashboardBackground />
  <h2 className="font-display text-3xl mb-8 relative z-10">Formula</h2>
  <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6">
    <GlassPanel><RecipeGrid />
      <button className="mt-4 rounded-full ...">+ Add ingredient</button>
    </GlassPanel>
    <GlassPanel><StullChart /></GlassPanel>
    <GlassPanel><Diagnostics /></GlassPanel>
  </div>
  <div className="relative z-10 grid grid-cols-1 md:grid-cols-[1fr_1.6fr_1fr] gap-6 mt-6">
    <GlassPanel><Neighbours /></GlassPanel>
    <GlassPanel className="min-h-[420px]"><GlazePreview /></GlassPanel>
    <GlassPanel><Remediation /></GlassPanel>
  </div>
</section>
```

`GlassPanel` = a thin wrapper around shadcn's `Card`:
```tsx
function GlassPanel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <Card className={`rounded-2xl backdrop-blur-xl bg-[var(--glaze-glass)] border border-white/40 dark:border-white/10 shadow-[0_8px_32px_rgba(242,141,160,0.15)] p-5 ${className}`}>
      {children}
    </Card>
  );
}
```

`GlazePreview` gets the visually dominant center slot (it renders the SDXL output — the most striking real content in this section, so give it the most room, per the sketch's larger center box).

Debounced auto-predict (per teammate-1 Day 3 spec) triggers a subtle loading shimmer on the affected `GlassPanel`s, not a full-section spinner — keeps the dashboard feeling alive rather than blocking.

---

## 6. About section (`#about`)

Full-width, generous vertical padding (`py-32`), centered content column `max-w-2xl mx-auto`, `--bg-dream` background (bookend the page — hero and about share the same base tone, dashboard is the "glaze" interlude between them).

Content: short project description (2–3 short paragraphs, plain language, no marketing fluff) — what GlazeSmith does, the six-layer pipeline in one sentence, that it was built for the AMD Unicorn Track hackathon on ROCm MI300X. Pull factual claims from `README.md`/`ARCHITECTURE.md` — don't invent capabilities. One or two flowers as quiet corner decoration, same low-opacity treatment as the dashboard background, not the full vine treatment from Hero (that's the hero's signature, not repeated here).

---

## 7. Dark/light mode

- `next-themes` `ThemeProvider` in `layout.tsx`, `attribute="class"`, `defaultTheme="light"` (page is designed light-first — dark is a faithful adaptation via the token table in Section 1, not an afterthought, but light is the intended default given the pink/dreamy direction).
- All colors referenced via CSS variables (Section 1) so toggling `.dark` on `<html>` repaints everything — never hardcode a hex directly in a component.
- `ThemeToggle.tsx`: simple icon button, `Sun`/`Moon` from `lucide-react`, swap based on `resolvedTheme`.

---

## 8. Responsive rules

- Navbar: on mobile, collapse `App`/`About` text+pill into a single menu icon if space is tight; theme toggle always visible.
- Hero: vase canvas shrinks to ~280×350px on mobile, flower clusters scale down and reposition to avoid overlapping the vase; cloud blobs stay (cheap, no layout cost).
- Dashboard grid: `grid-cols-1` below `md`, all panels stack in the order RecipeGrid → StullChart → Diagnostics → Neighbours → GlazePreview → Remediation.
- Respect `prefers-reduced-motion`: disable the vase's continuous rotation (freeze it at a fixed angle) and the flower bob/cloud drift when set.

---

## 9. Acceptance checklist (verify against the sketch before calling this done)

- [ ] Navbar: hand-lettered "GlazeSmith" wordmark + flower glyph, `App` + `About` (pill) links, sun/moon toggle
- [ ] Hero: vase rotates continuously and automatically, never stops, no drag/orbit interaction
- [ ] Hero: pink dreamy background with soft drifting cloud blobs
- [ ] Hero: flower clusters with visible green stems in the corners, matching the sketch's vine placement
- [ ] App section labeled "Formula", bento grid (3 + 3 with wide center bottom panel), glass panels over a blurred/glossy flower-textured background
- [ ] All six existing components (RecipeGrid, StullChart, Diagnostics, Neighbours, GlazePreview, Remediation) wrapped in `GlassPanel`, internals untouched
- [ ] About section: short factual project description, light background, minimal decoration
- [ ] Dark mode fully repaints via CSS variables, no hardcoded light-only colors
- [ ] Mobile: everything stacks cleanly, vase and flowers scale down, motion respects `prefers-reduced-motion`
