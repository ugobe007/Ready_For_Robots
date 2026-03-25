/**
 * Renders API payload from GET /api/leads/homepage.scoringSystem (or /api/leads/scoring-system).
 */

function JsonBlock({ obj }) {
  return (
    <pre className="text-[11px] leading-relaxed text-cyan-200/90 bg-black/50 border border-neutral-800 rounded-lg p-3 overflow-x-auto font-mono">
      {JSON.stringify(obj, null, 2)}
    </pre>
  );
}

export default function HotDealsScoringExplainer({ data }) {
  if (!data) return null;

  const pc = data.priority_composite || {};
  const sets = data.signal_type_sets || {};
  const pw = data.per_signal_weighting || {};
  const paths = data.code_paths || {};

  return (
    <details className="border border-orange-900/35 rounded-xl bg-gradient-to-b from-orange-950/20 to-neutral-950/40 open:shadow-lg open:shadow-orange-950/20">
      <summary className="cursor-pointer list-none px-4 py-3 flex flex-wrap items-center justify-between gap-2 select-none [&::-webkit-details-marker]:hidden">
        <span className="text-sm font-semibold text-orange-300">
          How Hot deals are scored
        </span>
        <span className="text-xs text-neutral-500">
          Weights and thresholds · tune in backend
        </span>
        <span className="text-xs text-neutral-600 w-full md:w-auto md:ml-auto">
          Click to expand
        </span>
      </summary>
      <div className="px-4 pb-5 pt-0 space-y-6 text-sm text-neutral-300 border-t border-orange-900/25">
        <p className="text-neutral-400 leading-relaxed pt-4">{data.summary}</p>

        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-orange-400/90 mb-2">
            Tier rules (priority composite)
          </h3>
          <ul className="list-disc list-inside space-y-1 text-neutral-400 text-xs md:text-sm">
            {(pc.hot_tier_rules_plain || []).map((line, i) => (
              <li key={`h${i}`}>{line}</li>
            ))}
          </ul>
          <ul className="list-disc list-inside space-y-1 text-neutral-400 text-xs md:text-sm mt-2">
            {(pc.warm_tier_rules_plain || []).map((line, i) => (
              <li key={`w${i}`}>{line}</li>
            ))}
          </ul>
          {pc.emerging_tier && (
            <p className="text-xs text-cyan-500/90 mt-2">{pc.emerging_tier}</p>
          )}
          {pc.hot_signal_boost_note && (
            <p className="text-xs text-neutral-500 mt-2 leading-relaxed">{pc.hot_signal_boost_note}</p>
          )}
          {pc.warm_signal_boost_note && (
            <p className="text-xs text-neutral-500 mt-1 leading-relaxed">{pc.warm_signal_boost_note}</p>
          )}
        </div>

        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-orange-400/90 mb-2">
            Tunable constants (priority)
          </h3>
          <JsonBlock obj={pc.constants || {}} />
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <h4 className="text-[11px] font-bold uppercase text-neutral-500 mb-2">Hot-type signals</h4>
            <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
              {(sets.hot_types || []).map((t) => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-orange-950/50 text-orange-200 border border-orange-900/40 font-mono">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-neutral-500 mb-2">Warm-type signals</h4>
            <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
              {(sets.warm_types || []).map((t) => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/40 text-amber-200 border border-amber-900/40 font-mono">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-neutral-500 mb-2">Deployment boost set</h4>
            <div className="flex flex-wrap gap-1">
              {(sets.deployment_escalation_types || []).map((t) => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-200 border border-emerald-900/40 font-mono">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400/90 mb-2">
            Per-signal weights (card detail and ordering)
          </h3>
          <p className="text-xs text-neutral-500 mb-2">{pw.formula}</p>
          <div className="overflow-x-auto border border-neutral-800 rounded-lg">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-neutral-500 border-b border-neutral-800">
                  <th className="p-2 font-semibold">signal_type</th>
                  <th className="p-2 font-semibold">weight</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(pw.type_weights || {}).map(([k, v]) => (
                  <tr key={k} className="border-b border-neutral-800/60 hover:bg-neutral-900/50">
                    <td className="p-2 font-mono text-cyan-200/80">{k}</td>
                    <td className="p-2 text-neutral-300">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-neutral-500 mt-1">
            Default weight for unlisted types: {pw.default_type_weight}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-[11px] font-bold uppercase text-neutral-500 mb-2">Age decay (days)</h4>
            <div className="overflow-x-auto border border-neutral-800 rounded-lg">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-neutral-500 border-b border-neutral-800">
                    <th className="p-2">Range</th>
                    <th className="p-2">×</th>
                  </tr>
                </thead>
                <tbody>
                  {(pw.age_decay?.brackets || []).map((row, i) => (
                    <tr key={i} className="border-b border-neutral-800/60">
                      <td className="p-2 font-mono text-neutral-400">
                        {row.from_days}
                        {row.to_days != null ? `–${row.to_days}` : '+'} d
                      </td>
                      <td className="p-2">{row.multiplier}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-neutral-500 mt-1">
              Unknown signal age: ×{pw.age_decay?.unknown_age_multiplier}
            </p>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-neutral-500 mb-2">Text pattern multipliers</h4>
            <JsonBlock obj={pw.text_pattern_multipliers || {}} />
          </div>
        </div>

        <div>
          <h3 className="text-[11px] font-bold uppercase text-neutral-500 mb-1">High-fit industries (+boost)</h3>
          <p className="text-xs text-neutral-500 mb-2 font-mono leading-relaxed">
            {(data.high_fit_industries || []).join(', ')}
          </p>
        </div>

        <div className="text-[11px] text-neutral-600 space-y-1 border-t border-neutral-800 pt-4">
          <p className="font-semibold text-neutral-500">Change scores in code</p>
          {Object.entries(paths).map(([k, v]) => (
            <div key={k}>
              <span className="text-neutral-500">{k}: </span>
              <code className="text-cyan-500/90">{v}</code>
            </div>
          ))}
          {data.spotlight_selection?.note && (
            <p className="text-neutral-500 mt-2">{data.spotlight_selection.note}</p>
          )}
        </div>
      </div>
    </details>
  );
}
