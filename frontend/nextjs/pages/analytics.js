import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Analytics() {
  const router = useRouter();
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
              <Link href="/" className="text-neutral-400 hover:text-emerald-400 transition">
                Dashboard
              </Link>
              <Link href="/admin" className="text-neutral-400 hover:text-emerald-400 transition">
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

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <div className="text-neutral-400 text-sm mb-2">Total Calculations</div>
            <div className="text-3xl font-bold text-white">{analytics?.total_calculations || 0}</div>
            <div className="text-emerald-400 text-sm mt-2">
              +{analytics?.calculation_growth || 0}% vs previous period
            </div>
          </div>
          
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <div className="text-neutral-400 text-sm mb-2">Robot Searches</div>
            <div className="text-3xl font-bold text-white">{analytics?.robot_searches || 0}</div>
            <div className="text-cyan-400 text-sm mt-2">
              {analytics?.avg_matches_per_search || 0} avg matches
            </div>
          </div>
          
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <div className="text-neutral-400 text-sm mb-2">Avg Payback Period</div>
            <div className="text-3xl font-bold text-white">
              {analytics?.avg_payback_months || 0}<span className="text-xl text-neutral-400 ml-1">mo</span>
            </div>
            <div className="text-yellow-400 text-sm mt-2">
              ${(analytics?.avg_robot_cost || 0).toLocaleString()} avg cost
            </div>
          </div>
          
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <div className="text-neutral-400 text-sm mb-2">Email Captures</div>
            <div className="text-3xl font-bold text-white">{analytics?.email_captures || 0}</div>
            <div className="text-purple-400 text-sm mt-2">
              {analytics?.conversion_rate || 0}% conversion rate
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          {/* Top Robot Types */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Top Robot Types</h3>
            <div className="space-y-3">
              {analytics?.top_robot_types?.map((robot, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-neutral-300">{robot.type}</span>
                      <span className="text-neutral-400 text-sm">{robot.count} calcs</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-2">
                      <div 
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${robot.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-neutral-500 text-center py-4">No data available</p>}
            </div>
          </div>

          {/* Top Industries */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Top Industries</h3>
            <div className="space-y-3">
              {analytics?.top_industries?.map((industry, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-neutral-300">{industry.name}</span>
                      <span className="text-neutral-400 text-sm">{industry.count} calcs</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-2">
                      <div 
                        className="bg-cyan-500 h-2 rounded-full transition-all"
                        style={{ width: `${industry.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-neutral-500 text-center py-4">No data available</p>}
            </div>
          </div>

        </div>

        {/* Regional Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          {/* Geographic Distribution */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Geographic Distribution</h3>
            <div className="space-y-3">
              {analytics?.top_regions?.map((region, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-neutral-300">{region.name}</span>
                      <span className="text-neutral-400 text-sm">{region.searches} searches</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all"
                        style={{ width: `${region.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-neutral-500 text-center py-4">No data available</p>}
            </div>
          </div>

          {/* Cost Distribution */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50">
            <h3 className="text-lg font-semibold text-white mb-4">Robot Cost Distribution</h3>
            <div className="space-y-3">
              {analytics?.cost_buckets?.map((bucket, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-neutral-300">{bucket.range}</span>
                      <span className="text-neutral-400 text-sm">{bucket.count} robots</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full transition-all"
                        style={{ width: `${bucket.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-neutral-500 text-center py-4">No data available</p>}
            </div>
          </div>

        </div>

        {/* Insights & Recommendations */}
        <div className="border border-emerald-800 rounded-lg p-6 bg-neutral-900/50">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">📊 Strategic Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30">
              <div className="text-neutral-300 font-medium mb-2">🔥 Hottest Trend</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.hottest_trend || 'Not enough data yet'}
              </p>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30">
              <div className="text-neutral-300 font-medium mb-2">💡 Opportunity</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.opportunity || 'Gather more data to reveal opportunities'}
              </p>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30">
              <div className="text-neutral-300 font-medium mb-2">📈 Growth Area</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.growth_area || 'Continue monitoring user behavior'}
              </p>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30">
              <div className="text-neutral-300 font-medium mb-2">🎯 Action Item</div>
              <p className="text-neutral-400 text-sm">
                {analytics?.insights?.action_item || 'Build features users are requesting'}
              </p>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
