/**
 * Ready for Robots -- Lead Intelligence Dashboard
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import Link from 'next/link';
import Head from 'next/head';
import Image from 'next/image';
import { useAuth } from './_app';
import { authHeader, supabase } from '../lib/supabase';
import LoginDropdown from '../components/LoginDropdown';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { topSignalsForDisplay, MAX_SIGNALS_DISPLAY } from '../lib/signalsDisplay';
import { AutomationSpecBlock } from '../lib/automationProfile';
import { PlainTextWithSourceLinks } from '../lib/plainText';
import SiteNavPrimaryLinks from '../components/SiteNavPrimaryLinks';
import { SignalScoreBadge, SignalScoreLabel, PipelineScoreLegend } from '../lib/signalScoreBadge';
import { companyExternalHref, isWebSearchOnlyHref } from '../lib/companyExternalHref';
import { COMPANY_NAME_LINK_CLASS } from '../lib/companyNameLinkClass';

// Static export: API host from getApiBase() / NEXT_PUBLIC_API_URL (see lib/apiBase.js).
const API = getApiBase();

// -- helpers ----------------------------------------------------------------

/** Mirrors server junk patterns — hides obvious scraper fragments if API still returns them. */
const JUNK_DISPLAY_NAME_PATTERNS = [
  /\bessential benefits\b/i,
  /-->/,
  /fyi\s*-->/i,
  /==/,
  /--+\s*$/i,
  /\s+fetch\s*$/i,
  /\s+and\s+locus\s+robotics\b/i,
  /\bbito\s+lagertechnik\s+and\b/i,
  /\s-\s*ydr\b/i,
  /^\s*physical\s+ai\s*$/i,
  /^\s*tutor\s+intelligence\s*$/i,
  /^\s*bangladesh\s+rmg\s*$/i,
  /\blagertechnik\s+and\s+locus\b/i,
];

function isLikelyJunkDisplayName(name) {
  if (name == null || typeof name !== 'string') return true;
  const s = name.trim();
  if (!s) return true;
  return JUNK_DISPLAY_NAME_PATTERNS.some(p => p.test(s));
}

function barColor(v) {
  if (v >= 75) return 'bg-emerald-500';
  if (v >= 50) return 'bg-cyan-400';
  if (v >= 30) return 'bg-yellow-500';
  return 'bg-neutral-600';
}

