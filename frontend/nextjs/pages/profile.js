/**
 * Ready for Robots — User Profile Page
 * Route: /profile
 *
 * Requires login (redirects to /login if not authenticated).
 * All data is stored in Supabase via /api/user/* endpoints.
 *
 * Sections:
 *  1. AI Analytics Reports — saved full analysis snapshots
 *  2. Saved Companies      — flagged companies
 *  3. Target Lists         — grouped outreach lists
 *  4. Settings             — display name, sign out
 */
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from './_app';
import { supabase, authHeader } from '../lib/supabase';

const API = process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// ── Shared UI ─────────────────────────────────────────────────────────────────

const TIER_META = {
  HOT:  { text: 'text-red-400',    border: 'border-red-800'    },
  WARM: { text: 'text-yellow-400', border: 'border-yellow-800' },
  COLD: { text: 'text-cyan-400',   border: 'border-cyan-900'   },
};
const URGENCY_META = {
  ACT_NOW: { label: 'ACT NOW', text: 'text-red-400',     border: 'border-red-800'     },
  HOT:     { label: 'HOT',     text: 'text-orange-400',  border: 'border-orange-800'  },
  WARM:    { label: 'WARM',    text: 'text-yellow-400',  border: 'border-yellow-700'  },
  MONITOR: { label: 'MONITOR', text: 'text-cyan-400',    border: 'border-cyan-800'    },
  COLD:    { label: 'COLD',    text: 'text-neutral-500', border: 'border-neutral-700' },
};

function TierBadge({ tier }) {
  const m = TIER_META[tier] || TIER_META.COLD;
  return (
    <span className={`inline-flex items-center border ${m.border} ${m.text} rounded px-1.5 py-0.5 text-[10px] font-semibold leading-none`}>
      {tier || '—'}
    </span>
  );
}
function ScoreNum({ value }) {
  return (
    <span className="inline-flex items-center border border-emerald-700 text-emerald-400 rounded px-1.5 leading-none tabular-nums font-mono font-semibold text-[10px]"
      style={{ paddingTop: '0.2rem', paddingBottom: '0.2rem' }}>
      {Math.round(value ?? 0)}
    </span>
  );
}
function fmt(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
  } catch { return '—'; }
}
function Empty({ text }) {
  return (
    <div className="border border-neutral-800 rounded-lg px-6 py-8 text-center">
      <p className="text-xs text-neutral-700">{text}</p>
    </div>
  );
}

// ── Full Report Modal ─────────────────────────────────────────────────────────
const REPORT_TABS = ['summary', 'strategy', 'robot match', 'decision makers', 'intel', 'signals'];

