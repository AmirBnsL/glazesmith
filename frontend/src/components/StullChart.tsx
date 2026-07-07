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
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-amber-400">Stull Chart</h3>
      <svg width={chartW} height={chartH} className="bg-stone-800 rounded border border-stone-700">
        <line x1="0" y1={chartH} x2={chartW} y2="0" stroke="#444" strokeDasharray="4" />

        <text x="4" y="12" className="fill-stone-400 text-[8px]">SiO₂</text>
        <text x={chartW - 36} y={chartH - 4} className="fill-stone-400 text-[8px]">Al₂O₃</text>

        {coords && (
          <>
            <circle cx={x} cy={y} r="5" className="fill-amber-500" />
            <text x={x + 8} y={y + 4} className="fill-amber-300 text-[8px]">
              {coords.classification_zone.replace("_", " ")}
            </text>
          </>
        )}
      </svg>
      {coords && (
        <div className="text-[10px] text-stone-400">
          SiO₂: {coords.y_silica} mol · Al₂O₃: {coords.x_alumina} mol
        </div>
      )}
    </div>
  );
}
