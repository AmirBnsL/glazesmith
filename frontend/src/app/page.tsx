"use client";

import { useState, useCallback } from "react";
import RecipeGrid from "@/components/RecipeGrid";
import StullChart from "@/components/StullChart";
import Diagnostics from "@/components/Diagnostics";
import GlazePreview from "@/components/GlazePreview";
import Remediation from "@/components/Remediation";
import { predictGlaze } from "@/lib/api";
import type { RecipeIngredient, PredictResponse } from "@/lib/types";

export default function Home() {
  const [recipe, setRecipe] = useState<RecipeIngredient[]>([
    { material: "Nepheline Syenite", percentage: 50 },
    { material: "Silica (325 mesh)", percentage: 25 },
    { material: "Whiting", percentage: 15 },
    { material: "EPK Kaolin", percentage: 10 },
  ]);
  const [cone, setCone] = useState("6");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runPrediction = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await predictGlaze({
        target_cone: parseInt(cone) || 6,
        atmosphere: "oxidation",
        clay_body: "stoneware_buff",
        recipe,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Prediction failed");
    }
    setLoading(false);
  }, [recipe, cone]);

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-stone-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🏺</span>
          <h1 className="text-lg font-bold">GlazeSmith</h1>
          <span className="text-[10px] bg-amber-900/50 text-amber-400 px-2 py-0.5 rounded-full border border-amber-800/50">
            AMD ROCm
          </span>
          <span className="text-[10px] bg-stone-800 text-stone-400 px-2 py-0.5 rounded-full">
            v1.0
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-stone-500">
          <span>Fireworks AI · SDXL · GNN</span>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <aside className="w-80 border-r border-stone-800 p-4 flex flex-col gap-4 overflow-y-auto">
          <RecipeGrid recipe={recipe} onChange={setRecipe} />

          <div className="flex items-center gap-2">
            <label className="text-xs text-stone-400">Cone:</label>
            <input
              className="w-16 bg-stone-800 rounded px-2 py-1 text-sm text-center text-stone-100"
              value={cone}
              onChange={(e) => setCone(e.target.value)}
            />
            <label className="text-xs text-stone-400">Atmosphere:</label>
            <span className="text-xs text-stone-500">Oxidation</span>
          </div>

          <button
            onClick={runPrediction}
            disabled={loading}
            className="bg-amber-700 hover:bg-amber-600 disabled:opacity-50 text-sm font-medium py-2 rounded-xl transition-colors"
          >
            {loading ? "Predicting..." : "Run Prediction"}
          </button>

          {error && (
            <div className="bg-red-900/50 border border-red-800 rounded-xl p-3 text-xs text-red-300">
              {error}
            </div>
          )}

          <StullChart coords={result?.stull_coordinates || null} />
          <Diagnostics metrics={result?.metrics || null} />
        </aside>

        <section className="flex-1 grid grid-cols-2 gap-4 p-4 overflow-y-auto">
          <GlazePreview
            imageUrl={result?.render_output_url || null}
            loading={loading}
          />
          <Remediation
            remediation={result?.remediation || null}
            loading={loading}
          />
        </section>
      </main>
    </div>
  );
}
