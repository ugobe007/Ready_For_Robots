/**
 * Market Insights — User-facing Opportunity Report
 * Automation types, robot needs, ROI expectations, common tasks from scraped signals.
 * Available to all users (no admin required).
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import Head from 'next/head';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import IndustryBriefBlock from '../components/IndustryBriefBlock';
import RrSiteLayout from '../components/RrSiteLayout';

const API = getApiBase();

function displayIndustryName(k) {
  const s = String(k || '').trim();
  if (!s || ['unknown', 'other', 'uncategorized', 'n/a'].includes(s.toLowerCase())) return 'Emerging';
  return k;
}

function mergeIndustryCounts(obj) {
  const m = {};
  Object.entries(obj || {}).forEach(([k, v]) => {
    const lab = displayIndustryName(k);
    m[lab] = (m[lab] || 0) + Number(v);
  });
  return Object.entries(m).sort((a, b) => b[1] - a[1]);
}

function StatCard({ label, value, sub }) {
  return (
    <div className="rr-card rounded-lg p-5">
      <div className="text-[var(--rr-muted)] text-sm mb-1">{label}</div>
      <div className="text-2xl font-bold text-[var(--rr-text)]">{value ?? '—'}</div>
      {sub && <div className="text-xs text-[var(--rr-muted)] mt-1">{sub}</div>}
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
      const res = await fetch(`${API}/api/daily-report?days=${days}&format=json`, liveFetchInit());
      const d = await res.json();
      setData(d);
    } catch (e) {
      console.error('Market insights error:', e);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  const industryRows = useMemo(
    () => mergeIndustryCounts(data?.industries),
    [data?.industries],
  );

  if (loading) {
    return (
      <>
        <Head>
          <title>Market Insights | Ready For Robots</title>
        </Head>
        <RrSiteLayout active="market-insights">
          <div className="flex flex-1 items-center justify-center py-32 min-h-[50vh]">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-2 border-[var(--rr-border)] border-t-[var(--rr-green)] mb-4" />
              <p className="text-[var(--rr-muted)]">Loading market insights...</p>
            </div>
          </div>
        </RrSiteLayout>
      </>
    );
  }

  const totals = data?.totals || {};
  const maxVal = (obj) => obj && Object.values(obj).length ? Math.max(...Object.values(obj)) : 1;

  return (
    <>
      <Head>
        <title>Market Insights | Ready For Robots</title>
        <meta name="description" content="Opportunity analytics from live signals — automation themes, robot categories, ROI language, and industries." />
      </Head>
      <RrSiteLayout active="market-insights">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 text-[var(--rr-text)]">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--rr-green)] mb-2">Market intelligence</p>
            <h1 className="text-2xl md:text-3xl font-bold text-[var(--rr-text)] mb-2">Opportunity analytics</h1>
            <p className="text-[var(--rr-muted2)] max-w-2xl">Automation themes from signals, trending robot categories, ROI and trial language, and tasks to automate — updated from live opportunity data.</p>
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
          <StatCard label="Signals discovered" value={totals.signals} sub="In selected window" />
          <StatCard label="Companies w/ Opportunities" value={totals.companies_with_signals} />
          <StatCard label="ROI Mentions" value={data?.roi_mentions || 0} sub="In signal text" />
          <StatCard label="Pilot/Trial Mentions" value={data?.trial_pilot_mentions || 0} sub="In signal text" />
        </div>

        <IndustryBriefBlock brief={data?.industry_brief} className="mb-8" />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Automation Types */}
          <div className="rr-card rounded-lg p-6">
            <h3 className="text-lg font-semibold text-[var(--rr-text)] mb-4">Automation themes (inferred)</h3>
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

          {/* Robot categories trending */}
          <div className="rr-card rounded-lg p-6">
            <h3 className="text-lg font-semibold text-[var(--rr-text)] mb-4">Robot categories trending</h3>
            <p className="text-xs text-neutral-500 mb-3">Categories most mentioned with automation opportunities in this window — not a procurement forecast.</p>
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
          <div className="rr-card rounded-lg p-6">
            <h3 className="text-lg font-semibold text-[var(--rr-text)] mb-4">Most Common Tasks to Automate</h3>
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
          <div className="rr-card rounded-lg p-6">
            <h3 className="text-lg font-semibold text-[var(--rr-text)] mb-4">Industries</h3>
            <p className="text-xs text-neutral-500 mb-3">Unclassified companies are grouped as Emerging.</p>
            <div className="space-y-2">
              {industryRows.slice(0, 8).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-neutral-300">{k}</span>
                  <span className="text-neutral-500">{v}</span>
                </div>
              ))}
              {industryRows.length === 0 && <p className="text-neutral-500">No data</p>}
            </div>
          </div>
        </div>

        {/* Top Companies */}
        <div className="rr-card rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-[var(--rr-text)] mb-4">Top Companies by Signals</h3>
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
      </RrSiteLayout>
    </>
  );
}
