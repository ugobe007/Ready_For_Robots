/**
 * CRM workspace — teams + accounts (FastAPI /api/crm/*).
 * Requires sign-in; sends Authorization: Bearer access_token on every request.
 */
import { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from './_app';
import { authHeader } from '../lib/supabase';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import RrSiteLayout from '../components/RrSiteLayout';
import { SignalScoreBadge, LeadValueBadge, PipelineScoreLegend } from '../lib/signalScoreBadge';

function tierTextClass(tier) {
  if (!tier) return 'text-neutral-500';
  const u = String(tier).toUpperCase();
  if (u === 'HOT') return 'text-red-400 font-semibold';
  if (u === 'WARM') return 'text-amber-400 font-medium';
  return 'text-cyan-400';
}

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

/** Readable message from failed API response (handles generic 500 HTML/text). */
function parseApiError(status, text) {
  let detail = text;
  try {
    const j = JSON.parse(text);
    if (j.detail != null) detail = j.detail;
  } catch {
    /* keep raw */
  }
  if (typeof detail !== 'string') detail = JSON.stringify(detail);
  if (status >= 500 && /internal server error/i.test(detail)) {
    return 'Server error — run CRM migration c7d8e9f0a1b2 on your database (see docs/crm_migrations.md), redeploy if needed, then reload.';
  }
  return detail;
}

export default function CrmPage() {
  const router = useRouter();
  const { session, loading: authLoading } = useAuth();
  const API = getApiBase();

  // Static export uses trailingSlash; some CDNs serve `/` (home) for `/crm` without the slash.
  useEffect(() => {
    if (!router.isReady) return;
    const pathOnly = router.asPath.split('?')[0];
    const query = router.asPath.includes('?') ? `?${router.asPath.split('?')[1]}` : '';
    if (pathOnly === '/crm') {
      router.replace(`/crm/${query}`, undefined, { shallow: true });
    }
  }, [router.isReady, router.asPath, router]);

  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState('');
  const [accounts, setAccounts] = useState([]);
  const [loadingTeams, setLoadingTeams] = useState(true);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [err, setErr] = useState('');

  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamSlug, setNewTeamSlug] = useState('');
  const [creatingTeam, setCreatingTeam] = useState(false);

  const [acctName, setAcctName] = useState('');
  const [acctWebsite, setAcctWebsite] = useState('');
  const [acctIndustry, setAcctIndustry] = useState('');
  const [acctCompanyId, setAcctCompanyId] = useState('');
  const [companyPreview, setCompanyPreview] = useState(null);
  const [creatingAcct, setCreatingAcct] = useState(false);

  const authFetch = useCallback(
    (path, opts = {}) => {
      if (!session?.access_token) {
        return Promise.reject(new Error('Not signed in'));
      }
      return fetch(`${API}${path}`, liveFetchInit({
        ...opts,
        headers: {
          ...authHeader(session.access_token),
          ...(opts.headers || {}),
        },
      }));
    },
    [API, session?.access_token]
  );

  const loadTeams = useCallback(async () => {
    setErr('');
    setLoadingTeams(true);
    try {
      const r = await authFetch('/api/crm/teams');
      const text = await r.text();
      if (!r.ok) {
        throw new Error(parseApiError(r.status, text));
      }
      const data = JSON.parse(text);
      const list = Array.isArray(data) ? data : [];
      setTeams(list);
      return list;
    } catch (e) {
      setErr(e.message || 'Failed to load teams');
      setTeams([]);
      return [];
    } finally {
      setLoadingTeams(false);
    }
  }, [authFetch]);

  const loadAccounts = useCallback(
    async (tid) => {
      if (!tid) {
        setAccounts([]);
        return;
      }
      setLoadingAccounts(true);
      setErr('');
      try {
        const q = `team_id=${encodeURIComponent(tid)}`;
        const r = await authFetch(`/api/crm/accounts?${q}`);
        const text = await r.text();
        if (!r.ok) {
          throw new Error(parseApiError(r.status, text));
        }
        const data = JSON.parse(text);
        setAccounts(Array.isArray(data) ? data : []);
      } catch (e) {
        setErr(e.message || 'Failed to load accounts');
        setAccounts([]);
      } finally {
        setLoadingAccounts(false);
      }
    },
    [authFetch]
  );

  useEffect(() => {
    if (authLoading) return;
    if (!session) {
      router.replace('/login');
      return;
    }
    let cancelled = false;
    loadTeams().then((list) => {
      if (cancelled) return;
      const arr = Array.isArray(list) ? list : [];
      setTeamId((prev) => prev || (arr[0]?.id ?? ''));
    });
    return () => {
      cancelled = true;
    };
  }, [authLoading, session, router, loadTeams]);

  useEffect(() => {
    if (!teamId || !session) return;
    loadAccounts(teamId);
  }, [teamId, session, loadAccounts]);

  useEffect(() => {
    const raw = acctCompanyId.trim();
    if (!raw || !Number.isFinite(Number(raw))) {
      setCompanyPreview(null);
      return;
    }
    const id = Number(raw);
    const t = setTimeout(() => {
      fetch(`${API}/api/companies/${id}`)
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => setCompanyPreview(d))
        .catch(() => setCompanyPreview(null));
    }, 400);
    return () => clearTimeout(t);
  }, [acctCompanyId, API]);

  async function handleCreateTeam(e) {
    e.preventDefault();
    const name = newTeamName.trim();
    if (!name) return;
    setCreatingTeam(true);
    setErr('');
    try {
      const body = { name };
      const slug = newTeamSlug.trim();
      if (slug) body.slug = slug;
      const r = await authFetch('/api/crm/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const text = await r.text();
      if (!r.ok) {
        throw new Error(parseApiError(r.status, text));
      }
      const created = JSON.parse(text);
      setNewTeamName('');
      setNewTeamSlug('');
      await loadTeams();
      if (created?.id) setTeamId(created.id);
    } catch (e) {
      setErr(e.message || 'Could not create workspace');
    } finally {
      setCreatingTeam(false);
    }
  }

  async function handleCreateAccount(e) {
    e.preventDefault();
    setCreatingAcct(true);
    setErr('');
    try {
      const body = { team_id: teamId };
      const n = acctName.trim();
      const w = acctWebsite.trim();
      const ind = acctIndustry.trim();
      const cid = acctCompanyId.trim();
      if (cid && Number.isFinite(Number(cid))) body.company_id = Number(cid);
      if (n) body.name = n;
      if (w) body.website = w;
      if (ind) body.industry = ind;
      const r = await authFetch('/api/crm/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const text = await r.text();
      if (!r.ok) {
        throw new Error(parseApiError(r.status, text));
      }
      setAcctName('');
      setAcctWebsite('');
      setAcctIndustry('');
      setAcctCompanyId('');
      setCompanyPreview(null);
      await loadAccounts(teamId);
    } catch (e) {
      setErr(e.message || 'Could not add account');
    } finally {
      setCreatingAcct(false);
    }
  }

  if (authLoading) {
    return (
      <RrSiteLayout active="crm">
        <div className="max-w-5xl mx-auto px-4 py-20 text-center text-neutral-400 text-sm">Loading…</div>
      </RrSiteLayout>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <RrSiteLayout active="crm">
      <Head>
        <title>CRM Workspace | Ready For Robots</title>
        <meta
          name="description"
          content="Manage workspaces (teams) and buyer accounts linked to your pipeline."
        />
      </Head>

      <div className="crm-workspace max-w-6xl mx-auto px-4 py-8 md:py-10">
        <div className="mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-emerald-300 tracking-tight">
              CRM workspace
            </h1>
            <p className="crm-subtitle text-sm mt-1 max-w-xl leading-relaxed">
              Workspaces group your buyer accounts. Link a database company by ID to pre-fill name and industry, or enter a prospect manually.
            </p>
          </div>
          <Link href="/dashboard" className="crm-back-link w-fit shrink-0">
            ← Back to pipeline
          </Link>
        </div>

        {err && (
          <div className="crm-alert mb-6" role="alert">
            {err}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Teams */}
          <section className="space-y-4">
            <h2 className="crm-section-label">Workspaces</h2>
            {loadingTeams ? (
              <p className="text-sm text-slate-300">Loading workspaces…</p>
            ) : (
              <div className="crm-panel overflow-hidden">
                <ul className="divide-y divide-neutral-700">
                  {teams.map((t) => (
                    <li key={t.id}>
                      <button
                        type="button"
                        onClick={() => setTeamId(t.id)}
                        className={`w-full text-left px-4 py-3 flex items-center justify-between gap-2 transition-colors ${
                          teamId === t.id
                            ? 'bg-emerald-950/60 border-l-2 border-emerald-400'
                            : 'hover:bg-neutral-800/80'
                        }`}
                      >
                        <span className="font-medium text-neutral-100">{t.name}</span>
                        <span className="text-[10px] uppercase tracking-wide text-emerald-300 border border-emerald-700 rounded px-1.5 py-0.5">
                          {t.role}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <form onSubmit={handleCreateTeam} className="crm-panel p-4 space-y-3">
              <div className="crm-section-label">New workspace</div>
              <input
                type="text"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                placeholder="Workspace name"
                className="crm-input"
              />
              <input
                type="text"
                value={newTeamSlug}
                onChange={(e) => setNewTeamSlug(e.target.value)}
                placeholder="Optional slug (unique)"
                className="crm-input"
              />
              <button
                type="submit"
                disabled={creatingTeam || !newTeamName.trim()}
                className="crm-btn-emerald"
              >
                {creatingTeam ? 'Creating…' : 'Create workspace'}
              </button>
            </form>
          </section>

          {/* Accounts */}
          <section className="space-y-4">
            <h2 className="crm-section-label">
              Accounts{' '}
              {teamId && (
                <span className="text-slate-500 font-mono text-[10px] ml-2 normal-case tracking-normal">
                  {teamId.slice(0, 8)}…
                </span>
              )}
            </h2>

            <form onSubmit={handleCreateAccount} className="crm-panel p-4 space-y-3">
              <div className="crm-section-label">Add account</div>
              <input
                type="text"
                inputMode="numeric"
                value={acctCompanyId}
                onChange={(e) => setAcctCompanyId(e.target.value)}
                placeholder="Link company ID (optional — from pipeline DB)"
                className="crm-input"
              />
              {companyPreview && (
                <div className="text-xs text-emerald-200 border border-emerald-700/60 rounded-md px-3 py-2 bg-emerald-950/40">
                  {companyPreview.name}
                  {companyPreview.industry ? ` · ${companyPreview.industry}` : ''}
                </div>
              )}
              <input
                type="text"
                value={acctName}
                onChange={(e) => setAcctName(e.target.value)}
                placeholder="Account name (required if no company ID)"
                className="crm-input"
              />
              <input
                type="text"
                value={acctWebsite}
                onChange={(e) => setAcctWebsite(e.target.value)}
                placeholder="Website"
                className="crm-input"
              />
              <input
                type="text"
                value={acctIndustry}
                onChange={(e) => setAcctIndustry(e.target.value)}
                placeholder="Industry"
                className="crm-input"
              />
              <button type="submit" disabled={creatingAcct || !teamId} className="crm-btn-cyan">
                {creatingAcct ? 'Saving…' : 'Add to workspace'}
              </button>
            </form>

            <PipelineScoreLegend showTier className="mb-3" />

            <div className="crm-panel overflow-hidden min-h-[120px]">
              {loadingAccounts ? (
                <p className="p-4 text-sm text-slate-300">Loading accounts…</p>
              ) : accounts.length === 0 ? (
                <p className="p-4 text-sm text-slate-300">No accounts in this workspace yet.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-700 text-left text-[10px] uppercase tracking-widest text-neutral-400">
                      <th className="px-3 py-2 font-medium">Name</th>
                      <th className="px-3 py-2 font-medium text-right">Signal</th>
                      <th className="px-3 py-2 font-medium text-right">Value</th>
                      <th className="px-3 py-2 font-medium">Tier</th>
                      <th className="px-3 py-2 font-medium">Company</th>
                      <th className="px-3 py-2 font-medium">Industry</th>
                      <th className="px-3 py-2 font-medium">Added</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((a) => (
                      <tr key={a.id} className="border-b border-neutral-800/60 hover:bg-neutral-900/50">
                        <td className="px-3 py-2 text-neutral-100">{a.name}</td>
                        <td className="px-3 py-2 text-right">
                          {a.signal_score != null ? (
                            <SignalScoreBadge value={a.signal_score} />
                          ) : (
                            <span className="text-neutral-600 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {a.lead_value_score != null ? (
                            <LeadValueBadge value={a.lead_value_score} />
                          ) : (
                            <span className="text-neutral-600 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          {a.pipeline_priority_tier ? (
                            <span className={tierTextClass(a.pipeline_priority_tier)}>
                              {String(a.pipeline_priority_tier).toUpperCase()}
                            </span>
                          ) : (
                            <span className="text-neutral-600">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-neutral-400 tabular-nums">
                          {a.company_id != null ? (
                            <span className="text-cyan-400 tabular-nums">#{a.company_id}</span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="px-3 py-2 text-neutral-300">{a.industry || '—'}</td>
                        <td className="px-3 py-2 text-neutral-400 text-xs">{fmtDate(a.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        </div>
      </div>
    </RrSiteLayout>
  );
}
