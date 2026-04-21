import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import Image from 'next/image';
import LoginDropdown from '../components/LoginDropdown';
import HotDealsScoringExplainer from '../components/HotDealsScoringExplainer';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { companyExternalHref } from '../lib/companyExternalHref';
import { COMPANY_NAME_LINK_CLASS } from '../lib/companyNameLinkClass';
import { AutomationSpecBlock } from '../lib/automationProfile';
import { stripHtml } from '../lib/plainText';
// signalsDisplay helpers used in dashboard; index.js relies on API-side dedup/cap

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

/** Hero stat cells: live summary counts, or em dash while the first homepage fetch is in flight. */
function formatHeroCount(value, statsLoaded) {
  if (!statsLoaded) return '—';
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString();
}

/** Short opportunity line for hero CRM (blurb → summary → signal → industry). */
function opportunityLine(lead) {
  if (!lead || typeof lead !== 'object') return '';
  const blurb = stripHtml(lead.share_blurb);
  if (blurb.length > 24 && !/^https?:\/\//i.test(blurb)) {
    return blurb.length > 130 ? `${blurb.slice(0, 127)}…` : blurb;
  }
  const summary = stripHtml(lead.share_summary);
  if (summary.length > 24) {
    const dot = summary.indexOf('. ');
    const first = (dot > 0 ? summary.slice(0, dot + 1) : summary).trim();
    const t = first.length > 140 ? `${first.slice(0, 137)}…` : first;
    if (t.length > 20) return t;
  }
  const sigs = lead.signals || [];
  const top = sigs[0];
  const raw = stripHtml(top?.raw_text);
  if (raw.length > 12) {
    return raw.length > 120 ? `${raw.slice(0, 117)}…` : raw;
  }
  const ind = (lead.industry || '').trim();
  if (ind && ind.toLowerCase() !== 'new') {
    return `Automation fit in ${ind} — explore signals on the dashboard.`;
  }
  return '';
}

function extractLeadPreviews(data) {
  if (!Array.isArray(data)) return [];
  return data
    .map((lead) => {
      const name = lead?.company_name && String(lead.company_name).trim();
      if (!name) return null;
      return { name, opp: opportunityLine(lead) };
    })
    .filter(Boolean);
}

