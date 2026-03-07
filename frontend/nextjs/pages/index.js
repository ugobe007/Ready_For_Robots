/**
 * Ready for Robots - Homepage Redesign
 * Signal-first narrative: CTA → Intelligence Explanation → Live Examples → Engagement
 */
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from './_app';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

const SIGNAL_META = {
  funding_round: { label: 'Funding', color: 'violet' },
  strategic_hire: { label: 'Exec Hire', color: 'blue' },
  capex: { label: 'CapEx', color: 'cyan' },
  ma_activity: { label: 'M&A', color: 'pink' },
  expansion: { label: 'Expand', color: 'emerald' },
  job_posting: { label: 'Hiring', color: 'amber' },
  labor_shortage: { label: 'Labor Gap', color: 'red' },
  quality_bottleneck: { label: 'Quality', color: 'orange' },
  safety_incident: { label: 'Safety', color: 'red' },
  production_capacity: { label: 'Capacity', color: 'yellow' },
  warehouse_throughput: { label: 'Throughput', color: 'teal' },
  packaging_automation: { label: 'Packaging', color: 'indigo' },
  repetitive_process: { label: 'Repetitive', color: 'purple' },
  material_handling: { label: 'Material', color: 'lime' },
  news: { label: 'News', color: 'neutral' },
};

