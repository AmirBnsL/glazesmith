"use client";

import type { NeighbourInfo } from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Props {
  neighbours: NeighbourInfo[] | null;
  loading: boolean;
}

function similarityColor(sim: number): string {
  if (sim >= 0.90) return "bg-green-500";
  if (sim >= 0.80) return "bg-amber-500";
  return "bg-[var(--ink-soft)]/40";
}

export default function Neighbours({ neighbours, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-[var(--ink)]">Similar Recipes</h3>
        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3 text-[var(--ink-soft)] text-sm animate-pulse">
          Searching neighbours...
        </div>
      </div>
    );
  }

  if (!neighbours || neighbours.length === 0) return null;

  return (
    <div className="flex flex-col h-full space-y-2">
      <h3 className="text-xs font-semibold text-[var(--ink)] shrink-0">Similar Recipes</h3>
      <ScrollArea className="flex-1 min-h-0 pr-4">
        <div className="space-y-2 pb-4">
          {neighbours.map((n) => (
          <div key={n.rank} className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3 space-y-1.5 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] bg-[var(--ink-soft)]/10 text-[var(--ink-soft)] rounded-full w-5 h-5 flex items-center justify-center font-mono">
                  {n.rank}
                </span>
                <span className="text-sm text-[var(--ink)] font-medium">{n.recipe_name}</span>
              </div>
              <span className="text-[10px] font-mono text-[var(--ink-soft)]">
                {(n.cosine_similarity * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-[var(--ink-soft)]/10 h-1.5 rounded-full overflow-hidden mt-1">
              <div
                className={`h-full rounded-full ${similarityColor(n.cosine_similarity)}`}
                style={{ width: `${n.cosine_similarity * 100}%` }}
              />
            </div>
            <div className="flex flex-wrap gap-1 mt-2">
              {n.surface && (
                <span className="text-[10px] bg-[var(--ink-soft)]/5 border border-[var(--ink-soft)]/10 text-[var(--ink-soft)] px-1.5 py-0.5 rounded capitalize">
                  {n.surface}
                </span>
              )}
              {n.transparency && (
                <span className="text-[10px] bg-[var(--ink-soft)]/5 border border-[var(--ink-soft)]/10 text-[var(--ink-soft)] px-1.5 py-0.5 rounded capitalize">
                  {n.transparency}
                </span>
              )}
              {n.color_family && (
                <span className="text-[10px] bg-[var(--ink-soft)]/5 border border-[var(--ink-soft)]/10 text-[var(--ink-soft)] px-1.5 py-0.5 rounded capitalize">
                  {n.color_family}
                </span>
              )}
            </div>
            {n.community_notes && (
              <div className="text-[10px] text-[var(--ink-soft)] italic leading-tight mt-1">
                {n.community_notes}
              </div>
            )}
          </div>
        ))}
        </div>
      </ScrollArea>
    </div>
  );
}
