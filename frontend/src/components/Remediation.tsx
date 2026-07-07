"use client";

import type { Remediation as RemediationType } from "@/lib/types";

interface Props {
  remediation: RemediationType | null;
  loading: boolean;
}

export default function Remediation({ remediation, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-amber-400">AI Analysis</h3>
        <div className="bg-stone-800 rounded-xl p-3 text-stone-500 text-sm animate-pulse">
          Analyzing chemistry...
        </div>
      </div>
    );
  }

  if (!remediation) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-amber-400">AI Analysis</h3>
      <div className="bg-stone-800 rounded-xl p-3 space-y-3">
        <p className="text-sm text-stone-200 leading-relaxed">
          {remediation.chemical_analysis}
        </p>

        {remediation.recipe_adjustments.length > 0 && (
          <div>
            <div className="text-xs font-medium text-stone-400 mb-1">Suggested Adjustments</div>
            <div className="space-y-1">
              {remediation.recipe_adjustments.map((adj, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    adj.action === "increase" || adj.action === "introduce"
                      ? "bg-green-500" : "bg-red-500"
                  }`} />
                  <span className="text-stone-300">{adj.material}</span>
                  <span className="text-stone-400">
                    {adj.action === "increase" ? "+" : adj.action === "decrease" ? "" : "→"}
                    {adj.delta_percentage}%
                  </span>
                  <span className="text-[10px] text-stone-500 italic">{adj.action}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {remediation.expected_new_cte > 0 && (
          <div className="text-xs text-stone-400">
            Expected new CTE: <span className="font-mono text-stone-200">
              {remediation.expected_new_cte.toFixed(2)} ×10⁻⁶/°C
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
