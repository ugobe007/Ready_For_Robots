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
  const [inputMode, setInputMode] = useState('url'); // url | text
  const [robotDescription, setRobotDescription] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [expandedCompanies, setExpandedCompanies] = useState([]);

  // Usage tracking
  const [usageCount, setUsageCount] = useState(0);
  const [showPaywall, setShowPaywall] = useState(false);
  const FREE_LIMIT = 5;

  // Load usage count on mount
  useState(() => {
    try {
      const stored = localStorage.getItem('rfr_usage_count');
      setUsageCount(parseInt(stored || '0', 10));
    } catch {}
  }, []);

  // Track usage for anonymous users
  function trackUsage() {
    if (user) return; // Don't track signed-in users
    const newCount = usageCount + 1;
    setUsageCount(newCount);
    localStorage.setItem('rfr_usage_count', newCount.toString());
  }

  const toggleCompany = (idx) => {
    setExpandedCompanies(prev => 
      prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
    );
  };

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
    
    // Check usage limit for anonymous users
    if (!user && usageCount >= FREE_LIMIT) {
      setShowPaywall(true);
      return;
    }
    
    setStep('loading');

    try {
      const response = await fetch(`${API}/api/robot-ready/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_name: robotName,
          url: inputMode === 'url' ? robotUrl : null,
          description: inputMode === 'text' ? robotDescription : null,
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
      
      // Track usage for anonymous users
      trackUsage();

      // Track robot search for analytics
      fetch('/api/track/robot-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_name: robotName,
          has_url: !!robotUrl,
          target_industries: targetIndustries,
          target_regions: targetRegions,
          matches_found: data.matched_companies?.length || 0
        })
      }).catch(err => console.error('Analytics tracking failed:', err));
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
      setStep('form');
    }
  }

  const generatePlaybook = async () => {
    if (!results) return;
    
    try {
      const response = await fetch('/api/generate-playbook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_name: robotName,
          matched_companies: results.matched_companies,
          overall_strategy: results.overall_strategy,
          target_industries: targetIndustries,
          target_regions: targetRegions
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate playbook');
      }

      // Download the PDF
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${robotName.replace(/[^a-zA-Z0-9]/g, '_')}_sales_playbook.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Failed to generate playbook. Please try again.');
    }
  };

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
      {/* Paywall Modal */}
      {showPaywall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setShowPaywall(false)}>
          <div className="bg-neutral-950 border-2 border-emerald-700 rounded-lg max-w-lg w-full p-8" onClick={e => e.stopPropagation()}>
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-900/50 to-cyan-900/50 flex items-center justify-center text-3xl">
                  🚀
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Ready to Find More Customers?</h2>
                <p className="text-neutral-400 text-sm">
                  You've used all <span className="text-emerald-400 font-semibold">{FREE_LIMIT} free robot matches</span>. 
                  Sign up to unlock unlimited matches, save strategies, and accelerate your sales.
                </p>
              </div>
              <div className="space-y-3">
                <Link href="/login" 
                  className="block w-full py-3 px-6 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded transition-colors text-center">
                  Sign Up Free →
                </Link>
                <button onClick={() => setShowPaywall(false)}
                  className="block w-full py-2 px-6 border border-neutral-700 hover:border-neutral-500 text-neutral-400 hover:text-neutral-300 rounded transition-colors">
                  Maybe Later
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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

              {/* Input Mode Toggle */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-3">
                  How would you like to provide information?
                </label>
                <div className="flex gap-2 mb-4">
                  <button
                    type="button"
                    onClick={() => setInputMode('url')}
                    className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
                      inputMode === 'url'
                        ? 'border-2 border-emerald-600 text-emerald-400'
                        : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                    }`}>
                    🔗 I have a URL
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputMode('text')}
                    className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
                      inputMode === 'text'
                        ? 'border-2 border-emerald-600 text-emerald-400'
                        : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                    }`}>
                    📝 Describe my robot
                  </button>
                </div>
              </div>

              {inputMode === 'url' ? (
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Product URL *
                  </label>
                  <input
                    type="url"
                    value={robotUrl}
                    onChange={(e) => setRobotUrl(e.target.value)}
                    placeholder="https://yourcompany.com/products/robot"
                    required={inputMode === 'url'}
                    className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                  />
                  <p className="text-xs text-neutral-400 mt-1">
                    We'll scrape this page to understand your robot's capabilities
                  </p>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Robot Description *
                  </label>
                  <textarea
                    value={robotDescription}
                    onChange={(e) => setRobotDescription(e.target.value)}
                    placeholder="Describe your robot's capabilities, use cases, and key features...\n\nExample: Our autonomous delivery robot is designed for hospitals and hotels. It can navigate elevators, deliver items up to 50 lbs, has UV-C disinfection, operates 24/7, and integrates with building management systems."
                    required={inputMode === 'text'}
                    required
                    rows={6}
                    className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                  />
                  <p className="text-xs text-neutral-600 mt-1">
                    Include capabilities, target industries, key features, and use cases
                  </p>
                </div>
              )}

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
                          ? 'border-2 border-emerald-600 text-emerald-400'
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
                          ? 'border-2 border-emerald-600 text-emerald-400'
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
                className="w-full border-2 border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
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
            
            {/* Hero Header with Summary */}
            <div className="bg-gradient-to-br from-emerald-900/30 via-neutral-900 to-neutral-950 border-2 border-emerald-600/50 rounded-xl p-8">
              <div className="text-center mb-6">
                <h2 className="text-3xl font-bold text-emerald-400 mb-2">
                  ✅ Found {results.matched_companies?.length || 0} Perfect Matches
                </h2>
                <p className="text-neutral-300">Companies ready to buy your robot</p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
                <div className="text-center">
                  <div className="text-5xl font-bold text-white mb-2">
                    {results.matched_companies?.filter(c => c.priority_tier === 'HOT').length || 0}
                  </div>
                  <div className="text-sm text-neutral-300 uppercase tracking-wider font-semibold">Hot Leads</div>
                  <div className="text-xs text-red-400 mt-1">🔥 Ready to buy now</div>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-bold text-white mb-2">
                    {(() => {
                      const val = results.estimated_deal_value || 0;
                      if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
                      if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`;
                      return `$${val}`;
                    })()}
                  </div>
                  <div className="text-sm text-neutral-300 uppercase tracking-wider font-semibold">Pipeline Value</div>
                  <div className="text-xs text-emerald-400 mt-1">💰 Total opportunity</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-white mb-2">
                    {results.top_industry || 'Multiple'}
                  </div>
                  <div className="text-sm text-neutral-300 uppercase tracking-wider font-semibold">Top Industry</div>
                  <div className="text-xs text-cyan-400 mt-1">🎯 Best fit sector</div>
                </div>
              </div>
            </div>

            {/* Market Fit Score */}
            {(() => {
              // Calculate market fit score components
              const hotCount = results.matched_companies?.filter(c => c.priority_tier === 'HOT').length || 0;
              const totalMatches = results.matched_companies?.length || 0;
              
              // Industry demand score (0-35 points based on hot leads ratio)
              const industryDemand = Math.min(35, Math.round((hotCount / Math.max(totalMatches, 1)) * 35));
              
              // Geographic coverage (0-25 points based on total matches)
              const geoCoverage = Math.min(25, Math.round((totalMatches / 25) * 25));
              
              // Signal strength (0-25 points based on average signals per company)
              const avgSignals = results.matched_companies?.reduce((sum, c) => sum + (c.key_signals?.length || 0), 0) / Math.max(totalMatches, 1);
              const signalStrength = Math.min(25, Math.round(avgSignals * 5));
              
              // Opportunity quality (0-15 points based on estimated deal value)
              const dealQuality = Math.min(15, Math.round((results.estimated_deal_value || 0) / 50000));
              
              const marketFitScore = industryDemand + geoCoverage + signalStrength + dealQuality;
              
              // Score interpretation
              let scoreColor = 'text-red-400';
              let scoreBg = 'from-red-950/20';
              let scoreBorder = 'border-red-800/50';
              let scoreLabel = 'Weak Fit';
              
              if (marketFitScore >= 75) {
                scoreColor = 'text-emerald-400';
                scoreBg = 'from-emerald-950/20';
                scoreBorder = 'border-emerald-800/50';
                scoreLabel = 'Excellent Fit';
              } else if (marketFitScore >= 50) {
                scoreColor = 'text-yellow-400';
                scoreBg = 'from-yellow-950/20';
                scoreBorder = 'border-yellow-800/50';
                scoreLabel = 'Good Fit';
              }

              return (
                <div className={`border-2 ${scoreBorder} rounded-lg p-6 bg-gradient-to-br ${scoreBg} to-transparent`}>
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-sm font-semibold text-neutral-300 mb-1">Market Fit Score</h3>
                      <p className="text-xs text-neutral-600">Based on industry demand, coverage, and opportunity quality</p>
                    </div>
                    <div className="text-right">
                      <div className={`text-4xl font-bold ${scoreColor}`}>{marketFitScore}</div>
                      <div className={`text-xs font-semibold ${scoreColor}`}>{scoreLabel}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-neutral-600 mb-1">Industry Demand</div>
                      <div className="text-lg font-semibold text-neutral-300">{industryDemand}/35</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-neutral-600 mb-1">Geo Coverage</div>
                      <div className="text-lg font-semibold text-neutral-300">{geoCoverage}/25</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-neutral-600 mb-1">Signal Strength</div>
                      <div className="text-lg font-semibold text-neutral-300">{signalStrength}/25</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-neutral-600 mb-1">Deal Quality</div>
                      <div className="text-lg font-semibold text-neutral-300">{dealQuality}/15</div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Robot Capabilities */}
            {results.robot_capabilities && (
              <div className="border border-neutral-700 rounded-lg p-6 bg-neutral-900/50">
                <h3 className="text-base font-semibold text-white mb-4">Your Robot Profile</h3>
                
                {/* Robot Name with emerald border */}
                {results.robot_name && (
                  <div className="mb-4 inline-block border-2 border-emerald-500 rounded px-3 py-1.5">
                    <span className="text-emerald-400 font-semibold">{results.robot_name}</span>
                  </div>
                )}
                
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-neutral-400 font-semibold">Type</span>
                    <p className="text-neutral-200 mt-1">{results.robot_capabilities.type || 'Not specified'}</p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-wider text-neutral-400 font-semibold">Primary Use Case</span>
                    <p className="text-neutral-200 mt-1">{results.robot_capabilities.use_case || 'General automation'}</p>
                  </div>
                  {results.robot_capabilities.capabilities && (
                    <div className="md:col-span-2">
                      <span className="text-xs uppercase tracking-wider text-neutral-400 font-semibold">Capabilities</span>
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
                  <div 
                    key={idx} 
                    className="border border-neutral-700 rounded-lg p-5 hover:border-emerald-600 transition-all cursor-pointer"
                    onClick={() => toggleCompany(idx)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-baseline gap-2 mb-1">
                          <span className="text-xs font-bold text-neutral-400">#{idx + 1}</span>
                          <h4 className="text-lg font-bold text-white">{company.company_name}</h4>
                          {company.priority_tier === 'HOT' && (
                            <span className="border border-red-700 bg-red-900/30 text-red-300 rounded px-2 py-0.5 text-[10px] uppercase font-semibold">
                              🔥 Hot
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-neutral-400">
                          {[company.industry, company.location_city, company.location_state].filter(Boolean).join(' · ')}
                        </p>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-lg font-bold text-emerald-400 mb-1">
                          {company.match_score}% match
                        </div>
                        {company.employee_estimate && (
                          <div className="text-xs text-neutral-400">
                            {company.employee_estimate.toLocaleString()} employees
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Always Visible: Value Proposition */}
                    <div className="bg-emerald-950/30 border border-emerald-800/50 rounded p-3 mb-3">
                      <div className="text-xs uppercase tracking-wider text-emerald-400 mb-1 font-semibold">💡 Your Pitch</div>
                      <p className="text-sm text-neutral-200">{company.value_proposition}</p>
                    </div>

                    {/* Expandable Details */}
                    {expandedCompanies.includes(idx) && (
                      <div className="space-y-3 pt-3 border-t border-neutral-700">
                        {/* Key Signals */}
                        {company.key_signals && company.key_signals.length > 0 && (
                          <div>
                            <div className="text-xs uppercase tracking-wider text-cyan-400 mb-2 font-semibold">📊 Key Signals</div>
                            <div className="space-y-2">
                              {company.key_signals.map((signal, sidx) => (
                                <p key={sidx} className="text-sm text-neutral-300 pl-3 border-l-2 border-cyan-600">
                                  {signal}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Contact Info */}
                        {company.website && (
                          <div>
                            <div className="text-xs uppercase tracking-wider text-purple-400 mb-2 font-semibold">🔗 Contact</div>
                            <a 
                              href={company.website} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm text-purple-300 hover:text-purple-200 underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {company.website}
                            </a>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Click to expand/collapse indicator */}
                    <div className="text-xs text-neutral-400 mt-3 flex items-center justify-between">
                      <div>
                        <span className="text-emerald-400">→</span> {company.recommended_action || 'Reach out with personalized demo offer'}
                      </div>
                      <div className="text-emerald-400">
                        {expandedCompanies.includes(idx) ? '▲ Click to collapse' : '▼ Click to learn more'}
                      </div>
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
            <div className="flex gap-4 pt-6 border-t border-neutral-800">
              <button
                onClick={generatePlaybook}
                className="flex-1 border-2 border-purple-600 text-purple-400 hover:bg-purple-600 hover:text-white font-semibold px-6 py-3 rounded transition-colors">
                📄 Download Sales Playbook
              </button>
              <button
                onClick={() => { 
                  setStep('form'); 
                  setResults(null); 
                  setRobotName(''); 
                  setRobotUrl(''); 
                  setRobotDescription('');
                  setInputMode('url');
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
