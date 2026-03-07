import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

export default function PipelineResults() {
  const router = useRouter();
  const { company } = router.query;
  const [loading, setLoading] = useState(true);
  const [matches, setMatches] = useState([]);

  useEffect(() => {
    if (company) {
      // Simulate analysis - in production, this would call your backend
      setTimeout(() => {
        fetchMatches();
      }, 1500);
    }
  }, [company]);

  const fetchMatches = async () => {
    try {
      // Get top 5 HOT leads as matches
      const res = await fetch('https://ready-2-robot.fly.dev/api/leads?limit=5&temp=hot');
      const data = await res.json();
      setMatches(Array.isArray(data) ? data.slice(0, 5) : []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching matches:', err);
      setMatches([]);
      setLoading(false);
    }
  };

  const getEngagementStrategy = () => {
    if (!company) return [];
    
    return [
      {
        phase: 'Week 1-2: Awareness & Education',
        tactics: [
          'Share case study on automation ROI in their industry',
          'Comment on LinkedIn posts about labor challenges',
          'Send thought leadership article on workforce trends',
        ]
      },
      {
        phase: 'Week 3-4: Problem Agitation',
        tactics: [
          'Share industry benchmark data showing automation adoption',
          'Invite to webinar on solving labor shortages',
          'Send calculator tool for automation cost savings',
        ]
      },
      {
        phase: 'Week 5-6: Solution Introduction',
        tactics: [
          'Request 15-min intro call to discuss their challenges',
          'Share video demo of robot solving similar use case',
          'Offer pilot program assessment (limited slots)',
        ]
      },
      {
        phase: 'Week 7-8: Social Proof & Close',
        tactics: [
          'Introduce customer reference in their industry',
          'Share implementation timeline and ROI projections',
          'Propose pilot program with defined success metrics',
        ]
      }
    ];
  };

  if (!company) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-300 flex items-center justify-center">
        <div className="text-center">
          <p className="text-neutral-500">No company URL provided</p>
          <Link href="/">
            <button className="mt-4 px-4 py-2 border border-emerald-700 text-emerald-400 rounded hover:bg-emerald-900/20">
              Return to Dashboard
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-300">
      {/* Header */}
      <div className="border-b border-neutral-800 bg-neutral-900/50 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/">
            <h1 className="text-lg font-bold text-emerald-400 cursor-pointer hover:text-emerald-300">
              Ready for Robots
            </h1>
          </Link>
          <Link href="/login">
            <button className="px-4 py-2 text-sm border border-emerald-700 bg-emerald-900/20 text-emerald-400 rounded hover:border-emerald-600">
              Sign Up to Save Results
            </button>
          </Link>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Company Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-emerald-400 mb-2">
            Sales Pipeline for {company}
          </h1>
          <p className="text-neutral-400 text-sm">
            AI-powered prospect discovery and engagement strategy
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400 mb-4"></div>
            <p className="text-neutral-400">Analyzing {company} and discovering matches...</p>
          </div>
        ) : (
          <>
            {/* Top 5 Matches */}
            <div className="mb-10">
              <h2 className="text-xl font-semibold text-emerald-400 mb-4">
                🎯 Top 5 Prospect Matches
              </h2>
              {matches.length === 0 ? (
                <div className="border border-neutral-800 rounded bg-neutral-900/30 p-8 text-center">
                  <p className="text-neutral-400">No matches found at the moment. Try again later or sign up to access our full database.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {matches.map((lead, idx) => (
                    <div key={idx} className="border border-neutral-800 rounded bg-neutral-900/30 p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="font-semibold text-neutral-200 mb-1">
                            {lead.company_name || 'Company Name'}
                          </h3>
                          <div className="flex items-center gap-2 text-xs text-neutral-500">
                            <span>{lead.industry || 'Industry'}</span>
                            <span>•</span>
                            <span>{lead.employee_estimate || '100-500'} employees</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-1 rounded text-xs font-medium bg-red-900/30 text-red-400 border border-red-800">
                            Score: {lead.score || 85}
                          </span>
                        </div>
                      </div>
                      
                      {/* Signals */}
                      <div className="mb-2">
                        {lead.signals && lead.signals.length > 0 ? (
                          <>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {lead.signals.slice(0, 3).map((sig, i) => (
                                <span key={i} className="px-2 py-0.5 rounded text-[9px] uppercase font-medium bg-cyan-900/30 text-cyan-400 border border-cyan-800">
                                  {sig.signal_type || 'Signal'}
                                </span>
                              ))}
                              {lead.signals.length > 3 && (
                                <span className="px-2 py-0.5 rounded text-[9px] text-neutral-500">
                                  +{lead.signals.length - 3} more
                                </span>
                              )}
                            </div>
                            {lead.signals[0]?.description && (
                              <p className="text-xs text-neutral-400 line-clamp-2">
                                {lead.signals[0].description}
                              </p>
                            )}
                          </>
                        ) : (
                          <p className="text-xs text-neutral-500">Multiple intent signals detected</p>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs mt-3 pt-3 border-t border-neutral-800">
                        <span className="text-emerald-400">
                          💡 Why they're a match: {lead.signals?.length || 3} automation intent signals detected
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Engagement Strategy */}
            <div className="mb-10">
              <h2 className="text-xl font-semibold text-emerald-400 mb-4">
                📋 8-Week Engagement Strategy
              </h2>
              <div className="space-y-4">
                {getEngagementStrategy().map((phase, idx) => (
                  <div key={idx} className="border border-neutral-800 rounded bg-neutral-900/30 p-4">
                    <h3 className="font-semibold text-neutral-200 mb-3">
                      {phase.phase}
                    </h3>
                    <ul className="space-y-2">
                      {phase.tactics.map((tactic, i) => (
                        <li key={i} className="text-sm text-neutral-400 flex items-start gap-2">
                          <span className="text-emerald-400 mt-0.5">✓</span>
                          <span>{tactic}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA to Sign Up */}
            <div className="border border-emerald-800 rounded bg-emerald-950/20 p-6 text-center">
              <h3 className="text-xl font-semibold text-emerald-400 mb-2">
                Want the Full Pipeline Report?
              </h3>
              <p className="text-sm text-neutral-400 mb-4">
                Sign up free to unlock all automation-ready prospects, save your results, and get weekly updates on new matches.
              </p>
              <div className="flex items-center justify-center gap-3">
                <Link href="/login">
                  <button className="px-6 py-3 rounded text-sm font-semibold border border-emerald-700 bg-emerald-900/20 text-emerald-400 hover:border-emerald-600 hover:bg-emerald-900/30 transition-colors">
                    Sign Up Free
                  </button>
                </Link>
                <Link href="/">
                  <button className="px-6 py-3 rounded text-sm border border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300 transition-colors">
                    Back to Dashboard
                  </button>
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
