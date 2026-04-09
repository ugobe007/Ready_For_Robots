/**
 * Pipeline & scraper health — polls /api/scraper-health (watchdog JSON on the API host).
 * Auto-refresh every 30s. Use Tools → Pipeline health from the main nav.
 */
import { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import SiteNavPrimaryLinks from '../components/SiteNavPrimaryLinks';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

const API = getApiBase();
const POLL_MS = 30_000;

export default function PipelineHealthPage() {
  const [data, setData] = useState(null);
  const [apiHealth, setApiHealth] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState(null);

  const fetchAll = useCallback(async () => {
    setErr(null);
    try {
      const [h, s] = await Promise.all([
        fetch(`${API}/health`, liveFetchInit()).then((r) => r.json()).catch(() => null),
        fetch(`${API}/api/scraper-health`, liveFetchInit()).then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        }),
      ]);
      setApiHealth(h);
      setData(s);
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

  const summary = data?.summary || {};
  const recent = [...(data?.recent_runs || [])].reverse();

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
            <h1 className="text-lg font-semibold text-white">Pipeline &amp; scraper health</h1>
          </div>
          <SiteNavPrimaryLinks />
        </header>

        <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
          <p className="text-sm text-zinc-400 leading-relaxed">
            Live status from the API watchdog (<code className="text-cyan-500">/api/scraper-health</code>).
            Refreshes every {POLL_MS / 1000}s. Celery workers also log scraper health checks on a schedule.
          </p>

          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500">
            <button
              type="button"
              onClick={() => { setLoading(true); fetchAll(); }}
              className="px-3 py-1.5 rounded border border-zinc-600 hover:border-emerald-600 text-zinc-300"
            >
              Refresh now
            </button>
            {lastFetch && (
              <span>Last updated: {lastFetch.toLocaleTimeString()}</span>
            )}
            {apiHealth && (
              <span className="text-emerald-500/90">
                API /health: {apiHealth.status || 'ok'}
              </span>
            )}
          </div>

          {loading && !data && <p className="text-zinc-500 animate-pulse">Loading…</p>}
          {err && (
            <div className="rounded border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
              {err} — check <code className="text-red-200">NEXT_PUBLIC_API_URL</code> and that the backend is running.
            </div>
          )}

          {data && (
            <>
              <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded border border-zinc-800 p-4 bg-zinc-950/80">
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">URLs tracked</div>
                  <div className="text-2xl font-mono text-white mt-1">{summary.total_urls_tracked ?? '—'}</div>
                </div>
                <div className="rounded border border-zinc-800 p-4 bg-zinc-950/80">
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Open circuits</div>
                  <div className={`text-2xl font-mono mt-1 ${(summary.open_circuits || 0) > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {summary.open_circuits ?? 0}
                  </div>
                </div>
                <div className="rounded border border-zinc-800 p-4 bg-zinc-950/80">
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Last run</div>
                  <div className="text-sm text-zinc-200 mt-1 font-mono">{summary.last_run_status || '—'}</div>
                  <div className="text-[10px] text-zinc-500 mt-0.5 truncate" title={summary.last_run_scraper || ''}>
                    {summary.last_run_scraper || ''}
                  </div>
                </div>
                <div className="rounded border border-zinc-800 p-4 bg-zinc-950/80">
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Finished at</div>
                  <div className="text-xs text-zinc-300 mt-1 font-mono break-all">
                    {summary.last_run_finished_at || '—'}
                  </div>
                </div>
              </section>

              {(data.circuit_open_urls || []).length > 0 && (
                <section>
                  <h2 className="text-sm font-semibold text-amber-400 mb-2">Open circuit URLs</h2>
                  <ul className="text-xs font-mono space-y-1 text-amber-200/90 break-all">
                    {data.circuit_open_urls.map((u) => (
                      <li key={u}>{u}</li>
                    ))}
                  </ul>
                </section>
              )}

              {(data.active_runs || []).length > 0 && (
                <section>
                  <h2 className="text-sm font-semibold text-cyan-400 mb-2">Active runs</h2>
                  <pre className="text-xs bg-zinc-950 border border-zinc-800 rounded p-3 overflow-x-auto text-zinc-300">
                    {JSON.stringify(data.active_runs, null, 2)}
                  </pre>
                </section>
              )}

              <section>
                <h2 className="text-sm font-semibold text-white mb-3">Recent scraper runs (newest first)</h2>
                <div className="overflow-x-auto rounded border border-zinc-800">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-zinc-900/80 text-zinc-500 uppercase tracking-wide">
                      <tr>
                        <th className="px-3 py-2">scraper</th>
                        <th className="px-3 py-2">status</th>
                        <th className="px-3 py-2">started</th>
                        <th className="px-3 py-2">finished</th>
                        <th className="px-3 py-2">ok / fail</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent.length === 0 && (
                        <tr>
                          <td colSpan={5} className="px-3 py-6 text-zinc-500 text-center">
                            No runs in history yet — scrapers populate this file after guarded runs.
                          </td>
                        </tr>
                      )}
                      {recent.map((r, i) => (
                        <tr key={`${r.scraper_name}-${r.started_at}-${i}`} className="border-t border-zinc-800/80">
                          <td className="px-3 py-2 font-mono text-emerald-400/90">{r.scraper_name}</td>
                          <td className={`px-3 py-2 ${r.status === 'success' ? 'text-emerald-400' : r.status === 'failed' ? 'text-red-400' : 'text-zinc-300'}`}>
                            {r.status}
                          </td>
                          <td className="px-3 py-2 text-zinc-500 font-mono">{r.started_at || '—'}</td>
                          <td className="px-3 py-2 text-zinc-500 font-mono">{r.finished_at || '—'}</td>
                          <td className="px-3 py-2 tabular-nums text-zinc-400">
                            {r.urls_succeeded ?? 0} / {r.urls_attempted ?? 0}
                            {r.urls_skipped_circuit ? ` · skip ${r.urls_skipped_circuit}` : ''}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </>
  );
}
