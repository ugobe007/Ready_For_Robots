import {
  ArrowRight,
  BarChart3,
  CheckCircle,
  Search,
  Target,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { Link } from "wouter";
import { formatStat } from "@/hooks/usePipelineStats";
import { HeatBadge } from "@/components/marketing/primitives";

type BenchReport = {
  total_robots?: number;
  overall_leader?: { name?: string; vendor?: string; score?: number };
};

type StatsProps = {
  hotCount: number | null;
  totalCount: number | null;
};

export function MarketingWhatSignalDoes({ hotCount, totalCount }: StatsProps) {
  const totalLabel = formatStat(totalCount, "3,957");
  const features = [
    {
      icon: Search,
      title: "Discover",
      description:
        "Automation-ready buyers — timing, intent, and fit from live market signals. 150+ sources scanned 24/7.",
      stat: "150+",
      statLabel: "live sources",
    },
    {
      icon: BarChart3,
      title: "Develop",
      description:
        "Signal briefs and tailored outreach for each account. Every company scored on fit and timing.",
      stat: totalLabel,
      statLabel: "active signals",
    },
    {
      icon: TrendingUp,
      title: "Close",
      description:
        "Advance deals through follow-ups, re-engagement, and meeting-ready intelligence — from first signal to signed contract.",
      stat: "62%",
      statLabel: "strong buying intent",
    },
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-3">What ReadyForRobots SIGNAL Does</p>
          <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight">
            Discover, develop, and close
            <br />
            robot sales — from one system.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="p-7 rounded-xl border border-gray-100 border-l-4 border-l-emerald-500 shadow-sm hover:shadow-md transition-shadow duration-200"
              >
                <div className="flex items-start justify-between mb-5">
                  <div className="w-11 h-11 bg-emerald-50 rounded-lg flex items-center justify-center">
                    <Icon size={22} className="text-emerald-600" />
                  </div>
                  <div className="text-right">
                    <div className="score-number text-2xl">{f.stat}</div>
                    <div className="text-gray-500 text-xs font-mono-data">{f.statLabel}</div>
                  </div>
                </div>
                <h3 className="font-display text-xl font-bold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-600 leading-relaxed text-sm">{f.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function MarketingHowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Discover",
      description:
        "150+ sources scanned 24/7 for labor shortages, expansion, CapEx, and hiring patterns that indicate robot-ready buyers.",
      icon: Search,
    },
    {
      num: "02",
      title: "Develop",
      description:
        "Every company is scored on fit and timing, then developed with signal-specific briefs and trigger-aware outreach drafts.",
      icon: Target,
    },
    {
      num: "03",
      title: "Close",
      description:
        "Pipeline advances through follow-ups, re-engagement, and meeting-ready intelligence — from first signal to signed deal.",
      icon: TrendingUp,
    },
  ];

  return (
    <section id="how-it-works" className="py-20 bg-slate-50">
      <div className="container">
        <div className="mb-14">
          <p className="section-eyebrow mb-3">How It Works</p>
          <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight max-w-xl">
            From signal to signed deal — automated.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <div key={step.num} className="relative">
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-[calc(100%-1rem)] w-8 h-px bg-gray-200 z-10" />
                )}
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-emerald-600 rounded-xl flex items-center justify-center shadow-sm">
                      <Icon size={20} className="text-white" />
                    </div>
                  </div>
                  <div>
                    <div className="font-mono-data text-xs text-gray-500 font-semibold mb-1">{step.num}</div>
                    <h3 className="font-display text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{step.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function MarketingBeforeAfter() {
  const before = [
    "Cold lists with no context",
    "Reach out and hope for the right timing",
    "Generic email templates",
    "3% reply rate on cold outreach",
    "Find out about deals after the RFP drops",
    "SDR spends 70% of time prospecting",
    "No visibility into partnership opportunities",
  ];
  const after = [
    "Signal-triggered outreach with exact buying reason",
    "Contact during the decision window, not after",
    "Drafted message referencing their specific signal",
    "Warm conversations with buyers who have a real need",
    "Shape requirements before competitors know it exists",
    "SDR spends 100% of time on qualified conversations",
    "Signal surfaces integrators and channel partners",
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container">
        <div className="mb-14">
          <p className="section-eyebrow mb-3">The Difference</p>
          <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight">
            Before vs. After ReadyForRobots
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-red-50 border border-red-100 rounded-2xl p-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-7 h-7 bg-red-100 rounded-full flex items-center justify-center">
                <XCircle size={16} className="text-red-500" />
              </div>
              <span className="font-display font-bold text-red-700 uppercase text-xs tracking-widest">
                Without SIGNAL
              </span>
            </div>
            <ul className="space-y-3">
              {before.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-gray-700">
                  <XCircle size={15} className="text-red-400 flex-shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-7 h-7 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle size={16} className="text-emerald-600" />
              </div>
              <span className="font-display font-bold text-emerald-700 uppercase text-xs tracking-widest">
                With SIGNAL
              </span>
            </div>
            <ul className="space-y-3">
              {after.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-gray-700">
                  <CheckCircle size={15} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingCaseStudies() {
  const cases = [
    {
      industry: "HOSPITALITY",
      outcome: "15-robot deployment",
      outcomeColor: "bg-emerald-100 text-emerald-700",
      signals: [
        '"Can\'t staff overnight shifts" + "40% housekeeping vacancy" in earnings call',
        "Reached out 4 months before RFP with overnight automation case study",
        "Shaped requirements, won pilot without competition",
      ],
    },
    {
      industry: "LOGISTICS",
      outcome: "$2.4M contract",
      outcomeColor: "bg-blue-100 text-blue-700",
      signals: [
        '"Opening 2 new DCs" + posting for "automation engineer"',
        "Contacted during facility design phase with layout recommendations",
        "Designed automation into new buildings",
      ],
    },
  ];

  return (
    <section id="case-studies" className="py-20 bg-slate-50">
      <div className="container">
        <div className="mb-14">
          <p className="section-eyebrow mb-3">Real Signals. Real Deals.</p>
          <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight">Close before the RFP.</h2>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          {cases.map((c) => (
            <div key={c.industry} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
              <div className="flex items-center justify-between mb-6">
                <span className="text-xs font-mono-data font-semibold text-gray-500 uppercase tracking-widest">
                  {c.industry}
                </span>
                <span className={`text-xs font-mono-data font-bold px-3 py-1 rounded-full ${c.outcomeColor}`}>
                  {c.outcome}
                </span>
              </div>
              <ul className="space-y-4">
                {c.signals.map((signal) => (
                  <li key={signal} className="text-sm text-gray-700 leading-relaxed">
                    {signal}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function MarketingTestimonials() {
  const testimonials = [
    {
      quote:
        "We reached the buyer 4 months before the RFP — and shaped the requirements. That deal would never have happened with a cold list.",
      name: "VP of Sales",
      company: "Warehouse AMR Company",
      outcome: "15-robot pilot",
      signal: "Labor shortage signal",
      signalScore: 94,
    },
    {
      quote:
        "ReadyForRobots found a $2.4M logistics opportunity we had zero visibility into. The signal was an earnings call mention — we never would have caught it manually.",
      name: "Director of Business Development",
      company: "Industrial Robotics OEM",
      outcome: "$2.4M contract",
      signal: "Expansion signal",
      signalScore: 88,
    },
    {
      quote:
        "Our SDR used to spend 3 days a week on prospecting. Now that time goes to closing. The pipeline quality is completely different.",
      name: "Head of Sales",
      company: "Service Robot Startup",
      outcome: "3x pipeline velocity",
      signal: "CapEx signal",
      signalScore: 81,
    },
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container">
        <div className="mb-14">
          <p className="section-eyebrow mb-3">From the Sales Floor</p>
          <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight">
            What sales teams are saying.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div key={t.name} className="bg-slate-50 rounded-2xl p-7 border border-gray-100 flex flex-col">
              <div className="flex items-center justify-between mb-5 pb-4 border-b border-gray-100">
                <span className="text-xs font-mono-data text-gray-500">{t.signal}</span>
                <div className="flex items-center gap-2">
                  <span className="score-number text-xl">{t.signalScore}</span>
                  <HeatBadge heat="HOT" />
                </div>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed flex-1 mb-6">{t.quote}</p>
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div>
                  <div className="font-display font-semibold text-gray-900 text-sm">{t.name}</div>
                  <div className="text-gray-500 text-xs">{t.company}</div>
                </div>
                <span className="text-xs font-mono-data font-bold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-100">
                  {t.outcome}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function MarketingBenchmark({ benchReport }: { benchReport: BenchReport | null }) {
  const total = benchReport?.total_robots ?? 109;
  const leader = benchReport?.overall_leader;
  const robots = leader?.name
    ? [{ name: leader.name, vendor: leader.vendor || "", score: leader.score ?? 79, status: "Leader" }]
    : [
        { name: "Hexagon AEON", vendor: "Hexagon Robotics", score: 79, status: "Pilot" },
        { name: "Neura 4NE1", vendor: "Neura Robotics", score: 79, status: "Available" },
        { name: "Tesla Optimus Gen 2", vendor: "Tesla", score: 77, status: "Pilot" },
      ];

  return (
    <section className="py-20 bg-slate-50">
      <div className="container">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <p className="section-eyebrow mb-3">Humanoid Intelligence</p>
            <h2 className="font-display text-4xl font-bold text-gray-900 tracking-tight mb-4">
              {total} humanoids benchmarked. Know your product landscape.
            </h2>
            <p className="text-gray-600 text-base leading-relaxed mb-6">
              The HEIR benchmark tracks humanoid robots across data pipeline, cognition, mobility, and deployment
              readiness. Updated monthly.
            </p>
            <Link href="/robots" className="inline-flex items-center gap-2 text-emerald-600 font-semibold text-sm hover:text-emerald-700">
              View full benchmark <ArrowRight size={16} />
            </Link>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <span className="font-display font-bold text-gray-900 text-sm">HEIR Benchmark Index</span>
              <span className="text-xs font-mono-data text-gray-500">June 2026</span>
            </div>
            <div>
              {robots.map((robot, i) => (
                <div
                  key={robot.name}
                  className="flex items-center gap-4 px-6 py-4 border-b border-gray-50 last:border-0 hover:bg-slate-50 transition-colors"
                >
                  <span className="font-mono-data text-gray-400 text-sm w-5 text-right flex-shrink-0">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-semibold text-gray-900 text-sm truncate">{robot.name}</div>
                    <div className="text-gray-500 text-xs">{robot.vendor}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="score-number text-xl">{robot.score}</span>
                    <span className="text-xs font-mono-data px-2 py-0.5 bg-slate-100 text-slate-500 rounded">
                      {robot.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingReportSection({ onOpenReport }: { onOpenReport: () => void }) {
  return (
    <section className="py-20 bg-white">
      <div className="container">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-10 lg:p-14 flex flex-col lg:flex-row items-center gap-10">
          <div className="flex-1">
            <p className="text-emerald-400 text-xs font-mono-data font-semibold uppercase tracking-widest mb-3">
              Market Intelligence
            </p>
            <h2 className="font-display text-3xl lg:text-4xl font-bold text-white tracking-tight mb-4">
              The 2026 Automation Imperative
            </h2>
            <p className="text-slate-400 text-base leading-relaxed mb-8 max-w-lg">
              Our enterprise intelligence report analyzes labor-intensive industries, robotics buying signals, and ROI
              benchmarks so sales teams know where automation demand is forming now.
            </p>
            <div className="grid grid-cols-3 gap-6 mb-8">
              {[
                { value: "158", label: "enterprises analyzed" },
                { value: "437", label: "buying signals detected" },
                { value: "62%", label: "strong buying intent" },
              ].map((stat) => (
                <div key={stat.label}>
                  <div className="font-mono-data font-bold text-3xl text-emerald-400 mb-1">{stat.value}</div>
                  <div className="text-slate-500 text-xs">{stat.label}</div>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={onOpenReport}
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-all duration-150 active:scale-[0.97] text-sm"
            >
              Download Free Report
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="flex-shrink-0 w-56 h-72 bg-slate-700/50 rounded-2xl border border-white/10 flex flex-col items-center justify-center p-6 text-center">
            <div className="text-xs font-mono-data text-slate-400 uppercase tracking-widest mb-3">
              Enterprise Intelligence Report
            </div>
            <div className="font-display font-bold text-white text-xl leading-tight mb-2">The Automation Imperative</div>
            <div className="text-slate-400 text-xs leading-relaxed mb-4">
              Labor shortages, capital availability, and leadership commitment are creating a 2026 inflection point for
              robotics adoption.
            </div>
            <div className="text-slate-500 text-xs font-mono-data">June 2026 · ReadyForRobots</div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingFinalCTA({ hotCount, totalCount }: StatsProps) {
  const hotLabel = formatStat(hotCount, "319");
  const totalLabel = formatStat(totalCount, "3,957");

  return (
    <section className="py-24 bg-slate-900">
      <div className="container text-center">
        <h2 className="font-display text-5xl font-bold text-white tracking-tight mb-4">
          Discover. Develop. Close robot deals.
        </h2>
        <div className="flex items-center justify-center gap-8 mb-8 flex-wrap">
          {[
            { value: hotLabel, label: "hot leads now" },
            { value: totalLabel, label: "active signals" },
            { value: "62%", label: "buying intent" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="score-number text-3xl text-emerald-400">{s.value}</div>
              <div className="text-slate-500 text-xs font-mono-data mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
        <p className="text-slate-400 text-base mb-10 max-w-md mx-auto">
          Robot sales automated to closure. HubSpot sync optional.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/results?url="
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition-all duration-150 active:scale-[0.97] shadow-lg text-base"
          >
            Find buyers
            <ArrowRight size={16} />
          </Link>
          <Link
            href="/pipeline"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white/10 hover:bg-white/15 text-white font-semibold rounded-xl border border-white/20 transition-all duration-150 active:scale-[0.97] text-base"
          >
            Browse the pipeline free
          </Link>
        </div>
        <p className="text-slate-600 text-xs mt-5 font-mono-data">
          No signup to scan · Free pipeline preview · Upgrade when you save leads
        </p>
      </div>
    </section>
  );
}
