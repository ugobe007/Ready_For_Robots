/**
 * Ready for Robots -- Lead Intelligence Dashboard
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 */
import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
        <span className="text-[10px] tabular-nums text-neutral-500">{pct}</span>
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
  return <span className={`tabular-nums font-mono font-semibold text-sm ${cls}`}>{v}</span>;
}

const INDUSTRIES  = ['All', 'Hospitality', 'Logistics', 'Healthcare', 'Food Service'];
const SIGNAL_TYPES = ['', 'funding_round', 'strategic_hire', 'capex', 'ma_activity', 'expansion', 'job_posting', 'labor_shortage'];
const TIERS = ['ALL', 'HOT', 'WARM', 'COLD'];

function uniqueSignalTypes(signals = []) {
  const seen = new Set();
  return signals.filter(s => { if (seen.has(s.signal_type)) return false; seen.add(s.signal_type); return true; });
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

  const openCircuits = health?.circuit_open_urls?.length ?? 0;

  return (
    <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1400px] mx-auto">

      {/* header */}
      <header className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-emerald-400 text-lg font-bold">&diams;</span>
            <h1 className="text-base font-semibold tracking-tight text-neutral-100">Ready for Robots</h1>
            <span className="label border border-neutral-800 rounded px-1.5 py-0.5">RICHTECH ROBOTICS</span>
          </div>
          <p className="text-xs text-neutral-600 pl-7">Lead Intelligence &middot; Automation Signal Platform</p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && <span className="label text-neutral-700">{lastRefresh}</span>}
          <button onClick={fetchData} className="btn-ghost">&#8635; refresh</button>
        </div>
      </header>

      {/* error */}
      {error && (
        <div className="mb-6 border border-red-900 rounded px-4 py-3 text-red-400 text-xs">
          &#9888; {error}
        </div>
      )}

      {/* stat row -- inline text, no cards */}
      <div className="mb-8 flex flex-wrap items-center gap-6 border-b border-neutral-800 pb-6">
        <div>
          <span className="label block mb-0.5">Total Leads</span>
          <span className="text-xl font-semibold text-neutral-200 tabular-nums">
            {summary.total ?? leads.length}
          </span>
        </div>
        <div className="w-px h-6 bg-neutral-800" />
        <div>
          <span className="label block mb-0.5">Hot</span>
          <span className="text-xl font-semibold text-red-400 tabular-nums">{summary.hot ?? 0}</span>
        </div>
        <div>
          <span className="label block mb-0.5">Warm</span>
          <span className="text-xl font-semibold text-yellow-500 tabular-nums">{summary.warm ?? 0}</span>
        </div>
        <div>
          <span className="label block mb-0.5">Cold</span>
          <span className="text-xl font-semibold text-cyan-500 tabular-nums">{summary.cold ?? 0}</span>
        </div>
        <div className="w-px h-6 bg-neutral-800" />
        <div>
          <span className="label block mb-0.5">Junk filtered</span>
          <span className="text-xl font-semibold text-neutral-700 tabular-nums">{summary.junk_filtered ?? 0}</span>
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
                      <span className="font-medium text-neutral-100">{lead.company_name}</span>
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
                  <p className="mt-2 pl-10 text-[11px] text-neutral-700">
                    {lead.priority_reasons.join('  ')}
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
                        <span className="text-neutral-600">
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
                                <td className="py-1.5 text-neutral-600 max-w-xs truncate">
                                  {s.raw_text || '&mdash;'}
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
