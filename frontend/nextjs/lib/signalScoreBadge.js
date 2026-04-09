/**
 * Signal score — aggregate weighted evidence per lead (type × age × text boosts).
 * Matches API `score.signal_score` / CRM `signal_score`.
 */
export function SignalScoreBadge({ value, className = '' }) {
  const v = Math.round(Number(value) || 0);
  let ring = 'border-teal-800 text-teal-400';
  if (v >= 75) ring = 'border-teal-500 text-teal-200';
  else if (v >= 50) ring = 'border-teal-600 text-teal-300';
  else if (v >= 30) ring = 'border-cyan-800 text-cyan-400';
  return (
    <span
      className={`inline-flex items-center border rounded-md px-2 py-0.5 tabular-nums font-mono font-bold text-xs ${ring} ${className}`.trim()}
      title="Signal score — mean of top weighted signal rows (type, freshness, keywords)"
    >
      {v}
    </span>
  );
}

export function SignalScoreLabel({ className = '' }) {
  return (
    <span className={`text-[10px] uppercase tracking-wide text-teal-600 ${className}`.trim()}>
      signal
    </span>
  );
}

/** Pipeline deal value (intent + firmographics) — matches dashboard ValueNum styling */
export function LeadValueBadge({ value, className = '' }) {
  const v = Math.round(Number(value) || 0);
  let badgeClass = 'border-violet-900 text-violet-400';
  if (v >= 75) badgeClass = 'border-violet-500 text-violet-200';
  else if (v >= 50) badgeClass = 'border-violet-600 text-violet-300';
  else if (v >= 30) badgeClass = 'border-violet-800 text-violet-400';
  return (
    <span
      className={`inline-flex items-center border rounded-md px-2 py-0.5 tabular-nums font-mono font-bold text-xs ${badgeClass} ${className}`.trim()}
      title="Lead value score"
    >
      {v}
    </span>
  );
}

/**
 * Compact legend for pipeline + CRM tables (colors match Signal / Value / Intent badges).
 */
export function PipelineScoreLegend({ className = '', showTier = false }) {
  return (
    <div
      role="note"
      className={`rounded-md border border-neutral-800/90 bg-zinc-950/50 px-3 py-2 text-[11px] leading-snug text-neutral-500 ${className}`.trim()}
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-600 mb-1.5">
        Score key
      </p>
      <ul className="flex flex-wrap gap-x-4 gap-y-1.5">
        <li className="flex items-center gap-2 min-w-0">
          <span className="shrink-0 h-2.5 w-2.5 rounded-sm border-2 border-teal-500 bg-teal-950/40" aria-hidden />
          <span>
            <span className="text-teal-600/90 font-medium">Signal</span>
            {' — '}weighted evidence (type, age, text)
          </span>
        </li>
        <li className="flex items-center gap-2 min-w-0">
          <span className="shrink-0 h-2.5 w-2.5 rounded-sm border-2 border-violet-500 bg-violet-950/30" aria-hidden />
          <span>
            <span className="text-violet-400/90 font-medium">Value</span>
            {' — '}deal quality (intent + firmographics + timing)
          </span>
        </li>
        {!showTier && (
          <li className="flex items-center gap-2 min-w-0">
            <span className="shrink-0 h-2.5 w-2.5 rounded-sm border-2 border-emerald-600 bg-emerald-950/30" aria-hidden />
            <span>
              <span className="text-emerald-500/90 font-medium">Intent</span>
              {' — '}ML model score on rows & snapshot
            </span>
          </li>
        )}
        {showTier && (
          <li className="flex items-baseline gap-2 flex-wrap min-w-0">
            <span className="text-neutral-400 font-medium">Tier</span>
            <span className="text-neutral-600">—</span>
            <span className="text-red-400 font-semibold text-[10px]">HOT</span>
            <span className="text-amber-400 font-medium text-[10px]">WARM</span>
            <span className="text-cyan-400 text-[10px]">COLD</span>
            <span className="text-neutral-600">pipeline priority when linked</span>
          </li>
        )}
      </ul>
      {showTier && (
        <p className="mt-2 text-[10px] text-neutral-600 border-t border-neutral-800/80 pt-2">
          Link a company ID to pull live Signal, Value, and Tier from the same pipeline as the dashboard.
        </p>
      )}
    </div>
  );
}
