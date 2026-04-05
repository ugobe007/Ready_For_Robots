/** Turn taxonomy id into readable label */
function fmtId(id) {
  return String(id || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Renders API `automation_profile` (rules_v1) on lead cards.
 * @param {{ profile?: object, compact?: boolean, theme?: 'home' | 'dashboard' }} props
 */
export function AutomationSpecBlock({ profile, compact = false, theme = 'home' }) {
  if (!profile || typeof profile !== 'object') return null;

  const apps = Array.isArray(profile.application_areas) ? profile.application_areas : [];
  const robots = Array.isArray(profile.robot_categories) ? profile.robot_categories : [];
  const deploy = Array.isArray(profile.deployment_contexts) ? profile.deployment_contexts : [];
  const collab = String(profile.human_robot_collaboration || '').trim();
  const sizing = String(profile.sizing_notes || '').trim();
  const conf = String(profile.confidence || '').trim();

  const hasLists = apps.length || robots.length || deploy.length;
  if (!hasLists && !collab && !sizing) return null;

  const chip =
    theme === 'dashboard'
      ? 'text-[11px] font-medium border border-cyan-700/60 text-zinc-100 bg-cyan-950/35 px-1.5 py-0.5 rounded shadow-sm'
      : 'text-[11px] font-medium border border-violet-600/50 text-violet-50 bg-violet-950/35 px-1.5 py-0.5 rounded shadow-sm';

  const titleCls =
    theme === 'dashboard'
      ? 'text-xs font-semibold text-zinc-200 uppercase tracking-wide'
      : 'text-xs font-semibold text-neutral-200 uppercase tracking-wide';

  const subCls =
    theme === 'dashboard'
      ? 'text-[10px] font-semibold text-zinc-400 uppercase tracking-wider'
      : 'text-[10px] font-semibold text-neutral-400 uppercase tracking-wider';

  const wrapCls =
    theme === 'dashboard'
      ? 'rounded-lg border border-zinc-700/90 bg-zinc-900/60 p-3 space-y-2.5'
      : 'rounded-lg border border-violet-800/50 bg-violet-950/15 p-3 space-y-2.5';

  if (compact) {
    const bits = [...robots.slice(0, 3).map(fmtId), ...apps.slice(0, 2).map(fmtId)].filter(Boolean);
    if (bits.length === 0 && sizing) {
      return (
        <p className={`text-xs ${theme === 'dashboard' ? 'text-zinc-300' : 'text-neutral-300'} line-clamp-2`}>
          {sizing.slice(0, 160)}
          {sizing.length > 160 ? '…' : ''}
        </p>
      );
    }
    if (bits.length === 0) return null;
    return (
      <p className={`text-xs ${theme === 'dashboard' ? 'text-zinc-200' : 'text-neutral-200'}`}>
        <span className={theme === 'dashboard' ? 'text-cyan-400' : 'text-violet-300'}>Spec · </span>
        {bits.join(' · ')}
      </p>
    );
  }

  return (
    <div className={wrapCls}>
      <div className="flex items-center justify-between gap-2">
        <div className={titleCls}>Automation spec</div>
        {conf && (
          <span
            className={`text-[10px] font-medium uppercase ${theme === 'dashboard' ? 'text-zinc-400' : 'text-neutral-400'}`}
          >
            {conf} confidence
          </span>
        )}
      </div>

      {deploy.length > 0 && (
        <div>
          <div className={subCls}>Deployment</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {deploy.map((d) => (
              <span key={d} className={chip}>
                {fmtId(d)}
              </span>
            ))}
          </div>
        </div>
      )}

      {apps.length > 0 && (
        <div>
          <div className={subCls}>Applications</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {apps.map((a) => (
              <span key={a} className={chip}>
                {fmtId(a)}
              </span>
            ))}
          </div>
        </div>
      )}

      {robots.length > 0 && (
        <div>
          <div className={subCls}>Robot types</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {robots.map((r) => (
              <span key={r} className={chip}>
                {fmtId(r)}
              </span>
            ))}
          </div>
        </div>
      )}

      {collab && (
        <p className={`text-sm leading-relaxed ${theme === 'dashboard' ? 'text-zinc-200' : 'text-neutral-200'}`}>
          <span className={`${subCls} block mb-1`}>Human–robot</span>
          {collab}
        </p>
      )}

      {sizing && (
        <p className={`text-sm leading-relaxed ${theme === 'dashboard' ? 'text-zinc-300' : 'text-neutral-300'}`}>
          {sizing}
        </p>
      )}
    </div>
  );
}