/** One card per buyer name — duplicate DB rows (same company ingested twice) collapse for UI. */
function dedupeHomepageLeads(leads) {
  if (!Array.isArray(leads)) return [];
  const seen = new Set();
  return leads.filter((l) => {
    const k = (l.company_name || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if (!k) return true;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

/** Rotating { name, opp } rows (stable modulo). */
function previewAt(rows, idx) {
  if (!rows || rows.length === 0) return null;
  const i = Number(idx) || 0;
  return rows[i % rows.length];
}

export default function Signals() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  /** Set when the batched homepage request fails after retries (mobile networks, cold start). */
  const [homepageError, setHomepageError] = useState(null);
  /** Increment to re-run the homepage fetch (Retry button). */
  const [homepageRetryTick, setHomepageRetryTick] = useState(0);
  /** Avoid stale closure: homepage poll must not re-trigger full-page spotlight loading. */
  const homepageFetchCompletedRef = useRef(false);
  
  // Stats from GET /api/leads/homepage — summary uses same tiering as dashboard (junk excluded)
  const [statsData, setStatsData] = useState({
    activeLeads: 0,
    hotDeals: 0,
    liveSignals: 0,
    warmPipeline: 0,
    cold: 0
  });
  const [statsLoaded, setStatsLoaded] = useState(false);
  // Leads per industry (e.g. { Logistics: 400, Hospitality: 275 })
  const [leadsByIndustry, setLeadsByIndustry] = useState({});
  
  // Live signal flow state (pythh.ai style)
  const [signalFlow, setSignalFlow] = useState({
    labor_shortage: { value: 0.67, delta: 0, prev: 0.67 },
    expansion: { value: 0.54, delta: 0, prev: 0.54 },
    safety: { value: 0.71, delta: 0, prev: 0.71 }
  });

  // Hot leads state - will be fetched from API
  const [hotLeads, setHotLeads] = useState([]);
  const [tierLegend, setTierLegend] = useState(null);
  const [scoringSystem, setScoringSystem] = useState(null);

  // ── Hero feed rotation ────────────────────────────────────────────────────
  const FEED_VISIBLE  = 5;   // rows shown at once
  const FEED_INTERVAL = 3200; // ms between rotations
  const [feedOffset, setFeedOffset]       = useState(0);
  const [feedExiting, setFeedExiting]     = useState(false); // top row fading out
  const [feedEntering, setFeedEntering]   = useState(false); // bottom row fading in

  // Expanded deal for inline details
  const [expandedDealId, setExpandedDealId] = useState(null);
  // Which hot lead card has share menu open (for social share dropdown)
  const [shareMenuLeadId, setShareMenuLeadId] = useState(null);
  const [pipelineModalOpen, setPipelineModalOpen] = useState(false);
  const [pipelineModalInput, setPipelineModalInput] = useState('');

  /** Rotating company + opportunity lines per tier; from /api/leads + spotlight fallback */
  const [crmPreviewLists, setCrmPreviewLists] = useState({ active: [], hot: [], warm: [] });
  const [crmNameSpin, setCrmNameSpin] = useState({ active: 0, hot: 0, warm: 0 });

  // Rotating automation quotes from real news/signals
  const [currentQuoteIndex, setCurrentQuoteIndex] = useState(0);
  const automationQuotes = [
    { text: "\"We're looking at AMRs to handle overnight shifts we can't staff\"", company: "Midwest Distribution Center", signal: "Labor Shortage" },
    { text: "\"Labor costs are up 35% - automation ROI is finally positive\"", company: "Pacific Hotel Chain", signal: "Cost Pressure" },
    { text: "\"Our warehouse runs 24/7 but we can only find workers for 16 hours\"", company: "E-Commerce Fulfillment", signal: "Capacity Gap" },
    { text: "\"We need to double throughput without adding headcount\"", company: "Food Processing Plant", signal: "Productivity" },
    { text: "\"New facility opening Q2 - can't hire fast enough for ramp-up\"", company: "Logistics Expansion", signal: "Expansion" },
    { text: "\"Turnover is killing us - robots don't quit after 3 months\"", company: "QSR Chain", signal: "High Turnover" },
    { text: "\"OSHA citations for repetitive strain - need to automate packaging\"", company: "Manufacturing Site", signal: "Safety Risk" },
    { text: "\"Evaluating palletizing robots to eliminate back injuries\"", company: "Cold Storage Warehouse", signal: "Automation Intent" },
    { text: "\"Hospital lab can't find technicians - looking at automated specimen processing\"", company: "Regional Medical Center", signal: "Medical Tech" },
    { text: "\"Pharmacy automation could cut dispensing errors by 99%\"", company: "Healthcare System", signal: "Patient Safety" },
    { text: "\"Airport terminal cleaning requires 50 workers - only have 30\"", company: "International Airport", signal: "Staffing Crisis" },
    { text: "\"Our retail stores need overnight shelf scanning but no staff available\"", company: "Grocery Chain", signal: "Retail Automation" },
    { text: "\"Food processing line down 40% capacity due to worker shortage\"", company: "Food Manufacturing", signal: "Production Gap" },
    { text: "\"Datacenter expansion needs 24/7 monitoring - can't staff night shifts\"", company: "Cloud Infrastructure", signal: "Operations Challenge" },
    { text: "\"Apparel warehouse facing 80% turnover - need automated picking\"", company: "Fashion Logistics", signal: "Retention Crisis" },
    { text: "\"Hotel housekeeping takes 45 min per room - need to cut to 30\"", company: "Boutique Hotel Group", signal: "Efficiency Target" },
    { text: "\"Kitchen staff shortage forcing us to reduce menu and operating hours\"", company: "Restaurant Chain", signal: "Service Impact" },
    { text: "\"Competitors automated - we're losing market share on delivery speed\"", company: "3PL Provider", signal: "Competitive Pressure" },
    { text: "\"New minimum wage increase makes automation payback under 18 months\"", company: "Distribution Network", signal: "Economic Trigger" },
    { text: "\"Surgical robot ROI proven - expanding program to 3 more hospitals\"", company: "Health Network", signal: "Deployment Success" }
  ];

  useEffect(() => {
    if (!pipelineModalOpen) return;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setPipelineModalOpen(false);
        setPipelineModalInput('');
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [pipelineModalOpen]);

  // Close share menu when clicking outside
  useEffect(() => {
    if (shareMenuLeadId == null) return;
    const onDocClick = (e) => {
      if (!e.target.closest('[data-share-menu]')) setShareMenuLeadId(null);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [shareMenuLeadId]);

  // Rotate quotes every 4 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentQuoteIndex((prev) => (prev + 1) % automationQuotes.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [automationQuotes.length]);

  // Animate signal flow
  useEffect(() => {
    const updateSignalFlow = () => {
      setSignalFlow(prev => {
        const newFlow = {};
        Object.keys(prev).forEach(key => {
          const change = (Math.random() - 0.5) * 0.08;
          const newValue = Math.max(0, Math.min(1, prev[key].value + change));
          const delta = newValue - prev[key].value;
          newFlow[key] = {
            value: newValue,
            delta: delta,
            prev: prev[key].value
          };
        });
        return newFlow;
      });
    };

    const interval = setInterval(updateSignalFlow, 3000);
    return () => clearInterval(interval);
  }, []);

  // CRM strip: populate from spotlight leads (already loaded by /api/leads/homepage)
  // No separate heavy API calls — the homepage batched endpoint provides all we need.
  useEffect(() => {
    if (!hotLeads?.length) return;
    setCrmPreviewLists((prev) => {
      if (prev.active.length) return prev; // already populated, don't overwrite
      const spot = dedupeHomepageLeads(hotLeads);
      return {
        active: extractLeadPreviews(spot),
        hot: extractLeadPreviews(spot.filter((l) => l.priority_tier === 'HOT')),
        warm: extractLeadPreviews(spot.filter((l) => l.priority_tier === 'WARM')),
      };
    });
  }, [hotLeads]);

  // Rotate displayed company names on independent offsets so rows don’t move in lockstep
  useEffect(() => {
    const id = setInterval(() => {
      setCrmNameSpin((s) => ({
        active: s.active + 1,
        hot: s.hot + 2,
        warm: s.warm + 3,
      }));
    }, 3600);
    return () => clearInterval(id);
  }, []);

  // Single batched fetch: summary + hot leads in one request (faster, fewer round trips, better for mobile).
  // Fresh AbortController per request — reusing an aborted signal breaks the 5‑min poll after any timeout.
  useEffect(() => {
    const apiBase = getApiBase();
    let cancelled = false;
    const HOMEPAGE_TIMEOUT_MS = 20000;
    const INITIAL_RETRIES = 3;

    if (homepageRetryTick > 0) {
      homepageFetchCompletedRef.current = false;
    }

    const applyHomepagePayload = (data) => {
      const s = data.summary || {};
      setStatsData({
        activeLeads: s.total ?? 0,
        hotDeals: s.hot ?? 0,
        liveSignals: s.total_signals ?? 0,
        warmPipeline: s.warm ?? 0,
        cold: s.cold ?? 0,
      });
      setLeadsByIndustry(s.by_industry ?? {});
      setTierLegend(data.tierLegend || null);
      setScoringSystem(data.scoringSystem || null);
      setHotLeads(Array.isArray(data.hotLeads) ? data.hotLeads : []);
      setHomepageError(null);
    };

    const fetchHomepageOnce = async (signal) => {
      const res = await fetch(
        `${apiBase}/api/leads/homepage?cb=${Date.now()}`,
        liveFetchInit({ signal }),
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    };

    const fetchHomepage = async (isPoll) => {
      const isFirstFetch = !homepageFetchCompletedRef.current;
      if (isFirstFetch) {
        setLoading(true);
        setHomepageError(null);
      }

      const runSingleAttempt = async () => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), HOMEPAGE_TIMEOUT_MS);
        try {
          const data = await fetchHomepageOnce(controller.signal);
          clearTimeout(timeout);
          return data;
        } catch (e) {
          clearTimeout(timeout);
          throw e;
        }
      };

      try {
        let data;
        if (isPoll) {
          data = await runSingleAttempt();
        } else {
          let lastErr;
          for (let attempt = 0; attempt < INITIAL_RETRIES; attempt++) {
            if (cancelled) return;
            try {
              data = await runSingleAttempt();
              lastErr = null;
              break;
            } catch (err) {
              lastErr = err;
              const retryable =
                err?.name === 'AbortError' ||
                (typeof err?.message === 'string' && /failed to fetch|network|load/i.test(err.message));
              if (attempt < INITIAL_RETRIES - 1 && retryable) {
                await new Promise((r) => setTimeout(r, 800 * (attempt + 1)));
                continue;
              }
              throw err;
            }
          }
        }

        if (cancelled || data === undefined) return;
        applyHomepagePayload(data);
      } catch (err) {
        if (cancelled) return;
        if (err?.name === 'AbortError') {
          if (!isPoll) {
            console.error('Homepage fetch timed out:', err);
            setHomepageError('Request timed out. Check your connection and try again.');
            setHotLeads([]);
            setScoringSystem(null);
          }
          return;
        }
        console.error('Error fetching homepage data:', err);
        if (!isPoll) {
          setHomepageError('Could not load spotlight deals. Tap Retry or try again in a moment.');
          setHotLeads([]);
          setScoringSystem(null);
        }
      } finally {
        if (!cancelled) {
          setStatsLoaded(true);
          homepageFetchCompletedRef.current = true;
          setLoading(false);
        }
      }
    };

    fetchHomepage(false);
    const interval = setInterval(() => {
      fetchHomepage(true);
    }, 300_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [homepageRetryTick]);

  // ── Feed rotation effect ─────────────────────────────────────────────────
  useEffect(() => {
    const pool = dedupeHomepageLeads(hotLeads);
    if (pool.length <= FEED_VISIBLE) return;
    const timer = setInterval(() => {
      // Fade out → advance offset → fade in
      setFeedExiting(true);
      setTimeout(() => {
        setFeedOffset(prev => (prev + 1) % pool.length);
        setFeedExiting(false);
        setFeedEntering(true);
        setTimeout(() => setFeedEntering(false), 400);
      }, 300);
    }, FEED_INTERVAL);
    return () => clearInterval(timer);
    // FEED_VISIBLE / FEED_INTERVAL are module-level constants
  }, [hotLeads]); // eslint-disable-line react-hooks/exhaustive-deps

  // Use summary for counts (no full leads fetch)
  const hotCount = statsData.hotDeals ?? 0;
  const hottestSignal = hotLeads
    .flatMap(lead => (lead.signals || []).map(s => ({ ...s, company: lead.company_name })))
    .sort((a, b) => (b.signal_strength || 0) - (a.signal_strength || 0))[0];

  // Daily spotlight: API may still return same name twice if DB has duplicate companies; collapse here too.
  const topHotDeals = useMemo(() => dedupeHomepageLeads(hotLeads), [hotLeads]);

  const getColorClasses = (color) => {
    const colors = {
      cyan: {
        border: 'border-cyan-500',
        text: 'text-cyan-400',
        bg: 'bg-cyan-950/20',
        gradient: 'bg-gradient-to-r from-cyan-500 to-cyan-400',
        cardBorder: 'border-cyan-800/20',
        cardBg: 'bg-cyan-950/10',
        cardText: 'text-cyan-400',
        quoteText: 'text-cyan-200/90',
        quoteBorder: 'border-cyan-800/30',
        quoteBg: 'bg-cyan-950/20'
      },
      emerald: {
        border: 'border-emerald-500',
        text: 'text-emerald-400',
        bg: 'bg-emerald-950/20',
        gradient: 'bg-gradient-to-r from-emerald-500 to-emerald-400',
        cardBorder: 'border-emerald-800/20',
        cardBg: 'bg-emerald-950/10',
        cardText: 'text-emerald-400',
        quoteText: 'text-emerald-200/90',
        quoteBorder: 'border-emerald-800/30',
        quoteBg: 'bg-emerald-950/20'
      },
      amber: {
        border: 'border-amber-500',
        text: 'text-amber-400',
        bg: 'bg-amber-950/20',
        gradient: 'bg-gradient-to-r from-amber-500 to-orange-400',
        cardBorder: 'border-amber-800/20',
        cardBg: 'bg-amber-950/10',
        cardText: 'text-amber-400',
        quoteText: 'text-amber-200/90',
        quoteBorder: 'border-amber-800/30',
        quoteBg: 'bg-amber-950/20'
      },
      red: {
        border: 'border-red-500',
        text: 'text-red-400',
        bg: 'bg-red-950/20',
        gradient: 'bg-gradient-to-r from-red-500 to-red-400',
        cardBorder: 'border-red-800/20',
        cardBg: 'bg-red-950/10',
        cardText: 'text-red-400',
        quoteText: 'text-red-200/90',
        quoteBorder: 'border-red-800/30',
        quoteBg: 'bg-red-950/20'
      }
    };
    return colors[color] || colors.emerald;
  };

  const signalCategories = [
    {
      id: 'labor',
      name: 'Labor Signals',
      color: 'cyan',
      strength: 'STRONGEST',
      signals: [
        { name: 'Labor Scarcity', description: '"We can\'t find enough workers to cover shifts anymore"', weight: 9.5 },
        { name: 'Labor Cost Pressure', description: '"Wages are up 30% and still can\'t fill positions"', weight: 9.0 },
        { name: 'High Turnover', description: '"Turnover is killing us - constant training cycles"', weight: 8.5 },
        { name: 'Understaffing', description: '"We\'re constantly understaffed, running skeleton crews"', weight: 8.5 },
        { name: 'Overtime Costs', description: '"Overtime spending is out of control"', weight: 8.0 },
      ]
    },
    {
      id: 'productivity',
      name: 'Productivity Signals',
      color: 'emerald',
      strength: 'STRONG',
      signals: [
        { name: 'Throughput Bottleneck', description: '"We need to increase throughput without adding headcount"', weight: 8.5 },
        { name: 'Process Too Slow', description: '"This process is too slow, we\'re losing competitive edge"', weight: 8.0 },
        { name: 'Manual Repetition', description: '"Our team spends too much time on repetitive tasks"', weight: 8.0 },
        { name: 'Error Rates', description: '"Manual errors are causing costly rework"', weight: 7.5 },
        { name: 'Quality Issues', description: '"Inconsistent quality from shift to shift"', weight: 7.0 },
      ]
    },
    {
      id: 'expansion',
      name: 'Expansion Signals',
      color: 'emerald',
      strength: 'STRONG',
      signals: [
        { name: 'Capacity Expansion', description: '"We need to scale operations for new demand"', weight: 8.5 },
        { name: '24/7 Operations', description: '"We need to run overnight shifts but can\'t staff them"', weight: 8.0 },
        { name: 'New Facility Opening', description: 'Announcing new warehouse/facility construction', weight: 8.0 },
        { name: 'Geographic Expansion', description: 'Opening locations in new markets/regions', weight: 7.5 },
        { name: 'Product Line Expansion', description: 'Adding new SKUs/services requiring more capacity', weight: 7.0 },
      ]
    },
    {
      id: 'safety',
      name: 'Safety & Risk Signals',
      color: 'amber',
      strength: 'MODERATE',
      signals: [
        { name: 'Safety Incidents', description: '"We\'ve had injuries doing this repetitive work"', weight: 7.5 },
        { name: 'Ergonomic Issues', description: '"This job has ergonomic risks - heavy lifting, repetition"', weight: 7.0 },
        { name: 'Hazardous Environment', description: 'Extreme temps, confined spaces, toxic materials', weight: 7.0 },
        { name: 'Compliance Pressure', description: 'OSHA citations or regulatory scrutiny', weight: 6.5 },
      ]
    },
    {
      id: 'intent',
      name: 'Active Intent Signals',
      color: 'red',
      strength: 'HIGHEST VALUE',
      signals: [
        { name: 'Pilot Request', description: '"Can we run a pilot program?"', weight: 10.0 },
        { name: 'Demo Request', description: '"Can we see a demonstration?"', weight: 9.5 },
        { name: 'Automation Research', description: 'Posting about evaluating automation vendors', weight: 9.0 },
        { name: 'Automation Hire', description: 'Hiring "automation engineer" or "robotics integration"', weight: 9.0 },
        { name: 'Vendor Comparison', description: 'Asking about "vs competitor" or feature comparison', weight: 8.5 },
        { name: 'Budget Discussion', description: 'Asking about pricing, ROI, or payback period', weight: 8.0 },
      ]
    }
  ];

  const filteredCategories = activeCategory === 'all' 
    ? signalCategories 
    : signalCategories.filter(cat => cat.id === activeCategory);

  const crmPrevActive = previewAt(crmPreviewLists.active, crmNameSpin.active);
  const crmPrevHot = previewAt(crmPreviewLists.hot, crmNameSpin.hot);
  const crmPrevWarm = previewAt(crmPreviewLists.warm, crmNameSpin.warm);

  return (
    <>
      <Head>
        <title>Companies → Ready For Robots | Signal Intelligence &amp; Automation Leads</title>
        <meta name="description" content="Automation sales leads with actionable signals. Buying intent from 150+ sources — labor shortages, CapEx, new facilities. Each lead comes with signals you can act on." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={BASE_URL} />
        <meta property="og:title" content="Companies → Ready For Robots | Signal Intelligence &amp; Automation Leads" />
        <meta property="og:description" content="Automation sales leads with actionable signals. We track buying intent across 150+ sources. Each lead comes with signals you can act on." />
        <meta property="og:image" content={`${BASE_URL}/og-logo.png`} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="Ready for Robots" />
        <meta name="twitter:card" content="summary_large_image" />
        {/* Pythia glyph used for all @pythh X posts — drop delphi-pythia-icon-glyph-dark.jpg into public/images/ */}
        <meta name="twitter:image" content={`${BASE_URL}/images/delphi-pythia-icon-glyph-dark.jpg`} />
        <meta name="twitter:title" content="Companies → Ready For Robots | Signal Intelligence &amp; Automation Leads" />
        <meta name="twitter:description" content="Automation sales leads with actionable signals. Each lead comes with signals you can act on." />
      </Head>

      <div className="rr-theme min-h-screen">
        {/* Navigation — docs/design/homepage_design.html */}
        <div className="rr-navbar w-full">
          <div className="rr-navbar-inner">
          <div className="rr-nav-brand">
            {/* No whitespace inside .rr-brand-logo — avoids stray text nodes / hydration mismatch */}
            <div className="rr-brand-logo">
              <Image src="/logo-r.png" alt="" width={36} height={36} className="object-contain p-0.5" priority />
            </div>
            <Link href="/" className="rr-brand-name hidden sm:inline">Ready For Robots</Link>
          </div>
          <nav className="rr-nav-links">
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/dashboard" title="Lead pipeline and sales workspace">
              Pipeline
            </Link>
            <Link href="/crm/" title="CRM workspaces and buyer accounts">
              CRM
            </Link>
            <Link href="/market-insights">Market Insights</Link>
            <Link href="/about">Signals</Link>
            <a href="#leads">Browse Leads</a>
            <Link href="/newsletter">📰 Newsletter</Link>
            <Link href="/roi-calculator">ROI Calculator</Link>
          </nav>
          <div className="rr-nav-right">
            <div className="hidden md:flex items-center gap-3">
              <LoginDropdown className="[&_button]:rr-btn-signin" />
              <Link href="/login" className="rr-btn-signup">
                Sign Up
              </Link>
            </div>
                <div className="md:hidden relative">
                  <button
                    type="button"
                    onClick={() => {
                      const menu = document.getElementById('mobile-menu');
                      menu?.classList.toggle('hidden');
                    }}
                    className="text-neutral-400 hover:text-white px-3 py-2 text-xl"
                    aria-expanded="false"
                    aria-controls="mobile-menu"
                  >
                    ☰
                  </button>
                  <div id="mobile-menu" className="hidden absolute right-0 top-full mt-2 w-56 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
                    <Link href="/dashboard" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800">
                      📊 Dashboard
                    </Link>
                    <Link href="/dashboard" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800">
                      🧭 Pipeline
                    </Link>
                    <Link href="/crm/" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800">
                      🗂️ CRM
                    </Link>
                    <Link href="/market-insights" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800">
                      📈 Market Insights
                    </Link>
                    <Link href="/about" className="block px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 border-b border-neutral-800">
                      ⚡ Signal Intelligence
                    </Link>
                    <a href="#leads" className="block px-4 py-3 text-sm text-cyan-400 hover:bg-neutral-900 border-b border-neutral-800">
                      🔥 Browse Leads
                    </a>
                    <Link href="/newsletter" className="block px-4 py-3 text-sm text-cyan-300 hover:bg-neutral-900 border-b border-neutral-800">
                      📰 Newsletter
                    </Link>
                    <Link href="/roi-calculator" className="block px-4 py-3 text-sm text-yellow-400 hover:bg-neutral-900 border-b border-neutral-800">
                      💰 ROI Calculator
                    </Link>
                    <a href="#signals" className="block px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 border-b border-neutral-800">
                      💡 How It Works
                    </a>
                    <Link href="/login" className="block px-4 py-3 text-sm text-neutral-400 hover:bg-neutral-900 border-b border-neutral-800">
                      🔐 Sign in (Google, GitHub, Email)
                    </Link>
                    <Link href="/login" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900">
                      ✨ Sign Up
                    </Link>
                  </div>
                </div>
          </div>
          </div>
        </div>

        {/* Hero — headline left, compact quote + inline stats right (md+) */}
        <div className="rr-hero">
          <div className="rr-hero-inner">
            <div className="rr-hero-headline-row">
              <div className="rr-hero-headline-block">
                <p className="rr-hero-signal-source-tag">
                  14 signal types · 150+ sources
                </p>
                <h1 className="rr-hero-title-main rr-hero-title-bridge">
                  <span className="rr-hero-title-part">Companies</span>
                  <span className="rr-hero-title-arrow" aria-hidden="true">
                    →
                  </span>
                  <span className="rr-hero-title-part">
                    Ready <span className="rr-hero-title-em">For Robots</span>
                  </span>
                </h1>
                <p className="rr-hero-subhead">
                  Robot Automation Projects with Signal Intelligence.
                </p>
                <p className="rr-hero-lead">
                  We track buying intent across 150+ sources — labor shortages, CapEx, new facilities, executive hires. Each lead comes with signals you can act on.
                </p>
                <p className="rr-hero-lead-accent">
                  Explore the pipeline and CRM to turn signals into qualified conversations.
                </p>
                <div className="rr-hero-cta">
                  <button
                    type="button"
                    className="rr-btn-hero-primary rr-btn-hero-btn-wide"
                    onClick={() => {
                      setPipelineModalInput('');
                      setPipelineModalOpen(true);
                    }}
                  >
                    Preview pipeline
                  </button>
                  <Link href="/search" className="rr-btn-hero-secondary rr-btn-hero-secondary-emerald rr-btn-hero-btn-wide inline-block text-center">
                    Search Leads
                  </Link>
                </div>
                <p className="rr-hero-cta-hint">
                  <strong>Preview pipeline</strong>: your company → matches.{' '}
                  <strong>Search Leads</strong>: full database.
                </p>
              </div>
              {/* ── Hero right panel: Supabase-inspired live pipeline card */}
              <aside
                className="rr-hero-ticker-panel rr-hero-ticker-panel--live rr-hero-ticker-panel--supabase rr-hero-ticker-panel--crm-names flex flex-col"
                aria-label="Live signal feed"
              >
                <span className="rr-hero-ticker-accent" aria-hidden="true" />
                <div className="rr-hero-ticker-header">
                  <div className="rr-hero-ticker-header-left">
                    <span className="rr-hero-ticker-sb-mark" aria-hidden="true" />
                    <span className="rr-hero-ticker-header-title">Live pipeline</span>
                  </div>
                  <span className="rr-hero-ticker-live-pill">
                    <span className="rr-hero-ticker-live-dot" aria-hidden="true" />
                    Live
                  </span>
                </div>
                <div className="rr-hero-ticker-metrics shrink-0 mb-3">
                  <div className="rr-hero-ticker-metric">
                    <span className="rr-hero-ticker-metric-label">Active</span>
                    <span className="rr-hero-ticker-metric-value">{formatHeroCount(statsData.activeLeads, statsLoaded)}</span>
                  </div>
                  <div className="rr-hero-ticker-metric rr-hero-ticker-metric--hot">
                    <span className="rr-hero-ticker-metric-label">Hot</span>
                    <span className="rr-hero-ticker-metric-value">{formatHeroCount(statsData.hotDeals, statsLoaded)}</span>
                  </div>
                  <div className="rr-hero-ticker-metric rr-hero-ticker-metric--signals">
                    <span className="rr-hero-ticker-metric-label">Signals</span>
                    <span className="rr-hero-ticker-metric-value">{formatHeroCount(statsData.liveSignals, statsLoaded)}</span>
                  </div>
                </div>

                <div className="rr-hero-ticker-divider shrink-0" />

                {/* Rotating signal feed */}
                <div
                  className="flex-1 overflow-hidden"
                  style={{
                    transition: 'opacity 300ms ease',
                    opacity: feedExiting ? 0 : 1,
                  }}
                >
                  {loading ? (
                    <div className="py-8 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e] animate-pulse" />
                      <span className="text-xs text-neutral-500 font-mono">Loading rows…</span>
                    </div>
                  ) : topHotDeals.length === 0 ? (
                    <p className="text-xs text-neutral-600 py-6">No signals yet — check back soon</p>
                  ) : (
                    <div>
                      {Array.from({ length: Math.min(FEED_VISIBLE, topHotDeals.length) }, (_, i) => {
                        const lead      = topHotDeals[(feedOffset + i) % topHotDeals.length];
                        const tier      = lead.priority_tier || 'COLD';
                        const isHot     = tier === 'HOT';
                        const isWarm    = tier === 'WARM';
                        const topSig    = (lead.signals || [])[0];
                        const sigLabel  = (topSig?.signal_label || (topSig?.signal_type || '').replace(/_/g, ' ')).toLowerCase();
                        const tierLabel = isHot ? 'HOT' : isWarm ? 'WARM' : 'EMRG';
                        const tierColor = isHot ? '#34d399' : isWarm ? '#2dd4bf' : '#94a3b8';
                        const extUrl = companyExternalHref(lead);
                        return (
                          <div
                            key={`${feedOffset}-${i}`}
                            role="link"
                            tabIndex={0}
                            onClick={() => router.push('/dashboard')}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                router.push('/dashboard');
                              }
                            }}
                            className="rr-hero-ticker-row group flex items-start gap-3 py-3 px-1 -mx-1 rounded-md border-b border-white/[0.06] transition-colors last:border-b-0 cursor-pointer"
                          >
                            <span
                              className="shrink-0 mt-1 w-0.5 self-stretch rounded-full"
                              style={{ background: isHot ? '#34d399' : isWarm ? '#2dd4bf' : '#475569' }}
                            />
                            <div className="min-w-0 flex-1">
                              <div className="flex items-baseline gap-2">
                                <span
                                  className="shrink-0 text-[9px] font-bold tracking-[0.14em] uppercase"
                                  style={{ color: tierColor, minWidth: '2.6rem' }}
                                >
                                  {tierLabel}
                                </span>
                                <a
                                  href={extUrl || '#'}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  className={`${COMPANY_NAME_LINK_CLASS} text-sm font-semibold truncate`}
                                >
                                  {lead.company_name}
                                </a>
                              </div>
                              <p className="text-[11px] text-neutral-500 truncate mt-0.5 leading-snug pl-[2.6rem]">
                                {sigLabel && <span className="text-neutral-400">{sigLabel}</span>}
                                {sigLabel && lead.industry && <span className="mx-1 text-neutral-700">·</span>}
                                {lead.industry && <span>{lead.industry}</span>}
                              </p>
                            </div>
                            <span className="rr-hero-ticker-row-arrow shrink-0 text-neutral-600 group-hover:text-[#3ecf8e] text-xs mt-1 transition-colors">→</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Footer: live pulse + CTA + warm count */}
                <div className="rr-hero-ticker-footer mt-3 pt-3 shrink-0 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e] animate-pulse shrink-0" />
                    <Link
                      href="/dashboard"
                      className="rr-hero-ticker-footer-link text-[11px] font-semibold font-mono truncate"
                    >
                      View all {formatHeroCount(statsData.hotDeals, statsLoaded)} HOT →
                    </Link>
                  </div>
                  <span className="text-[10px] text-neutral-500 tabular-nums font-mono shrink-0">
                    {formatHeroCount(statsData.warmPipeline, statsLoaded)} warm
                  </span>
                </div>
              </aside>
            </div>
          </div>
        </div>

        {/* Daily Spotlight Deals — now above the fold */}
        <div id="leads" className="max-w-7xl mx-auto px-6 pt-6 pb-10 md:pb-12 space-y-8 scroll-mt-24">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-1 h-4 rounded-full bg-orange-500" />
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold tracking-[0.12em] uppercase text-neutral-400">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                HOT leads · Act this week
              </span>
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight mb-2">
              Today&apos;s automation pipeline
            </h2>
            <p className="text-sm text-neutral-500 max-w-xl mb-5">
              Ranked by newest signal activity. Three HOT, two Warm — each with buying signals you can act on.
            </p>
            {tierLegend && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
                {['HOT', 'WARM', 'COLD'].map((key) => {
                  const block = tierLegend[key];
                  if (!block) return null;
                  const styles =
                    key === 'HOT'  ? { border: 'border-orange-500/30', bg: 'bg-orange-500/8',  dot: 'bg-orange-500',  label: 'text-orange-400' } :
                    key === 'WARM' ? { border: 'border-amber-500/30',  bg: 'bg-amber-500/8',   dot: 'bg-amber-400',   label: 'text-amber-400'  } :
                                    { border: 'border-cyan-500/30',    bg: 'bg-cyan-500/8',    dot: 'bg-cyan-500',    label: 'text-cyan-400'   };
                  return (
                    <div key={key} className={`rounded-xl border ${styles.border} ${styles.bg} px-4 py-3`}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <div className={`w-2 h-2 rounded-full shrink-0 ${styles.dot}`} />
                        <span className={`text-xs font-bold uppercase tracking-wider ${styles.label}`}>{block.label}</span>
                        <span className="text-neutral-600 text-xs font-normal normal-case">— {block.tagline}</span>
                      </div>
                      <p className="text-xs text-neutral-500 leading-snug">{block.description}</p>
                    </div>
                  );
                })}
              </div>
            )}
            <HotDealsScoringExplainer data={scoringSystem} />
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-neutral-400 mt-4">Loading spotlight deals...</p>
            </div>
          ) : homepageError && topHotDeals.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <p className="text-neutral-400 max-w-md mx-auto">{homepageError}</p>
              <button
                type="button"
                onClick={() => setHomepageRetryTick((t) => t + 1)}
                className="inline-flex items-center justify-center rounded-lg border border-emerald-600/50 bg-emerald-950/30 px-4 py-2 text-sm font-medium text-emerald-300 hover:bg-emerald-900/40 hover:border-emerald-500/60 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : topHotDeals.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-neutral-400">No spotlight deals right now. New signals land throughout the day — check back soon!</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {topHotDeals.map((lead, idx) => {
                const score = typeof lead.score === 'object' ? (lead.score.overall_score || 0) : (lead.score || 0);
                // API already deduplicates by type and caps at 5 — use as-is
                const cardSignals = lead.signals || [];
                const isExpanded = expandedDealId === lead.id;
                const totalSignalCount = lead.signal_count || cardSignals.length;
                
                return (
                  <div 
                    key={lead.id}
                    onClick={() => setExpandedDealId(isExpanded ? null : lead.id)}
                    className={`rr-deal-card group space-y-3 transition-all cursor-pointer ${
                      isExpanded ? 'rr-deal-card-expanded' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-1.5">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <h4 className="text-base font-semibold text-neutral-100 group-hover:text-white transition-colors">
                            <a
                              href={companyExternalHref(lead) || '#'}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className={COMPANY_NAME_LINK_CLASS}
                            >
                              {lead.company_name}
                            </a>
                          </h4>
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded-full border ${
                              lead.priority_tier === 'WARM'
                                ? 'bg-amber-500/10 text-amber-400 border-amber-500/25'
                                : lead.priority_tier === 'COLD'
                                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/25'
                                  : 'bg-orange-500/10 text-orange-400 border-orange-500/25'
                            }`}
                          >
                            {lead.priority_tier === 'WARM'
                              ? '⚡ Warm'
                              : lead.priority_tier === 'COLD'
                                ? '✦ Emerging'
                                : '🔥 Hot'}
                          </span>
                          <span className="text-neutral-600 text-xs ml-auto sm:ml-0">{isExpanded ? '▲' : '▼'}</span>
                        </div>
                        <div className="text-xs text-neutral-500 font-medium">
                          {lead.industry} · {lead.location_city && lead.location_state ? `${lead.location_city}, ${lead.location_state}` : 'Location N/A'}
                        </div>
                        {lead.gtm && (
                          <div className="mt-2 rounded-md border border-emerald-800/50 bg-emerald-950/20 px-3 py-2">
                            <div className="text-[10px] uppercase tracking-wide text-emerald-600/90 mb-0.5">When they&apos;re ready · why now</div>
                            <div className="text-sm font-medium text-emerald-200/95">{lead.gtm.readiness_label}</div>
                            {Array.isArray(lead.gtm.why_now) && lead.gtm.why_now.length > 0 && (
                              <ul className="mt-1.5 space-y-0.5 text-xs text-neutral-400 list-disc list-inside">
                                {lead.gtm.why_now.slice(0, 3).map((line, wi) => (
                                  <li key={wi}>{line}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                        {lead.share_summary && (
                          <p className="text-xs text-neutral-400 leading-relaxed pt-1 border-l-2 border-orange-500/40 pl-3">
                            {lead.share_summary}
                          </p>
                        )}
                        {cardSignals.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {cardSignals.map((signal, sidx) => (
                              <span key={sidx} className="text-[11px] text-emerald-400 bg-emerald-500/8 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                                {signal.signal_label || signal.signal_type}
                              </span>
                            ))}
                          </div>
                        )}
                        {!isExpanded && (
                          <AutomationSpecBlock profile={lead.automation_profile} compact theme="home" />
                        )}
                      </div>
                      <div className="text-right space-y-2 flex flex-col items-end shrink-0">
                        <div className="flex flex-col items-center bg-neutral-900/60 border border-neutral-800 rounded-lg px-3 py-2 min-w-[52px]">
                          <div className="text-xl font-bold tabular-nums text-orange-400 leading-none">
                            {score.toFixed(0)}
                          </div>
                          <div className="text-[9px] text-neutral-600 font-semibold uppercase tracking-wider mt-0.5">score</div>
                        </div>
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <div className="relative" data-share-menu>
                            <button
                              type="button"
                              onClick={(e) => { e.stopPropagation(); setShareMenuLeadId(shareMenuLeadId === lead.id ? null : lead.id); }}
                              className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white text-xs font-medium border border-neutral-700"
                              aria-label="Share this lead"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                              Share
                            </button>
                            {shareMenuLeadId === lead.id && (() => {
                              const shareUrl = `${BASE_URL}/#leads`;
                              // Headline for X: "Company — Signal Type | HOT Lead" — fresh and specific
                              const topSignalLabel = (lead.signals && lead.signals[0]?.signal_label) || (lead.signals && lead.signals[0]?.signal_type?.replace(/_/g, ' ')) || 'Automation Signal';
                              const xHeadline = `${lead.company_name} — ${topSignalLabel} | ${lead.priority_tier === 'HOT' ? '🔥 Hot' : lead.priority_tier === 'WARM' ? '⚡ Warm' : '✦ Emerging'} Lead`;
                              const summaryBody = lead.share_summary || lead.share_blurb || `${lead.company_name} (${lead.industry || 'Automation'}) — automation signals · Ready For Robots`;
                              // X post: headline first, then first sentence of summary (~250 char budget)
                              const maxBody = 240 - xHeadline.length - 2;
                              const firstSentence = summaryBody.split('. ')[0] + '.';
                              const tweetBody = firstSentence.length <= maxBody ? firstSentence : firstSentence.slice(0, maxBody - 1) + '…';
                              const tweetText = `${xHeadline}\n\n${tweetBody}`;
                              const shareText = summaryBody; // LinkedIn/copy gets full summary
                              const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
                              const liTitle = encodeURIComponent(`${lead.company_name} — ${lead.priority_tier || 'Lead'} | Ready For Robots`);
                              const liSummary = encodeURIComponent(shareText.slice(0, 700));
                              const linkedInUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${liTitle}&summary=${liSummary}&source=readyforrobots.com`;
                              const copyShare = () => {
                                navigator.clipboard?.writeText(`${shareText}\n\n${shareUrl}`);
                                setShareMenuLeadId(null);
                              };
                              return (
                                <div className="absolute right-0 top-full mt-1 z-20 py-2 px-2 rounded-lg bg-neutral-800 border border-neutral-600 shadow-xl min-w-[160px]">
                                  <div className="text-[10px] text-neutral-500 uppercase tracking-wider mb-2 px-2">Share on social</div>
                                  <a href={twitterUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-neutral-700 text-sm text-neutral-200">
                                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                                    X (Twitter)
                                  </a>
                                  <a href={linkedInUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-neutral-700 text-sm text-neutral-200">
                                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                                    LinkedIn
                                  </a>
                                  <button type="button" onClick={copyShare} className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-neutral-700 text-sm text-neutral-200 text-left">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                                    Copy link & text
                                  </button>
                                </div>
                              );
                            })()}
                          </div>
                          <Link
                            href={`/dashboard?analyze=${lead.id}`}
                            className="inline-block text-xs text-orange-400 hover:text-orange-300 font-semibold underline"
                          >
                            Full analysis →
                          </Link>
                        </div>
                      </div>
                    </div>

                    {isExpanded && (
                      <div 
                        className="pt-4 mt-3 border-t border-neutral-800 space-y-4"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {/* Score sub-breakdown */}
                        {lead.score && typeof lead.score === 'object' && (
                          <div className="grid grid-cols-4 gap-2">
                            {[
                              { label: 'Automation', val: lead.score.automation_score },
                              { label: 'Labor Pain', val: lead.score.labor_pain_score },
                              { label: 'Expansion', val: lead.score.expansion_score },
                              { label: 'Market Fit', val: lead.score.market_fit_score },
                            ].map(({ label, val }) => (
                              <div key={label} className="bg-[#101010] border border-neutral-800/50 rounded p-2 text-center">
                                <div className="text-base font-bold text-neutral-200">{(val || 0).toFixed(0)}</div>
                                <div className="text-[10px] text-neutral-500 mt-0.5">{label}</div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Why it ranks — priority reasons */}
                        {lead.priority_reasons && lead.priority_reasons.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">Why it ranks</div>
                            <ul className="space-y-0.5">
                              {lead.priority_reasons.slice(0, 3).map((r, i) => (
                                <li key={i} className="flex items-start gap-1.5 text-xs text-neutral-300">
                                  <span className="text-orange-400 mt-0.5">›</span>
                                  <span>{r}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <AutomationSpecBlock profile={lead.automation_profile} theme="home" />

                        {/* Signal intelligence cards — top 5 unique types */}
                        {cardSignals.length > 0 && (
                          <div className="space-y-2">
                            <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">
                              Signal intelligence
                              <span className="ml-2 text-neutral-600 normal-case font-normal">({totalSignalCount} total signals on file)</span>
                            </div>
                            <div className="space-y-2">
                              {cardSignals.map((signal, sidx) => {
                                const strengthPct = Math.round((signal.strength || 0) * 100);
                                const excerpt = (signal.raw_text || '').replace(/\n/g, ' ').trim();
                                const shortExcerpt = excerpt.length > 200 ? excerpt.slice(0, 197) + '…' : excerpt;
                                return (
                                  <div key={`${lead.id}-intel-${sidx}`} className="bg-neutral-900/50 border border-neutral-800/60 rounded-lg p-3 space-y-1.5">
                                    <div className="flex items-center justify-between gap-2">
                                      <span className="text-xs font-semibold text-emerald-400">
                                        {signal.signal_label || signal.signal_type}
                                      </span>
                                      <div className="flex items-center gap-2">
                                        <div className="w-16 h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                                          <div
                                            className="h-full bg-emerald-500 rounded-full"
                                            style={{ width: `${strengthPct}%` }}
                                          />
                                        </div>
                                        <span className="text-[10px] text-neutral-500">{strengthPct}%</span>
                                      </div>
                                    </div>
                                    {shortExcerpt && (
                                      <p className="text-xs text-neutral-400 leading-relaxed">{shortExcerpt}</p>
                                    )}
                                    {signal.source_url && (
                                      <a
                                        href={signal.source_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-block text-[10px] text-orange-500/70 hover:text-orange-400 underline truncate max-w-full"
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        Source →
                                      </a>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Share + CTA row — share_summary is the social post header */}
                        <div className="space-y-2 pt-1">
                          {lead.share_summary && (
                            <div className="rounded bg-neutral-900/60 border border-orange-900/40 p-3 space-y-2">
                              <div className="text-[10px] font-semibold text-orange-400/70 uppercase tracking-wider">Post this to social</div>
                              <p className="text-xs text-neutral-400 leading-relaxed line-clamp-3">{lead.share_summary}</p>
                            </div>
                          )}
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div className="flex flex-wrap items-center gap-2">
                              {(() => {
                                const shareUrl = `${BASE_URL}/#leads`;
                                const topSignalLabel = (lead.signals && lead.signals[0]?.signal_label) || (lead.signals && lead.signals[0]?.signal_type?.replace(/_/g, ' ')) || 'Automation Signal';
                                const xHeadline = `${lead.company_name} — ${topSignalLabel} | ${lead.priority_tier === 'HOT' ? '🔥 Hot' : lead.priority_tier === 'WARM' ? '⚡ Warm' : '✦ Emerging'} Lead`;
                                const fullSummary = lead.share_summary || lead.share_blurb || `${lead.company_name} (${lead.industry || 'Automation'}) — automation signals · Ready For Robots`;
                                const maxBody = 240 - xHeadline.length - 2;
                                const firstSentence = fullSummary.split('. ')[0] + '.';
                                const tweetBody = firstSentence.length <= maxBody ? firstSentence : firstSentence.slice(0, maxBody - 1) + '…';
                                const tweetText = `${xHeadline}\n\n${tweetBody}`;
                                const liTitle2 = encodeURIComponent(`${lead.company_name} — ${lead.priority_tier || 'Lead'} | Ready For Robots`);
                                const liSummary2 = encodeURIComponent(fullSummary.slice(0, 700));
                                const linkedInUrl2 = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${liTitle2}&summary=${liSummary2}&source=readyforrobots.com`;
                                return (
                                  <>
                                    <a href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-black text-neutral-400 hover:text-white text-xs">
                                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                                      Share on X
                                    </a>
                                    <a href={linkedInUrl2} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-[#0a66c2] text-neutral-400 hover:text-white text-xs">
                                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                                      LinkedIn
                                    </a>
                                    <button
                                      type="button"
                                      onClick={() => navigator.clipboard?.writeText(`${tweetText}\n\n${shareUrl}`)}
                                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-emerald-600 text-neutral-400 hover:text-white text-xs"
                                    >
                                      Copy post
                                    </button>
                                  </>
                                );
                              })()}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Markets We Track — industry vertical nav */}
        <div className="max-w-7xl mx-auto px-6 pt-10 pb-2">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-1 h-4 rounded-full bg-emerald-500" />
            <span className="text-[11px] font-bold tracking-[0.12em] uppercase text-neutral-400">Coverage</span>
          </div>
          <div className="flex items-end justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Markets we track</h2>
              <p className="text-sm text-neutral-500 mt-1">Every vertical below has live signals — click to filter.</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {[
              { label: 'Logistics & Warehousing',            fit: 'Warehouse AMR Fleet',          q: 'Logistics' },
              { label: 'Hospitality & Hotels',               fit: 'Service & Delivery Robots',    q: 'Hospitality' },
              { label: 'Healthcare & Senior Living',         fit: 'Clinical Logistics Robots',    q: 'Healthcare' },
              { label: 'Food Service & Restaurants',         fit: 'BOH Kitchen Automation',       q: 'Food Service' },
              { label: 'Food Processing & Manufacturing',    fit: 'EOL Line Automation',          q: 'Food Processing & Manufacturing', badge: 'NEW' },
              { label: 'CPG & Consumer Goods',               fit: 'Palletizing & Case Packing',   q: 'CPG & Consumer Goods', badge: 'NEW' },
              { label: 'Contract Manufacturing',             fit: 'Flexible EOL Robotics',        q: 'Contract Manufacturing', badge: 'NEW' },
              { label: 'Retail & Grocery',                   fit: 'Picking & Restocking',         q: 'Retail' },
              { label: 'Airports & Transportation',          fit: 'Ground Ops Robots',            q: 'Airports & Transportation' },
              { label: 'Casinos & Gaming',                   fit: 'Floor & F&B Delivery',         q: 'Casinos & Gaming' },
              { label: 'Real Estate & Facilities',           fit: 'Cleaning & Concierge',         q: 'Real Estate & Facilities' },
              { label: 'Cruise Lines',                       fit: 'Onboard Delivery',             q: 'Cruise Lines' },
            ].map((m) => {
              const qFirst = m.q.split(' ')[0].toLowerCase();
              const matchingLead = hotLeads.find(lead =>
                (lead.industry || '').toLowerCase().includes(qFirst)
              );
              const topSig = matchingLead?.signals?.[0];
              const sigLabel = topSig?.signal_label || topSig?.signal_type?.replace(/_/g, ' ');
              return (
                <Link
                  key={m.q}
                  href={`/search?industry=${encodeURIComponent(m.q)}`}
                  className="group relative flex flex-col justify-between border border-neutral-800 hover:border-emerald-500/50 rounded-xl p-4 bg-neutral-900 hover:bg-[#141d2b] transition-all duration-150 overflow-hidden"
                >
                  {/* hover glow */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none bg-gradient-to-br from-emerald-500/5 to-transparent" />
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-sm font-bold text-emerald-400 group-hover:text-emerald-300 leading-snug transition-colors">{m.label}</p>
                    {m.badge && (
                      <span className="shrink-0 text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase tracking-widest">{m.badge}</span>
                    )}
                  </div>
                  <p className="text-[11px] text-neutral-500 leading-tight">{m.fit}</p>
                  {sigLabel && (
                    <div className="mt-2.5 inline-flex items-center gap-1.5 self-start text-[10px] text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded-full font-medium truncate max-w-full">
                      <span className="w-1 h-1 rounded-full bg-orange-400 shrink-0" />
                      {sigLabel}
                    </div>
                  )}
                  <div className="flex items-end justify-between mt-4 pt-3 border-t border-neutral-800">
                    {m.q && typeof leadsByIndustry[m.q] === 'number' && leadsByIndustry[m.q] > 0 ? (
                      <div>
                        <div className="text-xl font-bold tabular-nums text-emerald-400 leading-none">{leadsByIndustry[m.q]}</div>
                        <div className="text-[10px] text-neutral-600 mt-0.5 font-medium uppercase tracking-wide">leads</div>
                      </div>
                    ) : (
                      <span className="text-sm text-neutral-700 font-mono">—</span>
                    )}
                    <span className="text-neutral-600 group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all text-base">→</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="rr-section !pt-2 !pb-6">
          <Link href="#signals" className="rr-why-signals group block rounded-[var(--rr-radius-lg)]">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-lg shrink-0">💡</span>
                <div>
                  <div className="font-semibold text-[var(--rr-green)]">Why Signals Matter</div>
                  <div className="text-sm text-[var(--rr-muted2)] hidden sm:block">Learn how we identify buying intent</div>
                </div>
              </div>
              <span className="text-[var(--rr-green)] group-hover:translate-x-1 transition-transform shrink-0">→</span>
            </div>
          </Link>
        </div>

        {/* CTA — CRM / pipeline builder — after spotlight so users see proof before the ask */}
        <div id="cta" className="rr-section !pt-2">
          <div className="rr-pipeline-section rr-pipeline-home-cta border-emerald-900/30 bg-gradient-to-br from-emerald-950/25 to-[var(--rr-surface)]">
            <div className="rr-pipeline-eyebrow">● Free CRM builder</div>
            <div className="rr-pipeline-card-title-row">
              <h2 className="rr-pipeline-card-title text-2xl sm:text-[1.75rem] md:text-3xl font-extrabold tracking-tight text-[var(--rr-text)] !mb-0">
                Start Building your Customer CRM
              </h2>
              {!loading && hotLeads.length > 0 && (
                <div className="rr-home-spotlight-inline" aria-label="Spotlight companies">
                  <span className="rr-ticker-inline-label">
                    <span className="inline-block h-1 w-1 rounded-full bg-emerald-500" aria-hidden />
                    Spotlight
                  </span>
                  <div className="rr-home-spotlight-chips">
                    {dedupeHomepageLeads(hotLeads).slice(0, 6).map((lead) => (
                      <a
                        key={lead.id}
                        href={companyExternalHref(lead) || '#leads'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`rr-home-spotlight-chip ${COMPANY_NAME_LINK_CLASS}`}
                      >
                        {lead.company_name}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="rr-pipeline-card-lead mt-2 mb-4 space-y-2.5">
              <p>
                Automation projects are difficult to discover and plan for without great data. We deliver great data that is live, not stale.
              </p>
              <p>
                Then we help you shape your timing and strategy for each one so opportunities turn into PoCs (Proof of Concept) and projects.
              </p>
            </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const v = e.target.robotUrl?.value?.trim() ?? '';
                  setPipelineModalInput(v);
                  setPipelineModalOpen(true);
                }}
                className="space-y-2"
              >
                <input
                  type="text"
                  name="robotUrl"
                  placeholder="Enter your robot company website (e.g., amplibotics.ai)"
                  className="rr-pipeline-input !mb-2 !py-3"
                />
                <button type="submit" className="rr-btn-build rr-btn-build-compact">
                  Build CRM pipeline →
                </button>
              </form>

              <div className="rr-pipeline-checks">
                <span className="rr-pipeline-check">No signup required</span>
                <span className="rr-pipeline-check">Instant results</span>
                <span className="rr-pipeline-check">Free trial</span>
              </div>
          </div>
        </div>

        {/* What Are Buying Signals? */}
        <div id="signals" className="max-w-7xl mx-auto px-6 py-10 md:py-12 space-y-10">
          <div className="text-center space-y-4">
            <div className="text-xs text-cyan-400 font-semibold uppercase tracking-widest">SIGNAL INTELLIGENCE</div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">What Are Buying Signals?</h2>
            <p className="text-lg text-neutral-300 max-w-2xl mx-auto">
              Real-world indicators that a company needs automation — before they post an RFP
            </p>
          </div>

          {/* Signal Categories */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="border border-red-800/30 bg-red-950/10 rounded-lg p-5 space-y-3">
              <div className="text-red-400 font-semibold text-lg">🔥 Labor Shortage Signals</div>
              <div className="text-sm text-neutral-300 space-y-2">
                <p>"We can't find enough workers to cover shifts"</p>
                <p>"Turnover is killing us — constant training"</p>
                <p>"Wages up 30%, still can't fill positions"</p>
              </div>
              <div className="text-xs text-red-400/80 italic">Strongest automation trigger (35% weight)</div>
            </div>

            <div className="border border-emerald-800/30 bg-emerald-950/10 rounded-lg p-5 space-y-3">
              <div className="text-emerald-400 font-semibold text-lg">📈 Expansion Signals</div>
              <div className="text-sm text-neutral-300 space-y-2">
                <p>"Opening new facility next quarter"</p>
                <p>"Need 24/7 operations but can't staff it"</p>
                <p>"Scaling to meet new demand"</p>
              </div>
              <div className="text-xs text-emerald-400/80 italic">Growth-driven automation (25% weight)</div>
            </div>

            <div className="border border-amber-800/30 bg-amber-950/10 rounded-lg p-5 space-y-3">
              <div className="text-amber-400 font-semibold text-lg">⚠️ Safety Signals</div>
              <div className="text-sm text-neutral-300 space-y-2">
                <p>"OSHA citation for repetitive stress"</p>
                <p>"Multiple injuries in manual operations"</p>
                <p>"Heavy lifting causing worker comp claims"</p>
              </div>
              <div className="text-xs text-amber-400/80 italic">Risk reduction driver (20% weight)</div>
            </div>
          </div>

          <div className="border border-neutral-800 rounded-lg p-8 space-y-6 mt-8">
            <div className="text-center space-y-2">
              <div className="text-lg font-semibold text-white">How We Score Leads</div>
              <p className="text-neutral-400">
                Every company gets a score (0-100) based on 4 factors:
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">35%</div>
                <div className="text-xs text-neutral-400 mt-1">Labor Pain</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">30%</div>
                <div className="text-xs text-neutral-400 mt-1">Expansion</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">25%</div>
                <div className="text-xs text-neutral-400 mt-1">Automation Fit</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">10%</div>
                <div className="text-xs text-neutral-400 mt-1">Timing</div>
              </div>
            </div>
          </div>
        </div>

        {/* Success Stories */}
        <div className="max-w-7xl mx-auto px-6 py-10 md:py-12 space-y-10">
          <div className="text-center space-y-4">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-widest">SUCCESS STORIES</div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">Real Signals → Real Deals</h2>
            <p className="text-lg text-neutral-300 max-w-2xl mx-auto">
              How robotics companies are using signals to close deals before RFPs
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="border border-neutral-800 rounded-lg p-6 space-y-3">
              <div className="text-emerald-400 font-semibold">Regional Hotel Chain → AMR Deployment</div>
              <div className="text-sm text-neutral-300">
                <p className="mb-2"><span className="text-neutral-500">Signal detected:</span> "Can't staff overnight shifts" + "40% housekeeping vacancy" in earnings call</p>
                <p className="mb-2"><span className="text-neutral-500">Action:</span> Reached out 4 months before RFP with overnight automation case study</p>
                <p><span className="text-emerald-400">Result:</span> Shaped requirements, won pilot without competition → 15-robot deployment</p>
              </div>
            </div>

            <div className="border border-neutral-800 rounded-lg p-6 space-y-3">
              <div className="text-emerald-400 font-semibold">3PL Warehouse → Palletizing System</div>
              <div className="text-sm text-neutral-300">
                <p className="mb-2"><span className="text-neutral-500">Signal detected:</span> "Opening 2 new DCs" + posting for "automation engineer"</p>
                <p className="mb-2"><span className="text-neutral-500">Action:</span> Contacted during facility design phase with layout recommendations</p>
                <p><span className="text-emerald-400">Result:</span> Designed automation into new buildings → $2.4M contract</p>
              </div>
            </div>
          </div>
        </div>

        {/* Clear Next Steps */}
        <div className="max-w-7xl mx-auto px-6 py-10 md:py-12 space-y-10">
          <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-6 space-y-6">
            <div className="space-y-3">
              <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">GET STARTED</div>
              <h2 className="text-3xl font-bold text-white">Your Action Plan</h2>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="text-emerald-400 font-bold text-xl">1. Try It Free</div>
                <p className="text-sm text-neutral-300">
                  Enter your robot company URL above to see your top 5 prospects instantly — no signup required
                </p>
              </div>

              <div className="space-y-2">
                <div className="text-emerald-400 font-bold text-xl">2. Browse Database</div>
                <p className="text-sm text-neutral-300">
                  View all {hotCount} HOT leads organized by industry — see signals, scores, and contact insights
                </p>
                <Link href="/dashboard" className="text-xs text-cyan-400 hover:text-cyan-300 underline inline-block mt-1">
                  View Dashboard →
                </Link>
              </div>

              <div className="space-y-2">
                <div className="text-emerald-400 font-bold text-xl">3. Get Daily Alerts</div>
                <p className="text-sm text-neutral-300">
                  Sign up to receive new hot leads the moment signals are detected — be first to engage
                </p>
                <Link href="/login" className="text-xs text-cyan-400 hover:text-cyan-300 underline inline-block mt-1">
                  Create Free Account →
                </Link>
              </div>
            </div>
          </div>
        </div>

        <footer className="rr-footer">
          <div className="flex justify-center mb-3">
            <Image src="/logo-r.png" alt="" width={40} height={40} className="h-10 w-10 opacity-90" />
          </div>
          <p>© 2026 Signal intelligence for robotics sales.</p>
        </footer>

        {pipelineModalOpen && (
          <div
            className="fixed inset-0 z-[300] flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="pipeline-modal-title"
          >
            <div
              className="absolute inset-0 bg-black/75 backdrop-blur-sm"
              onClick={() => {
                setPipelineModalOpen(false);
                setPipelineModalInput('');
              }}
              aria-hidden
            />
            <div
              className="relative w-full max-w-md rounded-xl border border-emerald-700/35 bg-neutral-950 p-6 shadow-2xl ring-1 ring-emerald-500/10"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 id="pipeline-modal-title" className="text-lg font-bold text-emerald-400 mb-1">
                Preview your pipeline
              </h2>
              <p className="text-sm text-neutral-400 mb-4">
                Enter your company name or website URL. We&apos;ll open a prospect preview with top matches and an engagement plan.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const raw = pipelineModalInput.trim();
                  if (!raw) return;
                  setPipelineModalOpen(false);
                  setPipelineModalInput('');
                  router.push(`/pipeline-results?url=${encodeURIComponent(raw)}`);
                }}
              >
                <label htmlFor="pipeline-modal-input" className="sr-only">
                  Company name or URL
                </label>
                <input
                  id="pipeline-modal-input"
                  name="companyOrUrl"
                  type="text"
                  autoComplete="organization"
                  placeholder="e.g. Acme Robotics or acme.com"
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-900/80 px-3 py-2.5 text-sm text-neutral-200 placeholder:text-neutral-500 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600/40 mb-4"
                  value={pipelineModalInput}
                  onChange={(e) => setPipelineModalInput(e.target.value)}
                  autoFocus
                />
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <button
                    type="button"
                    className="px-4 py-2 text-sm text-neutral-400 hover:text-white rounded-lg"
                    onClick={() => {
                      setPipelineModalOpen(false);
                      setPipelineModalInput('');
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-lg bg-emerald-500 text-black text-sm font-semibold hover:bg-emerald-400 transition-colors"
                  >
                    Continue to pipeline
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}
