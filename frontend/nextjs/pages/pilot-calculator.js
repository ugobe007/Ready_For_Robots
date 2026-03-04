import { useState } from 'react';
import Link from 'next/link';

export default function PilotCalculator() {
  const [robotType, setRobotType] = useState('');
  const [useCase, setUseCase] = useState('');
  const [facilities, setFacilities] = useState('');
  const [shiftCoverage, setShiftCoverage] = useState('single'); // single, double, triple
  const [duration, setDuration] = useState('4'); // weeks
  const [results, setResults] = useState(null);

  const USE_CASES = [
    'Delivery/Transport',
    'Cleaning/Disinfection',
    'Security/Patrol',
    'Inventory Management',
    'Food Service',
    'Guest Services',
    'Warehouse Operations',
    'Other'
  ];

  function calculatePilot(e) {
    e.preventDefault();

    const facilityCount = parseInt(facilities) || 1;
    const durationWeeks = parseInt(duration) || 4;
    
    // Calculate robot requirements
    let robotsPerFacility = 1;
    if (shiftCoverage === 'double') robotsPerFacility = 2;
    if (shiftCoverage === 'triple') robotsPerFacility = 3;
    
    const totalRobots = facilityCount * robotsPerFacility;
    
    // Estimated costs (assuming $30k avg robot cost)
    const robotLeasePerWeek = 500; // Weekly lease during pilot
    const setupCost = 2000; // Per facility
    const trainingCost = 1500; // Per facility
    const supportCost = 1000; // Per week total
    
    const totalLeaseCost = totalRobots * robotLeasePerWeek * durationWeeks;
    const totalSetupCost = facilityCount * setupCost;
    const totalTrainingCost = facilityCount * trainingCost;
    const totalSupportCost = supportCost * durationWeeks;
    const totalPilotCost = totalLeaseCost + totalSetupCost + totalTrainingCost + totalSupportCost;
    
    // KPIs
    const kpis = [
      { name: 'Uptime', target: '95%', measurement: 'Track hours operational vs. downtime' },
      { name: 'Labor Hours Saved', target: durationWeeks * robotsPerFacility * 40 + ' hours', measurement: 'Compare manual vs. automated task time' },
      { name: 'Task Completion Rate', target: '98%', measurement: 'Successful completions / Total attempts' },
      { name: 'User Satisfaction', target: '4.5/5', measurement: 'Staff and end-user surveys' },
      { name: 'ROI Estimate', target: '8-12 months', measurement: 'Calculate based on actual savings data' }
    ];
    
    // Success criteria
    const successCriteria = [
      'Robot maintains >90% uptime during pilot period',
      'Demonstrates measurable labor cost savings',
      'Staff adoption rate >80% (trained staff actively using robots)',
      'No major safety incidents or operational disruptions',
      'Positive feedback from stakeholders (staff, customers, management)'
    ];
    
    // Pilot timeline
    const timeline = [
      { week: '1', phase: 'Setup & Training', activities: 'Install robots, train staff, establish baseline metrics' },
      { week: durationWeeks <= 4 ? '2-3' : '2-4', phase: 'Initial Operations', activities: 'Monitor performance, troubleshoot issues, collect feedback' },
      { week: durationWeeks <= 4 ? '4' : '5-8', phase: 'Optimization', activities: 'Fine-tune workflows, measure KPIs, compare to baseline' },
      { week: 'End', phase: 'Evaluation', activities: 'Final report, ROI analysis, go/no-go decision' }
    ];
    
    // Full deployment estimate
    const fullDeploymentRobots = facilityCount * robotsPerFacility;
    const avgRobotCost = 30000;
    const fullDeploymentCost = fullDeploymentRobots * avgRobotCost;
    const pilotDiscountPercent = Math.round((totalPilotCost / fullDeploymentCost) * 100);
    
    setResults({
      robots: totalRobots,
      robotsPerFacility,
      durationWeeks,
      totalPilotCost,
      leaseCost: totalLeaseCost,
      setupCost: totalSetupCost,
      trainingCost: totalTrainingCost,
      supportCost: totalSupportCost,
      kpis,
      successCriteria,
      timeline,
      fullDeploymentCost,
      pilotDiscountPercent
    });
  }

  function reset() {
    setRobotType('');
    setUseCase('');
    setFacilities('');
    setShiftCoverage('single');
    setDuration('4');
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
            <h1 className="text-4xl font-bold text-neutral-100 mb-3">🧪 Pilot Program Calculator</h1>
            <p className="text-lg text-neutral-400 mb-2">De-Risk Your Robot Investment</p>
            <p className="text-sm text-neutral-600 max-w-2xl mx-auto">
              Plan a structured pilot program with clear KPIs, success metrics, and costs before committing to full deployment.
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Form */}
          <div>
            <form onSubmit={calculatePilot} className="border border-neutral-800 rounded-lg p-8 space-y-6">
              
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Robot Type *
                </label>
                <input
                  type="text"
                  value={robotType}
                  onChange={(e) => setRobotType(e.target.value)}
                  placeholder="e.g., Autonomous Delivery Robot"
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Primary Use Case *
                </label>
                <select
                  value={useCase}
                  onChange={(e) => setUseCase(e.target.value)}
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 focus:outline-none focus:border-emerald-600">
                  <option value="">Select use case...</option>
                  {USE_CASES.map(uc => (
                    <option key={uc} value={uc}>{uc}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Number of Facilities *
                </label>
                <input
                  type="number"
                  min="1"
                  value={facilities}
                  onChange={(e) => setFacilities(e.target.value)}
                  placeholder="1"
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">How many locations will participate in the pilot?</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Shift Coverage *
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'single', label: 'Single (1 robot)', desc: '8-12 hrs' },
                    { value: 'double', label: 'Double (2 robots)', desc: '16-20 hrs' },
                    { value: 'triple', label: 'Triple (3 robots)', desc: '24 hrs' }
                  ].map(shift => (
                    <button
                      key={shift.value}
                      type="button"
                      onClick={() => setShiftCoverage(shift.value)}
                      className={`p-3 rounded border text-sm transition-colors ${
                        shiftCoverage === shift.value
                          ? 'border-emerald-600 text-emerald-400 bg-emerald-950/20'
                          : 'border-neutral-700 text-neutral-400 hover:border-neutral-600'
                      }`}>
                      <div className="font-medium">{shift.label.split(' ')[0]}</div>
                      <div className="text-xs text-neutral-600 mt-1">{shift.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Pilot Duration (weeks) *
                </label>
                <input
                  type="number"
                  min="2"
                  max="12"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  required
                  className="w-full bg-neutral-900 border border-neutral-700 rounded px-4 py-3 text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
                />
                <p className="text-xs text-neutral-600 mt-1">Recommended: 4-8 weeks</p>
              </div>

              <div className="flex gap-3">
                <button type="submit" className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded transition-colors">
                  Calculate Pilot Program
                </button>
                {results && (
                  <button type="button" onClick={reset} className="border border-neutral-700 text-neutral-400 hover:border-neutral-600 px-6 py-3 rounded transition-colors">
                    Reset
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Results */}
          <div className="border border-neutral-800 rounded-lg p-8">
            {!results ? (
              <div className="text-center py-12 text-neutral-600">
                <div className="text-4xl mb-4">🧪</div>
                <p className="text-sm">Enter your pilot details to see the plan and costs</p>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* Pilot Overview */}
                <div className="border-2 border-emerald-800/50 rounded-lg p-6 bg-gradient-to-br from-emerald-950/20 to-transparent">
                  <div className="text-xs text-emerald-400 font-semibold mb-1">PILOT SCOPE</div>
                  <div className="text-2xl font-bold text-emerald-400 mb-2">
                    {results.robots} Robot{results.robots > 1 ? 's' : ''} × {results.durationWeeks} Weeks
                  </div>
                  <div className="text-xs text-neutral-500">
                    {robotsPerFacility} robot{results.robotsPerFacility > 1 ? 's' : ''} per facility × {facilities} location{facilities > 1 ? 's' : ''}
                  </div>
                </div>

                {/* Total Cost */}
                <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
                  <div className="text-xs text-neutral-500 mb-1">Total Pilot Investment</div>
                  <div className="text-3xl font-bold text-neutral-200 mb-2">
                    ${results.totalPilotCost.toLocaleString()}
                  </div>
                  <div className="text-xs text-neutral-600 space-y-1">
                    <div>Robot Lease: ${results.leaseCost.toLocaleString()}</div>
                    <div>Setup: ${results.setupCost.toLocaleString()}</div>
                    <div>Training: ${results.trainingCost.toLocaleString()}</div>
                    <div>Support: ${results.supportCost.toLocaleString()}</div>
                  </div>
                </div>

                {/* Cost vs Full Deployment */}
                <div className="border border-yellow-800 rounded-lg p-4 bg-yellow-950/10">
                  <div className="text-xs text-yellow-500 mb-1">Risk Mitigation</div>
                  <div className="text-sm text-neutral-300">
                    Pilot costs only <span className="font-bold text-yellow-400">{results.pilotDiscountPercent}%</span> of full deployment (${results.fullDeploymentCost.toLocaleString()})
                  </div>
                  <div className="text-xs text-neutral-600 mt-1">
                    Test before committing to ${results.fullDeploymentCost.toLocaleString()} purchase
                  </div>
                </div>

                {/* KPIs */}
                <div>
                  <h3 className="text-sm font-semibold text-neutral-300 mb-3">Key Performance Indicators</h3>
                  <div className="space-y-2">
                    {results.kpis.map((kpi, idx) => (
                      <div key={idx} className="border border-neutral-800 rounded p-3 bg-neutral-900/30 text-xs">
                        <div className="font-medium text-neutral-300 mb-1">{kpi.name}</div>
                        <div className="text-emerald-400">Target: {kpi.target}</div>
                        <div className="text-neutral-600 mt-1">{kpi.measurement}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Success Criteria */}
                <div>
                  <h3 className="text-sm font-semibold text-neutral-300 mb-3">Success Criteria</h3>
                  <ul className="space-y-2">
                    {results.successCriteria.map((criteria, idx) => (
                      <li key={idx} className="text-xs text-neutral-400 flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">✓</span>
                        <span>{criteria}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Timeline */}
                <div>
                  <h3 className="text-sm font-semibold text-neutral-300 mb-3">Pilot Timeline</h3>
                  <div className="space-y-2">
                    {results.timeline.map((milestone, idx) => (
                      <div key={idx} className="border-l-2 border-cyan-600 pl-3 py-1">
                        <div className="text-xs font-medium text-cyan-400">Week {milestone.week}: {milestone.phase}</div>
                        <div className="text-xs text-neutral-600 mt-0.5">{milestone.activities}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CTA */}
                <div className="pt-4 border-t border-neutral-800">
                  <p className="text-xs text-neutral-500 mb-3">
                    💡 Ready to find companies that need this pilot program?
                  </p>
                  <Link href="/robot-ready"
                    className="block text-center border-2 border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white font-semibold py-3 px-6 rounded transition-colors">
                    Find Pilot Customers →
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 border border-cyan-800 rounded-lg p-6 bg-cyan-950/10">
          <h3 className="text-lg font-semibold text-cyan-400 mb-4">💡 Why Start with a Pilot?</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm text-neutral-300">
            <div>
              <div className="font-semibold mb-2">De-Risk Investment</div>
              <div className="text-neutral-500">Test robots in real conditions before committing to full purchase. Identify issues early.</div>
            </div>
            <div>
              <div className="font-semibold mb-2">Prove ROI</div>
              <div className="text-neutral-500">Collect actual data on savings, efficiency gains, and operational impact to justify expansion.</div>
            </div>
            <div>
              <div className="font-semibold mb-2">Build Confidence</div>
              <div className="text-neutral-500">Get staff buy-in, work out integration kinks, and create internal champions.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
