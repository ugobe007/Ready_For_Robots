/**
 * Cal lead drop — "I found a buyer for you" handoff card.
 */
import { ArrowRight, Bot, Clock, Flame, Mail, Sparkles } from "lucide-react";
import { Link } from "wouter";
import { cleanAndClampText } from "@/lib/text";

export type CalLeadDropData = {
  id: number;
  company_name: string;
  tier: string;
  intent_score: number;
  industry: string;
  location?: string;
  vertical_label?: string;
  why_now: string;
  robot_fit?: string[];
  timing?: string;
  pipeline_action?: string;
  signal_type?: string;
  signal_text?: string;
  draft_subject?: string;
  draft_body?: string;
  cal_observation?: string;
  cal_prompt: string;
  recommended_action?: string;
};

type Props = {
  drop: CalLeadDropData;
  variant?: "full" | "compact";
  showDraft?: boolean;
  onMoveNow?: () => void;
  pipelineHref?: string;
  signupHref?: string;
};

const TIER_STYLES: Record<
  string,
  { bg: string; text: string; border: string }
> = {
  HOT: {
    bg: "rgba(239,68,68,0.08)",
    text: "#b91c1c",
    border: "rgba(239,68,68,0.35)",
  },
  WARM: {
    bg: "rgba(245,158,11,0.1)",
    text: "#b45309",
    border: "rgba(245,158,11,0.4)",
  },
  COLD: {
    bg: "rgba(100,116,139,0.08)",
    text: "#475569",
    border: "rgba(100,116,139,0.3)",
  },
};

function tierStyle(tier: string) {
  return TIER_STYLES[(tier || "").toUpperCase()] ?? TIER_STYLES.WARM;
}

export default function CalLeadDrop({
  drop,
  variant = "full",
  showDraft = true,
  onMoveNow,
  pipelineHref = `/pipeline?lead=${drop.id}`,
  signupHref = `/signup?next=${encodeURIComponent(`/pipeline?lead=${drop.id}`)}&co=${encodeURIComponent(drop.company_name)}`,
}: Props) {
  const ts = tierStyle(drop.tier);
  const isHot = (drop.tier || "").toUpperCase() === "HOT";
  const compact = variant === "compact";

  return (
    <article
      className={
        compact
          ? "rounded-2xl border bg-white p-4 shadow-sm"
          : "rounded-2xl border bg-white p-5 sm:p-6 shadow-sm"
      }
      style={{ borderColor: ts.border }}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-2.5 min-w-0">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
            style={{ background: ts.bg }}
          >
            {isHot ? (
              <Flame className="h-4 w-4" style={{ color: ts.text }} />
            ) : (
              <Sparkles className="h-4 w-4" style={{ color: ts.text }} />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">
              SIGNAL recommendation
            </p>
            <h3 className="text-lg font-bold text-gray-900 truncate">
              {drop.company_name}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {drop.vertical_label || drop.industry}
              {drop.location ? ` · ${drop.location}` : ""}
            </p>
          </div>
        </div>
        <div
          className="shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide"
          style={{
            background: ts.bg,
            color: ts.text,
            border: `1px solid ${ts.border}`,
          }}
        >
          {drop.tier} · {Math.round(drop.intent_score)} intent
        </div>
      </div>

      <div className="space-y-3">
        {(drop.cal_observation || drop.cal_prompt) && (
          <div
            className="rounded-xl px-3 py-2.5 text-sm leading-relaxed"
            style={{ background: "rgba(5,150,105,0.06)", color: "#065f46" }}
          >
            <span className="font-semibold">SIGNAL: </span>
            {drop.cal_observation || drop.cal_prompt}
          </div>
        )}

        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1">
            Why now
          </p>
          <p className="text-sm leading-relaxed text-gray-800">
            {cleanAndClampText(drop.why_now, compact ? 220 : 360)}
          </p>
        </section>

        {(drop.robot_fit?.length ?? 0) > 0 && (
          <section>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5 flex items-center gap-1">
              <Bot className="h-3 w-3" />
              Fit for your robots
            </p>
            <div className="flex flex-wrap gap-1.5">
              {drop.robot_fit!.slice(0, compact ? 3 : 4).map(r => (
                <span
                  key={r}
                  className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-700"
                >
                  {r}
                </span>
              ))}
            </div>
          </section>
        )}

        {drop.timing && (
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <Clock className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
            <span>{drop.timing}</span>
          </div>
        )}

        {showDraft && (drop.draft_subject || drop.draft_body) && (
          <section className="rounded-xl border border-amber-200/80 bg-gradient-to-br from-amber-50/90 to-white p-3">
            <p className="text-[10px] font-bold uppercase tracking-widest text-amber-900 mb-2 flex items-center gap-1">
              <Mail className="h-3 w-3" />
              Open with this
            </p>
            {drop.draft_subject && (
              <p className="text-xs font-semibold text-amber-950 mb-2">
                {drop.draft_subject}
              </p>
            )}
            {drop.draft_body && (
              <pre className="whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed text-gray-600 max-h-32 overflow-y-auto">
                {cleanAndClampText(drop.draft_body, compact ? 280 : 480)}
              </pre>
            )}
          </section>
        )}

        {drop.cal_prompt && drop.cal_observation && (
          <p className="text-xs text-gray-600 italic">{drop.cal_prompt}</p>
        )}
      </div>

      {!compact && (
        <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center">
          {onMoveNow ? (
            <button
              type="button"
              onClick={onMoveNow}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700"
            >
              Move on this now
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          ) : (
            <Link
              href={signupHref}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700"
            >
              Move on this now — free
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          )}
          <Link
            href={pipelineHref}
            className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50"
          >
            View in pipeline
          </Link>
        </div>
      )}
    </article>
  );
}

export function dealToCalDrop(deal: {
  id: number;
  company: string;
  industry: string;
  location: string;
  score: number;
  priorityTier?: string;
  shareSummary?: string;
  notes?: string;
  robotTypesNeeded?: string[];
  outreachSubject?: string;
  outreachBody?: string;
  projectTiming?: { display_phrase?: string; label?: string };
  signalType?: string;
  signal?: string;
  pipelineAction?: string;
}): CalLeadDropData {
  const tier = (deal.priorityTier || "WARM").toUpperCase();
  const isHot = tier === "HOT";
  return {
    id: deal.id,
    company_name: deal.company,
    tier,
    intent_score: deal.score,
    industry: deal.industry,
    location: deal.location !== "—" ? deal.location : "",
    why_now: deal.shareSummary || deal.notes || deal.signal || "",
    robot_fit: deal.robotTypesNeeded,
    timing: deal.projectTiming?.display_phrase || deal.projectTiming?.label,
    pipeline_action: deal.pipelineAction,
    signal_type: deal.signalType,
    signal_text: deal.signal,
    draft_subject: deal.outreachSubject,
    draft_body: deal.outreachBody,
    cal_observation: isHot
      ? `My read on ${deal.company}: ${deal.shareSummary || deal.signal || "signals are aligning"}. I'd prioritize outreach this week.`
      : `My read on ${deal.company}: credible intent — worth validating on a discovery call.`,
    cal_prompt: isHot
      ? `I can save ${deal.company} and hand you a send-ready draft. Move on it now?`
      : `Want the full brief and talk track for ${deal.company}?`,
  };
}
