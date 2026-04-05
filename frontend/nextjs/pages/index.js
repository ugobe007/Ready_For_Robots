import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import Image from 'next/image';
import LoginDropdown from '../components/LoginDropdown';
import HotDealsScoringExplainer from '../components/HotDealsScoringExplainer';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
import { AutomationSpecBlock } from '../lib/automationProfile';
// signalsDisplay helpers used in dashboard; index.js relies on API-side dedup/cap

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

/** Hero stat cells: live summary counts, or em dash while the first homepage fetch is in flight. */
function formatHeroCount(value, statsLoaded) {
  if (!statsLoaded) return '—';
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString();
}

function stripHtml(s) {
  return String(s || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
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

  // CRM strip: longer name lists per tier (for rotation)
  useEffect(() => {
    const apiBase = getApiBase();
    let cancelled = false;
    const load = async () => {
      try {
        const [rAll, rHot, rWarm] = await Promise.all([
          fetch(`${apiBase}/api/leads?limit=40&sort=score`, liveFetchInit()),
          fetch(`${apiBase}/api/leads?tier=HOT&limit=35&sort=score`, liveFetchInit()),
          fetch(`${apiBase}/api/leads?tier=WARM&limit=35&sort=score`, liveFetchInit()),
        ]);
        const [dAll, dHot, dWarm] = await Promise.all([rAll.json(), rHot.json(), rWarm.json()]);
        if (cancelled) return;
        setCrmPreviewLists({
          active: extractLeadPreviews(dAll),
          hot: extractLeadPreviews(dHot),
          warm: extractLeadPreviews(dWarm),
        });
      } catch (e) {
        if (!cancelled) console.error('CRM preview lists:', e);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Spotlight leads fill names until tier lists load
  useEffect(() => {
    if (!hotLeads?.length) return;
    setCrmPreviewLists((prev) => {
      const fromSpotlight = {
        active: extractLeadPreviews(hotLeads),
        hot: extractLeadPreviews(hotLeads.filter((l) => l.priority_tier === 'HOT')),
        warm: extractLeadPreviews(hotLeads.filter((l) => l.priority_tier === 'WARM')),
      };
      return {
        active: prev.active.length ? prev.active : fromSpotlight.active,
        hot: prev.hot.length ? prev.hot : fromSpotlight.hot,
        warm: prev.warm.length ? prev.warm : fromSpotlight.warm,
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

  // Single batched fetch: summary + hot leads in one request (faster, fewer round trips, better for mobile)
  useEffect(() => {
    const apiBase = getApiBase();
    let cancelled = false;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10s for mobile/slow networks
    const fetchHomepage = async () => {
      const isFirstFetch = !homepageFetchCompletedRef.current;
      if (isFirstFetch) setLoading(true);
      try {
        const res = await fetch(
          `${apiBase}/api/leads/homepage?cb=${Date.now()}`,
          liveFetchInit({
            signal: controller.signal,
          }),
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        const s = data.summary || {};
        setStatsData({
          activeLeads: s.total ?? 0,
          hotDeals: s.hot ?? 0,
          liveSignals: s.total_signals ?? 0,
          warmPipeline: s.warm ?? 0,
          cold: s.cold ?? 0
        });
        setLeadsByIndustry(s.by_industry ?? {});
        // Preserve API order: recency-ranked + daily rotation (3 hot + 2 warm); do not re-sort by score
        setTierLegend(data.tierLegend || null);
        setScoringSystem(data.scoringSystem || null);
        setHotLeads(Array.isArray(data.hotLeads) ? data.hotLeads : []);
      } catch (err) {
        if (err?.name !== 'AbortError' && !cancelled) {
          console.error('Error fetching homepage data:', err);
          setHotLeads([]);
          setScoringSystem(null);
        }
      } finally {
        clearTimeout(timeout);
        if (!cancelled) {
          setStatsLoaded(true);
          homepageFetchCompletedRef.current = true;
          setLoading(false);
        }
      }
    };
    fetchHomepage();
    const interval = setInterval(fetchHomepage, 90000); // refresh every 90s
    return () => {
      cancelled = true;
      controller.abort();
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, []);

  // Use summary for counts (no full leads fetch)
  const hotCount = statsData.hotDeals ?? 0;
  const hottestSignal = hotLeads
    .flatMap(lead => (lead.signals || []).map(s => ({ ...s, company: lead.company_name })))
    .sort((a, b) => (b.signal_strength || 0) - (a.signal_strength || 0))[0];

  // Daily Hot Deals: already fetched as top 5 HOT (topHotDeals = hotLeads)
  const topHotDeals = hotLeads;

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
                <nav className="rr-hero-top-nav" aria-label="Quick links">
                  <Link href="/dashboard">Dashboard</Link>
                  <span className="rr-hero-top-nav-sep">·</span>
                  <Link href="/dashboard">Pipeline</Link>
                  <span className="rr-hero-top-nav-sep">·</span>
                  <Link href="/crm/">CRM</Link>
                  <span className="rr-hero-top-nav-sep">·</span>
                  <Link href="/search">Search</Link>
                  <span className="rr-hero-top-nav-sep">·</span>
                  <a href="#leads">Browse leads</a>
                  <span className="rr-hero-top-nav-sep">·</span>
                  <Link href="/about">Signals</Link>
                  <span className="rr-hero-top-nav-muted hidden sm:inline">
                    · 14 types · 140+ sources
                  </span>
                </nav>
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
              <aside
                className="rr-hero-ticker-panel rr-hero-ticker-panel--live rr-hero-ticker-panel--crm-names"
                aria-label="Signal feed and live pipeline totals"
              >
                <div className="rr-testimonial-bar rr-testimonial-bar--compact">
                  <span className="rr-testimonial-ico shrink-0" aria-hidden>💬</span>
                  <div className="flex-1 min-w-0">
                    <div key={currentQuoteIndex} className="rr-testimonial-text">
                      {automationQuotes[currentQuoteIndex].text}
                    </div>
                  </div>
                  <span className="rr-testimonial-counter tabular-nums">
                    {currentQuoteIndex + 1}/{automationQuotes.length}
                  </span>
                </div>
                <p className="rr-hero-sample-legend">
                  {statsLoaded
                    ? 'Live pipeline totals · same tiering as the dashboard'
                    : 'Loading live totals…'}
                </p>
                <div className="rr-hero-stat-strip rr-hero-stat-strip--compact">
                  <div className="rr-hero-stat-inline rr-hero-stat-inline--sm">
                    <span className="n text-[var(--rr-text)] tabular-nums">
                      {formatHeroCount(statsData.activeLeads, statsLoaded)}
                    </span>
                    <span className="l">Active</span>
                  </div>
                  <div className="rr-hero-stat-inline rr-hero-stat-inline--sm">
                    <span className="n tabular-nums" style={{ color: 'var(--rr-orange)' }}>
                      {formatHeroCount(statsData.hotDeals, statsLoaded)}
                    </span>
                    <span className="l">Hot</span>
                  </div>
                  <div
                    className="rr-hero-stat-inline rr-hero-stat-inline--sm"
                    title="Buying-intent signals across all leads"
                  >
                    <span className="n tabular-nums" style={{ color: 'var(--rr-cyan)' }}>
                      {formatHeroCount(statsData.liveSignals, statsLoaded)}
                    </span>
                    <span className="l">Signals</span>
                  </div>
                  <div className="rr-hero-stat-inline rr-hero-stat-inline--sm">
                    <span className="n tabular-nums" style={{ color: 'var(--rr-green)' }}>
                      {formatHeroCount(statsData.warmPipeline, statsLoaded)}
                    </span>
                    <span className="l">Warm</span>
                  </div>
                </div>
                <div
                  className="rr-hero-crm-strip rr-hero-crm-strip--names"
                  title="Live counts · inline company + opportunity — open the dashboard for full lists"
                >
                  <div className="rr-hero-crm-strip-label">CRM pipeline</div>
                  <div className="rr-hero-crm-strip-stats rr-hero-crm-strip-stats--two">
                    <div className="rr-hero-crm-tile rr-hero-crm-tile--inline">
                      <p
                        className="rr-hero-crm-inline"
                        title={
                          crmPrevActive
                            ? [crmPrevActive.name, crmPrevActive.opp].filter(Boolean).join(' — ')
                            : undefined
                        }
                        aria-live="polite"
                      >
                        <span className="rr-hero-crm-inline-ct tabular-nums">
                          {formatHeroCount(statsData.activeLeads, statsLoaded)}
                        </span>
                        <span className="rr-hero-crm-inline-dot">·</span>
                        <span className="rr-hero-crm-inline-role">active projects</span>
                        {crmPrevActive ? (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-co">{crmPrevActive.name}</span>
                            {crmPrevActive.opp ? (
                              <>
                                <span className="rr-hero-crm-inline-dot">·</span>
                                <span className="rr-hero-crm-inline-opp">{crmPrevActive.opp}</span>
                              </>
                            ) : null}
                          </>
                        ) : (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-placeholder">
                              {statsLoaded ? '…' : '—'}
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                    <div className="rr-hero-crm-tile rr-hero-crm-tile--inline rr-hero-crm-tile--split">
                      <p
                        className="rr-hero-crm-inline rr-hero-crm-inline--stacked"
                        title={
                          crmPrevHot
                            ? [crmPrevHot.name, crmPrevHot.opp].filter(Boolean).join(' — ')
                            : undefined
                        }
                        aria-live="polite"
                      >
                        <span className="rr-hero-crm-inline-ct rr-hero-crm-inline-ct--hot tabular-nums">
                          {formatHeroCount(statsData.hotDeals, statsLoaded)}
                        </span>
                        <span className="rr-hero-crm-inline-dot">·</span>
                        <span className="rr-hero-crm-inline-role rr-hero-crm-inline-role--hot">hot</span>
                        {crmPrevHot ? (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-co">{crmPrevHot.name}</span>
                            {crmPrevHot.opp ? (
                              <>
                                <span className="rr-hero-crm-inline-dot">·</span>
                                <span className="rr-hero-crm-inline-opp">{crmPrevHot.opp}</span>
                              </>
                            ) : null}
                          </>
                        ) : (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-placeholder">
                              {statsLoaded ? '…' : '—'}
                            </span>
                          </>
                        )}
                      </p>
                      <div className="rr-hero-crm-hw-divider" aria-hidden />
                      <p
                        className="rr-hero-crm-inline rr-hero-crm-inline--stacked"
                        title={
                          crmPrevWarm
                            ? [crmPrevWarm.name, crmPrevWarm.opp].filter(Boolean).join(' — ')
                            : undefined
                        }
                        aria-live="polite"
                      >
                        <span className="rr-hero-crm-inline-ct rr-hero-crm-inline-ct--warm tabular-nums">
                          {formatHeroCount(statsData.warmPipeline, statsLoaded)}
                        </span>
                        <span className="rr-hero-crm-inline-dot">·</span>
                        <span className="rr-hero-crm-inline-role rr-hero-crm-inline-role--warm">warm</span>
                        {crmPrevWarm ? (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-co">{crmPrevWarm.name}</span>
                            {crmPrevWarm.opp ? (
                              <>
                                <span className="rr-hero-crm-inline-dot">·</span>
                                <span className="rr-hero-crm-inline-opp">{crmPrevWarm.opp}</span>
                              </>
                            ) : null}
                          </>
                        ) : (
                          <>
                            <span className="rr-hero-crm-inline-dot">·</span>
                            <span className="rr-hero-crm-inline-placeholder">
                              {statsLoaded ? '…' : '—'}
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
                <p className="rr-emerging-note rr-emerging-note--inline">
                  Emerging ·{' '}
                  <span className="tabular-nums">{formatHeroCount(statsData.cold, statsLoaded)}</span> in pipeline
                </p>
                <Link
                  href="/market-insights/"
                  className="rr-hero-explore-btn"
                  title="Market insights — industry context and timing"
                >
                  Explore
                </Link>
              </aside>
            </div>
          </div>
        </div>

        <div className="rr-section !pt-0">
              {Object.keys(leadsByIndustry).length > 0 && (() => {
                const merged = {};
                Object.entries(leadsByIndustry).forEach(([industry, count]) => {
                  const key = (industry || '').trim().toLowerCase() === 'unknown' ? 'New' : (industry || 'New');
                  merged[key] = (merged[key] || 0) + (count || 0);
                });
                return (
                <div className="rr-industry-cloud">
                  <div className="rr-industry-cloud-label">Leads by Industry</div>
                  <div className="rr-industry-tags">
                    {Object.entries(merged)
                      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
                      .map(([industry, count]) => (
                        <span key={industry} className="rr-ind-tag">
                          {industry} <span className="cnt">{count}</span>
                        </span>
                      ))}
                  </div>
                </div>
                );
              })()}
        </div>

        {/* CTA — CRM / pipeline builder (layout aligned with dashboard pipeline card) */}
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
                    {hotLeads.slice(0, 6).map((lead) => (
                      <Link
                        key={lead.id}
                        href="#leads"
                        className="rr-home-spotlight-chip"
                      >
                        {lead.company_name}
                      </Link>
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

          <Link href="/dashboard" className="rr-browse-all-btn">
            Browse All {statsData.activeLeads} Leads by Industry →
          </Link>
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

        {/* ENHANCED: Strategic Snapshot - Top Hot Deals with More POP */}
        <div id="leads" className="max-w-7xl mx-auto px-6 pt-6 pb-10 md:pb-12 space-y-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="text-xs text-neutral-400 font-semibold uppercase tracking-widest border border-neutral-800 px-2 py-0.5 rounded">
                Daily Spotlight
              </div>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Daily spotlight deals
            </h2>
            <p className="text-lg text-neutral-400">
              Five accounts rotate each day: three Hot and two Warm, ranked by newest signal activity first.
            </p>
            {tierLegend && (
              <div className="mt-5 grid md:grid-cols-3 gap-3 text-left">
                {['HOT', 'WARM', 'COLD'].map((key) => {
                  const block = tierLegend[key];
                  if (!block) return null;
                  const accent =
                    key === 'HOT' ? 'border-orange-700/50 bg-orange-950/20' :
                    key === 'WARM' ? 'border-amber-700/50 bg-amber-950/15' :
                    'border-cyan-800/50 bg-cyan-950/15';
                  return (
                    <div key={key} className={`rounded-lg border px-4 py-3 ${accent}`}>
                      <div className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-0.5">
                        {block.label}
                        <span className="text-neutral-500 font-normal normal-case"> — {block.tagline}</span>
                      </div>
                      <p className="text-xs text-neutral-400 leading-snug">{block.description}</p>
                    </div>
                  );
                })}
              </div>
            )}
            <div className="mt-6">
              <HotDealsScoringExplainer data={scoringSystem} />
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-neutral-400 mt-4">Loading spotlight deals...</p>
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
                        <div className="flex items-center gap-2">
                          <h4 className="text-lg font-semibold text-white group-hover:text-orange-300 transition-colors">
                            {lead.company_name}
                          </h4>
                          <span
                            className={`px-2 py-0.5 text-xs font-semibold rounded text-white ${
                              lead.priority_tier === 'WARM'
                                ? 'bg-amber-600'
                                : lead.priority_tier === 'COLD'
                                  ? 'bg-cyan-700'
                                  : 'bg-orange-600'
                            }`}
                          >
                            {lead.priority_tier === 'WARM'
                              ? '⚡ Warm'
                              : lead.priority_tier === 'COLD'
                                ? '✦ Emerging'
                                : '🔥 Hot'}
                          </span>
                          <span className="text-neutral-500 text-sm">{isExpanded ? '▲' : '▼'}</span>
                        </div>
                        <div className="text-sm text-neutral-400">
                          {lead.industry} • {lead.location_city && lead.location_state ? `${lead.location_city}, ${lead.location_state}` : 'Location N/A'}
                        </div>
                        {lead.share_summary && (
                          <p className="text-sm text-neutral-300 leading-snug pt-1 border-l-2 border-orange-600/50 pl-3">
                            {lead.share_summary}
                          </p>
                        )}
                        {cardSignals.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {cardSignals.map((signal, sidx) => (
                              <span key={sidx} className="text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2 py-1 rounded font-medium">
                                {signal.signal_label || signal.signal_type}
                              </span>
                            ))}
                          </div>
                        )}
                        {!isExpanded && (
                          <AutomationSpecBlock profile={lead.automation_profile} compact theme="home" />
                        )}
                      </div>
                      <div className="text-right space-y-2 flex flex-col items-end">
                        <div className="relative">
                          <div className="text-3xl font-bold text-orange-400">
                            {score.toFixed(0)}
                          </div>
                          <div className="text-xs text-neutral-500 font-medium">SCORE</div>
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
                              const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
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
                                return (
                                  <>
                                    <a href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-black text-neutral-400 hover:text-white text-xs">
                                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                                      Share on X
                                    </a>
                                    <a href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-[#0a66c2] text-neutral-400 hover:text-white text-xs">
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
                            <Link
                              href={`/dashboard?analyze=${lead.id}`}
                              className="inline-flex items-center gap-1 text-sm text-orange-400 hover:text-orange-300 font-semibold whitespace-nowrap"
                            >
                              Full AI analysis →
                            </Link>
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

        {/* Browse All Leads by Industry */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="border border-neutral-800 rounded-lg p-8 text-center space-y-4">
            <h3 className="text-2xl font-semibold text-white">Browse All {statsData.activeLeads} Leads by Industry</h3>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              View complete database organized by Logistics, Hospitality, Healthcare, Food Service, and more
            </p>
            <div className="pt-2">
              <Link 
                href="/dashboard" 
                className="inline-block px-8 py-3 border border-emerald-500 text-emerald-400 rounded-lg hover:bg-emerald-950/30 transition-colors font-medium"
              >
                View Full Dashboard →
              </Link>
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
