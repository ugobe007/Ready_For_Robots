/**
 * Home — ReadyForRobots Dark Editorial Design
 * Inspired by: Linear, Vercel, Raycast
 * Color system: #0d0520 bg · #7c3aed purple (brand/headlines) · #03DAC5 teal (action/live/CTA)
 * Typography: Sora (display) · Inter (body) · JetBrains Mono (data)
 */
import React, { useState, useEffect, useRef } from "react";
import { Search, ArrowRight, Zap, Shield, TrendingUp, CheckCircle2, Globe, Target, Users, BarChart3, ChevronDown, Sparkles, FileText, RefreshCw, X, Quote } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import PipelinePreview from "@/components/PipelinePreview";
import ScoutWorkflowAnimation from "@/components/ScoutWorkflowAnimation";
import { useFadeUp, fadeUpClass } from "@/hooks/useFadeUp";

// Typewriter hook — spells out text character by character after a delay
// Uses refs for speed/delay so re-renders don't reset the animation mid-flight
function useTypewriter(text: string, speed = 55, startDelay = 600) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const speedRef = useRef(speed);
  const delayRef = useRef(startDelay);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    let i = 0;
    let interval: ReturnType<typeof setInterval>;
    const delay = setTimeout(() => {
      interval = setInterval(() => {
        i++;
        setDisplayed(text.slice(0, i));
        if (i >= text.length) {
          clearInterval(interval);
          setDone(true);
        }
      }, speedRef.current);
    }, delayRef.current);
    return () => {
      clearTimeout(delay);
      clearInterval(interval);
    };
  // Only re-run when the text itself changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return { displayed, done };
}

const HERO_BG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/64MkMTSKNNGyC2kuruR8g2/rfr-dark-hero-eCRKfoUwPNDkc82gUhUXL9.webp";

const faqs = [
  {
    q: "How does ReadyForRobots find buying signals?",
    a: "We monitor 150+ sources continuously — job boards, earnings calls, press releases, OSHA filings, real estate permits, and industry news. SCOUT detects patterns that indicate a company is ready to invest in automation.",
  },
  {
    q: "What types of robots does this work for?",
    a: "Any robot category with a B2B sales motion: warehouse AMRs, service robots, industrial arms, cleaning robots, food processing automation, healthcare robots, and more. You tell us your category and we tune the signals accordingly.",
  },
  {
    q: "How is this different from a lead list?",
    a: "A lead list gives you names. We give you timing, context, and a reason to reach out. Every opportunity comes with the exact signal that triggered it, a confidence score, and a drafted outreach message — so you reach the right buyer at the right moment.",
  },
  {
    q: "Do I need to sign up to see results?",
    a: "No. Enter your company URL above and we'll show you a sample of matched opportunities immediately — no account required. You only sign up when you want to act on them.",
  },
  {
    q: "How quickly does SCOUT act on new signals?",
    a: "Signals are detected and scored within minutes. Outreach drafts are ready within the hour. In Auto mode, approved actions are sent within 24 hours of signal detection.",
  },
];

const testimonials = [
  {
    quote: "We reached the buyer 4 months before the RFP — and shaped the requirements. That deal would never have happened with a cold list.",
    name: "VP of Sales",
    company: "Warehouse AMR Company",
    result: "15-robot pilot",
  },
  {
    quote: "ReadyForRobots found a $2.4M logistics opportunity we had zero visibility into. The signal was an earnings call mention — we never would have caught it manually.",
    name: "Director of Business Development",
    company: "Industrial Robotics OEM",
    result: "$2.4M contract",
  },
  {
    quote: "Our SDR used to spend 3 days a week on prospecting. Now that time goes to closing. The pipeline quality is completely different.",
    name: "Head of Sales",
    company: "Service Robot Startup",
    result: "3x pipeline velocity",
  },
];

const beforeAfter = [
  { before: "Cold lists with no context", after: "Signal-triggered outreach with exact buying reason" },
  { before: "Reach out and hope for the right timing", after: "Contact during the decision window, not after" },
  { before: "Generic email templates", after: "Drafted message referencing their specific signal" },
  { before: "3% reply rate on cold outreach", after: "Warm conversations with buyers who have a real need" },
  { before: "Find out about deals after the RFP drops", after: "Shape requirements before competitors know it exists" },
  { before: "SDR spends 70% of time prospecting", after: "SDR spends 100% of time on qualified conversations" },
  { before: "No visibility into partnership opportunities", after: "SCOUT surfaces integrators and channel partners ready to carry your product" },
];

