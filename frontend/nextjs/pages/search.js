import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import RrSiteLayout from '../components/RrSiteLayout';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { AutomationSpecBlock } from '../lib/automationProfile';

const API = getApiBase();

/** Canonical market insights path (same as https://readyforrobots.com/market-insights/) */
const MARKET_INSIGHTS_HREF = '/market-insights/';

/** Map GET /api/leads row → search result row + automation_profile */
function leadToSearchRow(lead) {
  const sigs = lead.signals || [];
  const matched_signals = sigs.slice(0, 6).map((s) => ({
    signal_type: s.signal_type,
    signal_text: s.raw_text || s.signal_text || '',
    strength:
      typeof s.strength === 'number'
        ? s.strength
        : s.signal_strength != null
          ? Number(s.signal_strength)
          : 0.5,
  }));
  return {
    id: lead.id,
    company_name: lead.company_name,
    industry: lead.industry,
    location_city: lead.location_city,
    location_state: lead.location_state,
    overall_score: lead.score?.overall_score ?? 0,
    matched_signals,
    automation_profile: lead.automation_profile,
    priority_tier: lead.priority_tier,
  };
}

const SEARCH_CATEGORIES = [
  { key: 'funding',       label: 'Funding Round' },
  { key: 'expansion',     label: 'Expansion/CapEx' },
  { key: 'labor',         label: 'Labor Shortage' },
  { key: 'exec',          label: 'Executive Hire' },
  { key: 'ma',            label: 'M&A Activity' },
  { key: 'warehouse_logistics', label: 'Warehouse Logistics' },
  { key: 'robot_automation', label: 'Robot Automation' }
];

