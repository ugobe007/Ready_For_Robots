import { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import RrSiteLayout from '../components/RrSiteLayout';

/** Decode query param and show a clean company or host label (never raw %20). */
function displayCompanyLabel(raw) {
  if (!raw || typeof raw !== 'string') return 'your company';
  let decoded = raw;
  try {
    decoded = decodeURIComponent(raw.replace(/\+/g, ' '));
  } catch {
    decoded = raw.replace(/\+/g, ' ');
  }
  const trimmed = decoded.trim();
  if (!trimmed) return 'your company';

  const looksLikeUrl =
    /^https?:\/\//i.test(trimmed) ||
    /^www\./i.test(trimmed) ||
    (/^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}/i.test(trimmed) && !/\s/.test(trimmed));

  if (looksLikeUrl) {
    try {
      const href = trimmed.startsWith('http') ? trimmed : `https://${trimmed}`;
      const h = new URL(href).hostname.replace(/^www\./, '');
      return h || trimmed;
    } catch {
      return trimmed;
    }
  }

  return trimmed;
}

/**
 * Same ordering as GET /api/leads?sort=score (priority composite). Showing only
 * overall_intent_score can invert rows vs the displayed number — use priority first.
 */
function scoreDisplay(lead) {
  const pri = lead?.priority_score;
  if (pri != null && Number.isFinite(Number(pri))) {
    return Number(pri).toFixed(1);
  }
  if (lead?.score == null) return '—';
  if (typeof lead.score === 'object') {
    const v = lead.score.overall_score;
    if (v == null || !Number.isFinite(Number(v))) return '—';
    return Number(v).toFixed(1);
  }
  const n = Number(lead.score);
  return Number.isFinite(n) ? n.toFixed(1) : '—';
}

function formatEmployeeLine(v) {
  if (v == null || v === '') return '—';
  if (typeof v === 'number' && Number.isFinite(v)) return String(v);
  if (typeof v === 'string') return v;
  if (typeof v === 'object') {
    try {
      return JSON.stringify(v);
    } catch {
      return '—';
    }
  }
  return String(v);
}

/** API signals use `raw_text`; some clients use `description` or `signal_text`. */
function signalInlineBody(sig) {
  if (!sig || typeof sig !== 'object') return '';
  const raw = sig.description ?? sig.raw_text ?? sig.signal_text ?? '';
  const s = String(raw).replace(/\s+/g, ' ').trim();
  if (!s) return '';
  return s.replace(/<[^>]+>/g, '').trim();
}

/** Supabase-style: monospace key · inline description (no chips). */
function SignalInlineRows({ signals }) {
  const rows = (signals || []).filter((s) => s != null && typeof s === 'object').slice(0, 5);
  if (rows.length === 0) {
    return (
      <p className="text-[13px] leading-snug text-neutral-500">
        <span className="font-mono text-[12px] text-neutral-600">signal</span>
        <span className="text-neutral-600"> · </span>
        <span className="text-neutral-500">Intent signals will appear here on the full dashboard.</span>
      </p>
    );
  }
  return (
    <div className="space-y-1">
      {rows.map((sig, i) => {
        const key = sig.signal_type || 'signal';
        const label = String(key).replace(/_/g, ' ');
        const body = signalInlineBody(sig);
        return (
          <p key={i} className="text-[13px] leading-snug text-neutral-300">
            <span className="font-mono text-[12px] text-neutral-500">{label}</span>
            {body ? (
              <>
                <span className="text-neutral-600"> · </span>
                <span className="text-neutral-400">{body}</span>
              </>
            ) : null}
          </p>
        );
      })}
    </div>
  );
}