const agentFeatures = [
  { icon: Search, title: "Lead prospecting", desc: "Finds buyers before they post an RFP" },
  { icon: Users, title: "Partnership development", desc: "Identifies integrators, distributors & channel partners" },
  { icon: FileText, title: "Outreach drafts", desc: "Signal-specific emails ready to send or edit" },
  { icon: RefreshCw, title: "Pipeline development", desc: "Nurtures leads and partners from signal to close" },
  { icon: Shield, title: "Qualification", desc: "Scores every opportunity — only real buyers reach you" },
  { icon: Globe, title: "Market intelligence", desc: "150+ sources monitored 24/7 for buying signals" },
];

export default function Home() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const { displayed: typedText, done: typedDone } = useTypewriter("Start closing.", 65, 700);

  const howItWorks = useFadeUp();
  const agentPitch = useFadeUp();
  const aboutSection = useFadeUp();
  const proofSection = useFadeUp();
  const beforeAfterSection = useFadeUp();
  const testimonialsSection = useFadeUp();
  const faqSection = useFadeUp();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      {/* ── HERO ── */}
      <section
        id="hero-cta"
        className="relative min-h-screen flex flex-col justify-center overflow-hidden"
        style={{ background: "#0d0520" }}
      >
        {/* Background image */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-60"
          style={{ backgroundImage: `url(${HERO_BG})` }}
        />
        {/* Radial glow center */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(124,58,237,0.12) 0%, transparent 70%)" }}
        />
        {/* Bottom fade */}
        <div
          className="absolute bottom-0 left-0 right-0 h-48 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, transparent, #0d0520)" }}
        />

        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-16">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-12 items-center">
          <div>
            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 mb-7">
              <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#7c3aed" }} />
              <span className="text-xs font-bold uppercase tracking-[0.15em]" style={{ color: "#c4b5fd" }}>
                SCOUT — AI Sales &amp; Partnership Agent for Robotics
              </span>
            </div>

            {/* Headline */}
            <h1
              className="font-extrabold leading-[1.05] tracking-tight mb-3 text-white"
              style={{ fontSize: "clamp(2.8rem, 6vw, 5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Stop prospecting.
              <br />
              <span
                style={{
                  background: "linear-gradient(135deg, #03DAC5 0%, #7c3aed 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                {typedText}
              </span>
              {!typedDone && (
                <span
                  className="inline-block w-[3px] h-[0.85em] ml-[2px] align-middle animate-pulse"
                  style={{ background: "#03DAC5", borderRadius: "1px", verticalAlign: "middle" }}
                />
              )}
            </h1>

            {/* Subheadline */}
            <p className="text-base text-white/60 leading-relaxed mb-6 max-w-lg" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              <span style={{ color: "#FFB000", fontWeight: 700 }}>SCOUT</span> does the prospecting, qualifying, outreach, and scheduling.<br />
              Your team just closes.
            </p>

            {/* CTA — Activate Pipeline */}
            <Link href="/results?url=">
              <button
                className="inline-flex items-center gap-2.5 font-bold px-7 py-3.5 rounded-2xl mb-4 transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
                style={{ fontSize: "1rem", color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
              >
                <Zap className="h-4.5 w-4.5" />
                Activate Pipeline
                <ArrowRight className="h-4 w-4" />
              </button>
            </Link>

            <p className="text-xs text-white/25" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              No signup required · Free to start · Results in seconds
            </p>
          </div>

          {/* SCOUT Workflow Animation — right column */}
          <div className="hidden lg:block">
            <ScoutWorkflowAnimation />
          </div>
          </div>
        </div>
      </section>
      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="py-14 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-6xl mx-auto">
          <p ref={howItWorks.ref as React.RefObject<HTMLParagraphElement>} className={`text-[10px] font-bold uppercase tracking-[0.2em] mb-7 ${fadeUpClass(howItWorks.visible)}`} style={{ color: "#a78bfa" }}>How it works</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>
            {[
              { step: "01", icon: Search, title: "We find the signals", desc: "Scanning 150+ sources for labor shortages, expansion plans, CapEx signals, and hiring patterns that indicate automation readiness.", color: "#8b5cf6" },
              { step: "02", icon: Shield, title: "We qualify the prospects", desc: "Every company is scored on 4 factors — labor pain, expansion stage, automation fit, and timing. Only real opportunities make the cut.", color: "#03DAC5" },
              { step: "03", icon: Zap, title: "We deliver ready actions", desc: "You get a prioritized pipeline with drafted outreach, recommended timing, and the exact signal that triggered the opportunity.", color: "#a78bfa" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="px-6 py-7 group hover:bg-white/3 transition-colors"
                  style={{ background: "rgba(255,255,255,0.02)" }}
                >
                  <p className="font-mono text-xs font-bold mb-4" style={{ color: item.color, fontFamily: "'JetBrains Mono', monospace" }}>
                    {item.step}
                  </p>
                  <div className="flex items-center gap-2.5 mb-3">
                    <Icon className="h-4 w-4" style={{ color: item.color }} />
                    <h3 className="text-sm font-bold text-white">{item.title}</h3>
                  </div>
                  <p className="text-sm text-white/40 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── PIPELINE PREVIEW ── */}
      <PipelinePreview />

      {/* ── AGENT PITCH ── */}
      <section
        className="py-16 px-6"
        style={{ background: "linear-gradient(180deg, #0d0520 0%, #130828 100%)" }}
      >
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left: copy */}
          <div ref={agentPitch.ref as React.RefObject<HTMLDivElement>} className={fadeUpClass(agentPitch.visible)}>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-5" style={{ color: "#a78bfa" }}>Meet SCOUT</p>
            <h2
              className="font-extrabold text-white leading-tight mb-5"
              style={{ fontSize: "clamp(2rem, 3.5vw, 2.75rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Sales &amp; partnerships,{" "}
              <span
                style={{
                  background: "linear-gradient(135deg, #03DAC5, #7c3aed)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >fully automated
              </span>
            </h2>
            <p className="text-white/45 text-base leading-relaxed mb-8">
              SCOUT is ReadyForRobots' AI sales &amp; partnership agent. It works 24/7 to find buyers, identify strategic partners, and develop every opportunity from first signal to closed deal — so your team focuses on conversations that matter, not hunting for them.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {agentFeatures.map((f) => {
                const Icon = f.icon;
                return (
                  <div
                    key={f.title}
                    className="flex items-start gap-3 p-4 rounded-xl border border-white/6 hover:border-violet-500/30 transition-colors"
                    style={{ background: "rgba(255,255,255,0.03)" }}
                  >
                    <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: "rgba(124,58,237,0.12)", border: "1px solid rgba(124,58,237,0.25)" }}>
                      <Icon className="h-4 w-4" style={{ color: "#a78bfa" }} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white mb-0.5">{f.title}</p>
                      <p className="text-xs text-white/35">{f.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Pipeline Agent card */}
          <div
            className="rounded-2xl border border-white/8 overflow-hidden shadow-2xl shadow-black/60"
            style={{ background: "rgba(255,255,255,0.03)" }}
          >
            {/* Card header */}
            <div
              className="px-5 py-4 flex items-center justify-between border-b border-white/6"
              style={{ background: "rgba(124,58,237,0.08)" }}
            >
              <div className="flex items-center gap-2.5">
                <div className="h-7 w-7 rounded-lg flex items-center justify-center" style={{ background: "#7c3aed" }}>
                  <Zap className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
                </div>
                <span className="text-sm font-semibold text-white">SCOUT</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-bold" style={{ color: "#03DAC5" }}>
                <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
                Running
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-px border-b border-white/6" style={{ background: "rgba(255,255,255,0.06)" }}>
              {[
                { value: "150+", label: "Sources monitored", color: "#8b5cf6" },
                { value: "24/7", label: "Always working", color: "#03DAC5" },
                { value: "14", label: "Signal types tracked", color: "#8b5cf6" },
                { value: "<48h", label: "Signal to outreach", color: "#f59e0b" },
              ].map((stat) => (
                <div key={stat.label} className="px-5 py-4" style={{ background: "rgba(255,255,255,0.02)" }}>
                  <p className="font-mono text-xl font-bold mb-0.5" style={{ color: stat.color, fontFamily: "'JetBrains Mono', monospace" }}>
                    {stat.value}
                  </p>
                  <p className="text-xs text-white/35">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Activity feed */}
            <div className="px-5 py-4 space-y-3">
              {[
                { label: "New signal: Silver Peak Hospitality", time: "just now", dot: "#03DAC5" },
                { label: "Outreach drafted: DesertLine Logistics", time: "4m ago", dot: "#8b5cf6" },
                { label: "Follow-up queued: Apex Manufacturing", time: "1h ago", dot: "#f59e0b" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: item.dot }} />
                    <span className="text-xs text-white/55">{item.label}</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/25 shrink-0" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                    {item.time}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── ABOUT US ── */}
      <section
        id="about"
        className="py-16 px-6 border-t border-white/6"
        style={{ background: "#130828" }}
      >
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-16 items-start">
          {/* Left: stats */}
          <div ref={aboutSection.ref as React.RefObject<HTMLDivElement>} className={`flex flex-col gap-3 ${fadeUpClass(aboutSection.visible)}`}>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>About Us</p>
            {[
              { icon: Target, value: "500+", label: "Robot deals influenced", color: "#8b5cf6" },
              { icon: Users, value: "60+", label: "Robotics companies served", color: "#03DAC5" },
              { icon: Globe, value: "12", label: "Verticals covered", color: "#8b5cf6" },
              { icon: BarChart3, value: "150+", label: "Signal sources monitored", color: "#a78bfa" },
            ].map((stat) => {
              const Icon = stat.icon;
              return (
                <div
                  key={stat.label}
                  className="flex items-center gap-4 p-4 rounded-xl border border-white/6"
                  style={{ background: "rgba(255,255,255,0.03)" }}
                >
                  <Icon className="h-4 w-4 shrink-0" style={{ color: stat.color }} />
                  <div>
                    <p className="font-mono text-lg font-bold" style={{ color: stat.color, fontFamily: "'JetBrains Mono', monospace" }}>
                      {stat.value}
                    </p>
                    <p className="text-xs text-white/35">{stat.label}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: copy */}
          <div className="lg:pt-10">
            <h2
              className="font-extrabold text-white leading-tight mb-5"
              style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Built by people<br />who've sold robots
            </h2>
            <p className="text-white/45 text-base leading-relaxed mb-4">
              ReadyForRobots was founded by robotics sales veterans who spent years
              losing deals to competitors who found the buyer first. We built the
              system we wished we had — one that monitors the market continuously
              and surfaces opportunities before they become RFPs.
            </p>
            <p className="text-white/45 text-base leading-relaxed mb-6">
              Today we serve robotics companies across warehousing, hospitality,
              healthcare, manufacturing, and food processing — helping them reach
              the right buyer at the right moment with the right message.
            </p>
            <div
              className="flex items-start gap-3 p-4 rounded-xl"
              style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.25)" }}
            >
              <Sparkles className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "#a78bfa" }} />
              <p className="text-sm font-medium italic" style={{ color: "#ddd6fe" }}>
                "We reached the buyer 4 months before the RFP — and shaped the requirements."
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── PROOF ── */}
      <section
        id="case-studies"
        className="py-16 px-6 border-t border-white/6"
        style={{ background: "#0d0520" }}
      >
        <div className="max-w-6xl mx-auto">
          <div ref={proofSection.ref as React.RefObject<HTMLDivElement>} className={`flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8 ${fadeUpClass(proofSection.visible)}`}>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>Real signals. Real deals.</p>
              <h2
                className="font-extrabold text-white leading-tight"
                style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
              >
                Close before the RFP
              </h2>
            </div>
            <p className="text-sm text-white/30 max-w-xs text-right hidden sm:block">
              How robotics companies use ReadyForRobots to win deals competitors never saw coming
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                signal: "\"Can't staff overnight shifts\" + \"40% housekeeping vacancy\" in earnings call",
                action: "Reached out 4 months before RFP with overnight automation case study",
                result: "Shaped requirements, won pilot without competition",
                outcome: "15-robot deployment",
                industry: "Hospitality",
                accentColor: "#8b5cf6",
              },
              {
                signal: "\"Opening 2 new DCs\" + posting for \"automation engineer\"",
                action: "Contacted during facility design phase with layout recommendations",
                result: "Designed automation into new buildings",
                outcome: "$2.4M contract",
                industry: "Logistics",
                accentColor: "#34d399",
              },
            ].map((story) => (
              <div
                key={story.industry}
                className="rounded-2xl border border-white/8 p-6 hover:border-white/14 transition-colors"
                style={{ background: "rgba(255,255,255,0.03)", borderLeft: `3px solid ${story.accentColor}` }}
              >
                <div className="flex items-center justify-between mb-5">
                  <span className="text-xs font-bold text-white/30 uppercase tracking-widest">{story.industry}</span>
                  <span
                    className="text-xs font-bold px-2.5 py-1 rounded-full border"
                    style={{ color: story.accentColor, background: `${story.accentColor}18`, borderColor: `${story.accentColor}40` }}
                  >
                    {story.outcome}
                  </span>
                </div>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0 mt-0.5" style={{ background: "rgba(248,113,113,0.1)" }}>
                      <TrendingUp className="h-3.5 w-3.5 text-red-400" />
                    </div>
                    <p className="text-sm text-white/45 italic leading-relaxed">"{story.signal}"</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0 mt-0.5" style={{ background: "rgba(139,92,246,0.1)" }}>
                      <ArrowRight className="h-3.5 w-3.5" style={{ color: "#a78bfa" }} />
                    </div>
                    <p className="text-sm text-white/60 leading-relaxed">{story.action}</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0 mt-0.5" style={{ background: "rgba(52,211,153,0.1)" }}>
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    </div>
                    <p className="text-sm font-semibold text-white leading-relaxed">{story.result}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BEFORE / AFTER ── */}
      <section
        className="py-16 px-6 border-t border-white/6"
        style={{ background: "#130828" }}
      >
        <div className="max-w-6xl mx-auto">
          <p ref={beforeAfterSection.ref as React.RefObject<HTMLParagraphElement>} className={`text-[10px] font-bold uppercase tracking-[0.2em] mb-4 ${fadeUpClass(beforeAfterSection.visible)}`} style={{ color: "#a78bfa" }}>The difference</p>
          <h2
            className="font-extrabold text-white leading-tight mb-8"
            style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            Before vs. After ReadyForRobots
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>
            {/* Before column */}
            <div className="p-8" style={{ background: "rgba(255,255,255,0.02)" }}>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-6 w-6 rounded-full flex items-center justify-center" style={{ background: "rgba(239,68,68,0.15)" }}>
                  <X className="h-3.5 w-3.5 text-red-400" />
                </div>
                <span className="text-sm font-bold text-red-400/80 uppercase tracking-widest">Before</span>
              </div>
              <div className="space-y-4">
                {beforeAfter.map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="h-1.5 w-1.5 rounded-full bg-red-400/40 shrink-0 mt-2" />
                    <p className="text-sm text-white/35 leading-relaxed">{item.before}</p>
                  </div>
                ))}
              </div>
            </div>
            {/* After column */}
            <div className="p-8" style={{ background: "rgba(124,58,237,0.05)" }}>
              <div className="flex items-center gap-2 mb-6">
                <div className="h-6 w-6 rounded-full flex items-center justify-center" style={{ background: "rgba(3,218,197,0.12)" }}>
                  <CheckCircle2 className="h-3.5 w-3.5" style={{ color: "#03DAC5" }} />
                </div>
                <span className="text-sm font-bold uppercase tracking-widest" style={{ color: "#03DAC5", opacity: 0.8 }}>With ReadyForRobots</span>
              </div>
              <div className="space-y-4">
                {beforeAfter.map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="h-1.5 w-1.5 rounded-full shrink-0 mt-2" style={{ background: "rgba(3,218,197,0.6)" }} />
                    <p className="text-sm text-white/70 leading-relaxed font-medium">{item.after}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section
        className="py-16 px-6 border-t border-white/6"
        style={{ background: "#0d0520" }}
      >
        <div className="max-w-6xl mx-auto">
          <p ref={testimonialsSection.ref as React.RefObject<HTMLParagraphElement>} className={`text-[10px] font-bold uppercase tracking-[0.2em] mb-4 ${fadeUpClass(testimonialsSection.visible)}`} style={{ color: "#a78bfa" }}>What they say</p>
          <h2
            className="font-extrabold text-white leading-tight mb-8"
            style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            From the sales floor
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {testimonials.map((t, i) => (
              <div
                key={i}
                className="rounded-2xl border border-white/8 p-6 flex flex-col gap-4 hover:border-violet-500/30 transition-colors"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                <div style={{ color: "#7c3aed", opacity: 0.5 }}>
                  <Quote className="h-5 w-5" />
                </div>
                <p className="text-sm text-white/60 leading-relaxed italic flex-1">"{t.quote}"</p>
                <div className="flex items-center justify-between pt-2 border-t border-white/6">
                  <div>
                    <p className="text-xs font-semibold text-white/70">{t.name}</p>
                    <p className="text-[10px] text-white/30">{t.company}</p>
                  </div>
                  <span
                    className="text-[10px] font-bold px-2 py-1 rounded-full"
                    style={{ color: "#a78bfa", background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
                  >
                    {t.result}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section
        id="faq"
        ref={faqSection.ref as React.RefObject<HTMLElement>}
        className={`py-16 px-6 border-t border-white/6 ${fadeUpClass(faqSection.visible)}`}
        style={{ background: "#130828" }}
      >
        <div className="max-w-3xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4" style={{ color: "#a78bfa" }}>Questions</p>
          <h2
            className="font-extrabold text-white mb-2"
            style={{ fontSize: "clamp(1.8rem, 3vw, 2.25rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            Frequently asked questions
          </h2>
          <p className="text-sm text-white/35 mb-10">Everything you need to know before you start automating</p>

          <div className="flex flex-col divide-y divide-white/6 rounded-2xl border border-white/8 overflow-hidden">
            {faqs.map((faq, i) => {
              const isOpen = openFaq === i;
              return (
                <div key={i} className="transition-colors" style={{ background: isOpen ? "rgba(124,58,237,0.06)" : "rgba(255,255,255,0.02)" }}>
                  <button
                    type="button"
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left"
                  >
                    <span className="text-sm font-semibold text-white/80">{faq.q}</span>
                    <ChevronDown className={`h-4 w-4 text-white/25 shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-5 border-t border-white/6">
                      <p className="text-sm text-white/45 leading-relaxed pt-4">{faq.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── BOTTOM CTA ── */}
      <section
        className="py-16 px-6 border-t border-white/6 relative overflow-hidden"
        style={{ background: "#0d0520" }}
      >
        {/* Glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 60% 50% at 50% 100%, rgba(124,58,237,0.15) 0%, transparent 70%)" }}
        />
        <div className="relative max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] mb-5" style={{ color: "#c4b5fd" }}>
            <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#7c3aed" }} />
            Ready to automate
          </div>
          <h2
            className="font-extrabold text-white mb-3"
            style={{ fontSize: "clamp(1.8rem, 3.5vw, 2.75rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            Let SCOUT run your pipeline.
          </h2>
          <p className="text-white/35 text-sm mb-8">SCOUT scans for buyers, scores each lead, drafts outreach, and runs your sales process — automatically.</p>

          {/* CTA — Activate Pipeline */}
          <Link href="/results?url=">
            <button
              className="inline-flex items-center gap-3 text-base font-bold px-8 py-4 rounded-2xl transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
              style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
            >
              <Zap className="h-5 w-5" />
              Activate Pipeline
              <ArrowRight className="h-4 w-4" />
            </button>
          </Link>
          <p className="mt-4 text-white/20 text-xs">No signup required · Free to start · Results in seconds</p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-white/6 py-6 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <img src="/logo-r.png" alt="" width={24} height={24} className="h-6 w-6 object-contain opacity-90" />
            <span className="text-sm font-semibold text-white/50">ReadyForRobots</span>
          </div>
          <p className="text-xs text-white/20">© 2026 SCOUT by ReadyForRobots · Signal intelligence for robotics sales.</p>
        </div>
      </footer>
    </div>
  );
}
