/**
 * ScoutHeroShowcase — merged hero: live SCOUT animation + synced 5-step rail.
 */
import { useState } from "react";
import ScoutPipelineDiagram from "@/components/ScoutPipelineDiagram";
import ScoutWorkflowAnimation, { type ScoutWorkflowStage } from "@/components/ScoutWorkflowAnimation";

export default function ScoutHeroShowcase() {
  const [stage, setStage] = useState<ScoutWorkflowStage>(0);

  return (
    <div className="w-full">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p
            className="text-[10px] font-bold uppercase tracking-[0.22em] mb-1"
            style={{ color: "#7c3aed", fontFamily: "JetBrains Mono, monospace" }}
          >
            SCOUT in motion
          </p>
          <p className="text-sm font-bold text-white/90" style={{ fontFamily: "Sora, sans-serif" }}>
            <span style={{ color: stage === 0 ? "#03DAC5" : "rgba(255,255,255,0.35)" }}>Identify</span>
            <span className="text-white/25 mx-2">→</span>
            <span style={{ color: stage === 1 ? "#03DAC5" : "rgba(255,255,255,0.35)" }}>Develop</span>
            <span className="text-white/25 mx-2">→</span>
            <span style={{ color: stage === 2 ? "#03DAC5" : "rgba(255,255,255,0.35)" }}>Connect</span>
          </p>
        </div>
        <p className="text-[11px] max-w-[200px] text-right leading-snug" style={{ color: "#6b7280" }}>
          Rail highlights the five stages behind each phase
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-3 md:gap-4 items-stretch">
        <ScoutPipelineDiagram workflowStage={stage} variant="rail" className="shrink-0 mx-auto md:mx-0" />
        <div className="flex-1 min-w-0">
          <ScoutWorkflowAnimation onStageChange={setStage} />
        </div>
      </div>
    </div>
  );
}
