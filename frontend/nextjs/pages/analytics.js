import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { getApiBase, liveFetchInit } from '../lib/apiBase';

export default function Analytics() {
  const router = useRouter();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d, all

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${getApiBase()}/api/analytics?range=${timeRange}`, liveFetchInit());
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
          <p className="text-neutral-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      {/* Header */}
      <header className="border-b border-neutral-800 bg-neutral-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-2xl font-bold text-emerald-400">
                Ready For Robots
              </Link>
              <span className="text-neutral-600">/</span>
              <h1 className="text-xl font-semibold text-neutral-200">Admin Analytics</h1>
              <span className="text-xs px-2 py-1 border border-red-700 text-red-400 rounded">ADMIN ONLY</span>
            </div>
            <nav className="flex items-center space-x-4">
              <Link href="/market-insights" className="text-neutral-400 hover:text-emerald-400 transition">
                Market Insights
              </Link>
              <Link href="/" className="text-neutral-400 hover:text-emerald-400 transition">
                Dashboard
              </Link>
              <Link href="https://ready-2-robot.fly.dev/admin" className="text-neutral-400 hover:text-emerald-400 transition">
                Admin
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Time Range Selector */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Platform Analytics</h2>
            <p className="text-neutral-400">Track what your users are calculating and discovering</p>
          </div>
          <div className="flex items-center space-x-2">
            {[
              { label: '7 Days', value: '7d' },
              { label: '30 Days', value: '30d' },
              { label: '90 Days', value: '90d' },
              { label: 'All Time', value: 'all' }
            ].map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value)}
                className={`px-4 py-2 rounded transition border ${
                  timeRange === range.value
                    ? 'border-emerald-600 text-emerald-400'
                    : 'border-neutral-800 text-neutral-400 hover:border-neutral-700'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Pipeline Stats — live from DB */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
            <div className="text-[11px] uppercase tracking-wide text-neutral-500 mb-1">Companies Tracked</div>
            <div className="text-2xl font-mono font-bold text-white">{(analytics?.total_companies || 0).toLocaleString()}</div>
            <div className="text-emerald-400 text-xs mt-1">+{analytics?.new_companies || 0} this period</div>
          </div>
          <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
            <div className="text-[11px] uppercase tracking-wide text-neutral-500 mb-1">Signals Collected</div>
            <div className="text-2xl font-mono font-bold text-white">{(analytics?.total_signals || 0).toLocaleString()}</div>
            <div className="text-cyan-400 text-xs mt-1">+{analytics?.new_signals || 0} this period</div>
          </div>
          <div className="border border-red-900 rounded-lg p-4 bg-red-950/20">
            <div className="text-[11px] uppercase tracking-wide text-neutral-500 mb-1">HOT Leads</div>
            <div className="text-2xl font-mono font-bold text-red-400">{analytics?.hot_count || 0}</div>
            <div className="text-neutral-500 text-xs mt-1">≥70 intent score</div>
          </div>
          <div className="border border-amber-900 rounded-lg p-4 bg-amber-950/20">
            <div className="text-[11px] uppercase tracking-wide text-neutral-500 mb-1">WARM Pipeline</div>
            <div className="text-2xl font-mono font-bold text-amber-400">{analytics?.warm_count || 0}</div>
            <div className="text-neutral-500 text-xs mt-1">40–69 intent score</div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

          {/* Top Industries — from DB */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Companies by Industry</h3>
            <div className="space-y-3">
              {analytics?.top_industries?.length > 0
                ? analytics.top_industries.map((industry, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-neutral-300 text-sm">{industry.name}</span>
                        <span className="text-neutral-400 text-xs tabular-nums">{industry.count.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-neutral-800 rounded-full h-1.5">
                        <div className="bg-cyan-500 h-1.5 rounded-full transition-all" style={{ width: `${industry.percentage}%` }} />
                      </div>
                    </div>
                  ))
                : <p className="text-neutral-500 text-center py-4 text-sm">No industry data yet</p>}
            </div>
          </div>

          {/* Signal Type Breakdown — from DB */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Signal Types Detected</h3>
            <div className="space-y-3">
              {analytics?.signal_type_breakdown?.length > 0
                ? analytics.signal_type_breakdown.map((sig, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-neutral-300 text-sm">{sig.type}</span>
                        <span className="text-neutral-400 text-xs tabular-nums">{sig.count.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-neutral-800 rounded-full h-1.5">
                        <div className="bg-emerald-500 h-1.5 rounded-full transition-all" style={{ width: `${sig.percentage}%` }} />
                      </div>
                    </div>
                  ))
                : <p className="text-neutral-500 text-center py-4 text-sm">No signal data yet</p>}
            </div>
          </div>

        </div>

        {/* Score Distribution + Top HOT Leads */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

          {/* Score Distribution */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Lead Score Distribution</h3>
            <div className="space-y-4">
              {(analytics?.score_distribution || []).map((band, idx) => {
                const total = (analytics?.total_scored || 1);
                const pct = total > 0 ? Math.round((band.count / total) * 100) : 0;
                const barColor = band.color === 'red' ? 'bg-red-500' : band.color === 'amber' ? 'bg-amber-500' : 'bg-cyan-500';
                const textColor = band.color === 'red' ? 'text-red-400' : band.color === 'amber' ? 'text-amber-400' : 'text-cyan-400';
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm font-medium ${textColor}`}>{band.range}</span>
                      <span className="text-neutral-400 text-xs tabular-nums">{band.count.toLocaleString()} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-2">
                      <div className={`${barColor} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top HOT Leads */}
          <div className="border border-red-900 rounded-lg p-6 bg-red-950/10">
            <h3 className="text-lg font-semibold text-red-400 mb-4">Top HOT Leads</h3>
            <div className="space-y-3">
              {analytics?.top_hot_leads?.length > 0
                ? analytics.top_hot_leads.map((lead, idx) => (
                    <div key={idx} className="flex items-center justify-between py-1 border-b border-neutral-800 last:border-0">
                      <div>
                        <div className="text-neutral-200 text-sm font-medium">{lead.name}</div>
                        <div className="text-neutral-500 text-xs">{lead.industry}</div>
                      </div>
                      <div className="text-red-400 font-mono text-sm font-bold">{lead.score}</div>
                    </div>
                  ))
                : <p className="text-neutral-500 text-center py-4 text-sm">No HOT leads yet</p>}
            </div>
          </div>

        </div>

        {/* Insights & Recommendations — Clickable cards */}
        <div className="border border-emerald-800 rounded-lg p-6 bg-neutral-900/50">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">📊 Strategic Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link href="/search?category=robot_automation" className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30 hover:border-emerald-700 hover:bg-neutral-900/50 transition block">
              <div className="text-neutral-300 font-medium mb-2">🔥 Hottest Trend</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.hottest_trend || 'Not enough data yet'}
              </p>
              <span className="text-xs text-emerald-500 mt-2 inline-block">Search leads →</span>
            </Link>
            <Link href="/search?category=expansion" className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30 hover:border-emerald-700 hover:bg-neutral-900/50 transition block">
              <div className="text-neutral-300 font-medium mb-2">💡 Opportunity</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.opportunity || 'Gather more data to reveal opportunities'}
              </p>
              <span className="text-xs text-emerald-500 mt-2 inline-block">View pipeline →</span>
            </Link>
            <Link href="/market-insights" className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30 hover:border-emerald-700 hover:bg-neutral-900/50 transition block">
              <div className="text-neutral-300 font-medium mb-2">📈 Growth Area</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.growth_area || 'Continue monitoring user behavior'}
              </p>
              <span className="text-xs text-emerald-500 mt-2 inline-block">Full report →</span>
            </Link>
            <Link href="/roi-calculator" className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30 hover:border-emerald-700 hover:bg-neutral-900/50 transition block">
              <div className="text-neutral-300 font-medium mb-2">🎯 Action Item</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.action_item || 'Build features users are requesting'}
              </p>
              <span className="text-xs text-emerald-500 mt-2 inline-block">ROI Calculator →</span>
            </Link>
          </div>
        </div>

      </main>
    </div>
  );
}