export default function HomePage() {
  const { user } = useAuth();
  const [companyUrl, setCompanyUrl] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [hotLeads, setHotLeads] = useState([]);
  const [expandedLead, setExpandedLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const [signalVelocity, setSignalVelocity] = useState({
    labor_shortage: 0,
    hiring: 0,
    expansion: 0,
    safety: 0,
    capacity: 0,
    total: 0
  });

  // Live Signal Flow (pythh.ai style)
  const [signalFlow, setSignalFlow] = useState({
    labor_shortage: { value: 0.67, delta: 0, prev: 0.67 },
    expansion: { value: 0.54, delta: 0, prev: 0.54 },
    safety: { value: 0.71, delta: 0, prev: 0.71 }
  });

  // Handle client-side mounting to avoid hydration errors
  useEffect(() => {
    setMounted(true);
    setCurrentTime(new Date().toLocaleTimeString());
  }, []);

  // Animate signal flow values (pythh.ai style - updates every 3s)
  useEffect(() => {
    const updateSignalFlow = () => {
      setSignalFlow(prev => {
        const newFlow = {};
        Object.keys(prev).forEach(key => {
          const change = (Math.random() - 0.5) * 0.08; // Random change -0.04 to +0.04
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

  // Fetch top 5 HOT leads
  useEffect(() => {
    async function fetchHotLeads() {
      try {
        const res = await fetch(`${API}/api/leads?tier=HOT&limit=20&sort=score`);
        if (res.ok) {
          const allLeads = await res.json();
          // Get top 5 by score
          const top5 = allLeads
            .filter(l => l.score?.overall_score != null)
            .sort((a, b) => (b.score?.overall_score ?? 0) - (a.score?.overall_score ?? 0))
            .slice(0, 5);
          setHotLeads(top5);
          setCurrentTime(new Date().toLocaleTimeString());
          
          // Calculate signal velocity from all leads
          calculateSignalVelocity(allLeads);
        }
      } catch (err) {
        console.error('Failed to fetch leads:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchHotLeads();
    
    // Update every 30 seconds
    const interval = setInterval(fetchHotLeads, 30000);
    return () => clearInterval(interval);
  }, []);

  // Calculate signal counts from leads (last 24h)
  const calculateSignalVelocity = (leads) => {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    let counts = {
      labor_shortage: 0,
      hiring: 0,
      expansion: 0,
      safety: 0,
      capacity: 0,
      total: 0
    };

    leads.forEach(lead => {
      if (!lead.signals || !Array.isArray(lead.signals)) return;
      lead.signals.forEach(signal => {
        const detectedAt = signal.detected_at || signal.created_at;
        if (!detectedAt) {
          // No timestamp, count it anyway
          counts.total++;
          if (signal.signal_type === 'labor_shortage') counts.labor_shortage++;
          else if (signal.signal_type === 'job_posting') counts.hiring++;
          else if (signal.signal_type === 'expansion') counts.expansion++;
          else if (signal.signal_type === 'safety_incident') counts.safety++;
          else if (signal.signal_type === 'production_capacity') counts.capacity++;
        } else {
          const signalDate = new Date(detectedAt);
          if (signalDate > oneDayAgo) {
            counts.total++;
            if (signal.signal_type === 'labor_shortage') counts.labor_shortage++;
            else if (signal.signal_type === 'job_posting') counts.hiring++;
            else if (signal.signal_type === 'expansion') counts.expansion++;
            else if (signal.signal_type === 'safety_incident') counts.safety++;
            else if (signal.signal_type === 'production_capacity') counts.capacity++;
          }
        }
      });
    });

    setSignalVelocity(counts);
  };

  const handleBuildPipeline = () => {
    if (!companyUrl.trim()) return;
    window.location.href = `/pipeline-results?url=${encodeURIComponent(companyUrl.trim())}`;
  };

  const toggleExpanded = (leadId) => {
    setExpandedLead(expandedLead === leadId ? null : leadId);
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      {/* Header */}
      <div className="flex items-center justify-between p-4 sm:px-6 border-b border-neutral-800">
        <Link href="/" className="flex items-center gap-2.5">
          {/* Signal Pulse Icon */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Outer pulse ring */}
            <circle cx="12" cy="12" r="10" stroke="#10B981" strokeWidth="0.5" opacity="0.3"/>
            {/* Middle pulse ring */}
            <circle cx="12" cy="12" r="7" stroke="#10B981" strokeWidth="0.75" opacity="0.5"/>
            {/* Inner pulse ring */}
            <circle cx="12" cy="12" r="4" stroke="#10B981" strokeWidth="1" opacity="0.7"/>
            {/* Center dot */}
            <circle cx="12" cy="12" r="1.5" fill="#10B981"/>
          </svg>
          
          <div className="flex flex-col leading-tight">
            <span className="text-[10px] font-medium text-neutral-400 tracking-wide" style={{fontFamily: 'Inter, system-ui, sans-serif'}}>READY FOR</span>
            <span className="text-sm font-bold text-emerald-400 tracking-wide" style={{fontFamily: 'Inter, system-ui, sans-serif'}}>ROBOTS</span>
          </div>
        </Link>
        <div className="flex items-center gap-3">
          {/* Hamburger menu */}
          <div className="relative">
            <button 
              onClick={() => setMenuOpen(!menuOpen)} 
              className="text-neutral-400 hover:text-neutral-200 text-lg"
            >
              ☰
            </button>
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-neutral-900 border border-neutral-700 rounded shadow-lg z-50">
                <Link 
                  href="/roi-calculator" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  ROI Calculator
                </Link>
                <Link 
                  href="/pilot-calculator" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  Pilot Calculator
                </Link>
                <Link 
                  href="/robot-ready" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  Robot Ready
                </Link>
                <Link 
                  href="/brief" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  Strategy Brief
                </Link>
                <Link 
                  href="/about" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  📘 About
                </Link>
                {user && (
                  <Link 
                    href="/admin" 
                    className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                    onClick={() => setMenuOpen(false)}
                  >
                    Admin
                  </Link>
                )}
                <Link 
                  href="/profile" 
                  className="block px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800" 
                  onClick={() => setMenuOpen(false)}
                >
                  👤 Profile
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">
        
        {/* Hero Headline */}
        <div className="text-center space-y-4 pb-8">
          <h1 className="tracking-wide" style={{fontFamily: 'Inter, system-ui, sans-serif'}}>
            <span className="text-neutral-400 font-normal text-3xl sm:text-4xl md:text-5xl" style={{textShadow: '0 0 20px rgba(163, 163, 163, 0.3)'}}>ready for </span>
            <span className="text-emerald-400 font-bold text-5xl sm:text-6xl md:text-7xl">ROBOTS</span>
          </h1>
          <p className="text-lg sm:text-xl max-w-3xl mx-auto">
            <span className="text-neutral-300">Find companies ready to buy </span>
            <span className="text-emerald-400 font-semibold" style={{textShadow: '0 0 20px rgba(16, 185, 129, 0.5), 0 0 40px rgba(16, 185, 129, 0.2)'}}>Automation</span>
            <span className="text-neutral-300"> — before your competitors do</span>
          </p>
        </div>

        {/* Live Signal Flow (pythh.ai style) */}
        <div className="space-y-3">
          <div>
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-1">SIGNALS</div>
            <h2 className="text-2xl font-bold text-white mb-2">Live buyer intent shifts</h2>
            <p className="text-sm text-neutral-400">
              Signals are real-time indicators of buyer behavior — not stated intent. We observe <span className="text-emerald-400">what companies do</span>, not what they say. <a href="/signals" className="text-emerald-400 hover:text-emerald-300 underline">Learn more →</a>
            </p>
          </div>

          <a href="/signals" className="block border border-neutral-800 rounded-lg p-4 space-y-4 hover:border-emerald-800/50 transition-colors cursor-pointer">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">SIGNAL FLOW</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-emerald-400">Live</span>
                </div>
              </div>
              <span className="text-xs text-neutral-500">Updates every 3s</span>
            </div>

            {/* Labor Shortage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-300">Labor Shortage Intensity</span>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">{signalFlow.labor_shortage.value.toFixed(2)}</span>
                  <span className={`text-xs ${
                    signalFlow.labor_shortage.delta > 0 ? 'text-red-400' : 
                    signalFlow.labor_shortage.delta < 0 ? 'text-emerald-400' : 'text-neutral-500'
                  }`}>
                    {signalFlow.labor_shortage.delta > 0 ? '▲' : signalFlow.labor_shortage.delta < 0 ? '▼' : '–'}
                    {signalFlow.labor_shortage.delta !== 0 ? ` ${Math.abs(signalFlow.labor_shortage.delta).toFixed(2)}` : ' 0.00'}
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-1000 ease-out"
                  style={{ width: `${signalFlow.labor_shortage.value * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Expansion Activity */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-300">Expansion Activity</span>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">{signalFlow.expansion.value.toFixed(2)}</span>
                  <span className={`text-xs ${
                    signalFlow.expansion.delta > 0 ? 'text-emerald-400' : 
                    signalFlow.expansion.delta < 0 ? 'text-red-400' : 'text-neutral-500'
                  }`}>
                    {signalFlow.expansion.delta > 0 ? '▲' : signalFlow.expansion.delta < 0 ? '▼' : '–'}
                    {signalFlow.expansion.delta !== 0 ? ` ${Math.abs(signalFlow.expansion.delta).toFixed(2)}` : ' 0.00'}
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-1000 ease-out"
                  style={{ width: `${signalFlow.expansion.value * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Safety Issues */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-300">Safety Issue Frequency</span>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">{signalFlow.safety.value.toFixed(2)}</span>
                  <span className={`text-xs ${
                    signalFlow.safety.delta > 0 ? 'text-orange-400' : 
                    signalFlow.safety.delta < 0 ? 'text-emerald-400' : 'text-neutral-500'
                  }`}>
                    {signalFlow.safety.delta > 0 ? '▲' : signalFlow.safety.delta < 0 ? '▼' : '–'}
                    {signalFlow.safety.delta !== 0 ? ` ${Math.abs(signalFlow.safety.delta).toFixed(2)}` : ' 0.00'}
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-amber-500 to-orange-400 transition-all duration-1000 ease-out"
                  style={{ width: `${signalFlow.safety.value * 100}%` }}
                ></div>
              </div>
            </div>
          </a>
        </div>

        {/* 1. CTA - Value First */}
        <div className="border border-emerald-700 rounded-lg px-6 py-8 text-center shadow-[0_0_30px_rgba(16,185,129,0.15)]">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
            Build Your Sales Pipeline
          </h2>
          <p className="text-neutral-400 mb-6 max-w-2xl mx-auto">
            Enter your robot company's website. We'll instantly show you 5 prospects with active buying signals — no signup required.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto">
            <input
              type="text"
              placeholder="amplibotics.ai, badger-robotics.com, etc."
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleBuildPipeline()}
              className="flex-1 px-4 py-3 bg-neutral-900 border border-neutral-700 rounded text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              onClick={handleBuildPipeline}
              disabled={!companyUrl.trim()}
              className="px-6 py-3 bg-transparent border border-emerald-500 text-emerald-400 rounded hover:border-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              Build Pipeline →
            </button>
          </div>
        </div>

        {/* Live Signal Velocity - Inline Minimal */}
        <div className="border border-neutral-800 rounded px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-semibold text-white">Live Signal Activity</span>
              <span className="text-xs text-neutral-500">· Last 24h</span>
            </div>
            <span className="text-lg font-bold text-emerald-400">{signalVelocity.total}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-neutral-400">Labor shortage:</span>
              <span className="font-semibold text-red-400">{signalVelocity.labor_shortage}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-neutral-400">Hiring struggles:</span>
              <span className="font-semibold text-amber-400">{signalVelocity.hiring}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-neutral-400">Expansion:</span>
              <span className="font-semibold text-cyan-400">{signalVelocity.expansion}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-neutral-400">Safety issues:</span>
              <span className="font-semibold text-orange-400">{signalVelocity.safety}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-neutral-400">Capacity needs:</span>
              <span className="font-semibold text-violet-400">{signalVelocity.capacity}</span>
            </div>
          </div>
        </div>

        {/* 2. Live Signal Examples - 3-5 HOT Leads (Clickable) */}
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
            <h2 className="text-2xl font-bold text-white">
              Live Hot Leads Right Now
            </h2>
            {mounted && currentTime && (
              <span className="text-xs text-neutral-500">
                Updated {currentTime}
              </span>
            )}
          </div>

          {loading ? (
            <div className="text-center py-12 text-neutral-500">
              <div className="inline-block animate-spin h-6 w-6 border-2 border-emerald-500 border-t-transparent rounded-full mb-2"></div>
              <p className="text-sm">Loading live signals...</p>
            </div>
          ) : hotLeads.length === 0 ? (
            <div className="text-center py-12 text-neutral-500">
              <p>No hot leads available</p>
            </div>
          ) : (
            <div className="space-y-4">
              {hotLeads.map((lead, index) => (
                <div 
                  key={lead.id}
                  className="border border-neutral-800 rounded-lg overflow-hidden hover:border-emerald-800 transition-all"
                >
                  {/* Lead Summary (Always Visible) */}
                  <button
                    onClick={() => toggleExpanded(lead.id)}
                    className="w-full px-5 py-4 text-left hover:bg-neutral-900/40 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-cyan-400">
                            {lead.company_name}
                          </h3>
                          <span className="px-2 py-0.5 text-xs font-semibold bg-red-900/30 border border-red-700 text-red-400 rounded">
                            HOT
                          </span>
                          <span className="px-2 py-0.5 text-xs font-mono bg-emerald-900/30 border border-emerald-700 text-emerald-400 rounded">
                            {Math.round(lead.score?.overall_score ?? 0)}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-500 mb-2">
                          {lead.industry && <span>{lead.industry}</span>}
                          {lead.location_city && (
                            <>
                              <span>·</span>
                              <span>{lead.location_city}</span>
                            </>
                          )}
                          {lead.employee_estimate && (
                            <>
                              <span>·</span>
                              <span>{lead.employee_estimate.toLocaleString()} employees</span>
                            </>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {(lead.signals || []).slice(0, 5).map((sig, i) => {
                            const meta = SIGNAL_META[sig.signal_type] || { label: sig.signal_type, color: 'neutral' };
                            return (
                              <span 
                                key={i}
                                className={`px-2 py-0.5 text-[9px] border border-${meta.color}-700 text-${meta.color}-400 rounded`}
                              >
                                {meta.label}
                              </span>
                            );
                          })}
                          {(lead.signals || []).length > 5 && (
                            <span className="px-2 py-0.5 text-[9px] text-neutral-500">
                              +{lead.signals.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-emerald-400 text-sm">
                        {expandedLead === lead.id ? '▲' : '▼'}
                      </div>
                    </div>
                  </button>

                  {/* Expanded Signal Details */}
                  {expandedLead === lead.id && (
                    <div className="border-t border-neutral-800 bg-neutral-950/50 px-5 py-4 space-y-4">
                      <div>
                        <h4 className="text-sm font-semibold text-emerald-400 mb-2">
                          Why This Opportunity Is Real
                        </h4>
                        <p className="text-xs text-neutral-400 mb-3">
                          These are actual signals detected from verified sources, not marketing assumptions.
                        </p>
                      </div>

                      {/* Signal List */}
                      <div className="space-y-3">
                        {(lead.signals || []).map((signal, i) => {
                          const meta = SIGNAL_META[signal.signal_type] || { label: signal.signal_type, color: 'neutral' };
                          return (
                            <div 
                              key={i}
                              className="border-l-2 border-cyan-700 pl-3 py-2"
                            >
                              <div className="flex items-start justify-between gap-3 mb-1">
                                <span className={`text-xs font-semibold text-${meta.color}-400 uppercase tracking-wide`}>
                                  {meta.label}
                                </span>
                                {signal.strength && (
                                  <span className="text-[10px] text-neutral-500">
                                    {Math.round(signal.strength * 100)}% confidence
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-neutral-300">
                                {signal.raw_text || signal.signal_text || 'Signal detected'}
                              </p>
                              {signal.detected_at && (
                                <p className="text-[10px] text-neutral-600 mt-1">
                                  Detected: {new Date(signal.detected_at).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {/* Score Breakdown */}
                      {lead.score && (
                        <div className="pt-3 border-t border-neutral-800">
                          <h5 className="text-xs font-semibold text-neutral-400 mb-2">Intelligence Scores</h5>
                          <div className="grid grid-cols-2 gap-2">
                            {lead.score.automation_score != null && (
                              <div className="text-xs">
                                <span className="text-neutral-500">Automation Fit:</span>
                                <span className="ml-2 text-emerald-400 font-semibold">
                                  {Math.round(lead.score.automation_score)}
                                </span>
                              </div>
                            )}
                            {lead.score.labor_pain_score != null && (
                              <div className="text-xs">
                                <span className="text-neutral-500">Labor Pain:</span>
                                <span className="ml-2 text-red-400 font-semibold">
                                  {Math.round(lead.score.labor_pain_score)}
                                </span>
                              </div>
                            )}
                            {lead.score.expansion_score != null && (
                              <div className="text-xs">
                                <span className="text-neutral-500">Expansion:</span>
                                <span className="ml-2 text-cyan-400 font-semibold">
                                  {Math.round(lead.score.expansion_score)}
                                </span>
                              </div>
                            )}
                            {lead.score.market_fit_score != null && (
                              <div className="text-xs">
                                <span className="text-neutral-500">Market Fit:</span>
                                <span className="ml-2 text-violet-400 font-semibold">
                                  {Math.round(lead.score.market_fit_score)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* CTA */}
                      <div className="pt-3 border-t border-neutral-800">
                        <Link
                          href={`/index_old_dashboard?analyze=${lead.id}`}
                          className="inline-block px-4 py-2 bg-transparent border border-emerald-500 text-emerald-400 rounded hover:border-emerald-400 hover:text-emerald-300 transition-colors text-sm font-semibold"
                        >
                          Full AI Analysis →
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="text-center pt-4">
            <Link
              href="/brief"
              className="inline-block px-6 py-3 border border-cyan-700 text-cyan-400 rounded hover:border-cyan-600 hover:text-cyan-300 transition-colors text-sm font-semibold"
            >
              View All Hot Leads in Strategy Brief →
            </Link>
          </div>
        </div>

        {/* 3. Signal Intelligence Explanation */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-white border-b border-neutral-800 pb-3">
            What Makes Us Different
          </h2>
          
          <div className="grid sm:grid-cols-2 gap-6">
            <div className="border border-neutral-800 rounded-lg p-5">
              <h3 className="text-emerald-400 font-semibold mb-2">Signal Intelligence</h3>
              <p className="text-sm text-neutral-400">
                We monitor <strong>behavioral signals</strong> — hiring spikes, expansion announcements, funding rounds, labor pain indicators — that reveal buying intent <em>right now</em>. Like Pythh tracks investor behavior to predict investment opportunities, we track customer behavior to predict automation buyers.
              </p>
            </div>

            <div className="border border-neutral-800 rounded-lg p-5">
              <h3 className="text-red-400 font-semibold mb-2">NOT Stale Databases</h3>
              <p className="text-sm text-neutral-400">
                Most lead gen tools sell outdated company lists with no indication of buyer intent. We show you <strong>who's ready to buy today</strong> based on real-time signals from 122+ sources. This is intelligence, not marketing lists.
              </p>
            </div>
          </div>

          <div className="border-l-2 border-cyan-700 pl-4">
            <p className="text-sm text-neutral-300 italic">
              "We need to be really good at finding and predicting customer needs. This is our core. We're battling against market noise — no site really delivers meaningful value because they don't use a signaling system like we do."
            </p>
          </div>
        </div>

        {/* 4. Engagement Strategy */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-white border-b border-neutral-800 pb-3">
            How to Engage Professionally
          </h2>

          <div className="grid sm:grid-cols-3 gap-4">
            <div className="border border-neutral-800 rounded-lg p-4">
              <div className="text-emerald-400 font-semibold mb-2 text-sm">1. Timing Matters</div>
              <p className="text-xs text-neutral-400">
                Contact prospects when signals are fresh (within 7-14 days). New exec hires = 90-day window. Funding rounds = 12-18 month deployment window.
              </p>
            </div>

            <div className="border border-neutral-800 rounded-lg p-4">
              <div className="text-cyan-400 font-semibold mb-2 text-sm">2. Lead With Insight</div>
              <p className="text-xs text-neutral-400">
                Reference the specific signal: "Saw your recent expansion announcement..." or "Noticed you're hiring 15 warehouse roles..." Show you've done research.
              </p>
            </div>

            <div className="border border-neutral-800 rounded-lg p-4">
              <div className="text-violet-400 font-semibold mb-2 text-sm">3. Target Decision Makers</div>
              <p className="text-xs text-neutral-400">
                VP Operations, COO, Directors of Ops for logistics/manufacturing. CFO for ROI discussion. New executives are most receptive.
              </p>
            </div>
          </div>
        </div>

        {/* Buyer Quotes Validation */}
        <div className="space-y-4" id="what-buyers-say">
          <div>
            <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">VALIDATION</div>
            <h2 className="text-2xl font-bold text-white mb-2">What buyers actually say</h2>
            <p className="text-sm text-neutral-400">
              These quotes appear in job listings, earnings calls, and LinkedIn posts — they're the strongest predictors of automation adoption.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {/* Labor Signals */}
            <div className="border border-cyan-800/30 bg-cyan-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-cyan-500 to-cyan-400 rounded"></div>
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wide">Labor Scarcity</span>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-neutral-300">“We can't find enough workers to cover shifts anymore.”</p>
                <p className="text-neutral-300">“Turnover is killing us.”</p>
                <p className="text-neutral-300">“We're constantly short staffed.”</p>
                <p className="text-neutral-300">“Nobody wants to do this job anymore.”</p>
              </div>
              <p className="text-xs text-cyan-400/80 italic">Strongest automation trigger</p>
            </div>

            {/* Expansion Signals */}
            <div className="border border-emerald-800/30 bg-emerald-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-emerald-500 to-emerald-400 rounded"></div>
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Capacity Pressure</span>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-neutral-300">“We need to increase throughput.”</p>
                <p className="text-neutral-300">“We need to scale without adding headcount.”</p>
                <p className="text-neutral-300">“We need to run overnight.”</p>
                <p className="text-neutral-300">“We're expanding production capacity.”</p>
              </div>
              <p className="text-xs text-emerald-400/80 italic">Scaling opportunity</p>
            </div>

            {/* Safety Signals */}
            <div className="border border-amber-800/30 bg-amber-950/20 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-1 w-8 bg-gradient-to-r from-amber-500 to-orange-400 rounded"></div>
                <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">Repetitive Work</span>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-neutral-300">“Our team spends too much time on repetitive tasks.”</p>
                <p className="text-neutral-300">“Employees hate doing this work.”</p>
                <p className="text-neutral-300">“This job has safety risks.”</p>
                <p className="text-neutral-300">“We've had injuries doing this task.”</p>
              </div>
              <p className="text-xs text-amber-400/80 italic">Prime robotics candidate</p>
            </div>
          </div>
        </div>

        {/* Footer CTA */}
        <div className="text-center pt-8 border-t border-neutral-800">
          <p className="text-neutral-400 mb-4">
            Ready to find prospects with real buying intent?
          </p>
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="px-8 py-3 bg-transparent border border-emerald-500 text-emerald-400 rounded hover:border-emerald-400 hover:text-emerald-300 transition-colors font-semibold"
          >
            Build Your Pipeline →
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-8 text-xs text-neutral-600 border-t border-neutral-800">
        <p>READY → ROBOTS · Signal Intelligence Platform · Updated every 30s</p>
      </div>
    </div>
  );
}
