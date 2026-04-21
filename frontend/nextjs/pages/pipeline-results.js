import { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import RrSiteLayout from '../components/RrSiteLayout';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { companyExternalHref } from '../lib/companyExternalHref';
import { COMPANY_NAME_LINK_CLASS } from '../lib/companyNameLinkClass';
import { AutomationSpecBlock } from '../lib/automationProfile';
import { PlainTextWithSourceLinks } from '../lib/plainText';

function formatSignalTypeLabel(t) {
  if (!t) return '';
  return String(t).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatUrlSignalWeights(weights) {
  if (!weights || typeof weights !== 'object') return '';
  return Object.entries(weights)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([k, v]) => `${formatSignalTypeLabel(k)} ${v}`)
    .join(' · ');
}

function displayHost(raw) {
  if (!raw || typeof raw !== 'string') return 'your company';
  try {
    const s = decodeURIComponent(raw);
    const href = s.startsWith('http://') || s.startsWith('https://') ? s : `https://${s}`;
    const h = new URL(href).hostname;
    return h || raw;
  } catch {
    return raw;
  }
}

// ── Signal badge ─────────────────────────────────────────────────────────────
const SIGNAL_META = {
  funding_round:     { label: 'FUNDING',    bg: 'bg-green-900/30',   border: 'border-green-700',   text: 'text-green-400' },
  expansion:         { label: 'EXPANSION',  bg: 'bg-purple-900/30',  border: 'border-purple-700',  text: 'text-purple-400' },
  capex:             { label: 'CAPEX',      bg: 'bg-purple-900/30',  border: 'border-purple-700',  text: 'text-purple-400' },
  labor_shortage:    { label: 'LABOR GAP',  bg: 'bg-red-900/30',     border: 'border-red-700',     text: 'text-red-400' },
  job_posting:       { label: 'HIRING',     bg: 'bg-yellow-900/30',  border: 'border-yellow-700',  text: 'text-yellow-400' },
  strategic_hire:    { label: 'EXEC HIRE',  bg: 'bg-cyan-900/30',    border: 'border-cyan-700',    text: 'text-cyan-400' },
  ma_activity:       { label: 'M&A',        bg: 'bg-pink-900/30',    border: 'border-pink-700',    text: 'text-pink-400' },
  news:              { label: 'NEWS',       bg: 'bg-blue-900/30',    border: 'border-blue-700',    text: 'text-blue-400' },
};

function SignalBadge({ type }) {
  const meta = SIGNAL_META[type] || {
    label: (type || 'SIGNAL').toUpperCase(),
    bg: 'bg-neutral-900/30', border: 'border-neutral-700', text: 'text-neutral-400',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-bold tracking-wide shrink-0 border ${meta.bg} ${meta.border} ${meta.text}`}>
      {meta.label}
    </span>
  );
}

function ScorePip({ label, value }) {
  if (value == null) return null;
  const v = Math.round(value);
  const color = v >= 80 ? 'text-red-400' : v >= 60 ? 'text-yellow-400' : v >= 40 ? 'text-cyan-400' : 'text-neutral-500';
  return (
    <div className="flex flex-col items-center min-w-[44px]">
      <span className={`text-sm font-bold tabular-nums ${color}`}>{v}</span>
      <span className="text-[9px] text-neutral-600 uppercase tracking-wide">{label}</span>
    </div>
  );
}

const GTM_MOTION_ICON = {
  'direct outreach': '📞',
  'demo':            '🖥️',
  'event':           '🎪',
  'partner':         '🤝',
  'content':         '📄',
};

// ── Individual lead panel ─────────────────────────────────────────────────────
function LeadPanel({ lead, rank, router }) {
  const [copied, setCopied] = useState(false);

  const overall  = typeof lead.score === 'object' ? lead.score?.overall_score  : lead.score;
  const sigScore = typeof lead.score === 'object' ? lead.score?.signal_score    : null;
  const autScore = typeof lead.score === 'object' ? lead.score?.automation_score: null;
  const labScore = typeof lead.score === 'object' ? lead.score?.labor_pain_score: null;

  const tier = lead.priority_tier;
  const tierBorder =
    tier === 'HOT'  ? 'border-orange-700/70 hover:border-orange-500'
    : tier === 'WARM' ? 'border-amber-700/50 hover:border-amber-500'
    : 'border-neutral-700 hover:border-cyan-600';
  const tierBadgeCls =
    tier === 'HOT'  ? 'border-orange-700 text-orange-400 bg-orange-950/40'
    : tier === 'WARM' ? 'border-amber-700 text-amber-400 bg-amber-950/30'
    : 'border-cyan-800 text-cyan-400 bg-cyan-950/20';
  const accentColor = tier === 'HOT' ? '#f97316' : tier === 'WARM' ? '#f59e0b' : '#06b6d4';

  const sigs  = (lead.signals || []).slice(0, 5);
  const gtm   = lead.gtm || {};
  const reasons = Array.isArray(lead.priority_reasons) ? lead.priority_reasons : [];
  const analysisUrl = `/dashboard?analyze=${lead.id}`;

  const location = [lead.location_city, lead.location_state].filter(Boolean).join(', ');

  const motionIcon = Object.entries(GTM_MOTION_ICON).find(([k]) =>
    (gtm.suggested_motion || '').toLowerCase().includes(k)
  )?.[1] || '→';

  const pct = (s) => {
    const v = Number(s.strength ?? s.signal_strength ?? 0.5);
    const x = v > 1 ? v / 100 : v;
    return Math.round(Math.min(100, Math.max(0, x * 100)));
  };

  function handleCardClick(e) {
    if (e.target.closest('a, button, [data-nopropagate]')) return;
    router.push(analysisUrl);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); router.push(analysisUrl); }
  }

  function handleCopy(e) {
    e.stopPropagation();
    const url = `${window.location.origin}${analysisUrl}`;
    const text = lead.share_summary ? `${lead.company_name} — ${lead.share_summary}\n\n${url}` : url;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      className={`group relative border rounded-xl px-5 py-5 cursor-pointer transition-all duration-150 overflow-hidden
        ${tierBorder} bg-neutral-900/40 hover:bg-neutral-900/70 focus:outline-none focus:ring-1 focus:ring-cyan-700`}
    >
      {/* Left accent bar */}
      <div className="absolute top-0 left-0 w-1 h-full rounded-l-xl opacity-40"
        style={{ background: accentColor }} />

      {/* ── Header ── */}
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3 pl-1">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-[10px] font-mono text-neutral-600">#{rank}</span>
            {lead.preview_match_score != null && (
              <span
                className="text-[10px] font-mono text-emerald-500/90"
                title="Match score: your URL signal weights × this lead’s signal strengths"
              >
                match {Number(lead.preview_match_score).toFixed(2)}
              </span>
            )}
            <h3 className="text-lg font-bold leading-tight">
              <a
                href={companyExternalHref(lead) || '#'}
                target="_blank"
                rel="noopener noreferrer"
                data-nopropagate="1"
                onClick={e => e.stopPropagation()}
                className={`${COMPANY_NAME_LINK_CLASS} font-bold`}
              >
                {lead.company_name || 'Company'}
              </a>
            </h3>
            {tier && (
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${tierBadgeCls}`}>
                {tier}
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500">
            {lead.industry  && <span>{lead.industry}</span>}
            {location       && <span>📍 {location}</span>}
            {lead.employee_estimate && <span>👥 {lead.employee_estimate} emp.</span>}
            {lead.website   && (
              <a href={lead.website} target="_blank" rel="noopener noreferrer"
                data-nopropagate="1" onClick={e => e.stopPropagation()}
                className="text-cyan-600 hover:text-cyan-400 transition-colors">
                {lead.website.replace(/^https?:\/\/(www\.)?/, '')}
              </a>
            )}
          </div>
        </div>

        {/* Score cluster */}
        <div className="flex items-start gap-3 shrink-0">
          <div className="flex gap-3 border border-neutral-800 rounded-lg px-3 py-2 bg-neutral-900/60">
            <div className="flex flex-col items-center min-w-[44px]">
              <span className={`text-sm font-bold tabular-nums ${
                (overall ?? 0) >= 80 ? 'text-red-400' : (overall ?? 0) >= 60 ? 'text-yellow-400' : 'text-cyan-400'
              }`}>{Math.round(overall ?? 0)}</span>
              <span className="text-[9px] text-neutral-600 uppercase tracking-wide">overall</span>
            </div>
            <ScorePip label="signal"   value={sigScore} />
            <ScorePip label="automate" value={autScore} />
            <ScorePip label="labor"    value={labScore} />
          </div>
          <Link
            href={analysisUrl}
            data-nopropagate="1"
            onClick={e => e.stopPropagation()}
            className="mt-1 text-xs px-3 py-2 rounded-md border border-cyan-800 text-cyan-400
                       hover:border-cyan-600 hover:text-cyan-300 hover:bg-cyan-950/30 transition-all whitespace-nowrap"
          >
            Full analysis →
          </Link>
        </div>
      </div>

      {/* ── CRM Highlights ── */}
      {(gtm.readiness_label || gtm.why_now || reasons.length > 0 || gtm.suggested_motion) && (
        <div className="mt-3 mb-3 rounded-lg border border-neutral-800 bg-neutral-950/50 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-neutral-600 mb-2">CRM Highlights</p>
          <div className="flex flex-wrap gap-4">
            {gtm.readiness_label && (
              <div className="flex flex-col gap-0.5 min-w-[110px]">
                <span className="text-[9px] uppercase tracking-widest text-neutral-600">Readiness</span>
                <span className={`text-xs font-semibold ${
                  /hot|now|urgent/i.test(gtm.readiness_label) ? 'text-orange-400'
                  : /warm/i.test(gtm.readiness_label)         ? 'text-amber-400'
                  : 'text-cyan-300'
                }`}>{gtm.readiness_label}</span>
              </div>
            )}
            {gtm.suggested_motion && (
              <div className="flex flex-col gap-0.5 min-w-[130px]">
                <span className="text-[9px] uppercase tracking-widest text-neutral-600">Sales Motion</span>
                <span className="text-xs text-neutral-300">{motionIcon} {gtm.suggested_motion}</span>
              </div>
            )}
            {gtm.why_now && (
              <div className="flex flex-col gap-0.5 flex-1 min-w-[160px]">
                <span className="text-[9px] uppercase tracking-widest text-neutral-600">Why Now</span>
                <span className="text-xs text-neutral-400 leading-relaxed">{gtm.why_now}</span>
              </div>
            )}
          </div>
          {reasons.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {reasons.slice(0, 4).map((r, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded border border-neutral-700 bg-neutral-900 text-neutral-400">
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Automation spec ── */}
      {lead.automation_profile && (
        <div className="mt-2 border-t border-neutral-800/60 pt-3">
          <AutomationSpecBlock profile={lead.automation_profile} theme="dashboard" />
        </div>
      )}

      {/* ── Signal evidence ── */}
      {sigs.length > 0 && (
        <div className="mt-3 border-t border-neutral-800/60 pt-3 space-y-2 min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-neutral-600 mb-1">Signal Evidence</p>
          {sigs.map((s, i) => (
            <div key={i} className="flex items-start gap-2 min-w-0">
              <SignalBadge type={s.signal_type} />
              <PlainTextWithSourceLinks
                text={s.raw_text || s.signal_text || s.description || ''}
                className="text-xs text-neutral-400 flex-1 min-w-0 leading-relaxed"
              />
              <span className={`shrink-0 text-xs font-mono tabular-nums ${
                pct(s) >= 70 ? 'text-emerald-400' : pct(s) >= 40 ? 'text-cyan-500' : 'text-neutral-500'
              }`}>{pct(s)}%</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="mt-4 pt-3 border-t border-neutral-800/40 flex items-center justify-between gap-3">
        <span className="text-[10px] text-neutral-600">Click anywhere to open full analysis</span>
        <button
          data-nopropagate="1"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded border border-neutral-700 text-neutral-500
                     hover:border-cyan-700 hover:text-cyan-400 transition-all"
        >
          {copied ? '✓ Copied' : '🔗 Share deal'}
        </button>
      </div>
    </div>
  );
}

function firstQueryValue(v) {
  if (v == null) return '';
  return Array.isArray(v) ? (v[0] || '') : String(v);
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function PipelineResults() {
  const router = useRouter();
  const urlQ = firstQueryValue(router.query.url).trim();
  const companyQ = firstQueryValue(router.query.company).trim();
  const [searchFallback, setSearchFallback] = useState('');

  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      const v = (sp.get('url') || sp.get('company') || '').trim();
      if (v) setSearchFallback(v);
    } catch {
      /* ignore */
    }
  }, [router.asPath]);

  const urlStr = urlQ || companyQ || searchFallback;
  const company = useMemo(() => displayHost(urlStr), [urlStr]);

  const [loading,  setLoading]  = useState(true);
  const [matches,  setMatches]  = useState([]);
  const [previewMeta, setPreviewMeta] = useState(null);

  const fetchMatches = useCallback(async () => {
    try {
      const u = new URL(`${getApiBase()}/api/leads`);
      u.searchParams.set('limit', '6');
      u.searchParams.set('tier', 'HOT');
      u.searchParams.set('sort', 'score');
      u.searchParams.set('exclude_junk', 'true');
      u.searchParams.set('preview_meta', 'true');
      if (urlStr) {
        u.searchParams.set('preview_context', urlStr);
      }
      const res = await fetch(u.toString(), liveFetchInit());
      const data = await res.json();
      if (data && typeof data === 'object' && Array.isArray(data.leads)) {
        setMatches(data.leads.slice(0, 6));
        setPreviewMeta(data.preview || null);
      } else if (Array.isArray(data)) {
        setMatches(data.slice(0, 6));
        setPreviewMeta(null);
      } else {
        setMatches([]);
        setPreviewMeta(null);
      }
    } catch {
      setMatches([]);
      setPreviewMeta(null);
    } finally {
      setLoading(false);
    }
  }, [urlStr]);

  useEffect(() => {
    if (!urlStr) return;
    setLoading(true);
    const t = setTimeout(fetchMatches, 800);
    return () => clearTimeout(t);
  }, [urlStr, fetchMatches]);

  if (!router.isReady) {
    return (
      <RrSiteLayout>
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="inline-block w-8 h-8 border-2 border-cyan-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-neutral-500 text-sm">Loading…</p>
        </div>
      </RrSiteLayout>
    );
  }

  if (!urlStr) {
    return (
      <RrSiteLayout>
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <p className="text-neutral-500">No company URL provided.</p>
          <p className="text-xs text-neutral-600 max-w-sm text-center">
            Add <code className="text-cyan-600">?url=</code> or <code className="text-cyan-600">?company=</code> to the address bar, or go back and use Preview pipeline.
          </p>
          <Link href="/" className="px-4 py-2 border border-cyan-800 text-cyan-400 rounded hover:border-cyan-600 text-sm">
            ← Back to home
          </Link>
        </div>
      </RrSiteLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Sales Pipeline for {company} | Ready For Robots</title>
        <meta name="description" content={`Top automation-ready prospects and CRM highlights for ${company}.`} />
      </Head>
      <RrSiteLayout active="search">
        <div className="px-4 py-8 md:px-8 md:py-10 max-w-5xl mx-auto text-[var(--rr-text)]">

          {/* ── Page header ── */}
          <div className="mb-8">
            <Link href="/" className="inline-flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-300 transition-colors mb-4">
              ← Back
            </Link>
            <h1 className="text-2xl font-bold text-white mb-1">
              Sales Pipeline — <span className="text-cyan-400">{company}</span>
            </h1>
            <p className="text-sm text-neutral-500">
              Top automation-ready prospects · click any deal to open the full analysis and outreach playbook
            </p>
            {(previewMeta?.inferred_industry || (previewMeta?.signal_types && previewMeta.signal_types.length > 0)) && (
              <p className="text-sm text-neutral-400 mt-3 max-w-2xl leading-relaxed">
                {previewMeta.inferred_industry ? (
                  <span>
                    Inferred vertical:{' '}
                    <span className="text-cyan-400/95 font-medium">{previewMeta.inferred_industry}</span>
                  </span>
                ) : null}
                {previewMeta.inferred_industry && previewMeta.signal_types?.length > 0 ? (
                  <span className="text-neutral-600"> · </span>
                ) : null}
                {previewMeta.signal_types?.length > 0 ? (
                  <span>
                    Buyer signals we match on:{' '}
                    {previewMeta.signal_types.map(formatSignalTypeLabel).join(' · ')}
                  </span>
                ) : null}
              </p>
            )}
            {previewMeta?.signal_weights && Object.keys(previewMeta.signal_weights).length > 0 && (
              <p className="text-xs text-neutral-500 mt-2 max-w-2xl leading-relaxed font-mono">
                URL scores (0–100 per buyer signal): {formatUrlSignalWeights(previewMeta.signal_weights)}
              </p>
            )}
          </div>

          {/* ── Leads ── */}
          {loading ? (
            <div className="text-center py-20">
              <div className="inline-block w-6 h-6 border-2 border-cyan-600 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-neutral-500 text-sm animate-pulse">Discovering matches for {company}…</p>
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-20 border border-neutral-800 rounded-xl">
              <p className="text-neutral-400 mb-2">No matches found right now.</p>
              <p className="text-sm text-neutral-600 mb-4">Try again shortly or browse all hot leads on the dashboard.</p>
              <Link href="/dashboard" className="text-sm text-cyan-400 hover:text-cyan-300">Open dashboard →</Link>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-neutral-400">
                  <span className="text-white font-semibold">{matches.length} HOT leads</span>
                  {' '}
                  — ranked by URL–lead signal match{previewMeta?.signal_weights && Object.keys(previewMeta.signal_weights).length > 0 ? ', then deal priority' : ' (deal priority)'}
                </p>
                <Link href="/dashboard"
                  className="text-xs px-3 py-2 rounded border border-neutral-700 text-neutral-400 hover:border-cyan-700 hover:text-cyan-300 transition-colors">
                  Full pipeline dashboard →
                </Link>
              </div>

              <div className="space-y-4">
                {matches.map((lead, idx) => (
                  <LeadPanel key={lead.id || idx} lead={lead} rank={idx + 1} router={router} />
                ))}
              </div>

              {/* ── Engagement guide ── */}
              <div className="mt-10 border border-neutral-800 rounded-xl p-6">
                <h2 className="text-base font-semibold text-neutral-200 mb-1">📋 8-Week Engagement Playbook</h2>
                <p className="text-xs text-neutral-500 mb-5">Generic cadence for cold-to-close on automation deals — tailor per account using each lead's Sales Motion above.</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { phase: 'Weeks 1–2: Awareness', tactics: [
                        'Share automation ROI case study in their vertical',
                        'Engage on LinkedIn — comment on labor / ops posts',
                        'Send thought-leadership article on workforce trends',
                    ]},
                    { phase: 'Weeks 3–4: Problem Agitation', tactics: [
                        'Share industry benchmark: automation adoption rates',
                        'Invite to webinar on solving labor shortages',
                        'Send ROI calculator for automation cost savings',
                    ]},
                    { phase: 'Weeks 5–6: Solution', tactics: [
                        'Request 15-min intro call to discuss their challenges',
                        'Share video demo solving a similar use case',
                        'Offer pilot program assessment (limited slots)',
                    ]},
                    { phase: 'Weeks 7–8: Close', tactics: [
                        'Introduce customer reference from their industry',
                        'Share implementation timeline and ROI projections',
                        'Propose pilot with defined success metrics',
                    ]},
                  ].map((p) => (
                    <div key={p.phase} className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/30">
                      <p className="text-xs font-semibold text-cyan-400 mb-2">{p.phase}</p>
                      <ul className="space-y-1.5">
                        {p.tactics.map((t, i) => (
                          <li key={i} className="text-xs text-neutral-400 flex items-start gap-2">
                            <span className="text-cyan-600 mt-0.5 shrink-0">✓</span>
                            {t}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── CTA ── */}
              <div className="mt-8 border border-cyan-900/50 rounded-xl bg-cyan-950/10 p-6 text-center">
                <h3 className="text-base font-semibold text-white mb-1">Save leads and track your pipeline</h3>
                <p className="text-sm text-neutral-400 mb-4">
                  Sign up to save these accounts, get weekly signal updates, and build outreach plans per deal.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Link href="/login"
                    className="px-5 py-2.5 rounded text-sm font-semibold border border-cyan-700 bg-cyan-950/30 text-cyan-300 hover:border-cyan-500 hover:text-cyan-200 transition-colors">
                    Sign up free →
                  </Link>
                  <Link href="/dashboard"
                    className="px-5 py-2.5 rounded text-sm border border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300 transition-colors">
                    Browse full dashboard
                  </Link>
                </div>
              </div>
            </>
          )}
        </div>
      </RrSiteLayout>
    </>
  );
}
