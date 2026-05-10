import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import RrSiteLayout from '../components/RrSiteLayout';
import ScoutScoreBreakdown from '../components/ScoutScoreBreakdown';
import { useAuth } from './_app';
import { authHeader } from '../lib/supabase';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

export default function PipelinePage() {
  const router = useRouter();
  const { session, loading: authLoading } = useAuth();
  const API = getApiBase();
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [workingId, setWorkingId] = useState('');

  async function loadPipeline() {
    if (!session?.access_token) return;
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API}/api/pipeline`, liveFetchInit({ headers: authHeader(session.access_token) }));
      const text = await response.text();
      if (!response.ok) throw new Error(text || 'Pipeline request failed');
      const data = JSON.parse(text);
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch (err) {
      setError(err.message || 'Could not load pipeline');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  async function action(item, path) {
    setWorkingId(item.id);
    try {
      const response = await fetch(`${API}/api/pipeline/${item.id}/${path}`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body: JSON.stringify({}),
      }));
      if (!response.ok) throw new Error('Pipeline action failed');
      await loadPipeline();
    } catch (err) {
      setError(err.message || 'Pipeline action failed');
    } finally {
      setWorkingId('');
    }
  }

  useEffect(() => {
    if (authLoading) return;
    if (!session) {
      router.replace('/login');
      return;
    }
    loadPipeline();
  }, [authLoading, session?.access_token]);

  return (
    <RrSiteLayout active="pipeline">
      <Head><title>SCOUT Pipeline | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap justify-between items-end gap-4 mb-8">
            <div>
              <p className="scout-kicker">Compatibility workspace</p>
              <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight">SCOUT pipeline</h1>
              <p className="text-slate-300 max-w-2xl mt-3">A Cursor-spec pipeline route backed by the existing CRM account engine.</p>
            </div>
            <Link href="/results" className="scout-btn-primary">Scan new company</Link>
          </div>
          {error && <div className="scout-card p-4 mb-6 text-amber-300 text-sm">{error}</div>}
          {loading ? (
            <div className="scout-card p-8 text-slate-300">Loading pipeline…</div>
          ) : items.length === 0 ? (
            <div className="scout-card p-8 text-center">
              <h2 className="text-2xl font-bold text-white mb-2">No pipeline items yet</h2>
              <p className="text-slate-300 mb-5">Scan a company or add accounts from CRM to begin.</p>
              <Link href="/results" className="scout-btn-secondary">Run first scan</Link>
            </div>
          ) : (
            <div className="grid lg:grid-cols-2 gap-5">
              {items.map((item) => (
                <article key={item.id} className="scout-card p-5">
                  <div className="flex justify-between gap-4 mb-4">
                    <div>
                      <p className="scout-kicker">{item.stage}</p>
                      <h2 className="text-xl font-bold text-white">{item.name}</h2>
                      <p className="text-sm text-slate-400">{item.industry || 'Industry unknown'}</p>
                    </div>
                    <span className="h-fit rounded-full border border-teal-400/30 bg-teal-400/10 px-3 py-1 text-xs font-semibold text-teal-200">{item.mode}</span>
                  </div>
                  <ScoutScoreBreakdown score={item.scoutScore} />
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button className="scout-btn-secondary" disabled={workingId === item.id} onClick={() => action(item, 'advance')}>Advance</button>
                    <button className="scout-btn-secondary" disabled={workingId === item.id} onClick={() => action(item, 'toggle-mode')}>Toggle mode</button>
                    <button className="scout-btn-secondary" disabled={workingId === item.id} onClick={() => action(item, 'generate-proposal')}>Generate proposal</button>
                    <button className="scout-btn-ghost" disabled={workingId === item.id} onClick={() => action(item, 'archive')}>Archive</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </main>
    </RrSiteLayout>
  );
}
