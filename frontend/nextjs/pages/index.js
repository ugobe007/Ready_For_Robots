import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';

export default function Signals() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState('all');
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [temperatureFilter, setTemperatureFilter] = useState('all'); // 'all', 'hot', 'warm', 'cold'
  
  // Live signal flow state (pythh.ai style)
  const [signalFlow, setSignalFlow] = useState({
    labor_shortage: { value: 0.67, delta: 0, prev: 0.67 },
    expansion: { value: 0.54, delta: 0, prev: 0.54 },
    safety: { value: 0.71, delta: 0, prev: 0.71 }
  });

  // Hot leads state
  const [hotLeads, setHotLeads] = useState([
    { company: 'Metro Logistics Hub', score: 94, signal: 'Labor Shortage + Expansion', industry: 'Logistics' },
    { company: 'Coastal Hotel Group', score: 91, signal: 'Staffing Crisis', industry: 'Hospitality' },
    { company: 'Fresh Valley Foods', score: 89, signal: '24/7 Operations Need', industry: 'Food Service' },
    { company: 'Regional Health Network', score: 87, signal: 'Safety + Turnover', industry: 'Healthcare' },
    { company: 'Urban Fulfillment Co', score: 85, signal: 'Capacity Expansion', industry: 'Warehousing' }
  ]);

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

  // Fetch all leads - use production API
  useEffect(() => {
    const fetchLeads = async () => {
      try {
        setLoading(true);
        // Use production API that's connected to Supabase
        const res = await fetch('https://ready-2-robot.fly.dev/api/leads');
        const data = await res.json();
        setLeads(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error fetching leads:', err);
        setLeads([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLeads();
    const interval = setInterval(fetchLeads, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  // Calculate lead counts by temperature
  const hotCount = leads.filter(l => l.temperature === 'hot' || l.priority_tier === 'HOT').length;
  const warmCount = leads.filter(l => l.temperature === 'warm' || l.priority_tier === 'WARM').length;
  const coldCount = leads.filter(l => l.temperature === 'cold' || l.priority_tier === 'COLD').length;
  
  // Calculate total signals and find hottest
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
                  <a href="#leads" className="text-neutral-400 hover:text-emerald-400 transition-colors">Browse Leads</a>
                  <a href="#signals" className="text-neutral-400 hover:text-emerald-400 transition-colors">How It Works</a>
                  <Link href="/about" className="text-neutral-400 hover:text-emerald-400 transition-colors">About</Link>
                  <Link href="/roi-calculator" className="text-neutral-400 hover:text-emerald-400 transition-colors">ROI Calculator</Link>
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <Link href="/login" className="text-sm text-neutral-400 hover:text-white transition-colors">Login</Link>
                <Link href="/login" className="text-sm px-4 py-2 border border-emerald-500 text-emerald-400 rounded hover:bg-emerald-950/30 transition-colors">
                  Sign Up Free
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Hero */}
        <div className="max-w-5xl mx-auto px-6 py-10 md:py-12">
          <div className="space-y-6">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-widest">SIGNAL INTELLIGENCE FOR ROBOTICS SALES</div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
              Sell robots to companies <span className="text-emerald-400">actively looking</span> to automate
            </h2>
            <p className="text-lg md:text-xl text-neutral-300 max-w-3xl">
              Stop cold calling. We track 106 companies showing real buying signals — labor shortages, new facilities, executive hires, CapEx budgets. You get warm leads, not dead ends.
            </p>
            
            {/* Signal Intelligence Value */}
            <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-6 space-y-2">
              <div className="text-sm font-semibold text-emerald-400">💡 Why Signals Matter</div>
              <p className="text-base text-neutral-200">
                <span className="text-emerald-400">Signals</span> are the breakthrough. We monitor <span className="text-white font-semibold">{leads.length} companies</span> showing automation buying signals right now — labor shortages, expansion plans, safety issues. These aren't leads "thinking about" robots someday. These are <span className="text-red-400 font-semibold">live opportunities</span> where automation solves urgent problems.
              </p>
            </div>
          </div>
        </div>

        {/* Lead Statistics - Hot Leads Bar (hidden when no data) */}
        {!loading && leads.length > 0 && (
        <div className="max-w-5xl mx-auto px-6 pb-8">
          <div className="border border-neutral-800 rounded-lg py-4 px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="text-2xl md:text-3xl font-bold text-white">{leads.length}</div>
                <div className="text-xs text-neutral-400 mt-1">Total Leads</div>
              </div>
              <div>
                <div className="text-2xl md:text-3xl font-bold text-red-400">{hotCount}</div>
                <div className="text-xs text-neutral-400 mt-1">🔥 Hot</div>
              </div>
              <div>
                <div className="text-2xl md:text-3xl font-bold text-cyan-400">{totalSignals}</div>
                <div className="text-xs text-neutral-400 mt-1">Signals</div>
              </div>
              <div>
                <div className="text-2xl md:text-3xl font-bold text-emerald-400">{warmCount}</div>
                <div className="text-xs text-neutral-400 mt-1">Warm</div>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* CTA - Build Your Pipeline */}
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="border border-emerald-500 rounded-lg px-6 py-6">
            <div className="space-y-6">
              <div className="space-y-3">
                <h2 className="text-2xl md:text-3xl font-bold text-white">
                  Build Your Sales Pipeline
                </h2>
                <p className="text-lg text-neutral-300">
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
                    className="w-full px-4 py-3 bg-black border border-emerald-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full px-6 py-3 bg-transparent border border-emerald-500 text-emerald-400 rounded-lg font-semibold hover:border-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  Build Pipeline →
                </button>
              </form>

              <div className="flex items-center justify-between text-xs text-neutral-500 pt-2 border-t border-neutral-800">
                <span>✓ No signup required</span>
                <span>✓ Instant results</span>
                <span>✓ Free trial</span>
              </div>
            </div>
          </div>
        </div>

        {/* Strategic Snapshot - Top Hot Deals */}
        <div id="leads" className="max-w-5xl mx-auto px-6 py-10 md:py-12 space-y-8">
          <div className="space-y-3">
            <div className="text-xs text-red-400 font-semibold uppercase tracking-widest">🔥 STRATEGIC SNAPSHOT — LIVE SIGNAL DATA</div>
            <h2 className="text-3xl md:text-4xl font-bold text-white">Top Hot Deals Today</h2>
            <p className="text-neutral-400">
              Live companies with urgent automation needs — click any company to see full AI analysis and signal details
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-neutral-400 mt-4">Loading hot deals...</p>
            </div>
          ) : topHotDeals.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-neutral-400">No hot deals available yet. Keep monitoring!</p>
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
                    className="border border-neutral-800 hover:border-red-800/50 rounded-lg p-4 space-y-3 transition-all cursor-pointer hover:bg-red-950/5"
                    style={{
                      animation: `slideIn 0.5s ease-out ${idx * 0.05}s both`
                    }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-1.5">
                        <div className="flex items-center gap-3">
                          <h4 
                            className="text-lg font-semibold text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/analyze?id=${lead.id}`);
                            }}
                          >
                            {lead.company_name}
                          </h4>
                          <span className="px-2 py-0.5 text-xs font-semibold bg-red-950/50 text-red-400 border border-red-800/50 rounded">
                            🔥 HOT
                          </span>
                        </div>
                        <div className="text-sm text-neutral-400">
                          {lead.industry} • {lead.location_city && lead.location_state ? `${lead.location_city}, ${lead.location_state}` : 'Location N/A'}
                        </div>
                        {topSignals.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {topSignals.map((signal, sidx) => (
                              <span key={sidx} className="text-xs text-neutral-500 border border-neutral-800 px-2 py-1 rounded">
                                {signal.signal_type}
                              </span>
                            ))}
                            {(lead.signals?.length || 0) > 2 && (
                              <span className="text-xs text-emerald-400 font-semibold">
                                +{lead.signals.length - 2} more signals
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-right space-y-1">
                        <div className="text-2xl font-bold text-emerald-400">
                          {score.toFixed(0)}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/analyze?id=${lead.id}`);
                          }}
                          className="text-xs text-cyan-400 hover:text-cyan-300 underline"
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
                href="/index_old_dashboard" 
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
                <Link href="/index_old_dashboard" className="text-xs text-cyan-400 hover:text-cyan-300 underline inline-block mt-1">
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
      `}</style>
    </>
  );
}
