/**
 * PipelinePreview — ReadyForRobots Dark Editorial Design
 * Dark background, inline signal rows, expand-on-click for recommended action
 * Inspired by: Linear, Vercel, Raycast
 */
import { useState } from "react";
import { Link } from "wouter";
import { TrendingUp, Users, AlertTriangle, ChevronRight, ChevronDown, ArrowRight, Zap } from "lucide-react";

const signals = [
  {
    company: "Silver Peak Hospitality",
    industry: "Hospitality",
    signal: "Housekeeping vacancy rate hit 43% — 3 properties",
    action: "Pitch overnight cleaning robot pilot to VP Operations",
    score: 94,
    status: "HOT",
    time: "2m ago",
    signalType: "labor",
  },
  {
    company: "DesertLine Logistics",
    industry: "Logistics",
    signal: "Announced 2 new distribution centers in Phoenix",
    action: "Reach out during facility design phase with layout recommendations",
    score: 88,
    status: "HOT",
    time: "18m ago",
    signalType: "expansion",
  },
  {
    company: "Apex Food Processing",
    industry: "Food Processing",
    signal: "OSHA citation: repetitive motion injuries on line 4",
    action: "Send ergonomic automation ROI case study",
    score: 76,
    status: "WARM",
    time: "1h ago",
    signalType: "safety",
  },
  {
    company: "NovaCare Health Systems",
    industry: "Healthcare",
    signal: "Hiring 12 pharmacy techs — 4th consecutive quarter",
    action: "Pharmacy automation discovery call with Director of Operations",
    score: 71,
    status: "WARM",
    time: "3h ago",
    signalType: "labor",
  },
  {
    company: "Summit Manufacturing",
    industry: "Manufacturing",
    signal: "CapEx budget increased 28% YoY per earnings call",
    action: "Connect with VP Operations before Q3 planning cycle",
    score: 65,
    status: "WARM",
    time: "5h ago",
    signalType: "expansion",
  },
];

const signalIcons: Record<string, React.ElementType> = {
  labor: Users,
  expansion: TrendingUp,
  safety: AlertTriangle,
};

const statusConfig = {
  HOT: { color: "#f87171", bg: "rgba(248,113,113,0.12)", border: "rgba(248,113,113,0.25)" },
  WARM: { color: "#a78bfa", bg: "rgba(96,165,250,0.10)", border: "rgba(96,165,250,0.22)" },
};

export default function PipelinePreview() {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <section
      className="py-20 px-6 border-t border-white/6"
      style={{ background: "linear-gradient(180deg, #0d0520 0%, #0d1220 100%)" }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-2" style={{ color: "#a78bfa" }}>Live pipeline</p>
            <h2
              className="font-extrabold text-white"
              style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Your pipeline is already moving
            </h2>
          </div>
          <p className="text-xs text-white/25 font-mono" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            Updated 2 min ago · 38 hot leads
          </p>
        </div>

        {/* Signal rows */}
        <div
          className="rounded-2xl border border-white/8 overflow-hidden divide-y divide-white/6"
          style={{ background: "rgba(255,255,255,0.02)" }}
        >
          {signals.map((s, i) => {
            const isOpen = expanded === i;
            const status = statusConfig[s.status as keyof typeof statusConfig];
            const SignalIcon = signalIcons[s.signalType] || Zap;

            return (
              <div
                key={i}
                className="transition-colors"
                style={{ background: isOpen ? "rgba(124,58,237,0.05)" : undefined }}
              >
                {/* Main row */}
                <button
                  onClick={() => setExpanded(isOpen ? null : i)}
                  className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-white/3 transition-colors"
                >
                  {/* Signal icon */}
                  <div
                    className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
                  >
                    <SignalIcon className="h-3.5 w-3.5 text-white/40" />
                  </div>

                  {/* Company + signal */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white">{s.company}</span>
                      <span className="text-[10px] font-bold text-white/25 uppercase tracking-widest">{s.industry}</span>
                    </div>
                    <p className="text-xs text-white/40 truncate mt-0.5">{s.signal}</p>
                  </div>

                  {/* Score */}
                  <div className="hidden sm:flex flex-col items-end shrink-0">
                    <span
                      className="font-mono text-sm font-bold"
                      style={{
                        color: s.score >= 85 ? "#f87171" : s.score >= 70 ? "#a78bfa" : "#8b5cf6",
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      {s.score}
                    </span>
                    <span className="text-[10px] text-white/20">score</span>
                  </div>

                  {/* Status badge */}
                  <span
                    className="hidden sm:inline-flex shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full"
                    style={{ color: status.color, background: status.bg, border: `1px solid ${status.border}` }}
                  >
                    {s.status}
                  </span>

                  {/* Time */}
                  <span
                    className="hidden md:block text-[10px] font-mono text-white/20 shrink-0"
                    style={{ fontFamily: "'JetBrains Mono', monospace" }}
                  >
                    {s.time}
                  </span>

                  {/* Expand icon */}
                  {isOpen
                    ? <ChevronDown className="h-3.5 w-3.5 text-white/20 shrink-0" />
                    : <ChevronRight className="h-3.5 w-3.5 text-white/20 shrink-0" />
                  }
                </button>

                {/* Expanded action */}
                {isOpen && (
                  <div
                    className="px-5 pb-4 border-t border-white/6"
                    style={{ background: "rgba(124,58,237,0.04)" }}
                  >
                    <div className="flex items-start justify-between gap-4 pt-4">
                      <div className="flex items-start gap-2.5">
                        <Zap className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: "#a78bfa" }} />
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#a78bfa" }}>
                            Recommended action
                          </p>
                          <p className="text-sm text-white/65">{s.action}</p>
                        </div>
                      </div>
                      <button className="shrink-0 flex items-center gap-1.5 text-xs font-semibold text-white px-3 py-1.5 rounded-lg transition-colors" style={{ background: "#7c3aed" }}>
                        Approve
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-white/20">Showing 5 of 247 active opportunities</p>
          <Link
            href="/results?url="
            className="flex items-center gap-1.5 text-xs font-semibold transition-colors" style={{ color: "#a78bfa" }}
          >
            Activate SIGNAL
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
