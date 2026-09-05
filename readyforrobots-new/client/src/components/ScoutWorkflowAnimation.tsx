/**
 * ScoutWorkflowAnimation — SIGNAL pipeline visualization (Identify → Develop → Connect).
 * Ported from rfr_cursor_package/frontend/components/ScoutWorkflowAnimation.tsx
 */
import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

type Track = "sales" | "partnership";

interface Cycle {
  track: Track;
  trackLabel: string;
  company: string;
  industry: string;
  robotType: string;
  robotColor: string;
  signal: string;
  score: number;
  scoreLabel: string;
  outreachLines: string[];
  sentLabel: string;
}

const CYCLES: Cycle[] = [
  {
    track: "sales",
    trackLabel: "SALES LEAD",
    company: "Apex Logistics",
    industry: "3PL · Midwest US",
    robotType: "Warehouse AMR",
    robotColor: "#03DAC5",
    signal: "3 DC expansions · labor shortage filing",
    score: 91,
    scoreLabel: "High automation fit",
    outreachLines: [
      "Hi Sarah — saw Apex is expanding",
      "three DCs in Q3. We help 3PLs deploy",
      "AMRs before the RFP drops.",
    ],
    sentLabel: "Outreach sent · 2 min ago",
  },
  {
    track: "partnership",
    trackLabel: "PARTNERSHIP",
    company: "Meridian Integrators",
    industry: "Systems Integrator · 6 regions",
    robotType: "Industrial Arm",
    robotColor: "#059669",
    signal: "Hiring automation engineers · CapEx signal",
    score: 87,
    scoreLabel: "Strong channel fit",
    outreachLines: [
      "Hi Marcus — Meridian's push into",
      "industrial automation is a natural",
      "fit for a co-sell partnership.",
    ],
    sentLabel: "Intro sent · just now",
  },
  {
    track: "sales",
    trackLabel: "SALES LEAD",
    company: "FreshRoute Foods",
    industry: "Food Processing · Southeast US",
    robotType: "Service Robot",
    robotColor: "#FFB000",
    signal: "OSHA filing · sanitation labor gap",
    score: 84,
    scoreLabel: "Strong automation fit",
    outreachLines: [
      "Hi Priya — FreshRoute's OSHA filing",
      "points to a sanitation gap our service",
      "robots solve in under 30 days.",
    ],
    sentLabel: "Outreach sent · 8 min ago",
  },
];

const STAGE_DURATIONS = [4000, 4500, 5000] as const;
const BETWEEN_CYCLES = 900;

export type ScoutWorkflowStage = 0 | 1 | 2;
const STAGE_LABELS = ["Discover", "Develop", "Close"];

type ScoutWorkflowAnimationProps = {
  onStageChange?: (stage: ScoutWorkflowStage) => void;
  className?: string;
  /** Inside ScoutHeroShowcase — no outer chrome or phase tabs (parent provides). */
  embedded?: boolean;
};

