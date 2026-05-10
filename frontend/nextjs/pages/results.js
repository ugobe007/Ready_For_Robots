import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import RrSiteLayout from '../components/RrSiteLayout';
import ScoutScoreBreakdown from '../components/ScoutScoreBreakdown';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { useAuth } from './_app';
import { authHeader } from '../lib/supabase';

export default function ResultsPage() {
  const router = useRouter();
  const { session } = useAuth();
  const API = getApiBase();
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  async function scan(target) {
    const value = (target || url || '').trim();
    if (!value) return;
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${API}/api/scout/scan-for-results`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: value }),
      }));
      const data = await response.json();
      setResult(data.result);
      setUrl(value);
    } catch {
      setMessage('SCOUT scan failed. Confirm the API is running and try again.');
    } finally {
      setLoading(false);
    }
  }

  async function addToPipeline() {
    if (!session?.access_token || !result?.company) {
      router.push('/login');
      return;
    }
    try {
      const response = await fetch(`${API}/api/pipeline`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body: JSON.stringify({
          company_id: result.company.id,
          name: result.company.name,
          website: result.company.website,
          industry: result.company.industry,
        }),
      }));
      if (!response.ok) throw new Error('Pipeline add failed');
      setMessage('Added to pipeline.');
    } catch {
      setMessage('Could not add this company to your pipeline yet.');
    }
  }

  useEffect(() => {
    if (!router.isReady) return;
    const initial = router.query.url || router.query.companyUrl;
    if (typeof initial === 'string') scan(initial);
  }, [router.isReady]);

  return (
    <RrSiteLayout active="signals">
      <Head><title>SCOUT Results | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <div className="max-w-6xl mx-auto">
          <p className="scout-kicker">URL scan</p>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-4">SCOUT results</h1>
          <p className="text-slate-300 max-w-2xl mb-8">Paste a company URL and SCOUT will return a six-factor robot-readiness readout, signal evidence, and next actions.</p>
          <form onSubmit={(e) => { e.preventDefault(); scan(); }} className="scout-card p-3 flex flex-col md:flex-row gap-3 mb-8">
            <input className="scout-input flex-1" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" />
            <button className="scout-btn-primary" disabled={loading}>{loading ? 'Scanning…' : 'Scan company'}</button>
          </form>
          {message && <p className="mb-6 text-sm text-amber-300">{message}</p>}
          {result && (
            <div className="grid lg:grid-cols-[380px_1fr] gap-6">
              <ScoutScoreBreakdown score={result.score} />
              <section className="scout-card p-5">
                <div className="flex flex-wrap justify-between gap-4 mb-6">
                  <div>
                    <p className="scout-kicker">Matched company</p>
                    <h2 className="text-2xl font-bold text-white">{result.company?.name}</h2>
                    <p className="text-sm text-slate-400">{result.company?.industry || 'Industry unknown'} · {result.company?.location || 'Location unknown'}</p>
                  </div>
                  <button className="scout-btn-secondary" onClick={addToPipeline}>Add to Pipeline</button>
                </div>
                <h3 className="font-semibold text-white mb-3">Signal evidence</h3>
                <div className="space-y-3 mb-6">
                  {(result.signals || []).length ? result.signals.map((signal, index) => (
                    <div key={index} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="text-xs font-mono text-teal-300 uppercase">{signal.type || 'signal'} · {Math.round((signal.strength || 0) * 100)}%</p>
                      <p className="text-sm text-slate-300 mt-1">{signal.text}</p>
                    </div>
                  )) : <p className="text-slate-400">No stored signal evidence yet. SCOUT marked this for monitoring.</p>}
                </div>
                <h3 className="font-semibold text-white mb-3">Next best actions</h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {(result.nextBestActions || []).map((action) => <li key={action}>→ {action}</li>)}
                </ul>
              </section>
            </div>
          )}
          <Link href="/signals" className="inline-block mt-8 text-teal-300 hover:text-teal-200">Browse live signals →</Link>
        </div>
      </main>
    </RrSiteLayout>
  );
}