export default function PipelineResults() {
  const router = useRouter();
  const { url } = router.query;
  const urlStr = Array.isArray(url) ? url[0] : url;

  const company = useMemo(() => displayCompanyLabel(urlStr), [urlStr]);
  const [loading, setLoading] = useState(true);
  const [matches, setMatches] = useState([]);
  const [expandedKey, setExpandedKey] = useState(null);
  const [savedIds, setSavedIds] = useState(() => new Set());

  useEffect(() => {
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
      setSavedIds(new Set((store.companies || []).map((c) => c.id)));
    } catch {
      setSavedIds(new Set());
    }
  }, []);

  const fetchMatches = useCallback(async () => {
    if (!urlStr) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${getApiBase()}/api/leads?limit=6&tier=HOT&sort=score`,
        liveFetchInit()
      );
      const data = await res.json();
      setMatches(Array.isArray(data) ? data.slice(0, 6) : []);
    } catch (err) {
      console.error('Error fetching matches:', err);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  }, [urlStr]);

  useEffect(() => {
    if (!urlStr) return;
    fetchMatches();
  }, [urlStr, fetchMatches]);

  const toggleSave = useCallback((lead) => {
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[],"lists":[]}');
      if (!store.companies) store.companies = [];
      const id = lead.id;
      if (id == null) return;
      const already = store.companies.some((c) => c.id === id);
      if (already) {
        store.companies = store.companies.filter((c) => c.id !== id);
      } else {
        store.companies.push({
          id,
          name: lead.company_name,
          industry: lead.industry,
          score: lead.priority_score ?? lead.score?.overall_score ?? lead.score ?? 0,
          tier: lead.priority_tier,
          saved_at: new Date().toISOString(),
          website: lead.website,
        });
      }
      localStorage.setItem('rfr_saved', JSON.stringify(store));
      setSavedIds(new Set(store.companies.map((c) => c.id)));
    } catch {
      /* ignore */
    }
  }, []);

  const getEngagementStrategy = () => {
    if (!url) return [];

    return [
      {
        phase: 'Week 1-2: Awareness & Education',
        tactics: [
          'Share case study on automation ROI in their industry',
          'Comment on LinkedIn posts about labor challenges',
          'Send thought leadership article on workforce trends',
        ],
      },
      {
        phase: 'Week 3-4: Problem Agitation',
        tactics: [
          'Share industry benchmark data showing automation adoption',
          'Invite to webinar on solving labor shortages',
          'Send calculator tool for automation cost savings',
        ],
      },
      {
        phase: 'Week 5-6: Solution Introduction',
        tactics: [
          'Request 15-min intro call to discuss their challenges',
          'Share video demo of robot solving similar use case',
          'Offer pilot program assessment (limited slots)',
        ],
      },
      {
        phase: 'Week 7-8: Social Proof & Close',
        tactics: [
          'Introduce customer reference in their industry',
          'Share implementation timeline and ROI projections',
          'Propose pilot program with defined success metrics',
        ],
      },
    ];
  };

  const innerNoUrl = (
    <div className="flex-1 flex items-center justify-center px-4 py-20">
      <div className="text-center max-w-md">
        <p className="text-neutral-500 text-sm mb-4">No company URL or name provided.</p>
        <Link href="/">
          <button
            type="button"
            className="px-4 py-2 border border-emerald-700 text-emerald-400 rounded-lg hover:bg-emerald-900/20 text-sm"
          >
            Back to home
          </button>
        </Link>
      </div>
    </div>
  );

  if (!router.isReady) {
    return (
      <RrSiteLayout active="pipeline">
        <div className="flex-1 flex items-center justify-center min-h-[50vh] bg-neutral-950">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-emerald-500/30 border-t-emerald-400" />
        </div>
      </RrSiteLayout>
    );
  }

  if (!url) {
    return (
      <RrSiteLayout active="pipeline">
        <Head>
          <title>Pipeline preview | Ready For Robots</title>
        </Head>
        {innerNoUrl}
      </RrSiteLayout>
    );
  }

  return (
    <RrSiteLayout active="pipeline">
      <Head>
        <title>Build Your Automation Pipeline — {company} | Ready For Robots</title>
      </Head>

      <div className="min-h-0 flex-1 bg-neutral-950 text-neutral-300">
        <div className="border-b border-neutral-800/90">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-9">
            <p className="font-mono text-[11px] uppercase tracking-wide text-neutral-500 mb-1">
              Pipeline preview
            </p>
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-neutral-100 mb-2">
              Build Your Automation Pipeline
            </h1>
            <p className="text-neutral-400 text-sm sm:text-base max-w-2xl leading-snug">
              Automation Projects that Match{' '}
              <span className="font-mono text-neutral-300">{company}</span> with Targeted PoCs.
            </p>
            <div className="mt-4 max-w-3xl border-l-2 border-emerald-700/45 pl-3">
              <p className="font-mono text-[11px] uppercase tracking-wide text-neutral-500 mb-1.5">
                How this pipeline works
              </p>
              <div className="space-y-2 text-sm text-neutral-300 leading-relaxed">
                <p>
                  <span className="text-neutral-200">Review</span> the rows below — use{' '}
                  <span className="text-neutral-200">Review</span> / <span className="text-neutral-200">Save to CRM</span>{' '}
                  as text actions (not the full dashboard). Signals show as{' '}
                  <span className="font-mono text-[12px] text-neutral-500">type · description</span> inline.
                </p>
                <p className="text-neutral-400 text-[13px]">
                  Signal intelligence surfaces intent, timing, and needs. Continue on the{' '}
                  <Link href="/dashboard" className="text-emerald-400/95 underline decoration-emerald-700/50 underline-offset-2 hover:text-emerald-300">
                    pipeline
                  </Link>{' '}
                  or{' '}
                  <Link href="/crm/" className="text-emerald-400/95 underline decoration-emerald-700/50 underline-offset-2 hover:text-emerald-300">
                    CRM
                  </Link>{' '}
                  for depth.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
          {loading ? (
            <div className="border-t border-neutral-800/90 py-10 text-center">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-neutral-700 border-t-emerald-500/80" />
              <p className="mt-3 text-[13px] text-neutral-500">Loading HOT matches for {company}…</p>
            </div>
          ) : (
            <>
              <div className="mb-10">
                <div className="mb-3 border-b border-neutral-800/90 pb-2">
                  <h2 className="font-mono text-[11px] uppercase tracking-wide text-neutral-500">
                    Prospect preview
                  </h2>
                  <p className="mt-1 text-[13px] text-neutral-500">
                    Flat rows — full lead UI lives on the dashboard.{' '}
                    <span className="font-mono text-[11px] text-neutral-600">score</span> is tabular; signals are inline text.
                  </p>
                </div>
                {matches.length === 0 ? (
                  <p className="text-[13px] text-neutral-500">
                    No matches right now.{' '}
                    <Link
                      href="/dashboard"
                      className="text-emerald-400/95 underline decoration-emerald-800 underline-offset-2 hover:text-emerald-300"
                    >
                      Open dashboard
                    </Link>
                  </p>
                ) : (
                  <div className="divide-y divide-neutral-800/90 border-t border-neutral-800/90">
                    {matches.map((lead, rowIndex) => {
                      if (lead == null || typeof lead !== 'object') return null;
                      const key =
                        lead.id != null ? String(lead.id) : `row-${rowIndex}`;
                      const open = expandedKey === key;
                      const canSave = lead.id != null;
                      const saved = canSave && savedIds.has(lead.id);
                      const signals = Array.isArray(lead.signals) ? lead.signals : [];
                      const topSig = signals[0];
                      const intentLabel = String(
                        topSig?.signal_type || 'AUTOMATION_INTENT',
                      ).replace(/_/g, ' ');
                      return (
                        <div key={key} className="py-3 first:pt-0">
                          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                            <div className="min-w-0">
                              <span className="text-[15px] font-medium text-neutral-100">
                                {lead.company_name || 'Company'}
                              </span>
                              <span className="text-neutral-600"> · </span>
                              <span className="text-[13px] text-neutral-500">
                                {lead.industry || '—'} · {formatEmployeeLine(lead.employee_estimate)} employees
                              </span>
                            </div>
                            <span className="font-mono text-[12px] tabular-nums text-orange-400/90">
                              score {scoreDisplay(lead)}
                            </span>
                          </div>

                          <div className="mt-2">
                            <SignalInlineRows signals={signals} />
                          </div>

                          {open && (
                            <div className="mt-2 border-l border-neutral-700 pl-2 text-[13px] leading-snug text-neutral-400 space-y-1">
                              <p>
                                <span className="font-mono text-[11px] text-neutral-500">intent</span>
                                <span className="text-neutral-600"> · </span>
                                Aligns with {intentLabel.toLowerCase()}; confirm on outreach.
                              </p>
                              <p>
                                <span className="font-mono text-[11px] text-neutral-500">timing</span>
                                <span className="text-neutral-600"> · </span>
                                From recent signal activity — see dashboard for dates.
                              </p>
                              <p>
                                <span className="font-mono text-[11px] text-neutral-500">needs</span>
                                <span className="text-neutral-600"> · </span>
                                Robotics / automation fit in {lead.industry || 'this segment'}; validate in discovery.
                              </p>
                            </div>
                          )}

                          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-0 text-[13px]">
                            <button
                              type="button"
                              onClick={() => setExpandedKey(open ? null : key)}
                              className="border-0 bg-transparent p-0 text-emerald-400/95 underline decoration-emerald-800 underline-offset-2 hover:text-emerald-300 cursor-pointer"
                            >
                              {open ? 'Hide review' : 'Review'}
                            </button>
                            {canSave && (
                              <button
                                type="button"
                                onClick={() => toggleSave(lead)}
                                className={`border-0 bg-transparent p-0 underline underline-offset-2 cursor-pointer ${
                                  saved ? 'text-amber-400/90 decoration-amber-900' : 'text-neutral-500 decoration-neutral-700 hover:text-emerald-400/90 hover:decoration-emerald-900'
                                }`}
                              >
                                {saved ? 'Saved to CRM' : 'Save to CRM'}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="mb-10 border-t border-neutral-800/90 pt-6">
                <h2 className="font-mono text-[11px] uppercase tracking-wide text-neutral-500 mb-4">
                  8-week engagement strategy
                </h2>
                <div className="space-y-5">
                  {getEngagementStrategy().map((phase, idx) => (
                    <div key={idx} className="border-l border-neutral-800 pl-3">
                      <h3 className="text-[13px] font-medium text-neutral-200">{phase.phase}</h3>
                      <ul className="mt-2 space-y-1 text-[13px] text-neutral-400 leading-snug">
                        {phase.tactics.map((tactic, i) => (
                          <li key={i} className="pl-0">
                            <span className="text-neutral-600">· </span>
                            {tactic}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-neutral-800/90 pt-6">
                <p className="text-[13px] text-neutral-500 text-center max-w-md mx-auto">
                  Want cloud save, CRM sync, and the full workspace? Sign in — or open the dashboard to continue.
                </p>
                <p className="mt-3 text-center text-[13px] text-neutral-400">
                  <Link
                    href="/login"
                    className="text-emerald-400/95 underline decoration-emerald-800 underline-offset-2 hover:text-emerald-300"
                  >
                    Sign up
                  </Link>
                  <span className="text-neutral-600"> · </span>
                  <Link
                    href="/dashboard"
                    className="text-neutral-400 underline decoration-neutral-700 underline-offset-2 hover:text-neutral-200"
                  >
                    Open dashboard
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </RrSiteLayout>
  );
}
