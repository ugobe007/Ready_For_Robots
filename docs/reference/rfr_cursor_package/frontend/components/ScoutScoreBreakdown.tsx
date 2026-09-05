/**
 * ScoutScoreBreakdown — displays the 6-factor SCOUT Score on a lead card.
 * Shows composite score, band badge, and expandable factor breakdown.
 */
import { useState } from "react";
import { ChevronDown, ChevronUp, Zap } from "lucide-react";

export type ScoreData = {
  scoutScore: number;
  scoreReadiness: number;
  scoreUseCase: number;
  scoreRoi: number;
  scoreDeploymentSize: number;
  scoreRecognizableProblem: number;
  scoreCustomerValue: number;
  scoreNotes?: Record<string, string> | null;
};

const FACTORS = [
  { key: "scoreReadiness", label: "Readiness to Buy", max: 25, tier: 1 },
  { key: "scoreUseCase", label: "Use Case Clarity", max: 20, tier: 1 },
  { key: "scoreRoi", label: "Achievable ROI", max: 15, tier: 1 },
  { key: "scoreDeploymentSize", label: "Deployment Scale", max: 15, tier: 2 },
  { key: "scoreRecognizableProblem", label: "Recognizable Problem", max: 15, tier: 2 },
  { key: "scoreCustomerValue", label: "Customer Value", max: 10, tier: 2 },
] as const;

function getBand(score: number): { label: string; color: string; bg: string } {
  if (score >= 80) return { label: "Hot", color: "#ef4444", bg: "rgba(239,68,68,0.12)" };
  if (score >= 60) return { label: "Warm", color: "#FFB000", bg: "rgba(255,176,0,0.12)" };
  if (score >= 40) return { label: "Developing", color: "#a78bfa", bg: "rgba(167,139,250,0.12)" };
  return { label: "Monitoring", color: "rgba(255,255,255,0.4)", bg: "rgba(255,255,255,0.05)" };
}

function FactorBar({
  label,
  value,
  max,
  note,
  tier,
}: {
  label: string;
  value: number;
  max: number;
  note?: string;
  tier: 1 | 2;
}) {
  const pct = Math.round((value / max) * 100);
  const barColor = tier === 1 ? "#03DAC5" : "#a78bfa";

  return (
    <div className="mb-3 last:mb-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-medium" style={{ color: "rgba(255,255,255,0.6)" }}>
          {label}
        </span>
        <span className="text-[11px] font-mono font-bold" style={{ color: barColor }}>
          {value}/{max}
        </span>
      </div>
      <div
        className="h-1.5 rounded-full overflow-hidden"
        style={{ background: "rgba(255,255,255,0.08)" }}
      >
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      {note && (
        <p className="mt-0.5 text-[10px] leading-relaxed" style={{ color: "rgba(255,255,255,0.35)" }}>
          {note}
        </p>
      )}
    </div>
  );
}

export default function ScoutScoreBreakdown({
  data,
  compact = false,
}: {
  data: ScoreData;
  compact?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const band = getBand(data.scoutScore);
  const notes = (data.scoreNotes ?? {}) as Record<string, string>;

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: `1px solid ${band.color}30`, background: "rgba(255,255,255,0.02)" }}
    >
      {/* Score header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.03] transition-colors"
      >
        <div className="flex items-center gap-3">
          <Zap className="h-3.5 w-3.5" style={{ color: band.color }} />
          <span className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.7)" }}>
            SCOUT Score
          </span>
          {/* Band badge */}
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: band.bg, color: band.color }}
          >
            {band.label}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Composite score */}
          <span
            className="text-lg font-black font-mono leading-none"
            style={{ color: band.color }}
          >
            {data.scoutScore}
          </span>
          <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>
            /100
          </span>
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5 ml-1" style={{ color: "rgba(255,255,255,0.3)" }} />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 ml-1" style={{ color: "rgba(255,255,255,0.3)" }} />
          )}
        </div>
      </button>

      {/* Score bar (always visible) */}
      <div className="px-4 pb-3">
        <div
          className="h-2 rounded-full overflow-hidden"
          style={{ background: "rgba(255,255,255,0.06)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${data.scoutScore}%`,
              background: `linear-gradient(90deg, ${band.color}80, ${band.color})`,
            }}
          />
        </div>
        {!compact && (
          <div className="flex justify-between mt-1">
            <span className="text-[9px]" style={{ color: "rgba(255,255,255,0.2)" }}>
              Tier 1: Quality
            </span>
            <span className="text-[9px]" style={{ color: "rgba(255,255,255,0.2)" }}>
              Tier 2: Value
            </span>
          </div>
        )}
      </div>

      {/* Expandable factor breakdown */}
      {expanded && (
        <div
          className="px-4 pb-4 pt-1"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          {/* Tier 1 */}
          <p className="text-[9px] font-bold uppercase tracking-widest mb-2 mt-2" style={{ color: "#03DAC5" }}>
            Tier 1 — Deal Quality
          </p>
          {FACTORS.filter((f) => f.tier === 1).map((f) => (
            <FactorBar
              key={f.key}
              label={f.label}
              value={data[f.key as keyof ScoreData] as number}
              max={f.max}
              note={notes[f.key.replace("score", "").charAt(0).toLowerCase() + f.key.replace("score", "").slice(1)]}
              tier={1}
            />
          ))}

          {/* Tier 2 */}
          <p className="text-[9px] font-bold uppercase tracking-widest mb-2 mt-4" style={{ color: "#a78bfa" }}>
            Tier 2 — Deal Value
          </p>
          {FACTORS.filter((f) => f.tier === 2).map((f) => (
            <FactorBar
              key={f.key}
              label={f.label}
              value={data[f.key as keyof ScoreData] as number}
              max={f.max}
              note={notes[f.key.replace("score", "").charAt(0).toLowerCase() + f.key.replace("score", "").slice(1)]}
              tier={2}
            />
          ))}
        </div>
      )}
    </div>
  );
}
