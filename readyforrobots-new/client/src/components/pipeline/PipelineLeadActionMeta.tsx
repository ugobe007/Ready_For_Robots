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

type Props = {
  lead: PipelineLeadActionFields;
  variant?: "light" | "dark" | "compact";
  className?: string;
};

export default function PipelineLeadActionMeta({ lead, variant = "light", className = "" }: Props) {
  const action = actionLine(lead);
  const types = robotTypes(lead);
  if (!action && types.length === 0) return null;

  const actionClass =
    variant === "dark"
      ? "text-slate-300 text-sm"
      : variant === "compact"
        ? "text-[11px] text-stone-700 leading-snug"
        : "text-xs text-gray-700 leading-snug";

  const chipClass =
    variant === "dark"
      ? "inline-flex rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300"
      : "pipeline-robot-type-chip";

  const prefix = action.includes(":") ? action.split(":")[0]?.trim() : null;
  const body =
    prefix && action.includes(":")
      ? action.slice(action.indexOf(":") + 1).trim()
      : action;

  return (
    <div className={`space-y-1.5 ${className}`}>
      {action && (
        <p className={actionClass}>
          {prefix && body ? (
            <>
              <span className={variant === "dark" ? "font-bold text-emerald-400" : "font-bold text-emerald-800"}>
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
