/**
 * ScoutHeroShowcase — single unified shell: 5-step rail + live SIGNAL demo.
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
    <div className="w-full overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg shadow-emerald-100/30">
      <div className="flex items-center justify-between px-4 py-2.5 bg-emerald-50 border-b border-emerald-100">
        <div className="flex items-center gap-1.5" aria-hidden>
          <span className="h-3 w-3 rounded-full bg-red-400" />
          <span className="h-3 w-3 rounded-full bg-amber-400" />
          <span className="h-3 w-3 rounded-full bg-emerald-500" />
        </div>
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400 font-mono-data">
          signal · pipeline
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full animate-pulse bg-emerald-500" />
          <span className="text-[10px] font-bold text-emerald-600">LIVE</span>
        </span>
      </div>

      <div className="flex border-b border-gray-100 bg-slate-50">
        {STAGE_LABELS.map((label, i) => {
          const isActive = stage === i;
          const isDone = stage > i;
          return (
            <button
              type="button"
              key={label}
              onClick={() => setStage(i as ScoutWorkflowStage)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-[10px] sm:text-[11px] font-bold uppercase tracking-widest transition-all duration-500 border-b-2 ${
                isActive
                  ? "text-emerald-700 bg-emerald-50 border-emerald-600"
                  : isDone
                    ? "text-emerald-500/70 border-transparent"
                    : "text-gray-400 border-transparent hover:text-gray-600"
              } ${i < STAGE_LABELS.length - 1 ? "border-r border-gray-100" : ""}`}
            >
              {isDone ? (
                <CheckCircle2 className="h-3 w-3 shrink-0" />
              ) : isActive ? (
                <Loader2 className="h-3 w-3 shrink-0 animate-spin" />
              ) : (
                <Circle className="h-3 w-3 shrink-0" />
              )}
              {label}
            </button>
          );
        })}
      </div>

      {/* Rail + demo — one surface */}
      <div className="flex flex-col sm:flex-row items-stretch min-h-[320px]">
        <aside className="relative shrink-0 sm:w-[200px] md:w-[210px] flex flex-col border-b sm:border-b-0 sm:border-r border-gray-100 bg-slate-50">
          <div className="px-3 py-2 flex items-center justify-between gap-2 border-b border-gray-100">
            <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-emerald-600 font-mono-data">
              5 stages
            </span>
            <span className="text-[9px] text-gray-400 hidden sm:inline">
              feeds →
            </span>
          </div>
          <ScoutPipelineDiagram
            workflowStage={stage}
            embedded
            className="flex-1"
          />
          <div className="hidden sm:block absolute top-12 right-0 w-[3px] h-[calc(100%-3rem)] pointer-events-none bg-gradient-to-b from-transparent via-emerald-400 to-transparent opacity-60" />
        </aside>

        <div className="flex-1 min-w-0 flex flex-col bg-white">
          <div className="hidden sm:flex px-4 py-1.5 items-center gap-2 border-b border-gray-100 bg-emerald-50/50">
            <span className="text-[9px] uppercase tracking-widest text-emerald-600 font-mono-data">
              live opportunity
            </span>
            <span className="text-[9px] text-gray-400">
              ← synced to {STAGE_LABELS[stage].toLowerCase()}
            </span>
          </div>
          <div className="flex-1 p-0">
            <ScoutWorkflowAnimation
              embedded
              onStageChange={setStage}
              className="h-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