function ReportModal({ report, onClose }) {
  const [tab, setTab] = useState('summary');
  const d     = report.report_data  || {};
  const sc    = report.summary_card || {};
  const strat = d.strategy          || {};
  const um    = URGENCY_META[strat.urgency] || URGENCY_META.MONITOR;

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[4vh]" onClick={onClose}>
      <div className="absolute inset-0 bg-black/80" />
      <div className="relative w-full max-w-3xl max-h-[90vh] flex flex-col bg-[#0c0c0c] border border-neutral-700 rounded-lg shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}>

        {/* header */}
        <div className="flex items-start justify-between px-6 py-4 border-b border-neutral-800 shrink-0">
          <div>
            <h2 className="text-base font-semibold text-neutral-100">{report.company_name}</h2>
            <p className="text-xs text-neutral-600 mt-0.5">{report.title} · saved {fmt(report.created_at)}</p>
          </div>
          <button onClick={onClose} className="text-neutral-600 hover:text-neutral-200 px-2 py-1 text-sm">✕</button>
        </div>

        {/* tabs */}
        <div className="flex border-b border-neutral-800 px-4 shrink-0 overflow-x-auto">
          {REPORT_TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-2.5 text-xs font-medium transition-colors border-b-2 whitespace-nowrap -mb-px ${
                tab === t ? 'border-emerald-600 text-emerald-400' : 'border-transparent text-neutral-600 hover:text-neutral-400'
              }`}>{t}</button>
          ))}
        </div>

        {/* content */}
        <div className="px-6 py-5 overflow-y-auto flex-1">

          {tab === 'summary' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="border border-neutral-800 rounded p-4 space-y-2">
                  <p className="label">intent scores</p>
                  {[['overall', d.scores?.overall_score], ['automation', d.scores?.automation_score],
                    ['labor pain', d.scores?.labor_pain_score], ['expansion', d.scores?.expansion_score],
                    ['market fit', d.scores?.market_fit_score]].map(([l, v]) => (
                    <div key={l} className="flex items-center justify-between">
                      <span className="text-xs text-neutral-500">{l}</span>
                      <span className="text-xs font-mono text-neutral-300 tabular-nums">{Math.round(v ?? 0)}</span>
                    </div>
                  ))}
                </div>
                <div className="border border-neutral-800 rounded p-4 space-y-1.5">
                  <p className="label">company</p>
                  <p className="text-xs text-neutral-300">{d.company?.industry}</p>
                  {d.company?.location_city && <p className="text-xs text-neutral-500">{d.company.location_city}, {d.company.location_state}</p>}
                  {d.company?.employee_estimate && <p className="text-xs text-neutral-600">{d.company.employee_estimate.toLocaleString()} employees</p>}
                  {d.company?.website && <a href={d.company.website} target="_blank" rel="noreferrer" className="text-[10px] text-cyan-700 hover:text-cyan-500 block truncate">{d.company.website.replace(/^https?:\/\//, '')}</a>}
                </div>
              </div>
              {sc.pitch_angle && (
                <div className="border border-neutral-800 rounded p-4">
                  <p className="label mb-1.5">pitch angle</p>
                  <p className="text-sm text-neutral-300 leading-relaxed">{sc.pitch_angle}</p>
                </div>
              )}
              {sc.top_robot && (
                <div className="border border-emerald-900 rounded p-4">
                  <p className="label mb-1">recommended robot</p>
                  <p className="text-sm font-semibold text-emerald-400">{sc.top_robot}</p>
                </div>
              )}
              {(sc.talking_points || []).length > 0 && (
                <div className="border border-neutral-800 rounded p-4">
                  <p className="label mb-2">key talking points</p>
                  <ul className="space-y-1.5">
                    {sc.talking_points.map((tp, i) => (
                      <li key={i} className="flex gap-2 text-xs text-neutral-400">
                        <span className="text-emerald-700 shrink-0">▸</span>{tp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {tab === 'strategy' && strat.urgency && (
            <div className={`border ${um.border} rounded p-5 space-y-4`}>
              <div className="flex items-center justify-between">
                <span className={`badge ${um.border} ${um.text}`}>{um.label}</span>
                <span className="text-xs text-neutral-600">{Math.round((strat.confidence || 0) * 100)}% confidence</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><p className="label block mb-1">who to contact</p><p className="text-sm text-neutral-200">{strat.contact_role}</p></div>
                <div><p className="label block mb-1">best channel</p><p className="text-sm text-neutral-200">{strat.best_channel}</p></div>
              </div>
              <div><p className="label block mb-1">lead with</p><p className="text-sm text-neutral-200 leading-relaxed">{strat.pitch_angle}</p></div>
              <div>
                <p className="label block mb-2">talking points</p>
                <ul className="space-y-2">
                  {(strat.talking_points || []).map((tp, i) => (
                    <li key={i} className="flex gap-2 text-sm text-neutral-300">
                      <span className="text-emerald-700 shrink-0">▸</span>{tp}
                    </li>
                  ))}
                </ul>
              </div>
              <div className={`border-t ${um.border} pt-4`}>
                <p className="label block mb-1">timing</p>
                <p className={`text-sm ${um.text} leading-relaxed`}>⏱ {strat.timing_note}</p>
              </div>
            </div>
          )}

          {tab === 'robot match' && (
            <div className="space-y-4">
              {(d.robot_match || []).map((r, i) => (
                <div key={i} className={`border ${i === 0 ? 'border-emerald-900' : 'border-neutral-800'} rounded p-4 space-y-2`}>
                  <div className="flex items-center gap-2">
                    <a href={r.url} target="_blank" rel="noreferrer" className="font-semibold text-neutral-100 hover:text-emerald-400 text-sm">{r.name} ↗</a>
                    {i === 0 && <span className="badge border-emerald-800 text-emerald-400">best match</span>}
                  </div>
                  <p className="text-xs text-neutral-400">{r.use_cases?.[0]}</p>
                  {r.roi_stat && <p className="text-xs text-cyan-500/70 border border-cyan-900 rounded px-2 py-1">{r.roi_stat}</p>}
                  {(r.why_now || []).map((w, j) => <p key={j} className="text-xs text-amber-500/70">▸ {w}</p>)}
                </div>
              ))}
            </div>
          )}

          {tab === 'decision makers' && (
            <div className="space-y-2">
              {(d.decision_makers || []).map((dm, i) => (
                <div key={i} className="flex items-center justify-between border border-neutral-800 rounded px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-neutral-200">{dm.title}</p>
                    <p className="text-xs text-neutral-600">{dm.dept}</p>
                  </div>
                  <a href={dm.linkedin_search} target="_blank" rel="noreferrer" className="badge border-blue-900 text-blue-400 hover:border-blue-700">Find on LinkedIn ↗</a>
                </div>
              ))}
            </div>
          )}

          {tab === 'intel' && (
            <div className="space-y-2">
              {(d.intel_links || []).map((l, i) => (
                <a key={i} href={l.url} target="_blank" rel="noreferrer"
                  className="flex items-center justify-between border border-neutral-800 rounded px-4 py-3 hover:border-neutral-600 group transition-colors">
                  <p className="text-sm font-medium text-neutral-200 group-hover:text-white">{l.label}</p>
                  <span className="text-xs text-neutral-700 group-hover:text-neutral-400">↗</span>
                </a>
              ))}
            </div>
          )}

          {tab === 'signals' && (
            <div className="space-y-2">
              {(d.signals || []).map((s, i) => (
                <div key={i} className="flex items-start gap-3 border border-neutral-800 rounded px-4 py-3">
                  <span className="badge border-neutral-700 text-neutral-400 shrink-0">{s.signal_type}</span>
                  <span className="text-sm text-neutral-400 flex-1 leading-relaxed">{s.text || s.raw_text}</span>
                  <span className="text-xs font-mono text-neutral-600 tabular-nums shrink-0">{((s.strength || 0) * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Report card ───────────────────────────────────────────────────────────────
function ReportCard({ report, onDelete, onView }) {
  const sc = report.summary_card || {};
  const um = URGENCY_META[sc.urgency] || URGENCY_META.MONITOR;
  const tm = TIER_META[sc.tier] || TIER_META.COLD;

  return (
    <div className={`border ${tm.border} rounded-lg p-5 cursor-pointer group hover:border-opacity-80 transition-all`}
      onClick={() => onView(report)}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-neutral-100 group-hover:text-white transition-colors leading-snug">{report.company_name}</p>
          <p className="text-[10px] text-neutral-600 mt-0.5 truncate">{report.title}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {sc.tier  && <TierBadge tier={sc.tier} />}
          {sc.score != null && <ScoreNum value={sc.score} />}
        </div>
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-neutral-600 mb-3">
        {sc.industry  && <span>{sc.industry}</span>}
        {sc.urgency   && <span className={um.text}>{um.label}</span>}
        {sc.top_robot && <span className="text-emerald-700">▲ {sc.top_robot}</span>}
        {sc.signal_count > 0 && <span>{sc.signal_count} signals</span>}
        {sc.confidence != null && <span>{Math.round(sc.confidence * 100)}% confidence</span>}
      </div>
      {sc.pitch_angle && (
        <p className="text-xs text-neutral-500 leading-relaxed line-clamp-2 mb-2">{sc.pitch_angle}</p>
      )}
      {sc.top_signal_text && (
        <p className="text-[10px] text-neutral-700 italic line-clamp-1 mb-3">&ldquo;{sc.top_signal_text}&rdquo;</p>
      )}
      <div className="flex items-center justify-between border-t border-neutral-800 pt-3">
        <span className="text-[10px] text-neutral-700">saved {fmt(report.created_at)}</span>
        <div className="flex gap-2">
          <button onClick={e => { e.stopPropagation(); onView(report); }}
            className="text-[10px] border border-emerald-900 text-emerald-500 rounded px-2 py-0.5 hover:border-emerald-700 transition-colors">
            view report
          </button>
          <button onClick={async e => { e.stopPropagation(); if (!confirm(`Delete "${report.title}"?`)) return; await onDelete(report.id); }}
            className="text-[10px] border border-neutral-800 text-neutral-700 rounded px-2 py-0.5 hover:border-red-900 hover:text-red-500 transition-colors">
            delete
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const { session, loading: authLoading } = useAuth();
  const router = useRouter();

  const [reports,       setReports]       = useState([]);
  const [saved,         setSaved]         = useState([]);
  const [lists,         setLists]         = useState([]);
  const [userInfo,      setUserInfo]      = useState(null);
  const [dataLoading,   setDataLoading]   = useState(true);
  const [activeSection, setActiveSection] = useState('reports');
  const [viewReport,    setViewReport]    = useState(null);
  const [newListName,   setNewListName]   = useState('');
  const [addToListOpen, setAddToListOpen] = useState(null);
  const [dispName,      setDispName]      = useState('');
  const [savingName,    setSavingName]    = useState(false);

  // redirect if not logged in
  useEffect(() => {
    if (!authLoading && !session) router.replace('/login');
  }, [session, authLoading, router]);

  const token = session?.access_token;

  const apiFetch = useCallback(async (path, opts = {}) => {
    if (!token) throw new Error('Not authenticated');
    const res = await fetch(`${API}${path}`, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...authHeader(token), ...(opts.headers || {}) },
    });
    if (!res.ok) { const t = await res.text().catch(() => ''); throw new Error(t || res.statusText); }
    return res.json();
  }, [token]);

  const loadAll = useCallback(async () => {
    if (!token) return;
    setDataLoading(true);
    try {
      const [me, r, s, l] = await Promise.all([
        apiFetch('/api/user/me'),
        apiFetch('/api/user/reports'),
        apiFetch('/api/user/saved'),
        apiFetch('/api/user/lists'),
      ]);
      setUserInfo(me); setDispName(me.display_name || '');
      setReports(r); setSaved(s); setLists(l);
    } catch (e) { console.error('profile load:', e); }
    finally { setDataLoading(false); }
  }, [apiFetch, token]);

  useEffect(() => { if (session) loadAll(); }, [session, loadAll]);

  async function del(path)       { return apiFetch(path, { method: 'DELETE' }); }
  async function post(path, body){ return apiFetch(path, { method: 'POST', body: JSON.stringify(body) }); }

  async function handleDeleteReport(id) {
    try { await del(`/api/user/reports/${id}`); setReports(p => p.filter(r => r.id !== id)); }
    catch (e) { alert(e.message); }
  }
  async function handleUnsave(companyId) {
    try { await del(`/api/user/saved/${companyId}`); setSaved(p => p.filter(s => s.company_id !== companyId)); }
    catch (e) { alert(e.message); }
  }
  async function handleCreateList() {
    const name = newListName.trim(); if (!name) return;
    try { const nl = await post('/api/user/lists', { name }); setLists(p => [nl, ...p]); setNewListName(''); }
    catch (e) { alert(e.message); }
  }
  async function handleDeleteList(id) {
    if (!confirm('Delete this list?')) return;
    try { await del(`/api/user/lists/${id}`); setLists(p => p.filter(l => l.id !== id)); }
    catch (e) { alert(e.message); }
  }
  async function handleAddToList(listId, companyId, companyName) {
    try {
      await post(`/api/user/lists/${listId}/companies`, { company_id: companyId, company_name: companyName });
      const updated = await apiFetch('/api/user/lists');
      setLists(updated); setAddToListOpen(null);
    } catch (e) { alert(e.message); }
  }
  async function handleRemoveFromList(listId, companyId) {
    try {
      await del(`/api/user/lists/${listId}/companies/${companyId}`);
      setLists(p => p.map(l => l.id === listId
        ? { ...l, companies: l.companies.filter(c => c.company_id !== companyId), company_count: l.company_count - 1 }
        : l));
    } catch (e) { alert(e.message); }
  }
  async function handleSaveDisplayName() {
    setSavingName(true);
    try {
      await apiFetch('/api/user/me', { method: 'PUT', body: JSON.stringify({ display_name: dispName }) });
      setUserInfo(p => ({ ...p, display_name: dispName }));
    } catch (e) { alert(e.message); }
    setSavingName(false);
  }
  async function handleSignOut() { await supabase.auth.signOut(); router.replace('/login'); }

  function exportTSV(rows, filename) {
    const header = ['Company', 'Industry', 'Tier', 'Score', 'Website', 'Date'];
    const body   = rows.map(r => [r.company_name, r.industry, r.tier, r.score ?? '', r.website ?? '', fmt(r.saved_at || r.added_at)].join('\t'));
    const blob   = new Blob([[header.join('\t'), ...body].join('\n')], { type: 'text/plain' });
    const a      = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click();
  }

  if (authLoading || (!session && typeof window !== 'undefined')) {
    return <div className="min-h-screen bg-[#080808]" />;
  }

  const SECTIONS = [
    { key: 'reports',  label: `Reports (${reports.length})`  },
    { key: 'saved',    label: `Saved (${saved.length})`      },
    { key: 'lists',    label: `Lists (${lists.length})`      },
    { key: 'settings', label: 'Settings'                     },
  ];

  return (
    <>
      {viewReport && <ReportModal report={viewReport} onClose={() => setViewReport(null)} />}

      <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1400px] mx-auto">

        <header className="mb-8 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {userInfo?.display_name || userInfo?.email?.split('@')[0] || 'My Profile'}
              </h1>
              <span className="label border border-neutral-700 rounded px-2 py-0.5 text-neutral-400">Richtech Robotics</span>
            </div>
            <p className="text-xs text-neutral-600">{userInfo?.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/" className="btn-ghost text-xs border-neutral-700 text-neutral-500 hover:border-neutral-500">← dashboard</Link>
            <button onClick={handleSignOut} className="btn-ghost text-xs border-neutral-800 text-neutral-600 hover:border-red-900 hover:text-red-500">sign out</button>
          </div>
        </header>

        {/* section tabs */}
        <div className="flex border-b border-neutral-800 mb-8">
          {SECTIONS.map(s => (
            <button key={s.key} onClick={() => setActiveSection(s.key)}
              className={`px-4 py-2.5 text-xs font-medium transition-colors border-b-2 -mb-px ${
                activeSection === s.key ? 'border-emerald-600 text-emerald-400' : 'border-transparent text-neutral-600 hover:text-neutral-400'
              }`}>{s.label}</button>
          ))}
        </div>

        {dataLoading ? (
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => <div key={i} className="animate-pulse h-10 bg-neutral-900/60 rounded" />)}
          </div>
        ) : (
          <>
            {/* ── Reports ── */}
            {activeSection === 'reports' && (
              <section>
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className="text-sm font-semibold text-neutral-100">AI Analytics Reports</h2>
                    <p className="text-xs text-neutral-600 mt-0.5">Saved full-analysis snapshots — click AI Analysis on any lead → Save Report</p>
                  </div>
                  {reports.length > 0 && <span className="label">{reports.length} report{reports.length !== 1 ? 's' : ''}</span>}
                </div>
                {reports.length === 0
                  ? <Empty text="No reports saved. Open a lead → AI Analysis → click Save Report." />
                  : <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {reports.map(r => <ReportCard key={r.id} report={r} onDelete={handleDeleteReport} onView={setViewReport} />)}
                    </div>}
              </section>
            )}

            {/* ── Saved Companies ── */}
            {activeSection === 'saved' && (
              <section>
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className="text-sm font-semibold text-neutral-100">Saved Companies</h2>
                    <p className="text-xs text-neutral-600 mt-0.5">Flagged from the dashboard</p>
                  </div>
                  {saved.length > 0 && (
                    <button onClick={() => exportTSV(saved, 'richtech_saved.tsv')} className="btn-ghost text-xs border-neutral-800 text-neutral-600">↓ export TSV</button>
                  )}
                </div>
                {saved.length === 0
                  ? <Empty text="No companies saved. Use the ☆ save button on any lead." />
                  : <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {saved.map(c => {
                        const tm = TIER_META[c.tier] || TIER_META.COLD;
                        return (
                          <div key={c.company_id} className={`border ${tm.border} rounded-lg p-4 space-y-3`}>
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-neutral-100 truncate">{c.company_name}</p>
                                <p className="text-xs text-neutral-500 mt-0.5">{c.industry || '—'}</p>
                              </div>
                              <div className="flex items-center gap-1.5 shrink-0">
                                <TierBadge tier={c.tier} />
                                {c.score != null && <ScoreNum value={c.score} />}
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-neutral-600">
                              <span>saved {fmt(c.saved_at)}</span>
                              {c.website && (
                                <><span>·</span><a href={c.website} target="_blank" rel="noreferrer" className="text-cyan-800 hover:text-cyan-500 truncate max-w-[9rem]">{c.website.replace(/^https?:\/\//, '')}</a></>
                              )}
                            </div>
                            <div className="flex gap-2">
                              <a href={`/?analyze=${c.company_id}`} className="flex-1 text-center text-xs border border-emerald-900 text-emerald-400 rounded px-2 py-1.5 hover:border-emerald-700 transition-colors">▲ AI Analysis</a>
                              <button onClick={() => handleUnsave(c.company_id)} className="text-xs border border-neutral-800 text-neutral-600 rounded px-2 py-1.5 hover:border-red-900 hover:text-red-500 transition-colors">remove</button>
                            </div>
                            {lists.length > 0 && (
                              <div className="relative">
                                <button onClick={() => setAddToListOpen(addToListOpen === c.company_id ? null : c.company_id)}
                                  className="w-full text-[10px] border border-neutral-800 text-neutral-600 rounded px-2 py-1 hover:border-neutral-700 transition-colors">+ add to list</button>
                                {addToListOpen === c.company_id && (
                                  <div className="absolute z-10 top-full left-0 mt-1 w-full bg-[#111] border border-neutral-700 rounded shadow-xl">
                                    {lists.map(l => {
                                      const inList = l.companies?.some(lc => lc.company_id === c.company_id);
                                      return (
                                        <button key={l.id} onClick={() => !inList && handleAddToList(l.id, c.company_id, c.company_name)}
                                          className={`block w-full text-left px-3 py-2 text-xs transition-colors ${inList ? 'text-neutral-700 cursor-default' : 'text-neutral-300 hover:bg-neutral-800'}`}>
                                          {l.name} {inList ? '✓' : ''}
                                        </button>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>}
              </section>
            )}

            {/* ── Lists ── */}
            {activeSection === 'lists' && (
              <section>
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <h2 className="text-sm font-semibold text-neutral-100">Target Lists</h2>
                    <p className="text-xs text-neutral-600 mt-0.5">Group companies into outreach campaigns</p>
                  </div>
                </div>
                <div className="flex gap-2 mb-6 max-w-sm">
                  <input type="text" value={newListName} onChange={e => setNewListName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleCreateList()}
                    placeholder="New list name..."
                    className="flex-1 bg-transparent border border-neutral-700 rounded px-3 py-1.5 text-xs text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-neutral-500 transition-colors" />
                  <button onClick={handleCreateList} disabled={!newListName.trim()}
                    className="border border-emerald-900 text-emerald-400 rounded px-3 py-1.5 text-xs disabled:opacity-30 hover:border-emerald-700 transition-colors">+ create</button>
                </div>
                {lists.length === 0 ? <Empty text="No lists yet. Create one above." /> : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {lists.map(l => (
                      <div key={l.id} className="border border-neutral-800 rounded-lg">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800">
                          <div>
                            <p className="text-sm font-medium text-neutral-200">{l.name}</p>
                            <p className="text-[10px] text-neutral-600 mt-0.5">{l.company_count} companies · {fmt(l.created_at)}</p>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => exportTSV(l.companies || [], `${l.name.replace(/\s+/g, '_')}.tsv`)}
                              className="text-[10px] border border-neutral-800 text-neutral-600 rounded px-2 py-1 hover:border-neutral-600 transition-colors">↓</button>
                            <button onClick={() => handleDeleteList(l.id)}
                              className="text-[10px] border border-neutral-800 text-neutral-700 rounded px-2 py-1 hover:border-red-900 hover:text-red-500 transition-colors">delete</button>
                          </div>
                        </div>
                        {!(l.companies || []).length
                          ? <p className="text-xs text-neutral-700 px-4 py-3">Empty — use "add to list" on saved companies.</p>
                          : <div className="p-3 space-y-1.5">
                              {l.companies.map(c => {
                                const match = saved.find(s => s.company_id === c.company_id);
                                return (
                                  <div key={c.company_id} className="flex items-center justify-between border border-neutral-800 rounded px-3 py-2">
                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                      {match?.tier && <TierBadge tier={match.tier} />}
                                      <span className="text-xs text-neutral-300 truncate">{c.company_name}</span>
                                      {match?.score != null && <ScoreNum value={match.score} />}
                                    </div>
                                    <div className="flex gap-2 shrink-0 ml-2">
                                      <a href={`/?analyze=${c.company_id}`} className="text-[10px] border border-emerald-900 text-emerald-500 rounded px-1.5 py-0.5 hover:border-emerald-700 transition-colors">▲</a>
                                      <button onClick={() => handleRemoveFromList(l.id, c.company_id)} className="text-[10px] border border-neutral-800 text-neutral-600 rounded px-1.5 py-0.5 hover:border-red-900 hover:text-red-500 transition-colors">✕</button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* ── Settings ── */}
            {activeSection === 'settings' && (
              <section className="max-w-sm space-y-6">
                <div>
                  <h2 className="text-sm font-semibold text-neutral-100 mb-4">Account</h2>
                  <div className="space-y-3">
                    <div>
                      <p className="label mb-1">email</p>
                      <p className="text-xs text-neutral-400 border border-neutral-800 rounded px-3 py-2">{userInfo?.email}</p>
                    </div>
                    <div>
                      <p className="label mb-1">display name</p>
                      <div className="flex gap-2">
                        <input type="text" value={dispName} onChange={e => setDispName(e.target.value)} placeholder="Your name"
                          className="flex-1 bg-transparent border border-neutral-700 rounded px-3 py-1.5 text-xs text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-neutral-500 transition-colors" />
                        <button onClick={handleSaveDisplayName} disabled={savingName}
                          className="border border-emerald-900 text-emerald-400 rounded px-3 py-1.5 text-xs disabled:opacity-40 hover:border-emerald-700 transition-colors">{savingName ? '…' : 'save'}</button>
                      </div>
                    </div>
                    <div>
                      <p className="label mb-1">member since</p>
                      <p className="text-xs text-neutral-600">{fmt(userInfo?.created_at)}</p>
                    </div>
                  </div>
                </div>
                <div className="border-t border-neutral-800 pt-5">
                  <button onClick={handleSignOut} className="border border-red-900 text-red-500 rounded px-4 py-2 text-xs hover:border-red-700 transition-colors">Sign out</button>
                </div>
              </section>
            )}
          </>
        )}

        <footer className="mt-16 text-center text-[10px] text-neutral-700">
          ready for robots · richtech robotics · profile data synced to cloud
        </footer>
      </div>
    </>
  );
}
