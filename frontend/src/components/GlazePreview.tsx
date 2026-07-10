"use client";

import type { PredictResponse } from "@/lib/types";

interface Props {
  imageUrl: string | null;
  loading: boolean;
  neighbours?: PredictResponse["nearest_neighbours"] | null;
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

export default function GlazePreview({ imageUrl, loading, neighbours }: Props) {
  const neighborColor = (() => {
    if (!neighbours || neighbours.length === 0) return null;
    const counts: Record<string, number> = {};
    for (const n of neighbours) {
      const c = n.color_family;
      if (c && COLOR_MAP[c]) counts[c] = (counts[c] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted.length > 0 ? sorted[0][0] : null;
  })();

  const bgColor = neighborColor ? COLOR_MAP[neighborColor] : "#444";

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-amber-400">Fired Glaze Preview</h3>
      <div
        className="rounded-xl border border-stone-700 aspect-square flex items-center justify-center overflow-hidden"
        style={!loading && !imageUrl && neighborColor ? { backgroundColor: bgColor } : {}}
      >
        {loading && (
          <div className="text-stone-500 text-sm animate-pulse">Generating preview...</div>
        )}
        {!loading && imageUrl && (
          <img src={imageUrl} alt="Glaze preview" className="w-full h-full object-cover" />
        )}
        {!loading && !imageUrl && !neighborColor && (
          <div className="text-stone-600 text-xs text-center px-4">
            Enter a recipe and run prediction to see the fired glaze preview
          </div>
        )}
        {!loading && !imageUrl && neighborColor && (
          <div className="text-center">
            <div className="text-white/80 text-xs font-semibold drop-shadow-md">
              {neighborColor}
            </div>
            <div className="text-white/50 text-[10px] mt-1">
              SDXL image generation unavailable
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
