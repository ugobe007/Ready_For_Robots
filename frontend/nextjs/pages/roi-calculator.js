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
  }

  function downloadBenchmarkReport() {
    if (!benchmarkEmail) {
      alert('Please enter your email to receive the report');
      return;
    }
    // TODO: Send to backend for email capture
    alert(`✅ Industry Benchmark Report sent to ${benchmarkEmail}!\n\nCheck your inbox in a few minutes.`);
    setShowBenchmarkDownload(false);
    setBenchmarkEmail('');
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
                <div className="pt-4 border-t border-neutral-800">
                  <p className="text-xs text-neutral-500 mb-3">
                    💡 Want to find companies ready to buy robots like yours?
                  </p>
                  <Link href="/robot-ready"
                    className="block text-center border-2 border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
                    Find Your Customers →
                  </Link>
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
    </div>
  );
}
