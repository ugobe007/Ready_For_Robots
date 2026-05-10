/**
 * Home — ReadyForRobots Dark Editorial Design
 * Inspired by: Linear, Vercel, Raycast
 * Dark hero (#0d0520) · Electric indigo accent · Grain texture · Glowing cards
 * Typography: Sora (display) · Inter (body) · JetBrains Mono (data)
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { Search, ArrowRight, Zap, Shield, TrendingUp, CheckCircle2, Globe, Target, Users, BarChart3, ChevronDown, Sparkles, FileText, RefreshCw, X, Quote } from "lucide-react";
import { toast } from "sonner";
import { Link } from "wouter";
import Header from "@/components/Header";
import HeroLivePipeline from "@/components/HeroLivePipeline";
import PipelinePreview from "@/components/PipelinePreview";
import ScoutWorkflowAnimation from "@/components/ScoutWorkflowAnimation";

const HERO_BG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/64MkMTSKNNGyC2kuruR8g2/rfr-dark-hero-eCRKfoUwPNDkc82gUhUXL9.webp";

const faqs = [
  {
    q: "How does ReadyForRobots find buying signals?",
    a: "We monitor 150+ sources continuously — job boards, earnings calls, press releases, OSHA filings, real estate permits, and industry news. Our system detects patterns that indicate a company is ready to invest in automation.",
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
    q: "How quickly does the system act on new signals?",
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
];

const agentFeatures = [
  { icon: Search, title: "Prospecting", desc: "Finds companies before they post an RFP" },
  { icon: FileText, title: "Outreach drafts", desc: "Signal-specific emails ready to send or edit" },
  { icon: RefreshCw, title: "Follow-up tracking", desc: "Knows when to re-engage and why" },
  { icon: Shield, title: "Qualification", desc: "Scores every lead — only real buyers reach you" },
];

export default function Home() {
  const [url, setUrl] = useState("");
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      toast.error("Please enter your company website URL");
      return;
    }
    toast.success("Scanning your pipeline…", {
      description: "We'll show you matched opportunities in seconds.",
    });
  };

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

        <div className="relative max-w-6xl mx-auto px-6 pt-32 pb-24">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_minmax(0,22rem)] gap-12 lg:gap-14 items-center">
          <div>
            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 mb-7 flex-wrap">
              <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#7c3aed" }} />
              <span className="rfr-scout-wordmark text-[10px] text-violet-200/95">SCOUT</span>
              <span className="text-xs text-white/35 hidden sm:inline">·</span>
              <span className="text-xs font-semibold text-white/45 tracking-wide" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                Autonomous sales agent
              </span>
            </div>

            {/* Headline */}
            <h1
              className="font-extrabold leading-[1.0] tracking-tight mb-6 text-white"
              style={{ fontSize: "clamp(2.8rem, 6vw, 5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Automate Your<br />
              <span
                style={{
                  background: "linear-gradient(135deg, #c4b5fd 0%, #8b5cf6 50%, #7c3aed 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Robot Sales
              </span>
              <br />Pipeline
            </h1>

            {/* Subheadline */}
            <p className="text-lg text-white/50 leading-relaxed mb-10 max-w-xl" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              <strong className="text-white/70 rfr-scout-wordmark text-[11px] align-middle mr-1.5">SCOUT</strong>
              runs your pipeline end-to-end: it finds buyers, scores signals,
              drafts outreach, follows up, and books meetings — so your team sells while SCOUT does the motion work.
            </p>

            {/* CTA form */}
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-stretch gap-3 max-w-lg">
              <div className="relative flex-1">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/25">
                  <Search className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Enter your robot company website…"
                  className="w-full pl-11 pr-4 py-3.5 text-sm text-white font-medium rounded-xl border border-white/12 bg-white/8 backdrop-blur-sm placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-blue-500/50 transition"
                />
              </div>
              <button
                type="submit"
                className="shrink-0 flex items-center justify-center gap-2 text-white font-semibold text-sm px-6 py-3.5 rounded-xl shadow-lg transition-all hover:-translate-y-0.5"
                style={{ background: "#7c3aed", boxShadow: "0 8px 24px rgba(124,58,237,0.35)" }}
              >
                Start automating
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-3 text-xs text-white/25" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              No signup required · Free to start · Results in seconds
            </p>
          </div>

          {/* Live pipeline card — stacks under copy on mobile; right column on lg */}
          <div className="mt-10 lg:mt-0 w-full max-w-md mx-auto lg:mx-0 lg:max-w-none lg:justify-self-end">
            <HeroLivePipeline />
          </div>
          </div>
        </div>
      </section>
      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="py-20 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-6xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-10" style={{ color: "#a78bfa" }}>How it works</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>
            {[
              { step: "01", icon: Search, title: "We find the signals", desc: "Scanning 150+ sources for labor shortages, expansion plans, CapEx signals, and hiring patterns that indicate automation readiness.", color: "#8b5cf6" },
              { step: "02", icon: Shield, title: "We qualify the prospects", desc: "Every company is scored on 4 factors — labor pain, expansion stage, automation fit, and timing. Only real opportunities make the cut.", color: "#34d399" },
              { step: "03", icon: Zap, title: "We deliver ready actions", desc: "You get a prioritized pipeline with drafted outreach, recommended timing, and the exact signal that triggered the opportunity.", color: "#f59e0b" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="px-8 py-10 group hover:bg-white/3 transition-colors"
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

      {/* ── SCOUT workflow (from rfr_cursor_package) ── */}
      <section className="py-20 px-6 border-t border-white/6" style={{ background: "#130828" }}>
        <div className="max-w-6xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3 rfr-scout-wordmark text-violet-300/90">SCOUT motion</p>
          <h2
            className="font-extrabold text-white leading-tight mb-4 max-w-xl"
            style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            From signal to sent outreach — in one loop
          </h2>
          <p className="text-sm text-white/40 mb-10 max-w-xl">
            Identify buying intent, develop the SCOUT score, then connect with drafted outreach. Teal highlights match the prototype design system.
          </p>
          <ScoutWorkflowAnimation />
        </div>
      </section>

      {/* ── AGENT PITCH ── */}
      <section
        className="py-24 px-6"
        style={{ background: "linear-gradient(180deg, #0d0520 0%, #130828 100%)" }}
      >
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left: copy */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-5" style={{ color: "#a78bfa" }}>Your AI sales agent</p>
            <h2
              className="font-extrabold text-white leading-tight mb-5"
              style={{ fontSize: "clamp(2rem, 3.5vw, 2.75rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              A full-time sales development rep —{" "}
              <span
                style={{
                  background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                without the headcount
              </span>
            </h2>
            <p className="text-white/45 text-base leading-relaxed mb-8">
              ReadyForRobots works around the clock to build and engage your pipeline.
              It does the prospecting, writes the outreach, tracks follow-ups, and
              surfaces only the opportunities worth your time.
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
              <div className="flex items-center gap-2.5 min-w-0">
                <img src="/logo-r.png" alt="" width={28} height={28} className="h-7 w-7 shrink-0 object-contain opacity-95" />
                <div className="min-w-0">
                  <span className="text-sm font-semibold text-white block truncate" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    SCOUT
                  </span>
                  <span className="rfr-scout-wordmark text-[9px] text-violet-300/80">Pipeline agent</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Running
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-px border-b border-white/6" style={{ background: "rgba(255,255,255,0.06)" }}>
              {[
                { value: "150+", label: "Sources monitored", color: "#8b5cf6" },
                { value: "24/7", label: "Always working", color: "#34d399" },
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

            {/* Activity feed — staggered motion (not static “buttons”) */}
            <div className="px-5 py-4 space-y-3">
              {[
                { label: "New signal: Silver Peak Hospitality", time: "just now", dot: "#34d399" },
                { label: "Outreach drafted: DesertLine Logistics", time: "4m ago", dot: "#8b5cf6" },
                { label: "Follow-up queued: Apex Manufacturing", time: "1h ago", dot: "#f59e0b" },
              ].map((item, i) => (
                <motion.div
                  key={item.label}
                  className="flex items-center justify-between gap-3"
                  initial={{ opacity: 0, x: 12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-24px" }}
                  transition={{ delay: i * 0.12, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: item.dot }} />
                    <span className="text-xs text-white/55 truncate">{item.label}</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/25 shrink-0" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                    {item.time}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── ABOUT US ── */}
      <section
        id="about"
        className="py-24 px-6 border-t border-white/6"
        style={{ background: "#130828" }}
      >
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-16 items-start">
          {/* Left: stats */}
          <div className="flex flex-col gap-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>About Us</p>
            {[
              { icon: Target, value: "500+", label: "Robot deals influenced", color: "#8b5cf6" },
              { icon: Users, value: "60+", label: "Robotics companies served", color: "#34d399" },
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
        className="py-24 px-6 border-t border-white/6"
        style={{ background: "#0d0520" }}
      >
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-12">
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
        className="py-24 px-6 border-t border-white/6"
        style={{ background: "#130828" }}
      >
        <div className="max-w-6xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4" style={{ color: "#a78bfa" }}>The difference</p>
          <h2
            className="font-extrabold text-white leading-tight mb-12"
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
                <div className="h-6 w-6 rounded-full flex items-center justify-center" style={{ background: "rgba(52,211,153,0.15)" }}>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                </div>
                <span className="text-sm font-bold text-emerald-400/80 uppercase tracking-widest">With ReadyForRobots</span>
              </div>
              <div className="space-y-4">
                {beforeAfter.map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/60 shrink-0 mt-2" />
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
        className="py-24 px-6 border-t border-white/6"
        style={{ background: "#0d0520" }}
      >
        <div className="max-w-6xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4" style={{ color: "#a78bfa" }}>What they say</p>
          <h2
            className="font-extrabold text-white leading-tight mb-12"
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
        className="py-24 px-6 border-t border-white/6"
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
        className="py-24 px-6 border-t border-white/6 relative overflow-hidden"
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
            Let the system find your next deal
          </h2>
          <p className="text-white/35 text-sm mb-8">Enter your company URL and we'll build your pipeline in seconds.</p>
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-3 max-w-md mx-auto">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="yourcompany.com"
              className="flex-1 w-full px-4 py-3.5 text-sm text-white font-medium rounded-xl border border-white/12 bg-white/8 backdrop-blur-sm placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition"
            />
            <button
              type="submit"
              className="shrink-0 flex items-center gap-2 text-white font-semibold text-sm px-6 py-3.5 rounded-xl shadow-lg transition-all hover:-translate-y-0.5"
              style={{ background: "#7c3aed", boxShadow: "0 8px 24px rgba(124,58,237,0.35)" }}
            >
              Build my pipeline
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-white/6 py-6 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <img src="/logo-r.png" alt="" width={24} height={24} className="h-6 w-6 object-contain opacity-90" />
            <span className="text-sm font-semibold text-white/50">ReadyForRobots</span>
          </div>
          <p className="text-xs text-white/20">© 2026 Signal intelligence for robotics sales.</p>
        </div>
      </footer>
    </div>
  );
}
