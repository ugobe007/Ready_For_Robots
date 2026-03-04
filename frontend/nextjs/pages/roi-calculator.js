/**
 * ROI Calculator - Free Tool
 * Calculate robot payback period, annual savings, and ROI
 */
import { useState } from 'react';
import Link from 'next/link';

export default function ROICalculator() {
  const [robotType, setRobotType] = useState('');
  const [robotCost, setRobotCost] = useState('');
  const [industry, setIndustry] = useState('');
  const [laborMode, setLaborMode] = useState('hourly'); // hourly | annual
  const [hoursPerDay, setHoursPerDay] = useState('');
  const [hourlyWage, setHourlyWage] = useState('');
  const [annualLaborCost, setAnnualLaborCost] = useState('');
  const [results, setResults] = useState(null);
  const [showBenchmarkDownload, setShowBenchmarkDownload] = useState(false);
  const [benchmarkEmail, setBenchmarkEmail] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);

  // Industry benchmark data
  const INDUSTRY_BENCHMARKS = {
    'Hospitality (Hotels/Resorts)': { avgCost: 28000, avgPayback: 8.5, adoptionRate: 42 },
    'Healthcare (Hospitals/Clinics)': { avgCost: 35000, avgPayback: 9.2, adoptionRate: 38 },
    'Logistics/Warehousing': { avgCost: 45000, avgPayback: 7.1, adoptionRate: 61 },
    'Food Service/Restaurants': { avgCost: 22000, avgPayback: 11.3, adoptionRate: 28 },
    'Airports/Transportation': { avgCost: 38000, avgPayback: 8.8, adoptionRate: 45 },
    'Retail': { avgCost: 25000, avgPayback: 10.2, adoptionRate: 31 },
    'Manufacturing': { avgCost: 52000, avgPayback: 6.5, adoptionRate: 67 },
    'Real Estate/Facilities': { avgCost: 30000, avgPayback: 9.5, adoptionRate: 35 },
    'Other': { avgCost: 30000, avgPayback: 9.0, adoptionRate: 40 }
  };

  const ROBOT_TYPES = [
    'Delivery/Transport',
    'Disinfection/Cleaning',
    'Service Robot',
    'Warehouse/Logistics',
    'Medical/Healthcare',
    'Food Service',
    'Security/Patrol',
    'Other'
  ];

  const INDUSTRIES = [
    'Hospitality (Hotels/Resorts)',
    'Healthcare (Hospitals/Clinics)',
    'Logistics/Warehousing',
    'Food Service/Restaurants',
    'Airports/Transportation',
    'Retail',
    'Manufacturing',
    'Real Estate/Facilities',
    'Other'
  ];

  function calculateROI() {
    const cost = parseFloat(robotCost);
    if (!cost || cost <= 0) {
      alert('Please enter a valid robot cost');
      return;
    }

    // Calculate annual labor cost
    let annualLabor = 0;
    if (laborMode === 'hourly') {
      const hours = parseFloat(hoursPerDay) || 0;
      const wage = parseFloat(hourlyWage) || 0;
      annualLabor = hours * wage * 365;
    } else {
      annualLabor = parseFloat(annualLaborCost) || 0;
    }

    if (annualLabor <= 0) {
      alert('Please enter valid labor costs');
      return;
    }

    // Assume 10% maintenance cost per year
    const annualMaintenance = cost * 0.10;
    const annualSavings = annualLabor - annualMaintenance;
    const paybackMonths = (cost / annualSavings) * 12;
    const roi1Year = ((annualSavings - cost) / cost) * 100;
    const roi3Year = (((annualSavings * 3) - cost) / cost) * 100;
    const totalSavings3Year = (annualSavings * 3) - cost;

    // Get industry benchmark if available
    const benchmark = industry ? INDUSTRY_BENCHMARKS[industry] : null;

    setResults({
      robotCost: cost,
      annualLaborReplaced: annualLabor,
      annualMaintenance: annualMaintenance,
      annualSavings: annualSavings,
      paybackMonths: paybackMonths,
      roi1Year: roi1Year,
      roi3Year: roi3Year,
      totalSavings3Year: totalSavings3Year,
      industry: industry,
      benchmark: benchmark
    });

    // Track calculation for analytics
    fetch('/api/track/roi-calculation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        robot_type: robotType,
        robot_cost: cost,
        industry: industry,
        payback_months: paybackMonths,
        annual_savings: annualSavings
      })
    }).catch(err => console.error('Analytics tracking failed:', err));
  }

  function downloadBenchmarkReport() {
    if (!benchmarkEmail) {
      alert('Please enter your email to receive the report');
      return;
    }
    
    // Track email capture for analytics
    fetch('/api/track/roi-calculation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        robot_type: robotType,
        robot_cost: parseFloat(robotCost),
        industry: industry,
        payback_months: results?.paybackMonths,
        annual_savings: results?.annualSavings,
        email: benchmarkEmail
      })
    }).catch(err => console.error('Analytics tracking failed:', err));
    
    alert(`✅ Industry Benchmark Report sent to ${benchmarkEmail}!\n\nCheck your inbox in a few minutes.`);
    setShowBenchmarkDownload(false);
    setBenchmarkEmail('');
  }

  async function shareResults() {
    if (!results) return;
    
    try {
      const response = await fetch('/api/share-calculation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_type: robotType,
          robot_cost: results.robotCost,
          industry: industry,
          payback_months: results.paybackMonths,
          annual_savings: results.annualSavings,
          roi_1_year: results.roi1Year,
          roi_3_year: results.roi3Year,
          total_savings_3_year: results.totalSavings3Year
        })
      });
      
      const data = await response.json();
      const fullUrl = `${window.location.origin}${data.share_url}`;
      setShareUrl(fullUrl);
      setShowShareModal(true);
    } catch (err) {
      alert('Failed to create share link. Please try again.');
    }
  }

  function copyShareLink() {
    navigator.clipboard.writeText(shareUrl);
    alert('✅ Link copied to clipboard!');
  }

  function reset() {
    setRobotType('');
    setRobotCost('');
    setIndustry('');
    setHoursPerDay('');
    setHourlyWage('');
    setAnnualLaborCost('');
    setResults(null);
  }

  return (
    <div className="min-h-screen bg-neutral-950">
      <div className="max-w-5xl mx-auto p-8">
        
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-xs text-emerald-600 hover:text-emerald-400 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="text-center mb-6">
            <h1 className="text-4xl font-bold text-neutral-100 mb-3">💰 Robot ROI Calculator</h1>
            <p className="text-lg text-neutral-400 mb-2">Calculate Your Payback Period in 30 Seconds</p>
          </div>

          {/* How it Works */}
          <div className="border border-neutral-800 rounded-lg p-6 bg-neutral-900/50 mb-6">
            <h2 className="text-sm font-semibold text-emerald-400 mb-3">How This Works</h2>
            <div className="text-sm text-neutral-400 space-y-2">
              <p>
                <strong className="text-neutral-300">1. Enter your robot details</strong> - Cost, type, and industry
              </p>
              <p>
                <strong className="text-neutral-300">2. Input labor costs</strong> - Either hourly wage + hours/day OR annual labor cost
              </p>
              <p>
                <strong className="text-neutral-300">3. Get instant results</strong> - Payback period, annual savings, 3-year ROI
              </p>
              <p className="pt-2 border-t border-neutral-800 text-xs text-neutral-500">
                💡 <strong>Want to save your calculations?</strong> Sign up for a free account to track multiple robots, 
                compare scenarios, and generate shareable reports. (Coming soon)
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Calculator Form */}
          <div className="border border-neutral-800 rounded-lg p-6 space-y-6">
            <h2 className="text-xl font-bold text-neutral-100">Calculator Inputs</h2>

            {/* Robot Type */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Robot Type
              </label>
              <select
                value={robotType}
                onChange={(e) => setRobotType(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 focus:outline-none focus:border-emerald-600">
                <option value="">Select type...</option>
                {ROBOT_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {/* Robot Cost */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Robot Cost (USD) *
              </label>
              <input
                type="number"
                value={robotCost}
                onChange={(e) => setRobotCost(e.target.value)}
                placeholder="25000"
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
              />
              <p className="text-xs text-neutral-600 mt-1">Purchase price or lease equivalent</p>
            </div>

            {/* Industry */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Industry
              </label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 focus:outline-none focus:border-emerald-600">
                <option value="">Select industry...</option>
                {INDUSTRIES.map(ind => (
                  <option key={ind} value={ind}>{ind}</option>
                ))}
              </select>
            </div>

            {/* Labor Cost Mode Toggle */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-3">
                How do you want to calculate labor replacement? *
              </label>
              <div className="flex gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => setLaborMode('hourly')}
                  className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
                    laborMode === 'hourly'
                      ? 'border-2 border-emerald-600 text-emerald-400'
                      : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                  }`}>
                  ⏰ Hourly Wage
                </button>
                <button
                  type="button"
                  onClick={() => setLaborMode('annual')}
                  className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
                    laborMode === 'annual'
                      ? 'border-2 border-emerald-600 text-emerald-400'
                      : 'border border-neutral-800 text-neutral-600 hover:border-neutral-700'
                  }`}>
                  📊 Annual Cost
                </button>
              </div>
            </div>

            {/* Labor Inputs */}
            {laborMode === 'hourly' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Hours per Day *
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={hoursPerDay}
                    onChange={(e) => setHoursPerDay(e.target.value)}
                    placeholder="8"
                    className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                  />
                  <p className="text-xs text-neutral-600 mt-1">Robot operating hours per day</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Hourly Wage (USD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={hourlyWage}
                    onChange={(e) => setHourlyWage(e.target.value)}
                    placeholder="15.00"
                    className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                  />
                  <p className="text-xs text-neutral-600 mt-1">Labor cost per hour (including benefits)</p>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Annual Labor Cost (USD) *
                </label>
                <input
                  type="number"
                  value={annualLaborCost}
                  onChange={(e) => setAnnualLaborCost(e.target.value)}
                  placeholder="45000"
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">Total annual cost of labor being replaced</p>
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={calculateROI}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded transition-colors">
                Calculate ROI
              </button>
              <button
                onClick={reset}
                className="border border-neutral-700 text-neutral-400 hover:border-emerald-600 hover:text-emerald-400 px-6 py-3 rounded transition-colors">
                Reset
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="border border-neutral-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-neutral-100 mb-6">Results</h2>

            {!results ? (
              <div className="text-center py-12 text-neutral-600">
                <div className="text-4xl mb-4">📊</div>
                <p className="text-sm">Enter your robot details and click "Calculate ROI" to see results</p>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* Key Metric - Payback */}
                <div className="border-2 border-emerald-800/50 rounded-lg p-6 bg-gradient-to-br from-emerald-950/20 to-transparent">
                  <div className="text-xs text-emerald-400 font-semibold mb-1">PAYBACK PERIOD</div>
                  <div className="text-4xl font-bold text-emerald-400 mb-1">
                    {results.paybackMonths.toFixed(1)} months
                  </div>
                  <div className="text-xs text-neutral-500">
                    {(results.paybackMonths / 12).toFixed(1)} years to break even
                  </div>
                </div>

                {/* Annual Savings */}
                <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
                  <div className="text-xs text-neutral-500 mb-1">Annual Savings</div>
                  <div className="text-2xl font-bold text-neutral-200">
                    ${results.annualSavings.toLocaleString()}
                  </div>
                  <div className="text-xs text-neutral-600 mt-2">
                    Labor: ${results.annualLaborReplaced.toLocaleString()} - 
                    Maintenance: ${results.annualMaintenance.toLocaleString()}
                  </div>
                </div>

                {/* ROI */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
                    <div className="text-xs text-neutral-500 mb-1">1-Year ROI</div>
                    <div className={`text-xl font-bold ${results.roi1Year > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {results.roi1Year.toFixed(0)}%
                    </div>
                  </div>
                  <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
                    <div className="text-xs text-neutral-500 mb-1">3-Year ROI</div>
                    <div className="text-xl font-bold text-emerald-400">
                      {results.roi3Year.toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* 3-Year Savings */}
                <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
                  <div className="text-xs text-neutral-500 mb-1">Total 3-Year Savings</div>
                  <div className="text-2xl font-bold text-neutral-200">
                    ${results.totalSavings3Year.toLocaleString()}
                  </div>
                </div>

                {/* Industry Benchmark Comparison */}
                {results.benchmark && (
                  <div className="border-2 border-yellow-800/50 rounded-lg p-4 bg-gradient-to-br from-yellow-950/20 to-transparent">
                    <div className="text-xs text-yellow-400 font-semibold mb-3">📊 INDUSTRY BENCHMARK</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Your Payback:</span>
                        <span className={`font-semibold ${
                          results.paybackMonths < results.benchmark.avgPayback 
                            ? 'text-emerald-400' : 'text-yellow-400'
                        }`}>
                          {results.paybackMonths.toFixed(1)} mo
                          {results.paybackMonths < results.benchmark.avgPayback && ' ✓ Better'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Industry Avg:</span>
                        <span className="text-neutral-400">{results.benchmark.avgPayback} mo</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-neutral-800">
                        <span className="text-neutral-500">Market Adoption:</span>
                        <span className="text-neutral-400">{results.benchmark.adoptionRate}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Download Industry Report CTA */}
                {!showBenchmarkDownload ? (
                  <div className="pt-4 border-t border-neutral-800">
                    <button
                      onClick={() => setShowBenchmarkDownload(true)}
                      className="w-full border-2 border-yellow-600 text-yellow-400 hover:bg-yellow-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
                      📥 Download Full Industry Benchmark Report
                    </button>
                    <p className="text-xs text-neutral-600 text-center mt-2">
                      Get avg costs, payback times, and adoption trends for your industry
                    </p>
                  </div>
                ) : (
                  <div className="pt-4 border-t border-neutral-800 space-y-3">
                    <div className="text-sm text-neutral-400 mb-2">
                      📧 Enter your email to receive the full industry benchmark report:
                    </div>
                    <input
                      type="email"
                      value={benchmarkEmail}
                      onChange={(e) => setBenchmarkEmail(e.target.value)}
                      placeholder="you@company.com"
                      className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-yellow-600"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={downloadBenchmarkReport}
                        className="flex-1 bg-yellow-600 hover:bg-yellow-500 text-white font-semibold py-3 px-6 rounded transition-colors">
                        Send Report
                      </button>
                      <button
                        onClick={() => setShowBenchmarkDownload(false)}
                        className="border border-neutral-700 text-neutral-400 hover:border-neutral-600 px-6 py-3 rounded transition-colors">
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* CTA */}
                <div className="pt-4 border-t border-neutral-800 space-y-3">
                  <div>
                    <button
                      onClick={shareResults}
                      className="w-full text-center border-2 border-purple-600 text-purple-400 hover:bg-purple-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
                      🔗 Share These Results
                    </button>
                    <p className="text-xs text-neutral-600 mt-1 text-center">
                      Get a link to share on LinkedIn, Twitter, or email
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-neutral-500 mb-2">
                      💡 Want to find companies ready to buy robots like yours?
                    </p>
                    <Link href="/robot-ready"
                      className="block text-center border-2 border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
                      Find Your Customers →
                    </Link>
                  </div>
                </div>

                {/* Save Results Teaser */}
                <div className="text-xs text-neutral-600 text-center pt-2 border-t border-neutral-800">
                  <p>📌 Sign up for free to save calculations and generate reports</p>
                  <p className="text-neutral-700 mt-1">(Coming soon)</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 text-center text-xs text-neutral-600">
          <p className="mb-2">
            <strong className="text-neutral-500">Assumptions:</strong> Results assume 10% annual maintenance cost, 
            365-day operation, and consistent labor replacement.
          </p>
          <p>
            Actual results may vary based on deployment conditions, utilization rates, and site-specific factors.
          </p>
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={() => setShowShareModal(false)}>
          <div className="bg-neutral-900 border border-neutral-700 rounded-lg p-8 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold text-white mb-4">🔗 Share Your Results</h2>
            <p className="text-neutral-400 text-sm mb-6">
              Anyone with this link can view your ROI calculation results. Share on social media or send to colleagues!
            </p>
            
            <div className="bg-neutral-800 border border-neutral-700 rounded p-3 mb-4 flex items-center gap-2">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 bg-transparent text-neutral-300 text-sm focus:outline-none"
              />
              <button
                onClick={copyShareLink}
                className="border border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white px-4 py-2 rounded text-sm font-medium transition-colors">
                Copy
              </button>
            </div>

            <div className="flex gap-3 mb-6">
              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`Check out my robot ROI calculation: ${results?.paybackMonths.toFixed(1)} month payback, $${results?.annualSavings.toLocaleString()}/year savings!`)}&url=${encodeURIComponent(shareUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-center bg-blue-500 hover:bg-blue-400 text-white py-2 px-4 rounded text-sm font-medium transition-colors">
                Share on Twitter
              </a>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-center bg-blue-700 hover:bg-blue-600 text-white py-2 px-4 rounded text-sm font-medium transition-colors">
                Share on LinkedIn
              </a>
            </div>

            <button
              onClick={() => setShowShareModal(false)}
              className="w-full border border-neutral-700 text-neutral-400 hover:border-neutral-600 py-2 px-4 rounded transition-colors">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