function ScoreBar({ value = 0, label }) {
  const pct = Math.min(100, Math.max(0, Math.round(value)));
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-400">{label}</span>
        <span className="text-xs tabular-nums text-zinc-500">{pct}</span>
      </div>
      <div className="bar-track">
        <div className={`bar-fill ${barColor(pct)}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// Tier -- stroke + text only, no fill
const TIER_META = {
  HOT:  { text: 'text-red-400',    border: 'border-red-800',    borderL: 'border-l-red-800',    label: 'HOT'  },
  WARM: { text: 'text-yellow-400', border: 'border-yellow-800', borderL: 'border-l-yellow-800', label: 'WARM' },
  COLD: { text: 'text-cyan-400',   border: 'border-cyan-900',   borderL: 'border-l-cyan-900',   label: 'COLD' },
};

function TierBadge({ tier }) {
  const m = TIER_META[tier] || TIER_META.COLD;
  return (
    <span className={`badge ${m.border} ${m.text}`}>
      {tier}
    </span>
  );
}

// Signal badges -- stroke only, no fill
const SIGNAL_META = {
  funding_round:         { label: 'Funding',      border: 'border-violet-700',  text: 'text-violet-400'  },
  strategic_hire:        { label: 'Exec Hire',    border: 'border-blue-700',    text: 'text-blue-400'    },
  capex:                 { label: 'CapEx',        border: 'border-cyan-700',    text: 'text-cyan-400'    },
  ma_activity:           { label: 'M&A',          border: 'border-amber-700',    text: 'text-amber-400'    },
  expansion:             { label: 'Expand',       border: 'border-emerald-800', text: 'text-emerald-400' },
  job_posting:           { label: 'Hiring',       border: 'border-amber-700',   text: 'text-amber-400'   },
  labor_shortage:        { label: 'Labor Gap',    border: 'border-red-800',     text: 'text-red-400'     },
  quality_bottleneck:    { label: 'Quality',      border: 'border-orange-700',  text: 'text-orange-400'  },
  safety_incident:       { label: 'Safety',       border: 'border-red-700',     text: 'text-red-300'     },
  production_capacity:   { label: 'Capacity',     border: 'border-yellow-700',  text: 'text-yellow-400'  },
  warehouse_throughput:  { label: 'Throughput',   border: 'border-teal-700',    text: 'text-teal-400'    },
  packaging_automation:  { label: 'Packaging',    border: 'border-indigo-700',  text: 'text-indigo-400'  },
  repetitive_process:    { label: 'Repetitive',   border: 'border-purple-700',  text: 'text-purple-400'  },
  material_handling:     { label: 'Material',     border: 'border-lime-700',    text: 'text-lime-400'    },
  news:                  { label: 'News',         border: 'border-neutral-700', text: 'text-neutral-400' },
};

function SignalBadge({ type }) {
  const m = SIGNAL_META[type] || { label: type, border: 'border-neutral-700', text: 'text-neutral-400' };
  return <span className={`badge signal-badge ${m.border} ${m.text}`} title={`${m.label} signal detected`}>{m.label}</span>;
}

function HealthDot({ open }) {
  return (
    <span className={`inline-block h-1.5 w-1.5 rounded-full ${open ? 'bg-red-500' : 'bg-emerald-500'}`} />
  );
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

// Builds the X tweet text: headline first, then first sentence of summary
function buildTweetText(lead) {
  const topSig = (lead.signals || [])[0];
  const sigLabel = topSig?.signal_label || (topSig?.signal_type || '').replace(/_/g, ' ');
  const tierEmoji = lead.priority_tier === 'HOT' ? '🔥' : lead.priority_tier === 'WARM' ? '⚡' : '✦';
  const headline = `${lead.company_name}${sigLabel ? ` — ${sigLabel}` : ''} | ${tierEmoji} ${lead.priority_tier || 'Lead'}`;
  const summary = lead.share_summary || lead.share_blurb || '';
  const firstSentence = summary.split('. ')[0] + (summary.includes('. ') ? '.' : '');
  const maxBody = 240 - headline.length - 2;
  const body = firstSentence && firstSentence.length <= maxBody
    ? firstSentence
    : firstSentence.slice(0, Math.max(30, maxBody - 1)) + '…';
  return body ? `${headline}\n\n${body}` : headline;
}

// Compact share bar used on lead rows and drawer
function LeadShareBar({ lead, compact = false }) {
  const [copied, setCopied] = useState(false);
  const shareUrl = `${SITE_URL}/#leads`;
  const tweetText = buildTweetText(lead);
  const fullSummary = lead.share_summary || lead.share_blurb || `${lead.company_name} — automation signals`;

  const copyPost = (e) => {
    e.stopPropagation();
    navigator.clipboard?.writeText(`${tweetText}\n\n${shareUrl}`).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
  const liTitle = encodeURIComponent(`${lead.company_name} — ${lead.priority_tier || 'Lead'} | Ready For Robots`);
  const liSummary = encodeURIComponent(fullSummary.slice(0, 700));
  const linkedInUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${liTitle}&summary=${liSummary}&source=readyforrobots.com`;

  if (compact) {
    return (
      <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
        <a href={twitterUrl} target="_blank" rel="noopener noreferrer" title="Share on X"
          className="p-1 rounded hover:bg-neutral-800 text-neutral-600 hover:text-white transition-colors">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
        <a href={linkedInUrl} target="_blank" rel="noopener noreferrer" title="Share on LinkedIn"
          className="p-1 rounded hover:bg-neutral-800 text-neutral-600 hover:text-[#0a66c2] transition-colors">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
        <button onClick={copyPost} title="Copy post"
          className="p-1 rounded hover:bg-neutral-800 text-neutral-600 hover:text-emerald-400 transition-colors text-[9px] font-mono">
          {copied ? '✓' : '⧉'}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2" onClick={e => e.stopPropagation()}>
      {/* Intelligence summary paragraph */}
      {fullSummary && (
        <div className="rounded border border-cyan-900/40 bg-cyan-950/10 p-3">
          <div className="text-[10px] font-semibold text-cyan-500 uppercase tracking-wider mb-1.5">Intelligence Summary</div>
          <p className="text-xs text-neutral-300 leading-relaxed">{fullSummary}</p>
        </div>
      )}
      {/* Share row */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] text-neutral-500 uppercase tracking-wider">Share:</span>
        <a href={twitterUrl} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded border border-neutral-700 bg-neutral-900 hover:bg-black text-neutral-400 hover:text-white text-[10px] font-medium transition-colors">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          X (Twitter)
        </a>
        <a href={linkedInUrl} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded border border-neutral-700 bg-neutral-900 hover:bg-[#0a66c2] text-neutral-400 hover:text-white text-[10px] font-medium transition-colors">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          LinkedIn
        </a>
        <button onClick={copyPost}
          className="inline-flex items-center gap-1.5 px-2 py-1 rounded border border-neutral-700 bg-neutral-900 hover:bg-emerald-900 text-neutral-400 hover:text-emerald-300 text-[10px] font-medium transition-colors">
          {copied ? '✓ Copied!' : 'Copy post'}
        </button>
      </div>
    </div>
  );
}

function ScoreNum({ value }) {
  const v = Math.round(value ?? 0);
  let badgeClass = 'score-badge-poor border-red-700 text-red-400';
  if (v >= 75) badgeClass = 'score-badge-high border-emerald-700 text-emerald-400';
  else if (v >= 50) badgeClass = 'score-badge-medium border-cyan-700 text-cyan-400';
  else if (v >= 30) badgeClass = 'score-badge-low border-yellow-700 text-yellow-400';
  
  return (
    <span className={`inline-flex items-center border rounded-md px-2 leading-none tabular-nums font-mono font-bold text-xs ${badgeClass}`} style={{ paddingTop: '0.25rem', paddingBottom: '0.25rem' }}>
      {v}
    </span>
  );
}

/** Deal value score (intent + firmographics + spec + timing + procurement) — distinct from ML intent */
function ValueNum({ value }) {
  const v = Math.round(value ?? 0);
  let badgeClass = 'border-violet-900 text-violet-400';
  if (v >= 75) badgeClass = 'border-violet-500 text-violet-200';
  else if (v >= 50) badgeClass = 'border-violet-600 text-violet-300';
  else if (v >= 30) badgeClass = 'border-violet-800 text-violet-400';
  return (
    <span
      className={`inline-flex items-center border rounded-md px-2 leading-none tabular-nums font-mono font-bold text-xs ${badgeClass}`}
      style={{ paddingTop: '0.25rem', paddingBottom: '0.25rem' }}
      title="Lead value: blended deal quality (not tier alone)"
    >
      {v}
    </span>
  );
}

const PROCUREMENT_HINT_LABELS = {
  rfp_procurement: 'RFP',
  go_live_milestone: 'Go-live',
  quarter_fy_window: 'FY/Q',
  near_term_horizon: 'Near-term',
  capex_committed: 'CapEx',
};

function ProcurementHints({ hints, className = '' }) {
  const list = Array.isArray(hints) ? hints : [];
  if (!list.length) return null;
  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {list.map((h) => (
        <span
          key={h}
          title={h}
          className="text-[9px] px-1.5 py-0.5 rounded border border-amber-800/70 text-amber-400/95 font-medium"
        >
          {PROCUREMENT_HINT_LABELS[h] || String(h).replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  );
}

const INDUSTRIES  = ['All', 'Hospitality', 'Logistics', 'Healthcare', 'Food Service', 'Food Processing & Manufacturing', 'CPG & Consumer Goods', 'Contract Manufacturing', 'Airports & Transportation', 'Casinos & Gaming', 'Cruise Lines', 'Theme Parks & Entertainment', 'Real Estate & Facilities', 'Manufacturing'];
const SIGNAL_TYPES = ['', 'funding_round', 'strategic_hire', 'capex', 'ma_activity', 'expansion', 'job_posting', 'labor_shortage', 'quality_bottleneck', 'safety_incident', 'production_capacity', 'warehouse_throughput', 'packaging_automation', 'repetitive_process', 'material_handling'];
const TIERS = ['ALL', 'HOT', 'WARM', 'COLD'];

const SEARCH_CATEGORIES = [
  { key: 'automation_investment', label: 'Automation Investments' },
  { key: 'acquisitions',          label: 'Acquisitions & M&A'    },
  { key: 'labor_downsizing',      label: 'Labor Downsizing'      },
  { key: 'warehouse_logistics',   label: 'Warehouse Logistics'   },
  { key: 'robot_automation',      label: 'Robot Automation'      },
  { key: 'intra_logistics',       label: 'Intra-Logistics'       },
  { key: 'pack_work',             label: 'Pack In / Pack Out'    },
  { key: 'kitting',               label: 'Kitting & Assembly'    },
  { key: 'restocking',            label: 'Restocking'            },
  { key: 'inventory_management',  label: 'Inventory Mgmt'        },
  { key: 'healthcare_automation', label: 'Healthcare Automation' },
  { key: 'retail_automation',     label: 'Retail Automation'     },
];

function TrendingTicker() {
  return null;
}

function uniqueSignalTypes(signals = []) {
  const seen = new Set();
  return signals.filter(s => { if (seen.has(s.signal_type)) return false; seen.add(s.signal_type); return true; });
}

// -- Strategic Snapshot (replaces HOT/WARM/COLD boxes) ----------------------
const INDUSTRY_ROBOT_FIT = {
  'Hospitality':                    'Service & Delivery',
  'Logistics':                      'Warehouse AMR Fleet',
  'Healthcare':                     'Clinical Logistics',
  'Food Service':                   'BOH Automation',
  'Food Processing & Manufacturing':'EOL Line Automation',
  'CPG & Consumer Goods':           'Palletizing & Case Pack',
  'Contract Manufacturing':         'Flexible EOL Robotics',
  'Airports & Transportation':      'Ground Ops Robots',
  'Retail':                         'Picking & Restocking',
  'Casinos & Gaming':               'Floor & F&B Delivery',
  'Cruise Lines':                   'Onboard Delivery',
  'Theme Parks & Entertainment':    'F&B & Custodial',
  'Real Estate & Facilities':       'Cleaning & Concierge',
  'Automotive & Manufacturing':     'Assembly & Machine Tending',
  'Manufacturing':                  'Assembly & Material Handling',
};

const READINESS = {
  HOT:  { label: 'Active Buyer',  color: 'text-red-400',     dot: 'bg-red-500'     },
  WARM: { label: 'Evaluating',    color: 'text-yellow-400',  dot: 'bg-yellow-500'  },
  COLD: { label: 'Monitoring',    color: 'text-neutral-500', dot: 'bg-neutral-600' },
};

/** Prefer API `gtm` (robot readiness stage + why now); fall back to tier labels. */
function gtmReadinessDisplay(lead) {
  const g = lead.gtm;
  if (!g || !g.readiness_label) {
    const r = READINESS[lead.priority_tier] || READINESS.COLD;
    return { label: r.label, color: r.color, sub: null };
  }
  const stage = g.readiness_stage;
  const color =
    stage === 'deploying' ? 'text-amber-400' :
    stage === 'evaluating' ? 'text-amber-400' :
    'text-zinc-500';
  const sub = Array.isArray(g.why_now) && g.why_now[0] ? g.why_now[0] : null;
  return { label: g.readiness_label, color, sub };
}

function dealLabel(emp) {
  if (!emp) return { tier: '—', est: null };
  if (emp >= 100000) return { tier: 'Enterprise',  est: Math.round(emp / 400) };
  if (emp >= 20000)  return { tier: 'Large',       est: Math.round(emp / 500) };
  if (emp >= 5000)   return { tier: 'Mid-Market',  est: Math.round(emp / 600) };
  if (emp >= 1000)   return { tier: 'Regional',    est: Math.round(emp / 700) };
  return                    { tier: 'SMB',         est: Math.round(emp / 800) };
}

function topSignal(lead) {
  const sigs = lead.signals || [];
  if (!sigs.length) return null;
  return [...sigs].sort((a, b) => (b.strength || 0) - (a.strength || 0))[0];
}

function strategicFit(lead) {
  const base = INDUSTRY_ROBOT_FIT[lead.industry] || 'Automation Suite';
  const sig  = topSignal(lead);
  if (sig?.signal_type === 'quality_bottleneck')   return `${base} · Quality Fix`;
  if (sig?.signal_type === 'safety_incident')      return `${base} · Safety Issue`;
  if (sig?.signal_type === 'production_capacity')  return `${base} · At Capacity`;
  if (sig?.signal_type === 'warehouse_throughput') return `${base} · Throughput`;
  if (sig?.signal_type === 'packaging_automation') return `${base} · Packaging`;
  if (sig?.signal_type === 'repetitive_process')   return `${base} · Repetitive`;
  if (sig?.signal_type === 'material_handling')    return `${base} · Material`;
  if (sig?.signal_type === 'labor_shortage')       return `${base} · Labor Crisis`;
  if (sig?.signal_type === 'capex')                return `${base} · CapEx Window`;
  if (sig?.signal_type === 'expansion')            return `${base} · Growth Phase`;
  if (sig?.signal_type === 'strategic_hire')       return `${base} · New Exec`;
  if (sig?.signal_type === 'funding_round')        return `${base} · Funded`;
  if (sig?.signal_type === 'ma_activity')          return `${base} · M&A`;
  return base;
}

function StrategicSnapshot({ leads, onSelect }) {
  const sorted = [...leads]
    .filter(l => l.score?.overall_score != null)
    .sort((a, b) => (b.score?.overall_score ?? 0) - (a.score?.overall_score ?? 0))
    .slice(0, 10);
  
  if (!sorted.length) return null;

  return (
    <div className="rr-strategic-snapshot rr-strategic-snapshot--tight">
      <div className="rr-strategic-snapshot-hdr">
        <div className="rr-strategic-snapshot-title">
          <span className="rr-snapshot-bolt" aria-hidden>⚡</span>
          <span>Strategic Snapshot</span>
        </div>
        <div className="rr-strategic-snapshot-meta tabular-nums">
          Showing top {sorted.length} deals
        </div>
      </div>

      <div className="rr-strategic-snapshot-table-wrap">
        <div
          className="rr-strategic-snapshot-thead hidden md:grid"
          style={{gridTemplateColumns:'1.5rem 1fr 7.5rem 7rem 6rem 3.25rem 4rem 4rem 6.5rem'}}>
          <span />
          <span className="text-[10px] uppercase font-bold tracking-wide text-[var(--rr-muted)] px-3 py-2.5">company</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-[var(--rr-muted)] px-2 py-2.5">signal</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-[var(--rr-muted)] px-2 py-2.5">readiness</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-[var(--rr-muted)] px-2 py-2.5">deal size</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-teal-500/90 px-2 py-2.5 text-right" title="Weighted signal evidence">sig</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-violet-400/90 px-2 py-2.5 text-right" title="Deal value">value</span>
          <span className="text-[10px] uppercase font-bold tracking-wide text-[var(--rr-muted)] px-2 py-2.5 text-right" title="ML intent">intent</span>
          <span />
        </div>

        {sorted.map((lead, i) => {
          const sig   = topSignal(lead);
          const ready = gtmReadinessDisplay(lead);
          const deal  = dealLabel(lead.employee_estimate);
          const sigM  = sig ? (SIGNAL_META[sig.signal_type] || { label: sig.signal_type, border: 'border-neutral-700', text: 'text-neutral-400' }) : null;
          const excerpt = sig ? (sig.raw_text || '').substring(0, 55) : '';

          return (
            <div key={lead.id}
              className="grid grid-cols-[1.5rem_1fr_auto] md:grid-cols-none border-b border-[var(--rr-border)] last:border-0 hover:bg-white/[0.02] transition-colors group items-center"
              style={{
                gridTemplateColumns:'1.5rem 1fr 7.5rem 7rem 6rem 3.25rem 4rem 4rem 6.5rem'
              }}>

              {/* rank */}
              <span className="text-[10px] text-neutral-600 pl-3 group-hover:text-neutral-500 transition-colors tabular-nums">{i + 1}</span>

              {/* company — div (not button) so the name can be a real <a> */}
              <div
                role="button"
                tabIndex={0}
                onClick={() => onSelect(lead)}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(lead);
                  }
                }}
                className="px-3 py-3 min-w-0 text-left w-full cursor-pointer"
              >
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <a
                      href={companyExternalHref(lead) || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={e => e.stopPropagation()}
                      className={`${COMPANY_NAME_LINK_CLASS} text-[12px] font-semibold leading-tight`}
                    >
                      {lead.company_name}
                    </a>
                  </div>
                  <span className="text-[10px] text-neutral-500 truncate hidden sm:inline">
                    {[lead.industry, lead.location_city].filter(Boolean).join(' · ')}
                  </span>
                  {excerpt && (
                    <p className="text-[10px] text-neutral-400 truncate mt-0.5 max-w-[24rem]" title={sig?.raw_text}>
                      {excerpt}{excerpt.length === 55 ? '…' : ''}
                    </p>
                  )}
                </div>
              </div>

              {/* signal badge */}
              <div className="hidden md:flex items-center px-2 py-2">
                {sigM
                  ? <span className={`text-[10px] px-2 py-0.5 rounded border bg-transparent ${sigM.border} ${sigM.text}`}>{sigM.label}</span>
                  : <span className="text-[10px] text-neutral-800">—</span>}
              </div>

              {/* readiness (GTM stage + first “why now”) */}
              <div className="hidden md:flex flex-col justify-center gap-0.5 px-2 py-2 min-w-0">
                <span className={`text-[11px] font-medium ${ready.color}`}>{ready.label}</span>
                {ready.sub && (
                  <span className="text-[10px] text-neutral-500 leading-snug line-clamp-2" title={ready.sub}>
                    {ready.sub}
                  </span>
                )}
              </div>

              {/* deal */}
              <div className="hidden md:flex items-center px-2 py-2">
                <span className="text-[11px] text-neutral-400">{deal.tier}</span>
              </div>

              {/* aggregate signal score */}
              <div className="hidden md:flex items-center justify-end px-2 py-2">
                <SignalScoreBadge value={lead.score?.signal_score ?? 0} />
              </div>

              {/* lead value */}
              <div className="hidden md:flex flex-col items-end justify-center px-2 py-2 gap-0.5">
                <ValueNum value={lead.score?.lead_value_score ?? 0} />
                <ProcurementHints hints={lead.procurement_hints} />
              </div>

              {/* ML intent */}
              <div className="flex items-center justify-end px-2 py-2">
                <ScoreNum value={lead.score?.overall_score ?? 0} />
              </div>

              {/* Action */}
              <div className="flex items-center justify-end pr-3 py-2">
                <button
                  onClick={() => onSelect(lead)}
                  className="px-2 py-1 text-[10px] border border-emerald-800 text-emerald-500 hover:border-emerald-500 hover:bg-emerald-950/30 transition-colors rounded">
                  Analyze →
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// -- Quick scrape widget -------------------------------------------------------
function QuickScrape({ onDone }) {
  const [open,   setOpen]   = useState(false);
  const [urls,   setUrls]   = useState('');
  const [ind,    setInd]    = useState('');
  const [now,    setNow]    = useState(false);
  const [status, setStatus] = useState(null);  // null | 'loading' | 'done' | 'error'
  const [result, setResult] = useState(null);

  async function submit() {
    if (!urls.trim()) return;
    setStatus('loading');
    try {
      const r = await fetch(`${API}/api/agent/scrape/quick`, liveFetchInit({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls, industry: ind || null, scrape_now: now }),
      }));
      const data = await r.json();
      setResult(data);
      setStatus('done');
      setUrls('');
      if (onDone) onDone();
    } catch {
      setStatus('error');
    }
  }

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-neutral-500 hover:text-neutral-300 transition-colors">
        <span>&#43; quick scrape &mdash; paste URLs to add as lead sources</span>
        <span className="text-neutral-700">{open ? '&#9650;' : '&#9660;'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-neutral-800">
          <textarea value={urls} onChange={e => setUrls(e.target.value)}
            rows={4} placeholder="https://www.simplyhired.com/search?q=hotel+manager&l=las+vegas&#10;https://www.linkedin.com/jobs/search/?keywords=warehouse+automation"
            className="w-full mt-3 bg-neutral-900 border border-neutral-600 rounded px-3 py-2 text-xs
                       text-neutral-200 placeholder-neutral-500 font-mono
                       focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-900 transition-colors resize-y" />
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="label block mb-1">industry hint</label>
              <select value={ind} onChange={e => setInd(e.target.value)}
                className="bg-transparent border border-neutral-800 rounded px-2 py-1 text-xs text-neutral-400
                           focus:outline-none focus:border-neutral-600">
                <option value="">auto-detect</option>
                {INDUSTRIES.filter(i => i !== 'All').map(i => (
                  <option key={i} value={i}>{i}</option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={now} onChange={e => setNow(e.target.checked)}
                className="accent-emerald-500" />
              <span className={now ? 'text-emerald-400' : 'text-neutral-400'}>scrape now</span>
            </label>
            <button onClick={submit} disabled={status === 'loading'}
              className="ml-auto btn-ghost border-emerald-900 text-emerald-400 hover:border-emerald-600">
              {status === 'loading' ? 'adding...' : '&#8599; add sources'}
            </button>
          </div>
          {status === 'done' && result && (
            <div className="text-xs text-emerald-500 border border-emerald-900 rounded px-3 py-2">
              &#10003; Added {result.added} source(s). {result.skipped > 0 ? `${result.skipped} already existed.` : ''}
              {result.tasks_queued > 0 ? ` ${result.tasks_queued} scrape task(s) queued.` : ''}
            </div>
          )}
          {status === 'error' && (
            <div className="text-xs text-red-500">&#9888; Failed to add sources — check API connection.</div>
          )}
        </div>
      )}
    </div>
  );
}

// -- Agent insights panel ------------------------------------------------------
const URGENCY_META = {
  NOW:     { text: 'text-red-400',    border: 'border-red-900',    label: 'ACT NOW'  },
  SOON:    { text: 'text-yellow-400', border: 'border-yellow-900', label: 'SOON'     },
  MONITOR: { text: 'text-neutral-500',border: 'border-neutral-800',label: 'MONITOR'  },
};

function AgentInsightsPanel() {
  const [open,     setOpen]     = useState(false);
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [tab,      setTab]      = useState('strategies');

  async function load() {
    if (data) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/agent/insights`, liveFetchInit());
      if (r.ok) setData(await r.json());
    } catch {}
    setLoading(false);
  }

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next) load();
  }

  const tabs = ['strategies', 'sources', 'patterns', 'targets'];

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={toggle}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs hover:bg-neutral-900/40 transition-colors">
        <span className="flex items-center gap-2">
          <span className="text-emerald-400">&#9650; ML Agent</span>
          <span className="text-neutral-600">&mdash; lead source rankings, signal patterns &amp; approach strategies</span>
        </span>
        <span className="text-neutral-700">{open ? '&#9650;' : '&#9660;'}</span>
      </button>

      {open && (
        <div className="border-t border-neutral-800">
          {loading && <p className="px-4 py-6 text-xs text-neutral-400 animate-pulse">running analysis&hellip;</p>}
          {!loading && data && (
            <div className="px-4 pb-4">
              {/* learning notes */}
              <div className="py-3 border-b border-neutral-800/60 space-y-1">
                {data.learning_notes.map((n, i) => (
                  <p key={i} className="text-xs text-neutral-300">{n}</p>
                ))}
              </div>

              {/* coverage gaps */}
              {data.coverage_gaps?.length > 0 && (
                <div className="py-3 border-b border-neutral-800/60">
                  <p className="label mb-2">coverage gaps</p>
                  <div className="space-y-1">
                    {data.coverage_gaps.map((g, i) => (
                      <p key={i} className="text-xs text-yellow-700">&#9651; {g}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* tab bar */}
              <div className="flex gap-1 mt-3 mb-4">
                {tabs.map(t => (
                  <button key={t} onClick={() => setTab(t)}
                    className={tab === t ? 'tab-active' : 'tab-inactive'}>
                    {t}
                  </button>
                ))}
              </div>

              {/* strategies tab */}
              {tab === 'strategies' && (
                <div className="space-y-3">
                  {data.top_strategies.length === 0 && <p className="text-xs text-neutral-500">No strategies yet — need more lead data.</p>}
                  {data.top_strategies.map((s, i) => {
                    const um = URGENCY_META[s.urgency] || URGENCY_META.MONITOR;
                    return (
                      <div key={i} className={`border ${um.border} rounded p-4`}>
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <a
                              href={companyExternalHref({ company_name: s.company_name }) || '#'}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`${COMPANY_NAME_LINK_CLASS} text-sm font-medium`}
                            >
                              {s.company_name}
                            </a>
                            <span className={`ml-2 badge ${um.border} ${um.text}`}>{um.label}</span>
                          </div>
                          <span className="label">{Math.round(s.confidence * 100)}% confidence</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          <div>
                            <span className="label block mb-0.5">contact</span>
                            <span className="text-neutral-300">{s.contact_role}</span>
                          </div>
                          <div>
                            <span className="label block mb-0.5">channel</span>
                            <span className="text-neutral-300">{s.best_channel}</span>
                          </div>
                          <div className="sm:col-span-2">
                            <span className="label block mb-0.5">lead with</span>
                            <span className="text-neutral-300">{s.pitch_angle}</span>
                          </div>
                          <div className="sm:col-span-2">
                            <span className="label block mb-1">talking points</span>
                            <ul className="space-y-1">
                              {s.talking_points.map((tp, ti) => (
                                <li key={ti} className="text-neutral-500 flex gap-2">
                                  <span className="text-emerald-800 shrink-0">&#8227;</span>{tp}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="sm:col-span-2">
                            <span className={`text-[11px] ${um.text}`}>&#9201; {s.timing_note}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* sources tab */}
              {tab === 'sources' && (
                <div>
                  {data.source_rankings.length === 0 && <p className="text-xs text-neutral-500">No source data yet.</p>}
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-neutral-800">
                        {['tier','source','leads','avg score','industries','signals'].map(h => (
                          <th key={h} className="pb-2 pr-4 label font-normal text-left">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.source_rankings.map((r, i) => (
                        <tr key={i} className="border-b border-neutral-900">
                          <td className="py-1.5 pr-4">
                            <span className={`badge ${
                              r.quality_tier === 'GOLD'   ? 'border-yellow-700 text-yellow-400' :
                              r.quality_tier === 'SILVER' ? 'border-neutral-600 text-neutral-300' :
                              r.quality_tier === 'BRONZE' ? 'border-amber-900 text-amber-600' :
                              'border-neutral-800 text-neutral-600'
                            }`}>{r.quality_tier}</span>
                          </td>
                          <td className="py-1.5 pr-4 text-neutral-300 font-mono">{r.domain}</td>
                          <td className="py-1.5 pr-4 tabular-nums text-neutral-400">{r.lead_count}</td>
                          <td className="py-1.5 pr-4">
                            <ScoreNum value={r.avg_score} />
                          </td>
                          <td className="py-1.5 pr-4 text-neutral-600 max-w-[8rem] truncate">{r.top_industries.join(', ')}</td>
                          <td className="py-1.5 text-neutral-600">{r.top_signal_types.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* patterns tab */}
              {tab === 'patterns' && (
                <div className="space-y-2">
                  {data.signal_patterns.length === 0 && <p className="text-xs text-neutral-500">No patterns detected yet.</p>}
                  {data.signal_patterns.map((p, i) => (
                    <div key={i} className="border border-neutral-800 rounded px-3 py-2.5">
                      <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                        {p.signals.map(s => (
                          <span key={s} className="badge border-emerald-800 text-emerald-400">{s}</span>
                        ))}
                        <span className="ml-auto label">{p.occurrence_count}x &middot; avg <ScoreNum value={p.avg_score} /></span>
                      </div>
                      <p className="text-xs text-neutral-300">{p.insight}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* targets tab */}
              {tab === 'targets' && (
                <div className="space-y-2">
                  <p className="text-xs text-neutral-400 mb-3">Agent-recommended scrape sources based on coverage gaps.</p>
                  {data.recommended_targets.map((t, i) => (
                    <div key={i} className="flex items-start gap-3 border border-neutral-800 rounded px-3 py-2.5">
                      <div className="flex-1 min-w-0">
                        <a href={t.url} target="_blank" rel="noreferrer"
                          className="text-xs text-cyan-600 hover:text-cyan-400 font-mono truncate block">{t.url}</a>
                        <p className="text-xs text-neutral-500 mt-0.5">{t.reason}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <span className="badge border-emerald-900 text-emerald-600">{t.expected_industry}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button onClick={() => setData(null) || load()}
                className="mt-4 btn-ghost text-neutral-400 text-[10px]">&#8635; rerun analysis</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// -- AI Analysis modal (tabbed: Strategy | Robots | Decision Makers | Intel | Signals) --
const AI_TABS = ['strategy', 'engagement', 'robot match', 'decision makers', 'intel', 'signals'];

// Classify a talking-point string → emerald (important) | cyan (time-sensitive) | grey
function tpColor(text) {
  const t = (text || '').toLowerCase();
  if (/\b(now|urgent|immediately|deadline|this quarter|q[1-4]|actively|currently|recent|just announced|underway|hiring now|this month|this week|window|right now|breaking|open role)\b/.test(t))
    return 'text-cyan-400';
  if (/\b(roi|cost|saving|labor shortage|vacancy|capex|budget|million|billion|vp |director|chief|automation|robot|replace|reduce|solve|address|critical|workforce|staffing|efficiency|pain)\b/.test(t))
    return 'text-emerald-400';
  return 'text-neutral-400';
}

function AIAnalysisModal({ lead, onClose, onSaveToggle }) {
  const { session } = useAuth();
  const [activeTab,    setActiveTab]    = useState('strategy');
  const [profile,      setProfile]      = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [saved,        setSaved]        = useState(false);
  const [reportSaved,  setReportSaved]  = useState(false);
  const [savingReport, setSavingReport] = useState(false);
  const [automationProfileExtra, setAutomationProfileExtra] = useState(null);
  const [gtmExtra, setGtmExtra] = useState(null);
  const [repFbSending, setRepFbSending] = useState(false);
  const [repFbDone, setRepFbDone] = useState(false);
  const [repFbErr, setRepFbErr] = useState(null);

  // load profile + check saved state
  useEffect(() => {
    // check localStorage saved state
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
      setSaved(!!(store.companies || []).find(c => c.id === lead.id));
    } catch {}

    fetch(`${API}/api/agent/profile/${lead.id}`, liveFetchInit())
      .then(r => r.ok ? r.json() : null)
      .then(d => { setProfile(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [lead.id]);

  // When modal opened from search, list payload may omit automation_profile / gtm — hydrate from API
  useEffect(() => {
    setAutomationProfileExtra(null);
    setGtmExtra(null);
    if (!lead?.id) return;
    if (lead?.automation_profile && lead?.gtm) return;
    fetch(`${API}/api/leads/by-id/${lead.id}`, liveFetchInit())
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.automation_profile) setAutomationProfileExtra(d.automation_profile);
        if (d?.gtm) setGtmExtra(d.gtm);
      })
      .catch(() => {});
  }, [lead.id, lead.automation_profile, lead.gtm]);

  useEffect(() => {
    setRepFbDone(false);
    setRepFbErr(null);
  }, [lead.id]);

  async function submitRepFeedback(vote, reasonCode = null) {
    if (repFbSending || lead?.id == null) return;
    setRepFbSending(true);
    setRepFbErr(null);
    try {
      const hdr = { 'Content-Type': 'application/json' };
      if (session?.access_token) hdr.Authorization = `Bearer ${session.access_token}`;
      const r = await fetch(`${API}/api/leads/${lead.id}/feedback`, liveFetchInit({
        method: 'POST',
        headers: hdr,
        body: JSON.stringify({
          vote,
          ...(reasonCode ? { reason_code: reasonCode } : {}),
        }),
      }));
      if (!r.ok) throw new Error((await r.text()) || r.statusText);
      setRepFbDone(true);
    } catch (e) {
      setRepFbErr(e.message || 'Failed to send');
    } finally {
      setRepFbSending(false);
    }
  }

  // close on Escape
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  async function saveReport() {
    if (!session) { window.location.href = '/login'; return; }
    setSavingReport(true);
    try {
      const reportData = {
        company_id:    lead.id,
        company_name:  lead.company_name,
        title:         `AI Report — ${lead.company_name}`,
        report_data:   {
          company:       profile?.company || {},
          scores:        lead.score || profile?.scores || {},
          strategy:      profile?.strategy || {},
          robot_match:   profile?.robot_match || [],
          decision_makers: profile?.decision_makers || [],
          intel_links:   profile?.intel_links || [],
          signals:       lead.signals || [],
        },
      };
      const res = await fetch(`${API}/api/user/reports`, liveFetchInit({
        method:  'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body:    JSON.stringify(reportData),
      }));
      if (res.ok) setReportSaved(true);
      else throw new Error(await res.text());
    } catch (e) { alert('Save failed: ' + e.message); }
    setSavingReport(false);
  }

  function toggleSave() {
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[],"lists":[]}');
      if (!store.companies) store.companies = [];
      if (saved) {
        store.companies = store.companies.filter(c => c.id !== lead.id);
      } else {
        store.companies.push({
          id:        lead.id,
          name:      lead.company_name,
          industry:  lead.industry,
          score:     lead.score?.overall_score ?? profile?.scores?.overall_score ?? 0,
          tier:      lead.priority_tier,
          saved_at:  new Date().toISOString(),
          website:   lead.website || profile?.company?.website,
        });
      }
      localStorage.setItem('rfr_saved', JSON.stringify(store));
      setSaved(!saved);
      if (onSaveToggle) onSaveToggle();
    } catch {}
  }

  const tm     = TIER_META[lead.priority_tier] || TIER_META.COLD;
  const sc     = lead.score || profile?.scores || {};
  const strat  = profile?.strategy;
  const um     = strat ? (URGENCY_META[strat.urgency] || URGENCY_META.MONITOR) : null;
  const comp   = profile?.company || {};
  const city   = comp.location_city || lead.location_city || '';
  const state  = comp.location_state || lead.location_state || '';
  const emp    = comp.employee_estimate || lead.employee_estimate;
  const site   = comp.website || lead.website;

  const automationProfile = lead.automation_profile || automationProfileExtra;
  const gtm = lead.gtm || gtmExtra;
  const engagementSignals = lead.signals || [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/80" />
      <div
        className="relative w-full max-w-3xl max-h-[min(90vh,920px)] my-4 overflow-y-auto bg-[#0c0c0c] border border-neutral-700 rounded-lg shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}
      >

        {/* ── HEADER ── */}
        <div className={`flex items-start justify-between px-6 py-4 border-b ${tm.border} shrink-0`}>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-neutral-100 truncate flex flex-wrap items-baseline gap-x-2 gap-y-0">
                <a
                  href={companyExternalHref(lead) || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${COMPANY_NAME_LINK_CLASS} text-lg font-semibold`}
                >
                  {lead.company_name}
                </a>
                {isWebSearchOnlyHref(lead) && (
                  <span className="text-[10px] font-normal uppercase tracking-wide text-zinc-500">search</span>
                )}
              </h2>
              <TierBadge tier={lead.priority_tier} />
              {sc.signal_score != null && (
                <span className="inline-flex items-center gap-1">
                  <SignalScoreLabel />
                  <SignalScoreBadge value={sc.signal_score} />
                </span>
              )}
              {sc.overall_score != null && <ScoreNum value={sc.overall_score} />}
              {sc.lead_value_score != null && <ValueNum value={sc.lead_value_score} />}
            </div>
            {lead.procurement_hints?.length > 0 && (
              <div className="mt-1.5">
                <span className="text-[10px] uppercase tracking-wide text-amber-600/90 mr-2">procurement</span>
                <ProcurementHints hints={lead.procurement_hints} className="inline-flex" />
              </div>
            )}
            {gtm && (
              <div className="mt-2 rounded border border-emerald-900/40 bg-emerald-950/25 px-3 py-2 max-w-xl">
                <div className="text-[10px] uppercase tracking-wide text-emerald-600/90 mb-0.5">GTM · robot readiness</div>
                <div className="text-sm text-emerald-100/95 font-medium">{gtm.readiness_label}</div>
                {Array.isArray(gtm.why_now) && gtm.why_now.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5 text-xs text-neutral-400 list-disc list-inside">
                    {gtm.why_now.slice(0, 4).map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                )}
                {gtm.suggested_motion && (
                  <p className="mt-2 text-[11px] text-neutral-500 leading-snug">{gtm.suggested_motion}</p>
                )}
              </div>
            )}
            <div className="mt-2 rounded border border-zinc-800/80 bg-zinc-950/40 px-3 py-2 max-w-xl">
              <div className="text-[10px] uppercase tracking-wide text-zinc-500 mb-1">Rep feedback</div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  disabled={repFbSending || repFbDone}
                  onClick={() => submitRepFeedback('up')}
                  className="text-xs px-2 py-1 rounded border border-zinc-700 text-zinc-300 hover:border-emerald-700 hover:text-emerald-400 disabled:opacity-40"
                >
                  👍 Good lead
                </button>
                <button
                  type="button"
                  disabled={repFbSending || repFbDone}
                  onClick={() => submitRepFeedback('down')}
                  className="text-xs px-2 py-1 rounded border border-zinc-700 text-zinc-300 hover:border-amber-800 hover:text-amber-400 disabled:opacity-40"
                >
                  👎 Off
                </button>
                <span className="text-[10px] text-zinc-600">Wrong company?</span>
                <button
                  type="button"
                  disabled={repFbSending || repFbDone}
                  onClick={() => submitRepFeedback('down', 'wrong_company')}
                  className="text-[10px] px-1.5 py-0.5 rounded border border-zinc-800 text-zinc-500 hover:text-zinc-300 disabled:opacity-40"
                >
                  flag
                </button>
              </div>
              {repFbDone && <p className="text-[11px] text-emerald-500/90 mt-1.5">Thanks — recorded.</p>}
              {repFbErr && <p className="text-[11px] text-red-400/90 mt-1.5">{repFbErr}</p>}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-400">
              {lead.industry && <span className="text-neutral-300">{lead.industry}</span>}
              {city && <span>{city}{state ? `, ${state}` : ''}</span>}
              {emp && <span>{emp.toLocaleString()} employees</span>}
              {site && (
                <a href={site} target="_blank" rel="noreferrer"
                  className="text-cyan-700 hover:text-cyan-400 transition-colors truncate max-w-[12rem]"
                  onClick={e => e.stopPropagation()}>{site.replace(/^https?:\/\//, '')}</a>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-4 shrink-0">
            <button
              onClick={toggleSave}
              className={`btn-ghost text-xs ${saved
                ? 'border-emerald-700 text-emerald-400 hover:border-emerald-500'
                : 'border-neutral-700 text-neutral-500 hover:border-neutral-500'}`}>
              {saved ? '★ saved' : '☆ save'}
            </button>
            <button
              onClick={saveReport}
              disabled={savingReport || reportSaved}
              className={`btn-ghost text-xs ${reportSaved
                ? 'border-emerald-800 text-emerald-500'
                : 'border-neutral-800 text-neutral-400 hover:border-neutral-600'}`}>
              {reportSaved ? '◆ report saved' : savingReport ? '…' : '◇ save report'}
            </button>
            <Link href="/profile" className="btn-ghost text-xs border-neutral-800 text-neutral-400 hover:border-neutral-600">profile</Link>
            <button onClick={onClose}
              className="text-neutral-400 hover:text-neutral-200 transition-colors px-2 py-1 text-sm">
              ✕
            </button>
          </div>
        </div>

        {/* ── TAB BAR ── */}
        <div className="flex items-center gap-0 border-b border-neutral-800 px-4 shrink-0 overflow-x-auto">
          {AI_TABS.map(tab => (
            <button key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2.5 text-xs font-medium transition-colors border-b-2 whitespace-nowrap -mb-px ${
                activeTab === tab
                  ? (tab === 'engagement' ? 'border-cyan-600 text-cyan-400' : 'border-emerald-600 text-emerald-400')
                  : tab === 'engagement'
                  ? 'border-transparent text-cyan-400 hover:text-cyan-300 font-semibold'
                  : 'border-transparent text-neutral-400 hover:text-neutral-300'
              }`}>
              {tab === 'engagement' ? '📋 engagement' : tab}
            </button>
          ))}
        </div>

        {/* ── TAB CONTENT ── */}
        <div className="px-6 py-5 overflow-y-auto flex-1">

          {/* ── STRATEGY tab ── */}
          {activeTab === 'strategy' && (
            <div className="space-y-5">
              {/* intent scores */}
              <div>
                <p className="label mb-3">intent scores</p>
                <div className="grid grid-cols-2 gap-x-10 gap-y-3">
                  <ScoreBar value={sc.lead_value_score ?? 0} label="lead value" />
                  <ScoreBar value={sc.overall_score     ?? 0} label="ML intent" />
                  <ScoreBar value={sc.automation_score  ?? 0} label="automation" />
                  <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
                  <ScoreBar value={sc.expansion_score   ?? 0} label="expansion" />
                  <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
                </div>
                {sc.lead_value_components && (
                  <p className="text-[10px] text-neutral-500 mt-3 leading-relaxed">
                    Value blend: intent {Math.round((sc.lead_value_components.intent_strength || 0) * 100)} ·
                    firmographic {Math.round((sc.lead_value_components.firmographic_strength || 0) * 100)} ·
                    spec {Math.round((sc.lead_value_components.spec_richness || 0) * 100)} ·
                    freshness {Math.round((sc.lead_value_components.timing_freshness || 0) * 100)} ·
                    procurement {Math.round((sc.lead_value_components.procurement_timeline || 0) * 100)}
                  </p>
                )}
              </div>

              {loading && (
                <p className="text-sm text-neutral-400 animate-pulse py-3">generating AI analysis&hellip;</p>
              )}

              <AutomationSpecBlock profile={automationProfile} theme="dashboard" />

              {!loading && strat && um && (
                <div className={`border ${um.border} rounded p-5 space-y-4`}>
                  <div className="flex items-center justify-between">
                    <span className={`badge ${um.border} ${um.text}`}>{um.label}</span>
                    <span className="text-xs text-neutral-400">{Math.round(strat.confidence * 100)}% confidence</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="label block mb-1">who to contact</span>
                      <span className="text-sm font-medium text-emerald-400">{strat.contact_role}</span>
                    </div>
                    <div>
                      <span className="label block mb-1">best channel</span>
                      <span className="text-sm text-neutral-400">{strat.best_channel}</span>
                    </div>
                  </div>
                  <div>
                    <span className="label block mb-1">lead with</span>
                    <p className="text-sm text-emerald-300 leading-relaxed font-medium">{strat.pitch_angle}</p>
                  </div>
                  <div>
                    <span className="label block mb-2">talking points</span>
                    <ul className="space-y-2">
                      {(strat.talking_points || []).map((tp, i) => (
                        <li key={i} className={`flex gap-2 text-sm ${tpColor(tp)}`}>
                          <span className="text-neutral-500 shrink-0 mt-0.5">▸</span>
                          {tp}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className={`border-t ${um.border} pt-4`}>
                    <span className="label block mb-1.5">timing &amp; next steps</span>
                    <p className="text-sm text-cyan-400 leading-relaxed">⏱ {strat.timing_note}</p>
                  </div>
                </div>
              )}

              {!loading && !strat && (
                <p className="text-sm text-neutral-500 border border-neutral-800 rounded px-4 py-3">
                  No strategy available — run the ML Agent first.
                </p>
              )}
            </div>
          )}

          {/* ── ENGAGEMENT tab ── */}
          {activeTab === 'engagement' && (
            <div className="space-y-5">
              {/* Approach Strategy */}
              <div className="border border-cyan-900 rounded-lg p-5 bg-gradient-to-br from-neutral-950 to-neutral-900">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base font-bold text-cyan-400">📋 Recommended Approach</span>
                </div>
                
                {/* Determine best approach based on signals */}
                {(() => {
                  const signals = lead.signals || [];
                  const emp = lead.employee_estimate || null;
                  const hasExpansion = signals.some(s => ['expansion', 'capex', 'ma_activity'].includes(s.signal_type));
                  const hasLabor = signals.some(s => ['labor_shortage', 'job_posting'].includes(s.signal_type));
                  const hasFunding = signals.some(s => s.signal_type === 'funding_round');
                  const hasExec = signals.some(s => s.signal_type === 'strategic_hire');
                  const hotSignals = signals.length >= 3;
                  
                  let approach, reason, contentType;
                  
                  if (hasExpansion && hotSignals) {
                    approach = "Industry-Specific Solution Brief + ROI Model";
                    reason = "Expansion signals indicate active planning phase — they need to see concrete ROI and implementation timeline for new facilities.";
                    contentType = "solution-brief";
                  } else if (hasLabor) {
                    approach = "Problem-Solution Whitepaper";
                    reason = "Labor challenges are immediate pain — demonstrate how automation solves their specific staffing crisis with case studies.";
                    contentType = "whitepaper";
                  } else if (hasFunding && hasExec) {
                    approach = "Executive Briefing + Pilot Proposal";
                    reason = "New funding + leadership = fresh strategic initiatives. Target new execs with high-level vision and quick-win pilot program.";
                    contentType = "executive-brief";
                  } else if (signals.length >= 2) {
                    approach = "Thought Leadership + Industry Benchmarks";
                    reason = "Multiple signals indicate they're researching solutions. Position yourself as the industry expert with data-driven insights.";
                    contentType = "thought-leadership";
                  } else {
                    approach = "Educational Content Series";
                    reason = "Limited signals — build awareness first with valuable, non-salesy content that addresses their industry challenges.";
                    contentType = "educational";
                  }
                  
                  return (
                    <div className="space-y-3">
                      <div className="flex items-start gap-3 bg-neutral-900/50 border border-cyan-800/50 rounded p-4">
                        <span className="text-2xl mt-0.5">🎯</span>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-cyan-300 mb-1">{approach}</p>
                          <p className="text-xs text-neutral-400 leading-relaxed">{reason}</p>
                        </div>
                      </div>
                      
                      {/* Specific Content Recommendations */}
                      <div className="pt-3">
                        <span className="label block mb-2">📝 Specific Content to Create:</span>
                        <div className="space-y-2">
                          {contentType === 'solution-brief' && (
                            <>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-emerald-400 font-semibold">1. Solution Brief:</span>
                                <span className="text-neutral-300"> "How {profile?.robot_match?.[0]?.name || 'Robotics'} Streamlines {lead.industry} Expansion: A {lead.company_name} Implementation Guide"</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-cyan-400 font-semibold">2. ROI Calculator:</span>
                                <span className="text-neutral-300"> Custom model showing payback period for {emp ? `${emp.toLocaleString()}-employee` : 'their'} facilities (12-18 month typical ROI)</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-yellow-400 font-semibold">3. Case Study:</span>
                                <span className="text-neutral-300"> Similar {lead.industry} company that deployed automation during expansion</span>
                              </div>
                            </>
                          )}
                          
                          {contentType === 'whitepaper' && (
                            <>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-emerald-400 font-semibold">1. Whitepaper:</span>
                                <span className="text-neutral-300"> "Solving {lead.industry}'s Labor Crisis: How Automation Fills {signals.find(s => s.signal_type === 'labor_shortage')?.signal_text?.match(/\d+/)?.[0] || '50+'} Open Positions"</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-cyan-400 font-semibold">2. Data Sheet:</span>
                                <span className="text-neutral-300"> Labor cost savings breakdown showing total impact on EBITDA</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-yellow-400 font-semibold">3. Video Demo:</span>
                                <span className="text-neutral-300"> 3-minute walkthrough showing robot deployment in {lead.industry} facility</span>
                              </div>
                            </>
                          )}
                          
                          {contentType === 'executive-brief' && (
                            <>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-emerald-400 font-semibold">1. Executive Briefing:</span>
                                <span className="text-neutral-300"> One-page strategic overview: "Accelerating {lead.company_name}'s Growth with Automation Infrastructure"</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-cyan-400 font-semibold">2. Pilot Proposal:</span>
                                <span className="text-neutral-300"> 90-day proof-of-concept program with clear success metrics and fast deployment</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-yellow-400 font-semibold">3. Industry Report:</span>
                                <span className="text-neutral-300"> "{lead.industry} Automation Trends 2026: What Leading Companies Are Deploying"</span>
                              </div>
                            </>
                          )}
                          
                          {contentType === 'thought-leadership' && (
                            <>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-emerald-400 font-semibold">1. Benchmark Report:</span>
                                <span className="text-neutral-300"> "{lead.industry} Automation Adoption: How {lead.company_name} Compares to Top Performers"</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-cyan-400 font-semibold">2. LinkedIn Article Series:</span>
                                <span className="text-neutral-300"> 5-part series on {lead.industry} operational excellence and automation ROI</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-yellow-400 font-semibold">3. Webinar:</span>
                                <span className="text-neutral-300"> "Future of {lead.industry}: Technology Trends Driving Competitive Advantage"</span>
                              </div>
                            </>
                          )}
                          
                          {contentType === 'educational' && (
                            <>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-emerald-400 font-semibold">1. Educational Guide:</span>
                                <span className="text-neutral-300"> "Complete Guide to {lead.industry} Automation: Technologies, Costs, and Implementation"</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-cyan-400 font-semibold">2. Cost Comparison Tool:</span>
                                <span className="text-neutral-300"> Interactive calculator: Manual operations vs. automated solutions for {lead.industry}</span>
                              </div>
                              <div className="bg-neutral-900/30 rounded px-3 py-2 text-xs">
                                <span className="text-yellow-400 font-semibold">3. FAQ Resource:</span>
                                <span className="text-neutral-300"> "Top 20 Questions {lead.industry} Leaders Ask About Robotics Deployment"</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
              
              {/* Multi-Touch Engagement Sequence */}
              <div className="border border-emerald-900 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base font-bold text-emerald-400">🔄 Trust-Building Sequence</span>
                  <span className="text-xs text-neutral-500">(6-8 week nurture campaign)</span>
                </div>
                
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-cyan-900/30 border border-cyan-700 flex items-center justify-center text-xs font-semibold text-cyan-400">1</div>
                      <div className="w-px h-full bg-neutral-800 mt-2"></div>
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="text-sm font-semibold text-neutral-200 mb-1">Week 1: Value-First Education</p>
                      <p className="text-xs text-neutral-400 mb-2">Send industry report or whitepaper (no pitch, pure value)</p>
                      <div className="bg-neutral-900/50 rounded px-3 py-2 text-xs text-neutral-500">
                        📧 Subject: "[Industry Insight] {lead.industry} Automation Trends Report"<br/>
                        🎯 Goal: Establish expertise, no ask
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-emerald-900/30 border border-emerald-700 flex items-center justify-center text-xs font-semibold text-emerald-400">2</div>
                      <div className="w-px h-full bg-neutral-800 mt-2"></div>
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="text-sm font-semibold text-neutral-200 mb-1">Week 3: Relevant Case Study</p>
                      <p className="text-xs text-neutral-400 mb-2">Share success story from similar company in their industry</p>
                      <div className="bg-neutral-900/50 rounded px-3 py-2 text-xs text-neutral-500">
                        📧 Subject: "How [Similar Company] Solved [Their Pain Point]"<br/>
                        🎯 Goal: Demonstrate real-world results
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-yellow-900/30 border border-yellow-700 flex items-center justify-center text-xs font-semibold text-yellow-400">3</div>
                      <div className="w-px h-full bg-neutral-800 mt-2"></div>
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="text-sm font-semibold text-neutral-200 mb-1">Week 5: Personalized ROI Analysis</p>
                      <p className="text-xs text-neutral-400 mb-2">Send custom ROI model specific to their facility size/industry</p>
                      <div className="bg-neutral-900/50 rounded px-3 py-2 text-xs text-neutral-500">
                        📧 Subject: "ROI Breakdown: Automation for {emp ? `${emp.toLocaleString()}-person` : 'Your'} {lead.industry} Operations"<br/>
                        🎯 Goal: Show financial impact with their numbers
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-violet-900/30 border border-violet-700 flex items-center justify-center text-xs font-semibold text-violet-400">4</div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-neutral-200 mb-1">Week 7: Soft Pilot Offer</p>
                      <p className="text-xs text-neutral-400 mb-2">Invite to low-risk proof-of-concept program (NOW you make the ask)</p>
                      <div className="bg-neutral-900/50 rounded px-3 py-2 text-xs text-neutral-500">
                        📧 Subject: "Quick Question: Would a 90-day pilot make sense?"<br/>
                        🎯 Goal: Convert to conversation after establishing trust
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Key Messaging Themes */}
              <div className="border border-yellow-900 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base font-bold text-yellow-400">💬 Key Messaging Themes</span>
                </div>
                
                <div className="space-y-2">
                  {(() => {
                    const signals = lead.signals || [];
                    const hasLabor = signals.some(s => ['labor_shortage', 'job_posting'].includes(s.signal_type));
                    const hasExpansion = signals.some(s => ['expansion', 'capex'].includes(s.signal_type));
                    const hasFunding = signals.some(s => s.signal_type === 'funding_round');
                    
                    const themes = [];
                    
                    if (hasLabor) {
                      themes.push({
                        icon: '🔴',
                        title: 'Labor Crisis Solution',
                        message: `"We help ${lead.industry} companies eliminate dependency on hard-to-find labor while improving consistency and throughput"`
                      });
                    }
                    
                    if (hasExpansion) {
                      themes.push({
                        icon: '📈',
                        title: 'Scale Without Proportional Headcount',
                        message: `"Expand to new facilities without the traditional hiring challenge — automation scales instantly"`
                      });
                    }
                    
                    if (hasFunding) {
                      themes.push({
                        icon: '💰',
                        title: 'Smart Capital Deployment',
                        message: `"Turn growth capital into competitive moats — automation investments compound over time while labor costs increase indefinitely"`
                      });
                    }
                    
                    themes.push({
                      icon: '⚡',
                      title: 'Speed to Value',
                      message: `"90-day pilots with measurable KPIs — prove ROI before full commitment"`
                    });
                    
                    themes.push({
                      icon: '🎯',
                      title: 'Industry-Specific Expertise',
                      message: `"We've deployed in ${lead.industry} facilities like yours — we understand your unique challenges and constraints"`
                    });
                    
                    return themes.map((theme, i) => (
                      <div key={i} className="bg-neutral-900/30 rounded px-4 py-3">
                        <div className="flex items-start gap-2">
                          <span className="text-lg">{theme.icon}</span>
                          <div className="flex-1">
                            <p className="text-xs font-semibold text-yellow-400 mb-1">{theme.title}</p>
                            <p className="text-xs text-neutral-300 italic leading-relaxed">{theme.message}</p>
                          </div>
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              </div>
              
              {/* Distribution Channels */}
              <div className="border border-blue-900 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-base font-bold text-blue-400">📡 Distribution Channels</span>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-neutral-900/30 rounded px-3 py-3 border border-blue-900/30">
                    <p className="text-xs font-semibold text-blue-400 mb-1">🔗 LinkedIn (Primary)</p>
                    <p className="text-xs text-neutral-400 leading-relaxed">
                      Connect with {strat?.contact_role || 'VP Operations, COO'} → Share articles → Tag in relevant posts → InMail with value
                    </p>
                  </div>
                  
                  <div className="bg-neutral-900/30 rounded px-3 py-3 border border-emerald-900/30">
                    <p className="text-xs font-semibold text-emerald-400 mb-1">📧 Email (Nurture)</p>
                    <p className="text-xs text-neutral-400 leading-relaxed">
                      Warm sequences with educational content → Personalized insights → No hard sells for first 4-6 weeks
                    </p>
                  </div>
                  
                  <div className="bg-neutral-900/30 rounded px-3 py-3 border border-yellow-900/30">
                    <p className="text-xs font-semibold text-yellow-400 mb-1">📰 Industry Publications</p>
                    <p className="text-xs text-neutral-400 leading-relaxed">
                      Sponsor content in {lead.industry} trade magazines → Build brand awareness before direct outreach
                    </p>
                  </div>
                  
                  <div className="bg-neutral-900/30 rounded px-3 py-3 border border-violet-900/30">
                    <p className="text-xs font-semibold text-violet-400 mb-1">🎤 Events/Webinars</p>
                    <p className="text-xs text-neutral-400 leading-relaxed">
                      Host virtual {lead.industry} roundtables → Invite as speaker → Facility tours → Build peer network
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Why This Approach Works */}
              <div className="bg-gradient-to-r from-cyan-950/30 to-emerald-950/30 border border-cyan-900/50 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-sm font-bold text-cyan-400">💡 Why Cold Calling Fails (and This Works)</span>
                </div>
                <div className="space-y-2 text-xs text-neutral-300 leading-relaxed">
                  <p className="flex items-start gap-2">
                    <span className="text-red-400 shrink-0 mt-0.5">✕</span>
                    <span><span className="font-semibold text-neutral-200">Cold calling:</span> Interrupts their day, zero context, feels salesy, 99% rejection rate</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-emerald-400 shrink-0 mt-0.5">✓</span>
                    <span><span className="font-semibold text-neutral-200">Value-first content:</span> They discover YOU when researching solutions, builds trust passively, positions you as expert</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-emerald-400 shrink-0 mt-0.5">✓</span>
                    <span><span className="font-semibold text-neutral-200">Multi-touch nurture:</span> By touch #4, they've seen your name 6-8 times across channels — familiarity = trust</span>
                  </p>
                  <p className="flex items-start gap-2">
                    <span className="text-emerald-400 shrink-0 mt-0.5">✓</span>
                    <span><span className="font-semibold text-neutral-200">Signal-based timing:</span> Their {engagementSignals.length >= 3 ? 'hot signals' : 'signals'} show they're in market RIGHT NOW — strike while iron is hot with relevant solutions</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ── ROBOT MATCH tab ── */}
          {activeTab === 'robot match' && (
            <div className="space-y-4">
              <div className="border border-violet-800/50 rounded-lg p-4 bg-violet-950/20">
                <p className="text-xs font-semibold text-violet-300 uppercase tracking-wide mb-2">
                  Automation spec (signal + industry model)
                </p>
                <p className="text-sm text-neutral-300 mb-3 leading-relaxed">
                  Rule-based fit: deployment context, application areas, and robot categories to emphasize before vendor shortlist.
                </p>
                <AutomationSpecBlock profile={automationProfile} theme="dashboard" />
              </div>

              {loading && <p className="text-sm text-neutral-400 animate-pulse py-3">Loading agent vendor matches&hellip;</p>}
              {!loading && (profile?.robot_match || []).length === 0 && (
                <p className="text-sm text-neutral-300 leading-relaxed">
                  No linked vendor catalog matches from the AI agent yet — use the automation spec above for outreach and discovery.
                </p>
              )}
              {(profile?.robot_match || []).map((robot, i) => (
                <div key={i} className={`border ${i === 0 ? 'border-emerald-900' : 'border-neutral-800'} rounded p-5 space-y-3`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <a href={robot.url} target="_blank" rel="noreferrer"
                        className="text-base font-semibold text-neutral-100 hover:text-emerald-400 transition-colors">
                        {robot.name} ↗
                      </a>
                      {i === 0 && <span className="badge border-emerald-800 text-emerald-400">best match</span>}
                    </div>
                    <span className="label">{robot.tagline}</span>
                  </div>
                  <p className="text-sm text-neutral-300 leading-relaxed">{robot.use_cases?.[0]}</p>
                  {robot.use_cases?.slice(1).map((uc, j) => (
                    <p key={j} className="text-xs text-neutral-300 leading-relaxed">▸ {uc}</p>
                  ))}
                  {robot.roi_stat && (
                    <div className="border border-cyan-900 rounded px-3 py-2">
                      <span className="label block mb-0.5">ROI insight</span>
                      <p className="text-xs text-cyan-400">{robot.roi_stat}</p>
                    </div>
                  )}
                  {(robot.why_now || []).length > 0 && (
                    <div className="space-y-1">
                      <span className="label block">why now</span>
                      {robot.why_now.map((w, j) => (
                        <p key={j} className="text-xs text-amber-500/80">▸ {w}</p>
                      ))}
                    </div>
                  )}
                  <a href={robot.url} target="_blank" rel="noreferrer"
                    className="inline-block text-xs text-emerald-600 hover:text-emerald-400 border border-emerald-900 hover:border-emerald-700 rounded px-3 py-1.5 transition-colors">
                    view {robot.name} product page ↗
                  </a>
                </div>
              ))}
            </div>
          )}

          {/* ── DECISION MAKERS tab ── */}
          {activeTab === 'decision makers' && (
            <div className="space-y-3">
              <p className="text-xs text-neutral-400 mb-4">
                Click any role to search LinkedIn for people at {lead.company_name} with that title.
                These are typical decision-makers and economic buyers for robotics automation deployments.
              </p>
              {loading && <p className="text-sm text-neutral-400 animate-pulse">loading&hellip;</p>}
              {(profile?.decision_makers || []).map((dm, i) => (
                <div key={i} className="flex items-center justify-between border border-neutral-800 rounded px-4 py-3 hover:border-neutral-600 transition-colors group">
                  <div>
                    <p className="text-sm font-medium text-neutral-200">{dm.title}</p>
                    <p className="text-xs text-neutral-400">{dm.dept} department</p>
                  </div>
                  <div className="flex gap-2">
                    <a href={dm.linkedin_search} target="_blank" rel="noreferrer"
                      onClick={e => e.stopPropagation()}
                      className="badge border-blue-900 text-blue-400 hover:border-blue-700 transition-colors">
                      Find on LinkedIn ↗
                    </a>
                  </div>
                </div>
              ))}
              {!loading && (profile?.intel_links || []).length > 0 && (
                <div className="mt-5 pt-5 border-t border-neutral-800">
                  <p className="label mb-3">company LinkedIn pages</p>
                  {(profile.intel_links || [])
                    .filter(l => l.icon === 'li')
                    .map((l, i) => (
                      <a key={i} href={l.url} target="_blank" rel="noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="inline-block mr-2 mb-2 badge border-blue-900 text-blue-400 hover:border-blue-700 transition-colors">
                        {l.label} ↗
                      </a>
                    ))}
                </div>
              )}
            </div>
          )}

          {/* ── INTEL tab ── */}
          {activeTab === 'intel' && (
            <div className="space-y-5">
              {loading && <p className="text-sm text-neutral-400 animate-pulse">loading intelligence&hellip;</p>}
              
              {!loading && (
                <>
                  {/* 1. Competitive Intelligence */}
                  <div className="border border-violet-900 rounded p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-violet-400">🏆 Competitive Intelligence</span>
                    </div>
                    <div className="space-y-2">
                      {profile?.competitive_intel?.current_vendors ? (
                        <div className="text-xs">
                          <span className="label">Current vendors:</span>
                          <p className="text-neutral-300 mt-1">{profile.competitive_intel.current_vendors}</p>
                        </div>
                      ) : (
                        <div className="text-xs">
                          <span className="label">Current vendors:</span>
                          <p className="text-neutral-500 mt-1">No competitive vendor data detected in signals</p>
                        </div>
                      )}
                      
                      {lead.industry && (
                        <div className="text-xs border-t border-neutral-800 pt-2">
                          <span className="label">Industry benchmark:</span>
                          <p className="text-cyan-400 mt-1">
                            {lead.industry === 'Logistics' && '67% of peer companies adopted warehouse AMRs in 2025'}
                            {lead.industry === 'Hospitality' && '43% of hotel chains deployed service robots in 2025'}
                            {lead.industry === 'Food Service' && '38% of QSR chains automated BOH operations in 2025'}
                            {lead.industry === 'Healthcare' && '52% of hospitals deployed clinical logistics robots in 2025'}
                            {lead.industry === 'Food Processing & Manufacturing' && '71% of food plants cite EOL palletizing as #1 automation priority in 2025'}
                            {lead.industry === 'CPG & Consumer Goods' && '64% of CPG manufacturers deployed robotic case packing or palletizing in 2025'}
                            {lead.industry === 'Contract Manufacturing' && 'Co-packers adopting flexible EOL robots 2× faster than captive plants — high changeover ROI'}
                            {!['Logistics', 'Hospitality', 'Food Service', 'Healthcare', 'Food Processing & Manufacturing', 'CPG & Consumer Goods', 'Contract Manufacturing'].includes(lead.industry) && 'Automation adoption accelerating across industry'}
                          </p>
                        </div>
                      )}
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Competitive pressure:</span>
                        <p className="text-amber-400 mt-1">
                          {sc.overall_score >= 75 && 'HIGH - Competitors likely automating; risk falling behind'}
                          {sc.overall_score >= 45 && sc.overall_score < 75 && 'MEDIUM - Some competitive movement expected'}
                          {sc.overall_score < 45 && 'LOW - Early mover opportunity'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 2. Decision Maker Intelligence */}
                  <div className="border border-blue-900 rounded p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-blue-400">👔 Decision Maker Intelligence</span>
                    </div>
                    <div className="space-y-2">
                      {(lead.signals || []).filter(s => s.signal_type === 'strategic_hire').length > 0 ? (
                        <>
                          <div className="text-xs">
                            <span className="label">Recent executive hires:</span>
                            {(lead.signals || []).filter(s => s.signal_type === 'strategic_hire').slice(0, 2).map((s, i) => (
                              <p key={i} className="text-emerald-400 mt-1">• {s.text}</p>
                            ))}
                          </div>
                          <div className="text-xs border-t border-neutral-800 pt-2">
                            <span className="label">Opportunity window:</span>
                            <p className="text-cyan-400 mt-1">
                              ⚡ New executives typically plan initiatives in first 90 days - strike now!
                            </p>
                          </div>
                        </>
                      ) : (
                        <div className="text-xs">
                          <span className="label">Recent executive hires:</span>
                          <p className="text-neutral-500 mt-1">No recent C-suite/VP hires detected in signals</p>
                        </div>
                      )}
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Primary decision makers:</span>
                        <div className="mt-1 space-y-1">
                          {lead.industry === 'Logistics' && (
                            <>
                              <p className="text-neutral-300">• VP Operations / COO (budget owner)</p>
                              <p className="text-neutral-300">• Director Warehouse Operations (technical buyer)</p>
                            </>
                          )}
                          {lead.industry === 'Hospitality' && (
                            <>
                              <p className="text-neutral-300">• VP Operations / COO (budget owner)</p>
                              <p className="text-neutral-300">• Director F&B / Guest Services (end user)</p>
                            </>
                          )}
                          {lead.industry === 'Food Service' && (
                            <>
                              <p className="text-neutral-300">• VP Operations (budget owner)</p>
                              <p className="text-neutral-300">• Director Kitchen Operations (technical buyer)</p>
                            </>
                          )}
                          {lead.industry === 'Food Processing & Manufacturing' && (
                            <>
                              <p className="text-neutral-300">• VP / Director Manufacturing (budget owner)</p>
                              <p className="text-neutral-300">• Plant Manager / Engineering Director (technical buyer)</p>
                              <p className="text-neutral-300">• Director EOL / Packaging Engineering (project lead)</p>
                            </>
                          )}
                          {lead.industry === 'CPG & Consumer Goods' && (
                            <>
                              <p className="text-neutral-300">• VP / Director Engineering & Automation (budget owner)</p>
                              <p className="text-neutral-300">• Plant Manager / Operations Director (technical buyer)</p>
                              <p className="text-neutral-300">• Packaging Engineering Manager (project lead)</p>
                            </>
                          )}
                          {lead.industry === 'Contract Manufacturing' && (
                            <>
                              <p className="text-neutral-300">• COO / VP Operations (budget owner)</p>
                              <p className="text-neutral-300">• Director Engineering (technical buyer)</p>
                              <p className="text-neutral-300">• Continuous Improvement Manager (internal champion)</p>
                            </>
                          )}
                          {!['Logistics', 'Hospitality', 'Food Service', 'Food Processing & Manufacturing', 'CPG & Consumer Goods', 'Contract Manufacturing'].includes(lead.industry) && (
                            <>
                              <p className="text-neutral-300">• COO / VP Operations (budget owner)</p>
                              <p className="text-neutral-300">• Operations Director (technical buyer)</p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 3. Timing Intelligence */}
                  <div className="border border-amber-900 rounded p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-amber-400">⏰ Timing Intelligence</span>
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs">
                        <span className="label">Budget cycle:</span>
                        <p className="text-neutral-300 mt-1">
                          {new Date().getMonth() >= 9 && new Date().getMonth() <= 11 && 'Q4 - Budget planning season (best time to position for next fiscal year)'}
                          {new Date().getMonth() >= 0 && new Date().getMonth() <= 2 && 'Q1 - Fresh budgets released, high approval rate for strategic initiatives'}
                          {new Date().getMonth() >= 3 && new Date().getMonth() <= 5 && 'Q2 - Mid-year review period, competitive for remaining funds'}
                          {new Date().getMonth() >= 6 && new Date().getMonth() <= 8 && 'Q3 - Use-it-or-lose-it budget window opening'}
                        </p>
                      </div>
                      
                      {(lead.signals || []).some(s => s.signal_type === 'expansion') && (
                        <div className="text-xs border-t border-neutral-800 pt-2">
                          <span className="label">Expansion timeline:</span>
                          <p className="text-emerald-400 mt-1">
                            🚀 Active expansion detected - automation typically approved 4-6 months before facility opens
                          </p>
                        </div>
                      )}
                      
                      {(lead.signals || []).some(s => s.signal_type === 'funding_round') && (
                        <div className="text-xs border-t border-neutral-800 pt-2">
                          <span className="label">Funding window:</span>
                          <p className="text-violet-400 mt-1">
                            💰 Recent funding detected - capital available for strategic initiatives (12-18 month deployment window)
                          </p>
                        </div>
                      )}
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Best contact timing:</span>
                        <p className="text-cyan-400 mt-1">
                          {new Date().getDay() >= 1 && new Date().getDay() <= 3 && '📅 Tue-Thu mornings (9-11am) best for ops leaders'}
                          {new Date().getDay() === 0 || new Date().getDay() === 6 && '📅 Wait for weekday - Tue-Thu mornings best'}
                          {new Date().getDay() === 4 && '📅 Thursday morning good, but Tue-Wed optimal for ops leaders'}
                          {new Date().getDay() === 5 && '📅 Friday avoid - Tue-Thu mornings best for ops leaders'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 4. Risk/Readiness Scoring */}
                  <div className="border border-red-900 rounded p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-red-400">⚠️ Risk & Readiness Assessment</span>
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs">
                        <span className="label">Automation maturity:</span>
                        <p className={`mt-1 ${
                          (lead.signals || []).some(s => s.signal_type === 'automation_intent') ? 'text-emerald-400' :
                          (lead.signals || []).some(s => s.signal_type === 'capex') ? 'text-cyan-400' :
                          'text-amber-400'
                        }`}>
                          {(lead.signals || []).some(s => s.signal_type === 'automation_intent') && '✅ HIGH - Active automation initiatives detected'}
                          {!(lead.signals || []).some(s => s.signal_type === 'automation_intent') && (lead.signals || []).some(s => s.signal_type === 'capex') && '⚡ MEDIUM - CapEx spending indicates investment readiness'}
                          {!(lead.signals || []).some(s => s.signal_type === 'automation_intent') && !(lead.signals || []).some(s => s.signal_type === 'capex') && '⚠️ LOW - No automation signals; requires education on ROI'}
                        </p>
                      </div>
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Labor pain severity:</span>
                        <p className={`mt-1 ${sc.labor_pain_score >= 70 ? 'text-red-400' : sc.labor_pain_score >= 40 ? 'text-amber-400' : 'text-neutral-400'}`}>
                          {sc.labor_pain_score >= 70 && '🔴 CRITICAL - Acute labor shortage driving urgency'}
                          {sc.labor_pain_score >= 40 && sc.labor_pain_score < 70 && '🟡 MODERATE - Labor challenges present but not crisis-level'}
                          {sc.labor_pain_score < 40 && '🟢 LOW - Limited labor pain signals detected'}
                        </p>
                      </div>
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Deal complexity:</span>
                        <p className="text-neutral-300 mt-1">
                          {emp && emp >= 10000 && '🏢 ENTERPRISE - Long sales cycle (9-18 months), multiple stakeholders, procurement process'}
                          {emp && emp >= 1000 && emp < 10000 && '🏭 MID-MARKET - Moderate cycle (4-9 months), executive sponsorship required'}
                          {emp && emp < 1000 && '🏪 SMB - Fast cycle (1-4 months), owner/operator decision'}
                          {!emp && '📊 UNKNOWN - Gather company size to estimate sales cycle'}
                        </p>
                      </div>
                      
                      <div className="text-xs border-t border-neutral-800 pt-2">
                        <span className="label">Technical risk:</span>
                        <p className="text-cyan-400 mt-1">
                          {lead.industry === 'Logistics' && '✅ LOW - Mature automation category with proven ROI'}
                          {lead.industry === 'Hospitality' && '⚠️ MEDIUM - Emerging category, emphasize case studies'}
                          {lead.industry === 'Food Service' && '⚡ MEDIUM - Growing adoption, highlight health/labor benefits'}
                          {lead.industry === 'Food Processing & Manufacturing' && '✅ LOW - Palletizing & EOL robotics are fully proven; ROI payback typically 12–24 months'}
                          {lead.industry === 'CPG & Consumer Goods' && '✅ LOW - Case packing and palletizing well-established; focus on changeover speed and uptime SLAs'}
                          {lead.industry === 'Contract Manufacturing' && '⚡ MEDIUM - High ROI but changeover complexity is a key objection; lead with flexibility story'}
                          {!['Logistics', 'Hospitality', 'Food Service', 'Food Processing & Manufacturing', 'CPG & Consumer Goods', 'Contract Manufacturing'].includes(lead.industry) && '⚠️ ASSESS - Evaluate automation maturity in industry vertical'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Research Links */}
                  {(profile?.intel_links || []).length > 0 && (
                    <div className="border border-neutral-800 rounded p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-sm font-semibold text-neutral-400">🔗 Research Links</span>
                      </div>
                      <div className="space-y-2">
                        {(profile?.intel_links || []).map((link, i) => (
                          <a key={i} href={link.url} target="_blank" rel="noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="flex items-center justify-between border border-neutral-800 rounded px-3 py-2 hover:border-neutral-600 transition-colors group text-xs">
                            <span className="text-neutral-300 group-hover:text-white transition-colors">{link.label}</span>
                            <span className="text-neutral-500 group-hover:text-neutral-300">↗</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* ── SIGNALS tab ── */}
          {activeTab === 'signals' && (() => {
            const allSigs = (profile?.signals?.length ? profile.signals : lead.signals) || [];
            const showSigs = topSignalsForDisplay(allSigs, MAX_SIGNALS_DISPLAY);
            const total = lead.signal_count || profile?.signal_count || allSigs.length || 0;
            return (
            <div className="space-y-2">
              <p className="label mb-1">signals &middot; {total}</p>
              {total > MAX_SIGNALS_DISPLAY && (
                <p className="text-[11px] text-neutral-500 mb-2">
                  Showing top {MAX_SIGNALS_DISPLAY} by weighted score ({total - MAX_SIGNALS_DISPLAY} more not listed).
                </p>
              )}
              {showSigs.map((s, i) => (
                <div key={i} className="flex items-start gap-3 border border-neutral-800 rounded px-4 py-3">
                  <SignalBadge type={s.signal_type} />
                  <span className="text-sm text-neutral-400 flex-1 leading-relaxed">{s.text || s.raw_text}</span>
                  <div className="shrink-0 flex flex-col items-end gap-1">
                    <span className={`text-xs font-mono tabular-nums ${
                      (s.strength || 0) >= 0.7 ? 'text-emerald-500'
                      : (s.strength || 0) >= 0.4 ? 'text-cyan-500'
                      : 'text-neutral-400'
                    }`}>{((s.strength || 0) * 100).toFixed(0)}%</span>
                    {s.source_url && (
                      <a href={s.source_url} target="_blank" rel="noreferrer"
                        className="text-[10px] text-cyan-800 hover:text-cyan-600">src ↗</a>
                    )}
                  </div>
                </div>
              ))}
              {(allSigs.length === 0) && (
                <p className="text-sm text-neutral-500">No signals recorded yet.</p>
              )}
            </div>
            );
          })()}

        </div>
      </div>
    </div>
  );
}

// -- Intelligence search panel -----------------------------------------------
function IntelSearchPanel({ onOpenLead, canPerformAction, trackUsage, showPaywall }) {
  const searchRef = useRef(null);
  const [open,     setOpen]     = useState(true);
  const [query,    setQuery]    = useState('');
  const [category, setCategory] = useState(null);
  const [results,  setResults]  = useState(null);
  const [loading,  setLoading]  = useState(false);

  // '/' keyboard shortcut to focus search
  useEffect(() => {
    function onKey(e) {
      if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        if (!open) setOpen(true);
        setTimeout(() => searchRef.current?.focus(), 50);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  async function runSearch(q, cat) {
    // Check usage limit before searching
    if (!canPerformAction()) {
      showPaywall();
      return;
    }
    
    setLoading(true);
    setResults(null);
    try {
      const params = new URLSearchParams();
      if (q && q.trim())  params.set('q', q.trim());
      if (cat)            params.set('category', cat);
      params.set('limit', '30');
      const r = await fetch(`${API}/api/search?${params}`, liveFetchInit());
      if (r.ok) {
        setResults(await r.json());
        trackUsage(); // Track successful search
      }
    } catch {}
    setLoading(false);
  }

  function selectCategory(key) {
    const next = category === key ? null : key;
    setCategory(next);
    if (next || query.trim()) runSearch(query, next || null);
    else setResults(null);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim() || category) runSearch(query, category);
  }

  function clearAll() {
    setQuery('');
    setCategory(null);
    setResults(null);
  }

  return (
    <div className="mb-6 border border-neutral-800 rounded">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs hover:bg-neutral-900/40 transition-colors">
        <span className="flex items-center gap-2">
          <span className="text-cyan-400">&#8855; Intelligence Search</span>
          <span className="text-neutral-400 hidden sm:inline">&mdash; find buyers by investment activity, M&A, labor trends &amp; verticals</span>
          <span className="text-neutral-800 text-[10px] hidden md:inline">press / to focus</span>
        </span>
        <span className="text-neutral-500">{open ? '&#9650;' : '&#9660;'}</span>
      </button>

      {open && (
        <div className="border-t border-neutral-800 px-4 pb-5 pt-4 space-y-4">
          {/* category grid */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <p className="label text-cyan-400">quick search by category</p>
              <span className="text-[9px] text-neutral-600">🎯 Pre-configured signal searches</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {SEARCH_CATEGORIES.map(cat => (
                <button key={cat.key} onClick={() => selectCategory(cat.key)}
                  className={`tab ${
                    category === cat.key
                      ? 'border-cyan-600 text-cyan-300'
                      : 'border-neutral-700 text-cyan-400 hover:border-cyan-500 hover:text-cyan-300'
                  }`}>
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* free-text input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input ref={searchRef} type="text" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="/ search — company name, keyword, or signal type..."
              className="flex-1 bg-neutral-900 border border-neutral-600 rounded px-3 py-2 text-sm
                         text-neutral-100 placeholder-neutral-400
                         focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-900 focus:text-white transition-colors" />
            <button type="submit"
              className="btn border-cyan-800 text-cyan-400 hover:border-cyan-600 hover:text-cyan-300 shrink-0">
              &#8853; search
            </button>
            {(query || category || results) && (
              <button type="button" onClick={clearAll}
                className="btn border-neutral-800 text-neutral-500 hover:text-neutral-300 shrink-0">
                clear
              </button>
            )}
          </form>

          {/* loading */}
          {loading && (
            <p className="text-sm text-neutral-400 animate-pulse">searching signals&hellip;</p>
          )}

          {/* results */}
          {!loading && results && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm font-medium text-neutral-300">
                  {results.total} result{results.total !== 1 ? 's' : ''}
                </span>
                {results.category_label && (
                  <span className="badge border-cyan-800 text-cyan-400">{results.category_label}</span>
                )}
                {results.query && (
                  <span className="text-sm text-neutral-400">matching &ldquo;{results.query}&rdquo;</span>
                )}
              </div>

              {results.total === 0 ? (
                <p className="text-sm text-neutral-400 border border-neutral-800 rounded px-3 py-3">
                  No results found. Try a different category, or type a company name like &ldquo;Marriott&rdquo; or a keyword like &ldquo;AMR&rdquo;.
                </p>
              ) : (
                <div className="space-y-2">
                  {results.results.map(r => (
                    <div key={r.id}
                      className="border border-neutral-800 rounded px-4 py-3 hover:border-neutral-600 transition-colors group overflow-hidden min-w-0">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <a
                            href={companyExternalHref(r) || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`${COMPANY_NAME_LINK_CLASS} text-base font-semibold`}
                          >
                            {r.company_name}
                          </a>
                          {r.industry && (
                            <span className="label text-neutral-400">{r.industry}</span>
                          )}
                          {r.location_city && (
                            <span className="label text-neutral-500">
                              {r.location_city}{r.location_state ? `, ${r.location_state}` : ''}
                            </span>
                          )}
                          {r.match_source === 'name' && !r.matched_signals?.length && (
                            <span className="badge border-neutral-700 text-neutral-400">name match</span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <ScoreNum value={r.overall_score} />
                          <button onClick={() => onOpenLead && onOpenLead(r)}
                            className="text-xs text-cyan-500 hover:text-cyan-300 transition-colors">
                            view &#8594;
                          </button>
                        </div>
                      </div>
                      {r.matched_signals?.length > 0 && (
                        <div className="space-y-1.5 mt-1 min-w-0">
                          {r.matched_signals.map((s, i) => (
                            <div key={i} className="flex items-start gap-2 min-w-0">
                              <SignalBadge type={s.signal_type} />
                              <PlainTextWithSourceLinks
                                text={s.signal_text}
                                className="text-xs text-neutral-300 flex-1 min-w-0 leading-relaxed"
                              />
                              <span className={`shrink-0 text-xs font-mono tabular-nums ${
                                s.strength >= 0.7 ? 'text-emerald-400'
                                : s.strength >= 0.4 ? 'text-cyan-500'
                                : 'text-neutral-400'
                              }`}>{(s.strength * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// -- Paywall Modal -----------------------------------------------------------
function PaywallModal({ isOpen, onClose, usageCount, limit }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-neutral-950 border-2 border-emerald-700 rounded-lg max-w-lg w-full p-8" onClick={e => e.stopPropagation()}>
        <div className="text-center space-y-6">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-900/50 to-cyan-900/50 flex items-center justify-center text-3xl">
              🚀
            </div>
          </div>

          {/* Headline */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">You've Discovered the Power!</h2>
            <p className="text-neutral-400 text-sm">
              You've used all <span className="text-emerald-400 font-semibold">{limit} free searches</span>. 
              Sign up to unlock unlimited searches, save companies, and build your sales strategy.
            </p>
          </div>

          {/* Features list */}
          <div className="border border-neutral-800 rounded-lg p-4 text-left space-y-3">
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">With a free account you get:</p>
            <div className="space-y-2">
              <div className="flex items-start gap-2 text-sm">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span className="text-neutral-300">Unlimited searches & company matching</span>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span className="text-neutral-300">Save companies and build target lists</span>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span className="text-neutral-300">Generate outreach strategies with AI</span>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span className="text-neutral-300">Access daily strategy briefs</span>
              </div>
            </div>
          </div>

          {/* Tier comparison hint */}
          <div className="text-xs text-neutral-600 bg-neutral-900/50 border border-neutral-800 rounded p-3">
            💎 <span className="text-cyan-400">Professional</span> and <span className="text-yellow-400">Premium</span> tiers 
            unlock advanced features like API access, custom integrations, and priority support.
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3">
            <Link href="/login" 
              className="block w-full py-3 px-6 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded transition-colors text-center">
              Sign Up →
            </Link>
            <button onClick={onClose}
              className="block w-full py-2 px-6 border border-neutral-700 hover:border-neutral-500 text-neutral-400 hover:text-neutral-300 rounded transition-colors">
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// -- main page --------------------------------------------------------------
export default function Dashboard() {
  const { session } = useAuth();
  const [leads, setLeads]         = useState([]);
  const [summary, setSummary]     = useState({});
  const [health, setHealth]       = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [expanded, setExpanded]         = useState({});
  const [collapsedSections, setCollapsedSections] = useState({});
  const [lastRefresh, setLast]    = useState(null);
  const [resetting, setResetting] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [savedIds, setSavedIds] = useState(new Set());
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [liveSignals, setLiveSignals] = useState([]);

  // Usage tracking and tier management
  const [usageCount, setUsageCount] = useState(0);
  const [showPaywall, setShowPaywall] = useState(false);
  const [userTier, setUserTier] = useState('free'); // free, professional, premium
  const FREE_LIMIT = 5;

  // Load usage count on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('rfr_usage_count');
      setUsageCount(parseInt(stored || '0', 10));
    } catch {}
  }, []);

  // Dev / opt-in: log access_token for API testing (curl). Add ?debug_auth=1 or use npm run dev.
  useEffect(() => {
    if (typeof window === 'undefined' || !supabase) return;
    const debug =
      process.env.NODE_ENV === 'development' ||
      new URLSearchParams(window.location.search).get('debug_auth') === '1';
    if (!debug) return;

    (async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error('[debug_auth] session error:', error.message);
        return;
      }
      const accessToken = data.session?.access_token;
      if (accessToken) {
        console.info('[debug_auth] access_token (for Authorization: Bearer …):', accessToken);
      } else {
        console.info('[debug_auth] no session — sign in first');
      }
    })();
  }, []);

  // Check if user can perform action
  function canPerformAction() {
    // Signed-in users can always perform actions (tier determines features)
    if (session) return true;
    // Anonymous users have a limit
    return usageCount < FREE_LIMIT;
  }

  // Track usage for anonymous users
  function trackUsage() {
    if (session) return; // Don't track signed-in users
    const newCount = usageCount + 1;
    setUsageCount(newCount);
    localStorage.setItem('rfr_usage_count', newCount.toString());
    if (newCount >= FREE_LIMIT) {
      setShowPaywall(true);
    }
  }

  // load saved company IDs from localStorage on mount
  useEffect(() => {
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
      setSavedIds(new Set((store.companies || []).map(c => c.id)));
    } catch {}
  }, []);

  // Merge cloud-saved companies when signed in (persistence via /api/user/saved)
  useEffect(() => {
    if (!session?.access_token) return;
    (async () => {
      try {
        const res = await fetch(`${API}/api/user/saved`, liveFetchInit({
          headers: { ...authHeader(session.access_token) },
        }));
        if (!res.ok) return;
        const rows = await res.json();
        if (!Array.isArray(rows) || rows.length === 0) return;
        setSavedIds((prev) => {
          const next = new Set(prev);
          rows.forEach((r) => next.add(r.company_id));
          return next;
        });
        try {
          const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
          if (!store.companies) store.companies = [];
          const byId = new Map(store.companies.map((c) => [c.id, c]));
          for (const r of rows) {
            if (!byId.has(r.company_id)) {
              byId.set(r.company_id, {
                id: r.company_id,
                name: r.company_name,
                industry: r.industry,
                score: r.score ?? 0,
                tier: r.tier,
                saved_at: r.saved_at,
                website: r.website,
              });
            }
          }
          store.companies = [...byId.values()];
          localStorage.setItem('rfr_saved', JSON.stringify(store));
        } catch {
          /* ignore */
        }
      } catch (e) {
        console.error('load saved companies', e);
      }
    })();
  }, [session?.access_token]);

  async function quickSave(lead) {
    if (lead.id == null) return;
    const alreadySaved = savedIds.has(lead.id);
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[],"lists":[]}');
      if (!store.companies) store.companies = [];
      if (alreadySaved) {
        store.companies = store.companies.filter((c) => c.id !== lead.id);
      } else {
        store.companies.push({
          id: lead.id,
          name: lead.company_name,
          industry: lead.industry,
          score: lead.score?.overall_score ?? 0,
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

    if (session?.access_token) {
      try {
        if (alreadySaved) {
          const res = await fetch(`${API}/api/user/saved/${lead.id}`, liveFetchInit({
            method: 'DELETE',
            headers: { ...authHeader(session.access_token) },
          }));
          if (!res.ok && res.status !== 404) {
            const t = await res.text().catch(() => '');
            console.error('unsave company', res.status, t);
          }
        } else {
          const res = await fetch(`${API}/api/user/saved`, liveFetchInit({
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
            body: JSON.stringify({
              company_id: lead.id,
              company_name: lead.company_name,
              industry: lead.industry ?? null,
              tier: lead.priority_tier ?? null,
              score: lead.score?.overall_score ?? null,
              website: lead.website ?? null,
              notes: null,
            }),
          }));
          if (!res.ok) {
            const t = await res.text().catch(() => '');
            console.error('save company', res.status, t);
          }
        }
      } catch (e) {
        console.error('quickSave api', e);
      }
    }
  }

  // filter state
  const [search, setSearch]           = useState('');
  const [tier, setTier]               = useState('ALL');
  const [industry, setIndustry]       = useState('All');
  const [minScore, setMinScore]       = useState(0);
  const [sigType, setSigType]         = useState('');
  const [excludeJunk, setExcludeJunk] = useState(true);
  const [sort, setSort]               = useState('score');

  const buildQuery = useCallback(() => {
    const p = new URLSearchParams();
    p.set('limit', '50');
    p.set('exclude_junk', excludeJunk);
    p.set('min_score', minScore);
    // Backend only knows score | name | signals — lead_value is sorted client-side after fetch
    p.set('sort', sort === 'lead_value' ? 'score' : sort);
    if (tier !== 'ALL')     p.set('tier', tier);
    if (industry !== 'All') p.set('industry', industry);
    if (sigType)            p.set('signal_type', sigType);
    return p.toString();
  }, [tier, industry, minScore, sigType, excludeJunk, sort]);

  // Fetch live signals for ticker
  const fetchLiveSignals = useCallback((leadsData) => {
    // Extract signals from leads already fetched — no extra API call needed
    const signals = [];
    (leadsData || []).forEach(lead => {
      if (lead.signals && lead.signals.length > 0) {
        lead.signals.slice(0, 2).forEach(sig => {
          signals.push({
            company: lead.company_name,
            type: sig.signal_type || 'news',
            industry: lead.industry,
            lead: lead,
          });
        });
      }
    });
    setLiveSignals(signals.slice(0, 15));
  }, []);

  const fetchData = useCallback(async () => {
    const controller = new AbortController();
    const DASHBOARD_FETCH_MS = 55000;
    const tid = setTimeout(() => controller.abort(), DASHBOARD_FETCH_MS);
    try {
      const init = { signal: controller.signal };
      const [leadsRes, summaryRes, healthRes] = await Promise.all([
        fetch(`${API}/api/leads?${buildQuery()}`, liveFetchInit(init)),
        fetch(`${API}/api/leads/summary?exclude_junk=${excludeJunk}&cb=${Date.now()}`, liveFetchInit(init)),
        fetch(`${API}/api/scraper-health`, liveFetchInit(init)),
      ]);
      if (!leadsRes.ok) {
        let hint = await leadsRes.text().catch(() => '');
        try {
          const j = JSON.parse(hint);
          if (j.detail != null) {
            hint = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
          }
        } catch {
          /* keep raw body */
        }
        setError(
          hint
            ? `API ${leadsRes.status}: ${hint.slice(0, 280)}`
            : `API ${leadsRes.status}: ${leadsRes.statusText}. Check that FastAPI is running and DATABASE_URL is correct.`,
        );
        setLeads([]);
      } else {
        const raw = await leadsRes.text();
        if (raw.trimStart().startsWith('<')) {
          setError(
            'API returned a web page instead of JSON (wrong API host). The UI must call the FastAPI origin (e.g. https://ready-2-robot.fly.dev), not the static marketing host.',
          );
          setLeads([]);
        } else {
          const leadsData = JSON.parse(raw);
          setLeads(leadsData);
          setError(null);
          fetchLiveSignals(leadsData);
        }
      }
      if (summaryRes.ok) {
        const st = await summaryRes.text();
        if (!st.trimStart().startsWith('<')) {
          try {
            setSummary(JSON.parse(st));
          } catch {
            /* ignore */
          }
        }
      }
      if (healthRes.ok) {
        const ht = await healthRes.text();
        if (!ht.trimStart().startsWith('<')) {
          try {
            setHealth(JSON.parse(ht));
          } catch {
            /* ignore */
          }
        }
      }
    } catch (e) {
      if (e?.name === 'AbortError') {
        setError(
          'Request timed out waiting for the API (55s). The server may be cold or overloaded — refresh or try again.',
        );
      } else {
        setError(
          'Cannot reach API. For localhost:3000, run FastAPI on :8000 (next dev proxies /api → :8000). ' +
            'Command: python -m uvicorn app.main:app --reload',
        );
      }
    } finally {
      clearTimeout(tid);
      setLoading(false);
      setLast(new Date().toLocaleTimeString());
    }
  }, [buildQuery, excludeJunk, fetchLiveSignals]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    const t = setInterval(fetchData, 300_000);
    return () => clearInterval(t);
  }, [fetchData]);

  // Auto-open AI Analysis modal when coming from profile page (?analyze=ID)
  useEffect(() => {
    if (typeof window === 'undefined' || leads.length === 0) return;
    const params = new URLSearchParams(window.location.search);
    const analyzeId = params.get('analyze');
    if (!analyzeId) return;
    const found = leads.find(l => l.id === parseInt(analyzeId, 10));
    if (found) {
      setSelectedLead(found);
      // Clean the URL without navigation
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [leads]);

  const filtered = leads.filter(l =>
    !isLikelyJunkDisplayName(l.company_name) &&
    (!search || (l.company_name || '').toLowerCase().includes(search.toLowerCase()))
  );

  const sortedForUi = useMemo(() => {
    if (sort !== 'lead_value') return filtered;
    return [...filtered].sort(
      (a, b) => (b.score?.lead_value_score ?? 0) - (a.score?.lead_value_score ?? 0),
    );
  }, [filtered, sort]);

  // Free tier: limit to 5 leads for non-logged-in users
  const displayedLeads = !session ? sortedForUi.slice(0, 5) : sortedForUi;

  async function handleResetAll() {
    setResetting(true);
    await fetch(`${API}/api/scraper-health/reset-all`, liveFetchInit({ method: 'POST' }));
    await fetchData();
    setResetting(false);
  }

  function handleOpenFromSearch(searchResult) {
    // Try to find the full cached lead first
    const found = leads.find(l => l.id === searchResult.id);
    if (found) {
      setSelectedLead(found);
    } else {
      // Construct minimal lead for the modal from search result
      const tier = searchResult.overall_score >= 75 ? 'HOT'
                 : searchResult.overall_score >= 45 ? 'WARM' : 'COLD';
      setSelectedLead({
        ...searchResult,
        priority_tier: tier,
        score: {
          overall_score:    searchResult.overall_score,
          automation_score: 0,
          labor_pain_score: 0,
          expansion_score:  0,
          market_fit_score: 0,
        },
        signals: (searchResult.matched_signals || []).map(s => ({
          signal_type: s.signal_type,
          strength:    s.strength,
          raw_text:    s.signal_text,
          source_url:  '',
        })),
        signal_count: searchResult.matched_signals?.length || 0,
      });
    }
  }

  const openCircuits = health?.circuit_open_urls?.length ?? 0;

  return (
    <>
      <Head>
        <title>Automation Projects Ready For Robots · Signal Intelligence</title>
        <meta name="description" content="Lead intelligence dashboard — automation projects with buying signals." />
      </Head>
      <div className="rr-theme rr-page-wrap text-[15px] sm:text-base antialiased [font-feature-settings:'ss01'_1,'cv01'_1]">

      {/* Paywall Modal */}
      <PaywallModal 
        isOpen={showPaywall} 
        onClose={() => setShowPaywall(false)}
        usageCount={usageCount}
        limit={FREE_LIMIT}
      />

      {selectedLead && (
        <AIAnalysisModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onSaveToggle={() => {
            try {
              const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
              setSavedIds(new Set((store.companies || []).map(c => c.id)));
            } catch {}
          }}
        />
      )}

      {/* Top nav — docs/design/dashboard_design.html (inner centered to max-w main column) */}
      <header className="rr-topnav w-full">
        <div className="rr-topnav-inner">
        <Link href="/" className="rr-topnav-brand group min-w-0">
          <div className="rr-brand-logo overflow-hidden">
            <Image src="/logo-r.png" alt="" width={34} height={34} className="!p-0.5 object-contain" priority />
          </div>
          <div className="min-w-0 hidden sm:block">
            <div className="rr-brand-name leading-tight">Automation Projects Ready For Robots</div>
            <div className="rr-brand-sub">with Signal Intelligence</div>
          </div>
        </Link>

          {/* Mobile: hamburger */}
          <div className="md:hidden relative ml-auto shrink-0">
            <button 
              onClick={() => setShowMenu(!showMenu)}
              type="button"
              className="rr-btn-signin px-3 text-lg leading-none">
              ☰
            </button>
            {showMenu && (
              <div className="absolute right-0 top-full mt-2 w-64 max-h-[min(80vh,520px)] overflow-y-auto border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
                <div className="border-b border-neutral-800">
                  <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Main</div>
                  <Link href="/" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-emerald-400 hover:bg-neutral-900 cursor-pointer">🏠 Home</div>
                  </Link>
                  <button
                    type="button"
                    onClick={() => { fetchData(); setShowMenu(false); }}
                    className="w-full text-left px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 border-t border-neutral-800"
                  >
                    &#8635; Refresh data
                  </button>
                  <Link href="/dashboard" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 cursor-pointer border-t border-neutral-800">📊 Pipeline</div>
                  </Link>
                </div>
                <div className="border-b border-neutral-800">
                  <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Pipeline</div>
                  <Link href="/crm/" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-emerald-400 hover:bg-neutral-900 cursor-pointer">🗂️ CRM</div>
                  </Link>
                </div>
                <div className="border-b border-neutral-800">
                  <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Discover</div>
                  <Link href="/search" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 cursor-pointer">🔍 Search</div>
                  </Link>
                  <Link href="/market-insights" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 cursor-pointer">📈 Market</div>
                  </Link>
                  <Link href="/about" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-emerald-400 hover:bg-neutral-900 cursor-pointer">⚡ Signals</div>
                  </Link>
                  <Link href="/newsletter" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-neutral-300 hover:bg-neutral-900 cursor-pointer">📰 Newsletter</div>
                  </Link>
                  <Link href="/social" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-neutral-300 hover:bg-neutral-900 cursor-pointer">🎨 Studio</div>
                  </Link>
                </div>
                <div>
                  <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Tools</div>
                  <Link href="/roi-calculator" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-yellow-400 hover:bg-neutral-900 cursor-pointer">💰 ROI</div>
                  </Link>
                  <Link href="/pilot-calculator" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 cursor-pointer">🧪 Pilot</div>
                  </Link>
                  <Link href="/robot-ready" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-emerald-400 hover:bg-neutral-900 cursor-pointer">🤖 Robot Ready</div>
                  </Link>
                  <Link href="/brief" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-cyan-400 hover:bg-neutral-900 cursor-pointer">📋 Brief</div>
                  </Link>
                  <Link href="https://ready-2-robot.fly.dev/admin" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-emerald-400 hover:bg-neutral-900 cursor-pointer">⚙️ Admin</div>
                  </Link>
                  <Link href="/profile" onClick={() => setShowMenu(false)}>
                    <div className="px-4 py-2.5 text-[13px] text-neutral-300 hover:bg-neutral-900 cursor-pointer pb-3">♡ Profile</div>
                  </Link>
                </div>
              </div>
            )}
          </div>

        <SiteNavPrimaryLinks
          ariaLabel="Dashboard"
          prepend={
            <>
              {!session && usageCount < FREE_LIMIT && (
                <span className="rr-badge-free">{FREE_LIMIT - usageCount} free searches left</span>
              )}
              {lastRefresh && (
                <span className="rr-topnav-time tabular-nums">{lastRefresh}</span>
              )}
            </>
          }
          extraAfterHome={
            <button type="button" className="rr-nav-refresh" onClick={fetchData}>
              Refresh
            </button>
          }
        />
        <div className="rr-topnav-right hidden md:flex items-center">
          {session
            ? <span className="text-sm text-[var(--rr-muted2)] max-w-[10rem] truncate">{session.user.email.split('@')[0]}</span>
            : (
              <div title="Browse freely — sign in only to save companies and reports">
                <LoginDropdown
                  label="sign in to save"
                  className="[&_button]:rounded-md [&_button]:border [&_button]:border-[#1f2d42] [&_button]:px-3 [&_button]:py-1.5 [&_button]:text-sm [&_button]:text-[#94a3b8] [&_button]:hover:border-[#10b981] [&_button]:hover:text-[#10b981]"
                />
              </div>
            )}
        </div>
        </div>
      </header>

      {error && (
        <div className="rr-error-strip max-w-[1400px] mx-auto w-full">
          {error}
        </div>
      )}

      <div className="rr-body-layout w-full max-w-[1600px] mx-auto">
        
        {/* Mobile filter toggle button */}
        <button
          type="button"
          onClick={() => setShowMobileFilters(!showMobileFilters)}
          className="lg:hidden fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full border border-neutral-700 bg-neutral-900/95 px-4 py-3 text-sm font-medium text-neutral-200 shadow-xl backdrop-blur-sm hover:border-neutral-500 hover:bg-neutral-900"
        >
          <span>Filters</span>
          {(tier !== 'ALL' || industry !== 'All' || sigType || search || minScore > 0) && (
            <span className="flex h-2 w-2 rounded-full bg-emerald-500" aria-hidden />
          )}
        </button>

        {/* LEFT COLUMN - Filters & Controls */}
        <aside className={`
          rr-sidebar flex flex-col shrink-0 space-y-6
          lg:sticky lg:top-[56px] lg:self-start lg:max-h-[calc(100vh-3.5rem)] lg:overflow-y-auto sidebar-scroll
          ${
            showMobileFilters 
              ? 'fixed inset-0 z-50 !flex bg-[var(--rr-bg)] p-4 overflow-y-auto' 
              : 'hidden'
          }
          lg:flex
        `}>
          
          {/* Mobile close button */}
          <button 
            onClick={() => setShowMobileFilters(false)}
            className="lg:hidden mb-4 w-full bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded text-sm font-medium">
            ✕ Close Filters
          </button>
          
          {/* Quick Stats moved to main column */}

          {/* Filters */}
          <div className="rr-filters-card space-y-4">
            <h3 className="rr-sidebar-section-label !mb-0">Filters</h3>
            
            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">Search Companies</label>
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="company name..."
                className="w-full bg-zinc-950 border border-zinc-600 rounded-lg px-3 py-2.5 text-base
                           text-zinc-100 placeholder-zinc-500
                           focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-900
                           transition-colors" />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">
                Min Score <span className="text-emerald-400 font-semibold tabular-nums">{minScore}</span>
              </label>
              <input type="range" min={0} max={100} value={minScore}
                onChange={e => setMinScore(Number(e.target.value))}
                className="w-full accent-emerald-500" />
              <div className="flex justify-between text-xs text-zinc-500 mt-1.5 font-medium tabular-nums">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">Priority Tier</label>
              <div className="grid grid-cols-2 gap-2">
                {TIERS.map(t => (
                  <button key={t} onClick={() => setTier(t)}
                    className={`px-3 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                      tier === t 
                        ? 'bg-emerald-900/50 border border-emerald-600 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.15)]' 
                        : 'border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:bg-white/5'
                    }`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">Industry</label>
              <select value={industry} onChange={e => setIndustry(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-600 rounded-lg px-3 py-2.5 text-base
                           text-zinc-100 focus:outline-none focus:border-emerald-600">
                {INDUSTRIES.map(ind => (
                  <option key={ind} value={ind}>{ind}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">Signal Type</label>
              <select value={sigType} onChange={e => setSigType(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-600 rounded-lg px-3 py-2.5 text-base
                           text-zinc-100 focus:outline-none focus:border-emerald-600">
                <option value="">All Signals</option>
                {SIGNAL_TYPES.filter(Boolean).map(st => (
                  <option key={st} value={st}>{SIGNAL_META[st]?.label || st}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-zinc-300">Sort By</label>
              <select value={sort} onChange={e => setSort(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-600 rounded-lg px-3 py-2.5 text-base
                           text-zinc-100 focus:outline-none focus:border-emerald-600">
                <option value="score">ML intent (High → Low)</option>
                <option value="lead_value">Lead value (High → Low)</option>
                <option value="signals">Signal Count</option>
                <option value="name">Company Name</option>
              </select>
            </div>

            <div className="h-px bg-zinc-700/80" />

            <label className="flex items-center gap-3 cursor-pointer select-none">
              <input type="checkbox" checked={excludeJunk} onChange={e => setExcludeJunk(e.target.checked)}
                className="sr-only peer" />
              <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-900 transition-colors relative">
                <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-zinc-500 peer-checked:bg-emerald-400 rounded-full transition-all ${excludeJunk ? 'translate-x-5' : ''}`} />
              </div>
              <span className="text-sm text-zinc-200">
                {excludeJunk ? 'Hiding junk leads' : 'Showing all leads'}
              </span>
            </label>

            {(tier !== 'ALL' || industry !== 'All' || sigType || search || minScore > 0) && (
              <>
                <div className="h-px bg-zinc-700/80" />
                <button onClick={() => {
                  setTier('ALL');
                  setIndustry('All');
                  setSigType('');
                  setSearch('');
                  setMinScore(0);
                }}
                  className="w-full text-sm text-zinc-300 hover:text-emerald-300 transition-colors py-2.5 border border-zinc-700 rounded-lg hover:border-emerald-700/80 hover:bg-white/5">
                  ✕ Clear all filters
                </button>
              </>
            )}
          </div>

          {/* Quick Scrape */}
          <QuickScrape onDone={fetchData} />

        </aside>

        {/* RIGHT COLUMN - Main Content */}
        <main className="rr-main rr-main--tight flex-1 min-w-0 !p-4 md:!p-6">

          <section
            className="mb-6 rounded-xl border border-emerald-800/45 bg-gradient-to-br from-emerald-950/35 via-neutral-950/90 to-neutral-950 p-5 sm:p-6 shadow-lg shadow-black/25"
            aria-labelledby="crm-pipeline-guide-title"
          >
            <div className="flex flex-col xl:flex-row xl:items-start gap-6 xl:gap-10">
              <div className="min-w-0 flex-1 space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xl" aria-hidden>🗂️</span>
                  <h2 id="crm-pipeline-guide-title" className="text-lg font-bold text-white tracking-tight">
                    CRM &amp; sales pipeline
                  </h2>
                </div>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  This page is your live workspace: use filters to narrow accounts, save deals into your list, then open a row for the AI assistant and engagement workflow.
                </p>
                <ol className="list-decimal list-inside space-y-2.5 text-sm text-neutral-300 leading-relaxed">
                  <li>
                    <span className="font-semibold text-emerald-400/95">Advanced search</span> — Use the{' '}
                    <strong className="text-neutral-200">left column</strong> (tap <strong className="text-neutral-200">Filters</strong> on mobile) to search by company name,{' '}
                    <strong className="text-neutral-200">tier</strong>, <strong className="text-neutral-200">industry</strong>, and{' '}
                    <strong className="text-neutral-200">signal type</strong>. Combine <strong className="text-neutral-200">min score</strong> and{' '}
                    <strong className="text-neutral-200">sort</strong> to fine-tune the list. For broader queries, use{' '}
                    <Link href="/search" className="text-cyan-400 hover:text-cyan-300 underline-offset-2 hover:underline">
                      Intelligence Search
                    </Link>
                    .
                  </li>
                  <li>
                    <span className="font-semibold text-emerald-400/95">Save deals</span> — Click{' '}
                    <strong className="text-neutral-200">☆ save</strong> on a row to bookmark it.{' '}
                    {session ? (
                      <span className="text-neutral-400">Signed in: saves sync to your account (same list as Profile).</span>
                    ) : (
                      <span className="text-neutral-400">
                        Guests: saves stay in this browser.{' '}
                        <Link href="/login" className="text-amber-400/95 hover:text-amber-300">
                          Sign in
                        </Link>{' '}
                        for cloud sync.
                      </span>
                    )}
                  </li>
                  <li>
                    <span className="font-semibold text-emerald-400/95">Workflow + AI</span> — Open any lead for strategy, outreach angles, and talking points. Use saved accounts as your working pipeline before pushing to CRM accounts.
                  </li>
                </ol>
              </div>
              <aside className="shrink-0 w-full xl:w-72 space-y-3 rounded-lg border border-neutral-800/90 bg-black/35 p-4 sm:p-5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-500">Account &amp; CRM</p>
                <Link
                  href="/crm/"
                  className="block text-sm font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  Set up CRM workspace →
                </Link>
                <p className="text-xs text-neutral-500 leading-relaxed">
                  Create teams and accounts so saved leads map to buyer records you can work in the CRM app.
                </p>
                <Link href="/profile" className="block text-sm text-cyan-400/90 hover:text-cyan-300">
                  Profile &amp; saved companies →
                </Link>
                {!session && (
                  <Link href="/login" className="block text-sm text-amber-400/90 hover:text-amber-300">
                    Sign in to persist saves →
                  </Link>
                )}
              </aside>
            </div>
          </section>

          {/* Headline + compact inline metrics (replaces large stat grid + recent-activity links) */}
          <header className="rr-dashboard-intro">
            <div className="rr-dashboard-intro-head">
              <h1 className="rr-dashboard-title">
                Automation Projects <span className="rr-dashboard-title-accent">Ready For Robots</span>
              </h1>
              <p className="rr-dashboard-deck">
                Live pipeline — filter on the left, prioritize by tier, act on signals.
              </p>
            </div>
            <div className="rr-dashboard-metrics-inline" aria-label="Pipeline summary">
              <div className="rr-dash-metric">
                <span className="n tabular-nums text-[var(--rr-text)]">{(summary.total ?? 0).toLocaleString('en-US')}</span>
                <span className="l">Active</span>
              </div>
              <button
                type="button"
                className="rr-dash-metric rr-dash-metric--btn"
                onClick={() => { setTier('HOT'); setIndustry('All'); setSearch(''); }}
              >
                <span className="n tabular-nums text-[var(--rr-orange)]">{(summary.hot ?? 0).toLocaleString('en-US')}</span>
                <span className="l">Hot</span>
              </button>
              <div className="rr-dash-metric">
                <span className="n tabular-nums text-[var(--rr-cyan)]">{(summary.total_signals ?? 0).toLocaleString('en-US')}</span>
                <span className="l">Signals</span>
              </div>
              <button
                type="button"
                className="rr-dash-metric rr-dash-metric--btn"
                onClick={() => { setTier('WARM'); setIndustry('All'); setSearch(''); }}
              >
                <span className="n tabular-nums text-[var(--rr-green)]">{(summary.warm ?? 0).toLocaleString('en-US')}</span>
                <span className="l">Warm</span>
              </button>
            </div>
          </header>

          {/* Pipeline CTA — headline + compact live ticker on one row (md+) */}
          <div className="rr-pipeline-card mb-0 border-emerald-900/30 bg-gradient-to-br from-emerald-950/25 to-[var(--rr-surface)]">
            <div className="mb-3">
              <div className="rr-pipeline-card-title-row">
                <h2 className="rr-pipeline-card-title text-2xl sm:text-[1.75rem] md:text-3xl font-extrabold tracking-tight">
                  Find your next customers
                </h2>
                {!loading && liveSignals.length > 0 && (
                  <div className="rr-ticker-inline" aria-label="Live signals">
                    <span className="rr-ticker-inline-label">
                      <span className="inline-block h-1 w-1 rounded-full bg-emerald-500 animate-pulse" aria-hidden />
                      Live
                    </span>
                    <div className="rr-ticker-inline-scroll">
                      <div className="rr-ticker-inline-track">
                        {liveSignals.concat(liveSignals).map((sig, idx) => {
                          const sigMeta = SIGNAL_META[sig.type] || { label: sig.type, text: 'text-neutral-400' };
                          return (
                            <button
                              type="button"
                              key={idx}
                              onClick={() => setSelectedLead(sig.lead)}
                              className="rr-ticker-inline-item"
                            >
                              <span className="text-cyan-400/95 hover:text-cyan-300 underline decoration-dotted underline-offset-2">
                                {sig.company}
                              </span>
                              <span className={`${sigMeta.text} font-medium`}>{sigMeta.label}</span>
                              <span className="text-zinc-600 opacity-80">·</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <p className="rr-pipeline-card-lead">
                Paste your site URL — see matched prospects with signals in seconds.
              </p>
              <PipelineScoreLegend className="mb-3" />
            </div>
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pipeline-input-row">
              <input
                id="dashboard-pipeline-url"
                type="text"
                placeholder="https://your-robotics-company.com"
                className="rr-filter-input flex-1 min-w-0 !py-2.5 sm:!py-3 text-base"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const url = e.target.value.trim();
                    if (url) {
                      window.location.href = `/pipeline-results?url=${encodeURIComponent(url)}`;
                    }
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  const el = typeof document !== 'undefined' ? document.getElementById('dashboard-pipeline-url') : null;
                  const url = (el?.value || '').trim();
                  if (url) {
                    window.location.href = `/pipeline-results?url=${encodeURIComponent(url)}`;
                  }
                }}
                className="rr-btn-primary rr-btn-primary-compact shrink-0 !px-3.5 !py-2 text-xs sm:text-sm"
              >
                View pipeline →
              </button>
            </div>
            <p className="rr-pipeline-meta">No signup required · Results open on the next page</p>
          </div>

          {/* strategic snapshot */}
          {!loading && leads.length > 0 && (
            <StrategicSnapshot leads={leads} onSelect={setSelectedLead} />
          )}

          {/* agent insights */}
          <AgentInsightsPanel />

      {/* lead list */}
      {loading ? (
        <p className="py-16 text-center text-zinc-300 text-lg font-medium animate-pulse">Loading leads…</p>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center rounded-xl border border-zinc-800 bg-zinc-950/40 px-6">
          <p className="text-zinc-200 text-lg font-medium">No leads match your filters</p>
          <p className="mt-2 text-zinc-500 text-base">Try clearing filters or lowering the minimum score.</p>
          {leads.length === 0 && (
            <p className="mt-4 text-sm text-zinc-500">
              Empty database — run{' '}
              <code className="rounded border border-zinc-600 bg-zinc-900 px-2 py-0.5 text-zinc-300 font-mono text-sm">
                python scripts/test_scraper.py --clear
              </code>{' '}
              to seed
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {INDUSTRIES.filter(ind => ind !== 'All').map(ind => {
            const group = displayedLeads.filter(l => (l.industry || 'New') === ind);
            if (group.length === 0) return null;
            const hotCount  = group.filter(l => l.priority_tier === 'HOT').length;
            const warmCount = group.filter(l => l.priority_tier === 'WARM').length;
            const isExpanded = !!collapsedSections[ind];
            const displayGroup = isExpanded ? group : group.slice(0, 3);
            const hasMore = group.length > 3;
            return (
              <div key={ind}>
                {/* industry section header - clickable to expand */}
                <button
                  onClick={() => setCollapsedSections(p => ({ ...p, [ind]: !isExpanded }))}
                  className="w-full flex items-center gap-2 py-3 mb-1 border-b border-zinc-700 group hover:border-emerald-800/60 transition-colors text-left cursor-pointer">
                  <span className="text-sm font-bold tracking-wide uppercase text-zinc-200 group-hover:text-white transition-colors">
                    {ind}
                  </span>
                  {hotCount  > 0 && <span className="text-xs font-semibold uppercase tracking-wide text-red-400 tabular-nums">{hotCount} hot</span>}
                  {warmCount > 0 && <span className="text-xs font-semibold uppercase tracking-wide text-amber-400 tabular-nums">{warmCount} warm</span>}
                  <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500 ml-auto tabular-nums">
                    {group.length} {group.length === 1 ? 'lead' : 'leads'}
                    {hasMore && <span className="ml-2 text-cyan-400">{isExpanded ? '(showing all)' : '(top 3)'}</span>}
                    &nbsp; {isExpanded ? '\u25bc' : '\u25b6'}
                  </span>
                </button>
                <div className="space-y-px">
                  {displayGroup.map((lead, i) => {
            const sc     = lead.score || {};
            const isOpen = expanded[lead.id];
            const tm     = TIER_META[lead.priority_tier] || TIER_META.COLD;

            return (
              <div key={lead.id}
                className={`lead-card border-b border-neutral-800/60 py-3 rounded-sm ${
                  isOpen ? `border-l-4 pl-3 ${tm.borderL}` : 'border-l-2 border-l-transparent pl-3 hover:border-l-emerald-800'
                }`}>

                {/* row header */}
                <div className="flex cursor-pointer items-start gap-4"
                  onClick={() => setExpanded(p => ({ ...p, [lead.id]: !p[lead.id] }))}
                  role="button" tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && setExpanded(p => ({...p, [lead.id]: !p[lead.id]}))  }>

        <span className="text-sm font-mono font-semibold text-zinc-500 w-8 text-right shrink-0 mt-0.5">#{i+1}</span>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <a
                        href={companyExternalHref(lead) || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()}
                        className={`${COMPANY_NAME_LINK_CLASS} text-xl font-semibold`}
                      >
                        {lead.company_name}
                      </a>
                      <TierBadge tier={lead.priority_tier} />
                      {/* Signal count badge instead of individual badges */}
                      {(lead.signals || []).length > 0 && (
                        <span className="text-xs border border-cyan-700 text-cyan-300 px-2 py-0.5 rounded-md font-medium">
                          {lead.signal_count} signal{lead.signal_count !== 1 ? 's' : ''}
                        </span>
                      )}
                      {lead.location_city && (
                        <span className="text-sm text-zinc-400">
                          {lead.location_city}{lead.location_state ? `, ${lead.location_state}` : ''}
                        </span>
                      )}
                    </div>
                    {/* Move AI Analysis button to separate line for cleaner layout */}
                    <div className="flex gap-2 mt-1.5">
                      <button
                        className="text-sm text-emerald-400 hover:text-emerald-300 underline decoration-dotted transition-colors"
                        onClick={e => { e.stopPropagation(); setSelectedLead(lead); }}>
                        → View Analysis
                      </button>
                    </div>
                  </div>

                  {/* scores: signal + value + ML intent */}
                  <div className="shrink-0 text-right space-y-1">
                    <div className="flex flex-col items-end gap-0.5">
                      <SignalScoreBadge value={sc.signal_score ?? 0} />
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-teal-600/90">signal</span>
                    </div>
                    <div className="flex flex-col items-end gap-0.5 pt-1 border-t border-zinc-800/80">
                      <ValueNum value={sc.lead_value_score ?? 0} />
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-violet-500/90">value</span>
                    </div>
                    <div className="flex flex-col items-end gap-0.5 pt-1 border-t border-zinc-800/80">
                      <ScoreNum value={sc.overall_score ?? 0} />
                      <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">intent</span>
                    </div>
                  </div>

                  {/* Click indicator */}
                  <button 
                    className="shrink-0 px-3 py-1.5 text-xs font-medium border border-cyan-600 text-cyan-300 
                               rounded-lg hover:border-cyan-400 hover:text-cyan-200 transition-colors"
                    onClick={(e) => { e.stopPropagation(); setExpanded(p => ({ ...p, [lead.id]: !p[lead.id] })); }}>
                    {isOpen ? 'close' : 'click here'}
                  </button>

                  <span className={`text-xs font-semibold mt-1 ${tm.text}`}>{isOpen ? 'v' : '>'}</span>
                </div>

                {/* score bars */}
                <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-3 pl-10">
                  <ScoreBar value={sc.signal_score ?? 0} label="signal evidence" />
                  <ScoreBar value={sc.lead_value_score ?? 0} label="lead value" />
                  <ScoreBar value={sc.overall_score     ?? 0} label="ML intent" />
                  <ScoreBar value={sc.automation_score ?? 0} label="automation" />
                  <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
                  <ScoreBar value={sc.expansion_score   ?? 0} label="expansion"  />
                  <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
                </div>
                {lead.procurement_hints?.length > 0 && (
                  <div className="mt-2 pl-10 flex flex-wrap items-center gap-2">
                    <span className="text-[10px] uppercase text-amber-600/80">procurement</span>
                    <ProcurementHints hints={lead.procurement_hints} />
                  </div>
                )}

                {/* priority reasons -- inline text */}
                {lead.priority_reasons?.length > 0 && (
                  <p className="mt-2 pl-10 text-sm text-zinc-400 leading-relaxed">
                    {lead.priority_reasons.join('  ·  ')}
                  </p>
                )}
                <div className="mt-2 pl-10">
                  <AutomationSpecBlock profile={lead.automation_profile} compact theme="dashboard" />
                </div>

                {/* expanded drawer */}
                {isOpen && (
                  <div className="mt-4 pl-10 space-y-4">
                    {/* AI Analysis + Save actions */}
                    <div className="flex items-center gap-2">
                      <button
                        className="btn-ghost border-emerald-900 text-emerald-400 hover:border-emerald-700 text-xs"
                        onClick={e => { e.stopPropagation(); setSelectedLead(lead); }}>
                        ▲ AI Analysis
                      </button>
                      <button
                        className={`btn-ghost text-xs ${
                          savedIds.has(lead.id)
                            ? 'border-emerald-800 text-emerald-400 hover:border-emerald-600'
                            : 'border-neutral-800 text-neutral-600 hover:border-neutral-600'
                        }`}
                        onClick={e => { e.stopPropagation(); quickSave(lead); }}>
                        {savedIds.has(lead.id) ? '★ saved' : '☆ save'}
                      </button>
                    </div>

                    {/* Intelligence summary + social share */}
                    <LeadShareBar lead={lead} />
                    <AutomationSpecBlock profile={lead.automation_profile} theme="dashboard" />
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs">
                      {lead.website && (
                        <a href={lead.website} target="_blank" rel="noreferrer"
                          className="text-cyan-600 hover:text-cyan-400 transition-colors">
                          {lead.website}
                        </a>
                      )}
                      {lead.employee_estimate && (
                        <span className="text-neutral-400">
                          {lead.employee_estimate.toLocaleString()} employees
                        </span>
                      )}
                      <span className={`font-mono ${tm.text}`}>
                        priority {lead.priority_score}
                      </span>
                    </div>

                    {(lead.signals || []).length > 0 && (() => {
                      const drawerSignals = topSignalsForDisplay(lead.signals || [], MAX_SIGNALS_DISPLAY);
                      const nTotal = lead.signal_count || (lead.signals || []).length;
                      return (
                      <div>
                        <p className="label mb-2">signals &middot; {nTotal}</p>
                        {nTotal > MAX_SIGNALS_DISPLAY && (
                          <p className="text-[10px] text-neutral-500 mb-2">
                            Showing top {MAX_SIGNALS_DISPLAY} by weighted score.
                          </p>
                        )}
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-neutral-800 text-left">
                              <th className="pb-1 pr-4 label font-normal">type</th>
                              <th className="pb-1 pr-4 label font-normal">strength</th>
                              <th className="pb-1 pr-4 label font-normal">source</th>
                              <th className="pb-1 label font-normal">summary</th>
                            </tr>
                          </thead>
                          <tbody>
                            {drawerSignals.map((s, si) => {
                              const str = Number(s.strength ?? 0);
                              return (
                              <tr key={si} className="border-b border-neutral-900 align-top">
                                <td className="py-1.5 pr-4"><SignalBadge type={s.signal_type} /></td>
                                <td className="py-1.5 pr-4 tabular-nums">
                                  <span className={`font-mono ${
                                    str >= 0.7 ? 'text-emerald-400'
                                    : str >= 0.4 ? 'text-cyan-500'
                                    : 'text-neutral-600'
                                  }`}>
                                    {(str * 100).toFixed(0)}%
                                  </span>
                                </td>
                                <td className="py-1.5 pr-4">
                                  {s.source_url
                                    ? <a href={s.source_url} target="_blank" rel="noreferrer"
                                        className="text-cyan-700 hover:text-cyan-500">&#8599;</a>
                                    : <span className="text-neutral-800">&mdash;</span>}
                                </td>
                                <td className="py-1.5 text-[11px] text-neutral-500 max-w-xs truncate">
                                  {s.raw_text || '—'}
                                </td>
                              </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            );
                    })}
                    {/* Show expand button if there are more leads */}
                    {hasMore && !isExpanded && (
                      <button
                        onClick={() => setCollapsedSections(p => ({ ...p, [ind]: true }))}
                        className="w-full py-3 text-sm text-cyan-400 hover:text-cyan-300 border border-neutral-800 rounded hover:border-cyan-700 transition-colors mt-2">
                        ▼ Show {group.length - 3} more {group.length - 3 === 1 ? 'lead' : 'leads'} in {ind}
                      </button>
                    )}
                    {isExpanded && hasMore && (
                      <button
                        onClick={() => setCollapsedSections(p => ({ ...p, [ind]: false }))}
                        className="w-full py-3 text-sm text-neutral-400 hover:text-neutral-300 border border-neutral-800 rounded hover:border-neutral-700 transition-colors mt-2">
                        ▲ Show top 3 only
                      </button>
                    )}
                  </div>
              </div>
            );
          })}
          
          {/* Signup Wall for non-logged-in users */}
          {!session && filtered.length > 5 && (
            <div className="border-2 border-emerald-600/30 bg-gradient-to-b from-emerald-950/30 to-black rounded-xl p-8 text-center space-y-6 mt-8">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-900/30 border border-emerald-700/50 rounded-full">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                  <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wide">Free Preview Complete</span>
                </div>
                <h3 className="text-3xl font-bold text-white">
                  Unlock {filtered.length - 5} More Hot Leads
                </h3>
                <p className="text-lg text-neutral-300 max-w-2xl mx-auto">
                  You've viewed 5 free leads. Create a free account to see all {filtered.length} companies with active automation signals
                </p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto py-6">
                <div className="space-y-2">
                  <div className="text-2xl">🔥</div>
                  <div className="text-sm font-semibold text-emerald-400">Full Database Access</div>
                  <div className="text-xs text-neutral-400">Browse all {filtered.length} qualified leads</div>
                </div>
                <div className="space-y-2">
                  <div className="text-2xl">📊</div>
                  <div className="text-sm font-semibold text-emerald-400">AI Analysis Reports</div>
                  <div className="text-xs text-neutral-400">Deep signal insights & engagement playbooks</div>
                </div>
                <div className="space-y-2">
                  <div className="text-2xl">🔔</div>
                  <div className="text-sm font-semibold text-emerald-400">Daily Alerts</div>
                  <div className="text-xs text-neutral-400">New hot leads delivered to your inbox</div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
                <Link 
                  href="/login" 
                  className="px-8 py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-lg transition-all duration-200 shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)]"
                >
                  Create Free Account →
                </Link>
                <div className="text-xs text-neutral-400">
                  No credit card required • Instant access
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* scraper health */}
      {health && (
        <div className="mt-12 border-t border-zinc-700/80 pt-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Scraper health</span>
              <Link href="/pipeline-health" className="text-xs text-cyan-500 hover:text-cyan-400 whitespace-nowrap">
                Full run history →
              </Link>
            </div>
            <button onClick={handleResetAll} disabled={resetting || openCircuits === 0}
              className="btn-danger">
              {resetting ? 'resetting...' : 'reset circuits'}
            </button>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm mb-4 text-zinc-400">
            <span>tracked — <span className="text-zinc-200 font-medium">{health.summary?.total_urls_tracked ?? 0}</span></span>
            <span>healthy — <span className="text-emerald-400 font-medium">{health.summary?.healthy_urls ?? 0}</span></span>
            {openCircuits > 0 && <span className="text-red-500">open &mdash; {openCircuits}</span>}
            {health.summary?.last_run_scraper && (
              <span>
                last run &mdash; {health.summary.last_run_scraper}{' '}
                <span className={health.summary.last_run_status === 'success' ? 'text-emerald-500' : 'text-red-500'}>
                  {health.summary.last_run_status}
                </span>
              </span>
            )}
          </div>

          {Object.keys(health.url_health || {}).length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-700/80">
                  {['', 'url', 'attempts', 'failures', 'circuit'].map(h => (
                    <th key={h} className="pb-2 pr-6 text-left text-xs font-bold uppercase tracking-wide text-zinc-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(health.url_health).map(([url, info]) => (
                  <tr key={url} className="border-b border-neutral-900">
                    <td className="py-1.5 pr-4"><HealthDot open={info.circuit_open} /></td>
                    <td className="py-1.5 pr-6 max-w-[14rem] truncate text-zinc-300" title={url}>
                      {url.replace(/^https?:\/\//, '').substring(0, 45)}
                    </td>
                    <td className="py-1.5 pr-6 tabular-nums text-zinc-400">{info.attempts ?? '—'}</td>
                    <td className="py-1.5 pr-6 tabular-nums text-zinc-400">{info.failures ?? info.consecutive_failures ?? '—'}</td>
                    <td className="py-1.5 text-zinc-500 text-[10px] max-w-[8rem] truncate" title={info.last_error || ''}>
                      {info.circuit_open ? 'open' : 'ok'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-zinc-500">No URLs tracked — run a scraper first</p>
          )}
        </div>
      )}

        </main>
      </div>

      <footer className="rr-footer mt-auto">
        Refreshes every 5 min · up to 50 leads per load (rotating pool)
      </footer>
    </div>
    </>
  );
}
