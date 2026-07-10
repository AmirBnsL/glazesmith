"use client";

import type { NeighbourInfo } from "@/lib/types";

interface Props {
  neighbours: NeighbourInfo[] | null;
  loading: boolean;
}

function similarityColor(sim: number): string {
  if (sim >= 0.90) return "bg-green-600";
  if (sim >= 0.80) return "bg-amber-600";
  return "bg-stone-600";
}

export default function Neighbours({ neighbours, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-amber-400">Similar Recipes</h3>
        <div className="bg-stone-800 rounded-xl p-3 text-stone-500 text-sm animate-pulse">
          Searching neighbours...
        </div>
      </div>
    );
  }

  if (!neighbours || neighbours.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-amber-400">Similar Recipes</h3>
      <div className="space-y-2">
        {neighbours.map((n) => (
          <div key={n.rank} className="bg-stone-800 rounded-xl p-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] bg-stone-700 text-stone-400 rounded-full w-5 h-5 flex items-center justify-center font-mono">
                  {n.rank}
                </span>
                <span className="text-sm text-stone-200">{n.recipe_name}</span>
              </div>
              <span className="text-[10px] font-mono text-stone-400">
                {(n.cosine_similarity * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-stone-700 h-1 rounded">
              <div
                className={`h-1 rounded ${similarityColor(n.cosine_similarity)}`}
                style={{ width: `${n.cosine_similarity * 100}%` }}
              />
            </div>
            <div className="flex flex-wrap gap-1">
              {n.surface && (
                <span className="text-[10px] bg-stone-700 text-stone-300 px-1.5 py-0.5 rounded capitalize">
                  {n.surface}
                </span>
              )}
              {n.transparency && (
                <span className="text-[10px] bg-stone-700 text-stone-300 px-1.5 py-0.5 rounded capitalize">
                  {n.transparency}
                </span>
              )}
              {n.color_family && (
                <span className="text-[10px] bg-stone-700 text-stone-300 px-1.5 py-0.5 rounded capitalize">
                  {n.color_family}
                </span>
              )}
            </div>
            {n.community_notes && (
              <div className="text-[10px] text-stone-500 italic leading-tight">
                {n.community_notes}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
