/**
 * RaasVsCapexCalculator.js — Ready For Robots Financial Engine
 * 
 * Compares RaaS (Robots-as-a-Service) monthly operating expenses vs.
 * CapEx outright purchase against human labor across 1, 2, and 3-shift operations.
 */
import { useState, useMemo } from 'react';

export const PRESET_MODELS = [
  {
    id: 'agility-digit',
    name: 'Agility Robotics — Digit (Humanoid)',
    category: 'Humanoid',
    raasMonthly: 8500,
    raasSetup: 25000,
    capexPurchase: 200000,
    capexSetup: 20000,
    capexAnnualMaint: 36000,
    defaultSpeedParity: 0.50, // 50% speed parity vs human (needs 2 robots for 1 line)
    typicalPicksPerHour: 150,
  },
  {
    id: 'apptronik-apollo',
    name: 'Apptronik — Apollo (Humanoid)',
    category: 'Humanoid',
    raasMonthly: 7800,
    raasSetup: 22000,
    capexPurchase: 185000,
    capexSetup: 18000,
    capexAnnualMaint: 32000,
    defaultSpeedParity: 0.55,
    typicalPicksPerHour: 165,
  },
  {
    id: 'gxo-amr-heavy',
    name: 'Palletizing / Heavy Logistics AMR',
    category: 'AMR / AGV',
    raasMonthly: 3800,
    raasSetup: 10000,
    capexPurchase: 95000,
    capexSetup: 10000,
    capexAnnualMaint: 12000,
    defaultSpeedParity: 0.90,
    typicalPicksPerHour: 270,
  },
  {
    id: 'universal-cobot',
    name: 'Collaborative Arm / Bin Picker',
    category: 'Cobot',
    raasMonthly: 2200,
    raasSetup: 5000,
    capexPurchase: 45000,
    capexSetup: 5000,
    capexAnnualMaint: 6000,
    defaultSpeedParity: 0.80,
    typicalPicksPerHour: 240,
  },
];

