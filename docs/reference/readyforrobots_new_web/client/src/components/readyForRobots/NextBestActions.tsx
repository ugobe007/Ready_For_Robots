import type { NextAction, PriorityLevel } from "@/types/readyForRobots";

export type NextBestActionsProps = {
  actions: NextAction[];
};

function priorityClass(p: PriorityLevel): string {
  if (p === "high") return "border-l-4 border-l-blue-800";
  if (p === "medium") return "border-l-4 border-l-blue-500";
  return "border-l-4 border-l-blue-200";
}

export default function NextBestActions({ actions }: NextBestActionsProps) {
  return (
    <aside
      className="min-w-0 w-full max-w-full overflow-hidden break-words rounded-lg border border-blue-200 bg-white/95 p-5 shadow-sm"
      aria-labelledby="next-actions-heading"
    >
      <h2 id="next-actions-heading" className="break-words text-sm font-semibold text-blue-950">
        Next best actions
      </h2>
      <p className="mt-1 text-xs leading-relaxed text-slate-600 break-words">
        Suggested order to work accounts—same live data as the feed, condensed for quick triage.
      </p>
      <ol className="mt-4 flex min-w-0 flex-col gap-3">
        {actions.length === 0 ? (
          <li className="text-sm text-slate-600 break-words">No actions yet — load leads first.</li>
        ) : (
          actions.map((action, index) => (
            <li
              key={action.id}
              className={`min-w-0 max-w-full overflow-hidden break-words rounded-sm border border-blue-100 bg-sky-50/80 p-3 pl-3 ${priorityClass(action.priority)}`}
            >
              <span className="text-xs font-medium text-blue-800/80">{index + 1}.</span>
              <p className="mt-1 text-sm font-medium text-blue-950 break-words">{action.label}</p>
              <p className="text-xs text-slate-600 break-words [overflow-wrap:anywhere]">
                {action.companyName}
              </p>
            </li>
          ))
        )}
      </ol>
    </aside>
  );
}
