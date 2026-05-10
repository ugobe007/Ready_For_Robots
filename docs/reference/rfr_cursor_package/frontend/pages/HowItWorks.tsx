/**
 * How It Works — ReadyForRobots
 * Color system: #0d0520 bg · #7c3aed purple (brand/decorative) · #03DAC5 teal (action/live/CTA)
 * Design: Dark violet 60-30-10. Flat open layout — no padded panels, no buttons.
 * Robot image anchored right of hero. Inline text, numbered steps, clean dividers.
 * Typography: Sora headlines · Inter body · JetBrains Mono scores/labels
 */

import Header from "@/components/Header";
import { Link } from "wouter";
import {
  Search, Cpu, FileText, CheckCircle, TrendingUp,
  Zap, Shield, Clock, ArrowRight,
  Briefcase, BarChart3, AlertTriangle, Building2,
  Newspaper, Activity, Globe, MapPin, Handshake,
} from "lucide-react";

const ROBOT_IMAGE =
  "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/64MkMTSKNNGyC2kuruR8g2/robot-hiw-Yopt6ezNpbmPkaFHBTsEx6.webp";

const steps = [
  { num: "01", icon: Search,       title: "Signal Detection",  text: "150+ data sources — OSHA filings, job postings, SEC disclosures, LinkedIn, news — monitored 24/7 for buying signals.", teal: false },
  { num: "02", icon: Cpu,          title: "AI Scoring",        text: "Each signal scored across Confidence, Urgency, and Fit. Only signals above 70 enter your pipeline.", teal: false },
  { num: "03", icon: FileText,     title: "Outreach Drafting", text: "A personalized email — subject line, opening hook, call to action — drafted for every qualified signal, referencing the exact trigger event.", teal: true },
  { num: "04", icon: CheckCircle,  title: "You Review",        text: "Assisted: you approve before it sends. Auto: approved templates send automatically. Manual: you control every step.", teal: true },
  { num: "05", icon: TrendingUp,   title: "Pipeline Advances", text: "Responses and engagement tracked. Follow-up timing surfaced. Deals moved through stages automatically.", teal: true },
  { num: "06", icon: Handshake,    title: "Partnership Discovery", text: "SCOUT also scans for integrators, system integrators, distributors, and channel partners actively seeking robotics products to carry — surfacing strategic relationships alongside direct sales.", teal: true },
];

const sources = [
  { icon: Briefcase,     label: "Job Postings",         sub: "LinkedIn · Indeed · ZipRecruiter" },
  { icon: BarChart3,     label: "Earnings Calls",       sub: "SEC filings · CapEx announcements" },
  { icon: AlertTriangle, label: "OSHA Filings",         sub: "Safety incidents · Workers' comp" },
  { icon: Building2,     label: "Real Estate",          sub: "Permits · Lease filings · Expansions" },
  { icon: Newspaper,     label: "Press Releases",       sub: "News · PR Newswire · Business Wire" },
  { icon: Activity,      label: "Intent Signals",       sub: "RFP databases · Automation searches" },
  { icon: Globe,         label: "Web Signals",          sub: "Careers pages · Tech stack changes" },
  { icon: MapPin,        label: "Local Data",           sub: "Permits · Zoning · Construction starts" },
  { icon: BarChart3,     label: "Trade Publications",   sub: "Industry journals · Analyst reports" },
  { icon: Building2,     label: "Facility Expansions",  sub: "New sites · Capacity increases" },
  { icon: AlertTriangle, label: "Safety Incidents",     sub: "OSHA 300 logs · Inspection reports" },
  { icon: Briefcase,     label: "CapEx Announcements",  sub: "Capital expenditure filings · Budgets" },
  { icon: Handshake,     label: "Partner Signals",       sub: "SI directories · Distributor filings · Channel RFPs" },
];

