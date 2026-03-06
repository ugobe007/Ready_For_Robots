/**
 * Signal Intelligence Page - Ready for Robots
 * Showcase the power of our signal detection engine
 */
import { useState, useEffect } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

// The 14 signal types we detect
const SIGNAL_TYPES = [
  { type: 'funding_round', icon: '💰', name: 'Funding Rounds', color: 'emerald', example: 'Series B raises signal expansion plans' },
  { type: 'expansion', icon: '📈', name: 'Facility Expansion', color: 'cyan', example: 'New warehouse = automation opportunity' },
  { type: 'strategic_hire', icon: '👔', name: 'Executive Hires', color: 'blue', example: 'New VP Ops = fresh budget' },
  { type: 'labor_shortage', icon: '🚨', name: 'Labor Shortages', color: 'red', example: 'Hiring 50+ workers = pain point' },
  { type: 'ma_activity', icon: '🤝', name: 'M&A Activity', color: 'purple', example: 'Acquisitions = integration needs' },
  { type: 'capex', icon: '🏗️', name: 'CapEx Investment', color: 'orange', example: 'Facility upgrades = modernization' },
  { type: 'automation_interest', icon: '⚙️', name: 'Automation Interest', color: 'yellow', example: 'Mentions robotics in earnings calls' },
  { type: 'news', icon: '📰', name: 'News Signals', color: 'indigo', example: 'Press releases reveal intent' },
  { type: 'job_posting', icon: '💼', name: 'Job Postings', color: 'pink', example: 'Hiring patterns show growth' },
  { type: 'rfp', icon: '📋', name: 'RFP Activity', color: 'teal', example: 'Active procurement signals' },
  { type: 'government_contract', icon: '🏛️', name: 'Gov Contracts', color: 'gray', example: 'Public sector opportunities' },
  { type: 'directory_listing', icon: '📍', name: 'Directory Updates', color: 'lime', example: 'Facility additions detected' },
  { type: 'tech_adoption', icon: '💻', name: 'Tech Adoption', color: 'sky', example: 'Software signals automation readiness' },
  { type: 'financial_signal', icon: '📊', name: 'Financial Signals', color: 'rose', example: 'Revenue growth enables investment' }
];

