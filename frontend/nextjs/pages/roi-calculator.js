/**
 * Ready For Robots — ROI & RaaS vs. CapEx Financial Engine
 * 
 * High-converting enterprise portal evaluating 5-year RaaS ($8,500/mo) vs. CapEx ($200k)
 * unit economics against human labor across 1, 2, and 3-shift warehouse operations.
 */
import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import RrSiteLayout from '../components/RrSiteLayout';
import RaasVsCapexCalculator from '../components/RaasVsCapexCalculator';

export default function ROICalculatorPage() {
  const [activeTab, setActiveTab] = useState('raas-engine'); // 'raas-engine' | 'traditional'

  const handleLeadCapture = (leadData) => {
    console.log('RaaS Financial Engine Lead Captured:', leadData);
  };

  return (
    <RrSiteLayout active="roi">
      <Head>
        <title>RaaS vs. CapEx Robot ROI Calculator | Ready For Robots</title>
        <meta
          name="description"
          content="Calculate 5-year RaaS ($8,500/mo) vs. CapEx ($200k) unit economics, shift multipliers, and speed parity for Agility Digit, Apptronik Apollo, and warehouse automation."
        />
        <meta property="og:title" content="RaaS vs. CapEx Robot ROI Calculator | Ready For Robots" />
        <meta
          property="og:description"
          content="Evaluate 1-shift vs 3-shift operational ROI, pick-speed parity, and pre-approved RaaS leasing options for enterprise robotics."
        />
      </Head>

      <div className="bg-slate-950 text-slate-100 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-8">
          
          {/* Hero Banner */}
          <div className="text-center space-y-4 max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
              <span>📊 Strategic Procurement & Sales Enablement</span>
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
              RaaS vs. CapEx <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">Robot Financial Engine</span>
            </h1>
            <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
              Agility's public numbers ($8,500/mo RaaS vs $200k CapEx) prove that robotics is now a financial ROI calculation. Run instant 5-year Net Present Value audits across 1, 2, and 3-shift operations.
            </p>

            {/* Sub-navigation tabs */}
            <div className="inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium mt-4">
              <button
                type="button"
                onClick={() => setActiveTab('raas-engine')}
                className={`px-5 py-2.5 rounded-lg transition-all ${
                  activeTab === 'raas-engine'
                    ? 'bg-emerald-500 text-slate-950 font-bold shadow-lg'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                ⚡ RaaS ($8,500/mo) vs CapEx Engine
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('market-benchmarks')}
                className={`px-5 py-2.5 rounded-lg transition-all ${
                  activeTab === 'market-benchmarks'
                    ? 'bg-emerald-500 text-slate-950 font-bold shadow-lg'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                📈 Industry RaaS Benchmarks
              </button>
            </div>
          </div>

          {/* Primary Tool Tab: Interactive RaaS Engine */}
          {activeTab === 'raas-engine' && (
            <div>
              <RaasVsCapexCalculator onLeadCapture={handleLeadCapture} />
            </div>
          )}

          {/* Secondary Tab: Industry RaaS Benchmarks */}
          {activeTab === 'market-benchmarks' && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-6">
              <div className="space-y-2">
                <h3 className="text-2xl font-bold text-white">2026 Commercial Robotics Pricing & RaaS Benchmarks</h3>
                <p className="text-slate-400 text-sm">
                  Disclosed pricing models across humanoids, logistics AMRs, and collaborative robot arms.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  {
                    name: 'Agility Robotics — Digit',
                    category: 'Humanoid',
                    raas: '$8,500 / month',
                    raasSetup: '$25,000 deployment',
                    capex: '$200,000 purchase',
                    maint: '$36,000 / year',
                    parity: '50% Speed (0.50 FTE)',
                    badge: 'Disclosed Pricing',
                  },
                  {
                    name: 'Apptronik — Apollo',
                    category: 'Humanoid',
                    raas: '$7,800 / month',
                    raasSetup: '$22,000 deployment',
                    capex: '$185,000 purchase',
                    maint: '$32,000 / year',
                    parity: '55% Speed (0.55 FTE)',
                    badge: 'Disclosed Pricing',
                  },
                  {
                    name: 'Heavy Logistics AMR / AGV',
                    category: 'AMR Fleet',
                    raas: '$3,800 / month',
                    raasSetup: '$10,000 deployment',
                    capex: '$95,000 purchase',
                    maint: '$12,000 / year',
                    parity: '90% Speed (0.90 FTE)',
                    badge: 'Market Estimate',
                  },
                  {
                    name: 'Collaborative Arm (Cobot)',
                    category: 'Cobot',
                    raas: '$2,200 / month',
                    raasSetup: '$5,000 deployment',
                    capex: '$45,000 purchase',
                    maint: '$6,000 / year',
                    parity: '80% Speed (0.80 FTE)',
                    badge: 'Market Estimate',
                  },
                ].map((b, idx) => (
                  <div key={idx} className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {b.category}
                      </span>
                      <span className="text-[10px] text-slate-500">{b.badge}</span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{b.name}</h4>
                    <div className="space-y-1 text-xs text-slate-300 font-mono pt-2 border-t border-slate-800">
                      <div><strong className="text-emerald-400">RaaS:</strong> {b.raas}</div>
                      <div><strong className="text-slate-400">Setup:</strong> {b.raasSetup}</div>
                      <div><strong className="text-cyan-400">CapEx:</strong> {b.capex}</div>
                      <div><strong className="text-slate-400">Speed:</strong> {b.parity}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Value Prop Cards for Enterprise Buyers & OEM Sales Teams */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-2">
              <div className="text-2xl">🏭</div>
              <h3 className="text-base font-bold text-white">For Enterprise CFOs & 3PLs</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Replaces manual feasibility consulting with instant 5-year NPV audits, shift thresholds, and speed parity adjustments.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-2">
              <div className="text-2xl">⚡</div>
              <h3 className="text-base font-bold text-white">For OEM Sales Teams</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate co-branded, CFO-ready ROI reports for enterprise prospects in 5 minutes instead of 6 weeks of application engineering.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-2">
              <div className="text-2xl">💳</div>
              <h3 className="text-base font-bold text-white">Pre-Approved RaaS Leasing</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Direct integration with institutional equipment financiers (DLL Group, Mitsubishi HC Capital) for instant lease underwriting.
              </p>
            </div>
          </div>

          {/* Quick Navigation Footer */}
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 border-t border-slate-800 pt-6">
            <span>Ready For Robots — Strategic Capability & ROI Engine</span>
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="hover:text-emerald-400">Dashboard</Link>
              <Link href="/robot-ready" className="hover:text-emerald-400">Robot Use-Case Match</Link>
              <Link href="/market-insights" className="hover:text-emerald-400">Market Insights</Link>
            </div>
          </div>

        </div>
      </div>
    </RrSiteLayout>
  );
}
