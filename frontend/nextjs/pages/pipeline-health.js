/**
 * Pipeline health — live stats from the database + scraper watchdog.
 * Auto-refresh every 30s.
 */
import { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import SiteNavPrimaryLinks from '../components/SiteNavPrimaryLinks';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

const API = getApiBase();
const POLL_MS = 30_000;

function StatCard({ label, value, sub, color = 'text-white' }) {
  return (
    <div className="rounded border border-zinc-800 p-4 bg-zinc-950/80">
      <div className="text-[10px] uppercase tracking-wide text-zinc-500 mb-1">{label}</div>
      <div className={`text-2xl font-mono ${color}`}>{value ?? '—'}</div>
      {sub && <div className="text-[10px] text-zinc-500 mt-0.5">{sub}</div>}
    </div>
  );
}

export default function PipelineHealthPage() {
  const [data, setData]       = useState(null);
  const [err, setErr]         = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState(null);

  const fetchAll = useCallback(async () => {
    setErr(null);
    try {
      const res = await fetch(`${API}/api/pipeline-stats`, liveFetchInit());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      setLastFetch(new Date());
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, POLL_MS);
    return () => clearInterval(id);
  }, [fetchAll]);

  const db = data?.database || {};
  const sigs = data?.signal_breakdown || {};
  const inds = data?.industry_breakdown || {};
  const wd = data?.scraper_watchdog || {};

  return (
    <>
      <Head>
        <title>Pipeline health | Ready for Robots</title>
        <meta name="robots" content="noindex" />
      </Head>
      <div className="min-h-screen bg-[#0a0a0a] text-zinc-200">
        <header className="border-b border-zinc-800 px-4 py-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-emerald-500 hover:text-emerald-400">
              ← Pipeline
            </Link>
            <h1 className="text-lg font-semibold text-white">Pipeline health</h1>
          </div>
          <SiteNavPrimaryLinks />
        </header>

        <main className="max-w-5xl mx-auto px-4 py-8 space-y-10">

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500">
            <button
              type="button"
              onClick={() => { setLoading(true); fetchAll(); }}
              className="px-3 py-1.5 rounded border border-zinc-600 hover:border-emerald-600 text-zinc-300"
            >
              Refresh now
            </button>
            {lastFetch && <span>Updated {lastFetch.toLocaleTimeString()}</span>}
            <span className="ml-auto">Auto-refreshes every {POLL_MS / 1000}s</span>
          </div>

          {loading && !data && <p className="text-zinc-500 animate-pulse">Loading…</p>}
          {err && (
            <div className="rounded border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
              {err}
            </div>
          )}

          {data && (
            <>
              {/* ── Database overview ─────────────────────────────── */}
              <section className="space-y-3">
                <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">Database</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard label="Total leads"    value={db.total_companies?.toLocaleString()} />
                  <StatCard label="Total signals"  value={db.total_signals?.toLocaleString()} />
                  <StatCard label="HOT leads"      value={db.hot?.toLocaleString()}  color="text-orange-400" />
                  <StatCard label="WARM leads"     value={db.warm?.toLocaleString()} color="text-yellow-400" />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard
                    label="New (last 24 h)"
                    value={db.new_last_24h != null ? db.new_last_24h.toLocaleString() : '—'}
                    color={db.new_last_24h > 0 ? 'text-emerald-400' : 'text-zinc-400'}
                  />
                  <StatCard
                    label="New (last 7 days)"
                    value={db.new_last_7d != null ? db.new_last_7d.toLocaleString() : '—'}
                    color={db.new_last_7d > 0 ? 'text-emerald-400' : 'text-zinc-400'}
                  />
                  <StatCard label="Scored leads"  value={db.scored_leads?.toLocaleString()} />
                  <StatCard
                    label="Latest signal"
                    value={db.latest_signal_at
                      ? new Date(db.latest_signal_at).toLocaleDateString()
                      : '—'}
                    sub={db.latest_signal_at
                      ? new Date(db.latest_signal_at).toLocaleTimeString()
                      : ''}
                  />
                </div>
              </section>

              {/* ── Signal breakdown ──────────────────────────────── */}
              {Object.keys(sigs).length > 0 && (
                <section className="space-y-3">
                  <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">Signal types</h2>
                  <div className="rounded border border-zinc-800 divide-y divide-zinc-800/60">
                    {Object.entries(sigs).map(([type, count]) => (
                      <div key={type} className="flex items-center gap-3 px-4 py-2 text-sm">
                        <span className="font-mono text-cyan-400/90 w-48 shrink-0">{type}</span>
                        <div className="flex-1 bg-zinc-900 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-emerald-600 h-full rounded-full"
                            style={{ width: `${Math.min(100, (count / db.total_signals) * 100 * 5)}%` }}
                          />
                        </div>
                        <span className="tabular-nums text-zinc-400 w-12 text-right">{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* ── Industry breakdown ────────────────────────────── */}
              {Object.keys(inds).length > 0 && (
                <section className="space-y-3">
                  <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">Top industries</h2>
                  <div className="rounded border border-zinc-800 divide-y divide-zinc-800/60">
                    {Object.entries(inds).map(([ind, count]) => (
                      <div key={ind} className="flex items-center gap-3 px-4 py-2 text-sm">
                        <span className="text-zinc-200 flex-1">{ind}</span>
                        <span className="tabular-nums text-zinc-400">{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* ── Scraper watchdog ──────────────────────────────── */}
              <section className="space-y-3">
                <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">Scraper watchdog</h2>
                <p className="text-xs text-zinc-500">{wd.note}</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <StatCard label="URLs tracked"  value={wd.urls_tracked ?? 0} />
                  <StatCard
                    label="Open circuits"
                    value={wd.open_circuits ?? 0}
                    color={(wd.open_circuits || 0) > 0 ? 'text-red-400' : 'text-emerald-400'}
                  />
                  <StatCard
                    label="Last run"
                    value={wd.recent_run?.status || 'no data'}
                    sub={wd.recent_run?.scraper_name || ''}
                    color={wd.recent_run?.status === 'success' ? 'text-emerald-400' : 'text-zinc-400'}
                  />
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </>
  );
}
