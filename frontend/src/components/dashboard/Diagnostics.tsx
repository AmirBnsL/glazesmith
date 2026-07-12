"use client";

interface Props {
  metrics: {
    original_cte: number;
    target_cte_max: number;
    crazing_risk: number;
    finish: string;
    transparency: string;
    color_family: string;
  } | null;
}

export default function Diagnostics({ metrics }: Props) {
  if (!metrics) return null;

  const cteVal = (metrics.original_cte * 1e6).toFixed(2);
  const targetVal = (metrics.target_cte_max * 1e6).toFixed(2);
  const riskPct = (metrics.crazing_risk * 100).toFixed(0);
  const riskColor = metrics.crazing_risk > 0.5 ? "text-red-400" : metrics.crazing_risk > 0.2 ? "text-amber-400" : "text-green-400";

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-[var(--ink)]">Diagnostics</h3>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3">
          <div className="text-[10px] text-[var(--ink-soft)] uppercase tracking-wider mb-1">CTE (×10⁻⁶/°C)</div>
          <div className="font-mono font-bold text-[var(--ink)]">{cteVal}</div>
          <div className="text-[10px] text-[var(--ink-soft)] mt-1">Target: &lt; {targetVal}</div>
        </div>

        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3">
          <div className="text-[10px] text-[var(--ink-soft)] uppercase tracking-wider mb-1">Crazing Risk</div>
          <div className={`font-bold ${riskColor}`}>{riskPct}%</div>
          <div className="w-full bg-[var(--ink-soft)]/20 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full rounded-full ${metrics.crazing_risk > 0.5 ? "bg-red-500" : metrics.crazing_risk > 0.2 ? "bg-amber-500" : "bg-green-500"}`}
              style={{ width: `${riskPct}%` }}
            />
          </div>
        </div>

        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3">
          <div className="text-[10px] text-[var(--ink-soft)] uppercase tracking-wider mb-1">Surface</div>
          <div className="font-bold capitalize text-[var(--ink)]">{metrics.finish}</div>
        </div>

        <div className="bg-white/40 border border-[var(--ink-soft)]/20 rounded-xl p-3">
          <div className="text-[10px] text-[var(--ink-soft)] uppercase tracking-wider mb-1">SiO₂:Al₂O₃</div>
          <div className="font-mono font-bold text-[var(--ink)]">—</div>
        </div>
      </div>
    </div>
  );
}
