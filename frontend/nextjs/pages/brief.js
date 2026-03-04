/**
 * Daily Strategy Brief
 * Executive summary of hot leads, market signals, and recommended actions
 */
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from './_app';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

export default function StrategyBrief() {
  const { user } = useAuth();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [date] = useState(new Date());

  useEffect(() => {
    fetch(`${API}/api/leads?limit=500`)
      .then(r => r.json())
      .then(data => {
        setLeads(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Removed auth requirement - public access for demos

  const hotLeads = leads.filter(l => l.priority_tier === 'HOT').slice(0, 10);
  const warmLeads = leads.filter(l => l.priority_tier === 'WARM').slice(0, 15);
  
  // Group signals by type
  const allSignals = leads.flatMap(l => l.signals || []);
  const signalsByType = allSignals.reduce((acc, sig) => {
    const type = sig.signal_type || 'unknown';
    if (!acc[type]) acc[type] = [];
    acc[type].push(sig);
    return acc;
  }, {});

  // Top industries
  const industryCount = leads.reduce((acc, l) => {
    const ind = l.industry || 'Unknown';
    acc[ind] = (acc[ind] || 0) + 1;
    return acc;
  }, {});
  const topIndustries = Object.entries(industryCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const formatDate = (d) => {
    return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const SIGNAL_META = {
    funding_round:  { label: 'Funding Rounds', icon: '💰', color: 'text-violet-400', border: 'border-violet-700' },
    strategic_hire: { label: 'Executive Hires', icon: '👔', color: 'text-blue-400', border: 'border-blue-700' },
    capex:          { label: 'CapEx Signals', icon: '🏗️', color: 'text-cyan-400', border: 'border-cyan-700' },
    ma_activity:    { label: 'M&A Activity', icon: '🤝', color: 'text-pink-400', border: 'border-pink-700' },
    expansion:      { label: 'Expansions', icon: '📈', color: 'text-emerald-400', border: 'border-emerald-700' },
    labor_shortage: { label: 'Labor Gaps', icon: '⚠️', color: 'text-red-400', border: 'border-red-800' },
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-neutral-600 animate-pulse">Loading strategy brief...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950">
      <div className="max-w-6xl mx-auto p-8">
        
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-xs text-emerald-600 hover:text-emerald-400 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-neutral-100 mb-2">Daily Strategy Brief</h1>
              <p className="text-sm text-neutral-500">{formatDate(date)}</p>
            </div>
            <button 
              onClick={() => window.print()}
              className="px-4 py-2 border border-neutral-700 text-neutral-400 rounded text-xs hover:border-emerald-600 hover:text-emerald-400 transition-colors">
              🖨️ Print Brief
            </button>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="border-2 border-emerald-800/50 rounded-lg p-6 mb-6 bg-gradient-to-br from-emerald-950/20 to-transparent">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-4">Executive Summary</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div>
              <div className="text-3xl font-bold text-neutral-100 mb-1">{hotLeads.length}</div>
              <div className="text-xs text-neutral-500 uppercase tracking-wider">Hot Opportunities</div>
              <div className="text-[10px] text-red-400 mt-1">Priority outreach today</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-neutral-100 mb-1">{warmLeads.length}</div>
              <div className="text-xs text-neutral-500 uppercase tracking-wider">Warm Prospects</div>
              <div className="text-[10px] text-yellow-400 mt-1">Nurture sequence</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-neutral-100 mb-1">{allSignals.length}</div>
              <div className="text-xs text-neutral-500 uppercase tracking-wider">Active Signals</div>
              <div className="text-[10px] text-cyan-400 mt-1">Market intelligence</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-neutral-100 mb-1">{topIndustries.length}</div>
              <div className="text-xs text-neutral-500 uppercase tracking-wider">Target Sectors</div>
              <div className="text-[10px] text-neutral-500 mt-1">Industry coverage</div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          
          {/* Left Column - Priority Actions */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Top 10 Hot Leads */}
            <div className="border border-neutral-800 rounded-lg p-6">
              <h2 className="text-sm font-semibold text-red-400 mb-4 flex items-center gap-2">
                <span className="text-lg">🔥</span> Priority Outreach - Top 10
              </h2>
              <div className="space-y-3">
                {hotLeads.map((lead, idx) => {
                  const topSig = lead.signals?.[0];
                  return (
                    <Link key={lead.id} href={`/?lead=${lead.id}`}
                      className="block border border-neutral-800 rounded p-4 hover:border-red-800 hover:bg-red-950/20 transition-all group">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-baseline gap-2 mb-1">
                            <span className="text-xs font-bold text-neutral-600">#{idx + 1}</span>
                            <span className="text-sm font-semibold text-neutral-100 group-hover:text-emerald-400 transition-colors">
                              {lead.company_name}
                            </span>
                          </div>
                          <div className="text-[10px] text-neutral-600 mb-2">
                            {[lead.industry, lead.location_city, lead.location_state].filter(Boolean).join(' · ')}
                          </div>
                          {topSig && (
                            <p className="text-[11px] text-neutral-500 line-clamp-2">
                              {topSig.raw_text}
                            </p>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          <div className="inline-flex items-center border border-emerald-700 text-emerald-400 rounded px-2 py-1 text-xs font-mono font-semibold tabular-nums">
                            {Math.round(lead.score?.overall_score || 0)}
                          </div>
                          <div className="text-[9px] text-neutral-700 mt-1">{lead.signal_count} signals</div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Warm Pipeline */}
            <div className="border border-neutral-800 rounded-lg p-6">
              <h2 className="text-sm font-semibold text-yellow-400 mb-4">Warm Pipeline - Monitor & Nurture</h2>
              <div className="space-y-2">
                {warmLeads.slice(0, 8).map((lead, idx) => (
                  <Link key={lead.id} href={`/?lead=${lead.id}`}
                    className="flex items-center justify-between p-3 border border-neutral-800 rounded hover:border-yellow-800 hover:bg-yellow-950/10 transition-all group">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span className="text-xs font-semibold text-neutral-100 group-hover:text-emerald-400 transition-colors truncate">
                          {lead.company_name}
                        </span>
                        <span className="text-[10px] text-neutral-600 shrink-0">{lead.industry}</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-neutral-600 ml-4 tabular-nums">
                      {Math.round(lead.score?.overall_score || 0)}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Market Intelligence */}
          <div className="space-y-6">
            
            {/* Signal Activity */}
            <div className="border border-neutral-800 rounded-lg p-6">
              <h2 className="text-sm font-semibold text-cyan-400 mb-4">Signal Activity</h2>
              <div className="space-y-3">
                {Object.entries(signalsByType)
                  .filter(([type]) => SIGNAL_META[type])
                  .sort((a, b) => b[1].length - a[1].length)
                  .slice(0, 6)
                  .map(([type, sigs]) => {
                    const meta = SIGNAL_META[type];
                    return (
                      <div key={type} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{meta.icon}</span>
                          <span className={`text-xs ${meta.color}`}>{meta.label}</span>
                        </div>
                        <span className="text-sm font-bold text-neutral-300 tabular-nums">{sigs.length}</span>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Top Industries */}
            <div className="border border-neutral-800 rounded-lg p-6">
              <h2 className="text-sm font-semibold text-neutral-300 mb-4">Top Industries</h2>
              <div className="space-y-3">
                {topIndustries.map(([industry, count], idx) => (
                  <div key={industry} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-neutral-700 w-4">#{idx + 1}</span>
                      <span className="text-xs text-neutral-300">{industry}</span>
                    </div>
                    <span className="text-sm font-semibold text-emerald-400 tabular-nums">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Actions */}
            <div className="border border-emerald-800 rounded-lg p-6 bg-emerald-950/10">
              <h2 className="text-sm font-semibold text-emerald-400 mb-4">Recommended Actions</h2>
              <div className="space-y-3 text-xs text-neutral-300">
                <div className="flex gap-2">
                  <span className="text-emerald-400 shrink-0">✓</span>
                  <span>Prioritize outreach to top {Math.min(5, hotLeads.length)} HOT leads today</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-emerald-400 shrink-0">✓</span>
                  <span>Review {signalsByType.strategic_hire?.length || 0} executive hire signals for buying committee mapping</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-emerald-400 shrink-0">✓</span>
                  <span>Monitor {signalsByType.funding_round?.length || 0} funding events for budget availability</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-emerald-400 shrink-0">✓</span>
                  <span>Track {signalsByType.expansion?.length || 0} expansion projects for greenfield opportunities</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-neutral-800 text-center text-[10px] text-neutral-700">
          <p>Generated by Ready for Robots Intelligence Platform · {formatDate(date)}</p>
          <p className="mt-1">Confidential - For Internal Use Only</p>
        </div>
      </div>

      <style jsx global>{`
        @media print {
          body { background: white !important; }
          .max-w-6xl { max-width: 100% !important; }
          button { display: none !important; }
          a { color: inherit !important; text-decoration: none !important; }
        }
      `}</style>
    </div>
  );
}
