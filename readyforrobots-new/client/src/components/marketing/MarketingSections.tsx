import {
  ArrowRight,
  BarChart3,
  CheckCircle,
  CheckCircle2,
  Cpu,
  FileText,
  Mail,
  Search,
  Shield,
  Target,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import { Link, useLocation } from "wouter";
import AnimatedStat, { statTarget } from "@/components/marketing/AnimatedStat";
import { HeatBadge } from "@/components/marketing/primitives";
import { checkoutLoginPath, signupHrefForCheckout } from "@/lib/authNext";

type BenchReport = {
  total_robots?: number;
  overall_leader?: { name?: string; vendor?: string; score?: number };
};

type StatsProps = {
  hotCount: number | null;
  totalCount: number | null;
};

export function MarketingWhatSignalDoes({ totalCount }: StatsProps) {
  const features = [
    {
      icon: Search,
      title: "Discover",
      description:
        "Automation-ready buyers from live timing, intent, and fit signals.",
      statValue: 150,
      statSuffix: "+",
      statLabel: "live sources",
      iconTone: "bg-sky-100 text-sky-700",
      railTone: "border-l-sky-500",
    },
    {
      icon: BarChart3,
      title: "Develop",
      description:
        "Signal briefs and outreach context for each account, scored by fit and timing.",
      statValue: statTarget(totalCount, 3957),
      statSuffix: "",
      statLabel: "active signals",
      iconTone: "bg-amber-100 text-amber-700",
      railTone: "border-l-amber-500",
    },
    {
      icon: TrendingUp,
      title: "Close",
      description:
        "Advance deals with follow-ups, re-engagement, and meeting-ready intelligence.",
      statValue: 62,
      statSuffix: "%",
      statLabel: "strong buying intent",
      iconTone: "bg-slate-100 text-slate-700",
      railTone: "border-l-slate-500",
    },
  ];

  return (
    <section className="py-12 lg:py-14 bg-white">
      <div className="container">
        <div className="text-center mb-8">
          <p className="section-eyebrow mb-3">What ReadyForRobots SIGNAL Does</p>
          <h2 className="section-headline font-bold text-gray-900">
            Discover, develop, and close robot sales.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4 lg:gap-5">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className={`rounded-xl border border-gray-200 border-l-4 p-5 shadow-sm transition-shadow duration-200 hover:shadow-md ${f.railTone}`}
              >
                <div className="mb-4 flex items-start justify-between">
                  <div className={`h-11 w-11 rounded-lg flex items-center justify-center ${f.iconTone}`}>
                    <Icon size={22} />
                  </div>
                  <div className="text-right">
                    <AnimatedStat
                      value={f.statValue}
                      suffix={f.statSuffix}
                      className="score-number text-2xl block"
                    />
                    <div className="text-gray-500 text-xs font-mono-data">{f.statLabel}</div>
                  </div>
                </div>
                <h3 className="mb-1.5 font-display text-xl font-bold text-gray-900">{f.title}</h3>
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
        "Continuous signal coverage spots labor, expansion, CapEx, and hiring patterns that indicate robot demand.",
      icon: Search,
      mockup: {
        kicker: "Signal detected",
        title: "Apex Logistics",
        lines: ["3 DC expansions · Midwest US", "Labor shortage filing · match"],
        accent: "text-sky-700",
        bar: 72,
      },
    },
    {
      num: "02",
      title: "Develop",
      description:
        "Each company is scored on fit and timing, then developed with signal-specific briefs and outreach drafts.",
      icon: Target,
      mockup: {
        kicker: "Fit score",
        title: "91 / 100",
        lines: ["Confidence 88 · Urgency 72", "Automation fit · warehouse AMR"],
        accent: "text-amber-600",
        bar: 91,
      },
    },
    {
      num: "03",
      title: "Close",
      description:
        "Pipeline advances with follow-ups and meeting-ready intelligence before the RFP is released.",
      icon: TrendingUp,
      mockup: {
        kicker: "Draft outreach",
        title: "Hi Sarah — saw Apex is expanding",
        lines: ["three DCs in Q3. We help 3PLs deploy", "AMRs before the RFP drops."],
        accent: "text-emerald-700",
        bar: 100,
      },
    },
  ];

  return (
    <section id="how-it-works" className="overflow-hidden bg-slate-100/70 py-14 lg:py-16">
      <div className="container">
        <div className="mb-8 max-w-2xl">
          <p className="section-eyebrow mb-3">How It Works</p>
          <h2 className="section-headline font-bold text-gray-900">
            From signal to signed deal — automated.
          </h2>
        </div>

        <div className="relative">
          <div
            className="hidden lg:block absolute top-[4.25rem] left-[12%] right-[12%] h-0.5 bg-gradient-to-r from-sky-300 via-amber-400 to-slate-400"
            aria-hidden
          />

          <div className="grid gap-6 lg:grid-cols-3 lg:gap-6">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={step.num} className="relative flex flex-col">
                  <div className="mb-4 flex flex-col items-center text-center">
                    <div className="relative z-10 mb-4">
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ring-4 ring-white shadow-lg ${
                        i === 0
                          ? "bg-sky-600 shadow-sky-500/25"
                          : i === 1
                            ? "bg-amber-500 shadow-amber-500/25"
                                : "bg-slate-700 shadow-slate-500/20"
                      }`}>
                        <Icon size={28} className="text-white" />
                      </div>
                      <span className={`absolute -top-2 -right-2 flex h-7 w-7 items-center justify-center rounded-full bg-white border font-mono-data text-[10px] font-bold shadow-sm ${
                        i === 0
                          ? "border-sky-200 text-sky-700"
                          : i === 1
                            ? "border-amber-200 text-amber-700"
                                : "border-slate-200 text-slate-700"
                      }`}>
                        {step.num}
                      </span>
                    </div>
                    <h3 className="font-display text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
                    <p className="max-w-xs text-sm leading-relaxed text-gray-600">{step.description}</p>
                  </div>

                  <div className="mt-auto rounded-xl border border-gray-200 bg-white p-3.5 shadow-sm">
                    <div className="mb-2.5 flex items-center justify-between gap-2 border-b border-gray-100 pb-2">
                      <span className="text-[10px] font-mono-data font-semibold uppercase tracking-widest text-slate-600">
                        {step.mockup.kicker}
                      </span>
                      <FileText size={14} className={`shrink-0 ${i === 0 ? "text-sky-500" : i === 1 ? "text-amber-500" : "text-slate-500"}`} />
                    </div>
                    <p className={`mb-1.5 text-sm font-semibold ${step.mockup.accent}`}>{step.mockup.title}</p>
                    <div className="space-y-1">
                      {step.mockup.lines.map((line) => (
                        <p key={line} className="text-xs text-gray-600 leading-relaxed font-mono-data">
                          {line}
                        </p>
                      ))}
                    </div>
                    <div className="mt-2.5 flex items-center gap-2">
                      <div className="signal-strength-track flex-1 max-w-none">
                        <div className="signal-strength-fill" style={{ width: `${step.mockup.bar}%` }} />
                      </div>
                      {i < steps.length - 1 && (
                        <span className="hidden lg:inline text-gray-300" aria-hidden>
                          →
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingBeforeAfter() {
  const before = [
    "105M-company search — still no idea who is buying robots now",
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
    <section className="before-after-section relative overflow-hidden">
      <div className="container relative">
        <div className="mb-10 max-w-2xl">
          <p className="section-eyebrow mb-3">The Difference</p>
          <h2 className="section-headline font-bold text-slate-900">
            Before vs. After ReadyForRobots
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            Same sales team — different pipeline when buyer intent leads the motion.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
          <div className="before-after-panel-before">
            <div className="before-after-panel-before-header">
              <span className="before-after-badge-before">Blind outreach</span>
            </div>
            <div className="before-after-panel-before-body">
              <div className="before-after-panel-label before-after-panel-label-before font-display">
                <XCircle size={16} className="text-red-600" aria-hidden />
                <span>Without SIGNAL</span>
              </div>
              <ul className="space-y-3">
                {before.map((item) => (
                  <li key={item} className="before-after-list-item before-after-list-item-before">
                    <XCircle size={15} className="text-red-500 flex-shrink-0 mt-0.5" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="before-after-panel-after">
            <div className="before-after-panel-after-header">
              <span className="before-after-badge-after">Signal-matched buyers</span>
            </div>
            <div className="before-after-panel-after-body">
              <div className="before-after-panel-label before-after-panel-label-after font-display">
                <CheckCircle size={16} className="text-emerald-700" aria-hidden />
                <span>With SIGNAL</span>
              </div>
              <ul className="space-y-3">
                {after.map((item) => (
                  <li key={item} className="before-after-list-item before-after-list-item-after">
                    <CheckCircle size={15} className="text-sky-600 flex-shrink-0 mt-0.5" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingVsGenericAI() {
  const rows = [
    {
      dumb: "Search 100M+ companies — no idea who's buying robots now",
      rfr: "Curated robot-buyer intent, ranked HOT / WARM / COLD by real events",
    },
    {
      dumb: '"CTO at a logistics company" — you guess the pitch',
      rfr: "robot_types_needed + the exact SKU to pitch on every lead",
    },
    {
      dumb: "Export a CSV, then go build your own stack",
      rfr: "Pipeline, Cal outreach drafts, and HubSpot sync — done for you",
    },
    {
      dumb: "Static lists that go stale the day you download them",
      rfr: "Live signals refreshed daily — contact in the buying window",
    },
  ];

  return (
    <section className="relative overflow-hidden bg-slate-900 py-16 lg:py-24">
      <div
        className="absolute inset-0 opacity-[0.4] pointer-events-none"
        aria-hidden
        style={{
          backgroundImage:
            "radial-gradient(circle at 15% 20%, rgba(56,189,248,0.18) 0%, transparent 45%), radial-gradient(circle at 85% 80%, rgba(245,158,11,0.18) 0%, transparent 40%)",
        }}
      />
      <div className="container relative">
        <div className="mb-10 max-w-2xl">
          <p className="section-eyebrow section-eyebrow-on-dark mb-3">Why not just use a generic AI tool?</p>
          <h2 className="section-headline font-bold text-white">
            Generic AI guesses.{" "}
            <span className="text-sky-300">SIGNAL knows who&apos;s buying robots.</span>
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            Horizontal &ldquo;AI&rdquo; search and data tools hand you a list. ReadyForRobots hands you a moving
            pipeline built for robot companies — verified buyer intent, the right SKU, and deals advancing in CRM.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4 lg:gap-5">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="mb-4 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-400">
              <XCircle size={15} className="text-red-400" aria-hidden />
              Generic AI &amp; data tools
            </p>
            <ul className="space-y-3">
              {rows.map((row) => (
                <li key={row.dumb} className="flex items-start gap-2.5 text-sm leading-relaxed text-slate-400">
                  <XCircle size={15} className="mt-0.5 flex-shrink-0 text-red-400/70" aria-hidden />
                  {row.dumb}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-sky-300/35 bg-sky-400/[0.08] p-5 shadow-[0_0_40px_-12px_rgba(56,189,248,0.45)]">
            <p className="mb-4 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-sky-200">
              <CheckCircle size={15} className="text-sky-300" aria-hidden />
              ReadyForRobots SIGNAL
            </p>
            <ul className="space-y-3">
              {rows.map((row) => (
                <li key={row.rfr} className="flex items-start gap-2.5 text-sm font-medium leading-relaxed text-slate-100">
                  <CheckCircle size={15} className="mt-0.5 flex-shrink-0 text-sky-300" aria-hidden />
                  {row.rfr}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
          <Link
            href="/compare"
            className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3 text-sm font-semibold text-slate-950 transition-all hover:bg-amber-400"
          >
            See the full comparison
            <ArrowRight size={14} />
          </Link>
          <Link
            href="/pipeline"
            className="inline-flex items-center gap-1 text-sm font-semibold text-slate-300 transition-colors hover:text-sky-200"
          >
            Browse the live pipeline free
          </Link>
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
      outcomeColor: "bg-amber-100 text-amber-700",
      signals: [
        '"Can\'t staff overnight shifts" + "40% housekeeping vacancy" in earnings call',
        "Reached out 4 months before RFP with overnight automation case study",
        "Shaped requirements, won pilot without competition",
      ],
    },
    {
      industry: "LOGISTICS",
      outcome: "$2.4M contract",
      outcomeColor: "bg-sky-100 text-sky-700",
      signals: [
        '"Opening 2 new DCs" + posting for "automation engineer"',
        "Contacted during facility design phase with layout recommendations",
        "Designed automation into new buildings",
      ],
    },
  ];

  return (
    <section id="case-studies" className="bg-white py-12 lg:py-14">
      <div className="container">
        <div className="mb-8">
          <p className="section-eyebrow mb-3">Real Signals. Real Deals.</p>
          <h2 className="section-headline font-bold text-gray-900 tracking-tight">Close before the RFP.</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:gap-5">
          {cases.map((c) => (
            <div key={c.industry} className="rounded-2xl border border-gray-200 bg-slate-50/70 p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-mono-data font-semibold text-gray-500 uppercase tracking-widest">
                  {c.industry}
                </span>
                <span className={`text-xs font-mono-data font-bold px-3 py-1 rounded-full ${c.outcomeColor}`}>
                  {c.outcome}
                </span>
              </div>
              <ul className="space-y-2.5">
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
    <section className="py-24 bg-slate-50/70">
      <div className="container">
        <div className="mb-14">
          <p className="section-eyebrow mb-3">From the Sales Floor</p>
          <h2 className="section-headline font-bold text-gray-900 tracking-tight">
            What sales teams are saying.
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div key={t.name} className="bg-slate-50 rounded-2xl p-7 border border-gray-100 flex flex-col">
              <div className="mb-5 pb-4 border-b border-gray-100">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <span className="text-xs font-mono-data text-gray-500">{t.signal}</span>
                  <HeatBadge heat="HOT" />
                </div>
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <span className="score-number text-2xl leading-none">{t.signalScore}</span>
                    <p className="text-[10px] font-mono-data text-gray-500 mt-1 uppercase tracking-wide">Signal strength</p>
                  </div>
                  <div className="signal-strength-track w-24">
                    <div className="signal-strength-fill" style={{ width: `${t.signalScore}%` }} />
                  </div>
                </div>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed flex-1 mb-6">{t.quote}</p>
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div>
                  <div className="font-display font-semibold text-gray-900 text-sm">{t.name}</div>
                  <div className="text-gray-500 text-xs">{t.company}</div>
                </div>
                <span className="text-xs font-mono-data font-bold px-2.5 py-1 bg-sky-50 text-sky-700 rounded-full border border-sky-100">
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
    <section className="py-16 lg:py-20 bg-slate-100/70">
      <div className="container">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <p className="section-eyebrow mb-3">Humanoid Intelligence</p>
            <h2 className="section-headline font-bold text-gray-900 tracking-tight mb-4">
              {total} humanoids benchmarked. Know your product landscape.
            </h2>
            <p className="text-gray-600 text-base leading-relaxed mb-6">
              The HEIR benchmark tracks humanoid robots across data pipeline, cognition, mobility, and deployment
              readiness. Updated monthly.
            </p>
            <Link href="/robots" className="inline-flex items-center gap-2 text-sky-700 font-semibold text-sm hover:text-sky-800">
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
                  className={`flex items-center gap-4 px-6 py-4 border-b border-gray-100 last:border-0 transition-colors ${
                    i % 2 === 0 ? "bg-white hover:bg-slate-50" : "bg-slate-50/80 hover:bg-slate-100/80"
                  }`}
                >
                  <span className="font-mono-data text-gray-900 text-sm font-bold w-5 text-right flex-shrink-0">{i + 1}</span>
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
    <section className="py-24 bg-white">
      <div className="container">
        <div className="rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-sky-950 p-10 lg:p-14 flex flex-col lg:flex-row items-center gap-10">
          <div className="flex-1">
            <p className="text-amber-300 text-xs font-mono-data font-semibold uppercase tracking-widest mb-3">
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
                  <div className="font-mono-data font-bold text-3xl text-sky-300 mb-1">{stat.value}</div>
                  <div className="text-slate-500 text-xs">{stat.label}</div>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={onOpenReport}
              className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl transition-all duration-150 active:scale-[0.97] text-sm"
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

const HOME_PRICING_TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    tagline: "Browse the live pipeline — no card required",
    icon: Zap,
    accent: "border-gray-200",
    iconBg: "bg-sky-50 text-sky-600",
    cta: "Start free",
    href: "/signup?plan=free&next=%2Fpipeline",
    features: ["URL scan & buyer matching", "10 live pipeline leads", "Save up to 5 leads"],
    highlight: false,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/mo",
    tagline: "Full pipeline + SIGNAL research for active sellers",
    icon: Cpu,
    accent: "border-sky-300 ring-1 ring-sky-200 shadow-lg shadow-sky-100/50",
    iconBg: "bg-amber-50 text-amber-600",
    cta: "Upgrade to Pro",
    href: checkoutLoginPath("pro"),
    checkoutTier: "pro" as const,
    features: ["Unlimited saved leads", "SIGNAL research on HOT/WARM", "HubSpot auto-sync"],
    highlight: true,
    badge: "Most popular",
  },
  {
    name: "Enterprise",
    price: "$129",
    period: "/mo",
    tagline: "Teams ready to act on more accounts",
    icon: Shield,
    accent: "border-gray-200",
    iconBg: "bg-slate-100 text-slate-700",
    cta: "Talk to sales",
    href: "mailto:sales@readyforrobots.com?subject=Enterprise%20workspace%20inquiry",
    external: true,
    features: ["Priority research coverage", "Team workflow", "Priority support"],
    highlight: false,
  },
] as const;

export function MarketingPricing() {
  const [, setLocation] = useLocation();

  return (
    <section id="pricing" className="pricing-dark-section py-16 lg:py-20">
      <div className="container relative">
        <div className="text-center mb-12 max-w-2xl mx-auto">
          <p className="section-eyebrow section-eyebrow-on-dark mb-3">Pricing</p>
          <h2 className="section-headline font-bold text-white mb-3">
            Simple plans for robot sales teams
          </h2>
          <p className="text-sm text-slate-400">
            Start free — scan URLs, browse the pipeline, upgrade when you need research and CRM sync.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5 max-w-5xl mx-auto mb-8">
          {HOME_PRICING_TIERS.map((tier) => {
            const Icon = tier.icon;
            const cardClass = tier.highlight ? "pricing-glass-card-pro" : "pricing-glass-card";
            return (
              <div
                key={tier.name}
                className={`${cardClass} ${tier.highlight ? "md:-translate-y-1" : ""}`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-950 shadow-[0_4px_14px_-4px_rgba(16,185,129,0.7)]">
                    {tier.badge}
                  </div>
                )}
                <div className="flex items-center gap-2.5 mb-4 mt-1">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                    tier.highlight
                      ? "bg-emerald-400/15 text-emerald-300"
                      : "bg-white/8 text-slate-300"
                  }`}>
                    <Icon size={18} />
                  </div>
                  <span className="font-display font-bold text-slate-100">{tier.name}</span>
                </div>
                <div className="mb-2 flex items-baseline gap-1">
                  <span className={`font-mono-data text-3xl font-bold ${tier.highlight ? "text-emerald-300" : "text-slate-100"}`}>{tier.price}</span>
                  {tier.period && <span className="text-sm text-slate-500">{tier.period}</span>}
                </div>
                <p className="text-xs text-slate-400 mb-5 leading-relaxed">{tier.tagline}</p>
                <ul className="space-y-2 mb-6 flex-1">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-xs text-slate-300">
                      <CheckCircle2 size={14} className={`shrink-0 mt-0.5 ${tier.highlight ? "text-emerald-400" : "text-sky-400"}`} />
                      {feature}
                    </li>
                  ))}
                </ul>
                {"external" in tier && tier.external ? (
                  <a
                    href={tier.href}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/[0.06] px-4 py-2.5 text-sm font-semibold text-slate-200 transition-all hover:bg-white/10 hover:text-white"
                  >
                    {tier.cta}
                    <ArrowRight size={14} />
                  </a>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      if ("checkoutTier" in tier && tier.checkoutTier) {
                        window.location.assign(signupHrefForCheckout(tier.checkoutTier));
                        return;
                      }
                      setLocation(tier.href);
                    }}
                    className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all active:scale-[0.98] ${
                      tier.highlight
                        ? "bg-gradient-to-b from-emerald-400 to-emerald-500 text-slate-950 font-bold shadow-[0_6px_20px_-6px_rgba(16,185,129,0.65)] hover:from-emerald-300 hover:to-emerald-400"
                        : "border border-white/15 bg-white/[0.06] text-slate-200 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {tier.cta}
                    <ArrowRight size={14} />
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-slate-500">
          Month-to-month when billing is enabled.{" "}
          <Link href="/pricing" className="font-semibold text-emerald-400 hover:text-emerald-300">
            Compare all features →
          </Link>
        </p>
      </div>
    </section>
  );
}

