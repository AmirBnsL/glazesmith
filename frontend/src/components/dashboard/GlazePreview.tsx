"use client";

import { useState } from "react";
import type { PredictResponse } from "@/lib/types";
import GlazeVasePreview from "./GlazeVasePreview";

interface Props {
  imageUrl: string | null;
  loading: boolean;
  generating: boolean;
  predictedColor?: string | null;
  neighbours?: PredictResponse["nearest_neighbours"] | null;
  onGenerate?: () => void;
}

const COLOR_MAP: Record<string, string> = {
  White: "#f0f0e8",
  Gray: "#8a8a8a",
  Black: "#2a2a2a",
  Blue: "#3b6ea5",
  Green: "#4a7c4f",
  Yellow: "#d4a843",
  Orange: "#c0702a",
  Red: "#8b3a3a",
  Purple: "#6b4f7a",
};

export default function GlazePreview({ imageUrl, loading, generating, predictedColor, neighbours, onGenerate }: Props) {
  const [viewMode, setViewMode] = useState<"3D" | "2D">("3D");
  const [devImageUrl, setDevImageUrl] = useState<string | null>(null);

  // Use the predicted color directly, fallback to calculating from neighbours if missing
  const colorFamily = predictedColor || (() => {
    if (!neighbours || neighbours.length === 0) return null;
    const counts: Record<string, number> = {};
    for (const n of neighbours) {
      const c = n.color_family;
      if (c && COLOR_MAP[c]) counts[c] = (counts[c] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted.length > 0 ? sorted[0][0] : null;
  })();

  const mappedHexColor = colorFamily ? COLOR_MAP[colorFamily] : null;
  const bgColor = mappedHexColor || "#444";

  const activeImageUrl = devImageUrl || imageUrl;

  const handleDevTest = async () => {
    try {
      const res = await fetch("/api/dev/random-material");
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDevImageUrl(url);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-2 flex flex-col h-full">
      <div className="flex justify-between items-center shrink-0">
        <h3 className="text-sm font-semibold text-[var(--ink)]">Fired Glaze Preview</h3>
        <div className="flex gap-2">
          {process.env.NODE_ENV === "development" && (
            <button
              onClick={handleDevTest}
              className="px-2 py-1 text-[10px] font-medium bg-amber-500/20 text-amber-700 rounded transition-colors hover:bg-amber-500/30"
            >
              Dev: Test Material
            </button>
          )}
          <div className="flex bg-white/30 rounded-lg p-0.5 border border-[var(--ink-soft)]/20">
            <button
              onClick={() => setViewMode("3D")}
              className={`px-2 py-0.5 text-[10px] font-medium rounded-md transition-colors ${viewMode === "3D" ? "bg-white shadow-sm text-[var(--ink)]" : "text-[var(--ink-soft)] hover:text-[var(--ink)]"}`}
            >
              3D Vase
            </button>
            <button
              onClick={() => setViewMode("2D")}
              className={`px-2 py-0.5 text-[10px] font-medium rounded-md transition-colors ${viewMode === "2D" ? "bg-white shadow-sm text-[var(--ink)]" : "text-[var(--ink-soft)] hover:text-[var(--ink)]"}`}
            >
              2D Swatch
            </button>
          </div>
        </div>
      </div>

      <div
        className="rounded-xl border border-[var(--ink-soft)]/20 aspect-square flex items-center justify-center overflow-hidden flex-1 relative"
        style={viewMode === "2D" && !loading && !activeImageUrl && colorFamily ? { backgroundColor: bgColor } : {}}
      >
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[var(--glaze-glass)]/50 backdrop-blur-sm">
            <div className="text-[var(--ink-soft)] text-sm animate-pulse">Generating preview...</div>
          </div>
        )}

        {viewMode === "3D" && (colorFamily || activeImageUrl) && (
          <div className="absolute inset-0 w-full h-full">
            <GlazeVasePreview source={activeImageUrl} colorFallback={mappedHexColor} />
          </div>
        )}

        {viewMode === "3D" && !colorFamily && !activeImageUrl && (
          <div className="text-[var(--ink-soft)] text-xs text-center px-4">
            Enter a recipe and run prediction to see the 3D glaze preview
          </div>
        )}

        {viewMode === "2D" && (
          <>
            {!loading && activeImageUrl && (
              <img src={activeImageUrl} alt="Glaze preview swatch" className="w-full h-full object-cover" />
            )}
            {!loading && !activeImageUrl && !colorFamily && (
              <div className="text-[var(--ink-soft)] text-xs text-center px-4">
                Enter a recipe and run prediction to see the 2D glaze swatch
              </div>
            )}
            {!loading && !activeImageUrl && colorFamily && !generating && (
              <div className="text-center relative z-10">
                <div className="text-white/90 text-sm font-bold drop-shadow-md tracking-wide">
                  {colorFamily}
                </div>
                <div className="text-white/70 text-[10px] mt-1 drop-shadow-sm font-medium">
                  SDXL image generation available
                </div>
              </div>
            )}
            {!loading && !activeImageUrl && colorFamily && generating && (
              <div className="text-white/80 text-sm animate-pulse font-medium drop-shadow-md relative z-10">
                Generating SDXL image...
              </div>
            )}
          </>
        )}
      </div>

      {!loading && !generating && !activeImageUrl && colorFamily && onGenerate && (
        <button
          onClick={onGenerate}
          className="w-full bg-white/40 hover:bg-[var(--glaze-glass)] border border-[var(--ink-soft)]/20 text-xs font-medium py-2 rounded-full transition-colors text-[var(--ink)] mt-2 shrink-0"
        >
          Generate Image (SDXL)
        </button>
      )}
    </div>
  );
}
