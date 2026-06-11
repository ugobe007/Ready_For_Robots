/**
 * ScoutPipelineDiagram — 5-step rail synced to ScoutWorkflowAnimation stages.
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
import type { ScoutWorkflowStage } from "@/components/ScoutWorkflowAnimation";

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
    title: "SIGNAL Drafts",
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

const STAGE_LABELS = ["Identify", "Develop", "Connect"] as const;

/** Steps highlighted per workflow animation stage */
const STAGE_HIGHLIGHTS: Record<ScoutWorkflowStage, number[]> = {
  0: [0, 1],
  1: [2, 3],
  2: [4],
};

const CYCLE_MS = 2200;

type Props = {
  variant?: "hero" | "rail" | "compact";
  className?: string;
  /** When set, highlights sync to SIGNAL in motion (no independent cycling). */
  workflowStage?: ScoutWorkflowStage;
  /** Flat list inside ScoutHeroShowcase — no nested card chrome. */
  embedded?: boolean;
};

export default function ScoutPipelineDiagram({
  variant = "hero",
  className = "",
  workflowStage,
  embedded = false,
}: Props) {
  const [soloActive, setSoloActive] = useState(0);
  const synced = workflowStage !== undefined;
  const rail = embedded || variant === "rail";

  useEffect(() => {
    if (synced) return;
    const id = setInterval(() => setSoloActive((i) => (i + 1) % STEPS.length), CYCLE_MS);
    return () => clearInterval(id);
  }, [synced]);

  const activeIndices = synced ? STAGE_HIGHLIGHTS[workflowStage] : [soloActive];

  const stepsBlock = (
    <div className={embedded ? "px-2 py-2 flex-1" : rail ? "px-2 py-2" : "px-3 py-3 sm:px-4 sm:py-4"}>
          <div className="relative flex flex-col gap-0.5">
            <div
              className="absolute left-[18px] top-2 bottom-2 w-px pointer-events-none"
              style={{
                background: "linear-gradient(180deg, #7c3aed 0%, #FFB000 38%, #03DAC5 100%)",
                opacity: 0.5,
              }}
            />

            {STEPS.map((step, i) => {
              const Icon = step.icon;
              const isActive = activeIndices.includes(i);
              const isScout = i === 2;
              const isPrimary =
                synced &&
                ((workflowStage === 0 && i === 1) ||
                  (workflowStage === 1 && i === 3) ||
                  (workflowStage === 2 && i === 4));

              return (
                <div
                  key={step.num}
                  className={`relative flex items-stretch gap-2 rounded-lg transition-all duration-500 ${
                    isPrimary ? "scout-pipeline-step-active" : ""
                  }`}
                  style={{
                    padding: rail ? "5px 4px 5px 2px" : "7px 8px 7px 4px",
                    background: isActive
                      ? `linear-gradient(90deg, ${step.glow} 0%, rgba(13,5,32,0.35) 72%)`
                      : "transparent",
                    border: isActive
                      ? `1px solid ${isScout && isActive ? "rgba(255,176,0,0.5)" : "rgba(124,58,237,0.3)"}`
                      : "1px solid transparent",
                    opacity: synced && !isActive ? 0.42 : 1,
                  }}
                >
                  <div className={`flex flex-col items-center shrink-0 ${rail ? "w-9" : "w-11"} pt-0.5`}>
                    <span
                      className="font-mono text-[10px] font-bold leading-none mb-1"
                      style={{
                        color: isActive ? step.accent : "rgba(124,58,237,0.3)",
                        fontFamily: "JetBrains Mono, monospace",
                      }}
                    >
                      {step.num}
                    </span>
                    <div
                      className={`flex items-center justify-center rounded-md transition-all duration-500 ${rail ? "h-7 w-7" : "h-8 w-8"}`}
                      style={{
                        background: isActive ? `${step.accent}22` : "rgba(124,58,237,0.06)",
                        border: `1px solid ${isActive ? step.accent : "rgba(124,58,237,0.15)"}`,
                      }}
                    >
                      <Icon
                        size={rail ? 13 : 15}
                        strokeWidth={2.25}
                        style={{ color: isActive ? step.accent : "#6b7280" }}
                      />
                    </div>
                  </div>

                  <div className="flex min-w-0 flex-1 flex-col justify-center py-0.5">
                    <p
                      className={`font-bold leading-tight truncate ${rail ? "text-[11px]" : "text-[13px]"}`}
                      style={{
                        fontFamily: "Sora, sans-serif",
                        color: isActive ? "#ffffff" : "rgba(255,255,255,0.55)",
                      }}
                    >
                      {step.title}
                    </p>
                    {!rail && (
                      <p
                        className="text-[10px] leading-snug truncate mt-0.5"
                        style={{
                          color: isActive ? step.accent : "#6b7280",
                          fontFamily: "JetBrains Mono, monospace",
                        }}
                      >
                        {step.tag}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
    </div>
  );

  if (embedded) {
    return (
      <div className={`w-full h-full flex flex-col ${className}`} aria-label="SIGNAL five-step pipeline">
        <style>{`
          @keyframes scout-pipeline-pop {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
          }
          .scout-pipeline-step-active { animation: scout-pipeline-pop 2.4s ease-in-out infinite; }
        `}</style>
        {stepsBlock}
      </div>
    );
  }

  return (
    <div
      className={`w-full ${rail ? "max-w-[220px]" : "max-w-md lg:max-w-lg"} ${className}`}
      aria-label="SIGNAL five-step pipeline: detect, score, draft, review, advance"
    >
      <style>{`
        @keyframes scout-pipeline-pop {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        .scout-pipeline-step-active { animation: scout-pipeline-pop 2.4s ease-in-out infinite; }
      `}</style>

      <div
        className="overflow-hidden h-full"
        style={{
          background: "linear-gradient(145deg, #130d2a 0%, #0d0520 55%, #0a1628 100%)",
          border: synced ? "1px solid rgba(3, 218, 197, 0.22)" : "1px solid rgba(124, 58, 237, 0.28)",
          borderRadius: rail ? 14 : 18,
          boxShadow: synced
            ? "0 0 32px rgba(3,218,197,0.08), 0 16px 40px rgba(0,0,0,0.45)"
            : "0 0 0 1px rgba(255,176,0,0.06), 0 0 60px rgba(124,58,237,0.18), 0 28px 56px rgba(0,0,0,0.55)",
        }}
      >
        <div
          className="flex items-center justify-between px-3 py-2"
          style={{
            borderBottom: "1px solid rgba(124,58,237,0.18)",
            background: "rgba(124,58,237,0.07)",
          }}
        >
          <span
            className="text-[9px] font-bold uppercase tracking-[0.2em]"
            style={{ color: "rgba(255,255,255,0.45)", fontFamily: "JetBrains Mono, monospace" }}
          >
            {rail ? "5 stages" : "signal · 5-stage engine"}
          </span>
          {synced ? (
            <span className="text-[9px] font-bold uppercase tracking-wider" style={{ color: "#03DAC5" }}>
              {STAGE_LABELS[workflowStage!]}
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
              <span className="text-[9px] font-bold" style={{ color: "#03DAC5" }}>
                LIVE
              </span>
            </span>
          )}
        </div>

        {stepsBlock}

        {!rail && (
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
            <span className="text-[10px] font-mono font-bold" style={{ color: "#FFB000" }}>
              &lt;2 min
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
