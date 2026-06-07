/**
 * How It Works — ReadyForRobots
 * Hero: SCOUT in motion + synced 5-step rail. Process: Supabase-style inline prose.
 */

import Header from "@/components/Header";
import ScoutHeroShowcase from "@/components/ScoutHeroShowcase";
import { Link } from "wouter";
import {
  Zap, Shield, Clock, ArrowRight,
  Briefcase, BarChart3, AlertTriangle, Building2,
  Newspaper, Activity, Globe, MapPin,
} from "lucide-react";

const processSteps: {
  title: string;
  body: string;
  pills?: string[];
}[] = [
  {
    title: "Signal detection",
    body: "SCOUT monitors OSHA filings, job postings, SEC disclosures, LinkedIn activity, press, permits, and dozens of other public sources — continuously, so your team does not have to.",
    pills: ["150+ sources", "24/7"],
  },
  {
    title: "AI scoring",
    body: "Every signal is scored on Confidence, Urgency, and Fit. Only opportunities at or above the threshold enter your pipeline — noise stays out.",
    pills: ["score ≥ 70"],
  },
  {
    title: "SCOUT drafts outreach",
    body: "For each qualified signal, SCOUT writes a subject line, opening hook, and call to action tied to the exact trigger event — expansion, filing, hire, CapEx, or pilot news.",
    pills: ["<2 min to draft"],
  },
  {
    title: "You review",
    body: "Choose how much automation you want: Manual (you send everything), Assisted (SCOUT drafts, you approve), or Auto (high-confidence signals send after a short review window).",
    pills: ["Manual", "Assisted", "Auto"],
  },
  {
    title: "Pipeline advances",
    body: "Replies, opens, and engagement feed back into the pipeline. SCOUT schedules follow-ups and can escalate technical questions so deals keep moving.",
  },
];

const sources = [
  { icon: Briefcase, label: "Job Postings", sub: "LinkedIn · Indeed · ZipRecruiter" },
  { icon: BarChart3, label: "Earnings Calls", sub: "SEC filings · CapEx announcements" },
  { icon: AlertTriangle, label: "OSHA Filings", sub: "Safety incidents · Workers' comp" },
  { icon: Building2, label: "Real Estate", sub: "Permits · Lease filings · Expansions" },
  { icon: Newspaper, label: "Press Releases", sub: "News · PR Newswire · Business Wire" },
  { icon: Activity, label: "Intent Signals", sub: "RFP databases · Automation searches" },
  { icon: Globe, label: "Web Signals", sub: "Careers pages · Tech stack changes" },
  { icon: MapPin, label: "Local Data", sub: "Permits · Zoning · Construction starts" },
  { icon: BarChart3, label: "Trade Publications", sub: "Industry journals · Analyst reports" },
  { icon: Building2, label: "Facility Expansions", sub: "New sites · Capacity increases" },
  { icon: AlertTriangle, label: "Safety Incidents", sub: "OSHA 300 logs · Inspection reports" },
  { icon: Briefcase, label: "CapEx Announcements", sub: "Capital expenditure filings · Budgets" },
];

const scoreDimensions = [
  { label: "Confidence", sublabel: "Source reliability & corroboration", value: 88, color: "#a78bfa" },
  { label: "Urgency", sublabel: "Decision window & buying intent", value: 72, color: "#818cf8" },
  { label: "Fit", sublabel: "ICP match & company profile", value: 95, color: "#7c3aed" },
];

const autonomyModes = [
  {
    mode: "Manual",
    icon: Shield,
    color: "#818cf8",
    tagline: "You control every step",
    steps: ["Signal detected and scored", "You receive a notification", "You review the signal detail", "You write or edit the outreach", "You send when ready"],
  },
  {
    mode: "Assisted",
    icon: Zap,
    color: "#a78bfa",
    tagline: "SCOUT drafts, you approve",
    steps: ["Signal detected and scored", "SCOUT drafts personalized email", "You review the draft in your queue", "You approve with one click", "SCOUT sends and tracks response"],
  },
  {
    mode: "Auto",
    icon: Clock,
    color: "#7c3aed",
    tagline: "Score 85+ triggers automatically",
    steps: ["Signal detected and scored", "SCOUT drafts personalized email", "Auto-sends after 30-min review window", "SCOUT tracks replies", "Follow-up scheduled automatically"],
  },
];

