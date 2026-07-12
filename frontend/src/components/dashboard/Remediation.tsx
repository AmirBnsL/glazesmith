"use client";

import type { Remediation as RemediationType } from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Props {
  remediation: RemediationType | null;
  loading: boolean;
}

export default function Remediation({ remediation, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-[var(--ink)]">AI Analysis</h3>
        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3 text-[var(--ink-soft)] text-sm animate-pulse">
          Analyzing chemistry...
        </div>
      </div>
    );
  }

  if (!remediation) return null;

  return (
    <div className="flex flex-col h-full space-y-2">
      <h3 className="text-sm font-semibold text-[var(--ink)] shrink-0">AI Analysis</h3>
      <ScrollArea className="flex-1 min-h-0">
        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3 space-y-3 mr-4">
        <p className="text-sm text-[var(--ink)] leading-relaxed font-medium">
          {remediation.chemical_analysis}
        </p>

        {remediation.recipe_adjustments.length > 0 && (
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)] mb-2">Suggested Adjustments</div>
            <div className="space-y-2">
              {remediation.recipe_adjustments.map((adj, i) => (
                <div key={i} className="bg-[var(--ink-soft)]/5 border border-[var(--ink-soft)]/10 rounded-lg p-2 space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <span className={`inline-block w-2 h-2 rounded-full ${
                      adj.action === "increase" || adj.action === "introduce"
                        ? "bg-green-500" : "bg-red-500"
                    }`} />
                    <span className="text-[var(--ink)] font-medium">{adj.material}</span>
                    <span className="text-[var(--ink-soft)] font-mono">
                      {adj.action === "increase" ? "+" : adj.action === "decrease" ? "" : "→"}
                      {adj.delta_percentage}%
                    </span>
                    <span className="text-[10px] text-[var(--ink-soft)] italic">{adj.action}</span>
                    {adj.recommendation === "recommended" && (
                      <span className="text-[10px] text-green-600 font-bold ml-auto">VERIFIED</span>
                    )}
                    {adj.recommendation === "not_recommended" && (
                      <span className="text-[10px] text-red-600 font-bold ml-auto">NOT RECOMMENDED</span>
                    )}
                  </div>
                  {adj.verified_cte != null && (
                    <div className="text-[11px] text-[var(--ink-soft)] font-mono pl-5">
                      verified CTE: {adj.verified_cte.toFixed(2)} ×10⁻⁶/°C
                      {adj.verified_surface && ` · surface: ${adj.verified_surface}`}
                      {adj.verified_crazing_risk != null && (
                        ` · crazing: ${(adj.verified_crazing_risk * 100).toFixed(0)}%`
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {remediation.verification_summary && (
          <div className="text-xs text-[var(--ink-soft)] italic border-t border-[var(--ink-soft)]/20 pt-2">
            {remediation.verification_summary}
          </div>
        )}

        {!remediation.verification_summary && remediation.expected_new_cte > 0 && (
          <div className="text-xs text-[var(--ink-soft)] font-medium">
            Expected new CTE: <span className="font-mono text-[var(--ink)]">
              {remediation.expected_new_cte.toFixed(2)} ×10⁻⁶/°C
            </span>
          </div>
        )}
        </div>
      </ScrollArea>
    </div>
  );
}