export function MarketingFinalCTA({ hotCount, totalCount }: StatsProps) {
  const hotTarget = statTarget(hotCount, 319);
  const totalTarget = statTarget(totalCount, 3957);

  return (
    <section className="cta-section-bg relative overflow-hidden py-24">
      {/* Glow orbs */}
      <div className="pointer-events-none absolute -top-20 left-[10%] h-64 w-64 rounded-full bg-emerald-500/[0.12] blur-[70px]" aria-hidden />
      <div className="pointer-events-none absolute bottom-[-4rem] right-[8%] h-72 w-72 rounded-full bg-sky-500/[0.09] blur-[80px]" aria-hidden />
      <div className="container relative text-center">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/[0.07] px-3.5 py-1.5 text-[11px] font-semibold text-emerald-200 shadow-[0_0_24px_-8px_rgba(16,185,129,0.4)]">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.9)]" />
          Live pipeline · updated daily
        </div>
        <h2 className="font-display text-4xl lg:text-5xl font-bold text-white tracking-tight mb-6" style={{ textWrap: "balance" } as React.CSSProperties}>
          Discover. Develop. Close robot deals.
        </h2>
        <div className="flex items-center justify-center gap-8 mb-8 flex-wrap">
          {[
            { value: hotTarget, suffix: "", label: "hot leads now" },
            { value: totalTarget, suffix: "", label: "active signals" },
            { value: 62, suffix: "%", label: "buying intent" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <AnimatedStat
                value={s.value}
                suffix={s.suffix}
                className="score-number text-3xl text-emerald-300 block drop-shadow-[0_0_16px_rgba(52,211,153,0.5)]"
              />
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
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-b from-emerald-400 to-emerald-500 text-slate-950 font-bold rounded-xl transition-all duration-150 active:scale-[0.97] shadow-[0_8px_28px_-8px_rgba(16,185,129,0.7)] hover:from-emerald-300 hover:to-emerald-400 hover:shadow-[0_10px_32px_-8px_rgba(16,185,129,0.85)] text-base"
          >
            Find buyers
            <ArrowRight size={16} />
          </Link>
          <Link
            href="/pipeline"
            className="inline-flex items-center justify-center gap-1 text-sm font-semibold text-slate-300 transition-colors hover:text-white"
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

type NewsletterBandProps = {
  newsletterEmail: string;
  newsletterStatus: "idle" | "submitting" | "success" | "error";
  onEmailChange: (v: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
};

export function MarketingNewsletterBand({
  newsletterEmail,
  newsletterStatus,
  onEmailChange,
  onSubmit,
}: NewsletterBandProps) {
  return (
    <section className="relative overflow-hidden bg-slate-950 border-t border-white/5">
      <div
        className="absolute inset-0 opacity-40 pointer-events-none"
        aria-hidden
        style={{
          backgroundImage:
            "radial-gradient(ellipse 70% 80% at 50% 0%, rgba(56,189,248,0.22), transparent 60%)",
        }}
      />
      <div className="container relative py-16 lg:py-20">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-400/35 text-amber-300 text-xs font-mono-data font-semibold uppercase tracking-widest mb-6">
            <Mail size={14} />
            Weekly brief
          </div>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-white tracking-tight mb-4 leading-tight">
            Get the Weekly Robot Intelligence Brief
          </h2>
          <p className="text-slate-400 text-base leading-relaxed mb-8 max-w-xl mx-auto">
            Buying signals, deployment moves, and strategic hires — curated daily for robotics sales teams. Free.
          </p>
          <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3 max-w-lg mx-auto">
            <input
              type="email"
              value={newsletterEmail}
              onChange={(e) => onEmailChange(e.target.value)}
              placeholder="work email"
              required
              className="flex-1 min-w-0 px-4 py-3.5 bg-white/[0.06] border border-white/15 rounded-xl text-white text-sm placeholder-slate-500 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur-sm focus:outline-none focus:border-emerald-300/70 focus:ring-2 focus:ring-emerald-300/20 transition-all"
            />
            <button
              type="submit"
              disabled={newsletterStatus === "submitting"}
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-b from-emerald-400 to-emerald-500 text-slate-950 font-bold rounded-xl transition-all disabled:opacity-50 shadow-[0_6px_20px_-6px_rgba(16,185,129,0.65)] hover:from-emerald-300 hover:to-emerald-400 hover:shadow-[0_8px_24px_-6px_rgba(16,185,129,0.8)] active:scale-[0.97]"
            >
              {newsletterStatus === "submitting" ? "Subscribing…" : "Subscribe free"}
              <Zap size={16} />
            </button>
          </form>
          {newsletterStatus === "success" && (
            <p className="text-sky-300 text-sm mt-4 font-medium">You&apos;re subscribed — check your inbox.</p>
          )}
          {newsletterStatus === "error" && (
            <p className="text-red-400 text-sm mt-4">Could not subscribe. Try again.</p>
          )}
          <Link
            href="/newsletter"
            className="inline-flex items-center gap-1.5 mt-6 text-sm text-slate-500 hover:text-sky-300 transition-colors"
          >
            Read today&apos;s edition <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </section>
  );
}