export default function ScoutWorkflowAnimation({
  onStageChange,
  className = "",
  embedded = false,
}: ScoutWorkflowAnimationProps) {
  const [cycleIdx, setCycleIdx] = useState(0);
  const [stage, setStage] = useState<ScoutWorkflowStage>(0);
  const [scoreProgress, setScoreProgress] = useState(0);
  const [outreachIdx, setOutreachIdx] = useState(0);
  const [sent, setSent] = useState(false);
  const [fading, setFading] = useState(false);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scoreTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const outreachTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const cycle = CYCLES[cycleIdx % CYCLES.length];

  useEffect(() => {
    onStageChange?.(stage);
  }, [stage, onStageChange]);

  useEffect(() => {
    setScoreProgress(0);
    setOutreachIdx(0);
    setSent(false);
  }, [stage, cycleIdx]);

  useEffect(() => {
    if (stage !== 1) return;
    let v = 0;
    const step = cycle.score / 100;
    scoreTimer.current = setInterval(() => {
      v += step;
      setScoreProgress(Math.min(Math.round(v), cycle.score));
      if (v >= cycle.score && scoreTimer.current)
        clearInterval(scoreTimer.current);
    }, 20);
    return () => {
      if (scoreTimer.current) clearInterval(scoreTimer.current);
    };
  }, [stage, cycleIdx, cycle.score]);

  useEffect(() => {
    if (stage !== 2) return;
    let idx = 0;
    outreachTimer.current = setInterval(() => {
      idx++;
      setOutreachIdx(idx);
      if (idx >= cycle.outreachLines.length) {
        if (outreachTimer.current) clearInterval(outreachTimer.current);
        setTimeout(() => setSent(true), 800);
      }
    }, 700);
    return () => {
      if (outreachTimer.current) clearInterval(outreachTimer.current);
    };
  }, [stage, cycleIdx, cycle.outreachLines.length]);

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      if (stage < 2) {
        setStage(s => (s + 1) as ScoutWorkflowStage);
      } else {
        setFading(true);
        setTimeout(() => {
          setCycleIdx(c => c + 1);
          setStage(0);
          setFading(false);
        }, BETWEEN_CYCLES);
      }
    }, STAGE_DURATIONS[stage]);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [stage, cycleIdx]);

  const isPartnership = cycle.track === "partnership";
  const sources = [
    "job_boards",
    "earnings_calls",
    "osha_filings",
    "real_estate_permits",
  ];

  const shellStyle = embedded
    ? {
        background: "transparent",
        border: "none",
        borderRadius: 0,
        opacity: fading ? 0 : 1,
        transition: "opacity 0.4s ease",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        boxShadow: "none",
      }
    : {
        background: "#130d2a",
        border: "1px solid rgba(124,58,237,0.2)",
        borderRadius: "16px",
        opacity: fading ? 0 : 1,
        transition: "opacity 0.4s ease",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        boxShadow:
          "0 0 0 1px rgba(124,58,237,0.1), 0 0 40px rgba(124,58,237,0.08), 0 24px 48px rgba(0,0,0,0.5)",
      };

  return (
    <div
      className={`flex flex-col overflow-hidden w-full h-full ${className}`.trim()}
      style={shellStyle}
    >
      {!embedded && (
        <>
          <div
            className="flex items-center justify-between px-4 py-2.5 shrink-0"
            style={{
              background: "rgba(124,58,237,0.06)",
              borderBottom: "1px solid rgba(124,58,237,0.15)",
            }}
          >
            <div className="flex items-center gap-1.5" aria-hidden>
              <span
                className="h-3 w-3 rounded-full"
                style={{ background: "#ff5f57" }}
              />
              <span
                className="h-3 w-3 rounded-full"
                style={{ background: "#febc2e" }}
              />
              <span
                className="h-3 w-3 rounded-full"
                style={{ background: "#28c840" }}
              />
            </div>
            <span className="rfr-scout-wordmark text-[10px] text-white/40">
              signal · live pipeline
            </span>
            <div className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 rounded-full animate-pulse"
                style={{ background: "#03DAC5" }}
              />
              <span
                className="text-[11px] font-bold"
                style={{ color: "#03DAC5" }}
              >
                LIVE
              </span>
            </div>
          </div>

          <div
            className="flex shrink-0"
            style={{
              borderBottom: "1px solid rgba(124,58,237,0.12)",
              background: "rgba(0,0,0,0.2)",
            }}
          >
            {STAGE_LABELS.map((label, i) => {
              const isActive = stage === i;
              const isDone = stage > i;
              return (
                <div
                  key={label}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 text-[11px] font-bold uppercase tracking-widest transition-all duration-500"
                  style={{
                    color: isDone
                      ? "rgba(3,218,197,0.55)"
                      : isActive
                        ? "#03DAC5"
                        : "rgba(255,255,255,0.22)",
                    background: isActive
                      ? "rgba(3,218,197,0.05)"
                      : "transparent",
                    borderBottom: isActive
                      ? "2px solid #03DAC5"
                      : "2px solid transparent",
                    borderRight:
                      i < 2 ? "1px solid rgba(255,255,255,0.07)" : "none",
                  }}
                >
                  {isDone ? (
                    <CheckCircle2 className="h-3 w-3 shrink-0" />
                  ) : isActive ? (
                    <Loader2 className="h-3 w-3 shrink-0 animate-spin" />
                  ) : (
                    <Circle className="h-3 w-3 shrink-0" />
                  )}
                  {label}
                </div>
              );
            })}
          </div>
        </>
      )}

      <div
        className={`px-4 py-3 shrink-0 ${embedded ? "border-b border-gray-100 bg-emerald-50/60" : ""}`}
        style={
          embedded
            ? undefined
            : {
                borderBottom: "1px solid rgba(124,58,237,0.12)",
                background: "rgba(124,58,237,0.06)",
              }
        }
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-sm font-bold ${embedded ? "text-gray-900" : "text-white"}`}
          >
            {cycle.company}
          </span>
          <span
            className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm"
            style={{
              color: cycle.robotColor,
              background: `${cycle.robotColor}${embedded ? "14" : "1a"}`,
              border: `1px solid ${cycle.robotColor}${embedded ? "33" : "40"}`,
            }}
          >
            {cycle.robotType}
          </span>
          <span
            className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm"
            style={
              isPartnership
                ? {
                    color: embedded ? "#047857" : "#a78bfa",
                    background: embedded
                      ? "rgba(4,120,87,0.08)"
                      : "rgba(167,139,250,0.12)",
                    border: embedded
                      ? "1px solid rgba(4,120,87,0.22)"
                      : "1px solid rgba(167,139,250,0.3)",
                  }
                : embedded
                  ? {
                      color: "#6b7280",
                      background: "#f3f4f6",
                      border: "1px solid #e5e7eb",
                    }
                  : {
                      color: "rgba(255,255,255,0.4)",
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.1)",
                    }
            }
          >
            {cycle.trackLabel}
          </span>
        </div>
        <p
          className={`text-[11px] mt-1 ${embedded ? "text-gray-500" : "text-white/35"}`}
        >
          {cycle.industry}
        </p>
      </div>

      <div
        className={`flex items-center gap-3 px-4 py-2.5 shrink-0 ${embedded ? "border-b border-gray-100 bg-white" : ""}`}
        style={
          embedded
            ? undefined
            : { borderBottom: "1px solid rgba(124,58,237,0.1)" }
        }
      >
        <span
          className={`text-[10px] font-bold uppercase tracking-widest shrink-0 ${embedded ? "text-emerald-700" : ""}`}
          style={embedded ? undefined : { color: "rgba(255,255,255,0.25)" }}
        >
          signal
        </span>
        <span
          className={`text-[11px] truncate ${embedded ? "text-gray-700" : "text-white/60"}`}
        >
          {cycle.signal}
        </span>
      </div>

      <div
        className="flex-1 px-4 py-4 flex flex-col gap-3"
        style={{ minHeight: "130px" }}
      >
        {stage === 0 && (
          <div className="flex flex-col gap-3 rfr-animate-fade-in">
            <div className="flex items-center gap-2">
              <span
                className={`h-1.5 w-1.5 rounded-full animate-pulse shrink-0 ${embedded ? "bg-emerald-500" : ""}`}
                style={embedded ? undefined : { background: "#03DAC5" }}
              />
              <span
                className={`text-[11px] ${embedded ? "text-emerald-700" : ""}`}
                style={embedded ? undefined : { color: "#03DAC5" }}
              >
                Scanning 150+ sources for buying signals…
              </span>
            </div>
            <div
              className={`flex flex-col divide-y rounded ${embedded ? "border border-gray-200 bg-gray-50 divide-gray-200" : ""}`}
              style={
                embedded
                  ? undefined
                  : {
                      background: "rgba(124,58,237,0.06)",
                      border: "1px solid rgba(124,58,237,0.15)",
                      borderRadius: "4px",
                    }
              }
            >
              {sources.map((src, i) => (
                <div
                  key={src}
                  className={`flex items-center gap-3 px-3 py-2 transition-all duration-500 ${embedded && i < 2 ? "bg-emerald-50/80" : ""}`}
                  style={
                    embedded
                      ? undefined
                      : {
                          borderBottom:
                            i < sources.length - 1
                              ? "1px solid rgba(255,255,255,0.05)"
                              : "none",
                          background:
                            i < 2 ? "rgba(3,218,197,0.03)" : "transparent",
                        }
                  }
                >
                  <span
                    className={`text-[11px] w-4 text-center font-bold shrink-0 ${embedded ? (i < 2 ? "text-emerald-600" : "text-gray-300") : ""}`}
                    style={
                      embedded
                        ? undefined
                        : {
                            color: i < 2 ? "#03DAC5" : "rgba(255,255,255,0.18)",
                          }
                    }
                  >
                    {i < 2 ? "✓" : "·"}
                  </span>
                  <span
                    className={`text-[11px] flex-1 ${embedded ? (i < 2 ? "text-gray-800" : "text-gray-400") : ""}`}
                    style={
                      embedded
                        ? undefined
                        : {
                            color:
                              i < 2
                                ? "rgba(255,255,255,0.65)"
                                : "rgba(255,255,255,0.22)",
                          }
                    }
                  >
                    {src}
                  </span>
                  {i < 2 && (
                    <span
                      className={`text-[10px] ${embedded ? "text-emerald-600" : ""}`}
                      style={embedded ? undefined : { color: "#03DAC5" }}
                    >
                      match
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {stage === 1 && (
          <div className="flex flex-col gap-3 rfr-animate-fade-in">
            <div className="flex items-center justify-between">
              <span
                className={`text-[10px] font-bold uppercase tracking-widest ${embedded ? "text-gray-500" : ""}`}
                style={
                  embedded ? undefined : { color: "rgba(255,255,255,0.3)" }
                }
              >
                fit_score
              </span>
              <div className="flex items-end gap-1.5">
                <span
                  className={`text-2xl font-extrabold tabular-nums leading-none ${embedded ? "text-emerald-600" : ""}`}
                  style={embedded ? undefined : { color: "#03DAC5" }}
                >
                  {scoreProgress}
                </span>
                <span
                  className={`text-xs mb-0.5 ${embedded ? "text-gray-400" : "text-white/25"}`}
                >
                  / 100
                </span>
              </div>
            </div>
            <div
              className={`h-1.5 overflow-hidden rounded-sm ${embedded ? "bg-gray-200" : ""}`}
              style={
                embedded
                  ? undefined
                  : {
                      background: "rgba(255,255,255,0.08)",
                      borderRadius: "2px",
                    }
              }
            >
              <div
                className="h-full transition-all duration-75 rounded-sm"
                style={{
                  width: `${scoreProgress}%`,
                  background: embedded
                    ? `linear-gradient(90deg, #059669, ${cycle.robotColor})`
                    : `linear-gradient(90deg, #03DAC5, ${cycle.robotColor})`,
                }}
              />
            </div>
            <div
              className={`flex flex-col rounded ${embedded ? "border border-gray-200 bg-gray-50" : ""}`}
              style={
                embedded
                  ? undefined
                  : {
                      background: "rgba(124,58,237,0.06)",
                      border: "1px solid rgba(124,58,237,0.15)",
                      borderRadius: "4px",
                    }
              }
            >
              {[
                { key: "labor_pain", val: "high", threshold: 30 },
                { key: "expansion_stage", val: "active", threshold: 55 },
                {
                  key: "automation_fit",
                  val: cycle.robotType.toLowerCase(),
                  threshold: 75,
                },
              ].map(({ key, val, threshold }, i) => {
                const done = scoreProgress >= threshold;
                return (
                  <div
                    key={key}
                    className={`flex items-center gap-3 px-3 py-2 transition-all duration-300 ${embedded && done ? "bg-emerald-50/80" : ""}`}
                    style={
                      embedded
                        ? { borderBottom: i < 2 ? "1px solid #e5e7eb" : "none" }
                        : {
                            borderBottom:
                              i < 2
                                ? "1px solid rgba(255,255,255,0.05)"
                                : "none",
                            background: done
                              ? "rgba(3,218,197,0.03)"
                              : "transparent",
                          }
                    }
                  >
                    <span
                      className={`text-[11px] w-4 text-center font-bold shrink-0 transition-colors duration-300 ${embedded ? (done ? "text-emerald-600" : "text-gray-300") : ""}`}
                      style={
                        embedded
                          ? undefined
                          : {
                              color: done
                                ? "#03DAC5"
                                : "rgba(255,255,255,0.18)",
                            }
                      }
                    >
                      {done ? "✓" : "·"}
                    </span>
                    <span
                      className={`text-[11px] flex-1 ${embedded ? "text-gray-600" : "text-white/40"}`}
                    >
                      {key}
                    </span>
                    <span
                      className={`text-[11px] font-bold transition-colors duration-300 ${embedded ? (done ? "text-gray-900" : "text-gray-400") : ""}`}
                      style={
                        embedded
                          ? undefined
                          : {
                              color: done
                                ? "rgba(255,255,255,0.75)"
                                : "rgba(255,255,255,0.18)",
                            }
                      }
                    >
                      {val}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-[11px]" style={{ color: cycle.robotColor }}>
              {cycle.scoreLabel}
            </p>
          </div>
        )}

        {stage === 2 && (
          <div className="flex flex-col gap-3 rfr-animate-fade-in">
            <span
              className={`text-[10px] font-bold uppercase tracking-widest ${embedded ? "text-gray-500" : ""}`}
              style={embedded ? undefined : { color: "rgba(255,255,255,0.3)" }}
            >
              draft_outreach
            </span>
            <div
              className={`flex flex-col gap-1 px-3 py-3 rounded ${embedded ? "border border-gray-200 bg-gray-50" : ""}`}
              style={
                embedded
                  ? { fontFamily: "'Inter', system-ui, sans-serif" }
                  : {
                      background: "rgba(124,58,237,0.06)",
                      border: "1px solid rgba(124,58,237,0.15)",
                      borderRadius: "4px",
                      fontFamily: "'Inter', system-ui, sans-serif",
                    }
              }
            >
              {cycle.outreachLines.map((line, i) => (
                <p
                  key={i}
                  className="text-[12px] leading-relaxed transition-all duration-500"
                  style={{
                    color:
                      i < outreachIdx
                        ? embedded
                          ? "#374151"
                          : "rgba(255,255,255,0.72)"
                        : "transparent",
                    transform:
                      i < outreachIdx ? "translateY(0)" : "translateY(4px)",
                  }}
                >
                  {line}
                </p>
              ))}
            </div>
            {sent && (
              <div
                className={`flex items-center gap-2 px-3 py-2 rfr-animate-fade-in rounded ${embedded ? "border border-emerald-200 bg-emerald-50" : ""}`}
                style={
                  embedded
                    ? undefined
                    : {
                        background: "rgba(3,218,197,0.07)",
                        border: "1px solid rgba(3,218,197,0.2)",
                        borderRadius: "4px",
                      }
                }
              >
                <CheckCircle2
                  className={`h-3.5 w-3.5 shrink-0 ${embedded ? "text-emerald-600" : ""}`}
                  style={embedded ? undefined : { color: "#03DAC5" }}
                />
                <span
                  className={`text-[11px] font-semibold ${embedded ? "text-emerald-700" : ""}`}
                  style={embedded ? undefined : { color: "#03DAC5" }}
                >
                  {cycle.sentLabel}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {!embedded && (
        <div
          className="flex items-center justify-between px-4 py-2 shrink-0"
          style={{
            background: "rgba(124,58,237,0.06)",
            borderTop: "1px solid rgba(124,58,237,0.15)",
          }}
        >
          <span className="rfr-scout-wordmark text-[9px] text-white/30">
            signal · {STAGE_LABELS[stage].toLowerCase()}
          </span>
          <span className="text-[10px] text-white/25">
            {(cycleIdx % CYCLES.length) + 1} / {CYCLES.length} opportunities
          </span>
        </div>
      )}
    </div>
  );
}

export { STAGE_LABELS };
