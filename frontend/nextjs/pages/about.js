/**
 * About Page - Ready for Robots
 * Platform overview with live industry heatmap
 */
import { useState, useEffect } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

export default function AboutPage() {
  const [stats, setStats] = useState({ total: 0, hot: 0, warm: 0, cold: 0 });
  const [industries, setIndustries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${API}/api/leads/summary`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }

        // Fetch leads for industry breakdown
        const leadsRes = await fetch(`${API}/api/leads`);
        if (leadsRes.ok) {
          const leads = await leadsRes.json();
          
          // Calculate industry distribution
          const industryMap = {};
          leads.forEach(lead => {
            const ind = lead.industry || 'Unknown';
            if (!industryMap[ind]) {
              industryMap[ind] = { name: ind, count: 0, hot: 0 };
            }
            industryMap[ind].count++;
            if (lead.priority_tier === 'HOT') {
              industryMap[ind].hot++;
            }
          });

          const sorted = Object.values(industryMap)
            .sort((a, b) => b.count - a.count)
            .slice(0, 8);
          
          setIndustries(sorted);
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

  const maxCount = industries[0]?.count || 1;

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
            <span className="text-sm text-cyan-400 font-medium">About</span>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-16">
        
        {/* Hero Section */}
        <section className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            AI-Powered Lead Intelligence
          </h1>
          <p className="text-xl text-neutral-400 max-w-3xl mx-auto">
            We help robot companies find buyers before they even know they're ready to buy.
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-neutral-500">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Real-time intelligence · {stats.total.toLocaleString()} active leads tracked</span>
          </div>
        </section>

        {/* Live Industry Heatmap */}
        <section className="border border-cyan-800/50 rounded-lg p-8 bg-gradient-to-br from-cyan-950/10 via-neutral-900 to-transparent">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-cyan-400 mb-2">
                🗺️ Live Pipeline Heatmap
              </h2>
              <p className="text-sm text-neutral-500">
                Real-time distribution of automation opportunities by industry
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-white tabular-nums">
                {stats.total.toLocaleString()}
              </div>
              <div className="text-xs text-neutral-500">Total Leads</div>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-12 bg-neutral-900 rounded animate-pulse"></div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {industries.map((ind, idx) => {
                const percentage = (ind.count / maxCount) * 100;
                const isHottest = idx === 0;
                
                return (
                  <div key={ind.name} className="group">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-neutral-300">
                          {ind.name}
                        </span>
                        {isHottest && (
                          <span className="text-lg">🔥</span>
                        )}
                        {ind.hot > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded border border-red-900 text-red-400">
                            {ind.hot} HOT
                          </span>
                        )}
                      </div>
                      <span className="text-sm font-bold text-emerald-400 tabular-nums">
                        {ind.count}
                      </span>
                    </div>
                    <div className="h-8 bg-neutral-900 rounded-lg overflow-hidden border border-neutral-800 group-hover:border-cyan-700 transition-colors">
                      <div 
                        className={`h-full transition-all duration-1000 ease-out ${
                          isHottest 
                            ? 'bg-gradient-to-r from-emerald-600 to-emerald-500' 
                            : 'bg-gradient-to-r from-cyan-700 to-cyan-600'
                        }`}
                        style={{ width: `${percentage}%` }}>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-neutral-800 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-red-400 tabular-nums">{stats.hot}</div>
              <div className="text-xs text-neutral-500">Hot Leads</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-400 tabular-nums">{stats.warm}</div>
              <div className="text-xs text-neutral-500">Warm Leads</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-400 tabular-nums">{stats.cold}</div>
              <div className="text-xs text-neutral-500">Cold Leads</div>
            </div>
          </div>
        </section>

        {/* Mission */}
        <section className="grid md:grid-cols-2 gap-8">
          <div className="border border-neutral-800 rounded-lg p-6 space-y-4">
            <h3 className="text-xl font-bold text-emerald-400">Our Mission</h3>
            <p className="text-neutral-300 leading-relaxed">
              Robot companies struggle to find buyers. Traditional sales is reactive—waiting for RFPs, 
              trade shows, and inbound leads. By the time companies post an RFP, they've already done 
              6 months of research and shortlisted vendors.
            </p>
            <p className="text-neutral-300 leading-relaxed">
              We flip the script. Our AI monitors <span className="text-cyan-400 font-semibold">140+ data sources</span> to 
              detect buying signals <span className="text-emerald-400 font-semibold">before</span> companies even know 
              they need automation.
            </p>
          </div>

          <div className="border border-neutral-800 rounded-lg p-6 space-y-4">
            <h3 className="text-xl font-bold text-cyan-400">How It Works</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">1.</span>
                <div>
                  <div className="font-medium text-neutral-200">AI Monitors Signals</div>
                  <div className="text-sm text-neutral-500">Job postings, exec hires, funding, M&A, capex, news</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">2.</span>
                <div>
                  <div className="font-medium text-neutral-200">Smart Scoring</div>
                  <div className="text-sm text-neutral-500">Multi-factor analysis: automation fit, labor pain, timing</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">3.</span>
                <div>
                  <div className="font-medium text-neutral-200">Prioritized Outreach</div>
                  <div className="text-sm text-neutral-500">HOT leads = reach out today. WARM = nurture sequence</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Platform Capabilities */}
        <section className="space-y-6">
          <h2 className="text-3xl font-bold text-center text-neutral-100">
            Platform Capabilities
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '🤖',
                title: 'AI-Powered Analysis',
                desc: 'Advanced NLP classifies signals, extracts intent, and scores automation fit in real-time',
                color: 'emerald'
              },
              {
                icon: '🎯',
                title: 'Intent Detection',
                desc: 'Detects 14 signal types: funding, exec hires, labor shortage, expansion, M&A, RFPs',
                color: 'cyan'
              },
              {
                icon: '⚡',
                title: 'Real-Time Updates',
                desc: 'Pipeline refreshes every 30 seconds. New leads appear within minutes of signal detection',
                color: 'emerald'
              },
              {
                icon: '📊',
                title: 'Multi-Factor Scoring',
                desc: 'Automation score, labor pain, expansion trajectory, market fit → overall priority',
                color: 'cyan'
              },
              {
                icon: '🔍',
                title: 'Intelligence Search',
                desc: 'Natural language queries: "hotels with labor shortage" or "logistics companies expanding"',
                color: 'emerald'
              },
              {
                icon: '💰',
                title: 'Deal Sizing',
                desc: 'Employee count + industry → estimated robot deployment size (5-10 units, 20-50 units, etc)',
                color: 'cyan'
              }
            ].map((feature, idx) => (
              <div key={idx} 
                className={`border border-neutral-800 rounded-lg p-6 hover:border-${feature.color}-700 transition-colors group`}>
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h4 className={`text-lg font-semibold text-${feature.color}-400 mb-2`}>
                  {feature.title}
                </h4>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Data Sources */}
        <section className="border border-neutral-800 rounded-lg p-8 bg-gradient-to-br from-neutral-900 to-transparent">
          <h2 className="text-2xl font-bold text-center text-neutral-100 mb-6">
            Data Sources
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">
                Public Signals (122 sources)
              </h4>
              <ul className="space-y-2 text-sm text-neutral-400">
                <li>• Indeed, LinkedIn, Glassdoor job postings (labor pain)</li>
                <li>• News APIs: GNews, NewsAPI, NewsData (50+ RSS feeds)</li>
                <li>• Industry directories: hotels, logistics, healthcare</li>
                <li>• Company websites, press releases, blog posts</li>
                <li>• Google search engine results (trending queries)</li>
              </ul>
            </div>
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-cyan-400 uppercase tracking-wide">
                Government & RFPs (18 sources) 🔥
              </h4>
              <ul className="space-y-2 text-sm text-neutral-400">
                <li>• SAM.gov, GSA.gov (US federal contracts)</li>
                <li>• TED.europa.eu (EU tenders - 27 countries)</li>
                <li>• TendersInfo, Biddingo, MERX (global procurement)</li>
                <li>• Qviro, JobToRob, Automate America (RFP marketplaces)</li>
                <li>• LinkedIn automation project searches</li>
              </ul>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-neutral-800 text-center">
            <p className="text-sm text-neutral-500">
              <span className="text-emerald-400 font-semibold">140+ sources</span> monitored 24/7 · 
              Government contracts average <span className="text-cyan-400 font-semibold">$2M-$10M+</span> deployments
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center border-2 border-emerald-800 rounded-lg p-12 bg-gradient-to-br from-emerald-950/20 to-transparent">
          <h2 className="text-3xl font-bold text-emerald-400 mb-4">
            Stop Chasing RFPs. Start Leading the Conversation.
          </h2>
          <p className="text-lg text-neutral-400 mb-8 max-w-2xl mx-auto">
            Get access to the same intelligence platform used by leading robotics companies 
            to identify opportunities 6-12 months before competitors.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/">
              <button className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors">
                View Live Dashboard
              </button>
            </Link>
            <Link href="/brief">
              <button className="px-8 py-3 border-2 border-cyan-600 text-cyan-400 hover:border-cyan-500 hover:text-cyan-300 font-semibold rounded-lg transition-colors">
                Daily Brief
              </button>
            </Link>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-800 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8 text-center text-sm text-neutral-500">
          <p>© 2026 Ready for Robots. Built with AI intelligence for the automation industry.</p>
          <p className="mt-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 mr-2"></span>
            System operational · Last updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
      </footer>
    </div>
  );
}
