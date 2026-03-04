import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d, all

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/analytics?range=${timeRange}`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
          <p className="text-zinc-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Ready For Robots
              </Link>
              <span className="text-zinc-500">/</span>
              <h1 className="text-xl font-semibold text-zinc-200">Usage Analytics</h1>
            </div>
            <nav className="flex items-center space-x-4">
              <Link href="/roi-calculator" className="text-zinc-400 hover:text-emerald-400 transition">
                ROI Calculator
              </Link>
              <Link href="/robot-ready" className="text-zinc-400 hover:text-emerald-400 transition">
                Robot Ready
              </Link>
              <Link href="/brief" className="text-zinc-400 hover:text-emerald-400 transition">
                Strategy Brief
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
            <p className="text-zinc-400">Track what your users are calculating and discovering</p>
          </div>
          <div className="flex items-center space-x-2 bg-zinc-800 rounded-lg p-1">
            {[
              { label: '7 Days', value: '7d' },
              { label: '30 Days', value: '30d' },
              { label: '90 Days', value: '90d' },
              { label: 'All Time', value: 'all' }
            ].map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value)}
                className={`px-4 py-2 rounded transition ${
                  timeRange === range.value
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <div className="text-zinc-400 text-sm mb-2">Total Calculations</div>
            <div className="text-3xl font-bold text-white">{analytics?.total_calculations || 0}</div>
            <div className="text-emerald-400 text-sm mt-2">
              +{analytics?.calculation_growth || 0}% vs previous period
            </div>
          </div>
          
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <div className="text-zinc-400 text-sm mb-2">Robot Searches</div>
            <div className="text-3xl font-bold text-white">{analytics?.robot_searches || 0}</div>
            <div className="text-cyan-400 text-sm mt-2">
              {analytics?.avg_matches_per_search || 0} avg matches
            </div>
          </div>
          
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <div className="text-zinc-400 text-sm mb-2">Avg Payback Period</div>
            <div className="text-3xl font-bold text-white">
              {analytics?.avg_payback_months || 0}<span className="text-xl text-zinc-400 ml-1">mo</span>
            </div>
            <div className="text-yellow-400 text-sm mt-2">
              ${(analytics?.avg_robot_cost || 0).toLocaleString()} avg cost
            </div>
          </div>
          
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <div className="text-zinc-400 text-sm mb-2">Email Captures</div>
            <div className="text-3xl font-bold text-white">{analytics?.email_captures || 0}</div>
            <div className="text-purple-400 text-sm mt-2">
              {analytics?.conversion_rate || 0}% conversion rate
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          {/* Top Robot Types */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Top Robot Types</h3>
            <div className="space-y-3">
              {analytics?.top_robot_types?.map((robot, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-zinc-300">{robot.type}</span>
                      <span className="text-zinc-400 text-sm">{robot.count} calcs</span>
                    </div>
                    <div className="w-full bg-zinc-700 rounded-full h-2">
                      <div 
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${robot.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-zinc-500 text-center py-4">No data available</p>}
            </div>
          </div>

          {/* Top Industries */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Top Industries</h3>
            <div className="space-y-3">
              {analytics?.top_industries?.map((industry, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-zinc-300">{industry.name}</span>
                      <span className="text-zinc-400 text-sm">{industry.count} calcs</span>
                    </div>
                    <div className="w-full bg-zinc-700 rounded-full h-2">
                      <div 
                        className="bg-cyan-500 h-2 rounded-full transition-all"
                        style={{ width: `${industry.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-zinc-500 text-center py-4">No data available</p>}
            </div>
          </div>

        </div>

        {/* Regional Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          {/* Geographic Distribution */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Geographic Distribution</h3>
            <div className="space-y-3">
              {analytics?.top_regions?.map((region, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-zinc-300">{region.name}</span>
                      <span className="text-zinc-400 text-sm">{region.searches} searches</span>
                    </div>
                    <div className="w-full bg-zinc-700 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all"
                        style={{ width: `${region.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-zinc-500 text-center py-4">No data available</p>}
            </div>
          </div>

          {/* Cost Distribution */}
          <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Robot Cost Distribution</h3>
            <div className="space-y-3">
              {analytics?.cost_buckets?.map((bucket, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-zinc-300">{bucket.range}</span>
                      <span className="text-zinc-400 text-sm">{bucket.count} robots</span>
                    </div>
                    <div className="w-full bg-zinc-700 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full transition-all"
                        style={{ width: `${bucket.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-zinc-500 text-center py-4">No data available</p>}
            </div>
          </div>

        </div>

        {/* Insights & Recommendations */}
        <div className="bg-gradient-to-br from-emerald-900/20 to-cyan-900/20 border border-emerald-500/30 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">📊 Strategic Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-zinc-300 font-medium mb-2">🔥 Hottest Trend</div>
              <p className="text-zinc-400 text-sm">
                {analytics?.insights?.hottest_trend || 'Not enough data yet'}
              </p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-zinc-300 font-medium mb-2">💡 Opportunity</div>
              <p className="text-zinc-400 text-sm">
                {analytics?.insights?.opportunity || 'Gather more data to reveal opportunities'}
              </p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-zinc-300 font-medium mb-2">📈 Growth Area</div>
              <p className="text-zinc-400 text-sm">
                {analytics?.insights?.growth_area || 'Continue monitoring user behavior'}
              </p>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-zinc-300 font-medium mb-2">🎯 Action Item</div>
              <p className="text-zinc-400 text-sm">
                {analytics?.insights?.action_item || 'Build features users are requesting'}
              </p>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
