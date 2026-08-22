/**
 * Pipeline action line + robot type chips — demo proof vs generic company search.
 */
import { jobExplanation } from "@/lib/jobsWorkflow";
import { cleanAndClampText } from "@/lib/text";

export type PipelineLeadActionFields = {
  pipeline_action?: string | null;
  pipelineAction?: string | null;
  robot_types_needed?: string[];
  robotTypesNeeded?: string[];
  share_summary?: string | null;
  shareSummary?: string | null;
  core_need?: string | null;
  signal?: string;
  company?: string | null;
  industry?: string | null;
  signals?: { display_text?: string }[];
  leadHighlights?: { specific_problem?: string | null };
  crmEvidence?: {
    friction_point?: string | null;
    workflow_scope?: { count?: number; label?: string | null; items?: string[] };
    timing?: { label?: string | null };
    robot_type?: { label?: string | null };
    budget?: { top_amount?: string | null; has_budget?: boolean };
  };
};

function actionLine(lead: PipelineLeadActionFields): string {
  return cleanAndClampText(
    jobExplanation({
      friction: lead.crmEvidence?.friction_point || lead.leadHighlights?.specific_problem,
      workflow:
        lead.crmEvidence?.workflow_scope?.label ||
        lead.crmEvidence?.workflow_scope?.items?.[0],
      summary: lead.share_summary || lead.shareSummary || lead.core_need || lead.signal,
      action: lead.pipeline_action || lead.pipelineAction,
      company: lead.company,
      industry: lead.industry,
      title: lead.signals?.[0]?.display_text,
    }),
    200,
  );
}

function robotTypes(lead: PipelineLeadActionFields): string[] {
  const fromApi = (lead.robot_types_needed || lead.robotTypesNeeded || []).filter(Boolean);
  return fromApi.slice(0, 4);
}

function evidenceLine(lead: PipelineLeadActionFields): string {
  const e = lead.crmEvidence;
  if (!e) return "";
  const parts: string[] = [];
  if (e.workflow_scope?.label) parts.push(e.workflow_scope.label);
  if (e.robot_type?.label) parts.push(e.robot_type.label);
  if (parts.length > 0) return cleanAndClampText(parts.join(" · "), 180);
  if (e.friction_point) return cleanAndClampText(e.friction_point, 180);
  return "";
}

type Props = {
  lead: PipelineLeadActionFields;
  variant?: "light" | "dark" | "compact" | "hero";
  className?: string;
};

export default function PipelineLeadActionMeta({ lead, variant = "light", className = "" }: Props) {
  const rawAction = actionLine(lead);
  // Hero: one tight line only
  const action =
    variant === "hero" && rawAction.length > 68
      ? rawAction.slice(0, 65).trimEnd() + "…"
      : rawAction;
  // Hero: no chips, no evidence — keep cards compact
  const types = variant === "hero" ? [] : robotTypes(lead);
  const proof = variant === "hero" ? "" : evidenceLine(lead);
  if (!action && types.length === 0 && !proof) return null;

  const actionClass =
    variant === "dark"
      ? "text-slate-300 text-sm"
      : variant === "hero"
        ? "text-[12px] text-slate-300 leading-snug"
      : variant === "compact"
        ? "pipeline-deal-action leading-snug"
        : "text-xs text-gray-700 leading-snug";

  const chipClass =
    variant === "dark"
      ? "inline-flex rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
      : variant === "hero"
        ? "inline-flex rounded-full border border-sky-300/28 bg-sky-400/8 px-2 py-0.5 text-[10px] font-medium text-sky-200/85"
      : "pipeline-robot-type-chip";

  const proofClass =
    variant === "dark"
      ? "text-[11px] text-emerald-200/90 leading-snug"
      : variant === "hero"
        ? "text-[11px] text-slate-400 leading-snug"
      : variant === "compact"
        ? "text-[10px] text-emerald-700 leading-snug"
        : "text-[11px] text-emerald-700 leading-snug";

  const prefix = action.includes(":") ? action.split(":")[0]?.trim() : null;
  const body =
    prefix && action.includes(":")
      ? action.slice(action.indexOf(":") + 1).trim()
      : action;

  return (
    <div className={`space-y-1.5 ${className}`}>
      {proof && <p className={proofClass}>{proof}</p>}
      {action && (
        <p className={actionClass}>
          {prefix && body ? (
            <>
              <span
                className={
                  variant === "dark"
                    ? "font-bold text-emerald-400"
                    : variant === "hero"
                      ? "font-bold text-cyan-300"
                      : "font-bold text-emerald-800"
                }
              >
                {prefix}:
              </span>{" "}
              {body}
            </>
          ) : (
            action
          )}
        </p>
      )}
      {types.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {types.map((type) => (
            <span key={type} className={chipClass}>
              {type}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export { actionLine as pipelineActionLine, robotTypes as pipelineRobotTypes };
