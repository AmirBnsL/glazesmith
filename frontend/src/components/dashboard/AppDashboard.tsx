"use client";

import { useState, useEffect } from "react";
import { DashboardBackground } from "./DashboardBackground";
import { GlassPanel } from "./GlassPanel";
import RecipeGrid from "./RecipeGrid";
import StullChart from "./StullChart";
import Diagnostics from "./Diagnostics";
import Neighbours from "./Neighbours";
import GlazePreview from "./GlazePreview";
import Remediation from "./Remediation";
import AIChat from "./AIChat";
import { predictGlaze, generateImage } from "@/lib/api";
import type { PredictResponse, RecipeIngredient } from "@/lib/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export interface RecipeRow extends RecipeIngredient {
  id: string;
}

export function AppDashboard() {
  const [recipe, setRecipe] = useState<RecipeRow[]>([]);
  const [targetCone, setTargetCone] = useState<number>(6);
  const [atmosphere, setAtmosphere] = useState<"oxidation" | "reduction">("oxidation");
  const [clayBody, setClayBody] = useState<string>("Standard");
  
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [imageGenerating, setImageGenerating] = useState<boolean>(false);
  
  const totalPercentage = recipe.reduce((sum, row) => sum + (row.percentage || 0), 0);
  const isValidTotal = Math.abs(totalPercentage - 100) < 1;
  const hasIngredients = recipe.length > 0;

  const handlePredict = async () => {
    if (!hasIngredients || !isValidTotal) return;
    setLoading(true);
    setError(null);
    try {
      const cleanRecipe = recipe.map(({ material, percentage }) => ({ material, percentage }));
      const res = await predictGlaze({
        target_cone: targetCone,
        atmosphere,
        clay_body: clayBody,
        recipe: cleanRecipe
      });
      setPrediction(res);
    } catch (err: any) {
      setError(err.message || "Failed to predict glaze.");
    } finally {
      setLoading(false);
    }
  };
  const handleGenerateImage = async () => {
    if (!prediction) return;
    setImageGenerating(true);
    try {
      const cleanRecipe = recipe.map(({ material, percentage }) => ({ material, percentage }));
      const res = await generateImage({
        surface: prediction.metrics.finish,
        transparency: prediction.metrics.transparency,
        color_family: prediction.metrics.color_family,
        recipe: cleanRecipe
      });
      if (res.success) {
        setPrediction((prev) => prev ? { ...prev, render_output_url: res.image_url } : null);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setImageGenerating(false);
    }
  };

  return (
    <section id="app" className="relative isolate py-24 px-6 md:px-12 min-h-screen">
      <DashboardBackground />
      <h2 className="font-display text-3xl mb-8 relative z-10 text-[var(--ink)]">Formula</h2>
      
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassPanel>
          {/* Controls Form */}
          <div className="flex flex-wrap gap-3 mb-6 p-3 bg-white/40 rounded-xl border border-[var(--ink-soft)]/20">
            <div className="flex-1 min-w-[100px]">
              <label className="block text-[10px] text-[var(--ink-soft)] mb-1 uppercase tracking-wider">Target Cone</label>
              <Select value={targetCone.toString()} onValueChange={(val) => setTargetCone(Number(val))}>
                <SelectTrigger className="w-full bg-white/40 border-[var(--ink-soft)]/30 text-[var(--ink)] text-sm h-8 rounded-lg">
                  <SelectValue placeholder="Target Cone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">Cone 5</SelectItem>
                  <SelectItem value="6">Cone 6</SelectItem>
                  <SelectItem value="10">Cone 10</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[100px]">
              <label className="block text-[10px] text-[var(--ink-soft)] mb-1 uppercase tracking-wider">Atmosphere</label>
              <Select value={atmosphere} onValueChange={(val: any) => setAtmosphere(val)}>
                <SelectTrigger className="w-full bg-white/40 border-[var(--ink-soft)]/30 text-[var(--ink)] text-sm h-8 rounded-lg">
                  <SelectValue placeholder="Atmosphere" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="oxidation">Oxidation</SelectItem>
                  <SelectItem value="reduction">Reduction</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[100px]">
              <label className="block text-[10px] text-[var(--ink-soft)] mb-1 uppercase tracking-wider">Clay Body</label>
              <Input 
                value={clayBody} 
                onChange={e => setClayBody(e.target.value)}
                placeholder="Standard"
                className="w-full bg-white/40 border-[var(--ink-soft)]/30 text-[var(--ink)] text-sm h-8 rounded-lg"
              />
            </div>
          </div>

          <RecipeGrid recipe={recipe} onChange={setRecipe} />
          
          {/* Prediction Status Hint */}
          <div className="mt-4 pt-4 border-t border-[var(--ink-soft)]/20">
            {error && (
              <div className="text-red-500 text-xs mb-2 p-2 bg-red-500/10 rounded-lg">{error}</div>
            )}
            {!hasIngredients ? (
              <div className="text-[var(--ink-soft)] text-xs italic">Add ingredients to begin prediction.</div>
            ) : !isValidTotal ? (
              <div className="text-amber-600 text-xs italic">
                Recipe totals {totalPercentage.toFixed(1)}%. It must equal 100% to run prediction. Add {(100 - totalPercentage).toFixed(1)}% more.
              </div>
            ) : (
              <button
                onClick={handlePredict}
                disabled={loading}
                className="w-full bg-white/60 hover:bg-[var(--glaze-glass)] border border-[var(--ink-soft)]/20 text-xs font-semibold py-2.5 rounded-full transition-colors text-[var(--ink)] shadow-sm disabled:opacity-50"
              >
                {loading ? "Running analysis..." : "Run Prediction"}
              </button>
            )}
          </div>
        </GlassPanel>
        
        <GlassPanel>
          <StullChart coords={prediction?.stull_coordinates || null} />
        </GlassPanel>
        
        <GlassPanel>
          <Diagnostics metrics={prediction?.metrics || null} />
        </GlassPanel>
      </div>
      
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-[1fr_1.6fr_1fr] gap-6 mt-6">
        <GlassPanel className="h-[500px] flex flex-col">
          <Neighbours neighbours={prediction?.nearest_neighbours || []} loading={loading} />
        </GlassPanel>
        
        <GlassPanel className="h-[500px] flex flex-col">
          <GlazePreview 
            imageUrl={prediction?.render_output_url || null} 
            loading={loading} 
            generating={imageGenerating} 
            predictedColor={prediction?.metrics?.color_family || null}
            neighbours={prediction?.nearest_neighbours || []} 
            onGenerate={handleGenerateImage} 
          />
        </GlassPanel>
        
        <GlassPanel className="h-[500px] flex flex-col">
          <AIChat prediction={prediction} recipe={recipe} />
        </GlassPanel>
      </div>
    </section>
  );
}
