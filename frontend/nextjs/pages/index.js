import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import LoginDropdown from '../components/LoginDropdown';
import HotDealsScoringExplainer from '../components/HotDealsScoringExplainer';
import { getApiBase, liveFetchInit } from '../lib/apiBase';
// signalsDisplay helpers used in dashboard; index.js relies on API-side dedup/cap

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

export default function Signals() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  
  // Stats ticker data - from /api/leads/summary (full DB counts, not limited by leads list)
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

  // Single batched fetch: summary + hot leads in one request (faster, fewer round trips, better for mobile)
  useEffect(() => {
    const apiBase = getApiBase();
    let cancelled = false;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10s for mobile/slow networks
    const fetchHomepage = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiBase}/api/leads/homepage`, liveFetchInit({
          signal: controller.signal,
        }));
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
  const warmCount = statsData.warmPipeline ?? 0;
  const emergingCount = statsData.cold ?? 0;
  const totalSignals = statsData.liveSignals ?? 0;
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

  return (
    <>
      <Head>
        <title>Automation Sales Leads with Actionable Signals | Ready For Robots</title>
        <meta name="description" content="Automation sales leads with actionable signals. Buying intent from 150+ sources — labor shortages, CapEx, new facilities. Each lead comes with signals you can act on." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={BASE_URL} />
        <meta property="og:title" content="Ready For Robots | Automation Sales Leads with Actionable Signals" />
        <meta property="og:description" content="Automation sales leads with actionable signals. We track buying intent across 150+ sources. Each lead comes with signals you can act on." />
        <meta property="og:image" content={`${BASE_URL}/og-logo.png`} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="Ready for Robots" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content={`${BASE_URL}/og-logo.png`} />
        <meta name="twitter:title" content="Ready For Robots | Automation Sales Leads with Actionable Signals" />
        <meta name="twitter:description" content="Automation sales leads with actionable signals. Each lead comes with signals you can act on." />
      </Head>

      <div className="min-h-screen bg-black text-white">
        {/* Navigation Bar */}
        <div className="border-b border-neutral-800">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <h1 className="text-lg font-semibold text-white">
                  <span className="text-white">READY</span>
                  {' '}
                  <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">→</span>
                  {' '}
                  <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">ROBOTS</span>
                </h1>
                <nav className="hidden md:flex items-center gap-6 text-sm">
                  <Link href="/dashboard" className="text-neutral-400 hover:text-emerald-400 transition-colors">Dashboard</Link>
                  <Link href="/market-insights" className="text-neutral-400 hover:text-emerald-400 transition-colors">Market Insights</Link>
                  <Link href="/about" className="text-neutral-400 hover:text-cyan-400 transition-colors">Signals</Link>
                  <a href="#leads" className="text-neutral-400 hover:text-emerald-400 transition-colors">Browse Leads</a>
                  <Link href="/newsletter" className="text-neutral-400 hover:text-cyan-400 transition-colors flex items-center gap-1">
                    📰 Newsletter
                  </Link>
                  <Link href="/roi-calculator" className="text-neutral-400 hover:text-emerald-400 transition-colors">ROI Calculator</Link>
                </nav>
              </div>
              <div className="hidden md:flex items-center gap-4">
                <LoginDropdown className="text-neutral-400" />
                <Link href="/login" className="text-sm px-4 py-2 border border-emerald-500 text-emerald-400 rounded hover:bg-emerald-950/30 transition-colors">
                  Sign Up Free
                </Link>
                
                {/* Mobile Menu */}
                <div className="md:hidden relative">
                  <button 
                    onClick={() => {
                      const menu = document.getElementById('mobile-menu');
                      menu.classList.toggle('hidden');
                    }}
                    className="text-neutral-400 hover:text-white px-3 py-2 text-xl"
                  >
                    ☰
                  </button>
                  <div id="mobile-menu" className="hidden absolute right-0 top-full mt-2 w-56 border border-neutral-800 rounded-lg bg-neutral-950 shadow-xl z-50">
                    <Link href="/dashboard" className="block px-4 py-3 text-sm text-emerald-400 hover:bg-neutral-900 border-b border-neutral-800">
                      📊 Dashboard
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
                      ✨ Sign Up Free
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hero */}
        <div className="max-w-5xl mx-auto px-6 py-10 md:py-12">
          <div className="space-y-6">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-widest">⚡ Curated lead lists · 14 signal types · 140+ sources</div>
            {/* Logo + Headline: icon dominant (bigger than descriptor), Ready For Robots as descriptor */}
            <div className="flex flex-col md:flex-row md:items-end gap-6 md:gap-10">
              <div className="flex-shrink-0">
                <div className="w-24 h-24 md:w-36 md:h-36 lg:w-44 lg:h-44 rounded-2xl bg-neutral-900/80 border border-neutral-800 flex items-center justify-center p-2 shadow-2xl shadow-emerald-500/10 overflow-hidden">
                  <img src="/logo.png" alt="Ready For Robots" className="w-full h-full object-contain" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold tracking-tight leading-tight text-white">
                  Automation Sales Leads with Actionable Signals
                </h2>
                <p className="mt-2 md:mt-3 text-base md:text-lg text-neutral-400 font-medium">
                  Ready For Robots
                </p>
              </div>
            </div>
            <p className="text-lg md:text-xl text-neutral-300 max-w-3xl">
              We track buying intent across 150+ sources — labor shortages, CapEx, new facilities, executive hires. Each lead comes with signals you can act on.
            </p>
            
            {/* Stats Ticker - uses /api/leads/summary for full DB counts */}
            <div className="space-y-3">
              {/* Rotating Automation Quotes */}
              <div className="border border-emerald-800/30 bg-gradient-to-r from-emerald-950/30 to-cyan-950/30 rounded-lg py-3 px-5 overflow-hidden">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center animate-pulse">
                      <span className="text-base">💬</span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div 
                      key={currentQuoteIndex}
                      className="animate-[fadeIn_0.5s_ease-in-out]"
                    >
                      <p className="text-sm md:text-base text-white font-medium italic">
                        {automationQuotes[currentQuoteIndex].text}
                      </p>
                      <p className="text-xs text-emerald-400 mt-0.5">
                        {automationQuotes[currentQuoteIndex].company} · <span className="text-cyan-400">{automationQuotes[currentQuoteIndex].signal}</span>
                      </p>
                    </div>
                  </div>
                  <div className="hidden md:block flex-shrink-0">
                    <div className="text-xs text-neutral-400 font-mono">
                      {currentQuoteIndex + 1}/{automationQuotes.length}
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats Bar - Tighter, values update smoothly without re-rendering */}
              <div className="border border-emerald-800/40 bg-gradient-to-b from-neutral-900 to-black rounded-lg py-2 px-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                  <div className="group cursor-default">
                    <div className="text-2xl md:text-3xl font-black bg-gradient-to-br from-white to-neutral-300 bg-clip-text text-transparent group-hover:scale-110 transition-all duration-500">
                      {statsData.activeLeads}
                    </div>
                    <div className="text-sm text-neutral-400 font-semibold tracking-wide">
                      {statsLoaded ? 'ACTIVE LEADS' : 'LOADING...'}
                    </div>
                  </div>
                  <div className="group cursor-default">
                    <div className="text-2xl md:text-3xl font-black bg-gradient-to-br from-orange-400 to-red-500 bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(251,146,60,0.5)] group-hover:scale-110 transition-all duration-500">
                      {statsData.hotDeals}
                    </div>
                    <div className="text-sm text-orange-400 font-semibold tracking-wide">🔥 HOT DEALS</div>
                  </div>
                  <div className="group cursor-default">
                    <div className="text-2xl md:text-3xl font-black bg-gradient-to-br from-cyan-400 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(34,211,238,0.4)] group-hover:scale-110 transition-all duration-500">
                      {statsData.liveSignals}
                    </div>
                    <div className="text-sm text-cyan-400 font-semibold tracking-wide">LIVE SIGNALS</div>
                  </div>
                  <div className="group cursor-default">
                    <div className="text-2xl md:text-3xl font-black bg-gradient-to-br from-emerald-400 to-green-500 bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(52,211,153,0.4)] group-hover:scale-110 transition-all duration-500">
                      {statsData.warmPipeline}
                    </div>
                    <div className="text-sm text-emerald-400 font-semibold tracking-wide">WARM PIPELINE</div>
                  </div>
                </div>
                {emergingCount > 0 && (
                  <p className="text-[11px] text-neutral-500 text-center mt-2 px-1">
                    <span className="text-cyan-500/90 font-medium">Emerging</span>
                    {' · '}
                    {emergingCount.toLocaleString()} opportunities in the full pipeline (watchlist / early signals — see legend below)
                  </p>
                )}
              </div>

              {/* Leads per industry — never show "Unknown"; merge into "New" */}
              {Object.keys(leadsByIndustry).length > 0 && (() => {
                const merged = {};
                Object.entries(leadsByIndustry).forEach(([industry, count]) => {
                  const key = (industry || '').trim().toLowerCase() === 'unknown' ? 'New' : (industry || 'New');
                  merged[key] = (merged[key] || 0) + (count || 0);
                });
                return (
                <div className="border border-neutral-800 rounded-lg py-3 px-4 bg-neutral-900/50">
                  <div className="text-xs text-neutral-500 font-semibold uppercase tracking-widest mb-2">Leads by industry</div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                    {Object.entries(merged)
                      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
                      .map(([industry, count]) => (
                        <span key={industry} className="text-sm text-neutral-300">
                          <span className="text-white font-medium">{industry}</span>
                          <span className="text-emerald-400/90 font-semibold ml-1.5">{count}</span>
                        </span>
                      ))}
                  </div>
                </div>
                );
              })()}
            </div>
          </div>
        </div>

        {/* CTA - Build Your Pipeline */}
        <div id="cta" className="max-w-5xl mx-auto px-6 pt-4 pb-8">
          <div className="relative border-2 border-neutral-600 rounded-xl px-8 py-8 bg-gradient-to-b from-neutral-900/50 to-black/50 shadow-[0_0_40px_rgba(255,255,255,0.05)]">
            
            <div className="relative space-y-6">
              <div className="space-y-3 text-center md:text-left">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-neutral-800/50 border border-neutral-700 rounded-full">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                  <span className="text-xs font-semibold text-neutral-300 uppercase tracking-wide">Free Pipeline Builder</span>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-white">
                  Build Your Sales Pipeline
                </h2>
                <p className="text-base md:text-lg text-neutral-400">
                  See your top 5 prospect matches instantly — with engagement strategy & buying signals
                </p>
              </div>

              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  const url = e.target.robotUrl.value;
                  router.push(`/pipeline-results?url=${encodeURIComponent(url)}`);
                }}
                className="space-y-4"
              >
                <div>
                  <input
                    type="text"
                    name="robotUrl"
                    placeholder="Enter your robot company website (e.g., amplibotics.ai)"
                    className="w-full px-5 py-4 bg-black border-2 border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:shadow-[0_0_20px_rgba(255,255,255,0.1)] transition-all"
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full px-6 py-4 bg-transparent border-2 border-emerald-500 text-emerald-400 rounded-lg font-bold text-lg hover:border-emerald-400 hover:text-emerald-300 hover:shadow-[0_0_30px_rgba(16,185,129,0.2)] transition-all duration-200"
                >
                  Build Pipeline →
                </button>
              </form>

              <div className="flex items-center justify-center md:justify-between text-xs text-neutral-500 pt-2 border-t border-neutral-800 flex-wrap gap-3">
                <span className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  No signup required
                </span>
                <span className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  Instant results
                </span>
                <span className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  Free trial
                </span>
              </div>
            </div>
          </div>
          
          {/* View All Leads CTA */}
          <div className="pt-4">
            <Link 
              href="/dashboard" 
              className="block text-center px-6 py-3 bg-transparent border border-neutral-600 text-neutral-300 rounded-lg hover:border-neutral-500 hover:text-white hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] transition-all duration-200 font-medium"
            >
              Browse All {statsData.activeLeads} Leads by Industry →
            </Link>
          </div>
        </div>

        {/* Link to Signals Page */}
        <div className="max-w-5xl mx-auto px-6 pb-4">
          <Link href="#signals" className="group block border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-5 hover:border-emerald-700/50 hover:bg-emerald-950/30 transition-all">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-sm font-semibold text-emerald-400">💡 Why Signals Matter</div>
                <div className="text-xs text-neutral-500 hidden md:block">Learn how we identify buying intent</div>
              </div>
              <div className="text-emerald-400 group-hover:translate-x-1 transition-transform">→</div>
            </div>
          </Link>
        </div>

        {/* ENHANCED: Strategic Snapshot - Top Hot Deals with More POP */}
        <div id="leads" className="max-w-5xl mx-auto px-6 pt-6 pb-10 md:pb-12 space-y-8">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="text-xs text-orange-400 font-semibold uppercase tracking-widest">
                ⚡ DAILY SPOTLIGHT
              </div>
              <div className="flex gap-1">
                <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse"></span>
                <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></span>
              </div>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Daily spotlight deals
            </h2>
            <p className="text-lg text-neutral-300">
              Five accounts rotate each day: <span className="text-orange-400 font-semibold">three Hot</span> and{' '}
              <span className="text-amber-400 font-semibold">two Warm</span>, ranked by{' '}
              <span className="text-neutral-200">newest signal activity</span> first so the list refreshes. Same high scorers will not dominate every visit.
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
                    className={`group border rounded-lg p-4 space-y-3 transition-all cursor-pointer ${
                      isExpanded 
                        ? 'border-orange-500/80 bg-orange-950/15 shadow-lg shadow-orange-500/5' 
                        : 'border-orange-800/40 hover:border-orange-500/60 bg-orange-950/5 hover:bg-orange-950/10'
                    }`}
                    style={{
                      animation: `slideIn 0.5s ease-out ${idx * 0.05}s both`
                    }}
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
                              const shareText = lead.share_blurb || `${lead.company_name} (${lead.industry || 'Automation'}) — automation signals · Ready For Robots`;
                              const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
                              const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
                              const copyShare = () => {
                                navigator.clipboard?.writeText(`${shareText} ${shareUrl}`);
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
                        className="pt-4 mt-3 border-t border-orange-800/40 space-y-4"
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
                              <div key={label} className="bg-neutral-900/60 rounded p-2 text-center">
                                <div className="text-base font-bold text-orange-300">{(val || 0).toFixed(0)}</div>
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

                        {/* Share + CTA row */}
                        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs text-neutral-500">Share:</span>
                            {(() => {
                              const shareUrl = `${BASE_URL}/#leads`;
                              const shareText = lead.share_blurb || `${lead.company_name} (${lead.industry || 'Automation'}) — automation signals · Ready For Robots`;
                              return (
                                <>
                                  <a href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-black text-neutral-400 hover:text-white text-xs">
                                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                                    X
                                  </a>
                                  <a href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-[#0a66c2] text-neutral-400 hover:text-white text-xs">
                                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                                    LinkedIn
                                  </a>
                                  <button
                                    type="button"
                                    onClick={() => navigator.clipboard?.writeText(`${shareText} ${shareUrl}`)}
                                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-neutral-800 hover:bg-emerald-600 text-neutral-400 hover:text-white text-xs"
                                  >
                                    Copy
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
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Browse All Leads by Industry */}
        <div className="max-w-5xl mx-auto px-6 py-8">
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
        <div id="signals" className="max-w-5xl mx-auto px-6 py-10 md:py-12 space-y-10">
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
        <div className="max-w-5xl mx-auto px-6 py-10 md:py-12 space-y-10">
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
        <div className="max-w-5xl mx-auto px-6 py-10 md:py-12 space-y-10">
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

        {/* Footer - Simple one-liner */}
        <div className="border-t border-neutral-800 py-8">
          <div className="max-w-5xl mx-auto px-6 text-center text-sm text-neutral-500">
            <p>© 2026 Ready → Robots. Signal intelligence for robotics sales.</p>
          </div>
        </div>
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
