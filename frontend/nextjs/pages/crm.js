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
        let detail = text;
        try {
          detail = JSON.parse(text).detail || text;
        } catch {
          /* raw */
        }
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
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
          let detail = text;
          try {
            detail = JSON.parse(text).detail || text;
          } catch {
            /* raw */
          }
          throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
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
        let detail = text;
        try {
          detail = JSON.parse(text).detail || text;
        } catch {
          /* raw */
        }
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
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
        let detail = text;
        try {
          detail = JSON.parse(text).detail || text;
        } catch {
          /* raw */
        }
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
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

      <div className="max-w-6xl mx-auto px-4 py-8 md:py-10 text-neutral-200">
        <div className="mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-emerald-300 tracking-tight">
              CRM workspace
            </h1>
            <p className="text-sm text-neutral-300 mt-1 max-w-xl leading-relaxed">
              Workspaces group your buyer accounts. Link a database company by ID to pre-fill name and industry, or enter a prospect manually.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-cyan-300 hover:text-cyan-200 border border-neutral-600 rounded-md px-4 py-2 w-fit bg-neutral-900/60"
          >
            ← Back to pipeline
          </Link>
        </div>

        {err && (
          <div
            className="mb-6 border border-red-500/60 bg-red-950/70 text-red-100 text-sm px-4 py-3 rounded-md"
            role="alert"
          >
            {err}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Teams */}
          <section className="space-y-4">
            <h2 className="text-xs uppercase tracking-widest text-neutral-400">Workspaces</h2>
            {loadingTeams ? (
              <p className="text-sm text-neutral-400">Loading workspaces…</p>
            ) : (
              <div className="border border-neutral-600 rounded-lg overflow-hidden bg-neutral-950/40">
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

            <form
              onSubmit={handleCreateTeam}
              className="border border-neutral-600 rounded-lg p-4 space-y-3 bg-neutral-950/30"
            >
              <div className="text-xs uppercase tracking-widest text-neutral-400">New workspace</div>
              <input
                type="text"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                placeholder="Workspace name"
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-600/50"
              />
              <input
                type="text"
                value={newTeamSlug}
                onChange={(e) => setNewTeamSlug(e.target.value)}
                placeholder="Optional slug (unique)"
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-600/50"
              />
              <button
                type="submit"
                disabled={creatingTeam || !newTeamName.trim()}
                className="text-sm font-medium bg-emerald-700 text-white border border-emerald-600 px-4 py-2 rounded-md hover:bg-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {creatingTeam ? 'Creating…' : 'Create workspace'}
              </button>
            </form>
          </section>

          {/* Accounts */}
          <section className="space-y-4">
            <h2 className="text-xs uppercase tracking-widest text-neutral-400">
              Accounts{' '}
              {teamId && (
                <span className="text-neutral-500 font-mono text-[10px] ml-2">{teamId.slice(0, 8)}…</span>
              )}
            </h2>

            <form
              onSubmit={handleCreateAccount}
              className="border border-neutral-600 rounded-lg p-4 space-y-3 bg-neutral-950/30"
            >
              <div className="text-xs uppercase tracking-widest text-neutral-400">Add account</div>
              <input
                type="text"
                inputMode="numeric"
                value={acctCompanyId}
                onChange={(e) => setAcctCompanyId(e.target.value)}
                placeholder="Link company ID (optional — from pipeline DB)"
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-cyan-600/50"
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
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-cyan-600/50"
              />
              <input
                type="text"
                value={acctWebsite}
                onChange={(e) => setAcctWebsite(e.target.value)}
                placeholder="Website"
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-cyan-600/50"
              />
              <input
                type="text"
                value={acctIndustry}
                onChange={(e) => setAcctIndustry(e.target.value)}
                placeholder="Industry"
                className="w-full bg-neutral-900 border border-neutral-600 rounded-md px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-cyan-600/50"
              />
              <button
                type="submit"
                disabled={creatingAcct || !teamId}
                className="text-sm font-medium bg-cyan-700 text-white border border-cyan-600 px-4 py-2 rounded-md hover:bg-cyan-600 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {creatingAcct ? 'Saving…' : 'Add to workspace'}
              </button>
            </form>

            <div className="border border-neutral-600 rounded-lg overflow-hidden min-h-[120px] bg-neutral-950/40">
              {loadingAccounts ? (
                <p className="p-4 text-sm text-neutral-400">Loading accounts…</p>
              ) : accounts.length === 0 ? (
                <p className="p-4 text-sm text-neutral-400">No accounts in this workspace yet.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-700 text-left text-[10px] uppercase tracking-widest text-neutral-400">
                      <th className="px-3 py-2 font-medium">Name</th>
                      <th className="px-3 py-2 font-medium">Company</th>
                      <th className="px-3 py-2 font-medium">Industry</th>
                      <th className="px-3 py-2 font-medium">Added</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((a) => (
                      <tr key={a.id} className="border-b border-neutral-800/60 hover:bg-neutral-900/50">
                        <td className="px-3 py-2 text-neutral-100">{a.name}</td>
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
