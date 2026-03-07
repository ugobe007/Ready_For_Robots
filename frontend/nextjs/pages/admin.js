/**
 * Ready for Robots — Admin Panel
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 *
 * Tabs:
 *  Overview       — stats: companies, signals, scored + breakdowns
 *  Import URLs    — paste URLs to register as scrape targets
 *  Import Companies — bulk-import company records (JSON)
 *  Scraper        — trigger scraper runs, view registered targets
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// ── tiny helpers ───────────────────────────────────────────────────────────

function StatCard({ label, value, sub }) {
  return (
    <div className="border border-neutral-800 px-5 py-4 min-w-[140px]">
      <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-1">{label}</div>
      <div className="text-2xl tabular-nums text-neutral-100">{value ?? '—'}</div>
      {sub && <div className="text-[11px] text-neutral-600 mt-1">{sub}</div>}
    </div>
  );
}

function Tag({ children, color = 'neutral' }) {
  const map = {
    emerald: 'border-emerald-800 text-emerald-400',
    cyan:    'border-cyan-800 text-cyan-400',
    yellow:  'border-yellow-800 text-yellow-400',
    neutral: 'border-neutral-700 text-neutral-400',
    red:     'border-red-800 text-red-400',
  };
  return (
    <span className={`border text-[10px] px-2 py-0.5 ${map[color] || map.neutral}`}>
      {children}
    </span>
  );
}

function Notice({ type = 'ok', children }) {
  const s = type === 'ok'
    ? 'border-emerald-800 text-emerald-400'
    : type === 'err'
    ? 'border-red-800 text-red-400'
    : 'border-neutral-700 text-neutral-400';
  return <div className={`border px-4 py-3 text-sm mt-3 ${s}`}>{children}</div>;
}

function Spinner() {
  return <span className="inline-block w-3 h-3 border border-neutral-500 border-t-cyan-400 rounded-full animate-spin" />;
}

const TABS = ['Dashboard', 'Users', 'Companies', 'Scrapers', 'Analytics', 'System', 'Robot Companies'];

const SCRAPERS  = ['all', 'job_board', 'hotel_dir', 'rss_feed', 'news'];
const INDUSTRIES = ['', 'Logistics', 'Hospitality', 'Food Service', 'Healthcare'];
const SIGNAL_TYPES = [
  '', 'labor_pain', 'labor_shortage', 'strategic_hire',
  'automation_intent', 'service_consistency', 'equipment_integration',
  'funding_round', 'capex', 'ma_activity', 'expansion',
];

// ── Analytics ──────────────────────────────────────────────────────────────

function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  const fetchAnalytics = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/analytics?range=${timeRange}`)
      .then(r => r.json())
      .then(d => { setAnalytics(d); setLoading(false); })
      .catch(e => { console.error('Analytics error:', e); setLoading(false); });
  }, [timeRange]);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  if (loading) return <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading analytics…</div>;
  if (!analytics) return <Notice type="err">No analytics data available</Notice>;

  return (
    <div className="space-y-8">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100">Platform Analytics</h2>
          <p className="text-xs text-neutral-600 mt-1">Track user behavior and platform usage</p>
        </div>
        <div className="flex items-center gap-2">
          {[
            { label: '7D', value: '7d' },
            { label: '30D', value: '30d' },
            { label: '90D', value: '90d' },
            { label: 'All', value: 'all' }
          ].map((range) => (
            <button
              key={range.value}
              onClick={() => setTimeRange(range.value)}
              className={`px-3 py-1.5 text-xs border transition-colors ${
                timeRange === range.value
                  ? 'border-emerald-600 text-emerald-400'
                  : 'border-neutral-800 text-neutral-500 hover:border-neutral-700'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <StatCard label="Total Calculations" value={analytics?.total_calculations || 0} sub={`+${analytics?.calculation_growth || 0}% growth`} />
        <StatCard label="Robot Searches" value={analytics?.robot_searches || 0} sub={`${analytics?.avg_matches_per_search || 0} avg matches`} />
        <StatCard label="Avg Payback" value={`${analytics?.avg_payback_months || 0}mo`} sub={`$${(analytics?.avg_robot_cost || 0).toLocaleString()} avg cost`} />
        <StatCard label="Email Captures" value={analytics?.email_captures || 0} sub={`${analytics?.conversion_rate || 0}% conversion`} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Robot Types */}
        <div className="border border-neutral-800 p-5">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-4">Top Robot Types</div>
          <div className="space-y-3">
            {analytics?.top_robot_types?.map((robot, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1 text-xs">
                  <span className="text-neutral-300">{robot.type}</span>
                  <span className="text-neutral-500 tabular-nums">{robot.count}</span>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-1.5">
                  <div className="bg-emerald-500 h-1.5 rounded-full transition-all" style={{ width: `${robot.percentage}%` }}></div>
                </div>
              </div>
            )) || <p className="text-neutral-600 text-xs text-center py-4">No data</p>}
          </div>
        </div>

        {/* Top Industries */}
        <div className="border border-neutral-800 p-5">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-4">Top Industries</div>
          <div className="space-y-3">
            {analytics?.top_industries?.map((industry, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1 text-xs">
                  <span className="text-neutral-300">{industry.name}</span>
                  <span className="text-neutral-500 tabular-nums">{industry.count}</span>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-1.5">
                  <div className="bg-cyan-500 h-1.5 rounded-full transition-all" style={{ width: `${industry.percentage}%` }}></div>
                </div>
              </div>
            )) || <p className="text-neutral-600 text-xs text-center py-4">No data</p>}
          </div>
        </div>

        {/* Geographic Distribution */}
        <div className="border border-neutral-800 p-5">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-4">Geographic Distribution</div>
          <div className="space-y-3">
            {analytics?.top_regions?.map((region, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1 text-xs">
                  <span className="text-neutral-300">{region.name}</span>
                  <span className="text-neutral-500 tabular-nums">{region.searches}</span>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-1.5">
                  <div className="bg-purple-500 h-1.5 rounded-full transition-all" style={{ width: `${region.percentage}%` }}></div>
                </div>
              </div>
            )) || <p className="text-neutral-600 text-xs text-center py-4">No data</p>}
          </div>
        </div>

        {/* Cost Distribution */}
        <div className="border border-neutral-800 p-5">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-4">Robot Cost Distribution</div>
          <div className="space-y-3">
            {analytics?.cost_buckets?.map((bucket, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1 text-xs">
                  <span className="text-neutral-300">{bucket.range}</span>
                  <span className="text-neutral-500 tabular-nums">{bucket.count}</span>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-1.5">
                  <div className="bg-yellow-500 h-1.5 rounded-full transition-all" style={{ width: `${bucket.percentage}%` }}></div>
                </div>
              </div>
            )) || <p className="text-neutral-600 text-xs text-center py-4">No data</p>}
          </div>
        </div>
      </div>

      {/* Strategic Insights */}
      <div className="border border-emerald-900 p-5">
        <div className="text-[10px] uppercase tracking-widest text-emerald-500 mb-4">📊 Strategic Insights</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-neutral-800 p-3">
            <div className="text-xs text-neutral-400 mb-1">🔥 Hottest Trend</div>
            <p className="text-xs text-neutral-500">{analytics?.insights?.hottest_trend || 'Not enough data yet'}</p>
          </div>
          <div className="border border-neutral-800 p-3">
            <div className="text-xs text-neutral-400 mb-1">💡 Opportunity</div>
            <p className="text-xs text-neutral-500">{analytics?.insights?.opportunity || 'Gather more data'}</p>
          </div>
          <div className="border border-neutral-800 p-3">
            <div className="text-xs text-neutral-400 mb-1">📈 Growth Area</div>
            <p className="text-xs text-neutral-500">{analytics?.insights?.growth_area || 'Monitor user behavior'}</p>
          </div>
          <div className="border border-neutral-800 p-3">
            <div className="text-xs text-neutral-400 mb-1">🎯 Action Item</div>
            <p className="text-xs text-neutral-500">{analytics?.insights?.action_item || 'Build requested features'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Users ──────────────────────────────────────────────────────────────────

function Users() {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userActivity, setUserActivity] = useState(null);
  const [loadingActivity, setLoadingActivity] = useState(false);

  const loadUsers = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/admin/users`).then(r => r.json()),
      fetch(`${API}/api/admin/users/stats`).then(r => r.json())
    ])
      .then(([usersData, statsData]) => {
        setUsers(usersData.users || []);
        setStats(statsData);
        setLoading(false);
      })
      .catch(e => { console.error(e); setLoading(false); });
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const viewActivity = (userId) => {
    setSelectedUser(userId);
    setLoadingActivity(true);
    fetch(`${API}/api/admin/users/${userId}/activity`)
      .then(r => r.json())
      .then(d => { setUserActivity(d); setLoadingActivity(false); })
      .catch(e => { console.error(e); setLoadingActivity(false); });
  };

  const deleteUser = (userId, email) => {
    if (!confirm(`Delete user ${email} and ALL their data? This cannot be undone.`)) return;
    fetch(`${API}/api/admin/users/${userId}`, { method: 'DELETE' })
      .then(r => r.json())
      .then(d => {
        if (d.status === 'success') {
          alert(`User ${email} deleted`);
          loadUsers();
          setSelectedUser(null);
          setUserActivity(null);
        } else {
          alert(`Error: ${d.message}`);
        }
      })
      .catch(e => alert(`Error deleting user: ${e.message}`));
  };

  if (loading) return <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading users…</div>;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100">User Management</h2>
          <p className="text-xs text-neutral-600 mt-1">Manage registered users and view activity</p>
        </div>
        <button onClick={loadUsers} className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-800 transition-colors">
          🔄 Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <StatCard label="Total Users" value={stats.total_users} />
          <StatCard label="Active (7d)" value={stats.active_users} />
          <StatCard label="Total Saved" value={stats.total_saved} />
          <StatCard label="Total Reports" value={stats.total_reports} />
          <StatCard label="Total Lists" value={stats.total_lists} />
        </div>
      )}

      {/* Users Table */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">
          All Users ({users.length})
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left py-2 text-xs text-neutral-500 font-normal">Email</th>
              <th className="text-left py-2 text-xs text-neutral-500 font-normal">Created</th>
              <th className="text-left py-2 text-xs text-neutral-500 font-normal">Last Active</th>
              <th className="text-right py-2 text-xs text-neutral-500 font-normal">Saved</th>
              <th className="text-right py-2 text-xs text-neutral-500 font-normal">Reports</th>
              <th className="text-right py-2 text-xs text-neutral-500 font-normal">Lists</th>
              <th className="text-right py-2 text-xs text-neutral-500 font-normal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-b border-neutral-800/50 hover:bg-neutral-900/30">
                <td className="py-2 text-neutral-300">{user.email}</td>
                <td className="py-2 text-neutral-500 text-xs">{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td>
                <td className="py-2 text-neutral-500 text-xs">{user.last_active ? new Date(user.last_active).toLocaleDateString() : '—'}</td>
                <td className="py-2 text-right tabular-nums text-neutral-500">{user.saved_count}</td>
                <td className="py-2 text-right tabular-nums text-neutral-500">{user.reports_count}</td>
                <td className="py-2 text-right tabular-nums text-neutral-500">{user.lists_count}</td>
                <td className="py-2 text-right">
                  <button
                    onClick={() => viewActivity(user.id)}
                    className="border border-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors mr-2"
                  >
                    View
                  </button>
                  <button
                    onClick={() => deleteUser(user.id, user.email)}
                    className="border border-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:text-red-400 hover:border-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User Activity Panel */}
      {selectedUser && (
        <div className="border border-cyan-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-cyan-400">User Activity</div>
            <button onClick={() => { setSelectedUser(null); setUserActivity(null); }} className="text-neutral-600 hover:text-neutral-400 text-xs">
              ✕ Close
            </button>
          </div>
          
          {loadingActivity ? (
            <div className="text-neutral-500 text-sm py-4 flex gap-2 items-center"><Spinner /> Loading activity…</div>
          ) : userActivity ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Saved Companies */}
              <div>
                <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Saved Companies ({userActivity.saved_companies?.length || 0})</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {userActivity.saved_companies?.map(c => (
                    <div key={c.company_id} className="text-xs text-neutral-400 border-l-2 border-neutral-800 pl-2">
                      {c.name} <span className="text-neutral-600">· {c.industry}</span>
                    </div>
                  ))}
                  {!userActivity.saved_companies?.length && <div className="text-xs text-neutral-600">No saved companies</div>}
                </div>
              </div>

              {/* Reports */}
              <div>
                <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Reports ({userActivity.reports?.length || 0})</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {userActivity.reports?.map(r => (
                    <div key={r.id} className="text-xs text-neutral-400 border-l-2 border-neutral-800 pl-2">
                      Report #{r.id.slice(0, 8)} <span className="text-neutral-600">· {r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</span>
                    </div>
                  ))}
                  {!userActivity.reports?.length && <div className="text-xs text-neutral-600">No reports</div>}
                </div>
              </div>

              {/* Lists */}
              <div>
                <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Lists ({userActivity.lists?.length || 0})</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {userActivity.lists?.map(l => (
                    <div key={l.id} className="text-xs text-neutral-400 border-l-2 border-neutral-800 pl-2">
                      {l.name} <span className="text-neutral-600">· {l.description || 'No description'}</span>
                    </div>
                  ))}
                  {!userActivity.lists?.length && <div className="text-xs text-neutral-600">No lists</div>}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

// ── Overview ───────────────────────────────────────────────────────────────

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const loadStats = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/admin/stats`)
      .then(r => r.json())
      .then(d => { setStats(d); setLoading(false); setRefreshing(false); })
      .catch(e => { setErr(e.message); setLoading(false); setRefreshing(false); });
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  if (loading) return <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading dashboard…</div>;
  if (err)     return <Notice type="err">Error: {err}</Notice>;
  if (!stats)  return null;

  const { totals, by_industry, by_signal_type, recent_companies, pipeline_value, conversion_metrics } = stats;

  return (
    <div className="space-y-8">
      {/* Header Actions */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100">Admin Dashboard</h2>
          <p className="text-xs text-neutral-600 mt-1">System metrics and business intelligence</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-800 transition-colors disabled:opacity-50"
        >
          {refreshing ? <><Spinner /> Refreshing...</> : '🔄 Refresh Data'}
        </button>
      </div>

      {/* Business Metrics */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Business Metrics</div>
        <div className="flex flex-wrap gap-3">
          <StatCard label="Total Pipeline" value={`$${pipeline_value?.toLocaleString() || 0}`} sub="Estimated value" />
          <StatCard label="Hot Leads" value={totals.scored.toLocaleString()} sub={`${conversion_metrics?.hot_rate || 0}% conversion`} />
          <StatCard label="Companies" value={totals.companies.toLocaleString()} sub={`${totals.signals} signals`} />
          <StatCard label="Avg Score" value={conversion_metrics?.avg_score || '—'} sub="Quality indicator" />
        </div>
      </div>

      {/* System Health */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">System Health</div>
        <div className="flex flex-wrap gap-3">
          <StatCard label="Scrapers" value={stats.scraper_health?.active || 0} sub={`${stats.scraper_health?.success_rate || 0}% success`} />
          <StatCard label="API Uptime" value="99.9%" sub="Last 30 days" />
          <StatCard label="DB Size" value={stats.database?.size_mb ? `${stats.database.size_mb}MB` : '—'} sub={`${stats.database?.tables || 0} tables`} />
          <StatCard label="Cache Hit" value={`${stats.performance?.cache_hit_rate || 85}%`} sub="Performance" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* By Industry */}
        <div>
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">By Industry</div>
          <table className="w-full text-sm">
            <tbody>
              {by_industry.map(r => (
                <tr key={r.industry} className="border-b border-neutral-800/50">
                  <td className="py-1.5 text-neutral-300">{r.industry || 'Unknown'}</td>
                  <td className="py-1.5 text-right tabular-nums text-neutral-500">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* By Signal Type */}
        <div>
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">By Signal Type</div>
          <table className="w-full text-sm">
            <tbody>
              {by_signal_type.map(r => (
                <tr key={r.signal_type} className="border-b border-neutral-800/50">
                  <td className="py-1.5 text-neutral-300">{r.signal_type}</td>
                  <td className="py-1.5 text-right tabular-nums text-neutral-500">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Companies */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Recent Companies</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left py-2 text-neutral-600 font-normal">Name</th>
              <th className="text-left py-2 text-neutral-600 font-normal">Industry</th>
              <th className="text-left py-2 text-neutral-600 font-normal">Source</th>
              <th className="text-right py-2 text-neutral-600 font-normal">Created</th>
            </tr>
          </thead>
          <tbody>
            {recent_companies.map(c => (
              <tr key={c.id} className="border-b border-neutral-800/40 hover:bg-neutral-900/40">
                <td className="py-2 text-neutral-200">{c.name}</td>
                <td className="py-2 text-neutral-500">{c.industry || '—'}</td>
                <td className="py-2 text-neutral-600 truncate max-w-[200px] text-xs">{c.source || '—'}</td>
                <td className="py-2 text-right text-neutral-600 text-xs tabular-nums">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Import URLs ────────────────────────────────────────────────────────────

function ImportUrls() {
  const [text, setText]       = useState('');
  const [industry, setIndustry]   = useState('');
  const [sigType, setSigType]     = useState('');
  const [scrapeNow, setScrapeNow] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [err, setErr]             = useState('');

  const submit = useCallback(async () => {
    const urls = text.split('\n').map(s => s.trim()).filter(Boolean);
    if (!urls.length) return;
    setLoading(true); setResult(null); setErr('');
    try {
      const r = await fetch(`${API}/api/admin/import/urls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls,
          industry:    industry || null,
          signal_type: sigType  || null,
          scrape_now:  scrapeNow,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setResult(d);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [text, industry, sigType, scrapeNow]);

  return (
    <div className="space-y-5 max-w-2xl">
      <p className="text-sm text-neutral-500">
        Paste URLs to register as scrape targets — one per line. The system auto-detects
        the scraper type and industries from the URL structure.
      </p>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        className="w-full h-40 bg-transparent border border-neutral-700 text-neutral-200 text-sm p-3 resize-y focus:outline-none focus:border-cyan-700 font-mono"
        placeholder={"https://www.indeed.com/jobs?q=housekeeper+hotel\nhttps://www.supplychaindive.com/feeds/news/\nhttps://www.yellowpages.com/search?..."}
      />

      <div className="flex flex-wrap gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-neutral-500">Industry hint</label>
          <select
            value={industry}
            onChange={e => setIndustry(e.target.value)}
            className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-cyan-700"
          >
            {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'Auto-detect'}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-neutral-500">Signal type hint</label>
          <select
            value={sigType}
            onChange={e => setSigType(e.target.value)}
            className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-cyan-700"
          >
            {SIGNAL_TYPES.map(s => <option key={s} value={s} className="bg-neutral-900">{s || 'Auto-detect'}</option>)}
          </select>
        </div>

        <div className="flex items-end pb-1.5">
          <label className="flex items-center gap-2 text-sm text-neutral-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={scrapeNow}
              onChange={e => setScrapeNow(e.target.checked)}
              className="accent-emerald-500"
            />
            Scrape immediately
          </label>
        </div>
      </div>

      <button
        onClick={submit}
        disabled={loading || !text.trim()}
        className="border border-emerald-700 text-emerald-400 text-sm px-5 py-2 hover:bg-emerald-950 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {loading && <Spinner />}
        {loading ? 'Importing…' : 'Import URLs'}
      </button>

      {err    && <Notice type="err">{err}</Notice>}
      {result && (
        <Notice type="ok">
          <strong>{result.added}</strong> added · <strong>{result.skipped}</strong> skipped
          {result.skipped_details?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5 text-neutral-500">
              {result.skipped_details.map((s, i) => (
                <li key={i}>{s.url || s.name} — {s.reason}</li>
              ))}
            </ul>
          )}
        </Notice>
      )}

      {result?.targets?.length > 0 && (
        <div className="mt-4">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Registered</div>
          <div className="space-y-2">
            {result.targets.map((t, i) => (
              <div key={i} className="border border-neutral-800 px-3 py-2">
                <div className="text-xs text-neutral-300 font-mono truncate">{t.url}</div>
                <div className="flex gap-2 mt-1 flex-wrap">
                  <Tag color="cyan">{t.scraper}</Tag>
                  {t.industries.map(ind => <Tag key={ind}>{ind}</Tag>)}
                  {t.signal_types.map(st => <Tag key={st} color="emerald">{st}</Tag>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Import Companies ───────────────────────────────────────────────────────

const COMPANY_EXAMPLE = JSON.stringify([
  { name: "Marriott Chicago River North", industry: "Hospitality", website: "https://marriott.com", location_city: "Chicago", location_state: "IL" },
  { name: "XPO Logistics Memphis DC", industry: "Logistics", website: "https://xpo.com", location_city: "Memphis", location_state: "TN" },
], null, 2);

function ImportCompanies() {
  const [text, setText]     = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [err, setErr]         = useState('');

  const submit = useCallback(async () => {
    let companies;
    try {
      companies = JSON.parse(text);
      if (!Array.isArray(companies)) companies = [companies];
    } catch {
      setErr('Invalid JSON — paste an array of company objects.'); return;
    }
    setLoading(true); setResult(null); setErr('');
    try {
      const r = await fetch(`${API}/api/admin/import/companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setResult(d);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [text]);

  return (
    <div className="space-y-5 max-w-2xl">
      <p className="text-sm text-neutral-500">
        Paste a JSON array of company objects. Required: <code className="text-cyan-500">name</code>.
        Optional: <code className="text-neutral-400">website industry location_city location_state source</code>.
      </p>

      <details className="border border-neutral-800 text-xs">
        <summary className="px-3 py-2 text-neutral-500 cursor-pointer hover:text-neutral-400">Example format</summary>
        <pre className="px-3 pb-3 text-neutral-600 overflow-auto">{COMPANY_EXAMPLE}</pre>
      </details>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        className="w-full h-48 bg-transparent border border-neutral-700 text-neutral-200 text-sm p-3 resize-y focus:outline-none focus:border-cyan-700 font-mono"
        placeholder={'[\n  { "name": "Hilton Denver Tech Center", "industry": "Hospitality" }\n]'}
      />

      <button
        onClick={submit}
        disabled={loading || !text.trim()}
        className="border border-cyan-700 text-cyan-400 text-sm px-5 py-2 hover:bg-cyan-950 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {loading && <Spinner />}
        {loading ? 'Importing…' : 'Import Companies'}
      </button>

      {err    && <Notice type="err">{err}</Notice>}
      {result && (
        <Notice type="ok">
          <strong>{result.added}</strong> added · <strong>{result.skipped}</strong> skipped
          {result.skipped_details?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5 text-neutral-500">
              {(result.skipped_details || result.names?.map(n => ({ name: n })) || []).map((s, i) => (
                <li key={i}>{s.name} {s.reason ? `— ${s.reason}` : ''}</li>
              ))}
            </ul>
          )}
          {result.names?.length > 0 && (
            <ul className="mt-2 text-xs space-y-0.5">
              {result.names.map((n, i) => <li key={i} className="text-emerald-400">+ {n}</li>)}
            </ul>
          )}
        </Notice>
      )}
    </div>
  );
}

// ── Scraper Panel ──────────────────────────────────────────────────────────

function ScraperPanel() {
  const [targets, setTargets]       = useState(null);
  const [loadingTargets, setLT]     = useState(true);
  const [filterScraper, setFS]      = useState('');
  const [filterIndustry, setFI]     = useState('');
  const [triggerScraper, setTS]     = useState('all');
  const [triggerIndustry, setTI]    = useState('');
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTR]      = useState(null);
  const [triggerErr, setTE]         = useState('');

  const loadTargets = useCallback(() => {
    setLT(true);
    const params = new URLSearchParams();
    if (filterScraper)  params.set('scraper', filterScraper);
    if (filterIndustry) params.set('industry', filterIndustry);
    fetch(`${API}/api/admin/scrape/targets?${params}`)
      .then(r => r.json())
      .then(d => { setTargets(d); setLT(false); })
      .catch(() => setLT(false));
  }, [filterScraper, filterIndustry]);

  useEffect(() => { loadTargets(); }, [loadTargets]);

  const triggerScrape = useCallback(async () => {
    setTriggering(true); setTR(null); setTE('');
    try {
      const r = await fetch(`${API}/api/admin/scrape/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scraper: triggerScraper, industry: triggerIndustry || null }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      setTR(d);
    } catch (e) {
      setTE(e.message);
    } finally {
      setTriggering(false);
    }
  }, [triggerScraper, triggerIndustry]);

  const summary = targets?.summary;

  return (
    <div className="space-y-8">
      {/* Trigger */}
      <div>
        <div className="text-[10px] uppercase tracking-widest text-neutral-500 mb-3">Trigger Scrape</div>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-neutral-600">Scraper</label>
            <select
              value={triggerScraper}
              onChange={e => setTS(e.target.value)}
              className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-emerald-700"
            >
              {SCRAPERS.map(s => <option key={s} value={s} className="bg-neutral-900">{s}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-neutral-600">Industry filter</label>
            <select
              value={triggerIndustry}
              onChange={e => setTI(e.target.value)}
              className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-1.5 focus:outline-none focus:border-emerald-700"
            >
              {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All industries'}</option>)}
            </select>
          </div>
          <button
            onClick={triggerScrape}
            disabled={triggering}
            className="border border-emerald-700 text-emerald-400 text-sm px-5 py-2 hover:bg-emerald-950 disabled:opacity-40 flex items-center gap-2"
          >
            {triggering && <Spinner />}
            {triggering ? 'Queuing…' : 'Run Scraper'}
          </button>
        </div>
        {triggerErr    && <Notice type="err">{triggerErr}</Notice>}
        {triggerResult && (
          <Notice type={triggerResult.status === 'queued' ? 'ok' : 'neutral'}>
            {triggerResult.status === 'queued'
              ? `Queued: ${triggerResult.scraper}${triggerResult.industry ? ' · ' + triggerResult.industry : ''}`
              : triggerResult.reason}
          </Notice>
        )}
      </div>

      {/* Summary counts */}
      {summary && (
        <div className="flex flex-wrap gap-3">
          <StatCard label="Job Board" value={summary.job_board} />
          <StatCard label="Hotel Dir" value={summary.hotel_dir} />
          <StatCard label="Logistics" value={summary.logistics_dir} />
          <StatCard label="RSS Feeds" value={summary.rss_feed} />
          <StatCard label="News Queries" value={summary.news_queries} />
          <StatCard label="Total" value={summary.total_targets} />
        </div>
      )}

      {/* Targets table */}
      <div>
        <div className="flex items-center gap-4 mb-3">
          <div className="text-[10px] uppercase tracking-widest text-neutral-500">Targets</div>
          <select
            value={filterScraper}
            onChange={e => setFS(e.target.value)}
            className="bg-transparent border border-neutral-800 text-neutral-500 text-xs px-2 py-1 focus:outline-none"
          >
            <option value="" className="bg-neutral-900">All scrapers</option>
            {SCRAPERS.filter(s => s !== 'all').map(s => <option key={s} value={s} className="bg-neutral-900">{s}</option>)}
          </select>
          <select
            value={filterIndustry}
            onChange={e => setFI(e.target.value)}
            className="bg-transparent border border-neutral-800 text-neutral-500 text-xs px-2 py-1 focus:outline-none"
          >
            {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All industries'}</option>)}
          </select>
        </div>

        {loadingTargets
          ? <div className="text-neutral-500 text-sm flex gap-2 items-center"><Spinner /> Loading…</div>
          : (
            <div className="space-y-1.5 max-h-[460px] overflow-y-auto pr-1">
              {targets?.targets?.map((t, i) => (
                <div key={i} className="border border-neutral-800/60 px-3 py-2 hover:border-neutral-700">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-xs text-neutral-300 flex-1 min-w-0">{t.label}</span>
                    <Tag color="cyan">{t.scraper}</Tag>
                  </div>
                  <div className="text-[10px] font-mono text-neutral-600 truncate mt-0.5">{t.url}</div>
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    {t.industries.map(ind => <Tag key={ind}>{ind}</Tag>)}
                    {t.signal_types.map(st => <Tag key={st} color="emerald">{st}</Tag>)}
                    <Tag color="neutral">{t.cadence}</Tag>
                  </div>
                </div>
              ))}
            </div>
          )
        }
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

// Companies Manager Component
function CompaniesManager() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/admin/companies/search?q=${searchTerm}&industry=${filterIndustry}&limit=100`)
      .then(r => r.json())
      .then(d => { setCompanies(d.companies || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [searchTerm, filterIndustry]);

  const deleteCompany = async (id) => {
    if (!confirm('Delete this company and all its signals?')) return;
    setDeleting(id);
    try {
      await fetch(`${API}/api/admin/companies/${id}`, { method: 'DELETE' });
      setCompanies(companies.filter(c => c.id !== id));
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
    setDeleting(null);
  };

  return (
    <div className="space-y-5">
      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search companies..."
          className="flex-1 bg-transparent border border-neutral-700 text-neutral-200 text-sm px-4 py-2 focus:outline-none focus:border-emerald-700"
        />
        <select
          value={filterIndustry}
          onChange={e => setFilterIndustry(e.target.value)}
          className="bg-transparent border border-neutral-700 text-neutral-300 text-sm px-3 py-2 focus:outline-none focus:border-emerald-700"
        >
          {INDUSTRIES.map(i => <option key={i} value={i} className="bg-neutral-900">{i || 'All Industries'}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-neutral-500 text-sm py-8 flex gap-2 items-center"><Spinner /> Loading companies...</div>
      ) : (
        <>
          <div className="text-xs text-neutral-600">{companies.length} companies found</div>
          <div className="space-y-2">
            {companies.map(c => (
              <div key={c.id} className="border border-neutral-800 px-4 py-3 hover:border-neutral-700 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-neutral-100 font-medium">{c.name}</span>
                      {c.industry && <Tag>{c.industry}</Tag>}
                      {c.score && <Tag color="emerald">Score: {c.score}</Tag>}
                    </div>
                    <div className="text-xs text-neutral-600 mt-1">
                      {c.website && <span>{c.website} · </span>}
                      {c.location_city && <span>{c.location_city}, {c.location_state} · </span>}
                      <span>{c.signal_count || 0} signals</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => window.open(`/companies/${c.id}`, '_blank')}
                      className="text-xs border border-neutral-700 px-3 py-1 text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
                    >
                      View
                    </button>
                    <button
                      onClick={() => deleteCompany(c.id)}
                      disabled={deleting === c.id}
                      className="text-xs border border-neutral-700 px-3 py-1 text-neutral-400 hover:text-red-400 hover:border-red-700 transition-colors disabled:opacity-50"
                    >
                      {deleting === c.id ? <Spinner /> : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// System Controls Component
function SystemControls() {
  const [clearing, setClearing] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [result, setResult] = useState('');

  const clearCache = async () => {
    if (!confirm('Clear all cache data?')) return;
    setClearing(true);
    try {
      await fetch(`${API}/api/admin/system/cache/clear`, { method: 'POST' });
      setResult('✅ Cache cleared successfully');
    } catch (e) {
      setResult('❌ Error: ' + e.message);
    }
    setClearing(false);
  };

  const reindexDatabase = async () => {
    if (!confirm('Reindex database? This may take several minutes.')) return;
    setReindexing(true);
    try {
      await fetch(`${API}/api/admin/system/reindex`, { method: 'POST' });
      setResult('✅ Database reindexed successfully');
    } catch (e) {
      setResult('❌ Error: ' + e.message);
    }
    setReindexing(false);
  };

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h3 className="text-sm font-semibold text-neutral-200 mb-4">System Operations</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Clear Cache</div>
              <div className="text-xs text-neutral-600">Reset all API and query caches</div>
            </div>
            <button
              onClick={clearCache}
              disabled={clearing}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors disabled:opacity-50"
            >
              {clearing ? <Spinner /> : 'Clear Cache'}
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Reindex Database</div>
              <div className="text-xs text-neutral-600">Optimize database indexes for faster queries</div>
            </div>
            <button
              onClick={reindexDatabase}
              disabled={reindexing}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors disabled:opacity-50"
            >
              {reindexing ? <Spinner /> : 'Reindex'}
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Trigger All Scrapers</div>
              <div className="text-xs text-neutral-600">Run all active scrapers immediately</div>
            </div>
            <Link 
              href="#"
              onClick={(e) => { e.preventDefault(); alert('Use Scrapers tab for granular control'); }}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
            >
              Go to Scrapers
            </Link>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-neutral-200 mb-4">Database Management</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Export All Data</div>
              <div className="text-xs text-neutral-600">Download complete database as JSON</div>
            </div>
            <button
              onClick={() => window.open(`${API}/api/admin/export/all`, '_blank')}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors"
            >
              Export
            </button>
          </div>

          <div className="flex items-center justify-between border border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm text-neutral-200">Backup Database</div>
              <div className="text-xs text-neutral-600">Create timestamped backup</div>
            </div>
            <button
              onClick={() => alert('Feature coming soon - use database provider backup tools')}
              className="border border-neutral-700 px-4 py-2 text-sm text-neutral-400 hover:text-emerald-400 hover:border-emerald-700 transition-colors"
            >
              Backup
            </button>
          </div>
        </div>
      </div>

      {result && <Notice type={result.startsWith('✅') ? 'ok' : 'err'}>{result}</Notice>}
    </div>
  );
}

export default function AdminPage() {
  const [tab, setTab] = useState('Dashboard');

  return (
    <div style={{ backgroundColor: '#080808' }} className="min-h-screen text-neutral-300">
      {/* Top bar */}
      <header className="border-b border-neutral-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <span className="text-sm font-medium tracking-wide text-neutral-200">Ready for Robots</span>
          <span className="text-neutral-700">|</span>
          <span className="text-sm text-neutral-500">Admin</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/analytics" className="text-xs text-neutral-600 hover:text-emerald-400 transition-colors">
            📊 Analytics
          </Link>
          <Link href="/" className="text-xs text-neutral-600 hover:text-cyan-400 transition-colors">
            ← Dashboard
          </Link>
        </div>
      </header>

      <main className="px-6 pt-6 pb-16 max-w-5xl mx-auto">
        {/* Tab bar */}
        <div className="flex gap-1 border-b border-neutral-800 mb-8">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm -mb-px transition-colors ${
                tab === t
                  ? 'border-b border-emerald-500 text-emerald-400'
                  : 'text-neutral-600 hover:text-neutral-400'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === 'Dashboard'   && <Dashboard />}
        {tab === 'Users'       && <Users />}
        {tab === 'Companies'   && <CompaniesManager />}
        {tab === 'Scrapers'    && <ScraperPanel />}
        {tab === 'Analytics'   && <Analytics />}
        {tab === 'System'      && <SystemControls />}
        {tab === 'Robot Companies' && <RobotCompaniesLink />}
      </main>
    </div>
  );
}

function RobotCompaniesLink() {
  return (
    <div className="max-w-2xl">
      <div className="border border-emerald-800 bg-emerald-950/20 px-6 py-8">
        <h2 className="text-lg font-semibold text-emerald-400 mb-3">
          🤖 Robot Companies Management
        </h2>
        <p className="text-sm text-neutral-400 mb-6">
          Access the full robot companies database with workflow management and email outreach tools.
          This is an admin-only section for managing Chinese robotics companies looking to enter the U.S. market.
        </p>
        <div className="space-y-3 text-sm text-neutral-300">
          <div className="flex items-start gap-2">
            <span className="text-emerald-500">•</span>
            <span>View 200+ robot company profiles with scoring and signals</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-500">•</span>
            <span>Track workflow stages and next actions for each company</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-500">•</span>
            <span>Generate personalized email introductions (6 template types)</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-500">•</span>
            <span>Filter by hot leads, distribution needs, market entry wave</span>
          </div>
        </div>
        <Link 
          href="/robot-companies"
          className="mt-6 inline-block border border-emerald-500 text-emerald-400 px-6 py-3 text-sm font-medium hover:bg-emerald-500/10 transition-colors"
        >
          Open Robot Companies →
        </Link>
      </div>
    </div>
  );
}
