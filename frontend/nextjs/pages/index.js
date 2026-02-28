/**
 * Ready for Robots -- Lead Intelligence Dashboard
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

// In production (Fly.io) frontend + API share the same origin — use relative URLs.
// For local dev, point to the local uvicorn server.
const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// -- helpers ----------------------------------------------------------------

function barColor(v) {
  if (v >= 75) return 'bg-emerald-500';
  if (v >= 50) return 'bg-cyan-500';
  if (v >= 30) return 'bg-yellow-600';
  return 'bg-neutral-600';
}

function ScoreBar({ value = 0, label }) {
  const pct = Math.min(100, Math.max(0, Math.round(value)));
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between">
        <span className="label">{label}</span>
        <span className="text-xs tabular-nums text-neutral-400">{pct}</span>
      </div>
      <div className="bar-track">
        <div className={`bar-fill ${barColor(pct)}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// Tier -- stroke + text only, no fill
const TIER_META = {
  HOT:  { text: 'text-red-400',    border: 'border-red-800',    borderL: 'border-l-red-800',    label: 'HOT'  },
  WARM: { text: 'text-yellow-400', border: 'border-yellow-800', borderL: 'border-l-yellow-800', label: 'WARM' },
  COLD: { text: 'text-cyan-400',   border: 'border-cyan-900',   borderL: 'border-l-cyan-900',   label: 'COLD' },
};

function TierBadge({ tier }) {
  const m = TIER_META[tier] || TIER_META.COLD;
  return (
    <span className={`badge ${m.border} ${m.text}`}>
      {tier}
    </span>
  );
}

// Signal badges -- stroke only, no fill
const SIGNAL_META = {
  funding_round:  { label: 'Funding',   border: 'border-violet-700', text: 'text-violet-400' },
  strategic_hire: { label: 'Exec Hire', border: 'border-blue-700',   text: 'text-blue-400'   },
  capex:          { label: 'CapEx',     border: 'border-cyan-700',   text: 'text-cyan-400'   },
  ma_activity:    { label: 'M&A',       border: 'border-pink-700',   text: 'text-pink-400'   },
  expansion:      { label: 'Expand',    border: 'border-emerald-800',text: 'text-emerald-400'},
  job_posting:    { label: 'Hiring',    border: 'border-amber-700',  text: 'text-amber-400'  },
  labor_shortage: { label: 'Labor Gap', border: 'border-red-800',    text: 'text-red-400'    },
  news:           { label: 'News',      border: 'border-neutral-700',text: 'text-neutral-400'},
};

function SignalBadge({ type }) {
  const m = SIGNAL_META[type] || { label: type, border: 'border-neutral-700', text: 'text-neutral-400' };
  return <span className={`badge ${m.border} ${m.text}`}>{m.label}</span>;
}

function HealthDot({ open }) {
  return (
    <span className={`inline-block h-1.5 w-1.5 rounded-full ${open ? 'bg-red-500' : 'bg-emerald-500'}`} />
  );
}

function ScoreNum({ value }) {
  const v = Math.round(value ?? 0);
  const cls = v >= 75 ? 'text-emerald-400' : v >= 50 ? 'text-cyan-400' : v >= 30 ? 'text-yellow-500' : 'text-neutral-500';
  return <span className={`tabular-nums font-mono font-semibold text-base ${cls}`}>{v}</span>;
}

const INDUSTRIES  = ['All', 'Hospitality', 'Logistics', 'Healthcare', 'Food Service'];
const SIGNAL_TYPES = ['', 'funding_round', 'strategic_hire', 'capex', 'ma_activity', 'expansion', 'job_posting', 'labor_shortage'];
const TIERS = ['ALL', 'HOT', 'WARM', 'COLD'];

const SEARCH_CATEGORIES = [
  { key: 'automation_investment', label: 'Automation Investments' },
  { key: 'acquisitions',          label: 'Acquisitions & M&A'    },
  { key: 'labor_downsizing',      label: 'Labor Downsizing'      },
  { key: 'intra_logistics',       label: 'Intra-Logistics'       },
  { key: 'pack_work',             label: 'Pack In / Pack Out'    },
  { key: 'kitting',               label: 'Kitting & Assembly'    },
  { key: 'restocking',            label: 'Restocking'            },
  { key: 'inventory_management',  label: 'Inventory Mgmt'        },
  { key: 'healthcare_automation', label: 'Healthcare Automation' },
  { key: 'retail_automation',     label: 'Retail Automation'     },
];

function uniqueSignalTypes(signals = []) {
  const seen = new Set();
  return signals.filter(s => { if (seen.has(s.signal_type)) return false; seen.add(s.signal_type); return true; });
}

// -- Top-5 per tier table -------------------------------------------------------
const TIER_TABLE_META = {
  HOT:  { label: 'HOT',  text: 'text-red-400',    border: 'border-red-900',    head: 'border-b border-red-900/40' },
  WARM: { label: 'WARM', text: 'text-yellow-400', border: 'border-yellow-900',  head: 'border-b border-yellow-900/40' },
  COLD: { label: 'COLD', text: 'text-cyan-400',   border: 'border-cyan-900',   head: 'border-b border-cyan-900/40' },
};

function TopFiveTable({ tier, leads, onFilterTier, onSelect }) {
  const m     = TIER_TABLE_META[tier];
  const items = leads.filter(l => l.priority_tier === tier).slice(0, 5);
  return (
    <div className={`border ${m.border} rounded p-4`}>
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-bold tracking-widest ${m.text}`}>{tier}</span>
        <button onClick={() => onFilterTier(tier)}
          className={`text-[10px] ${m.text} opacity-60 hover:opacity-100 transition-opacity`}>
          view all &rarr;
        </button>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-neutral-800 py-2">no {tier.toLowerCase()} leads yet</p>
      ) : (
        <table className="w-full">
          <thead>
            <tr className={`${m.head} text-left`}>
              <th className="pb-1.5 pr-3 label font-normal">#</th>
              <th className="pb-1.5 pr-3 label font-normal">company</th>
              <th className="pb-1.5 pr-2 label font-normal">ind.</th>
              <th className="pb-1.5 label font-normal text-right">score</th>
            </tr>
          </thead>
          <tbody>
            {items.map((l, i) => (
              <tr key={l.id} className="border-b border-neutral-900 cursor-pointer hover:bg-neutral-900/40 group"
                onClick={() => onSelect ? onSelect(l) : onFilterTier(tier)}>
                <td className="py-1.5 pr-3 label">{i + 1}</td>
                <td className="py-1.5 pr-3 text-xs text-neutral-200 max-w-[9rem] truncate group-hover:text-emerald-400 transition-colors" title={l.company_name}>
                  {l.company_name}
                </td>
                <td className="py-1.5 pr-2 label truncate max-w-[5rem]" title={l.industry}>
                  {(l.industry || '').split(' ')[0]}
                </td>
                <td className="py-1.5 text-right">
                  <ScoreNum value={l.score?.overall_score ?? 0} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// -- Quick scrape widget -------------------------------------------------------
function QuickScrape({ onDone }) {
  const [open,   setOpen]   = useState(false);
  const [urls,   setUrls]   = useState('');
  const [ind,    setInd]    = useState('');
  const [now,    setNow]    = useState(false);
  const [status, setStatus] = useState(null);  // null | 'loading' | 'done' | 'error'
  const [result, setResult] = useState(null);

  async function submit() {
    if (!urls.trim()) return;
    setStatus('loading');
    try {
      const r = await fetch(`${API}/api/agent/scrape/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls, industry: ind || null, scrape_now: now }),
      });
      const data = await r.json();
      setResult(data);
      setStatus('done');
      setUrls('');
      if (onDone) onDone();
    } catch {
      setStatus('error');
    }
  }

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-neutral-500 hover:text-neutral-300 transition-colors">
        <span>&#43; quick scrape &mdash; paste URLs to add as lead sources</span>
        <span className="text-neutral-700">{open ? '&#9650;' : '&#9660;'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-neutral-800">
          <textarea value={urls} onChange={e => setUrls(e.target.value)}
            rows={4} placeholder="https://www.simplyhired.com/search?q=hotel+manager&l=las+vegas&#10;https://www.linkedin.com/jobs/search/?keywords=warehouse+automation"
            className="w-full mt-3 bg-transparent border border-neutral-800 rounded px-3 py-2 text-xs
                       text-neutral-300 placeholder-neutral-700 font-mono
                       focus:outline-none focus:border-emerald-800 transition-colors resize-y" />
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="label block mb-1">industry hint</label>
              <select value={ind} onChange={e => setInd(e.target.value)}
                className="bg-transparent border border-neutral-800 rounded px-2 py-1 text-xs text-neutral-400
                           focus:outline-none focus:border-neutral-600">
                <option value="">auto-detect</option>
                {INDUSTRIES.filter(i => i !== 'All').map(i => (
                  <option key={i} value={i}>{i}</option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={now} onChange={e => setNow(e.target.checked)}
                className="accent-emerald-500" />
              <span className={now ? 'text-emerald-400' : 'text-neutral-600'}>scrape now</span>
            </label>
            <button onClick={submit} disabled={status === 'loading'}
              className="ml-auto btn-ghost border-emerald-900 text-emerald-400 hover:border-emerald-600">
              {status === 'loading' ? 'adding...' : '&#8599; add sources'}
            </button>
          </div>
          {status === 'done' && result && (
            <div className="text-xs text-emerald-500 border border-emerald-900 rounded px-3 py-2">
              &#10003; Added {result.added} source(s). {result.skipped > 0 ? `${result.skipped} already existed.` : ''}
              {result.tasks_queued > 0 ? ` ${result.tasks_queued} scrape task(s) queued.` : ''}
            </div>
          )}
          {status === 'error' && (
            <div className="text-xs text-red-500">&#9888; Failed to add sources — check API connection.</div>
          )}
        </div>
      )}
    </div>
  );
}

// -- Agent insights panel ------------------------------------------------------
const URGENCY_META = {
  NOW:     { text: 'text-red-400',    border: 'border-red-900',    label: 'ACT NOW'  },
  SOON:    { text: 'text-yellow-400', border: 'border-yellow-900', label: 'SOON'     },
  MONITOR: { text: 'text-neutral-500',border: 'border-neutral-800',label: 'MONITOR'  },
};

function AgentInsightsPanel() {
  const [open,     setOpen]     = useState(false);
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [tab,      setTab]      = useState('strategies');

  async function load() {
    if (data) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/agent/insights`);
      if (r.ok) setData(await r.json());
    } catch {}
    setLoading(false);
  }

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next) load();
  }

  const tabs = ['strategies', 'sources', 'patterns', 'targets'];

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={toggle}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs hover:bg-neutral-900/40 transition-colors">
        <span className="flex items-center gap-2">
          <span className="text-emerald-400">&#9650; ML Agent</span>
          <span className="text-neutral-600">&mdash; lead source rankings, signal patterns &amp; approach strategies</span>
        </span>
        <span className="text-neutral-700">{open ? '&#9650;' : '&#9660;'}</span>
      </button>

      {open && (
        <div className="border-t border-neutral-800">
          {loading && <p className="px-4 py-6 text-xs text-neutral-700 animate-pulse">running analysis&hellip;</p>}
          {!loading && data && (
            <div className="px-4 pb-4">
              {/* learning notes */}
              <div className="py-3 border-b border-neutral-800/60 space-y-1">
                {data.learning_notes.map((n, i) => (
                  <p key={i} className="text-xs text-neutral-300">{n}</p>
                ))}
              </div>

              {/* coverage gaps */}
              {data.coverage_gaps?.length > 0 && (
                <div className="py-3 border-b border-neutral-800/60">
                  <p className="label mb-2">coverage gaps</p>
                  <div className="space-y-1">
                    {data.coverage_gaps.map((g, i) => (
                      <p key={i} className="text-xs text-yellow-700">&#9651; {g}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* tab bar */}
              <div className="flex gap-1 mt-3 mb-4">
                {tabs.map(t => (
                  <button key={t} onClick={() => setTab(t)}
                    className={tab === t ? 'tab-active' : 'tab-inactive'}>
                    {t}
                  </button>
                ))}
              </div>

              {/* strategies tab */}
              {tab === 'strategies' && (
                <div className="space-y-3">
                  {data.top_strategies.length === 0 && <p className="text-xs text-neutral-700">No strategies yet — need more lead data.</p>}
                  {data.top_strategies.map((s, i) => {
                    const um = URGENCY_META[s.urgency] || URGENCY_META.MONITOR;
                    return (
                      <div key={i} className={`border ${um.border} rounded p-4`}>
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <span className="text-sm font-medium text-neutral-100">{s.company_name}</span>
                            <span className={`ml-2 badge ${um.border} ${um.text}`}>{um.label}</span>
                          </div>
                          <span className="label">{Math.round(s.confidence * 100)}% confidence</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          <div>
                            <span className="label block mb-0.5">contact</span>
                            <span className="text-neutral-300">{s.contact_role}</span>
                          </div>
                          <div>
                            <span className="label block mb-0.5">channel</span>
                            <span className="text-neutral-300">{s.best_channel}</span>
                          </div>
                          <div className="sm:col-span-2">
                            <span className="label block mb-0.5">lead with</span>
                            <span className="text-neutral-300">{s.pitch_angle}</span>
                          </div>
                          <div className="sm:col-span-2">
                            <span className="label block mb-1">talking points</span>
                            <ul className="space-y-1">
                              {s.talking_points.map((tp, ti) => (
                                <li key={ti} className="text-neutral-500 flex gap-2">
                                  <span className="text-emerald-800 shrink-0">&#8227;</span>{tp}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="sm:col-span-2">
                            <span className={`text-[11px] ${um.text}`}>&#9201; {s.timing_note}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* sources tab */}
              {tab === 'sources' && (
                <div>
                  {data.source_rankings.length === 0 && <p className="text-xs text-neutral-700">No source data yet.</p>}
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-neutral-800">
                        {['tier','source','leads','avg score','industries','signals'].map(h => (
                          <th key={h} className="pb-2 pr-4 label font-normal text-left">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.source_rankings.map((r, i) => (
                        <tr key={i} className="border-b border-neutral-900">
                          <td className="py-1.5 pr-4">
                            <span className={`badge ${
                              r.quality_tier === 'GOLD'   ? 'border-yellow-700 text-yellow-400' :
                              r.quality_tier === 'SILVER' ? 'border-neutral-600 text-neutral-300' :
                              r.quality_tier === 'BRONZE' ? 'border-amber-900 text-amber-600' :
                              'border-neutral-800 text-neutral-600'
                            }`}>{r.quality_tier}</span>
                          </td>
                          <td className="py-1.5 pr-4 text-neutral-300 font-mono">{r.domain}</td>
                          <td className="py-1.5 pr-4 tabular-nums text-neutral-400">{r.lead_count}</td>
                          <td className="py-1.5 pr-4">
                            <ScoreNum value={r.avg_score} />
                          </td>
                          <td className="py-1.5 pr-4 text-neutral-600 max-w-[8rem] truncate">{r.top_industries.join(', ')}</td>
                          <td className="py-1.5 text-neutral-600">{r.top_signal_types.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* patterns tab */}
              {tab === 'patterns' && (
                <div className="space-y-2">
                  {data.signal_patterns.length === 0 && <p className="text-xs text-neutral-700">No patterns detected yet.</p>}
                  {data.signal_patterns.map((p, i) => (
                    <div key={i} className="border border-neutral-800 rounded px-3 py-2.5">
                      <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                        {p.signals.map(s => (
                          <span key={s} className="badge border-emerald-800 text-emerald-400">{s}</span>
                        ))}
                        <span className="ml-auto label">{p.occurrence_count}x &middot; avg <ScoreNum value={p.avg_score} /></span>
                      </div>
                      <p className="text-xs text-neutral-300">{p.insight}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* targets tab */}
              {tab === 'targets' && (
                <div className="space-y-2">
                  <p className="text-xs text-neutral-600 mb-3">Agent-recommended scrape sources based on coverage gaps.</p>
                  {data.recommended_targets.map((t, i) => (
                    <div key={i} className="flex items-start gap-3 border border-neutral-800 rounded px-3 py-2.5">
                      <div className="flex-1 min-w-0">
                        <a href={t.url} target="_blank" rel="noreferrer"
                          className="text-xs text-cyan-600 hover:text-cyan-400 font-mono truncate block">{t.url}</a>
                        <p className="text-xs text-neutral-500 mt-0.5">{t.reason}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <span className="badge border-emerald-900 text-emerald-600">{t.expected_industry}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button onClick={() => setData(null) || load()}
                className="mt-4 btn-ghost text-neutral-600 text-[10px]">&#8635; rerun analysis</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// -- Company strategy modal -------------------------------------------------
function CompanyStrategyModal({ lead, onClose }) {
  const [strategy, setStrategy] = useState(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    fetch(`${API}/api/agent/strategy/${lead.id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setStrategy(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [lead.id]);

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const sc = lead.score || {};
  const tm = TIER_META[lead.priority_tier] || TIER_META.COLD;
  const um = strategy ? (URGENCY_META[strategy.urgency] || URGENCY_META.MONITOR) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[5vh]"
      onClick={onClose}>
      <div className="absolute inset-0 bg-black/75" />
      <div
        className="relative w-full max-w-2xl max-h-[88vh] overflow-y-auto bg-[#0c0c0c] border border-neutral-700 rounded-lg shadow-2xl"
        onClick={e => e.stopPropagation()}>

        {/* header */}
        <div className={`flex items-start justify-between px-6 py-4 border-b ${tm.border}`}>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-neutral-100">{lead.company_name}</h2>
              <TierBadge tier={lead.priority_tier} />
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-500">
              {lead.industry && <span>{lead.industry}</span>}
              {lead.location_city && (
                <span>{lead.location_city}{lead.location_state ? `, ${lead.location_state}` : ''}</span>
              )}
              {lead.employee_estimate && (
                <span>{lead.employee_estimate.toLocaleString()} employees</span>
              )}
              {lead.website && (
                <a href={lead.website} target="_blank" rel="noreferrer"
                  className="text-cyan-600 hover:text-cyan-400 transition-colors"
                  onClick={e => e.stopPropagation()}>{lead.website}</a>
              )}
            </div>
          </div>
          <button onClick={onClose}
            className="ml-4 shrink-0 text-neutral-600 hover:text-neutral-200 text-sm transition-colors px-2 py-1">
            &#10005;
          </button>
        </div>

        <div className="px-6 py-5 space-y-6">
          {/* intent scores */}
          <div>
            <p className="label mb-3">intent scores</p>
            <div className="grid grid-cols-2 gap-x-10 gap-y-3">
              <ScoreBar value={sc.overall_score     ?? 0} label="overall" />
              <ScoreBar value={sc.automation_score  ?? 0} label="automation" />
              <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
              <ScoreBar value={sc.expansion_score   ?? 0} label="expansion" />
              <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
            </div>
          </div>

          {/* approach strategy */}
          <div>
            <p className="label mb-3">approach strategy</p>
            {loading && (
              <p className="text-sm text-neutral-700 animate-pulse py-3">generating strategy&hellip;</p>
            )}
            {!loading && strategy && um && (
              <div className={`border ${um.border} rounded p-5 space-y-4`}>
                <div className="flex items-center justify-between">
                  <span className={`badge ${um.border} ${um.text}`}>{um.label}</span>
                  <span className="text-xs text-neutral-600">{Math.round(strategy.confidence * 100)}% confidence</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="label block mb-1">who to contact</span>
                    <span className="text-sm text-neutral-200">{strategy.contact_role}</span>
                  </div>
                  <div>
                    <span className="label block mb-1">best channel</span>
                    <span className="text-sm text-neutral-200">{strategy.best_channel}</span>
                  </div>
                </div>
                <div>
                  <span className="label block mb-1">lead with</span>
                  <p className="text-sm text-neutral-200 leading-relaxed">{strategy.pitch_angle}</p>
                </div>
                <div>
                  <span className="label block mb-2">talking points</span>
                  <ul className="space-y-2">
                    {(strategy.talking_points || []).map((tp, i) => (
                      <li key={i} className="flex gap-2 text-sm text-neutral-300">
                        <span className="text-emerald-700 shrink-0 mt-0.5">&#8227;</span>
                        {tp}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className={`border-t ${um.border} pt-4`}>
                  <span className="label block mb-1.5">next steps &amp; timing</span>
                  <p className={`text-sm ${um.text} leading-relaxed`}>&#9201; {strategy.timing_note}</p>
                </div>
              </div>
            )}
            {!loading && !strategy && (
              <p className="text-sm text-neutral-700 border border-neutral-800 rounded px-4 py-3">
                No strategy available &mdash; open the ML Agent panel to run analysis first.
              </p>
            )}
          </div>

          {/* signals */}
          {(lead.signals || []).length > 0 && (
            <div>
              <p className="label mb-3">signals &middot; {lead.signal_count}</p>
              <div className="space-y-2">
                {(lead.signals || []).map((s, i) => (
                  <div key={i} className="flex items-start gap-3 border border-neutral-800 rounded px-4 py-3">
                    <SignalBadge type={s.signal_type} />
                    <span className="text-sm text-neutral-400 flex-1 leading-relaxed">{s.raw_text}</span>
                    <span className={`shrink-0 text-xs font-mono tabular-nums ${
                      s.strength >= 0.7 ? 'text-emerald-500'
                      : s.strength >= 0.4 ? 'text-cyan-500'
                      : 'text-neutral-600'
                    }`}>{(s.strength * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// -- Intelligence search panel -----------------------------------------------
function IntelSearchPanel({ onOpenLead }) {
  const [open,     setOpen]     = useState(true);
  const [query,    setQuery]    = useState('');
  const [category, setCategory] = useState(null);
  const [results,  setResults]  = useState(null);
  const [loading,  setLoading]  = useState(false);

  async function runSearch(q, cat) {
    setLoading(true);
    setResults(null);
    try {
      const params = new URLSearchParams();
      if (q && q.trim())  params.set('q', q.trim());
      if (cat)            params.set('category', cat);
      params.set('limit', '30');
      const r = await fetch(`${API}/api/search?${params}`);
      if (r.ok) setResults(await r.json());
    } catch {}
    setLoading(false);
  }

  function selectCategory(key) {
    const next = category === key ? null : key;
    setCategory(next);
    if (next || query.trim()) runSearch(query, next || null);
    else setResults(null);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim() || category) runSearch(query, category);
  }

  function clearAll() {
    setQuery('');
    setCategory(null);
    setResults(null);
  }

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs hover:bg-neutral-900/40 transition-colors">
        <span className="flex items-center gap-2">
          <span className="text-cyan-400">&#8855; Intelligence Search</span>
          <span className="text-neutral-400">&mdash; investments, acquisitions, labor trends &amp; automation verticals</span>
        </span>
        <span className="text-neutral-600">{open ? '&#9650;' : '&#9660;'}</span>
      </button>

      {open && (
        <div className="border-t border-neutral-800 px-4 pb-5 pt-4 space-y-4">
          {/* category grid */}
          <div>
            <p className="label mb-2.5">quick search by category</p>
            <div className="flex flex-wrap gap-1.5">
              {SEARCH_CATEGORIES.map(cat => (
                <button key={cat.key} onClick={() => selectCategory(cat.key)}
                  className={`tab ${
                    category === cat.key
                      ? 'border-cyan-600 text-cyan-300'
                      : 'border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200'
                  }`}>
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* free-text input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Company name or keyword — e.g. 'Amazon', 'autonomous forklift', 'Series B', 'government grant'..."
              className="flex-1 bg-transparent border border-neutral-800 rounded px-3 py-2 text-sm
                         text-neutral-200 placeholder-neutral-600
                         focus:outline-none focus:border-cyan-800 focus:text-white transition-colors" />
            <button type="submit"
              className="btn border-cyan-800 text-cyan-400 hover:border-cyan-600 hover:text-cyan-300 shrink-0">
              &#8853; search
            </button>
            {(query || category || results) && (
              <button type="button" onClick={clearAll}
                className="btn border-neutral-800 text-neutral-500 hover:text-neutral-300 shrink-0">
                clear
              </button>
            )}
          </form>

          {/* loading */}
          {loading && (
            <p className="text-sm text-neutral-400 animate-pulse">searching signals&hellip;</p>
          )}

          {/* results */}
          {!loading && results && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm font-medium text-neutral-300">
                  {results.total} result{results.total !== 1 ? 's' : ''}
                </span>
                {results.category_label && (
                  <span className="badge border-cyan-800 text-cyan-400">{results.category_label}</span>
                )}
                {results.query && (
                  <span className="text-sm text-neutral-400">matching &ldquo;{results.query}&rdquo;</span>
                )}
              </div>

              {results.total === 0 ? (
                <p className="text-sm text-neutral-400 border border-neutral-800 rounded px-3 py-3">
                  No results found. Try a different category, or type a company name like &ldquo;Marriott&rdquo; or a keyword like &ldquo;AMR&rdquo;.
                </p>
              ) : (
                <div className="space-y-2">
                  {results.results.map(r => (
                    <div key={r.id}
                      className="border border-neutral-800 rounded px-4 py-3 hover:border-neutral-600 transition-colors group">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-base font-semibold text-neutral-100 group-hover:text-white transition-colors">
                            {r.company_name}
                          </span>
                          {r.industry && (
                            <span className="label text-neutral-400">{r.industry}</span>
                          )}
                          {r.location_city && (
                            <span className="label text-neutral-500">
                              {r.location_city}{r.location_state ? `, ${r.location_state}` : ''}
                            </span>
                          )}
                          {r.match_source === 'name' && !r.matched_signals?.length && (
                            <span className="badge border-neutral-700 text-neutral-400">name match</span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <ScoreNum value={r.overall_score} />
                          <button onClick={() => onOpenLead && onOpenLead(r)}
                            className="text-xs text-cyan-500 hover:text-cyan-300 transition-colors">
                            view &#8594;
                          </button>
                        </div>
                      </div>
                      {r.matched_signals?.length > 0 && (
                        <div className="space-y-1.5 mt-1">
                          {r.matched_signals.map((s, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <SignalBadge type={s.signal_type} />
                              <span className="text-xs text-neutral-300 flex-1 leading-relaxed">{s.signal_text}</span>
                              <span className={`shrink-0 text-xs font-mono tabular-nums ${
                                s.strength >= 0.7 ? 'text-emerald-400'
                                : s.strength >= 0.4 ? 'text-cyan-500'
                                : 'text-neutral-600'
                              }`}>{(s.strength * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// -- main page --------------------------------------------------------------
export default function Dashboard() {
  const [leads, setLeads]         = useState([]);
  const [summary, setSummary]     = useState({});
  const [health, setHealth]       = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [expanded, setExpanded]   = useState({});
  const [lastRefresh, setLast]    = useState(null);
  const [resetting, setResetting] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  // filter state
  const [search, setSearch]           = useState('');
  const [tier, setTier]               = useState('ALL');
  const [industry, setIndustry]       = useState('All');
  const [minScore, setMinScore]       = useState(0);
  const [sigType, setSigType]         = useState('');
  const [excludeJunk, setExcludeJunk] = useState(true);
  const [sort, setSort]               = useState('score');

  const buildQuery = useCallback(() => {
    const p = new URLSearchParams();
    p.set('exclude_junk', excludeJunk);
    p.set('min_score', minScore);
    p.set('sort', sort);
    if (tier !== 'ALL')     p.set('tier', tier);
    if (industry !== 'All') p.set('industry', industry);
    if (sigType)            p.set('signal_type', sigType);
    return p.toString();
  }, [tier, industry, minScore, sigType, excludeJunk, sort]);

  const fetchData = useCallback(async () => {
    try {
      const [leadsRes, summaryRes, healthRes] = await Promise.all([
        fetch(`${API}/api/leads?${buildQuery()}`),
        fetch(`${API}/api/leads/summary?exclude_junk=${excludeJunk}`),
        fetch(`${API}/api/scraper-health`),
      ]);
      if (leadsRes.ok)   setLeads(await leadsRes.json());
      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (healthRes.ok)  setHealth(await healthRes.json());
      setError(null);
    } catch (e) {
      setError('Cannot reach API -- start the server: python -m uvicorn app.main:app --reload');
    } finally {
      setLoading(false);
      setLast(new Date().toLocaleTimeString());
    }
  }, [buildQuery, excludeJunk]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    const t = setInterval(fetchData, 30_000);
    return () => clearInterval(t);
  }, [fetchData]);

  const filtered = leads.filter(l =>
    !search || (l.company_name || '').toLowerCase().includes(search.toLowerCase())
  );

  async function handleResetAll() {
    setResetting(true);
    await fetch(`${API}/api/scraper-health/reset-all`, { method: 'POST' });
    await fetchData();
    setResetting(false);
  }

  function handleOpenFromSearch(searchResult) {
    // Try to find the full cached lead first
    const found = leads.find(l => l.id === searchResult.id);
    if (found) {
      setSelectedLead(found);
    } else {
      // Construct minimal lead for the modal from search result
      const tier = searchResult.overall_score >= 75 ? 'HOT'
                 : searchResult.overall_score >= 45 ? 'WARM' : 'COLD';
      setSelectedLead({
        ...searchResult,
        priority_tier: tier,
        score: {
          overall_score:    searchResult.overall_score,
          automation_score: 0,
          labor_pain_score: 0,
          expansion_score:  0,
          market_fit_score: 0,
        },
        signals: (searchResult.matched_signals || []).map(s => ({
          signal_type: s.signal_type,
          strength:    s.strength,
          raw_text:    s.signal_text,
          source_url:  '',
        })),
        signal_count: searchResult.matched_signals?.length || 0,
      });
    }
  }

  const openCircuits = health?.circuit_open_urls?.length ?? 0;

  return (
    <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1400px] mx-auto">

      {selectedLead && (
        <CompanyStrategyModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}

      {/* header */}
      <header className="mb-10 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-bold tracking-tight text-white">Ready for Robots</h1>
            <span className="label border border-neutral-700 rounded px-2 py-0.5 text-neutral-300">RICHTECH ROBOTICS</span>
          </div>
          <p className="text-base text-neutral-300">Lead Intelligence &middot; Automation Signal Platform</p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && <span className="label text-neutral-500">{lastRefresh}</span>}
          <button onClick={fetchData} className="btn-ghost">&#8635; refresh</button>
          <Link href="/admin" className="btn-ghost text-emerald-400 border-emerald-900 hover:border-emerald-700">&#9881; admin</Link>
        </div>
      </header>

      {/* error */}
      {error && (
        <div className="mb-6 border border-red-900 rounded px-4 py-3 text-red-400 text-xs">
          &#9888; {error}
        </div>
      )}

      {/* quick scrape */}
      <QuickScrape onDone={fetchData} />

      {/* stat row -- inline text, no cards */}
      <div className="mb-8 flex flex-wrap items-center gap-6 border-b border-neutral-800 pb-6">
        <div>
          <span className="label block mb-0.5">Total Leads</span>
          <span className="text-3xl font-semibold text-neutral-200 tabular-nums">
            {summary.total ?? leads.length}
          </span>
        </div>
        <div className="w-px h-6 bg-neutral-800" />
        <div>
          <span className="label block mb-0.5">Hot</span>
          <span className="text-3xl font-semibold text-red-400 tabular-nums">{summary.hot ?? 0}</span>
        </div>
        <div>
          <span className="label block mb-0.5">Warm</span>
          <span className="text-3xl font-semibold text-yellow-500 tabular-nums">{summary.warm ?? 0}</span>
        </div>
        <div>
          <span className="label block mb-0.5">Cold</span>
          <span className="text-3xl font-semibold text-cyan-500 tabular-nums">{summary.cold ?? 0}</span>
        </div>
        <div className="w-px h-6 bg-neutral-800" />
        <div>
          <span className="label block mb-0.5">Junk filtered</span>
          <span className="text-3xl font-semibold text-neutral-700 tabular-nums">{summary.junk_filtered ?? 0}</span>
        </div>
        {openCircuits > 0 && (
          <>
            <div className="w-px h-6 bg-neutral-800" />
            <div>
              <span className="label block mb-0.5">Open circuits</span>
              <span className="text-xl font-semibold text-red-500 tabular-nums">&#9889; {openCircuits}</span>
            </div>
          </>
        )}
      </div>

      {/* top-5 per tier */}
      {!loading && leads.length > 0 && (
        <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          {['HOT','WARM','COLD'].map(t => (
            <TopFiveTable key={t} tier={t} leads={leads}
              onSelect={setSelectedLead}
              onFilterTier={t => { setTier(t); setIndustry('All'); setSearch(''); }} />
          ))}
        </div>
      )}

      {/* intelligence search */}
      <IntelSearchPanel onOpenLead={handleOpenFromSearch} />

      {/* agent insights */}
      <AgentInsightsPanel />

      {/* filter bar */}
      <div className="mb-6 space-y-3">
        {/* row 1 */}
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="label block mb-1">Search</label>
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="company name..."
              className="w-full bg-transparent border border-neutral-800 rounded px-3 py-1.5 text-sm
                         text-neutral-300 placeholder-neutral-700
                         focus:outline-none focus:border-emerald-700 focus:text-neutral-100
                         transition-colors" />
          </div>
          <div>
            <label className="label block mb-1">Min score -- <span className="text-emerald-500">{minScore}</span></label>
            <input type="range" min={0} max={100} value={minScore}
              onChange={e => setMinScore(Number(e.target.value))}
              className="w-32 accent-emerald-500" />
          </div>
          <div>
            <label className="label block mb-1">Sort</label>
            <select value={sort} onChange={e => setSort(e.target.value)}
              className="bg-transparent border border-neutral-800 rounded px-2 py-1.5 text-xs
                         text-neutral-400 focus:outline-none focus:border-neutral-600">
              <option value="score">by score</option>
              <option value="signals">by signals</option>
              <option value="name">by name</option>
            </select>
          </div>
          <label className="flex items-center gap-2 cursor-pointer select-none mb-0.5">
            <input type="checkbox" checked={excludeJunk} onChange={e => setExcludeJunk(e.target.checked)}
              className="sr-only peer" />
            <span className="text-xs transition-colors peer-checked:text-emerald-400 text-neutral-600">
              {excludeJunk ? 'hide junk' : 'show junk'}
            </span>
          </label>
        </div>

        {/* row 2 -- filter tabs */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div className="flex items-center gap-1.5">
            <span className="label mr-1">priority</span>
            {TIERS.map(t => (
              <button key={t} onClick={() => setTier(t)}
                className={tier === t ? 'tab-active' : 'tab-inactive'}>
                {t === 'HOT' ? 'HOT' : t === 'WARM' ? 'WARM' : t === 'COLD' ? 'COLD' : 'ALL'}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-neutral-800" />
          <div className="flex items-center gap-1.5">
            <span className="label mr-1">industry</span>
            {INDUSTRIES.map(ind => (
              <button key={ind} onClick={() => setIndustry(ind)}
                className={industry === ind ? 'tab-active' : 'tab-inactive'}>
                {ind.toLowerCase()}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-neutral-800" />
          <div className="flex items-center gap-2">
            <span className="label">signal</span>
            <select value={sigType} onChange={e => setSigType(e.target.value)}
              className="bg-transparent border border-neutral-800 rounded px-2 py-0.5 text-xs
                         text-neutral-500 focus:outline-none focus:border-neutral-600">
              <option value="">any</option>
              {SIGNAL_TYPES.filter(Boolean).map(st => (
                <option key={st} value={st}>{SIGNAL_META[st]?.label || st}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* lead list */}
      {loading ? (
        <p className="py-16 text-center text-neutral-700 text-sm animate-pulse">loading...</p>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-neutral-700 text-sm">
          no leads match your filters
          {leads.length === 0 && (
            <p className="mt-2 text-xs text-neutral-800">
              run <code className="border border-neutral-800 rounded px-1 text-neutral-600">python scripts/test_scraper.py --clear</code> to seed
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-px">
          {filtered.map((lead, i) => {
            const sc     = lead.score || {};
            const isOpen = expanded[lead.id];
            const tm     = TIER_META[lead.priority_tier] || TIER_META.COLD;

            return (
              <div key={lead.id}
                className={`border-b border-neutral-800/60 py-3 ${
                  isOpen ? `border-l-2 pl-3 ${tm.borderL}` : 'pl-0'
                }`}>

                {/* row header */}
                <div className="flex cursor-pointer items-start gap-4"
                  onClick={() => setExpanded(p => ({ ...p, [lead.id]: !p[lead.id] }))}>

        <span className="label w-6 text-right shrink-0 mt-0.5">#{i+1}</span>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-lg font-semibold text-neutral-100">{lead.company_name}</span>
                      <TierBadge tier={lead.priority_tier} />
                      {lead.industry && <span className="label">{lead.industry}</span>}
                      {lead.location_city && (
                        <span className="label">
                          {lead.location_city}{lead.location_state ? `, ${lead.location_state}` : ''}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {uniqueSignalTypes(lead.signals || []).map(s => (
                        <SignalBadge key={s.signal_type} type={s.signal_type} />
                      ))}
                    </div>
                  </div>

                  {/* score -- text only, no pill bg */}
                  <div className="shrink-0 text-right">
                    <ScoreNum value={sc.overall_score ?? 0} />
                    <span className="label block">score</span>
                  </div>

                  <span className={`label mt-1 ${tm.text}`}>{isOpen ? 'v' : '>'}</span>
                </div>

                {/* score bars */}
                <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-5 pl-10">
                  <ScoreBar value={sc.automation_score ?? 0} label="automation" />
                  <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
                  <ScoreBar value={sc.expansion_score   ?? 0} label="expansion"  />
                  <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
                  <ScoreBar value={sc.overall_score     ?? 0} label="overall"    />
                </div>

                {/* priority reasons -- inline text */}
                {lead.priority_reasons?.length > 0 && (
                  <p className="mt-2 pl-10 text-xs text-neutral-500">
                    {lead.priority_reasons.join('  ·  ')}
                  </p>
                )}

                {/* expanded drawer */}
                {isOpen && (
                  <div className="mt-4 pl-10 space-y-4">
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs">
                      {lead.website && (
                        <a href={lead.website} target="_blank" rel="noreferrer"
                          className="text-cyan-600 hover:text-cyan-400 transition-colors">
                          {lead.website}
                        </a>
                      )}
                      {lead.employee_estimate && (
                        <span className="text-neutral-400">
                          {lead.employee_estimate.toLocaleString()} employees
                        </span>
                      )}
                      <span className={`font-mono ${tm.text}`}>
                        priority {lead.priority_score}
                      </span>
                    </div>

                    {(lead.signals || []).length > 0 && (
                      <div>
                        <p className="label mb-2">signals &middot; {lead.signal_count}</p>
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-neutral-800 text-left">
                              <th className="pb-1 pr-4 label font-normal">type</th>
                              <th className="pb-1 pr-4 label font-normal">strength</th>
                              <th className="pb-1 pr-4 label font-normal">source</th>
                              <th className="pb-1 label font-normal">summary</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(lead.signals || []).map((s, si) => (
                              <tr key={si} className="border-b border-neutral-900 align-top">
                                <td className="py-1.5 pr-4"><SignalBadge type={s.signal_type} /></td>
                                <td className="py-1.5 pr-4 tabular-nums">
                                  <span className={`font-mono ${
                                    s.strength >= 0.7 ? 'text-emerald-400'
                                    : s.strength >= 0.4 ? 'text-cyan-500'
                                    : 'text-neutral-600'
                                  }`}>
                                    {(s.strength * 100).toFixed(0)}%
                                  </span>
                                </td>
                                <td className="py-1.5 pr-4">
                                  {s.source_url
                                    ? <a href={s.source_url} target="_blank" rel="noreferrer"
                                        className="text-cyan-700 hover:text-cyan-500">&#8599;</a>
                                    : <span className="text-neutral-800">&mdash;</span>}
                                </td>
                                <td className="py-1.5 text-neutral-400 max-w-xs truncate">
                                  {s.raw_text || '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* scraper health */}
      {health && (
        <div className="mt-12 border-t border-neutral-800 pt-6">
          <div className="flex items-center justify-between mb-4">
            <span className="label">scraper health</span>
            <button onClick={handleResetAll} disabled={resetting || openCircuits === 0}
              className="btn-danger">
              {resetting ? 'resetting...' : 'reset circuits'}
            </button>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs mb-4 text-neutral-600">
            <span>tracked &mdash; <span className="text-neutral-400">{health.summary?.total_urls_tracked ?? 0}</span></span>
            <span>healthy &mdash; <span className="text-emerald-500">{health.summary?.healthy_urls ?? 0}</span></span>
            {openCircuits > 0 && <span className="text-red-500">open &mdash; {openCircuits}</span>}
            {health.summary?.last_run_scraper && (
              <span>
                last run &mdash; {health.summary.last_run_scraper}{' '}
                <span className={health.summary.last_run_status === 'success' ? 'text-emerald-500' : 'text-red-500'}>
                  {health.summary.last_run_status}
                </span>
              </span>
            )}
          </div>

          {Object.keys(health.url_health || {}).length > 0 ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-neutral-800">
                  {['', 'url', 'failures', 'restarts', 'last seen'].map(h => (
                    <th key={h} className="label pb-2 pr-6 text-left font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(health.url_health).map(([url, info]) => (
                  <tr key={url} className="border-b border-neutral-900">
                    <td className="py-1.5 pr-4"><HealthDot open={info.circuit_open} /></td>
                    <td className="py-1.5 pr-6 max-w-[14rem] truncate text-neutral-600" title={url}>
                      {url.replace(/^https?:\/\//, '').substring(0, 45)}
                    </td>
                    <td className="py-1.5 pr-6 tabular-nums text-neutral-600">{info.consecutive_failures}</td>
                    <td className="py-1.5 pr-6 tabular-nums text-neutral-600">{info.restart_count}</td>
                    <td className="py-1.5 text-neutral-700">
                      {info.last_success
                        ? new Date(info.last_success * 1000).toLocaleTimeString()
                        : 'never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-neutral-800">no urls tracked -- run a scraper first</p>
          )}
        </div>
      )}

      <footer className="mt-16 text-center label">
        ready for robots &middot; richtech robotics &middot; refreshes every 30s
      </footer>
    </div>
  );
}
