/**
 * ScoutHeroShowcase — single unified shell: 5-step rail + live SCOUT demo.
 */
import { useState } from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import ScoutPipelineDiagram from "@/components/ScoutPipelineDiagram";
import ScoutWorkflowAnimation, {
  STAGE_LABELS,
  type ScoutWorkflowStage,
} from "@/components/ScoutWorkflowAnimation";

export default function ScoutHeroShowcase() {
  const [stage, setStage] = useState<ScoutWorkflowStage>(0);

  return (
    <div
      className="w-full overflow-hidden"
      style={{
        background: "#130d2a",
        border: "1px solid rgba(124,58,237,0.28)",
        borderRadius: 16,
        boxShadow:
          "0 0 0 1px rgba(255,176,0,0.05), 0 0 48px rgba(124,58,237,0.15), 0 24px 48px rgba(0,0,0,0.5)",
      }}
    >
      {/* Shared chrome */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{
          background: "rgba(124,58,237,0.08)",
          borderBottom: "1px solid rgba(124,58,237,0.18)",
        }}
      >
        <div className="flex items-center gap-1.5" aria-hidden>
          <span className="h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
        </div>
        <span
          className="text-[10px] font-bold uppercase tracking-[0.2em]"
          style={{ color: "rgba(255,255,255,0.45)", fontFamily: "JetBrains Mono, monospace" }}
        >
          scout · pipeline
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
          <span className="text-[10px] font-bold" style={{ color: "#03DAC5" }}>
            LIVE
          </span>
        </span>
      </div>

      {/* Phase tabs — drive both rail + demo */}
      <div
        className="flex"
        style={{ borderBottom: "1px solid rgba(124,58,237,0.15)", background: "rgba(0,0,0,0.25)" }}
      >
        {STAGE_LABELS.map((label, i) => {
          const isActive = stage === i;
          const isDone = stage > i;
          return (
            <div
              key={label}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 text-[10px] sm:text-[11px] font-bold uppercase tracking-widest transition-all duration-500"
              style={{
                color: isDone ? "rgba(3,218,197,0.55)" : isActive ? "#03DAC5" : "rgba(255,255,255,0.22)",
                background: isActive ? "rgba(3,218,197,0.06)" : "transparent",
                borderBottom: isActive ? "2px solid #03DAC5" : "2px solid transparent",
                borderRight: i < 2 ? "1px solid rgba(255,255,255,0.06)" : "none",
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

      {/* Rail + demo — one surface */}
      <div className="flex flex-col sm:flex-row items-stretch min-h-[320px]">
        <aside
          className="relative shrink-0 sm:w-[200px] md:w-[210px] flex flex-col border-b sm:border-b-0 sm:border-r"
          style={{
            background: "rgba(0,0,0,0.2)",
            borderColor: "rgba(124,58,237,0.15)",
          }}
        >
          <div
            className="px-3 py-2 flex items-center justify-between gap-2"
            style={{ borderBottom: "1px solid rgba(124,58,237,0.1)" }}
          >
            <span
              className="text-[9px] font-bold uppercase tracking-[0.18em]"
              style={{ color: "#a78bfa", fontFamily: "JetBrains Mono, monospace" }}
            >
              5 stages
            </span>
            <span className="text-[9px] text-white/35 hidden sm:inline">feeds →</span>
          </div>
          <ScoutPipelineDiagram workflowStage={stage} embedded className="flex-1" />
          {/* Bridge glow into demo (desktop) */}
          <div
            className="hidden sm:block absolute top-12 right-0 w-[3px] h-[calc(100%-3rem)] pointer-events-none"
            style={{
              background: `linear-gradient(180deg, transparent, ${stage === 0 ? "#a78bfa" : stage === 1 ? "#FFB000" : "#03DAC5"}, transparent)`,
              boxShadow: `0 0 12px ${stage === 0 ? "rgba(167,139,250,0.5)" : stage === 1 ? "rgba(255,176,0,0.45)" : "rgba(3,218,197,0.45)"}`,
            }}
          />
        </aside>

        <div
          className="flex-1 min-w-0 flex flex-col"
          style={{
            borderTop: "none",
          }}
        >
          <div
            className="hidden sm:flex px-4 py-1.5 items-center gap-2"
            style={{
              borderBottom: "1px solid rgba(124,58,237,0.1)",
              background: "rgba(3,218,197,0.04)",
            }}
          >
            <span className="text-[9px] uppercase tracking-widest" style={{ color: "#03DAC5" }}>
              live opportunity
            </span>
            <span className="text-[9px] text-white/25">← synced to {STAGE_LABELS[stage].toLowerCase()}</span>
          </div>
          <div className="flex-1 p-0">
            <ScoutWorkflowAnimation embedded onStageChange={setStage} className="h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
