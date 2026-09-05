/**
 * Case Studies — ReadyForRobots
 * Three detailed fictional case studies showing signal → outreach → outcome.
 */
import { Link } from "wouter";
import Header from "@/components/Header";
import { ArrowRight, TrendingUp, Clock, DollarSign, Users } from "lucide-react";

const CASES = [
  {
    id: "midwest-3pl",
    tag: "Warehouse AMR",
    company: "Midwest 3PL operator (confidential)",
    outcome: "$1.4M pilot contract",
    timeToClose: "11 weeks",
    leadTime: "5 months before RFP",
    color: "#03DAC5",
    signal: {
      type: "Facility expansion + labor shortage",
      detail: "SCOUT detected a combination of signals: a commercial real estate permit for a 280,000 sq ft DC expansion in Columbus, OH, followed by 14 warehouse associate job postings on Indeed over 3 weeks, and a mention in the CEO's LinkedIn post about 'scaling operations while managing headcount costs.'",
    },
    action: {
      title: "Outreach before the RFP",
      detail: "The robot company's SDR reached out to the VP of Operations 5 months before the company issued a formal RFP. The outreach referenced the Columbus expansion specifically and offered a site assessment. The VP responded within 48 hours.",
    },
    result: {
      title: "Shaped the requirements",
      detail: "By engaging early, the robot company participated in the requirements definition process. When the RFP was issued 5 months later, the spec reflected their product's strengths. They won the pilot against two competitors who entered at the RFP stage.",
    },
    quote: "We reached the buyer 4 months before the RFP — and shaped the requirements. That deal would never have happened with a cold list.",
    quoteName: "VP of Sales, Warehouse AMR Company",
  },
  {
    id: "food-processing",
    tag: "Food & Beverage Automation",
    company: "Regional food processing group (confidential)",
    outcome: "$2.4M automation contract",
    timeToClose: "18 weeks",
    leadTime: "7 months before announcement",
    color: "#a78bfa",
    signal: {
      type: "Earnings call + FDA filing",
      detail: "SCOUT flagged a Q3 earnings call transcript where the CFO mentioned 'significant investment in process automation to address margin compression.' Three weeks later, an FDA facility registration update showed a new production line at their Texas plant. Neither signal was individually decisive — the combination was.",
    },
    action: {
      title: "Precision outreach to the right buyer",
      detail: "SCOUT identified the Director of Manufacturing Engineering (not the VP of Operations) as the likely decision-maker for automation equipment. The outreach referenced the earnings call language directly: 'I noticed your CFO mentioned process automation investment — we work with food processors on exactly this.' The director replied the same day.",
    },
    result: {
      title: "Exclusive evaluation",
      detail: "The robot company entered an exclusive 60-day evaluation period before the company opened the process to other vendors. By the time competitors were invited, the robot company had already completed a successful pilot on one line and had a champion inside the organization.",
    },
    quote: "ReadyForRobots found a $2.4M logistics opportunity we had zero visibility into. The signal was an earnings call mention — we never would have caught it manually.",
    quoteName: "Director of Business Development, Industrial Robotics OEM",
  },
  {
    id: "service-robot-startup",
    tag: "Service Robots",
    company: "National hotel chain (confidential)",
    outcome: "12-property deployment",
    timeToClose: "9 weeks",
    leadTime: "3 months before budget cycle",
    color: "#f87171",
    signal: {
      type: "Glassdoor reviews + job posting pattern",
      detail: "SCOUT detected a cluster of Glassdoor reviews at multiple hotel properties mentioning 'overnight staffing shortages' and 'management struggling to fill housekeeping shifts.' Simultaneously, the chain posted 40+ housekeeping roles across 12 properties in a single week — a pattern consistent with a systemic staffing problem, not normal turnover.",
    },
    action: {
      title: "Outreach to the right level",
      detail: "Rather than contacting individual property managers, SCOUT identified the VP of Hotel Operations at the corporate level as the decision-maker for technology investments across properties. The outreach framed the robot as a staffing solution, not a technology purchase — matching the language in the Glassdoor reviews exactly.",
    },
    result: {
      title: "Pilot → full deployment",
      detail: "A 2-property pilot was approved within 3 weeks of first contact. The pilot ran during the chain's Q4 budget cycle, which meant results were available when the annual budget was being set. The chain approved a 12-property deployment as a line item in the following year's budget.",
    },
    quote: "Our SDR used to spend 3 days a week on prospecting. Now that time goes to closing. The pipeline quality is completely different.",
    quoteName: "Head of Sales, Service Robot Startup",
  },
];