// Scoring dimensions: teal for the highest-value "Fit" score, purple shades for the rest
const scoreDimensions = [
  { label: "Confidence", sublabel: "Source reliability & corroboration", value: 88, color: "#a78bfa" },
  { label: "Urgency",    sublabel: "Decision window & buying intent",     value: 72, color: "#818cf8" },
  { label: "Fit",        sublabel: "ICP match & company profile",         value: 95, color: "#03DAC5" },
];

// Score threshold legend: teal for "Act now" (highest), purple shades for lower tiers
const scoreLegend: [string, string, string][] = [
  ["80–100", "#03DAC5", "Act now"],
  ["60–79",  "#a78bfa", "Watch"],
  ["<60",    "#4b5563", "Monitor only"],
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
    tagline: "System drafts, you approve",
    steps: ["Signal detected and scored", "Agent drafts personalized email", "You review the draft in your queue", "You approve with one click", "Agent sends and tracks response"],
  },
  {
    mode: "Auto",
    icon: Clock,
    // Teal for the most "active/live" autonomy mode — the one that fires automatically
    color: "#03DAC5",
    tagline: "Score 85+ triggers automatically",
    steps: ["Signal detected and scored", "Agent drafts personalized email", "Auto-sends after 30-min review window", "Agent tracks opens and replies", "Follow-up scheduled automatically"],
  },
];

const DIV = () => (
  <div className="max-w-6xl mx-auto px-6 lg:px-8">
    <div className="h-px" style={{ backgroundColor: "rgba(124, 58, 237, 0.18)" }} />
  </div>
);

