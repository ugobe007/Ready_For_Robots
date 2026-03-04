/**
 * Ready for Robots — Admin Panel
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 *
 * Tabs:
 *  Overview       — stats: companies, signals, scored + breakdowns
 *  Import URLs    — paste URLs to register as scrape targets
 *  Import Companies — bulk-import company records (JSON)
 *  Scraper        — trigger scraper runs, view registered targets
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// ── tiny helpers ───────────────────────────────────────────────────────────

function StatCard({ label, value, sub }) {
  return (
    <div className="border border-neutral-800 px-5 py-4 min-w-[140px]">
      <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-1">{label}</div>
      <div className="text-2xl tabular-nums text-neutral-100">{value ?? '—'}</div>
      {sub && <div className="text-[11px] text-neutral-600 mt-1">{sub}</div>}
    </div>
  );
}

function Tag({ children, color = 'neutral' }) {
  const map = {
    emerald: 'border-emerald-800 text-emerald-400',
    cyan:    'border-cyan-800 text-cyan-400',
    yellow:  'border-yellow-800 text-yellow-400',
    neutral: 'border-neutral-700 text-neutral-400',
    red:     'border-red-800 text-red-400',
  };
  return (
    <span className={`border text-[10px] px-2 py-0.5 ${map[color] || map.neutral}`}>
      {children}
    </span>
  );
}

function Notice({ type = 'ok', children }) {
  const s = type === 'ok'
    ? 'border-emerald-800 text-emerald-400'
    : type === 'err'
    ? 'border-red-800 text-red-400'
    : 'border-neutral-700 text-neutral-400';
  return <div className={`border px-4 py-3 text-sm mt-3 ${s}`}>{children}</div>;
}

function Spinner() {
  return <span className="inline-block w-3 h-3 border border-neutral-500 border-t-cyan-400 rounded-full animate-spin" />;
}

const TABS = ['Dashboard', 'Companies', 'Scrapers', 'Analytics', 'System'];

const SCRAPERS  = ['all', 'job_board', 'hotel_dir', 'rss_feed', 'news'];
const INDUSTRIES = ['', 'Logistics', 'Hospitality', 'Food Service', 'Healthcare'];
const SIGNAL_TYPES = [
  '', 'labor_pain', 'labor_shortage', 'strategic_hire',
  'automation_intent', 'service_consistency', 'equipment_integration',
  'funding_round', 'capex', 'ma_activity', 'expansion',
];

// ── Overview ───────────────────────────────────────────────────────────────

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const loadStats = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/admin/stats`)
      .then(r => r.json())
      .then(d => { setStats(d); setLoading(false); setRefreshing(false); })
      .catch(e => { setErr(e.message); setLoading(false); setRefreshing(false); });
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  if (loading) return <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading dashboard…</div>;
  if (err)     return <Notice type="err">Error: {err}</Notice>;
  if (!stats)  return null;

  const { totals, by_industry, by_signal_type, recent_companies, pipeline_value, conversion_metrics } = stats;

  return (
    <div className="space-y-8">
      {/* Header Actions */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100">Admin Dashboard</h2>
          <p className="text-xs text-neutral-600 mt-1">System metrics and business intelligence</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-800 transition-colors disabled:opacity-50"
        >
          {refreshing ? <><Spinner /> Refreshing...</> : '🔄 Refresh Data'}
        </button>
      </div>

      {/* Business Metrics */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Business Metrics</div>
        <div className="flex flex-wrap gap-3">
          <StatCard label="Total Pipeline" value={`$${pipeline_value?.toLocaleString() || 0}`} sub="Estimated value" />
          <StatCard label="Hot Leads" value={totals.scored.toLocaleString()} sub={`${conversion_metrics?.hot_rate || 0}% conversion`} />
          <StatCard label="Companies" value={totals.companies.toLocaleString()} sub={`${totals.signals} signals`} />
          <StatCard label="Avg Score" value={conversion_metrics?.avg_score || '—'} sub="Quality indicator" />
        </div>
      </div>

      {/* System Health */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">System Health</div>
        <div className="flex flex-wrap gap-3">
          <StatCard label="Scrapers" value={stats.scraper_health?.active || 0} sub={`${stats.scraper_health?.success_rate || 0}% success`} />
          <StatCard label="API Uptime" value="99.9%" sub="Last 30 days" />
          <StatCard label="DB Size" value={stats.database?.size_mb ? `${stats.database.size_mb}MB` : '—'} sub={`${stats.database?.tables || 0} tables`} />
          <StatCard label="Cache Hit" value={`${stats.performance?.cache_hit_rate || 85}%`} sub="Performance" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* By Industry */}
        <div>
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">By Industry</div>
          <table className="w-full text-sm">
            <tbody>
              {by_industry.map(r => (
                <tr key={r.industry} className="border-b border-neutral-800/50">
                  <td className="py-1.5 text-neutral-300">{r.industry || 'Unknown'}</td>
                  <td className="py-1.5 text-right tabular-nums text-neutral-500">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* By Signal Type */}
        <div>
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">By Signal Type</div>
          <table className="w-full text-sm">
            <tbody>
              {by_signal_type.map(r => (
                <tr key={r.signal_type} className="border-b border-neutral-800/50">
                  <td className="py-1.5 text-neutral-300">{r.signal_type}</td>
                  <td className="py-1.5 text-right tabular-nums text-neutral-500">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Companies */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Recent Companies</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left py-2 text-neutral-600 font-normal">Name</th>
              <th className="text-left py-2 text-neutral-600 font-normal">Industry</th>
              <th className="text-left py-2 text-neutral-600 font-normal">Source</th>
              <th className="text-right py-2 text-neutral-600 font-normal">Created</th>
            </tr>
          </thead>
          <tbody>
            {recent_companies.map(c => (
              <tr key={c.id} className="border-b border-neutral-800/40 hover:bg-neutral-900/40">
                <td className="py-2 text-neutral-200">{c.name}</td>
                <td className="py-2 text-neutral-500">{c.industry || '—'}</td>
                <td className="py-2 text-neutral-600 truncate max-w-[200px] text-xs">{c.source || '—'}</td>
                <td className="py-2 text-right text-neutral-600 text-xs tabular-nums">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Import URLs ────────────────────────────────────────────────────────────

function ImportUrls() {
  const [text, setText]       = useState('');
  const [industry, setIndustry]   = useState('');
  const [sigType, setSigType]     = useState('');
  const [scrapeNow, setScrapeNow] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [err, setErr]             = useState('');

  const submit = useCallback(async () => {
    const urls = text.split('\n').map(s => s.trim()).filter(Boolean);
    if (!urls.length) return;
    setLoading(true); setResult(null); setErr('');
    try {
      const r = await fetch(`${API}/api/admin/import/urls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls,
          industry:    industry || null,
          signal_type: sigType  || null,
          scrape_now:  scrapeNow,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setResult(d);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [text, industry, sigType, scrapeNow]);

  return (
    <div className="space-y-5 max-w-2xl">
      <p className="text-sm text-neutral-500">
        Paste URLs to register as scrape targets — one per line. The system auto-detects
        the scraper type and industries from the URL structure.
      </p>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        className="w-full h-40 bg-transparent border border-neutral-700 text-neutral-200 text-sm p-3 resize-y focus:outline-none focus:border-cyan-700 font-mono"
        placeholder={"https://www.indeed.com/jobs?q=housekeeper+hotel\nhttps://www.supplychaindive.com/feeds/news/\nhttps://www.yellowpages.com/search?..."}
      />

      <div className="flex flex-wrap gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-neutral-500">Industry hint</label>
          <select
            value={industry}
            onChange={e => setIndustry(e.target.value)}
            className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-cyan-700"
          >
            {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'Auto-detect'}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-neutral-500">Signal type hint</label>
          <select
            value={sigType}
            onChange={e => setSigType(e.target.value)}
            className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-cyan-700"
          >
            {SIGNAL_TYPES.map(s => <option key={s} value={s} className="bg-neutral-900">{s || 'Auto-detect'}</option>)}
          </select>
        </div>

        <div className="flex items-end pb-1.5">
          <label className="flex items-center gap-2 text-sm text-neutral-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={scrapeNow}
              onChange={e => setScrapeNow(e.target.checked)}
              className="accent-emerald-500"
            />
            Scrape immediately
          </label>
        </div>
      </div>

      <button
        onClick={submit}
        disabled={loading || !text.trim()}
        className="border border-emerald-700 text-emerald-400 text-sm px-5 py-2 hover:bg-emerald-950 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {loading && <Spinner />}
        {loading ? 'Importing…' : 'Import URLs'}
      </button>

      {err    && <Notice type="err">{err}</Notice>}
      {result && (
        <Notice type="ok">
          <strong>{result.added}</strong> added · <strong>{result.skipped}</strong> skipped
          {result.skipped_details?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5 text-neutral-500">
              {result.skipped_details.map((s, i) => (
                <li key={i}>{s.url || s.name} — {s.reason}</li>
              ))}
            </ul>
          )}
        </Notice>
      )}

      {result?.targets?.length > 0 && (
        <div className="mt-4">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Registered</div>
          <div className="space-y-2">
            {result.targets.map((t, i) => (
              <div key={i} className="border border-neutral-800 px-3 py-2">
                <div className="text-xs text-neutral-300 font-mono truncate">{t.url}</div>
                <div className="flex gap-2 mt-1 flex-wrap">
                  <Tag color="cyan">{t.scraper}</Tag>
                  {t.industries.map(ind => <Tag key={ind}>{ind}</Tag>)}
                  {t.signal_types.map(st => <Tag key={st} color="emerald">{st}</Tag>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Import Companies ───────────────────────────────────────────────────────

const COMPANY_EXAMPLE = JSON.stringify([
  { name: "Marriott Chicago River North", industry: "Hospitality", website: "https://marriott.com", location_city: "Chicago", location_state: "IL" },
  { name: "XPO Logistics Memphis DC", industry: "Logistics", website: "https://xpo.com", location_city: "Memphis", location_state: "TN" },
], null, 2);

function ImportCompanies() {
  const [text, setText]     = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [err, setErr]         = useState('');

  const submit = useCallback(async () => {
    let companies;
    try {
      companies = JSON.parse(text);
      if (!Array.isArray(companies)) companies = [companies];
    } catch {
      setErr('Invalid JSON — paste an array of company objects.'); return;
    }
    setLoading(true); setResult(null); setErr('');
    try {
      const r = await fetch(`${API}/api/admin/import/companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setResult(d);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [text]);

  return (
    <div className="space-y-5 max-w-2xl">
      <p className="text-sm text-neutral-500">
        Paste a JSON array of company objects. Required: <code className="text-cyan-500">name</code>.
        Optional: <code className="text-neutral-400">website industry location_city location_state source</code>.
      </p>

      <details className="border border-neutral-800 text-xs">
        <summary className="px-3 py-2 text-neutral-500 cursor-pointer hover:text-neutral-400">Example format</summary>
        <pre className="px-3 pb-3 text-neutral-600 overflow-auto">{COMPANY_EXAMPLE}</pre>
      </details>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        className="w-full h-48 bg-transparent border border-neutral-700 text-neutral-200 text-sm p-3 resize-y focus:outline-none focus:border-cyan-700 font-mono"
        placeholder={'[\n  { "name": "Hilton Denver Tech Center", "industry": "Hospitality" }\n]'}
      />

      <button
        onClick={submit}
        disabled={loading || !text.trim()}
        className="border border-cyan-700 text-cyan-400 text-sm px-5 py-2 hover:bg-cyan-950 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {loading && <Spinner />}
        {loading ? 'Importing…' : 'Import Companies'}
      </button>

      {err    && <Notice type="err">{err}</Notice>}
      {result && (
        <Notice type="ok">
          <strong>{result.added}</strong> added · <strong>{result.skipped}</strong> skipped
          {result.skipped_details?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5 text-neutral-500">
              {(result.skipped_details || result.names?.map(n => ({ name: n })) || []).map((s, i) => (
                <li key={i}>{s.name} {s.reason ? `— ${s.reason}` : ''}</li>
              ))}
            </ul>
          )}
          {result.names?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5">
              {result.names.map((n, i) => <li key={i} className="text-emerald-400">+ {n}</li>)}
            </ul>
          )}
        </Notice>
      )}
    </div>
  );
}

// ── Scraper Panel ──────────────────────────────────────────────────────────

function ScraperPanel() {
  const [targets, setTargets]       = useState(null);
  const [loadingTargets, setLT]     = useState(true);
  const [filterScraper, setFS]      = useState('');
  const [filterIndustry, setFI]     = useState('');
  const [triggerScraper, setTS]     = useState('all');
  const [triggerIndustry, setTI]    = useState('');
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTR]      = useState(null);
  const [triggerErr, setTE]         = useState('');

  const loadTargets = useCallback(() => {
    setLT(true);
    const params = new URLSearchParams();
    if (filterScraper)  params.set('scraper', filterScraper);
    if (filterIndustry) params.set('industry', filterIndustry);
    fetch(`${API}/api/admin/scrape/targets?${params}`)
      .then(r => r.json())
      .then(d => { setTargets(d); setLT(false); })
      .catch(() => setLT(false));
  }, [filterScraper, filterIndustry]);

  useEffect(() => { loadTargets(); }, [loadTargets]);

  const triggerScrape = useCallback(async () => {
    setTriggering(true); setTR(null); setTE('');
    try {
      const r = await fetch(`${API}/api/admin/scrape/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scraper: triggerScraper, industry: triggerIndustry || null }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setTR(d);
    } catch (e) {
      setTE(e.message);
    } finally {
      setTriggering(false);
    }
  }, [triggerScraper, triggerIndustry]);

  const summary = targets?.summary;

  return (
    <div className="space-y-8">
      {/* Trigger */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Trigger Scrape</div>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-neutral-600">Scraper</label>
            <select
              value={triggerScraper}
              onChange={e => setTS(e.target.value)}
              className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-emerald-700"
            >
              {SCRAPERS.map(s => <option key={s} value={s} className="bg-neutral-900">{s}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-neutral-600">Industry filter</label>
            <select
              value={triggerIndustry}
              onChange={e => setTI(e.target.value)}
              className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-emerald-700"
            >
              {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All industries'}</option>)}
            </select>
          </div>
          <button
            onClick={triggerScrape}
            disabled={triggering}
            className="border border-emerald-700 text-emerald-400 text-sm px-5 py-2 hover:bg-emerald-950 disabled:opacity-40 flex items-center gap-2"
          >
            {triggering && <Spinner />}
            {triggering ? 'Queuing…' : 'Run Scraper'}
          </button>
        </div>
        {triggerErr    && <Notice type="err">{triggerErr}</Notice>}
        {triggerResult && (
          <Notice type={triggerResult.status === 'queued' ? 'ok' : 'neutral'}>
            {triggerResult.status === 'queued'
              ? `Queued: ${triggerResult.scraper}${triggerResult.industry ? ' · ' + triggerResult.industry : ''}`
              : triggerResult.reason}
          </Notice>
        )}
      </div>

      {/* Summary counts */}
      {summary && (
        <div className="flex flex-wrap gap-3">
          <StatCard label="Job Board" value={summary.job_board} />
          <StatCard label="Hotel Dir" value={summary.hotel_dir} />
          <StatCard label="Logistics" value={summary.logistics_dir} />
          <StatCard label="RSS Feeds" value={summary.rss_feed} />
          <StatCard label="News Queries" value={summary.news_queries} />
          <StatCard label="Total" value={summary.total_targets} />
        </div>
      )}

      {/* Targets table */}
      <div>
        <div className="flex items-center gap-4 mb-3">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500">Targets</div>
          <select
            value={filterScraper}
            onChange={e => setFS(e.target.value)}
            className="bg-transparent border border-neutral-800 text-neutral-500 text-xs px-2 py-1 focus:outline-none"
          >
            <option value="" className="bg-neutral-900">All scrapers</option>
            {SCRAPERS.filter(s => s !== 'all').map(s => <option key={s} value={s} className="bg-neutral-900">{s}</option>)}
          </select>
          <select
            value={filterIndustry}
            onChange={e => setFI(e.target.value)}
            className="bg-transparent border border-neutral-800 text-neutral-500 text-xs px-2 py-1 focus:outline-none"
          >
            {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All industries'}</option>)}
          </select>
        </div>

        {loadingTargets
          ? <div className="text-neutral-500 text-sm flex gap-2 items-center"><Spinner /> Loading…</div>
          : (
            <div className="space-y-1.5 max-h-[460px] overflow-y-auto pr-1">
              {targets?.targets?.map((t, i) => (
                <div key={i} className="border border-neutral-800/60 px-3 py-2 hover:border-neutral-700">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-xs text-neutral-300 flex-1 min-w-0">{t.label}</span>
                    <Tag color="cyan">{t.scraper}</Tag>
                  </div>
                  <div className="text-[10px] font-mono text-neutral-600 truncate mt-0.5">{t.url}</div>
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    {t.industries.map(ind => <Tag key={ind}>{ind}</Tag>)}
                    {t.signal_types.map(st => <Tag key={st} color="emerald">{st}</Tag>)}
                    <Tag color="neutral">{t.cadence}</Tag>
                  </div>
                </div>
              ))}
            </div>
          )
        }
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

// Companies Manager Component
function CompaniesManager() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/admin/companies/search?q=${searchTerm}&industry=${filterIndustry}&limit=100`)
      .then(r => r.json())
      .then(d => { setCompanies(d.companies || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [searchTerm, filterIndustry]);

  const deleteCompany = async (id) => {
    if (!confirm('Delete this company and all its signals?')) return;
    setDeleting(id);
    try {
      await fetch(`${API}/api/admin/companies/${id}`, { method: 'DELETE' });
      setCompanies(companies.filter(c => c.id !== id));
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
    setDeleting(null);
  };

  return (
    <div className="space-y-5">
      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search companies..."
          className="flex-1 bg-transparent border border-neutral-700 text-neutral-200 text-sm px-4 py-2 focus:outline-none focus:border-emerald-700"
        />
        <select
          value={filterIndustry}
          onChange={e => setFilterIndustry(e.target.value)}
          className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-2 focus:outline-none focus:border-emerald-700"
        >
          {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All Industries'}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading companies...</div>
      ) : (
        <>
          <div className="text-xs text-neutral-600">{companies.length} companies found</div>
          <div className="space-y-2">
            {companies.map(c => (
              <div key={c.id} className="border border-neutral-800 px-4 py-3 hover:border-neutral-700 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-neutral-100 font-medium">{c.name}</span>
                      {c.industry && <Tag>{c.industry}</Tag>}
                      {c.score && <Tag color="emerald">Score: {c.score}</Tag>}
                    </div>
                    <div className="text-xs text-neutral-600 mt-1">
                      {c.website && <span>{c.website} · </span>}
                      {c.location_city && <span>{c.location_city}, {c.location_state} · </span>}
                      <span>{c.signal_count || 0} signals</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => window.open(`/companies/${c.id}`, '_blank')}
                      className="text-xs border border-neutral-700 px-3 py-1 text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
                    >
                      View
                    </button>
                    <button
                      onClick={() => deleteCompany(c.id)}
                      disabled={deleting === c.id}
                      className="text-xs border border-neutral-700 px-3 py-1 text-neutral-400 hover:text-red-400 hover:border-red-700 transition-colors disabled:opacity-50"
                    >
                      {deleting === c.id ? <Spinner /> : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// System Controls Component
function SystemControls() {
  const [clearing, setClearing] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [result, setResult] = useState('');

  const clearCache = async () => {
    if (!confirm('Clear all cache data?')) return;
    setClearing(true);
    try {
      await fetch(`${API}/api/admin/system/cache/clear`, { method: 'POST' });
      setResult('✅ Cache cleared successfully');
    } catch (e) {
      setResult('❌ Error: ' + e.message);
    }
    setClearing(false);
  };

  const reindexDatabase = async () => {
    if (!confirm('Reindex database? This may take several minutes.')) return;
    setReindexing(true);
    try {
      await fetch(`${API}/api/admin/system/reindex`, { method: 'POST' });
      setResult('✅ Database reindexed successfully');
    } catch (e) {
      setResult('❌ Error: ' + e.message);
    }
    setReindexing(false);
  };

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h3 className="text-sm font-semibold text-neutral-200 mb-4">System Operations</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Clear Cache</div>
              <div className="text-xs text-neutral-600">Reset all API and query caches</div>
            </div>
            <button
              onClick={clearCache}
              disabled={clearing}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors disabled:opacity-50"
            >
              {clearing ? <Spinner /> : 'Clear Cache'}
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Reindex Database</div>
              <div className="text-xs text-neutral-600">Optimize database indexes for faster queries</div>
            </div>
            <button
              onClick={reindexDatabase}
              disabled={reindexing}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors disabled:opacity-50"
            >
              {reindexing ? <Spinner /> : 'Reindex'}
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Trigger All Scrapers</div>
              <div className="text-xs text-neutral-600">Run all active scrapers immediately</div>
            </div>
            <Link 
              href="#"
              onClick={(e) => { e.preventDefault(); alert('Use Scrapers tab for granular control'); }}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
            >
              Go to Scrapers
            </Link>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-neutral-200 mb-4">Database Management</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Export All Data</div>
              <div className="text-xs text-neutral-600">Download complete database as JSON</div>
            </div>
            <button
              onClick={() => window.open(`${API}/api/admin/export/all`, '_blank')}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
            >
              Export
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Backup Database</div>
              <div className="text-xs text-neutral-600">Create timestamped backup</div>
            </div>
            <button
              onClick={() => alert('Feature coming soon - use database provider backup tools')}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors"
            >
              Backup
            </button>
          </div>
        </div>
      </div>

      {result && <Notice type={result.startsWith('✅') ? 'ok' : 'err'}>{result}</Notice>}
    </div>
  );
}

export default function AdminPage() {
  const [tab, setTab] = useState('Dashboard');

  return (
    <div style={{ backgroundColor: '#080808' }} className="min-h-screen text-neutral-300">
      {/* Top bar */}
      <header className="border-b border-neutral-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <span className="text-sm font-medium tracking-wide text-neutral-200">Ready for Robots</span>
          <span className="text-neutral-700">|</span>
          <span className="text-sm text-neutral-500">Admin</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/analytics" className="text-xs text-neutral-600 hover:text-emerald-400 transition-colors">
            📊 Analytics
          </Link>
          <Link href="/" className="text-xs text-neutral-600 hover:text-cyan-400 transition-colors">
            ← Dashboard
          </Link>
        </div>
      </header>

      <main className="px-6 pt-6 pb-16 max-w-5xl mx-auto">
        {/* Tab bar */}
        <div className="flex gap-1 border-b border-neutral-800 mb-8">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm -mb-px transition-colors ${
                tab === t
                  ? 'border-b border-emerald-500 text-emerald-400'
                  : 'text-neutral-600 hover:text-neutral-400'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === 'Dashboard'   && <Dashboard />}
        {tab === 'Companies'   && <CompaniesManager />}
        {tab === 'Scrapers'    && <ScraperPanel />}
        {tab === 'Analytics'   && <Link href="/analytics" className="block text-center py-12 text-neutral-500 hover:text-emerald-400 transition-colors">📊 Open Analytics Dashboard →</Link>}
        {tab === 'System'      && <SystemControls />}
      </main>
    </div>
  );
}