export default function CaseStudies() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      {/* ── HERO ── */}
      <section className="pt-32 pb-16 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-8">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: "#7c3aed" }} />
            <span className="text-xs font-bold uppercase tracking-[0.15em]" style={{ color: "#c4b5fd" }}>
              Case Studies
            </span>
          </div>
          <h1
            className="font-extrabold leading-[1.05] tracking-tight mb-5 text-white"
            style={{ fontSize: "clamp(2.2rem, 4.5vw, 3.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            Signal → outreach → outcome.
          </h1>
          <p className="text-lg text-white/50 leading-relaxed max-w-2xl" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Three examples of how robotics companies used SCOUT to reach buyers before competitors — and what happened next.
          </p>
          <p className="text-xs text-white/25 mt-3" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Company names are confidential. Deal details are representative of real outcomes.
          </p>
        </div>
      </section>

      {/* ── CASE STUDIES ── */}
      <div className="px-6 pb-20">
        <div className="max-w-4xl mx-auto space-y-12">
          {CASES.map((c, i) => (
            <article
              key={c.id}
              className="rounded-2xl border overflow-hidden"
              style={{ background: "rgba(255,255,255,0.02)", borderColor: `${c.color}20` }}
            >
              {/* Header */}
              <div
                className="px-6 py-5 border-b"
                style={{ background: `${c.color}08`, borderColor: `${c.color}15` }}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <span
                      className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full mb-2 inline-block"
                      style={{ background: `${c.color}15`, color: c.color }}
                    >
                      {c.tag}
                    </span>
                    <h2 className="text-lg font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                      {c.company}
                    </h2>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {[
                      { icon: DollarSign, label: "Outcome", value: c.outcome },
                      { icon: Clock, label: "Time to close", value: c.timeToClose },
                      { icon: TrendingUp, label: "Lead time", value: c.leadTime },
                    ].map((stat) => {
                      const Icon = stat.icon;
                      return (
                        <div
                          key={stat.label}
                          className="text-right px-3 py-2 rounded-lg"
                          style={{ background: "rgba(255,255,255,0.04)" }}
                        >
                          <p className="text-[9px] text-white/30 uppercase tracking-widest">{stat.label}</p>
                          <p className="text-sm font-bold" style={{ color: c.color, fontFamily: "'JetBrains Mono', monospace" }}>
                            {stat.value}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Steps */}
              <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                {[
                  { step: "01", label: "The signal", title: c.signal.type, detail: c.signal.detail },
                  { step: "02", label: "The action", title: c.action.title, detail: c.action.detail },
                  { step: "03", label: "The result", title: c.result.title, detail: c.result.detail },
                ].map((s) => (
                  <div key={s.step} className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span
                        className="text-[10px] font-bold font-mono"
                        style={{ color: c.color, fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {s.step}
                      </span>
                      <span className="text-[9px] font-bold uppercase tracking-widest text-white/25">{s.label}</span>
                    </div>
                    <h3 className="text-sm font-bold text-white mb-2" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                      {s.title}
                    </h3>
                    <p className="text-xs text-white/40 leading-relaxed" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                      {s.detail}
                    </p>
                  </div>
                ))}
              </div>

              {/* Quote */}
              <div
                className="px-6 py-4 border-t"
                style={{ background: "rgba(255,255,255,0.015)", borderColor: "rgba(255,255,255,0.05)" }}
              >
                <blockquote className="flex gap-3 items-start">
                  <span className="text-2xl leading-none mt-0.5" style={{ color: c.color, opacity: 0.5 }}>"</span>
                  <div>
                    <p className="text-sm text-white/60 italic leading-relaxed" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                      {c.quote}
                    </p>
                    <p className="text-[10px] text-white/30 mt-1.5" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                      — {c.quoteName}
                    </p>
                  </div>
                </blockquote>
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* ── CTA ── */}
      <section className="py-20 px-6 border-t" style={{ background: "#0d0520", borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
            See what SCOUT finds for your company
          </h2>
          <p className="text-white/40 mb-8 text-sm" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Enter your robot company URL and get a sample of matched opportunities in seconds — no signup required.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-bold px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5"
            style={{ background: "#03DAC5", color: "#000", boxShadow: "0 8px 24px rgba(3,218,197,0.25)" }}
          >
            Try SCOUT free <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
