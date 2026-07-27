/**
 * Pipeline action line + robot type chips — demo proof vs generic company search.
 */
import { cleanAndClampText } from "@/lib/text";

export type PipelineLeadActionFields = {
  pipeline_action?: string | null;
  pipelineAction?: string | null;
  robot_types_needed?: string[];
  robotTypesNeeded?: string[];
  share_summary?: string | null;
  core_need?: string | null;
  signal?: string;
  signals?: { display_text?: string }[];
  crmEvidence?: {
    friction_point?: string | null;
    workflow_scope?: { count?: number; label?: string | null; items?: string[] };
    timing?: { label?: string | null };
    robot_type?: { label?: string | null };
    budget?: { top_amount?: string | null; has_budget?: boolean };
  };
};

function actionLine(lead: PipelineLeadActionFields): string {
  const action = (lead.pipeline_action || lead.pipelineAction || "").trim();
  if (action) return cleanAndClampText(action, 200);
  const summary = (lead.share_summary || lead.core_need || lead.signal || "").trim();
  if (summary) return cleanAndClampText(summary, 200);
  return cleanAndClampText(lead.signals?.[0]?.display_text, 200) || "";
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
  if (e.timing?.label) parts.push(`Timing: ${e.timing.label}`);
  if (e.robot_type?.label) parts.push(`Robots: ${e.robot_type.label}`);
  if (e.budget?.top_amount) parts.push(`Budget: ${e.budget.top_amount}`);
  else if (e.budget?.has_budget) parts.push("Budget signal detected");
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
  const action = actionLine(lead);
  const types = robotTypes(lead);
  const proof = evidenceLine(lead);
  if (!action && types.length === 0 && !proof) return null;

  const actionClass =
    variant === "dark"
      ? "text-slate-300 text-sm"
      : variant === "hero"
        ? "text-[12px] text-slate-700 leading-snug"
      : variant === "compact"
        ? "text-[11px] text-stone-700 leading-snug"
        : "text-xs text-gray-700 leading-snug";

  const chipClass =
    variant === "dark"
      ? "inline-flex rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
      : variant === "hero"
        ? "inline-flex rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-sky-700"
      : "pipeline-robot-type-chip";

  const proofClass =
    variant === "dark"
      ? "text-[11px] text-emerald-200/90 leading-snug"
      : variant === "hero"
        ? "text-[11px] text-sky-700 leading-snug"
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
                      ? "font-bold text-amber-700"
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
