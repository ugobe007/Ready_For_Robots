import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

export default function Signals() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState('all');
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [temperatureFilter, setTemperatureFilter] = useState('all'); // 'all', 'hot', 'warm', 'cold'
  
  // Stats ticker data - from /api/leads/summary (full DB counts, not limited by leads list)
  const [statsData, setStatsData] = useState({
    activeLeads: 0,
    hotDeals: 0,
    liveSignals: 0,
    warmPipeline: 0
  });
  
  // Live signal flow state (pythh.ai style)
  const [signalFlow, setSignalFlow] = useState({
    labor_shortage: { value: 0.67, delta: 0, prev: 0.67 },
    expansion: { value: 0.54, delta: 0, prev: 0.54 },
    safety: { value: 0.71, delta: 0, prev: 0.71 }
  });

  // Hot leads state - will be fetched from API
  const [hotLeads, setHotLeads] = useState([]);

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

  const API_BASE = 'https://readyforrobots.com';

  // Fetch pipeline summary (full DB counts for ticker)
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/leads/summary`);
        const data = await res.json();
        setStatsData({
          activeLeads: data.total ?? 0,
          hotDeals: data.hot ?? 0,
          liveSignals: data.total_signals ?? 0,
          warmPipeline: data.warm ?? 0
        });
      } catch (err) {
        console.error('Error fetching summary:', err);
      }
    };
    fetchSummary();
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch all leads - use production API
  useEffect(() => {
    const fetchLeads = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/api/leads`);
        const data = await res.json();
        setLeads(Array.isArray(data) ? data : []);
        
        const hotOnly = (Array.isArray(data) ? data : [])
          .filter(l => l.temperature === 'hot' || l.priority_tier === 'HOT')
          .sort((a, b) => {
            const scoreA = typeof a.score === 'object' ? (a.score.overall_score || 0) : (a.score || 0);
            const scoreB = typeof b.score === 'object' ? (b.score.overall_score || 0) : (b.score || 0);
            return scoreB - scoreA;
          })
          .slice(0, 5);
        setHotLeads(hotOnly);
      } catch (err) {
        console.error('Error fetching leads:', err);
        setLeads([]);
        setHotLeads([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLeads();
    const interval = setInterval(fetchLeads, 30000);
    return () => clearInterval(interval);
  }, []);

  // Calculate lead counts by temperature (for leads list display)
  const hotCount = leads.filter(l => l.temperature === 'hot' || l.priority_tier === 'HOT').length;
  const warmCount = leads.filter(l => l.temperature === 'warm' || l.priority_tier === 'WARM').length;
  const coldCount = leads.filter(l => l.temperature === 'cold' || l.priority_tier === 'COLD').length;
  
  // Total signals from leads list (for fallback; ticker uses summary)
  const totalSignals = leads.reduce((sum, lead) => sum + (lead.signals?.length || 0), 0);
  const hottestSignal = leads
    .flatMap(lead => (lead.signals || []).map(s => ({ ...s, company: lead.company_name })))
    .sort((a, b) => (b.signal_strength || 0) - (a.signal_strength || 0))[0];

  // Get top HOT deals for Strategic Snapshot
  const topHotDeals = leads
    .filter(l => l.temperature === 'hot' || l.priority_tier === 'HOT')
    .sort((a, b) => {
      const scoreA = typeof a.score === 'object' ? (a.score.overall_score || 0) : (a.score || 0);
      const scoreB = typeof b.score === 'object' ? (b.score.overall_score || 0) : (b.score || 0);
      return scoreB - scoreA;
    })
    .slice(0, 5);

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
        <title>Signal Intelligence Framework | Ready → Robots</title>
        <meta name="description" content="Robot Ready Sales Leads with Signal Intelligence. Daily automation news, hot deals, and market intelligence." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={BASE_URL} />
        <meta property="og:title" content="Ready For Robots | Robot Ready Sales Leads with Signal Intelligence" />
        <meta property="og:description" content="Robot Ready Sales Leads with Signal Intelligence. Daily automation news, hot deals, and market intelligence." />
        <meta property="og:image" content={`${BASE_URL}/og-banner.png`} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="Ready for Robots" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content={`${BASE_URL}/og-banner.png`} />
        <meta name="twitter:title" content="Ready For Robots | Robot Ready Sales Leads with Signal Intelligence" />
        <meta name="twitter:description" content="Robot Ready Sales Leads with Signal Intelligence. Daily automation news, hot deals, and market intelligence." />
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
                  <Link href="/about" className="text-neutral-400 hover:text-cyan-400 transition-colors">Signals</Link>
                  <a href="#leads" className="text-neutral-400 hover:text-emerald-400 transition-colors">Browse Leads</a>
                  <Link href="/newsletter" className="text-neutral-400 hover:text-cyan-400 transition-colors flex items-center gap-1">
                    📰 Newsletter
                  </Link>
                  <Link href="/roi-calculator" className="text-neutral-400 hover:text-emerald-400 transition-colors">ROI Calculator</Link>
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <Link href="/login" className="hidden md:inline text-sm text-neutral-400 hover:text-white transition-colors">Login</Link>
                <Link href="/login" className="hidden md:inline text-sm px-4 py-2 border border-emerald-500 text-emerald-400 rounded hover:bg-emerald-950/30 transition-colors">
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
                      🔐 Login
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
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-widest">⚡ Powered by 14 Signal Types · 140+ Data Sources</div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
              <span className="bg-gradient-to-r from-violet-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                Robot Ready Sales Leads with Signal Intelligence
              </span>
            </h2>
            <p className="text-lg md:text-xl text-neutral-300 max-w-3xl">
              Stop cold calling. We track over 150 news sources to detect buying signals — labor shortages, new facilities, executive hires, CapEx budgets. You get warm leads, not dead ends.
            </p>
            
            {/* Stats Ticker - uses /api/leads/summary for full DB counts */}
            {(statsData.activeLeads > 0 || leads.length > 0) && (
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
                    <div className="text-sm text-neutral-400 font-semibold tracking-wide">ACTIVE LEADS</div>
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
              </div>
            </div>
            )}
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
              Browse All {leads.length} Leads by Industry →
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
                🔥 DAILY HOT DEALS
              </div>
              <div className="flex gap-1">
                <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse"></span>
                <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></span>
              </div>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Daily Hot Deals
            </h2>
            <p className="text-lg text-neutral-300">
              Live companies with <span className="text-red-400 font-semibold">urgent automation needs</span> — updated from our signal intelligence pipeline. Click any company for full AI analysis.
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-neutral-400 mt-4">Loading daily hot deals...</p>
            </div>
          ) : topHotDeals.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-neutral-400">No hot deals right now. Our scraper runs at 9am, 3pm & 9pm — check back soon!</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {topHotDeals.map((lead, idx) => {
                const score = typeof lead.score === 'object' ? (lead.score.overall_score || 0) : (lead.score || 0);
                const topSignals = (lead.signals || []).slice(0, 2);
                
                return (
                  <div 
                    key={lead.id}
                    onClick={() => router.push(`/analyze?id=${lead.id}`)}
                    className="group border border-orange-800/40 hover:border-orange-500/60 bg-orange-950/5 hover:bg-orange-950/10 rounded-lg p-4 space-y-3 transition-all cursor-pointer"
                    style={{
                      animation: `slideIn 0.5s ease-out ${idx * 0.05}s both`
                    }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-1.5">
                        <div className="flex items-center gap-2">
                          <h4 
                            className="text-lg font-semibold text-white group-hover:text-orange-300 transition-colors cursor-pointer"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/analyze?id=${lead.id}`);
                            }}
                          >
                            {lead.company_name}
                          </h4>
                          <span className="px-2 py-0.5 text-xs font-semibold bg-orange-600 text-white rounded">
                            🔥 HOT
                          </span>
                        </div>
                        <div className="text-sm text-neutral-400">
                          {lead.industry} • {lead.location_city && lead.location_state ? `${lead.location_city}, ${lead.location_state}` : 'Location N/A'}
                        </div>
                        {topSignals.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {topSignals.map((signal, sidx) => (
                              <span key={sidx} className="text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2 py-1 rounded font-medium">
                                {signal.signal_type}
                              </span>
                            ))}
                            {(lead.signals?.length || 0) > 2 && (
                              <span className="text-xs text-orange-400 font-bold bg-orange-950/30 border border-orange-800/40 px-2 py-1 rounded">
                                +{lead.signals.length - 2} more signals
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-right space-y-2">
                        <div className="relative">
                          <div className="text-3xl font-bold text-orange-400">
                            {score.toFixed(0)}
                          </div>
                          <div className="text-xs text-neutral-500 font-medium">SCORE</div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/analyze?id=${lead.id}`);
                          }}
                          className="text-xs text-orange-400 hover:text-orange-300 font-semibold underline"
                        >
                          Analyze →
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Browse All Leads by Industry */}
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="border border-neutral-800 rounded-lg p-8 text-center space-y-4">
            <h3 className="text-2xl font-semibold text-white">Browse All {leads.length} Leads by Industry</h3>
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
