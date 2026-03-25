/**
 * Renders industry_strategic brief from /api/daily-report or newsletter `industryBrief`.
 */
function formatBriefTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export default function IndustryBriefBlock({ brief, className = '' }) {
  if (!brief || !(brief.executive_take || '').trim()) return null;

  const sourceLabel =
    brief.source === 'openai'
      ? 'AI synthesis (live signals)'
      : 'Signal-based summary';

  return (
    <section
      className={`border border-violet-800/50 rounded-lg p-6 bg-gradient-to-br from-violet-950/30 to-neutral-950/40 ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-violet-300">
          Strategic industry brief
        </h2>
        <div className="flex flex-wrap items-center gap-2 text-[10px] text-neutral-500">
          {brief.period_days != null && (
            <span className="px-2 py-0.5 rounded border border-neutral-700">
              Last {brief.period_days}d window
            </span>
          )}
          <span className="px-2 py-0.5 rounded border border-violet-800/60 text-violet-400/90">
            {sourceLabel}
          </span>
          {formatBriefTime(brief.generated_at) && (
            <span>{formatBriefTime(brief.generated_at)}</span>
          )}
        </div>
      </div>

      <p className="text-sm text-neutral-200 leading-relaxed mb-6">{brief.executive_take}</p>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-xs font-semibold text-violet-400/90 uppercase tracking-wider mb-3">
            Macro trends
          </h3>
          <ul className="space-y-3 text-sm text-neutral-300">
            {(brief.macro_trends || []).map((t, i) => (
              <li key={i}>
                <span className="text-neutral-100 font-medium">
                  {typeof t === 'object' ? t.title : 'Trend'}:{' '}
                </span>
                <span className="text-neutral-400">
                  {typeof t === 'object' ? t.detail : t}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-violet-400/90 uppercase tracking-wider mb-3">
            Strategic implications
          </h3>
          <ul className="space-y-3 text-sm text-neutral-300">
            {(brief.strategic_implications || []).map((s, i) => (
              <li key={i}>
                <span className="text-cyan-400/90 font-medium">
                  {typeof s === 'object' ? s.audience || s.for_who || 'Stakeholders' : 'Stakeholders'}
                  :{' '}
                </span>
                <span className="text-neutral-400">
                  {typeof s === 'object' ? s.insight || s.detail : s}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-neutral-800">
        <div>
          <h3 className="text-xs font-semibold text-amber-500/90 uppercase tracking-wider mb-2">
            Risks & unknowns
          </h3>
          <ul className="list-disc list-inside text-xs text-neutral-500 space-y-1">
            {(brief.risks_and_unknowns || []).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-emerald-500/90 uppercase tracking-wider mb-2">
            What to watch
          </h3>
          <ul className="list-disc list-inside text-xs text-neutral-500 space-y-1">
            {(brief.watch_next || []).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
