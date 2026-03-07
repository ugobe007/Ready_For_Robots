import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useAuth } from './_app';

const API = typeof window !== 'undefined' 
  ? (window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://ready-2-robot.fly.dev')
  : 'https://ready-2-robot.fly.dev';

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
  const { session } = useAuth();
  const searchRef = useRef(null);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

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

  async function runSearch(q, cat) {
    setLoading(true);
    setResults(null);
    try {
      const params = new URLSearchParams();
      if (q && q.trim()) params.set('q', q.trim());
      if (cat) params.set('category', cat);
      params.set('limit', '50');
      const r = await fetch(`${API}/api/search?${params}`);
      if (r.ok) {
        setResults(await r.json());
      }
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
    <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1200px] mx-auto">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Link href="/">
            <div className="inline-block border-2 border-cyan-600 rounded-lg px-4 py-2 cursor-pointer hover:border-cyan-500 transition-colors"
              style={{ boxShadow: '0 0 12px rgba(34, 211, 238, 0.4), 0 0 24px rgba(34, 211, 238, 0.2)' }}>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 via-cyan-300 to-cyan-400 bg-clip-text text-transparent"
                style={{ textShadow: '0 0 30px rgba(34, 211, 238, 0.3)' }}>
                Ready for Robots
              </h1>
            </div>
          </Link>
          <span className="text-neutral-500">→</span>
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
          <div className="flex items-center gap-3 mb-4">
            <span className="text-lg font-medium text-neutral-200">
              {results.total} result{results.total !== 1 ? 's' : ''}
            </span>
            {results.category_label && (
              <span className="px-3 py-1 rounded text-xs border border-cyan-800 text-cyan-400">
                {results.category_label}
              </span>
            )}
            {results.query && (
              <span className="text-sm text-neutral-400">matching "{results.query}"</span>
            )}
          </div>

          {results.total === 0 ? (
            <div className="text-center py-16 border border-neutral-800 rounded-lg">
              <p className="text-neutral-400 mb-2">No results found</p>
              <p className="text-sm text-neutral-500">
                Try a different category, or search for a company name like "Marriott" or keyword like "AMR"
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.results.map(r => (
                <div key={r.id}
                  className="border border-neutral-800 rounded-lg px-5 py-4 hover:border-neutral-600 transition-colors">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link href={`/?lead=${r.id}`}>
                        <span className="text-lg font-semibold text-neutral-100 hover:text-cyan-400 cursor-pointer transition-colors">
                          {r.company_name}
                        </span>
                      </Link>
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
                      <Link href={`/?lead=${r.id}`}>
                        <button className="text-xs text-cyan-500 hover:text-cyan-300 transition-colors">
                          View Analysis →
                        </button>
                      </Link>
                    </div>
                  </div>
                  
                  {r.matched_signals?.length > 0 && (
                    <div className="space-y-2 mt-3">
                      {r.matched_signals.map((s, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <SignalBadge type={s.signal_type} />
                          <span className="text-xs text-neutral-300 flex-1 leading-relaxed">{s.signal_text}</span>
                          <span className={`shrink-0 text-xs font-mono tabular-nums ${
                            s.strength >= 0.7 ? 'text-emerald-400'
                            : s.strength >= 0.4 ? 'text-cyan-500'
                            : 'text-neutral-400'
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

      {/* Empty State */}
      {!loading && !results && (
        <div className="text-center py-20">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-xl text-neutral-300 mb-2">Start Searching</h3>
          <p className="text-neutral-500 text-sm">
            Select a category or enter a search query to find companies showing automation intent signals
          </p>
        </div>
      )}
    </div>
  );
}
