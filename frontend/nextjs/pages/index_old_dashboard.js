/**
 * Ready for Robots -- Lead Intelligence Dashboard
 * Supabase-style: no fills, stroke + text only, emerald/cyan accents.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useAuth } from './_app';
import { authHeader } from '../lib/supabase';

// In production (Fly.io) frontend + API share the same origin — use relative URLs.
// For local dev, point to the local uvicorn server.
const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// -- helpers ----------------------------------------------------------------

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
        <span className="label">{label}</span>
        <span className="text-[9px] tabular-nums text-neutral-500">{pct}</span>
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
  ma_activity:           { label: 'M&A',          border: 'border-pink-700',    text: 'text-pink-400'    },
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

function ScoreNum({ value }) {
  const v = Math.round(value ?? 0);
  let badgeClass = 'score-badge-poor border-red-700 text-red-400';
  if (v >= 75) badgeClass = 'score-badge-high border-emerald-700 text-emerald-400';
  else if (v >= 50) badgeClass = 'score-badge-medium border-cyan-700 text-cyan-400';
  else if (v >= 30) badgeClass = 'score-badge-low border-yellow-700 text-yellow-400';
  
  return (
    <span className={`inline-flex items-center border rounded px-1.5 leading-none tabular-nums font-mono font-semibold text-[10px] ${badgeClass}`} style={{ paddingTop: '0.2rem', paddingBottom: '0.2rem' }}>
      {v}
    </span>
  );
}

const INDUSTRIES  = ['All', 'Hospitality', 'Logistics', 'Healthcare', 'Food Service', 'Airports & Transportation', 'Casinos & Gaming', 'Cruise Lines', 'Theme Parks & Entertainment', 'Real Estate & Facilities', 'Manufacturing'];
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
  const [items, setItems] = useState([]);
  useEffect(() => {
    fetch(`${API}/api/trending`)
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => setItems(d.items || []))
      .catch(() => {});
  }, []);
  if (!items.length) return null;

  const TYPE_COLOR = {
    strategic_hire:        'text-blue-400',
    capex:                 'text-cyan-400',
    labor_shortage:        'text-red-400',
    expansion:             'text-emerald-400',
    funding_round:         'text-violet-400',
    job_posting:           'text-amber-400',
    ma_activity:           'text-pink-400',
    quality_bottleneck:    'text-orange-400',
    safety_incident:       'text-red-300',
    production_capacity:   'text-yellow-400',
    warehouse_throughput:  'text-teal-400',
    packaging_automation:  'text-indigo-400',
    repetitive_process:    'text-purple-400',
    material_handling:     'text-lime-400',
    news:                  'text-neutral-400',
  };

  const doubled = [...items, ...items];

  return (
    <div className="ticker-wrap border-b border-neutral-800 bg-neutral-950 py-1.5 w-screen relative left-1/2 -translate-x-1/2">
      <div className="ticker-inner flex items-center">
        {doubled.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-1.5 px-5 shrink-0">
            <span className={`text-[10px] font-semibold uppercase tracking-wide ${TYPE_COLOR[item.signal_type] || 'text-neutral-400'}`}>
              {SIGNAL_META[item.signal_type]?.label || item.signal_type}
            </span>
            <span className="text-[10px] font-semibold text-white">{item.company_name}</span>
            <span className="text-[10px] text-neutral-400 max-w-[24rem] truncate">
              {item.signal_text}
            </span>
            <span className="text-[10px] text-neutral-400 mx-2">&bull;</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function uniqueSignalTypes(signals = []) {
  const seen = new Set();
  return signals.filter(s => { if (seen.has(s.signal_type)) return false; seen.add(s.signal_type); return true; });
}

// -- Strategic Snapshot (replaces HOT/WARM/COLD boxes) ----------------------
const INDUSTRY_ROBOT_FIT = {
  'Hospitality':               'Service & Delivery',
  'Logistics':                 'Warehouse AMR Fleet',
  'Healthcare':                'Clinical Logistics',
  'Food Service':              'BOH Automation',
  'Airports & Transportation': 'Ground Ops Robots',
  'Retail':                    'Picking & Restocking',
  'Casinos & Gaming':          'Floor & F&B Delivery',
  'Cruise Lines':              'Onboard Delivery',
  'Theme Parks & Entertainment': 'F&B & Custodial',
  'Real Estate & Facilities':  'Cleaning & Concierge',
};

const READINESS = {
  HOT:  { label: 'Active Buyer',  color: 'text-red-400',     dot: 'bg-red-500'     },
  WARM: { label: 'Evaluating',    color: 'text-yellow-400',  dot: 'bg-yellow-500'  },
  COLD: { label: 'Monitoring',    color: 'text-neutral-500', dot: 'bg-neutral-600' },
};

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
  const [rotationIndex, setRotationIndex] = useState(0);
  const [prevVisible, setPrevVisible] = useState([]);
  const sorted = [...leads]
    .filter(l => l.score?.overall_score != null)
    .sort((a, b) => (b.score?.overall_score ?? 0) - (a.score?.overall_score ?? 0));
  
  // Rotate through leads every 5 seconds, showing 5 at a time
  useEffect(() => {
    if (sorted.length <= 5) return; // No need to rotate if we have 5 or fewer
    
    const interval = setInterval(() => {
      setRotationIndex(prev => {
        const maxIndex = sorted.length - 5;
        return prev >= maxIndex ? 0 : prev + 1;
      });
    }, 5000); // 5 seconds

    return () => clearInterval(interval);
  }, [sorted.length]);

  // Get 5 leads starting from rotationIndex
  const visible = sorted.slice(rotationIndex, rotationIndex + 5);

  // Track previous visible leads for animation
  useEffect(() => {
    if (visible.length > 0) {
      setPrevVisible(visible.map(l => l.id));
    }
  }, [rotationIndex]);

  if (!sorted.length) return null;

  // Determine which leads are entering (new in visible, not in prevVisible)
  const enteringIds = new Set(
    visible.filter(l => !prevVisible.includes(l.id)).map(l => l.id)
  );
  // Determine which leads are exiting (in prevVisible, not in visible)
  const exitingIds = new Set(
    prevVisible.filter(id => !visible.some(l => l.id === id))
  );

  // Helper to check if lead was updated recently (last hour)
  const isRecentlyUpdated = (lead) => {
    const updated = new Date(lead.updated_at || lead.created_at);
    const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
    return updated > hourAgo;
  };

  // Helper to check if lead has new signals (last 24h)
  const hasNewSignals = (lead) => {
    if (!lead.signals || lead.signals.length === 0) return false;
    const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return lead.signals.some(s => {
      const detected = new Date(s.detected_at || s.created_at);
      return detected > dayAgo;
    });
  };

  return (
    <div className="mb-6 strategic-snapshot-bg rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold uppercase tracking-wider text-cyan-400" style={{ textShadow: '0 0 12px rgba(34, 211, 238, 0.6), 0 0 24px rgba(34, 211, 238, 0.4)' }}>⚡ Strategic Snapshot</span>
          <div className="hidden sm:flex items-center gap-3 text-[10px] text-neutral-400">
            <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" />buyer</span>
            <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-yellow-500" />eval</span>
            <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-neutral-600" />watch</span>
          </div>
        </div>
        <div className="text-[10px] text-neutral-500">
          Showing 5 of {sorted.length} leads {sorted.length > 5 && '• Rotating every 5s'}
        </div>
      </div>

      <div className="border border-neutral-800 rounded overflow-hidden">
        {/* col headers */}
        <div className="hidden md:grid border-b border-neutral-800/60 bg-neutral-950"
          style={{gridTemplateColumns:'1.5rem 1fr 6rem 7rem 6rem 4.5rem 6rem'}}>
          <span />
          <span className="label px-3 py-2">company</span>
          <span className="label px-2 py-2">signal</span>
          <span className="label px-2 py-2">readiness</span>
          <span className="label px-2 py-2">deal</span>
          <span className="label px-2 py-2 text-right">score</span>
          <span />
        </div>

        {visible.map((lead, i) => {
          const sig   = topSignal(lead);
          const ready = READINESS[lead.priority_tier] || READINESS.COLD;
          const deal  = dealLabel(lead.employee_estimate);
          const fit   = strategicFit(lead);
          const sigM  = sig ? (SIGNAL_META[sig.signal_type] || { label: sig.signal_type, border: 'border-neutral-700', text: 'text-neutral-400' }) : null;
          const excerpt = sig ? (sig.raw_text || '').substring(0, 55) : '';
          const recentlyUpdated = isRecentlyUpdated(lead);
          const newSignal = hasNewSignals(lead);
          
          // Determine animation based on position and rotation state
          const isEntering = enteringIds.has(lead.id);
          const animationStyle = isEntering
            ? `slideInFromTop 0.4s ease-out both` // New leads enter from top
            : `slideInFromLeft 0.3s ease-out ${i * 0.05}s both`; // Initial cascade effect

          return (
            <div key={lead.id}
              className={`grid grid-cols-[1.5rem_1fr_auto] md:grid-cols-none border-b border-neutral-900 last:border-0
                         hover:bg-neutral-900/40 transition-all group items-center
                         ${recentlyUpdated ? 'bg-emerald-950/10 animate-pulse-slow' : ''}`}
              style={{
                gridTemplateColumns:'1.5rem 1fr 6rem 7rem 6rem 4.5rem 6rem',
                animation: animationStyle
              }}>

              {/* rank */}
              <span className="text-[10px] text-neutral-800 pl-3 group-hover:text-neutral-600 transition-colors tabular-nums">{i + 1}</span>

              {/* company — name + dim metadata inline - CLICKABLE */}
              <button onClick={() => onSelect(lead)} className="px-3 py-2 min-w-0 text-left w-full">
                <div className="flex items-baseline gap-2 flex-wrap">
                  <span className="text-[11px] font-medium text-cyan-400 group-hover:text-cyan-300 transition-colors leading-tight cursor-pointer">
                    {lead.company_name}
                  </span>
                  {newSignal && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded border border-cyan-700 text-cyan-400 font-semibold uppercase">
                      New
                    </span>
                  )}
                  {recentlyUpdated && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded border border-emerald-700 text-emerald-400 font-semibold">
                      ↗ Active
                    </span>
                  )}
                  <span className="text-[10px] text-neutral-500 truncate hidden sm:inline">
                    {[lead.industry, lead.location_city].filter(Boolean).join(' · ')}
                  </span>
                </div>
                {excerpt && (
                  <p className="text-[10px] text-neutral-400 truncate mt-0.5 max-w-[24rem]" title={sig?.raw_text}>
                    {excerpt}{excerpt.length === 55 ? '…' : ''}
                  </p>
                )}
              </button>

              {/* signal badge only */}
              <div className="hidden md:flex items-center px-2 py-2">
                {sigM
                  ? <span className={`badge ${sigM.border} ${sigM.text}`}>{sigM.label}</span>
                  : <span className="text-[10px] text-neutral-800">—</span>}
              </div>

              {/* readiness */}
              <div className="hidden md:flex items-center gap-1.5 px-2 py-2">
                <span className={`inline-block h-1.5 w-1.5 rounded-full shrink-0 ${ready.dot}`} />
                <span className={`text-[11px] ${ready.color}`}>{ready.label}</span>
              </div>

              {/* deal tier only */}
              <div className="hidden md:flex items-center px-2 py-2">
                <span className="text-[11px] text-neutral-400">{deal.tier}</span>
              </div>

              {/* score */}
              <div className="flex items-center justify-end px-2 py-2">
                <ScoreNum value={lead.score?.overall_score ?? 0} />
              </div>

              {/* CTA */}
              <div className="flex items-center justify-end pr-3 py-2">
                <button
                  onClick={() => onSelect(lead)}
                  className="text-[10px] text-emerald-800 hover:text-emerald-400 transition-colors whitespace-nowrap font-medium">
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
      const r = await fetch(`${API}/api/agent/scrape/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls, industry: ind || null, scrape_now: now }),
      });
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
      const r = await fetch(`${API}/api/agent/insights`);
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
                            <span className="text-sm font-medium text-neutral-100">{s.company_name}</span>
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

  // load profile + check saved state
  useEffect(() => {
    // check localStorage saved state
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[]}');
      setSaved(!!(store.companies || []).find(c => c.id === lead.id));
    } catch {}

    fetch(`${API}/api/agent/profile/${lead.id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setProfile(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [lead.id]);

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
      const res = await fetch(`${API}/api/user/reports`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader(session.access_token) },
        body:    JSON.stringify(reportData),
      });
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

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[4vh]"
      onClick={onClose}>
      <div className="absolute inset-0 bg-black/80" />
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-[#0c0c0c] border border-neutral-700 rounded-lg shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}>

        {/* ── HEADER ── */}
        <div className={`flex items-start justify-between px-6 py-4 border-b ${tm.border} shrink-0`}>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-neutral-100 truncate">{lead.company_name}</h2>
              <TierBadge tier={lead.priority_tier} />
              {sc.overall_score != null && <ScoreNum value={sc.overall_score} />}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500">
              {lead.industry && <span className="text-neutral-400">{lead.industry}</span>}
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
            <a href="/profile" className="btn-ghost text-xs border-neutral-800 text-neutral-400 hover:border-neutral-600">profile</a>
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
                  <ScoreBar value={sc.overall_score     ?? 0} label="overall" />
                  <ScoreBar value={sc.automation_score  ?? 0} label="automation" />
                  <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
                  <ScoreBar value={sc.expansion_score   ?? 0} label="expansion" />
                  <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
                </div>
              </div>

              {loading && (
                <p className="text-sm text-neutral-400 animate-pulse py-3">generating AI analysis&hellip;</p>
              )}

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
                    <span><span className="font-semibold text-neutral-200">Signal-based timing:</span> Their {signals.length >= 3 ? 'hot signals' : 'signals'} show they're in market RIGHT NOW — strike while iron is hot with relevant solutions</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ── ROBOT MATCH tab ── */}
          {activeTab === 'robot match' && (
            <div className="space-y-4">
              {loading && <p className="text-sm text-neutral-400 animate-pulse py-3">matching robots&hellip;</p>}
              {!loading && (profile?.robot_match || []).length === 0 && (
                <p className="text-sm text-neutral-500">No robot recommendations available.</p>
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
                    <p key={j} className="text-xs text-neutral-500 leading-relaxed">▸ {uc}</p>
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
                            {!['Logistics', 'Hospitality', 'Food Service', 'Healthcare'].includes(lead.industry) && 'Automation adoption accelerating across industry'}
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
                          {!['Logistics', 'Hospitality', 'Food Service'].includes(lead.industry) && (
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
                          {!['Logistics', 'Hospitality', 'Food Service'].includes(lead.industry) && '⚠️ ASSESS - Evaluate automation maturity in industry vertical'}
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
          {activeTab === 'signals' && (
            <div className="space-y-2">
              <p className="label mb-3">signals &middot; {lead.signal_count || profile?.signal_count || 0}</p>
              {((profile?.signals?.length ? profile.signals : lead.signals) || []).map((s, i) => (
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
              {(profile?.signals?.length === 0 && (lead.signals || []).length === 0) && (
                <p className="text-sm text-neutral-500">No signals recorded yet.</p>
              )}
            </div>
          )}

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
      const r = await fetch(`${API}/api/search?${params}`);
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
                      className="border border-neutral-800 rounded px-4 py-3 hover:border-neutral-600 transition-colors group">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-base font-semibold text-neutral-100 group-hover:text-white transition-colors">
                            {r.company_name}
                          </span>
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
                        <div className="space-y-1.5 mt-1">
                          {r.matched_signals.map((s, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <SignalBadge type={s.signal_type} />
                              <span className="text-xs text-neutral-300 flex-1 leading-relaxed">{s.signal_text}</span>
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
              Sign Up Free →
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

  function quickSave(lead) {
    try {
      const store = JSON.parse(localStorage.getItem('rfr_saved') || '{"companies":[],' + '"lists":[]}');
      if (!store.companies) store.companies = [];
      const alreadySaved = !!store.companies.find(c => c.id === lead.id);
      if (alreadySaved) {
        store.companies = store.companies.filter(c => c.id !== lead.id);
      } else {
        store.companies.push({
          id: lead.id, name: lead.company_name, industry: lead.industry,
          score: lead.score?.overall_score ?? 0, tier: lead.priority_tier,
          saved_at: new Date().toISOString(), website: lead.website,
        });
      }
      localStorage.setItem('rfr_saved', JSON.stringify(store));
      setSavedIds(new Set(store.companies.map(c => c.id)));
    } catch {}
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
    p.set('exclude_junk', excludeJunk);
    p.set('min_score', minScore);
    p.set('sort', sort);
    if (tier !== 'ALL')     p.set('tier', tier);
    if (industry !== 'All') p.set('industry', industry);
    if (sigType)            p.set('signal_type', sigType);
    return p.toString();
  }, [tier, industry, minScore, sigType, excludeJunk, sort]);

  // Fetch live signals for ticker
  const fetchLiveSignals = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/leads?limit=20&sort=signals_detected_at`);
      if (res.ok) {
        const allLeads = await res.json();
        // Extract unique signals from recent leads
        const signals = [];
        allLeads.forEach(lead => {
          if (lead.signals && lead.signals.length > 0) {
            lead.signals.slice(0, 2).forEach(sig => {
              signals.push({
                company: lead.company_name,
                type: sig.signal_type || 'news',
                industry: lead.industry,
                lead: lead
              });
            });
          }
        });
        setLiveSignals(signals.slice(0, 15)); // Keep top 15 for ticker
      }
    } catch (e) {
      console.error('Failed to fetch live signals:', e);
    }
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [leadsRes, summaryRes, healthRes] = await Promise.all([
        fetch(`${API}/api/leads?${buildQuery()}`),
        fetch(`${API}/api/leads/summary?exclude_junk=${excludeJunk}`),
        fetch(`${API}/api/scraper-health`),
      ]);
      if (leadsRes.ok)   setLeads(await leadsRes.json());
      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (healthRes.ok)  setHealth(await healthRes.json());
      setError(null);
      
      // Also fetch live signals
      await fetchLiveSignals();
    } catch (e) {
      setError('Cannot reach API -- start the server: python -m uvicorn app.main:app --reload');
    } finally {
      setLoading(false);
      setLast(new Date().toLocaleTimeString());
    }
  }, [buildQuery, excludeJunk, fetchLiveSignals]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    const t = setInterval(fetchData, 30_000);
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
    !search || (l.company_name || '').toLowerCase().includes(search.toLowerCase())
  );

  async function handleResetAll() {
    setResetting(true);
    await fetch(`${API}/api/scraper-health/reset-all`, { method: 'POST' });
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
      <div className="min-h-screen bg-[#080808] px-4 py-6 md:px-8 md:py-8 max-w-[1400px] mx-auto">

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

      {/* header */}
      <header className="mb-6 md:mb-10">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="mb-2">
              {/* READY → ROBOTS Wordmark - Option 4 */}
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-1">
                <span className="text-white">READY</span>
                <span className="mx-2"
                  style={{
                    background: 'linear-gradient(135deg, #10B981 0%, #06B6D4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                  →
                </span>
                <span
                  style={{
                    background: 'linear-gradient(135deg, #10B981 0%, #06B6D4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    textShadow: '0 0 30px rgba(16, 185, 129, 0.3)',
                    fontWeight: '900',
                    letterSpacing: '0.02em'
                  }}>
                  ROBOTS
                </span>
              </h1>
              <p className="text-xs md:text-sm text-neutral-400">Intent Signal Intelligence → Sales-Ready Leads</p>
            </div>
          </div>
          
          {/* Mobile: Just hamburger menu */}
          <div className="md:hidden relative">
            <button 
              onClick={() => setShowMenu(!showMenu)}
              className="btn-ghost border-neutral-700 text-neutral-400 hover:border-neutral-500 px-3 text-xl">
              ☰
            </button>
            {showMenu && (
              <div className="absolute right-0 top-full mt-2 w-56 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
                <button onClick={() => { fetchData(); setShowMenu(false); }}
                  className="w-full text-left px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                  &#8635; Refresh Data
                </button>
                <Link href="/search" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    🔍 Intelligence Search
                  </div>
                </Link>
                <Link href="/roi-calculator" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-yellow-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    💰 ROI Calculator
                  </div>
                </Link>
                <Link href="/pilot-calculator" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    🧪 Pilot Calculator
                  </div>
                </Link>
                <Link href="/robot-ready" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    🤖 Robot Ready
                  </div>
                </Link>
                <Link href="/profile" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    ♡ Profile
                  </div>
                </Link>
                <Link href="/admin" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    ⚙️ Admin Panel
                  </div>
                </Link>
                <Link href="/brief" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    📋 Strategy Brief
                  </div>
                </Link>
                <Link href="/about" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer">
                    ⚡ Signal Intelligence
                  </div>
                </Link>
              </div>
            )}
          </div>
        </div>
        
        {/* Desktop: Full nav bar */}
        <div className="hidden md:flex items-center gap-3 flex-wrap">
          {!session && usageCount < FREE_LIMIT && (
            <span className="text-[10px] border border-emerald-800 text-emerald-400 px-2 py-1 rounded">
              {FREE_LIMIT - usageCount} free searches left
            </span>
          )}
          {lastRefresh && <span className="label text-neutral-500">{lastRefresh}</span>}
          <button onClick={fetchData} className="btn-ghost">&#8635; refresh</button>
          <Link href="/roi-calculator" className="btn-ghost border-yellow-800 text-yellow-400 hover:border-yellow-600">💰 ROI Calc</Link>
          <Link href="/pilot-calculator" className="btn-ghost border-cyan-800 text-cyan-400 hover:border-cyan-600">🧪 Pilot Calc</Link>
          <Link href="/robot-ready" className="btn-ghost border-emerald-800 text-emerald-400 hover:border-emerald-600">🤖 Robot Ready</Link>
          <Link href="/profile" className="btn-ghost border-neutral-700 text-neutral-500 hover:border-neutral-500">♡ profile</Link>
          {session
            ? <span className="label text-neutral-400 text-xs hidden md:inline">{session.user.email.split('@')[0]}</span>
            : (
              <Link href="/login"
                className="btn-ghost text-xs border-neutral-800 text-neutral-400 hover:border-neutral-600"
                title="Browse freely — sign in only to save companies and reports">
                → sign in to save
              </Link>
            )}
          
          {/* Hamburger Menu */}
          <div className="relative">
            <button 
              onClick={() => setShowMenu(!showMenu)}
              className="btn-ghost border-neutral-700 text-neutral-400 hover:border-neutral-500 px-3">
              ☰
            </button>
            {showMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
                <Link href="/search" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    🔍 Intelligence Search
                  </div>
                </Link>
                <Link href="/admin" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    ⚙️ Admin Panel
                  </div>
                </Link>
                <Link href="/brief" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 cursor-pointer border-b border-neutral-800">
                    📋 Strategy Brief
                  </div>
                </Link>
                <Link href="/about" onClick={() => setShowMenu(false)}>
                  <div className="px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 cursor-pointer">
                    ⚡ Signal Intelligence
                  </div>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* error */}
      {error && (
        <div className="mb-6 border border-red-900 rounded px-4 py-3 text-red-400 text-xs">
          &#9888; {error}
        </div>
      )}

      {/* Mobile filter button (visible on small screens) */}
      <div className="lg:hidden mb-6">
        <button onClick={() => setShowMobileFilters(!showMobileFilters)}
          className="w-full flex items-center justify-between px-4 py-3 border border-neutral-800 rounded hover:border-neutral-700 transition-colors">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-neutral-300">Filters & Stats</span>
            {(tier !== 'ALL' || industry !== 'All' || sigType || search || minScore > 0) && (
              <span className="px-2 py-0.5 bg-emerald-900/50 border border-emerald-700 rounded text-[10px] text-emerald-400 font-semibold">
                {[tier !== 'ALL', industry !== 'All', sigType, search, minScore > 0].filter(Boolean).length} active
              </span>
            )}
          </div>
          <span className="text-neutral-500">{showMobileFilters ? '▼' : '▶'}</span>
        </button>

        {/* Mobile filters dropdown */}
        {showMobileFilters && (
          <div className="mt-4 border border-neutral-800 rounded-lg p-4 space-y-4 bg-neutral-900/50">
            {/* Stats summary */}
            <div className="grid grid-cols-2 gap-3">
              <div className="border border-neutral-800 rounded p-3">
                <span className="label block mb-1">Total</span>
                <span className="text-2xl font-bold text-neutral-200">{summary.total ?? leads.length}</span>
              </div>
              <button onClick={() => { setTier('HOT'); setIndustry('All'); setSearch(''); setShowMobileFilters(false); }}
                className="border border-red-900 rounded p-3 text-left hover:bg-red-900/10 transition-colors">
                <span className="label block mb-1 text-neutral-500">HOT</span>
                <span className="text-2xl font-bold text-red-400">{summary.hot ?? 0}</span>
              </button>
            </div>

            {/* Filters */}
            <div>
              <label className="label block mb-2">Search</label>
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="company name..."
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-emerald-600" />
            </div>

            <div>
              <label className="label block mb-2">Priority: <span className="text-emerald-400">{tier}</span></label>
              <div className="grid grid-cols-4 gap-2">
                {TIERS.map(t => (
                  <button key={t} onClick={() => setTier(t)}
                    className={`px-3 py-2 rounded text-xs font-medium ${tier === t ? 'bg-emerald-900/50 border border-emerald-700 text-emerald-400' : 'border border-neutral-800 text-neutral-400'}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label block mb-2">Industry</label>
              <select value={industry} onChange={e => setIndustry(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm text-neutral-300">
                {INDUSTRIES.map(ind => (<option key={ind} value={ind}>{ind}</option>))}
              </select>
            </div>

            {(tier !== 'ALL' || industry !== 'All' || sigType || search || minScore > 0) && (
              <button onClick={() => {
                setTier('ALL'); setIndustry('All'); setSigType(''); setSearch(''); setMinScore(0);
              }} className="w-full text-xs text-neutral-400 hover:text-emerald-400 py-2 border border-neutral-800 rounded">
                ✕ Clear all
              </button>
            )}
          </div>
        )}
      </div>

      {/* Two-column layout */}
      <div className="flex gap-6">
        
        {/* Mobile filter toggle button */}
        <button 
          onClick={() => setShowMobileFilters(!showMobileFilters)}
          className="lg:hidden fixed bottom-6 right-6 z-40 bg-emerald-700 hover:bg-emerald-600 text-white px-4 py-3 rounded-full shadow-lg border-2 border-emerald-500 flex items-center gap-2">
          <span className="text-sm font-semibold">Filters</span>
          <span className="text-xs">({tier !== 'ALL' || industry !== 'All' || search ? '●' : '○'})</span>
        </button>

        {/* LEFT COLUMN - Filters & Controls */}
        <aside className={`
          w-80 shrink-0 space-y-6 
          lg:sticky lg:top-6 lg:self-start lg:block lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto sidebar-scroll
          ${
            showMobileFilters 
              ? 'fixed inset-0 z-50 bg-[#080808] p-4 overflow-y-auto block' 
              : 'hidden'
          }
        `}>
          
          {/* Mobile close button */}
          <button 
            onClick={() => setShowMobileFilters(false)}
            className="lg:hidden mb-4 w-full bg-neutral-800 hover:bg-neutral-700 text-white px-4 py-2 rounded text-sm font-medium">
            ✕ Close Filters
          </button>
          
          {/* Quick Stats */}
          <div className="border border-neutral-800 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold tracking-widest uppercase text-neutral-400">Pipeline Overview</h3>
              <span className="text-[9px] text-neutral-600 border border-neutral-800 px-2 py-0.5 rounded">Live</span>
            </div>
            
            <div className="bg-gradient-to-br from-neutral-900/50 to-transparent border border-neutral-800 rounded p-3">
              <span className="label block mb-1 text-emerald-400 font-semibold">Total Leads</span>
              <span className="text-3xl font-bold text-white tabular-nums">
                {summary.total ?? leads.length}
              </span>
              <p className="text-[9px] text-neutral-600 mt-1">Active opportunities in database</p>
            </div>

            <div className="flex items-center gap-2 text-[9px] text-neutral-600 px-1">
              <span className="inline-block h-1 w-1 rounded-full bg-cyan-500 animate-pulse"></span>
              <span>Auto-refreshes every 30 seconds</span>
            </div>

            <div className="h-px bg-neutral-800" />
            
            <button onClick={() => { setTier('HOT'); setIndustry('All'); setSearch(''); }}
              className="w-full text-left p-3 border border-neutral-800 rounded hover:border-red-800 transition-colors group bg-gradient-to-br from-red-950/10 to-transparent hover:from-red-950/20">
              <div className="flex items-center justify-between">
                <span className="label text-emerald-400 font-semibold group-hover:text-red-400 transition-colors">HOT</span>
                <span className="text-2xl font-bold text-red-400 tabular-nums">{summary.hot ?? 0}</span>
              </div>
            </button>

            <button onClick={() => { setTier('WARM'); setIndustry('All'); setSearch(''); }}
              className="w-full text-left p-3 border border-neutral-800 rounded hover:border-yellow-800 transition-colors group">
              <div className="flex items-center justify-between">
                <span className="label text-emerald-400 font-semibold group-hover:text-yellow-400 transition-colors">WARM</span>
                <span className="text-2xl font-bold text-yellow-500 tabular-nums">{summary.warm ?? 0}</span>
              </div>
            </button>

            <button onClick={() => { setTier('COLD'); setIndustry('All'); setSearch(''); }}
              className="w-full text-left p-3 border border-neutral-800 rounded hover:border-cyan-900 transition-colors group">
              <div className="flex items-center justify-between">
                <span className="label text-emerald-400 font-semibold group-hover:text-cyan-400 transition-colors">COLD</span>
                <span className="text-2xl font-bold text-cyan-500 tabular-nums">{summary.cold ?? 0}</span>
              </div>
            </button>

            <div className="h-px bg-neutral-800" />

            <div className="flex items-center justify-between">
              <span className="label">Junk filtered</span>
              <span className="text-lg font-semibold text-neutral-500 tabular-nums">{summary.junk_filtered ?? 0}</span>
            </div>

            {openCircuits > 0 && (
              <>
                <div className="h-px bg-neutral-800" />
                <div className="flex items-center justify-between p-2 border border-red-900 rounded">
                  <span className="label text-red-400">Open circuits</span>
                  <span className="text-lg font-semibold text-red-500 tabular-nums">&#9889; {openCircuits}</span>
                </div>
              </>
            )}
          </div>

          {/* Filters */}
          <div className="border border-neutral-800 rounded-lg p-4 space-y-4">
            <h3 className="text-xs font-semibold tracking-widest uppercase text-neutral-300 mb-3">Filters</h3>
            
            <div>
              <label className="label block mb-2 text-neutral-300">Search Companies</label>
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="company name..."
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm
                           text-neutral-100 placeholder-neutral-600
                           focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-900
                           transition-colors" />
            </div>

            <div>
              <label className="label block mb-2">
                Min Score <span className="text-emerald-400 font-semibold">{minScore}</span>
              </label>
              <input type="range" min={0} max={100} value={minScore}
                onChange={e => setMinScore(Number(e.target.value))}
                className="w-full accent-emerald-500" />
              <div className="flex justify-between text-[10px] text-neutral-500 mt-1">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <div>
              <label className="label block mb-2">Priority Tier</label>
              <div className="grid grid-cols-2 gap-2">
                {TIERS.map(t => (
                  <button key={t} onClick={() => setTier(t)}
                    className={`px-3 py-2 rounded text-xs font-medium transition-all ${
                      tier === t 
                        ? 'bg-emerald-900/50 border border-emerald-700 text-emerald-400' 
                        : 'border border-neutral-800 text-neutral-400 hover:border-neutral-700'
                    }`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label block mb-2">Industry</label>
              <select value={industry} onChange={e => setIndustry(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm
                           text-neutral-300 focus:outline-none focus:border-emerald-600">
                {INDUSTRIES.map(ind => (
                  <option key={ind} value={ind}>{ind}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label block mb-2">Signal Type</label>
              <select value={sigType} onChange={e => setSigType(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm
                           text-neutral-300 focus:outline-none focus:border-emerald-600">
                <option value="">All Signals</option>
                {SIGNAL_TYPES.filter(Boolean).map(st => (
                  <option key={st} value={st}>{SIGNAL_META[st]?.label || st}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label block mb-2">Sort By</label>
              <select value={sort} onChange={e => setSort(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-3 py-2 text-sm
                           text-neutral-300 focus:outline-none focus:border-emerald-600">
                <option value="score">Score (High → Low)</option>
                <option value="signals">Signal Count</option>
                <option value="name">Company Name</option>
              </select>
            </div>

            <div className="h-px bg-neutral-800" />

            <label className="flex items-center gap-3 cursor-pointer select-none">
              <input type="checkbox" checked={excludeJunk} onChange={e => setExcludeJunk(e.target.checked)}
                className="sr-only peer" />
              <div className="w-10 h-5 bg-neutral-800 rounded-full peer-checked:bg-emerald-900 transition-colors relative">
                <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-neutral-600 peer-checked:bg-emerald-500 rounded-full transition-all ${excludeJunk ? 'translate-x-5' : ''}`} />
              </div>
              <span className="text-xs text-neutral-400">
                {excludeJunk ? 'Hiding junk leads' : 'Showing all leads'}
              </span>
            </label>

            {(tier !== 'ALL' || industry !== 'All' || sigType || search || minScore > 0) && (
              <>
                <div className="h-px bg-neutral-800" />
                <button onClick={() => {
                  setTier('ALL');
                  setIndustry('All');
                  setSigType('');
                  setSearch('');
                  setMinScore(0);
                }}
                  className="w-full text-xs text-neutral-400 hover:text-emerald-400 transition-colors py-2 border border-neutral-800 rounded hover:border-neutral-700">
                  ✕ Clear all filters
                </button>
              </>
            )}
          </div>

          {/* Quick Scrape */}
          <QuickScrape onDone={fetchData} />

        </aside>

        {/* RIGHT COLUMN - Main Content */}
        <main className="flex-1 min-w-0 space-y-6">
          
          {/* Recent Activity - Inline text only */}
          {!loading && leads.length > 0 && (() => {
            const hotLead = leads.filter(l => l.priority_tier === 'HOT').sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))[0];
            const warmLead = leads.filter(l => l.priority_tier === 'WARM')[0];
            const signalLead = leads.filter(l => l.signals && l.signals.length > 0).sort((a, b) => b.signal_count - a.signal_count)[0];
            
            return (
              <div className="text-sm text-neutral-500 flex items-center gap-3 flex-wrap">
                {hotLead && (
                  <span>
                    Latest HOT: <button onClick={() => setSelectedLead(hotLead)} className="text-red-400 hover:text-red-300 underline">{hotLead.company_name}</button>
                  </span>
                )}
                {warmLead && (
                  <span>
                    Latest WARM: <button onClick={() => setSelectedLead(warmLead)} className="text-yellow-400 hover:text-yellow-300 underline">{warmLead.company_name}</button>
                  </span>
                )}
                {signalLead && (
                  <span>
                    Latest signal: <button onClick={() => setSelectedLead(signalLead)} className="text-cyan-400 hover:text-cyan-300 underline">{signalLead.company_name}</button>
                  </span>
                )}
                <span>·</span>
                <span>{summary.total} total</span>
              </div>
            );
          })()}

          {/* Live Signal Ticker - horizontal scrolling stream */}
          {!loading && liveSignals.length > 0 && (
            <div className="border-t border-b border-neutral-800 py-2.5 px-4 bg-neutral-950/50 overflow-hidden">
              <div className="flex items-center gap-3 text-xs">
                <span className="shrink-0 flex items-center gap-1.5 text-neutral-500 font-medium">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Live Signals:
                </span>
                <div className="flex-1 overflow-hidden">
                  <div className="flex gap-3 animate-ticker whitespace-nowrap">
                    {liveSignals.concat(liveSignals).map((sig, idx) => {
                      const sigMeta = SIGNAL_META[sig.type] || { label: sig.type, text: 'text-neutral-400' };
                      return (
                        <button
                          key={idx}
                          onClick={() => setSelectedLead(sig.lead)}
                          className="inline-flex items-center gap-1.5 hover:opacity-80 transition-opacity"
                        >
                          <span className="text-cyan-400 hover:text-cyan-300 underline decoration-dotted">
                            {sig.company}
                          </span>
                          <span className={`${sigMeta.text} font-semibold`}>({sigMeta.label})</span>
                          <span className="text-neutral-700">→</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* CTA - Enhanced Visual Design */}
          <div className="mb-6 rounded-lg overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              boxShadow: '0 0 30px rgba(16, 185, 129, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05)'
            }}>
            <div className="px-6 py-5 md:px-8 md:py-6">
              {/* Headline with stronger copy */}
              <div className="mb-4">
                <h2 className="text-3xl md:text-4xl font-bold mb-2"
                  style={{
                    background: 'linear-gradient(135deg, #10B981 0%, #06B6D4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    letterSpacing: '-0.02em'
                  }}>
                  Find Your Next 5 Customers
                </h2>
                <p className="text-base md:text-lg text-neutral-300 leading-relaxed">
                  Get instant access to automation-ready prospects with active buying signals — in 30 seconds.
                </p>
              </div>

              {/* Benefits Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
                <div className="flex items-start gap-2">
                  <div className="text-emerald-400 text-lg mt-0.5">⚡</div>
                  <div>
                    <div className="text-sm font-semibold text-neutral-200">Instant Results</div>
                    <div className="text-xs text-neutral-400">5 qualified prospects in seconds</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-cyan-400 text-lg mt-0.5">🎯</div>
                  <div>
                    <div className="text-sm font-semibold text-neutral-200">Active Intent Signals</div>
                    <div className="text-xs text-neutral-400">Funding, hiring, expansion alerts</div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-emerald-400 text-lg mt-0.5">📋</div>
                  <div>
                    <div className="text-sm font-semibold text-neutral-200">Engagement Playbook</div>
                    <div className="text-xs text-neutral-400">8-week outreach strategy included</div>
                  </div>
                </div>
              </div>

              {/* Input + Button with better hierarchy */}
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Enter your robotics company URL..."
                  className="flex-1 px-5 py-3 rounded-lg text-sm bg-neutral-900/80 border border-neutral-700/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-emerald-500/50 focus:bg-neutral-900 transition-all"
                  style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)' }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const url = e.target.value.trim();
                      if (url) {
                        window.location.href = `/pipeline-results?company=${encodeURIComponent(url)}`;
                      }
                    }
                  }}
                />
                <button
                  onClick={(e) => {
                    const input = e.target.closest('div').querySelector('input');
                    const url = input.value.trim();
                    if (url) {
                      window.location.href = `/pipeline-results?company=${encodeURIComponent(url)}`;
                    }
                  }}
                  className="px-8 py-3 rounded-lg font-semibold text-sm sm:text-base border border-emerald-500 text-emerald-400 hover:border-emerald-400 hover:text-emerald-300 transition-all duration-200 whitespace-nowrap bg-transparent"
                >
                  Get My Pipeline →
                </button>
              </div>

              {/* Social proof */}
              <p className="text-xs text-neutral-500 mt-3 text-center sm:text-left">
                ✓ No signup required · ✓ See results instantly · ✓ Free to try
              </p>
            </div>
          </div>

          {/* strategic snapshot */}
          {!loading && leads.length > 0 && (
            <StrategicSnapshot leads={leads} onSelect={setSelectedLead} />
          )}

          {/* agent insights */}
          <AgentInsightsPanel />

      {/* lead list */}
      {loading ? (
        <p className="py-16 text-center text-neutral-700 text-sm animate-pulse">loading...</p>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-neutral-700 text-sm">
          no leads match your filters
          {leads.length === 0 && (
            <p className="mt-2 text-xs text-neutral-800">
              run <code className="border border-neutral-800 rounded px-1 text-neutral-600">python scripts/test_scraper.py --clear</code> to seed
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {INDUSTRIES.filter(ind => ind !== 'All').map(ind => {
            const group = filtered.filter(l => (l.industry || 'Unknown') === ind);
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
                  className="w-full flex items-center gap-2 py-2 mb-1 border-b border-neutral-700 group hover:border-neutral-500 transition-colors text-left cursor-pointer">
                  <span className="text-[11px] font-semibold tracking-widest uppercase text-neutral-400 group-hover:text-white transition-colors">
                    {ind}
                  </span>
                  {hotCount  > 0 && <span className="label text-red-400 tabular-nums">{hotCount} hot</span>}
                  {warmCount > 0 && <span className="label text-yellow-500 tabular-nums">{warmCount} warm</span>}
                  <span className="label text-neutral-700 ml-auto tabular-nums">
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

        <span className="label w-6 text-right shrink-0 mt-0.5">#{i+1}</span>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-lg font-semibold text-neutral-100">{lead.company_name}</span>
                      <TierBadge tier={lead.priority_tier} />
                      {/* Signal count badge instead of individual badges */}
                      {(lead.signals || []).length > 0 && (
                        <span className="text-[10px] border border-cyan-800 text-cyan-400 px-2 py-0.5 rounded">
                          {lead.signal_count} signal{lead.signal_count !== 1 ? 's' : ''}
                        </span>
                      )}
                      {lead.location_city && (
                        <span className="text-[10px] text-neutral-500">
                          {lead.location_city}{lead.location_state ? `, ${lead.location_state}` : ''}
                        </span>
                      )}
                    </div>
                    {/* Move AI Analysis button to separate line for cleaner layout */}
                    <div className="flex gap-2 mt-1.5">
                      <button
                        className="text-xs text-emerald-400 hover:text-emerald-300 underline decoration-dotted transition-colors"
                        onClick={e => { e.stopPropagation(); setSelectedLead(lead); }}>
                        → View Analysis
                      </button>
                    </div>
                  </div>

                  {/* score -- text only, no pill bg */}
                  <div className="shrink-0 text-right">
                    <ScoreNum value={sc.overall_score ?? 0} />
                    <span className="label block">score</span>
                  </div>

                  {/* Click indicator */}
                  <button 
                    className="shrink-0 px-3 py-1 text-[10px] border border-cyan-700 text-cyan-400 
                               rounded hover:border-cyan-500 hover:text-cyan-300 transition-colors"
                    onClick={(e) => { e.stopPropagation(); setExpanded(p => ({ ...p, [lead.id]: !p[lead.id] })); }}>
                    {isOpen ? 'close' : 'click here'}
                  </button>

                  <span className={`label mt-1 ${tm.text}`}>{isOpen ? 'v' : '>'}</span>
                </div>

                {/* score bars */}
                <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-5 pl-10">
                  <ScoreBar value={sc.automation_score ?? 0} label="automation" />
                  <ScoreBar value={sc.labor_pain_score  ?? 0} label="labor pain" />
                  <ScoreBar value={sc.expansion_score   ?? 0} label="expansion"  />
                  <ScoreBar value={sc.market_fit_score  ?? 0} label="market fit" />
                  <ScoreBar value={sc.overall_score     ?? 0} label="overall"    />
                </div>

                {/* priority reasons -- inline text */}
                {lead.priority_reasons?.length > 0 && (
                  <p className="mt-2 pl-10 text-[10px] text-neutral-500">
                    {lead.priority_reasons.join('  ·  ')}
                  </p>
                )}

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

                    {(lead.signals || []).length > 0 && (
                      <div>
                        <p className="label mb-2">signals &middot; {lead.signal_count}</p>
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
                            {(lead.signals || []).map((s, si) => (
                              <tr key={si} className="border-b border-neutral-900 align-top">
                                <td className="py-1.5 pr-4"><SignalBadge type={s.signal_type} /></td>
                                <td className="py-1.5 pr-4 tabular-nums">
                                  <span className={`font-mono ${
                                    s.strength >= 0.7 ? 'text-emerald-400'
                                    : s.strength >= 0.4 ? 'text-cyan-500'
                                    : 'text-neutral-600'
                                  }`}>
                                    {(s.strength * 100).toFixed(0)}%
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
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
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
        </div>
      )}

      {/* scraper health */}
      {health && (
        <div className="mt-12 border-t border-neutral-800 pt-6">
          <div className="flex items-center justify-between mb-4">
            <span className="label">scraper health</span>
            <button onClick={handleResetAll} disabled={resetting || openCircuits === 0}
              className="btn-danger">
              {resetting ? 'resetting...' : 'reset circuits'}
            </button>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs mb-4 text-neutral-600">
            <span>tracked &mdash; <span className="text-neutral-400">{health.summary?.total_urls_tracked ?? 0}</span></span>
            <span>healthy &mdash; <span className="text-emerald-500">{health.summary?.healthy_urls ?? 0}</span></span>
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
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-neutral-800">
                  {['', 'url', 'failures', 'restarts', 'last seen'].map(h => (
                    <th key={h} className="label pb-2 pr-6 text-left font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(health.url_health).map(([url, info]) => (
                  <tr key={url} className="border-b border-neutral-900">
                    <td className="py-1.5 pr-4"><HealthDot open={info.circuit_open} /></td>
                    <td className="py-1.5 pr-6 max-w-[14rem] truncate text-neutral-600" title={url}>
                      {url.replace(/^https?:\/\//, '').substring(0, 45)}
                    </td>
                    <td className="py-1.5 pr-6 tabular-nums text-neutral-600">{info.consecutive_failures}</td>
                    <td className="py-1.5 pr-6 tabular-nums text-neutral-600">{info.restart_count}</td>
                    <td className="py-1.5 text-neutral-700">
                      {info.last_success
                        ? new Date(info.last_success * 1000).toLocaleTimeString()
                        : 'never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-neutral-800">no urls tracked -- run a scraper first</p>
          )}
        </div>
      )}

        </main>
      </div>

      <footer className="mt-16 text-center label">
        ready for robots &middot; automation signal platform &middot; refreshes every 30s
      </footer>
    </div>
    </>
  );
}