// Signal badge component
function SignalBadge({ type }) {
  const SIGNAL_META = {
    funding_round:     { label: 'FUNDING',    bg: 'bg-green-900/30',   border: 'border-green-700',   text: 'text-green-400' },
    expansion:         { label: 'EXPANSION',  bg: 'bg-purple-900/30',  border: 'border-purple-700',  text: 'text-purple-400' },
    capex:             { label: 'CAPEX',      bg: 'bg-purple-900/30',  border: 'border-purple-700',  text: 'text-purple-400' },
    labor_shortage:    { label: 'LABOR GAP',  bg: 'bg-red-900/30',     border: 'border-red-700',     text: 'text-red-400' },
    job_posting:       { label: 'HIRING',     bg: 'bg-yellow-900/30',  border: 'border-yellow-700',  text: 'text-yellow-400' },
    strategic_hire:    { label: 'EXEC HIRE',  bg: 'bg-cyan-900/30',    border: 'border-cyan-700',    text: 'text-cyan-400' },
    ma_activity:       { label: 'M&A',        bg: 'bg-pink-900/30',    border: 'border-pink-700',    text: 'text-pink-400' },
    news:              { label: 'NEWS',       bg: 'bg-blue-900/30',    border: 'border-blue-700',    text: 'text-blue-400' },
  };
  const meta = SIGNAL_META[type] || { label: type?.toUpperCase() || 'SIGNAL', bg: 'bg-neutral-900/30', border: 'border-neutral-700', text: 'text-neutral-400' };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-bold tracking-wide ${meta.bg} ${meta.border} ${meta.text} border shrink-0`}>
      {meta.label}
    </span>
  );
}

function ScoreNum({ value }) {
  const v = value ?? 0;
  const color = v >= 80 ? 'text-red-400' : v >= 60 ? 'text-yellow-400' : v >= 40 ? 'text-cyan-500' : 'text-neutral-600';
  return <span className={`text-sm font-bold tabular-nums ${color}`}>{Math.round(v)}</span>;
}

export default function SearchPage() {
  const router = useRouter();
  const searchRef = useRef(null);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadHotLeads = useCallback(async () => {
    setLoading(true);
    setResults(null);
    try {
      const r = await fetch(
        `${API}/api/leads?tier=HOT&limit=30&sort=score&exclude_junk=true`,
        liveFetchInit(),
      );
      if (!r.ok) return;
      const leads = await r.json();
      const rows = (Array.isArray(leads) ? leads : []).map(leadToSearchRow);
      setResults({
        results: rows,
        total: rows.length,
        query: null,
        category: null,
        category_label: 'Hot leads',
        prepopulated: true,
      });
    } catch {}
    setLoading(false);
  }, []);

  async function runSearch(q, cat) {
    setLoading(true);
    setResults(null);
    try {
      const params = new URLSearchParams();
      if (q && q.trim()) params.set('q', q.trim());
      if (cat) params.set('category', cat);
      params.set('limit', '50');
      const r = await fetch(`${API}/api/search?${params}`, liveFetchInit());
      if (r.ok) {
        const data = await r.json();
        setResults({ ...data, prepopulated: false });
      }
      // Sync URL so links are shareable and back/forward work
      const next = {};
      if (q && q.trim()) next.q = q.trim();
      if (cat) next.category = cat;
      router.replace({ pathname: '/search', query: Object.keys(next).length ? next : {} }, undefined, { shallow: true });
    } catch {}
    setLoading(false);
  }

  // Read URL params on load and run search (avoids blank pages from links)
  useEffect(() => {
    if (!router.isReady) return;
    const q = router.query.q;
    const cat = router.query.category;
    if (q != null || cat != null) {
      const qVal = typeof q === 'string' ? q : (q?.[0] ?? '');
      const catVal = typeof cat === 'string' ? cat : (cat?.[0] ?? null);
      setQuery(qVal);
      setCategory(catVal);
      runSearch(qVal, catVal);
    }
  }, [router.isReady, router.query.q, router.query.category]);

  // No ?q= / ?category= — show HOT leads with automation specs (never empty table)
  useEffect(() => {
    if (!router.isReady) return;
    if (router.query.q !== undefined || router.query.category !== undefined) return;
    loadHotLeads();
  }, [router.isReady, router.query.q, router.query.category, loadHotLeads]);

  // '/' keyboard shortcut to focus search
  useEffect(() => {
    function onKey(e) {
      if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        searchRef.current?.focus();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  function selectCategory(key) {
    const next = category === key ? null : key;
    setCategory(next);
    if (next || query.trim()) runSearch(query, next || null);
    else loadHotLeads();
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim() || category) runSearch(query, category);
    else loadHotLeads();
  }

  function clearAll() {
    setQuery('');
    setCategory(null);
    router.replace('/search', undefined, { shallow: true });
    loadHotLeads();
  }

  return (
    <>
      <Head>
        <title>Intelligence Search | Ready For Robots</title>
        <meta name="description" content="Search companies by funding, expansion, labor signals, M&amp;A, and automation intent." />
      </Head>
      <RrSiteLayout active="search">
      <div className="px-4 py-8 md:px-8 md:py-10 max-w-7xl mx-auto text-[var(--rr-text)]">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <h2 className="text-xl text-cyan-400">Intelligence Search</h2>
        </div>
        <p className="text-sm text-neutral-400">Find buyers by investment activity, M&A, labor trends & verticals</p>
      </header>

      {/* Search Interface */}
      <div className="border border-neutral-800 rounded-lg p-6 mb-6 space-y-5">
        {/* Category Grid */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-cyan-400">Quick Search by Category</p>
            <span className="text-[10px] text-neutral-600">🎯 Pre-configured signal searches</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SEARCH_CATEGORIES.map(cat => (
              <button key={cat.key} onClick={() => selectCategory(cat.key)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all border ${
                  category === cat.key
                    ? 'border-cyan-600 bg-cyan-900/20 text-cyan-300'
                    : 'border-neutral-700 text-cyan-400 hover:border-cyan-500 hover:text-cyan-300'
                }`}>
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input ref={searchRef} type="text" value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search companies, keywords, or signal types... (press / to focus)"
            className="flex-1 bg-neutral-900 border border-neutral-600 rounded px-4 py-2.5 text-sm
                       text-neutral-100 placeholder-neutral-500
                       focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-900 transition-colors" />
          <button type="submit"
            className="px-5 py-2.5 rounded text-sm font-medium border border-cyan-800 text-cyan-400 
                       hover:border-cyan-600 hover:text-cyan-300 transition-colors shrink-0">
            🔍 Search
          </button>
          {(query || category || results) && (
            <button type="button" onClick={clearAll}
              className="px-4 py-2.5 rounded text-sm border border-neutral-800 text-neutral-500 
                         hover:text-neutral-300 transition-colors shrink-0">
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-16">
          <p className="text-neutral-400 animate-pulse">Searching signals...</p>
        </div>
      )}

      {/* Results */}
      {!loading && results && (
        <div>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <span className="text-lg font-medium text-neutral-200">
              {results.total} result{results.total !== 1 ? 's' : ''}
            </span>
            {results.category_label && (
              <span className="px-3 py-1 rounded text-xs border border-cyan-800 text-cyan-400">
                {results.category_label}
              </span>
            )}
            {results.prepopulated && (
              <span className="text-xs text-neutral-500">
                Showing live HOT pipeline — search or filter to narrow
              </span>
            )}
            {results.query && (
              <span className="text-sm text-neutral-400">matching &quot;{results.query}&quot;</span>
            )}
          </div>

          {results.total > 0 && (
            <div className="mb-6 rounded-lg border border-emerald-900/50 bg-emerald-950/20 px-4 py-3 flex flex-col gap-3">
              <p className="text-sm text-neutral-300">
                <span className="text-emerald-400 font-medium">Turn results into revenue:</span>{' '}
                save accounts to your pipeline and build customizable sales plans from the dashboard—starting with these leads. Each row includes an{' '}
                <span className="text-neutral-200">automation spec</span> (robot types, applications, deployment context).
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center justify-center rounded-md border border-emerald-700 bg-emerald-950/40 px-4 py-2 text-sm font-medium text-emerald-300 hover:border-emerald-500 hover:text-emerald-200 transition-colors"
                >
                  Open dashboard →
                </Link>
                <Link
                  href={MARKET_INSIGHTS_HREF}
                  className="inline-flex items-center justify-center rounded-md border border-cyan-800 bg-cyan-950/30 px-4 py-2 text-sm font-medium text-cyan-300 hover:border-cyan-600 hover:text-cyan-200 transition-colors"
                >
                  Explore market insights →
                </Link>
              </div>
            </div>
          )}

          {results.total === 0 ? (
            <div className="text-center py-16 border border-neutral-800 rounded-lg space-y-4">
              <p className="text-neutral-400 mb-2">No results found</p>
              <p className="text-sm text-neutral-500">
                Try a different category, or search for a company name like &quot;Marriott&quot; or keyword like &quot;AMR&quot;
              </p>
              <Link
                href={MARKET_INSIGHTS_HREF}
                className="inline-flex items-center justify-center rounded-md border border-cyan-800 bg-cyan-950/30 px-5 py-2.5 text-sm font-medium text-cyan-300 hover:border-cyan-600"
              >
                Explore market insights →
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {results.results.map((r) => {
                const tier = r.priority_tier;
                const tierCls =
                  tier === 'HOT'
                    ? 'border-orange-700 text-orange-400 bg-orange-950/30'
                    : tier === 'WARM'
                      ? 'border-amber-700 text-amber-400 bg-amber-950/20'
                      : 'border-cyan-800 text-cyan-400 bg-cyan-950/20';
                const pct = (s) => {
                  const v = Number(s.strength);
                  const x = v > 1 ? v / 100 : v;
                  return Math.round(Math.min(100, Math.max(0, x * 100)));
                };
                return (
                <div key={r.id}
                  className="border border-neutral-800 rounded-lg px-5 py-4 hover:border-neutral-600 transition-colors">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link href={`/dashboard?analyze=${r.id}`}>
                        <span className="text-lg font-semibold text-neutral-100 hover:text-cyan-400 cursor-pointer transition-colors">
                          {r.company_name}
                        </span>
                      </Link>
                      {tier && (
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${tierCls}`}>
                          {tier}
                        </span>
                      )}
                      {r.industry && (
                        <span className="text-xs text-neutral-500">{r.industry}</span>
                      )}
                      {r.location_city && (
                        <span className="text-xs text-neutral-600">
                          {r.location_city}{r.location_state ? `, ${r.location_state}` : ''}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <ScoreNum value={r.overall_score} />
                        <div className="text-[10px] text-neutral-600">score</div>
                      </div>
                      <Link href={`/dashboard?analyze=${r.id}`}>
                        <span className="text-xs text-cyan-500 hover:text-cyan-300 transition-colors">
                          View analysis →
                        </span>
                      </Link>
                    </div>
                  </div>

                  {r.automation_profile && (
                    <div className="mt-3 border-t border-neutral-800/80 pt-3">
                      <AutomationSpecBlock profile={r.automation_profile} theme="dashboard" />
                    </div>
                  )}
                  
                  {r.matched_signals?.length > 0 && (
                    <div className="space-y-2 mt-3">
                      {r.matched_signals.map((s, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <SignalBadge type={s.signal_type} />
                          <span className="text-xs text-neutral-300 flex-1 leading-relaxed">{s.signal_text}</span>
                          <span className={`shrink-0 text-xs font-mono tabular-nums ${
                            pct(s) >= 70 ? 'text-emerald-400'
                            : pct(s) >= 40 ? 'text-cyan-500'
                            : 'text-neutral-400'
                          }`}>{pct(s)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Empty State (e.g. API unreachable) */}
      {!loading && !results && (
        <div className="text-center py-20">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-xl text-neutral-300 mb-2">Start Searching</h3>
          <p className="text-neutral-500 text-sm mb-6">
            Select a category or enter a search query — or explore industry context and timing on Market Insights.
          </p>
          <Link
            href={MARKET_INSIGHTS_HREF}
            className="inline-flex items-center justify-center rounded-md border border-cyan-800 bg-cyan-950/30 px-5 py-2.5 text-sm font-medium text-cyan-300 hover:border-cyan-600 hover:text-cyan-200 transition-colors"
          >
            Explore market insights →
          </Link>
        </div>
      )}
      </div>
      </RrSiteLayout>
    </>
  );
}