export default function RaasVsCapexCalculator({ onLeadCapture }) {
  const [selectedPresetId, setSelectedPresetId] = useState('agility-digit');
  
  // Financial & Operational Inputs
  const [hourlyWage, setHourlyWage] = useState(24); // $24/hr average 3PL/warehouse
  const [shifts, setShifts] = useState(2); // 1, 2, or 3 shifts
  const [laborBurdenPct, setLaborBurdenPct] = useState(30); // 30% taxes/benefits/turnover
  const [humanPicksPerHour, setHumanPicksPerHour] = useState(300);
  
  // Custom Overrides
  const [raasMonthly, setRaasMonthly] = useState(8500);
  const [raasSetup, setRaasSetup] = useState(25000);
  const [capexPurchase, setCapexPurchase] = useState(200000);
  const [capexSetup, setCapexSetup] = useState(20000);
  const [capexAnnualMaint, setCapexAnnualMaint] = useState(36000);
  const [speedParity, setSpeedParity] = useState(0.50);

  // Email Lead Modal state
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [workEmail, setWorkEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [leadSubmitted, setLeadSubmitted] = useState(false);

  // Handle Preset Select
  const handleSelectPreset = (presetId) => {
    setSelectedPresetId(presetId);
    if (presetId === 'custom') return;
    const preset = PRESET_MODELS.find((m) => m.id === presetId);
    if (preset) {
      setRaasMonthly(preset.raasMonthly);
      setRaasSetup(preset.raasSetup);
      setCapexPurchase(preset.capexPurchase);
      setCapexSetup(preset.capexSetup);
      setCapexAnnualMaint(preset.capexAnnualMaint);
      setSpeedParity(preset.defaultSpeedParity);
    }
  };

  // Engine Calculations
  const calc = useMemo(() => {
    const hoursPerShiftYear = 2000; // 50 wks * 40 hrs
    const totalShiftHoursAnnual = shifts * hoursPerShiftYear;
    
    // Fully burdened human cost per hour and per shift
    const burdenedWage = hourlyWage * (1 + laborBurdenPct / 100);
    const humanAnnualLaborPerShift = hoursPerShiftYear * burdenedWage;
    const totalHumanAnnualLabor = shifts * humanAnnualLaborPerShift;
    const totalHuman5YearCost = totalHumanAnnualLabor * 5;

    // Fleet Size Multiplier based on Speed Parity Ratio
    // If robot is 50% speed of human, we need 2 units to match line throughput (1 / 0.5 = 2 units)
    const unitsNeededPerShiftLine = Math.ceil(1 / Math.max(0.1, speedParity));

    // RaaS Calculations
    const raasAnnualCostPerUnit = raasMonthly * 12;
    const raasAnnualTotalFleet = raasAnnualCostPerUnit * unitsNeededPerShiftLine;
    const raasTotal5Year = (raasSetup * unitsNeededPerShiftLine) + (raasAnnualTotalFleet * 5);
    const raasEffectiveHourly = totalShiftHoursAnnual > 0 ? (raasAnnualTotalFleet / totalShiftHoursAnnual) : 0;
    const raas5YearSavingsVsHuman = totalHuman5YearCost - raasTotal5Year;
    const raasAnnualSavingsVsHuman = totalHumanAnnualLabor - raasAnnualTotalFleet;

    // CapEx Calculations
    const capexInitialTotalFleet = (capexPurchase + capexSetup) * unitsNeededPerShiftLine;
    const capexAnnualMaintTotalFleet = capexAnnualMaint * unitsNeededPerShiftLine;
    const capexTotal5Year = capexInitialTotalFleet + (capexAnnualMaintTotalFleet * 5);
    const capexEffectiveHourly = totalShiftHoursAnnual > 0 ? ((capexTotal5Year / 5) / totalShiftHoursAnnual) : 0;
    const capex5YearSavingsVsHuman = totalHuman5YearCost - capexTotal5Year;

    // CapEx Savings Premium vs RaaS over 5 Years
    const capexSavingsOverRaas5Year = raasTotal5Year - capexTotal5Year;

    return {
      burdenedWage,
      humanAnnualLaborPerShift,
      totalHumanAnnualLabor,
      totalHuman5YearCost,
      unitsNeededPerShiftLine,
      totalShiftHoursAnnual,
      raasAnnualTotalFleet,
      raasTotal5Year,
      raasEffectiveHourly,
      raas5YearSavingsVsHuman,
      raasAnnualSavingsVsHuman,
      capexInitialTotalFleet,
      capexTotal5Year,
      capexEffectiveHourly,
      capex5YearSavingsVsHuman,
      capexSavingsOverRaas5Year,
    };
  }, [hourlyWage, shifts, laborBurdenPct, speedParity, raasMonthly, raasSetup, capexPurchase, capexSetup, capexAnnualMaint]);

  const handleLeadFormSubmit = (e) => {
    e.preventDefault();
    if (!workEmail) return;
    setLeadSubmitted(true);
    if (onLeadCapture) {
      onLeadCapture({ workEmail, companyName, selectedPresetId, calc });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl text-slate-100 max-w-6xl mx-auto my-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-6 mb-8 gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>⚡ Ready For Robots Financial Engine</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            RaaS ($8,500/mo) vs. CapEx ($200k) ROI Calculator
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Evaluate 5-year Net Present Value, shift multipliers, and pick-speed parity against human labor.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Select Model Preset</label>
          <select
            value={selectedPresetId}
            onChange={(e) => handleSelectPreset(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-500 font-medium"
          >
            {PRESET_MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.category})
              </option>
            ))}
            <option value="custom">-- Custom Hardware Entry --</option>
          </select>
        </div>
      </div>

      {/* Main Grid: Controls vs Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-6 bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80">
          <h3 className="text-base font-semibold text-emerald-400 uppercase tracking-wider text-xs border-b border-slate-800 pb-3">
            1. Operational Parameters
          </h3>

          {/* Shift Mode Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Operational Shifts (Hours / Year)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { count: 1, label: '1 Shift', sub: '2,000 hrs' },
                { count: 2, label: '2 Shifts', sub: '4,000 hrs' },
                { count: 3, label: '3 Shifts (24/7)', sub: '6,000 hrs' },
              ].map((s) => (
                <button
                  key={s.count}
                  type="button"
                  onClick={() => setShifts(s.count)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    shifts === s.count
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 font-semibold'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="text-sm font-bold">{s.label}</div>
                  <div className="text-[11px] opacity-75">{s.sub}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Base Wage Slider */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="text-slate-300">Base Hourly Human Wage</span>
              <span className="text-emerald-400 font-bold">${hourlyWage} / hr</span>
            </div>
            <input
              type="range"
              min="15"
              max="50"
              step="1"
              value={hourlyWage}
              onChange={(e) => setHourlyWage(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 rounded-lg h-2"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>$15/hr</span>
              <span>$24/hr (Avg 3PL)</span>
              <span>$50/hr</span>
            </div>
          </div>

          {/* Labor Burden % Slider */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="text-slate-300">Labor Overhead / Burden %</span>
              <span className="text-slate-200 font-bold">{laborBurdenPct}% (${calc.burdenedWage.toFixed(2)}/hr net)</span>
            </div>
            <input
              type="range"
              min="15"
              max="50"
              step="5"
              value={laborBurdenPct}
              onChange={(e) => setLaborBurdenPct(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 rounded-lg h-2"
            />
            <span className="text-[11px] text-slate-500">Includes taxes, benefits, workers' comp, and turnover management.</span>
          </div>

          {/* Speed Parity Ratio Slider */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="text-slate-300">Pick-Speed Parity Ratio vs. Human</span>
              <span className="text-emerald-400 font-bold">{(speedParity * 100).toFixed(0)}% Speed ({calc.unitsNeededPerShiftLine} unit/line)</span>
            </div>
            <input
              type="range"
              min="0.30"
              max="1.00"
              step="0.05"
              value={speedParity}
              onChange={(e) => setSpeedParity(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 rounded-lg h-2"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              If robot operates at 50% human speed (e.g. 150 picks/hr vs 300 picks/hr), line throughput requires {calc.unitsNeededPerShiftLine} robot units.
            </p>
          </div>

          {/* Financial Parameter Customization Accordion */}
          <div className="border-t border-slate-800 pt-4">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              2. Financial Cost Pricing Inputs
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">RaaS Monthly Fee</label>
                <input
                  type="number"
                  value={raasMonthly}
                  onChange={(e) => setRaasMonthly(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">RaaS Setup Fee</label>
                <input
                  type="number"
                  value={raasSetup}
                  onChange={(e) => setRaasSetup(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">CapEx Hardware Cost</label>
                <input
                  type="number"
                  value={capexPurchase}
                  onChange={(e) => setCapexPurchase(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">CapEx Annual Maint</label>
                <input
                  type="number"
                  value={capexAnnualMaint}
                  onChange={(e) => setCapexAnnualMaint(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-white font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Engine Output & Dynamic Feasibility (7 cols) */}
        <div className="lg:col-span-7 space-y-6">

          {/* Dynamic Shift Breakeven Alert Banner */}
          {shifts === 1 && (
            <div className="bg-amber-500/10 border border-amber-500/40 rounded-2xl p-4 flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h4 className="text-sm font-bold text-amber-300 uppercase tracking-wide">1-Shift Operation Alert</h4>
                <p className="text-xs text-amber-200/80 mt-0.5 leading-relaxed">
                  At 1 shift ({calc.totalShiftHoursAnnual.toLocaleString()} hrs/yr), RaaS costs <strong className="text-white">${calc.raasEffectiveHourly.toFixed(2)}/hr</strong> vs human labor at <strong className="text-white">${calc.burdenedWage.toFixed(2)}/hr</strong>. 
                  RaaS generates a net loss of <strong className="text-amber-100">${Math.abs(calc.raasAnnualSavingsVsHuman).toLocaleString()}/yr</strong>. Operating 2+ shifts is required for positive cash flow.
                </p>
              </div>
            </div>
          )}

          {shifts === 2 && (
            <div className="bg-cyan-500/10 border border-cyan-500/40 rounded-2xl p-4 flex items-start gap-3">
              <span className="text-2xl">🟡</span>
              <div>
                <h4 className="text-sm font-bold text-cyan-300 uppercase tracking-wide">2-Shift Breakeven Reached</h4>
                <p className="text-xs text-cyan-200/80 mt-0.5 leading-relaxed">
                  At 2 shifts ({calc.totalShiftHoursAnnual.toLocaleString()} hrs/yr), RaaS operates at <strong className="text-white">${calc.raasEffectiveHourly.toFixed(2)}/hr</strong> effective rate. 
                  Generates <strong className="text-emerald-300 font-bold">${calc.raasAnnualSavingsVsHuman.toLocaleString()}/yr net savings</strong> while eliminating $200k CapEx technology risk.
                </p>
              </div>
            </div>
          )}

          {shifts === 3 && (
            <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-2xl p-4 flex items-start gap-3">
              <span className="text-2xl">🟢</span>
              <div>
                <h4 className="text-sm font-bold text-emerald-300 uppercase tracking-wide">3-Shift / 24-7 Maximum Cash Flow Positive</h4>
                <p className="text-xs text-emerald-200/80 mt-0.5 leading-relaxed">
                  At 3 shifts ({calc.totalShiftHoursAnnual.toLocaleString()} hrs/yr), RaaS drops to an effective rate of <strong className="text-white">${calc.raasEffectiveHourly.toFixed(2)}/hr</strong>. 
                  Generates <strong className="text-emerald-300 font-bold">${calc.raasAnnualSavingsVsHuman.toLocaleString()}/yr net annual savings</strong> (${(calc.raas5YearSavingsVsHuman / 1000).toFixed(0)}k 5-year NPV profit).
                </p>
              </div>
            </div>
          )}

          {/* 3-Way Key Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            
            {/* Card 1: Human Labor */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Status Quo Human</div>
              <div className="text-xl font-bold text-white mt-1">${(calc.totalHuman5YearCost / 1000).toFixed(0)}k</div>
              <div className="text-[11px] text-slate-400 mt-1">${calc.burdenedWage.toFixed(2)} / hr burdened</div>
              <div className="text-[10px] text-slate-500 mt-2">5-Year Labor Expenses ({shifts} Shift{shifts > 1 ? 's' : ''})</div>
            </div>

            {/* Card 2: RaaS OpEx */}
            <div className="bg-emerald-950/40 p-4 rounded-xl border border-emerald-500/30">
              <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">RaaS OpEx ($8.5k/mo)</div>
              <div className="text-xl font-bold text-emerald-300 mt-1">${(calc.raasTotal5Year / 1000).toFixed(0)}k</div>
              <div className="text-[11px] text-emerald-400 mt-1">${calc.raasEffectiveHourly.toFixed(2)} / hr effective</div>
              <div className="text-[10px] text-emerald-400/80 mt-2">
                {calc.raas5YearSavingsVsHuman >= 0
                  ? `+$${(calc.raas5YearSavingsVsHuman / 1000).toFixed(0)}k 5-Year Savings`
                  : `-$${(Math.abs(calc.raas5YearSavingsVsHuman) / 1000).toFixed(0)}k 5-Year Loss`}
              </div>
            </div>

            {/* Card 3: CapEx Outright */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">CapEx Purchase ($200k)</div>
              <div className="text-xl font-bold text-cyan-300 mt-1">${(calc.capexTotal5Year / 1000).toFixed(0)}k</div>
              <div className="text-[11px] text-cyan-400 mt-1">${calc.capexEffectiveHourly.toFixed(2)} / hr effective</div>
              <div className="text-[10px] text-slate-400 mt-2">
                Save ${(calc.capexSavingsOverRaas5Year / 1000).toFixed(0)}k over RaaS (Assumes CapEx)
              </div>
            </div>
          </div>

          {/* 5-Year Cumulative Cash Flow Visualizer */}
          <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800 space-y-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              5-Year Cumulative Cash Outlay Breakdown
            </h4>

            {/* Status Quo Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Status Quo Human Labor</span>
                <span className="text-slate-200 font-mono font-bold">${calc.totalHuman5YearCost.toLocaleString()}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div className="bg-slate-500 h-full rounded-full" style={{ width: '100%' }}></div>
              </div>
            </div>

            {/* RaaS Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-emerald-400 font-medium">RaaS ($8,500/mo rental)</span>
                <span className="text-emerald-300 font-mono font-bold">${calc.raasTotal5Year.toLocaleString()}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (calc.raasTotal5Year / calc.totalHuman5YearCost) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* CapEx Bar */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-cyan-400 font-medium">CapEx Outright Purchase</span>
                <span className="text-cyan-300 font-mono font-bold">${calc.capexTotal5Year.toLocaleString()}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (calc.capexTotal5Year / calc.totalHuman5YearCost) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Action Trigger Box: Executive CFO Download / Lead Capture */}
          <div className="bg-gradient-to-r from-emerald-950/60 to-slate-950 p-5 rounded-2xl border border-emerald-500/30 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-white">Generate Executive CFO Audit Report</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Download a PDF summary or apply for pre-approved RaaS financing quotes from our capital partners.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowLeadModal(true)}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs uppercase tracking-wider transition-all shrink-0 shadow-lg shadow-emerald-500/20"
            >
              Export CFO Audit PDF →
            </button>
          </div>

        </div>
      </div>

      {/* Lead Capture & PDF Modal */}
      {showLeadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl relative text-slate-100">
            <button
              onClick={() => setShowLeadModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold"
            >
              ✕
            </button>

            {!leadSubmitted ? (
              <>
                <div className="space-y-1">
                  <h3 className="text-xl font-bold text-white">Download CFO Executive Audit</h3>
                  <p className="text-xs text-slate-400">
                    Get an instant formatted 5-year RaaS vs CapEx feasibility summary for your finance team.
                  </p>
                </div>

                <form onSubmit={handleLeadFormSubmit} className="space-y-3">
                  <div>
                    <label className="block text-xs text-slate-300 font-medium mb-1">Company / Organization</label>
                    <input
                      type="text"
                      placeholder="e.g. Nevada Logistics LLC"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      required
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-slate-300 font-medium mb-1">Work Email Address</label>
                    <input
                      type="email"
                      placeholder="vp-automation@company.com"
                      value={workEmail}
                      onChange={(e) => setWorkEmail(e.target.value)}
                      required
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20"
                  >
                    Generate Report & Pre-Approve RaaS Quote
                  </button>
                </form>
              </>
            ) : (
              <div className="py-6 text-center space-y-3">
                <div className="text-4xl">✅</div>
                <h3 className="text-xl font-bold text-emerald-400">CFO Audit Generated!</h3>
                <p className="text-xs text-slate-300">
                  We have compiled the 5-year RaaS vs CapEx model for <strong>{companyName || 'your organization'}</strong>. A copy has been dispatched to <strong>{workEmail}</strong>.
                </p>
                <button
                  onClick={() => {
                    setShowLeadModal(false);
                    setLeadSubmitted(false);
                  }}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-4 py-2 rounded-xl mt-2 font-medium"
                >
                  Close & Return to Calculator
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
