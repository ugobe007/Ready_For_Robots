/**
 * Robot Ready - Lead Generation for Robot Companies
 * Submit your robot URL, get matched with ideal customers
 */
import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from './_app';

const API = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

export default function RobotReady() {
  const { user } = useAuth();
  const [step, setStep] = useState('form'); // form | loading | results
  const [robotName, setRobotName] = useState('');
  const [robotUrl, setRobotUrl] = useState('');
  const [email, setEmail] = useState('');
  const [targetIndustries, setTargetIndustries] = useState([]);
  const [targetRegions, setTargetRegions] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const INDUSTRIES = [
    'Hospitality', 'Logistics', 'Healthcare', 'Food Service', 
    'Airports & Transportation', 'Casinos & Gaming', 'Cruise Lines', 
    'Theme Parks & Entertainment', 'Real Estate & Facilities'
  ];

  const REGIONS = [
    'Northeast US', 'Southeast US', 'Midwest US', 'Southwest US', 'West Coast US',
    'Canada', 'United Kingdom', 'Europe', 'Asia-Pacific', 'Global'
  ];

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setStep('loading');

    try {
      const response = await fetch(`${API}/api/robot-ready/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_name: robotName,
          url: robotUrl,
          email: email,
          target_industries: targetIndustries.length > 0 ? targetIndustries : null,
          target_regions: targetRegions.length > 0 ? targetRegions : null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze robot');
      }

      const data = await response.json();
      setResults(data);
      setStep('results');
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
      setStep('form');
    }
  }

  const toggleIndustry = (ind) => {
    setTargetIndustries(prev => 
      prev.includes(ind) ? prev.filter(i => i !== ind) : [...prev, ind]
    );
  };

  const toggleRegion = (reg) => {
    setTargetRegions(prev => 
      prev.includes(reg) ? prev.filter(r => r !== reg) : [...prev, reg]
    );
  };

  return (
    <div className="min-h-screen bg-neutral-950">
      <div className="max-w-4xl mx-auto p-8">
        
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-xs text-emerald-600 hover:text-emerald-400 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="text-center">
            <h1 className="text-4xl font-bold text-neutral-100 mb-3">🤖 Robot Ready</h1>
            <p className="text-lg text-neutral-400 mb-2">Find Your Ideal Customers</p>
            <p className="text-sm text-neutral-600 max-w-2xl mx-auto">
              Submit your robot's URL and we'll identify companies that are the perfect fit, 
              plus give you a customized outreach strategy and talking points.
            </p>
          </div>
        </div>

        {/* Form */}
        {step === 'form' && (
          <div className="max-w-xl mx-auto">
            <form onSubmit={handleSubmit} className="border border-neutral-800 rounded-lg p-8 space-y-6">
              
              {error && (
                <div className="border border-red-800 bg-red-950/20 rounded p-4 text-sm text-red-400">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Robot Name(s) *
                </label>
                <input
                  type="text"
                  value={robotName}
                  onChange={(e) => setRobotName(e.target.value)}
                  placeholder="e.g., TUG T3, Relay Robot, Serve"
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">
                  Separate multiple robots with commas
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Product URL *
                </label>
                <input
                  type="url"
                  value={robotUrl}
                  onChange={(e) => setRobotUrl(e.target.value)}
                  placeholder="https://yourcompany.com/products/robot"
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">
                  We'll scrape this page to understand your robot's capabilities
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Your Email (optional)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">
                  We'll email you the results (no spam, promise)
                </p>
              </div>

              {/* Target Industries */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Target Industries (optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {INDUSTRIES.map(ind => (
                    <button
                      key={ind}
                      type="button"
                      onClick={() => toggleIndustry(ind)}
                      className={`px-3 py-2 rounded text-xs font-medium transition-colors ${
                        targetIndustries.includes(ind)
                          ? 'bg-violet-900/50 border border-violet-700 text-violet-400'
                          : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                      }`}>
                      {ind}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-neutral-600 mt-2">
                  {targetIndustries.length > 0 
                    ? `Selected: ${targetIndustries.join(', ')}`
                    : 'Leave blank to search all industries'}
                </p>
              </div>

              {/* Target Regions */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Target Regions (optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {REGIONS.map(reg => (
                    <button
                      key={reg}
                      type="button"
                      onClick={() => toggleRegion(reg)}
                      className={`px-3 py-2 rounded text-xs font-medium transition-colors ${
                        targetRegions.includes(reg)
                          ? 'bg-cyan-900/50 border border-cyan-700 text-cyan-400'
                          : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                      }`}>
                      {reg}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-neutral-600 mt-2">
                  {targetRegions.length > 0 
                    ? `Selected: ${targetRegions.join(', ')}`
                    : 'Leave blank to search globally'}
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded transition-colors">
                🚀 Find My Customers
              </button>

              <div className="text-xs text-neutral-700 text-center pt-4 border-t border-neutral-800">
                <p>What you'll get:</p>
                <ul className="mt-2 space-y-1 text-left max-w-sm mx-auto">
                  <li>✓ Top 10 matched companies with contact details</li>
                  <li>✓ Customized value proposition for each</li>
                  <li>✓ Key decision-maker signals</li>
                  <li>✓ Recommended outreach strategy</li>
                </ul>
              </div>
            </form>
          </div>
        )}

        {/* Loading */}
        {step === 'loading' && (
          <div className="text-center py-16">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
            <h2 className="text-xl font-semibold text-neutral-300 mb-2">Analyzing Your Robot...</h2>
            <div className="max-w-md mx-auto space-y-2 text-sm text-neutral-600">
              <p>⚙️ Scraping product page...</p>
              <p>🤖 Identifying capabilities & use cases...</p>
              <p>🎯 Matching with {results?.total_leads || 'thousands of'} companies...</p>
              <p>💡 Generating outreach strategies...</p>
            </div>
          </div>
        )}

        {/* Results */}
        {step === 'results' && results && (
          <div className="space-y-6">
            
            {/* Summary */}
            <div className="border-2 border-emerald-800/50 rounded-lg p-6 bg-gradient-to-br from-emerald-950/20 to-transparent">
              <h2 className="text-2xl font-bold text-emerald-400 mb-4">
                ✅ Found {results.matched_companies?.length || 0} Perfect Matches
              </h2>
              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <div className="text-3xl font-bold text-neutral-100 mb-1">
                    {results.matched_companies?.filter(c => c.priority_tier === 'HOT').length || 0}
                  </div>
                  <div className="text-xs text-neutral-500 uppercase tracking-wider">Hot Leads</div>
                  <div className="text-[10px] text-red-400 mt-1">Ready to buy now</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-neutral-100 mb-1">
                    ${((results.estimated_deal_value || 0) / 1000).toFixed(0)}K
                  </div>
                  <div className="text-xs text-neutral-500 uppercase tracking-wider">Est. Pipeline Value</div>
                  <div className="text-[10px] text-emerald-400 mt-1">Total opportunity</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-neutral-100 mb-1">
                    {results.top_industry || 'Multiple'}
                  </div>
                  <div className="text-xs text-neutral-500 uppercase tracking-wider">Top Industry</div>
                  <div className="text-[10px] text-cyan-400 mt-1">Best fit sector</div>
                </div>
              </div>
            </div>

            {/* Robot Capabilities */}
            {results.robot_capabilities && (
              <div className="border border-neutral-800 rounded-lg p-6">
                <h3 className="text-sm font-semibold text-neutral-300 mb-3">Your Robot Profile</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-neutral-600">Type</span>
                    <p className="text-neutral-300">{results.robot_capabilities.type || 'Not specified'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-neutral-600">Primary Use Case</span>
                    <p className="text-neutral-300">{results.robot_capabilities.use_case || 'General automation'}</p>
                  </div>
                  {results.robot_capabilities.capabilities && (
                    <div className="md:col-span-2">
                      <span className="text-[10px] uppercase tracking-wider text-neutral-600">Capabilities</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {results.robot_capabilities.capabilities.map((cap, idx) => (
                          <span key={idx} className="border border-cyan-800 text-cyan-400 rounded px-2 py-1 text-xs">
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Matched Companies */}
            <div className="border border-neutral-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-neutral-100 mb-4">Your Top Matches</h3>
              <div className="space-y-4">
                {results.matched_companies?.slice(0, 10).map((company, idx) => (
                  <div key={idx} className="border border-neutral-800 rounded-lg p-5 hover:border-emerald-800 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-xs font-bold text-neutral-600">#{idx + 1}</span>
                          <h4 className="text-base font-semibold text-neutral-100">{company.company_name}</h4>
                          {company.priority_tier === 'HOT' && (
                            <span className="border border-red-800 text-red-400 rounded px-2 py-0.5 text-[10px] uppercase">
                              🔥 Hot
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-neutral-600">
                          {[company.industry, company.location_city, company.location_state].filter(Boolean).join(' · ')}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-emerald-400 mb-1">
                          {company.match_score}% match
                        </div>
                        {company.employee_estimate && (
                          <div className="text-[10px] text-neutral-600">
                            {company.employee_estimate.toLocaleString()} employees
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Value Proposition */}
                    <div className="bg-emerald-950/20 border border-emerald-900/50 rounded p-3 mb-3">
                      <div className="text-[10px] uppercase tracking-wider text-emerald-500 mb-1">💡 Your Pitch</div>
                      <p className="text-sm text-neutral-300">{company.value_proposition}</p>
                    </div>

                    {/* Key Signals */}
                    {company.key_signals && company.key_signals.length > 0 && (
                      <div className="mb-3">
                        <div className="text-[10px] uppercase tracking-wider text-neutral-600 mb-2">📊 Key Signals</div>
                        <div className="space-y-1">
                          {company.key_signals.slice(0, 2).map((signal, sidx) => (
                            <p key={sidx} className="text-xs text-neutral-500 pl-3 border-l-2 border-cyan-800">
                              {signal}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Next Steps */}
                    <div className="text-xs text-neutral-600">
                      <span className="text-emerald-500">→</span> {company.recommended_action || 'Reach out with personalized demo offer'}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Overall Strategy */}
            {results.overall_strategy && (
              <div className="border border-cyan-800 rounded-lg p-6 bg-cyan-950/10">
                <h3 className="text-lg font-semibold text-cyan-400 mb-4">📋 Recommended Strategy</h3>
                <div className="prose prose-invert prose-sm max-w-none">
                  <div className="space-y-3 text-sm text-neutral-300">
                    {results.overall_strategy.split('\n').map((para, idx) => (
                      para.trim() && <p key={idx}>{para}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* CTA */}
            <div className="text-center pt-6 border-t border-neutral-800">
              <button
                onClick={() => { 
                  setStep('form'); 
                  setResults(null); 
                  setRobotName(''); 
                  setRobotUrl(''); 
                  setTargetIndustries([]);
                  setTargetRegions([]);
                }}
                className="border border-neutral-700 text-neutral-400 hover:border-emerald-600 hover:text-emerald-400 px-6 py-3 rounded transition-colors">
                ← Analyze Another Robot
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
