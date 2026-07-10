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
            <div className="space-y-2">
              {remediation.recipe_adjustments.map((adj, i) => (
                <div key={i} className="bg-stone-900 rounded-lg p-2 space-y-1">
                  <div className="flex items-center gap-2 text-sm">
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
                    {adj.recommendation === "recommended" && (
                      <span className="text-[10px] text-green-400 font-medium ml-auto">VERIFIED</span>
                    )}
                    {adj.recommendation === "not_recommended" && (
                      <span className="text-[10px] text-red-400 font-medium ml-auto">NOT RECOMMENDED</span>
                    )}
                  </div>
                  {adj.verified_cte !== undefined && (
                    <div className="text-[11px] text-stone-500 font-mono pl-5">
                      verified CTE: {adj.verified_cte.toFixed(2)} ×10⁻⁶/°C
                      {adj.verified_surface && ` · surface: ${adj.verified_surface}`}
                      {adj.verified_crazing_risk !== undefined && (
                        ` · crazing: ${((adj.verified_crazing_risk ?? 0) * 100).toFixed(0)}%`
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {remediation.verification_summary && (
          <div className="text-xs text-stone-500 italic border-t border-stone-700 pt-2">
            {remediation.verification_summary}
          </div>
        )}

        {!remediation.verification_summary && remediation.expected_new_cte > 0 && (
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
