import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
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
        {/* Header */}
        <div className="border-b border-neutral-800">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <div className="text-sm text-neutral-400 text-center">
              Signal Intelligence Framework
            </div>
          </div>
        </div>

        {/* Hero */}
        <div className="max-w-6xl mx-auto px-4 py-12 space-y-6">
          <div className="space-y-3">
            <h1 className="text-lg text-white/90 font-medium tracking-wide">ready → ROBOTS</h1>
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">SIGNAL INTELLIGENCE</div>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
              Find buyers <span className="text-emerald-400">before they know</span> they need automation
            </h2>
            <p className="text-xl text-neutral-300 max-w-3xl">
              Signals are real-time indicators of buyer behavior — not stated intent. We observe <span className="text-emerald-400">what companies do</span>, not what they say.
            </p>
          </div>

          {/* Key Insight */}
          <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-6 space-y-2">
            <div className="text-sm font-semibold text-emerald-400">Strategic Insight</div>
            <p className="text-base text-neutral-200">
              Most robotics companies sell <span className="text-red-400">reactively</span> — responding to inbound RFPs when buyers are already comparing 5+ vendors. 
              Our signal intelligence lets you sell <span className="text-emerald-400">proactively</span> — engaging buyers 3-6 months before they enter procurement mode, when you can shape requirements and avoid competitive bidding.
            </p>
          </div>
        </div>

        {/* Lead Statistics - Hot Leads Bar */}
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="border border-emerald-700/50 bg-emerald-950/20 rounded-lg py-4 px-5">
            <div className="flex items-center justify-between gap-6 text-sm flex-wrap">
              <div className="flex items-center gap-2">
                <span className="text-emerald-400 font-semibold">📊 Total Leads:</span>
                <span className="text-white text-lg font-bold">{leads.length}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-red-400 font-semibold">🔥 Hot Leads:</span>
                <span className="text-white text-lg font-bold">{hotCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-cyan-400 font-semibold">⚡ Total Signals:</span>
                <span className="text-white text-lg font-bold">{totalSignals}</span>
              </div>
              <div className="flex items-center gap-2 max-w-md">
                <span className="text-amber-400 font-semibold">🎯 Hottest:</span>
                <span className="text-white text-sm truncate">
                  {hottestSignal ? `${hottestSignal.signal_type} @ ${hottestSignal.company}` : 'Loading...'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* CTA - Build Your Pipeline */}
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="border border-emerald-500 bg-gradient-to-br from-emerald-950/40 to-black rounded-lg px-6 py-8">
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
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-4">
          <div>
            <div className="text-xs text-red-400 font-semibold uppercase tracking-wider mb-1">STRATEGIC SNAPSHOT</div>
            <h2 className="text-2xl font-bold text-white mb-2">Top Hot Deals Today</h2>
            <p className="text-sm text-neutral-400">
              Highest-priority automation buyers detected in the last 24 hours
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

        {/* RASS Scoring Algorithm */}
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">SCORING ENGINE</div>
            <h2 className="text-2xl font-bold">Robot Adoption Signal Score (RASS)</h2>
            <p className="text-neutral-400">
              Our proprietary algorithm combines multiple signal types to predict automation readiness and deal timing.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-4">
            <div className="border border-neutral-800 rounded-lg p-4 space-y-2">
              <div className="text-emerald-400 font-semibold">Labor Pain Score</div>
              <div className="text-xs text-neutral-400">
                Weighted combination of labor scarcity, turnover, cost pressure, and understaffing signals
              </div>
              <div className="text-2xl font-bold text-white">35%</div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-2">
              <div className="text-emerald-400 font-semibold">Expansion Score</div>
              <div className="text-xs text-neutral-400">
                Capacity expansion, new facilities, geographic growth, 24/7 operations needs
              </div>
              <div className="text-2xl font-bold text-white">30%</div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-2">
              <div className="text-emerald-400 font-semibold">Automation Fit</div>
              <div className="text-xs text-neutral-400">
                Industry benchmarks, use case match, technical feasibility, ROI potential
              </div>
              <div className="text-2xl font-bold text-white">25%</div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-2">
              <div className="text-emerald-400 font-semibold">Timing Score</div>
              <div className="text-xs text-neutral-400">
                Budget cycles, executive hires, funding rounds, expansion timelines
              </div>
              <div className="text-2xl font-bold text-white">10%</div>
            </div>
          </div>

          <div className="border border-cyan-800/30 bg-cyan-950/20 rounded-lg p-5 space-y-3">
            <div className="font-semibold text-cyan-400">Signal Velocity Tracking</div>
            <p className="text-sm text-neutral-300">
              We don't just count signals — we track their <span className="text-cyan-400">velocity and sequence</span>. Example progression:
            </p>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-neutral-400">January:</span>
              <span className="text-neutral-300">"Labor shortage" complaints in earnings call</span>
              <span className="text-neutral-600">→</span>
              <span className="text-neutral-400">March:</span>
              <span className="text-neutral-300">Researching automation on LinkedIn</span>
              <span className="text-neutral-600">→</span>
              <span className="text-neutral-400">April:</span>
              <span className="text-emerald-400 font-semibold">Request vendor demos</span>
            </div>
            <p className="text-xs text-cyan-400/80">
              This 3-month signal progression indicates a buyer entering active evaluation mode. Companies showing this pattern convert at 4x the baseline rate.
            </p>
          </div>
        </div>

        {/* The 25 Strongest Buying Signals - Inline Text */}
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">The 25 Strongest Automation Buying Signals</h2>
            <p className="text-neutral-400">
              These signals appear in job listings, earnings calls, LinkedIn posts, and industry forums — they're the strongest predictors of automation adoption within 3-12 months.
            </p>
          </div>

          {/* Inline Text Summaries by Category */}
          <div className="space-y-6">
            {signalCategories.map(category => {
              const colors = getColorClasses(category.color);
              return (
                <div key={category.id} className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className={`h-1 w-12 ${colors.gradient} rounded`}></div>
                    <h3 className={`text-lg font-bold ${colors.cardText}`}>{category.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded border ${colors.cardBorder} ${colors.cardBg} ${colors.cardText}`}>
                      {category.strength}
                    </span>
                  </div>
                  <div className="text-sm text-neutral-300 leading-relaxed">
                    {category.signals.map((signal, idx) => (
                      <span key={idx}>
                        <span className="font-semibold text-white">{signal.name}</span>
                        <span className="text-neutral-500"> ({signal.weight.toFixed(1)})</span>
                        {idx < category.signals.length - 1 ? ' · ' : ''}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Data Sources */}
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">DATA SOURCES</div>
            <h2 className="text-2xl font-bold">Where Signals Come From</h2>
            <p className="text-neutral-400">
              We monitor 140+ public data sources to detect automation buying signals in real-time.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">Job Listings (45 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• Indeed, LinkedIn, Glassdoor, ZipRecruiter</li>
                <li>• Industry-specific job boards</li>
                <li>• Company career pages (direct scraping)</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Labor shortage, automation hires, expansion hiring, executive movement
              </div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">News & Earnings (32 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• Earnings call transcripts (public companies)</li>
                <li>• Industry trade publications</li>
                <li>• Business news (Reuters, Bloomberg)</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Expansion plans, labor pain mentions, CapEx increases, strategic priorities
              </div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">Social & Forums (28 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• LinkedIn posts (executives discussing pain)</li>
                <li>• Reddit (r/logistics, r/manufacturing)</li>
                <li>• Industry-specific forums</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Pain point discussions, vendor research, peer recommendations
              </div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">RFP Marketplaces (12 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• Government RFP databases</li>
                <li>• Private RFP platforms</li>
                <li>• Procurement networks</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Active automation projects, budget allocated, procurement timelines
              </div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">Directories (18 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• Industry association directories</li>
                <li>• Hotel/restaurant directories</li>
                <li>• Logistics network databases</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Company profiles, facility locations, employee counts, equipment
              </div>
            </div>
            <div className="border border-neutral-800 rounded-lg p-4 space-y-3">
              <div className="text-emerald-400 font-semibold">Government (5 sources)</div>
              <ul className="text-sm text-neutral-300 space-y-1">
                <li>• OSHA safety reports</li>
                <li>• SEC filings (expansion, CapEx)</li>
                <li>• Building permits</li>
              </ul>
              <div className="text-xs text-neutral-500">
                Signals: Safety incidents, facility construction, financial health
              </div>
            </div>
          </div>
        </div>

        {/* Why This Matters */}
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">STRATEGIC ADVANTAGE</div>
            <h2 className="text-2xl font-bold">Sell Before Your Competitors Know a Company Is Shopping</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="border border-red-800/30 bg-red-950/20 rounded-lg p-5 space-y-3">
              <div className="text-red-400 font-semibold text-lg">❌ Reactive Selling (Traditional)</div>
              <ul className="text-sm text-neutral-300 space-y-2">
                <li>• Wait for inbound RFP or demo request</li>
                <li>• Buyer already has 3-5 vendors in evaluation</li>
                <li>• Requirements written by competitor or consultant</li>
                <li>• Forced into price-based competition</li>
                <li>• 6-9 month sales cycle, 15-20% win rate</li>
              </ul>
              <div className="text-xs text-red-400/70 italic">
                "By the time they call you, the deal is already half-lost."
              </div>
            </div>
            <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-5 space-y-3">
              <div className="text-emerald-400 font-semibold text-lg">✓ Proactive Selling (Signal-Based)</div>
              <ul className="text-sm text-neutral-300 space-y-2">
                <li>• Engage 3-6 months before procurement mode</li>
                <li>• Only vendor in conversation (no competition)</li>
                <li>• Shape requirements around your solution</li>
                <li>• Build trust through consultative approach</li>
                <li>• 3-4 month sales cycle, 40-50% win rate</li>
              </ul>
              <div className="text-xs text-emerald-400/70 italic">
                "Become their trusted advisor before they start vendor evaluation."
              </div>
            </div>
          </div>
        </div>

        {/* Real Buyer Quotes */}
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">VALIDATION</div>
            <h2 className="text-2xl font-bold">What Buyers Actually Say</h2>
            <p className="text-neutral-400">
              These quotes appear in job listings, earnings calls, and LinkedIn posts — they're the language of automation adoption.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="border border-cyan-800/30 bg-cyan-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-cyan-500 to-cyan-400 rounded"></div>
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wide">Labor Scarcity</span>
              </div>
              <div className="space-y-2 text-sm text-cyan-200/90">
                <p>"We can't find enough workers to cover shifts anymore"</p>
                <p>"Turnover is killing us — constant training cycles"</p>
                <p>"We're constantly understaffed, running skeleton crews"</p>
                <p>"Overtime spending is out of control"</p>
              </div>
              <p className="text-xs text-cyan-400/80 italic">Strongest automation trigger</p>
            </div>
            <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-emerald-500 to-emerald-400 rounded"></div>
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Capacity Pressure</span>
              </div>
              <div className="space-y-2 text-sm text-emerald-200/90">
                <p>"We need to increase throughput without adding headcount"</p>
                <p>"This process is too slow, we're losing competitive edge"</p>
                <p>"We need to run overnight shifts but can't staff them"</p>
                <p>"We need to scale operations for new demand"</p>
              </div>
              <p className="text-xs text-emerald-400/80 italic">Growth-driven automation</p>
            </div>
            <div className="border border-amber-800/30 bg-amber-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-amber-500 to-orange-400 rounded"></div>
                <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">Repetitive Work</span>
              </div>
              <div className="space-y-2 text-sm text-amber-200/90">
                <p>"Our team spends too much time on repetitive tasks"</p>
                <p>"This job has safety risks — heavy lifting, repetition"</p>
                <p>"Manual errors are causing costly rework"</p>
                <p>"We've had injuries doing this repetitive work"</p>
              </div>
              <p className="text-xs text-amber-400/80 italic">Safety + efficiency driver</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-800 mt-12">
          <div className="max-w-6xl mx-auto px-4 py-8 text-center text-sm text-neutral-500">
            <p>Ready → Robots | Signal Intelligence for Robotics Sales</p>
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
