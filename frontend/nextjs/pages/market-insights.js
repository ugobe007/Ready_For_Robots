/**
 * Market Insights — User-facing Opportunity Report
 * Automation types, robot needs, ROI expectations, common tasks from scraped signals.
 * Available to all users (no admin required).
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

function StatCard({ label, value, sub }) {
  return (
    <div className="border border-neutral-800 rounded-lg p-5 bg-neutral-900/50">
      <div className="text-neutral-400 text-sm mb-1">{label}</div>
      <div className="text-2xl font-bold text-white">{value ?? '—'}</div>
      {sub && <div className="text-xs text-neutral-500 mt-1">{sub}</div>}
    </div>
  );
}

export default function MarketInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/api/daily-report?days=${days}&format=json`);
      const d = await res.json();
      setData(d);
    } catch (e) {
      console.error('Market insights error:', e);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
          <p className="text-neutral-400">Loading market insights...</p>
        </div>
      </div>
    );
  }

  const totals = data?.totals || {};
  const maxVal = (obj) => obj && Object.values(obj).length ? Math.max(...Object.values(obj)) : 1;

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <header className="border-b border-neutral-800 bg-neutral-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-2xl font-bold text-emerald-400">
                Ready For Robots
              </Link>
              <span className="text-neutral-600">/</span>
              <h1 className="text-xl font-semibold text-neutral-200">Market Insights</h1>
            </div>
            <nav className="flex items-center space-x-4">
              <Link href="/" className="text-neutral-400 hover:text-emerald-400 transition">Home</Link>
              <Link href="/search" className="text-neutral-400 hover:text-emerald-400 transition">Search</Link>
              <Link href="/newsletter" className="text-neutral-400 hover:text-emerald-400 transition">Newsletter</Link>
              <Link href="/roi-calculator" className="text-neutral-400 hover:text-emerald-400 transition">ROI Calculator</Link>
              <Link href="/dashboard" className="text-neutral-400 hover:text-emerald-400 transition">Dashboard</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Opportunity Analytics</h2>
            <p className="text-neutral-400">What automation is inferred? What robots are needed? ROI expectations? Common tasks — from scraped signals</p>
          </div>
          <div className="flex items-center gap-2">
            {[1, 7, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-4 py-2 rounded transition border ${
                  days === d ? 'border-emerald-600 text-emerald-400' : 'border-neutral-800 text-neutral-400 hover:border-neutral-700'
                }`}
              >
                {d} day{d > 1 ? 's' : ''}
              </button>
            ))}
            <button onClick={fetchReport} className="px-4 py-2 rounded border border-neutral-700 text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition">
              Refresh
            </button>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard label="Signals Analyzed" value={totals.signals} />
          <StatCard label="Companies w/ Opportunities" value={totals.companies_with_signals} />
          <StatCard label="ROI Mentions" value={data?.roi_mentions || 0} sub="In signal text" />
          <StatCard label="Pilot/Trial Mentions" value={data?.trial_pilot_mentions || 0} sub="In signal text" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Automation Types */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Automation Types Inferred</h3>
            <div className="space-y-3">
              {Object.entries(data?.automation_types_inferred || {}).slice(0, 8).map(([k, v]) => (
                <div key={k}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="text-neutral-300">{k.replace(/_/g, ' ')}</span>
                    <span className="text-neutral-500">{v}</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-2">
                    <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${(v / maxVal(data.automation_types_inferred)) * 100}%` }}></div>
                  </div>
                </div>
              )) || <p className="text-neutral-500">No data</p>}
            </div>
          </div>

          {/* Robot Types Needed */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Robot Types Needed</h3>
            <div className="space-y-3">
              {Object.entries(data?.robot_types_needed || {}).slice(0, 8).map(([k, v]) => (
                <div key={k}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="text-neutral-300">{k}</span>
                    <span className="text-neutral-500">{v}</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-2">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${(v / maxVal(data.robot_types_needed)) * 100}%` }}></div>
                  </div>
                </div>
              )) || <p className="text-neutral-500">No data</p>}
            </div>
          </div>

          {/* Common Tasks */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Most Common Tasks to Automate</h3>
            <div className="space-y-3">
              {Object.entries(data?.common_tasks_to_automate || {}).slice(0, 8).map(([k, v]) => (
                <div key={k}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="text-neutral-300">{k.replace(/_/g, ' ')}</span>
                    <span className="text-neutral-500">{v}</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${(v / maxVal(data.common_tasks_to_automate)) * 100}%` }}></div>
                  </div>
                </div>
              )) || <p className="text-neutral-500">No data</p>}
            </div>
          </div>

          {/* Industries */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Industries</h3>
            <div className="space-y-2">
              {Object.entries(data?.industries || {}).slice(0, 8).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-neutral-300">{k}</span>
                  <span className="text-neutral-500">{v}</span>
                </div>
              )) || <p className="text-neutral-500">No data</p>}
            </div>
          </div>
        </div>

        {/* Top Companies */}
        <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50 mb-8">
          <h3 className="text-lg font-semibold text-white mb-4">Top Companies by Signals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(data?.top_companies_by_signals || []).slice(0, 6).map((c, i) => (
              <Link key={i} href={`/search?q=${encodeURIComponent(c.name)}`} className="block border border-neutral-800 rounded-lg p-4 hover:border-emerald-700 hover:bg-neutral-900/50 transition">
                <div className="text-neutral-200 font-medium truncate">{c.name}</div>
                <div className="text-emerald-400 text-sm mt-1">{c.signals} signals</div>
              </Link>
            )) || <p className="text-neutral-500">No data</p>}
          </div>
        </div>

        {/* CTA */}
        <div className="border border-emerald-800 rounded-lg p-6 bg-emerald-950/20">
          <h3 className="text-lg font-semibold text-emerald-400 mb-2">Explore leads matching these opportunities</h3>
          <p className="text-neutral-400 text-sm mb-4">Search by industry, signal type, or company name to find hot prospects.</p>
          <Link href="/search?category=robot_automation" className="inline-block px-6 py-2 border border-emerald-500 text-emerald-400 rounded hover:bg-emerald-500/10 transition">
            Search Leads →
          </Link>
        </div>
      </main>
    </div>
  );
}