const DIV = () => (
  <div className="max-w-6xl mx-auto px-6 lg:px-8">
    <div className="h-px" style={{ backgroundColor: "rgba(124, 58, 237, 0.18)" }} />
  </div>
);

const SCOUT_CTA_STYLE = {
  color: "#FFB000",
  border: "1.5px solid #FFB000",
  background: "transparent",
  fontFamily: "Sora, sans-serif",
};

function InlinePill({ children }: { children: string }) {
  return (
    <span
      className="mx-0.5 inline-block rounded px-1.5 py-px text-[13px] font-medium align-baseline"
      style={{
        fontFamily: "JetBrains Mono, monospace",
        color: "#03DAC5",
        background: "rgba(3, 218, 197, 0.1)",
        border: "1px solid rgba(3, 218, 197, 0.25)",
      }}
    >
      {children}
    </span>
  );
}

export default function HowItWorks() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0d0520", color: "#f0eaff" }}>
      <Header />

      {/* ── Hero: live SCOUT + synced rail ── */}
      <section className="relative overflow-hidden" style={{ paddingTop: "112px" }}>
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-10 lg:gap-12 items-center pb-12 lg:pb-16">
            <div className="pt-4 lg:py-4">
              <p className="text-xs font-mono tracking-widest uppercase mb-6" style={{ color: "#FFB000" }}>
                Meet SCOUT
              </p>
              <h1
                className="font-bold leading-none mb-6"
                style={{ fontFamily: "Sora, sans-serif", fontSize: "clamp(2.4rem, 4.5vw, 3.8rem)", color: "#ffffff" }}
              >
                How SCOUT turns signals into{" "}
                <span style={{ color: "#FFB000" }}>sales motion.</span>
              </h1>
              <p
                className="text-base leading-relaxed mb-10 max-w-xl"
                style={{ color: "#c4b5fd", fontFamily: "Inter, sans-serif" }}
              >
                Not a revenue OS. Robotics intelligence on{" "}
                <span style={{ color: "#FFB000", fontWeight: 700 }}>HubSpot</span>
                —live signals, scored timing, your team closes.
              </p>

              <div className="mb-10 flex flex-wrap items-center gap-4">
                <Link
                  href="/results?url="
                  className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
                  style={SCOUT_CTA_STYLE}
                >
                  Activate SCOUT <Zap size={15} />
                </Link>
                <Link
                  href="/intelligence"
                  className="inline-flex items-center gap-2 text-sm font-bold text-white/50 transition-colors hover:text-white/75"
                  style={{ fontFamily: "Sora, sans-serif" }}
                >
                  See the scoring model <ArrowRight size={15} />
                </Link>
              </div>

              <div className="flex flex-wrap gap-x-8 gap-y-3">
                {[["150+", "data sources"], ["24/7", "monitoring"], ["<2 min", "signal to draft"], ["70+", "score threshold"]].map(([num, label]) => (
                  <div key={label} className="flex items-baseline gap-2">
                    <span
                      className="font-mono font-bold text-xl"
                      style={{ color: label === "signal to draft" ? "#FFB000" : "#a78bfa" }}
                    >
                      {num}
                    </span>
                    <span className="text-sm" style={{ color: "#6b7280" }}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="w-full min-w-0 lg:pt-10">
              <ScoutHeroShowcase />
            </div>
          </div>
        </div>
        <div
          className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, transparent, #0d0520)" }}
        />
      </section>

      <DIV />

      {/* ── vs all-in-one revenue platforms ── */}
      <section className="py-6 lg:py-8">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div
            className="rounded-2xl border px-6 py-5"
            style={{ borderColor: "rgba(3,218,197,0.2)", background: "rgba(3,218,197,0.04)" }}
          >
            <p className="text-sm font-bold text-white/80 mb-2" style={{ fontFamily: "Sora, sans-serif" }}>
              Intelligence layer, not a stack replacement
            </p>
            <p className="text-sm leading-relaxed text-white/45" style={{ fontFamily: "Inter, sans-serif" }}>
              All-in-one revenue platforms consolidate CRM, sequences, and AI into one workspace—you migrate your stack.
              SCOUT does the opposite: robotics-focused signals and outreach on HubSpot. HubSpot stays system of record;
              SCOUT is system of opportunity.
            </p>
          </div>
        </div>
      </section>

      <DIV />

      {/* ── The Process — tight inline prose, accent titles + glow ── */}
      <section className="py-12 lg:py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 w-full">
          <p
            className="text-sm font-medium mb-2"
            style={{ color: "#3ecf8e", fontFamily: "Inter, sans-serif" }}
          >
            The Process
          </p>
          <h2
            className="text-3xl md:text-4xl font-semibold tracking-tight leading-tight w-full"
            style={{ fontFamily: "Sora, sans-serif" }}
          >
            <span style={{ color: "#FFB000" }}>Five stages.</span>{" "}
            <span className="text-white">One continuous pipeline.</span>
          </h2>
          <p
            className="mt-3 text-base md:text-lg leading-relaxed w-full"
            style={{ color: "#c4b5fd", fontFamily: "Inter, sans-serif" }}
          >
            SCOUT is not a single trick — it is a full go-to-market engine for robotics sales teams.
            Each stage below maps to what you saw in the hero animation.
          </p>

          <div className="mt-3 w-full">
            {processSteps.map((step, i) => (
              <div key={step.title} className="w-full pb-4 last:pb-0">
                <h3
                  className="text-lg md:text-xl font-semibold tracking-tight"
                  style={{ fontFamily: "Sora, sans-serif", color: "#FFB000" }}
                >
                  {step.title}
                </h3>
                <p
                  className="mt-1.5 text-base md:text-[17px] leading-[1.72] w-full"
                  style={{ color: "#e9d5ff", fontFamily: "Inter, sans-serif" }}
                >
                  {step.body}
                  {step.pills?.map((pill) => (
                    <span key={pill}>
                      {" "}
                      <InlinePill>{pill}</InlinePill>
                    </span>
                  ))}
                </p>
                {i < processSteps.length - 1 && (
                  <div
                    className="mt-4 h-px w-full"
                    aria-hidden
                    style={{
                      background: `linear-gradient(90deg, transparent 0%, ${i % 2 === 0 ? "rgba(62, 207, 142, 0.55)" : "rgba(124, 58, 237, 0.55)"} 25%, ${i % 2 === 0 ? "#3ecf8e" : "#7c3aed"} 50%, ${i % 2 === 0 ? "rgba(62, 207, 142, 0.55)" : "rgba(124, 58, 237, 0.55)"} 75%, transparent 100%)`,
                    }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <DIV />

      {/* ── Signal sources ── */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
                Signal Sources
              </p>
              <h2 className="font-bold text-2xl mb-4" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                150+ sources,
                <br />
                one pipeline.
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: "#9ca3af" }}>
                Public and semi-public data across regulatory filings, employment signals,
                financial disclosures, and industry news — normalized into one scored feed.
              </p>
            </div>
            <div className="flex flex-wrap gap-x-8 gap-y-4 pt-2">
              {sources.map((s) => {
                const Icon = s.icon;
                return (
                  <div key={s.label} className="flex items-start gap-2.5 w-[calc(50%-1rem)] lg:w-auto">
                    <Icon size={14} style={{ color: "#7c3aed", marginTop: "2px", flexShrink: 0 }} />
                    <div>
                      <p className="text-sm font-medium" style={{ color: "#e9d5ff" }}>
                        {s.label}
                      </p>
                      <p className="text-xs" style={{ color: "#6b7280" }}>
                        {s.sub}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <DIV />

      {/* ── Scoring model ── */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
                Scoring Model
              </p>
              <h2 className="font-bold text-2xl mb-4" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                Three dimensions.
                <br />
                One score.
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: "#9ca3af" }}>
                Signals below 70 are filtered out automatically. Above 70, they enter your pipeline
                with a full breakdown.
              </p>
              <div className="mt-6 flex flex-col gap-2">
                {[["80–100", "#a78bfa", "Act now"], ["60–79", "#818cf8", "Watch"], ["<60", "#4b5563", "Monitor only"]].map(([range, color, label]) => (
                  <div key={range} className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold w-14" style={{ color }}>
                      {range}
                    </span>
                    <span className="text-xs" style={{ color: "#9ca3af" }}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-8 pt-2">
              {scoreDimensions.map((dim) => (
                <div key={dim.label}>
                  <div className="flex items-baseline justify-between mb-2">
                    <div className="flex items-baseline gap-3">
                      <span className="font-semibold text-sm" style={{ color: "#ffffff", fontFamily: "Sora, sans-serif" }}>
                        {dim.label}
                      </span>
                      <span className="text-xs" style={{ color: "#6b7280" }}>
                        {dim.sublabel}
                      </span>
                    </div>
                    <span
                      className="font-mono font-bold text-lg"
                      style={{ color: dim.color, fontFamily: "JetBrains Mono, monospace" }}
                    >
                      {dim.value}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(124,58,237,0.12)" }}>
                    <div className="h-full rounded-full" style={{ width: `${dim.value}%`, backgroundColor: dim.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <DIV />

      {/* ── Autonomy modes ── */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
            Autonomy Modes
          </p>
          <h2 className="font-bold text-2xl mb-12" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
            You choose how much SCOUT does.
          </h2>
          <div className="grid lg:grid-cols-3 gap-0">
            {autonomyModes.map((m, mi) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.mode}
                  style={{
                    paddingRight: mi < 2 ? "3rem" : "0",
                    borderRight: mi < 2 ? "1px solid rgba(124,58,237,0.15)" : "none",
                    paddingLeft: mi > 0 ? "3rem" : "0",
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon size={15} style={{ color: m.color }} />
                    <span className="font-semibold text-sm" style={{ color: "#ffffff", fontFamily: "Sora, sans-serif" }}>
                      {m.mode}
                    </span>
                  </div>
                  <p className="text-xs mb-5" style={{ color: "#6b7280" }}>
                    {m.tagline}
                  </p>
                  <ol className="space-y-2.5">
                    {m.steps.map((s, si) => (
                      <li key={si} className="flex items-start gap-2.5">
                        <span className="font-mono text-xs mt-0.5 flex-shrink-0" style={{ color: m.color }}>
                          {si + 1}.
                        </span>
                        <span className="text-sm leading-relaxed" style={{ color: "#9ca3af" }}>
                          {s}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <DIV />

      {/* ── Bottom CTA ── */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h2 className="font-bold text-2xl mb-2" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                Ready to automate your pipeline?
              </h2>
              <p className="text-sm" style={{ color: "#9ca3af" }}>
                Enter your company URL and see your first signals in seconds.
              </p>
            </div>
            <Link
              href="/results?url="
              className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
              style={SCOUT_CTA_STYLE}
            >
              Activate SCOUT <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </section>

      <footer className="py-8 border-t" style={{ borderColor: "rgba(124,58,237,0.15)" }}>
        <div className="max-w-6xl mx-auto px-6 lg:px-8 flex items-center justify-between">
          <span className="font-bold text-sm" style={{ fontFamily: "Sora, sans-serif", color: "#7c3aed" }}>
            ReadyForRobots
          </span>
          <span className="text-xs" style={{ color: "#4b5563" }}>
            © 2025 ReadyForRobots. All rights reserved.
          </span>
        </div>
      </footer>
    </div>
  );
}
