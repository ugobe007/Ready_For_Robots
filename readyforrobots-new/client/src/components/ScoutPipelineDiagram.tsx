/**
 * ScoutPipelineDiagram — tight 5-step hero visual for How It Works.
 * Static stack with cycling highlight (POP) — not bullet copy.
 */
import { useEffect, useState } from "react";
import {
  Search,
  Cpu,
  FileText,
  CheckCircle,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

const STEPS: {
  num: string;
  title: string;
  tag: string;
  icon: LucideIcon;
  accent: string;
  glow: string;
}[] = [
  {
    num: "01",
    title: "Signal Detection",
    tag: "150+ sources · 24/7",
    icon: Search,
    accent: "#a78bfa",
    glow: "rgba(167, 139, 250, 0.35)",
  },
  {
    num: "02",
    title: "AI Scoring",
    tag: "Confidence · Urgency · Fit",
    icon: Cpu,
    accent: "#818cf8",
    glow: "rgba(129, 140, 248, 0.35)",
  },
  {
    num: "03",
    title: "SCOUT Drafts",
    tag: "Trigger-aware outreach",
    icon: FileText,
    accent: "#FFB000",
    glow: "rgba(255, 176, 0, 0.45)",
  },
  {
    num: "04",
    title: "You Review",
    tag: "Manual · Assisted · Auto",
    icon: CheckCircle,
    accent: "#c4b5fd",
    glow: "rgba(196, 181, 253, 0.3)",
  },
  {
    num: "05",
    title: "Pipeline Advances",
    tag: "Track · follow-up · escalate",
    icon: TrendingUp,
    accent: "#03DAC5",
    glow: "rgba(3, 218, 197, 0.4)",
  },
];

const CYCLE_MS = 2200;

type Props = {
  variant?: "hero" | "compact";
  className?: string;
};

export default function ScoutPipelineDiagram({ variant = "hero", className = "" }: Props) {
  const [active, setActive] = useState(2);

  useEffect(() => {
    const id = setInterval(() => setActive((i) => (i + 1) % STEPS.length), CYCLE_MS);
    return () => clearInterval(id);
  }, []);

  const tight = variant === "hero";

  return (
    <div
      className={`w-full max-w-md lg:max-w-lg ${className}`}
      aria-label="SCOUT five-step pipeline: detect, score, draft, review, advance"
    >
      <style>{`
        @keyframes scout-pipeline-pop {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        @keyframes scout-pipeline-glow {
          0%, 100% { opacity: 0.55; }
          50% { opacity: 1; }
        }
        .scout-pipeline-step-active {
          animation: scout-pipeline-pop 2.2s ease-in-out infinite;
        }
        .scout-pipeline-rail-pulse {
          animation: scout-pipeline-glow 2.2s ease-in-out infinite;
        }
      `}</style>

      <div
        className="overflow-hidden"
        style={{
          background: "linear-gradient(145deg, #130d2a 0%, #0d0520 55%, #0a1628 100%)",
          border: "1px solid rgba(124, 58, 237, 0.28)",
          borderRadius: tight ? 18 : 14,
          boxShadow:
            "0 0 0 1px rgba(255,176,0,0.06), 0 0 60px rgba(124,58,237,0.18), 0 28px 56px rgba(0,0,0,0.55)",
        }}
      >
        <div
          className="flex items-center justify-between px-4 py-2.5"
          style={{
            borderBottom: "1px solid rgba(124,58,237,0.18)",
            background: "rgba(124,58,237,0.07)",
          }}
        >
          <span
            className="text-[10px] font-bold uppercase tracking-[0.22em]"
            style={{ color: "rgba(255,255,255,0.45)", fontFamily: "JetBrains Mono, monospace" }}
          >
            scout · 5-stage engine
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full animate-pulse"
              style={{ background: "#03DAC5", boxShadow: "0 0 8px #03DAC5" }}
            />
            <span className="text-[10px] font-bold" style={{ color: "#03DAC5" }}>
              LIVE
            </span>
          </span>
        </div>

        <div className={tight ? "px-3 py-3 sm:px-4 sm:py-4" : "px-3 py-3"}>
          <div className="relative flex flex-col gap-1">
            {/* vertical connector */}
            <div
              className="absolute left-[22px] top-3 bottom-3 w-px pointer-events-none"
              style={{
                background:
                  "linear-gradient(180deg, #7c3aed 0%, #FFB000 38%, #03DAC5 100%)",
                opacity: 0.55,
              }}
            />

            {STEPS.map((step, i) => {
              const Icon = step.icon;
              const isActive = active === i;
              const isScout = i === 2;

              return (
                <div
                  key={step.num}
                  className={`relative flex items-stretch gap-2.5 sm:gap-3 rounded-xl transition-all duration-500 ${
                    isActive ? "scout-pipeline-step-active" : ""
                  }`}
                  style={{
                    padding: tight ? "7px 8px 7px 4px" : "6px 6px 6px 2px",
                    background: isActive
                      ? `linear-gradient(90deg, ${step.glow} 0%, rgba(13,5,32,0.4) 70%)`
                      : "transparent",
                    border: isActive
                      ? `1px solid ${isScout ? "rgba(255,176,0,0.55)" : "rgba(124,58,237,0.35)"}`
                      : "1px solid transparent",
                    boxShadow: isActive
                      ? isScout
                        ? "0 0 28px rgba(255,176,0,0.22), inset 0 1px 0 rgba(255,255,255,0.06)"
                        : `0 0 20px ${step.glow}`
                      : "none",
                  }}
                >
                  <div className="flex flex-col items-center shrink-0 w-11 pt-0.5">
                    <span
                      className={`font-mono text-[11px] font-bold leading-none mb-1.5 transition-colors duration-500 ${
                        isActive ? "scout-pipeline-rail-pulse" : ""
                      }`}
                      style={{
                        color: isActive ? step.accent : "rgba(124,58,237,0.35)",
                        fontFamily: "JetBrains Mono, monospace",
                      }}
                    >
                      {step.num}
                    </span>
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-500"
                      style={{
                        background: isActive ? `${step.accent}22` : "rgba(124,58,237,0.08)",
                        border: `1px solid ${isActive ? step.accent : "rgba(124,58,237,0.2)"}`,
                        boxShadow: isActive ? `0 0 14px ${step.glow}` : "none",
                      }}
                    >
                      <Icon
                        size={15}
                        strokeWidth={2.25}
                        style={{ color: isActive ? step.accent : "#6b7280" }}
                      />
                    </div>
                  </div>

                  <div className="flex min-w-0 flex-1 flex-col justify-center py-0.5">
                    <p
                      className="text-[13px] font-bold leading-tight truncate"
                      style={{
                        fontFamily: "Sora, sans-serif",
                        color: isActive ? "#ffffff" : "rgba(255,255,255,0.72)",
                      }}
                    >
                      {step.title}
                      {isScout && (
                        <span
                          className="ml-1.5 inline-block rounded px-1 py-px text-[9px] font-bold uppercase tracking-wider align-middle"
                          style={{
                            background: "rgba(255,176,0,0.2)",
                            color: "#FFB000",
                            border: "1px solid rgba(255,176,0,0.35)",
                          }}
                        >
                          core
                        </span>
                      )}
                    </p>
                    <p
                      className="text-[10px] leading-snug truncate mt-0.5"
                      style={{
                        color: isActive ? step.accent : "#6b7280",
                        fontFamily: "JetBrains Mono, monospace",
                        opacity: isActive ? 0.95 : 0.7,
                      }}
                    >
                      {step.tag}
                    </p>
                  </div>

                  {isActive && (
                    <div
                      className="hidden sm:block w-1 shrink-0 self-stretch rounded-full my-1"
                      style={{
                        background: `linear-gradient(180deg, transparent, ${step.accent}, transparent)`,
                        boxShadow: `0 0 12px ${step.accent}`,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div
          className="flex items-center justify-between gap-2 px-4 py-2"
          style={{
            borderTop: "1px solid rgba(124,58,237,0.12)",
            background: "rgba(0,0,0,0.25)",
          }}
        >
          <span className="text-[9px] uppercase tracking-[0.18em]" style={{ color: "#6b7280" }}>
            signal → score → draft → approve → close
          </span>
          <span
            className="text-[10px] font-mono font-bold tabular-nums"
            style={{ color: "#FFB000" }}
          >
            &lt;2 min
          </span>
        </div>
      </div>
    </div>
  );
}
