const FACTOR_LABELS = {
  readiness: 'Readiness',
  useCase: 'Use case fit',
  roi: 'ROI pressure',
  deploymentSize: 'Deployment size',
  recognizableProblem: 'Recognizable problem',
  customerValue: 'Customer value',
};

export default function ScoutScoreBreakdown({ score }) {
  const factors = score?.factors || {};
  const weights = score?.weights || {};
  const total = Math.round(score?.total ?? 0);
  const band = score?.band || 'Monitoring';

  return (
    <section className="scout-card p-5">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <p className="scout-kicker">SCOUT Score</p>
          <h2 className="text-2xl font-black text-white">{band}</h2>
        </div>
        <div className="scout-score-orb">{total}</div>
      </div>
      <div className="space-y-3">
        {Object.entries(FACTOR_LABELS).map(([key, label]) => {
          const value = Number(factors[key] || 0);
          const max = Number(weights[key] || 1);
          const pct = Math.max(0, Math.min(100, (value / max) * 100));
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">{label}</span>
                <span className="font-mono text-teal-300">{Math.round(value)}/{max}</span>
              </div>
              <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                <div className="h-full rounded-full scout-gradient" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
      {score?.summary && <p className="mt-4 text-sm text-slate-300 leading-relaxed">{score.summary}</p>}
    </section>
  );
}
