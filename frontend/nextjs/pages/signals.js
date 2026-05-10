import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import RrSiteLayout from '../components/RrSiteLayout';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

export default function SignalsPage() {
  const API = getApiBase();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/scout/signal-update?limit=24`, liveFetchInit())
      .then((r) => (r.ok ? r.json() : { signals: [] }))
      .then((data) => setSignals(Array.isArray(data.signals) ? data.signals : []))
      .catch(() => setSignals([]))
      .finally(() => setLoading(false));
  }, [API]);

  return (
    <RrSiteLayout active="signals">
      <Head><title>Live Robot Buying Signals | Ready For Robots</title></Head>
      <main className="scout-page px-4 py-12">
        <div className="max-w-6xl mx-auto">
          <p className="scout-kicker">Signal feed</p>
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-4">Live automation triggers</h1>
          <p className="text-slate-300 max-w-2xl mb-8">Recent public signals SCOUT uses to identify robot-ready companies and route them into your pipeline.</p>
          {loading ? <div className="scout-card p-8 text-slate-300">Loading signals…</div> : (
            <div className="grid md:grid-cols-2 gap-4">
              {signals.map((signal, index) => (
                <article key={`${signal.companyId}-${index}`} className="scout-card p-5">
                  <div className="flex justify-between gap-3 mb-3">
                    <div>
                      <p className="scout-kicker">{signal.type || 'signal'}</p>
                      <h2 className="text-xl font-bold text-white">{signal.companyName}</h2>
                    </div>
                    <span className="font-mono text-amber-300">{Math.round((Number(signal.strength) || 0) * 100)}%</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed mb-4">{signal.text}</p>
                  <div className="flex gap-3 text-sm">
                    <Link href={`/results?url=${encodeURIComponent(signal.website || signal.companyName)}`} className="text-teal-300 hover:text-teal-200">Scan →</Link>
                    {signal.sourceUrl && <a href={signal.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white">Source ↗</a>}
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
