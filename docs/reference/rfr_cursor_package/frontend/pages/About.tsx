/**
 * About — ReadyForRobots
 * Mission, team, and company story in the dark editorial design language.
 */
import { Link } from "wouter";
import Header from "@/components/Header";
import { ArrowRight, Zap, Globe, Shield, TrendingUp } from "lucide-react";

const TEAM = [
  {
    name: "Alex Rivera",
    title: "Co-founder & CEO",
    bio: "Former VP of Sales at a Series B warehouse robotics company. Spent 6 years watching great robots lose deals to bad timing. Built ReadyForRobots to fix that.",
    initials: "AR",
    color: "#7c3aed",
  },
  {
    name: "Jordan Kim",
    title: "Co-founder & CTO",
    bio: "ML engineer with a background in NLP and signal detection. Previously built real-time monitoring systems at a logistics intelligence startup.",
    initials: "JK",
    color: "#03DAC5",
  },
  {
    name: "Morgan Chen",
    title: "Head of Product",
    bio: "Product lead with 8 years in B2B SaaS. Obsessed with reducing the gap between signal detection and human action.",
    initials: "MC",
    color: "#a78bfa",
  },
  {
    name: "Sam Okafor",
    title: "Head of Data",
    bio: "Built signal pipelines for financial intelligence platforms. Now applies the same discipline to the $250B global robotics market.",
    initials: "SO",
    color: "#f87171",
  },
];

const VALUES = [
  {
    icon: Zap,
    title: "Timing is everything",
    desc: "The best outreach in the world fails if it arrives after the decision is made. We built our entire product around getting you to the buyer first.",
    color: "#03DAC5",
  },
  {
    icon: Shield,
    title: "Signal quality over volume",
    desc: "We'd rather surface 10 high-confidence opportunities than flood your pipeline with noise. Every signal is scored, filtered, and explained.",
    color: "#7c3aed",
  },
  {
    icon: Globe,
    title: "Robots make the world better",
    desc: "We genuinely believe automation improves lives — reducing dangerous jobs, solving labor shortages, and enabling human workers to do more meaningful work.",
    color: "#a78bfa",
  },
  {
    icon: TrendingUp,
    title: "Sales should be a craft",
    desc: "We respect the craft of B2B sales. SCOUT is designed to make great salespeople more effective, not to replace the human judgment that closes deals.",
    color: "#f87171",
  },
];

export default function About() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      {/* ── HERO ── */}
      <section className="pt-32 pb-20 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 mb-8">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: "#7c3aed" }} />
            <span className="text-xs font-bold uppercase tracking-[0.15em]" style={{ color: "#c4b5fd" }}>
              About ReadyForRobots
            </span>
          </div>
          <h1
            className="font-extrabold leading-[1.05] tracking-tight mb-6 text-white"
            style={{ fontSize: "clamp(2.4rem, 5vw, 4rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
          >
            We built the intelligence layer<br />
            <span
              style={{
                background: "linear-gradient(135deg, #03DAC5 0%, #7c3aed 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              the robotics industry was missing.
            </span>
          </h1>
          <p className="text-lg text-white/50 leading-relaxed max-w-2xl" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Every year, billions of dollars in robotics deals are lost not because the product wasn't right — but because the seller showed up too late, too early, or without context. ReadyForRobots exists to fix that.
          </p>
        </div>
      </section>

      {/* ── STORY ── */}
      <section className="py-16 px-6" style={{ background: "rgba(255,255,255,0.02)" }}>
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4" style={{ color: "#a78bfa" }}>Our story</p>
            <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              Born from a lost deal
            </h2>
            <p className="text-white/50 leading-relaxed mb-4" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              Our CEO Alex spent six years selling warehouse robots. In 2022, his team lost a $1.8M deal to a competitor — not because their product was inferior, but because the competitor had reached the buyer four months earlier, during the facility planning phase, and had already shaped the requirements.
            </p>
            <p className="text-white/50 leading-relaxed" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              That deal — and dozens like it — made one thing clear: in robotics sales, timing isn't an advantage. It's the whole game. ReadyForRobots was founded in 2023 to give every robotics company the intelligence to be first.
            </p>
          </div>
          <div className="space-y-4">
            {[
              { label: "Founded", value: "2023", sub: "San Francisco, CA" },
              { label: "Signal sources monitored", value: "150+", sub: "Job boards, earnings calls, permits, news" },
              { label: "Robot categories covered", value: "12", sub: "Warehouse, industrial, service, food & more" },
              { label: "Avg. lead time advantage", value: "4–6 mo", sub: "Before RFP or public announcement" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="flex items-center justify-between px-4 py-3 rounded-xl border"
                style={{ background: "rgba(124,58,237,0.06)", borderColor: "rgba(124,58,237,0.15)" }}
              >
                <div>
                  <p className="text-xs text-white/40" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>{stat.label}</p>
                  <p className="text-[10px] text-white/25" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>{stat.sub}</p>
                </div>
                <span
                  className="font-bold text-lg"
                  style={{ color: "#a78bfa", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  {stat.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── VALUES ── */}
      <section className="py-16 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-4xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-10" style={{ color: "#a78bfa" }}>What we believe</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {VALUES.map((v) => {
              const Icon = v.icon;
              return (
                <div
                  key={v.title}
                  className="p-5 rounded-xl border"
                  style={{ background: `${v.color}08`, borderColor: `${v.color}20` }}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                    style={{ background: `${v.color}15` }}
                  >
                    <Icon className="h-4 w-4" style={{ color: v.color }} />
                  </div>
                  <h3 className="text-sm font-bold text-white mb-1.5" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {v.title}
                  </h3>
                  <p className="text-xs text-white/45 leading-relaxed" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                    {v.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── TEAM ── */}
      <section className="py-16 px-6" style={{ background: "rgba(255,255,255,0.02)" }}>
        <div className="max-w-4xl mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-10" style={{ color: "#a78bfa" }}>The team</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {TEAM.map((member) => (
              <div
                key={member.name}
                className="flex gap-4 p-5 rounded-xl border"
                style={{ background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.06)" }}
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-sm font-bold text-white"
                  style={{ background: `${member.color}25`, border: `1.5px solid ${member.color}40` }}
                >
                  {member.initials}
                </div>
                <div>
                  <p className="text-sm font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {member.name}
                  </p>
                  <p className="text-[10px] font-semibold mb-2" style={{ color: member.color }}>
                    {member.title}
                  </p>
                  <p className="text-xs text-white/40 leading-relaxed" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                    {member.bio}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6" style={{ background: "#0d0520" }}>
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
            Ready to see it in action?
          </h2>
          <p className="text-white/40 mb-8 text-sm" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Enter your company URL and SCOUT will show you a sample of matched opportunities — no signup required.
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