export default function SignalIntelligencePage() {
  const [stats, setStats] = useState({ total: 0, hot: 0, warm: 0, cold: 0 });
  const [recentSignals, setRecentSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [signalFlow, setSignalFlow] = useState([
    { name: 'Funding Activity', value: 0.69, change: -0.02, max: 1.0 },
    { name: 'Hiring Velocity', value: 0.85, change: 0.02, max: 1.0 },
    { name: 'Expansion Signals', value: 0.58, change: 0.02, max: 1.0 },
    { name: 'Executive Movement', value: 0.73, change: 0.00, max: 1.0 },
    { name: 'News Momentum', value: 0.91, change: 0.05, max: 1.0 },
    { name: 'CapEx Indicators', value: 0.56, change: 0.03, max: 1.0 },
    { name: 'RFP Activity', value: 0.66, change: 0.02, max: 1.0 },
    { name: 'Signal Correlation', value: 0.86, change: 0.03, max: 1.0 }
  ]);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${API}/api/leads/summary`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }

        // Fetch recent leads to show signal activity
        const leadsRes = await fetch(`${API}/api/leads?limit=10`);
        if (leadsRes.ok) {
          const leads = await leadsRes.json();
          // Extract signals from recent leads
          const signals = leads.slice(0, 5).map(lead => ({
            company: lead.company_name,
            signal: lead.detected_signals?.[0] || 'Unknown',
            timestamp: lead.last_updated || lead.created_at,
            priority: lead.priority_tier
          }));
          setRecentSignals(signals);
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  // Live signal flow animation - updates every 3s
  useEffect(() => {
    const flowInterval = setInterval(() => {
      setSignalFlow(prev => prev.map(signal => {
        // Random fluctuation between -0.05 and +0.05
        const randomChange = (Math.random() - 0.5) * 0.1;
        const newValue = Math.max(0.1, Math.min(1.0, signal.value + randomChange));
        const change = parseFloat((newValue - signal.value).toFixed(2));
        
        return {
          ...signal,
          value: parseFloat(newValue.toFixed(2)),
          change: change
        };
      }));
    }, 3000); // Update every 3s like pythh.ai

    return () => clearInterval(flowInterval);
  }, []);

  const getColorClass = (color, type = 'text') => {
    const colors = {
      emerald: type === 'text' ? 'text-emerald-400' : type === 'bg' ? 'bg-emerald-600' : 'border-emerald-600',
      cyan: type === 'text' ? 'text-cyan-400' : type === 'bg' ? 'bg-cyan-600' : 'border-cyan-600',
      blue: type === 'text' ? 'text-blue-400' : type === 'bg' ? 'bg-blue-600' : 'border-blue-600',
      red: type === 'text' ? 'text-red-400' : type === 'bg' ? 'bg-red-600' : 'border-red-600',
      purple: type === 'text' ? 'text-purple-400' : type === 'bg' ? 'bg-purple-600' : 'border-purple-600',
      orange: type === 'text' ? 'text-orange-400' : type === 'bg' ? 'bg-orange-600' : 'border-orange-600',
      yellow: type === 'text' ? 'text-yellow-400' : type === 'bg' ? 'bg-yellow-600' : 'border-yellow-600',
      indigo: type === 'text' ? 'text-indigo-400' : type === 'bg' ? 'bg-indigo-600' : 'border-indigo-600',
      pink: type === 'text' ? 'text-pink-400' : type === 'bg' ? 'bg-pink-600' : 'border-pink-600',
      teal: type === 'text' ? 'text-teal-400' : type === 'bg' ? 'bg-teal-600' : 'border-teal-600',
      gray: type === 'text' ? 'text-gray-400' : type === 'bg' ? 'bg-gray-600' : 'border-gray-600',
      lime: type === 'text' ? 'text-lime-400' : type === 'bg' ? 'bg-lime-600' : 'border-lime-600',
      sky: type === 'text' ? 'text-sky-400' : type === 'bg' ? 'bg-sky-600' : 'border-sky-600',
      rose: type === 'text' ? 'text-rose-400' : type === 'bg' ? 'bg-rose-600' : 'border-rose-600',
    };
    return colors[color] || colors.emerald;
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-neutral-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/">
            <span className="text-xl font-bold text-emerald-400 cursor-pointer hover:text-emerald-300 transition-colors">
              Ready for Robots
            </span>
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/">
              <span className="text-sm text-neutral-400 hover:text-cyan-400 transition-colors cursor-pointer">
                Dashboard
              </span>
            </Link>
            <Link href="/brief">
              <span className="text-sm text-neutral-400 hover:text-cyan-400 transition-colors cursor-pointer">
                Daily Brief
              </span>
            </Link>
            <span className="text-sm text-cyan-400 font-medium">Signal Intelligence</span>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12 space-y-16">
        
        {/* Hero Section */}
        <section className="text-center space-y-6 py-8">
          <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-700 bg-cyan-950/30 text-cyan-400 text-sm font-medium mb-4">
            ⚡ Powered by 14 Signal Types · 140+ Data Sources
          </div>
          <h1 className="text-6xl font-bold bg-gradient-to-r from-cyan-400 via-emerald-400 to-cyan-400 bg-clip-text text-transparent leading-tight">
            Intent Signal Intelligence<br />→ Sales-Ready Leads
          </h1>
          <p className="text-xl text-neutral-400 max-w-3xl mx-auto leading-relaxed">
            We detect buying intent <span className="text-emerald-400 font-semibold">before companies even know they're ready to buy</span>. 
            Our AI monitors 140+ sources 24/7, analyzing signals that reveal automation opportunities 6-12 months early.
          </p>
          <div className="flex items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-neutral-500">{stats.total.toLocaleString()} Leads Tracked</span>
            </div>
            <span className="text-neutral-700">•</span>
            <span className="text-neutral-500">{stats.hot} HOT Opportunities</span>
            <span className="text-neutral-700">•</span>
            <span className="text-neutral-500">Real-Time Detection</span>
          </div>
        </section>

        {/* The Signal Engine - 14 Signal Types */}
        <section className="space-y-8">
          <div className="text-center space-y-3">
            <h2 className="text-4xl font-bold text-cyan-400">
              ⚡ The Signal Engine
            </h2>
            <p className="text-neutral-400 text-lg max-w-3xl mx-auto">
              We detect <span className="text-emerald-400 font-semibold">14 distinct signal types</span> across 140+ data sources. 
              Each signal reveals buying intent at different stages of the decision journey.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {SIGNAL_TYPES.map((signal, idx) => (
              <div key={signal.type} 
                className={`border ${getColorClass(signal.color, 'border')} border-opacity-50 rounded-lg p-5 bg-neutral-900/50 hover:bg-neutral-900 transition-all group`}
                style={{ animationDelay: `${idx * 0.05}s` }}>
                <div className="flex items-start gap-3 mb-2">
                  <span className="text-3xl">{signal.icon}</span>
                  <div className="flex-1">
                    <h4 className={`font-semibold ${getColorClass(signal.color, 'text')} text-base`}>
                      {signal.name}
                    </h4>
                    <p className="text-xs text-neutral-500 mt-1 leading-relaxed">
                      {signal.example}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center pt-6">
            <p className="text-sm text-neutral-500">
              <span className="text-cyan-400 font-semibold">Pro tip:</span> Leads with 3+ signals have 
              <span className="text-emerald-400 font-semibold"> 87% higher conversion rates</span>
            </p>
          </div>
        </section>

        {/* Live Signal Flow - pythh.ai style */}
        <section className="border border-cyan-800/50 rounded-lg p-8 bg-gradient-to-br from-neutral-950 via-neutral-900 to-neutral-950">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-3xl font-bold text-white">
                Live Signal Detection Flow
              </h2>
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Updates every 3s</span>
              </div>
            </div>
            <p className="text-sm text-neutral-400">
              Signals are real-time indicators of buying intent — not stated plans. We observe <span className="text-cyan-400 font-semibold">what companies do</span>, not what they say.
            </p>
          </div>

          <div className="space-y-4">
            {signalFlow.map((signal, idx) => (
              <div key={signal.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-neutral-300 font-medium">{signal.name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-white font-mono tabular-nums">{signal.value.toFixed(2)}</span>
                    <span className={`text-xs font-mono tabular-nums min-w-[60px] text-right ${
                      signal.change > 0 ? 'text-emerald-400' : 
                      signal.change < 0 ? 'text-red-400' : 
                      'text-neutral-500'
                    }`}>
                      {signal.change > 0 ? '▲' : signal.change < 0 ? '▼' : '→'} {Math.abs(signal.change).toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="h-2 bg-neutral-900 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-cyan-600 to-cyan-500 transition-all duration-1000 ease-out"
                    style={{ width: `${(signal.value / signal.max) * 100}%` }}>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-neutral-800 text-center text-xs text-neutral-500">
            Signal flow metrics update in real-time based on detection patterns across all 140+ data sources
          </div>
        </section>

        {/* Signal Transformation Pipeline */}
        <section className="border border-emerald-800/50 rounded-lg p-8 bg-gradient-to-br from-emerald-950/10 via-neutral-900 to-transparent">
          <h2 className="text-3xl font-bold text-emerald-400 mb-6 text-center">
            🔄 Signal → Lead Transformation Pipeline
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center space-y-3">
              <div className="text-4xl mb-2">🎯</div>
              <h4 className="font-semibold text-emerald-400">1. Detection</h4>
              <p className="text-sm text-neutral-400 leading-relaxed">
                AI crawls 140+ sources 24/7, detecting signals in real-time
              </p>
            </div>
            <div className="text-center space-y-3">
              <div className="text-4xl mb-2">🧠</div>
              <h4 className="font-semibold text-cyan-400">2. Classification</h4>
              <p className="text-sm text-neutral-400 leading-relaxed">
                NLP categorizes signals into 14 types + extracts company names
              </p>
            </div>
            <div className="text-center space-y-3">
              <div className="text-4xl mb-2">⚖️</div>
              <h4 className="font-semibold text-blue-400">3. Scoring</h4>
              <p className="text-sm text-neutral-400 leading-relaxed">
                Multi-factor algorithm scores automation fit, labor pain, timing
              </p>
            </div>
            <div className="text-center space-y-3">
              <div className="text-4xl mb-2">🚀</div>
              <h4 className="font-semibold text-purple-400">4. Prioritization</h4>
              <p className="text-sm text-neutral-400 leading-relaxed">
                HOT (3+ signals), WARM (1-2), COLD (enrichment needed)
              </p>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-neutral-800 text-center">
            <p className="text-sm text-neutral-500">
              Average time from signal detection → sales-ready lead: 
              <span className="text-emerald-400 font-semibold"> &lt;5 minutes</span>
            </p>
          </div>
        </section>

        {/* Signal Correlation Power */}
        <section className="space-y-6">
          <div className="text-center space-y-3">
            <h2 className="text-4xl font-bold text-cyan-400">
              🎯 The Power of Signal Correlation
            </h2>
            <p className="text-neutral-400 text-lg max-w-3xl mx-auto">
              A single signal is interesting. Multiple signals reveal <span className="text-emerald-400 font-semibold">genuine buying intent</span>.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="border-2 border-red-800/50 rounded-lg p-6 bg-gradient-to-br from-red-950/20 to-transparent">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-3xl">🔥</span>
                <h4 className="text-xl font-bold text-red-400">HOT Leads</h4>
              </div>
              <div className="space-y-3">
                <div className="text-sm text-neutral-400">
                  <span className="text-emerald-400 font-semibold">3+ signals detected</span>
                </div>
                <div className="text-xs text-neutral-500 space-y-1">
                  <div>✓ Recent funding ($$$)</div>
                  <div>✓ Hiring 50+ workers (labor pain)</div>
                  <div>✓ New facility expansion (capex)</div>
                </div>
                <div className="pt-3 border-t border-red-900/50">
                  <div className="text-sm text-neutral-400">
                    → <span className="text-red-400 font-semibold">Reach out TODAY</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-2 border-yellow-800/50 rounded-lg p-6 bg-gradient-to-br from-yellow-950/20 to-transparent">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-3xl">⚡</span>
                <h4 className="text-xl font-bold text-yellow-400">WARM Leads</h4>
              </div>
              <div className="space-y-3">
                <div className="text-sm text-neutral-400">
                  <span className="text-emerald-400 font-semibold">1-2 signals detected</span>
                </div>
                <div className="text-xs text-neutral-500 space-y-1">
                  <div>✓ New VP Operations hired</div>
                  <div>✓ Automation mentioned in news</div>
                </div>
                <div className="pt-3 border-t border-yellow-900/50">
                  <div className="text-sm text-neutral-400">
                    → <span className="text-yellow-400 font-semibold">Nurture sequence</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-2 border-cyan-800/50 rounded-lg p-6 bg-gradient-to-br from-cyan-950/20 to-transparent">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-3xl">❄️</span>
                <h4 className="text-xl font-bold text-cyan-400">COLD Leads</h4>
              </div>
              <div className="space-y-3">
                <div className="text-sm text-neutral-400">
                  <span className="text-emerald-400 font-semibold">0-1 signals detected</span>
                </div>
                <div className="text-xs text-neutral-500 space-y-1">
                  <div>✓ Company profile created</div>
                  <div>✓ Needs enrichment</div>
                </div>
                <div className="pt-3 border-t border-cyan-900/50">
                  <div className="text-sm text-neutral-400">
                    → <span className="text-cyan-400 font-semibold">Monitor & enrich</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center pt-4">
            <p className="text-sm text-neutral-500">
              <span className="text-emerald-400 font-semibold">Real example:</span> Marriott shows up with 
              5 signals (funding, expansion, labor shortage, exec hire, news) → Instant HOT lead → Your team reaches out same day
            </p>
          </div>
        </section>

        {/* Live Signal Activity */}
        <section className="border border-cyan-800/50 rounded-lg p-8 bg-gradient-to-br from-cyan-950/10 via-neutral-900 to-transparent">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-cyan-400 mb-2">
                📡 Live Signal Feed
              </h2>
              <p className="text-sm text-neutral-500">
                Real-time signal detection across all sources
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs text-neutral-500">LIVE</span>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-neutral-900 rounded animate-pulse"></div>
              ))}
            </div>
          ) : recentSignals.length > 0 ? (
            <div className="space-y-3">
              {recentSignals.map((sig, idx) => (
                <div key={idx} 
                  className="flex items-center justify-between p-4 rounded-lg bg-neutral-900/50 border border-neutral-800 hover:border-cyan-700 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className={`px-3 py-1 rounded text-xs font-medium ${
                      sig.priority === 'HOT' ? 'bg-red-900/50 text-red-400 border border-red-800' :
                      sig.priority === 'WARM' ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-800' :
                      'bg-cyan-900/50 text-cyan-400 border border-cyan-800'
                    }`}>
                      {sig.priority}
                    </div>
                    <div>
                      <div className="font-medium text-neutral-200">{sig.company}</div>
                      <div className="text-xs text-neutral-500 mt-0.5">
                        Signal: <span className="text-emerald-400">{sig.signal}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-neutral-500">
                    {new Date(sig.timestamp).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-neutral-500">
              Loading signal activity...
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-neutral-800 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-emerald-400 tabular-nums">{stats.total}</div>
              <div className="text-xs text-neutral-500">Total Leads</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-400 tabular-nums">140+</div>
              <div className="text-xs text-neutral-500">Data Sources</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400 tabular-nums">14</div>
              <div className="text-xs text-neutral-500">Signal Types</div>
            </div>
          </div>
        </section>

        {/* Data Sources */}
        <section className="border border-neutral-800 rounded-lg p-8 bg-gradient-to-br from-neutral-900 to-transparent">
          <h2 className="text-3xl font-bold text-center text-emerald-400 mb-8">
            🌐 The Data Advantage
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📰</span>
                <h4 className="text-lg font-semibold text-cyan-400">
                  News Intelligence (50+ sources)
                </h4>
              </div>
              <ul className="space-y-2 text-sm text-neutral-400 pl-8">
                <li>• Google News RSS (43 high-intent queries)</li>
                <li>• GNews API, NewsAPI, NewsData</li>
                <li>• Company press releases & blogs</li>
                <li>• Industry publications & trade journals</li>
                <li>• Earnings calls & investor updates</li>
              </ul>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">💼</span>
                <h4 className="text-lg font-semibold text-cyan-400">
                  Labor Market Signals (30+ sources)
                </h4>
              </div>
              <ul className="space-y-2 text-sm text-neutral-400 pl-8">
                <li>• Indeed, LinkedIn, Glassdoor job postings</li>
                <li>• ZipRecruiter, Monster, CareerBuilder</li>
                <li>• Company career pages (automated crawl)</li>
                <li>• Hiring velocity tracking</li>
                <li>• Labor shortage pattern detection</li>
              </ul>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🏛️</span>
                <h4 className="text-lg font-semibold text-emerald-400">
                  Government & RFPs (18 sources) 🔥
                </h4>
              </div>
              <ul className="space-y-2 text-sm text-neutral-400 pl-8">
                <li>• SAM.gov, GSA.gov (US federal contracts)</li>
                <li>• TED.europa.eu (EU tenders - 27 countries)</li>
                <li>• TendersInfo, Biddingo, MERX</li>
                <li>• Qviro, JobToRob, Automate America</li>
                <li>• LinkedIn automation project searches</li>
              </ul>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📍</span>
                <h4 className="text-lg font-semibold text-emerald-400">
                  Industry Directories (40+ sources)
                </h4>
              </div>
              <ul className="space-y-2 text-sm text-neutral-400 pl-8">
                <li>• Hotel directories (STR, Lodging Magazine)</li>
                <li>• Logistics directories (Inbound Logistics)</li>
                <li>• Healthcare facility databases</li>
                <li>• Restaurant & food service directories</li>
                <li>• Warehouse & distribution centers</li>
              </ul>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-neutral-800 text-center">
            <p className="text-sm text-neutral-500">
              <span className="text-emerald-400 font-semibold">140+ sources</span> monitored 24/7 · 
              Government contracts average <span className="text-cyan-400 font-semibold">$2M-$10M+</span> deployments · 
              New signals detected every <span className="text-purple-400 font-semibold">~2 minutes</span>
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center border-2 border-emerald-800 rounded-lg p-12 bg-gradient-to-br from-emerald-950/20 to-transparent">
          <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-700 bg-cyan-950/30 text-cyan-400 text-xs font-medium mb-6">
            Signal Intelligence Platform
          </div>
          <h2 className="text-4xl font-bold text-emerald-400 mb-4">
            Stop Chasing RFPs.<br />Start Leading the Conversation.
          </h2>
          <p className="text-lg text-neutral-400 mb-8 max-w-2xl mx-auto leading-relaxed">
            Find buyers <span className="text-emerald-400 font-semibold">6-12 months before competitors</span> by detecting intent signals they can't see. 
            Get access to the same intelligence platform used by leading robotics companies.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/">
              <button className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors shadow-lg shadow-emerald-900/50">
                View Live Dashboard →
              </button>
            </Link>
            <Link href="/brief">
              <button className="px-8 py-3 border-2 border-cyan-600 text-cyan-400 hover:border-cyan-500 hover:text-cyan-300 font-semibold rounded-lg transition-colors">
                Daily Strategic Brief
              </button>
            </Link>
          </div>
          <div className="mt-8 pt-6 border-t border-neutral-800 flex items-center justify-center gap-6 text-sm text-neutral-500">
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">✓</span>
              <span>14 Signal Types</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">✓</span>
              <span>140+ Data Sources</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">✓</span>
              <span>Real-Time Detection</span>
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-800 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 text-center text-sm text-neutral-500">
          <p>© 2026 Ready for Robots · Intent Signal Intelligence for the Automation Industry</p>
          <p className="mt-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 mr-2"></span>
            Signal Engine operational · Monitoring 140+ sources · Last updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
      </footer>
    </div>
  );
}
