"use client";

import type { StullCoordinates } from "@/lib/types";

interface Props {
  coords: StullCoordinates | null;
}

export default function StullChart({ coords }: Props) {
  const chartW = 200;
  const chartH = 200;

  const x = coords ? Math.min(coords.x_alumina * 80, chartW - 10) : 0;
  const y = coords ? Math.max(chartH - coords.y_silica * 40, 10) : 0;

  return (
    <div className="space-y-3 w-full">
      <h3 className="text-xs font-semibold text-[var(--ink)]">Stull Chart</h3>
      <div className="w-full aspect-square">
        <svg viewBox={`0 0 ${chartW} ${chartH}`} preserveAspectRatio="xMidYMid meet" className="w-full h-full bg-white/40 rounded-xl border border-[var(--ink-soft)]/20">
          <line x1="0" y1={chartH} x2={chartW} y2="0" stroke="currentColor" className="text-[var(--ink-soft)]/30" strokeDasharray="4" />

        <text x="4" y="12" className="fill-[var(--ink-soft)] text-[8px]">SiO₂</text>
        <text x={chartW - 36} y={chartH - 4} className="fill-[var(--ink-soft)] text-[8px]">Al₂O₃</text>

        {coords && (
          <>
            <circle cx={x} cy={y} r="5" className="fill-[var(--flower-petal)]" />
            <text x={x + 8} y={y + 4} className="fill-[var(--ink)] text-[8px] font-medium">
              {coords.classification_zone.replace("_", " ")}
            </text>
          </>
        )}
      </svg>
      </div>
      {coords && (
        <div className="text-[10px] text-[var(--ink-soft)]">
          SiO₂: {coords.y_silica} mol · Al₂O₃: {coords.x_alumina} mol
        </div>
      )}
    </div>
  );
}