export default function HowItWorks() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0d0520", color: "#f0eaff" }}>
      <Header />

      {/* ── Hero ── */}
      <section className="relative overflow-hidden" style={{ paddingTop: "88px" }}>
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-0 items-end min-h-[480px]">

            {/* Left */}
            <div className="pb-10 lg:pb-0 pt-6">
              <p className="text-xs font-mono tracking-widest uppercase mb-6" style={{ color: "#7c3aed" }}>
                How It Works
              </p>
              <h1
                className="font-bold leading-none mb-6"
                style={{ fontFamily: "Sora, sans-serif", fontSize: "clamp(2.4rem, 4.5vw, 3.8rem)", color: "#ffffff" }}
              >
                Your AI sales agent,{" "}
                <span style={{ color: "#a78bfa" }}>explained.</span>
              </h1>
              <p className="text-base leading-relaxed mb-10 max-w-lg" style={{ color: "#c4b5fd", fontFamily: "Inter, sans-serif" }}>
                ReadyForRobots monitors the market, scores every signal, drafts personalized outreach,
                and advances your pipeline — automatically, or with as much human oversight as you want.
              </p>

              {/* Inline stats — teal for the two "live/active" stats, purple for the informational ones */}
              <div className="flex flex-wrap gap-x-8 gap-y-3">
                {[
                  { num: "150+", label: "data sources",    color: "#a78bfa" },
                  { num: "24/7", label: "monitoring",      color: "#03DAC5" },
                  { num: "<2 min", label: "signal to draft", color: "#03DAC5" },
                  { num: "70+",  label: "score threshold", color: "#a78bfa" },
                ].map(({ num, label, color }) => (
                  <div key={label} className="flex items-baseline gap-2">
                    <span className="font-mono font-bold text-xl" style={{ color }}>{num}</span>
                    <span className="text-sm" style={{ color: "#6b7280" }}>{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — robot */}
            <div className="relative flex justify-end items-end">
              <img
                src={ROBOT_IMAGE}
                alt="Industrial robot arm"
                className="w-full max-w-xs lg:max-w-sm object-contain"
                style={{ filter: "drop-shadow(0 0 80px rgba(124, 58, 237, 0.45))", marginBottom: "-2px" }}
              />
            </div>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, transparent, #0d0520)" }} />
      </section>

      <DIV />

      {/* ── 5-step process ── */}
      <section className="py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <p className="text-xs font-mono tracking-widest uppercase mb-8" style={{ color: "#7c3aed" }}>
            The Process
          </p>
          <div className="space-y-0">
            {steps.map((step, i) => {
              const Icon = step.icon;
              // Steps 03–05 are the "action" steps (drafting, reviewing, advancing) → teal
              const iconColor = step.teal ? "#03DAC5" : "#a78bfa";
              return (
                <div key={step.num}>
                  <div className="grid grid-cols-[56px_1fr] lg:grid-cols-[56px_180px_1fr] gap-6 items-start py-7">
                    <span className="font-mono font-bold text-2xl leading-none pt-0.5" style={{ color: "rgba(124,58,237,0.35)" }}>
                      {step.num}
                    </span>
                    <div className="flex items-start gap-2.5">
                      <Icon size={16} style={{ color: iconColor, marginTop: "3px", flexShrink: 0 }} />
                      <span className="font-semibold text-sm" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                        {step.title}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed" style={{ color: "#9ca3af", fontFamily: "Inter, sans-serif" }}>
                      {step.text}
                    </p>
                  </div>
                  {i < steps.length - 1 && (
                    <div className="h-px ml-14" style={{ backgroundColor: "rgba(124,58,237,0.1)" }} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <DIV />

      {/* ── Signal sources ── */}
      <section className="py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
                Signal Sources
              </p>
              <h2 className="font-bold text-2xl mb-4" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                150+ sources,<br />one pipeline.
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
                      <p className="text-sm font-medium" style={{ color: "#e9d5ff" }}>{s.label}</p>
                      <p className="text-xs" style={{ color: "#6b7280" }}>{s.sub}</p>
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
      <section className="py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-[260px_1fr] gap-16 items-start">
            <div>
              <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
                Scoring Model
              </p>
              <h2 className="font-bold text-2xl mb-4" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
                Three dimensions.<br />One score.
              </h2>
              <p className="text-sm leading-relaxed" style={{ color: "#9ca3af" }}>
                Signals below 70 are filtered out automatically. Above 70, they enter your pipeline
                with a full breakdown.
              </p>
              <div className="mt-6 flex flex-col gap-2">
                {scoreLegend.map(([range, color, label]) => (
                  <div key={range} className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold w-14" style={{ color }}>{range}</span>
                    <span className="text-xs" style={{ color: "#9ca3af" }}>{label}</span>
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
                      <span className="text-xs" style={{ color: "#6b7280" }}>{dim.sublabel}</span>
                    </div>
                    <span className="font-mono font-bold text-lg" style={{ color: dim.color, fontFamily: "JetBrains Mono, monospace" }}>
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
      <section className="py-14">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <p className="text-xs font-mono tracking-widest uppercase mb-4" style={{ color: "#7c3aed" }}>
            Autonomy Modes
          </p>
          <h2 className="font-bold text-2xl mb-12" style={{ fontFamily: "Sora, sans-serif", color: "#ffffff" }}>
            You choose how much the agent does.
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
                    {/* Live indicator on the Auto mode */}
                    {m.mode === "Auto" && (
                      <span className="ml-auto flex items-center gap-1 text-[10px] font-bold" style={{ color: "#03DAC5" }}>
                        <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
                        Live
                      </span>
                    )}
                  </div>
                  <p className="text-xs mb-5" style={{ color: "#6b7280" }}>{m.tagline}</p>
                  <ol className="space-y-2.5">
                    {m.steps.map((s, si) => (
                      <li key={si} className="flex items-start gap-2.5">
                        <span className="font-mono text-xs mt-0.5 flex-shrink-0" style={{ color: m.color }}>{si + 1}.</span>
                        <span className="text-sm leading-relaxed" style={{ color: "#9ca3af" }}>{s}</span>
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

      {/* ── Bottom CTA — inline, no panel ── */}
      <section className="py-14">
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
            {/* CTA link → teal (action) */}
            <Link
              href="/"
              className="inline-flex items-center gap-2 font-semibold text-sm px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5 hover:bg-teal-400/8"
              style={{
                color: "#03DAC5",
                border: "1.5px solid rgba(3,218,197,0.5)",
                background: "transparent",
                fontFamily: "Sora, sans-serif",
              }}
            >
              Start automating <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
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
