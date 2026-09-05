import { Button } from "@/components/ui/button";
import type { ActivityItem, ActivityStatus } from "@/types/readyForRobots";

export type ActionCardProps = {
  activity: ActivityItem;
  selected?: boolean;
  onSelect?: () => void;
  onApprove: (id: string) => void;
  onEdit: (id: string) => void;
  onSkip: (id: string) => void;
  onPrioritize: (id: string) => void;
};

function statusLabel(status: ActivityStatus): string {
  const map: Record<ActivityStatus, string> = {
    new_signal: "New signal",
    draft_ready: "Draft ready",
    outreach_sent: "Outreach sent",
    followup_sent: "Follow-up sent",
    qualified: "Qualified",
    meeting_suggested: "Meeting suggested",
    opportunity_created: "Opportunity created",
  };
  return map[status];
}

export default function ActionCard({
  activity,
  selected,
  onSelect,
  onApprove,
  onEdit,
  onSkip,
  onPrioritize,
}: ActionCardProps) {
  return (
    <article
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={onSelect ? () => onSelect() : undefined}
      onKeyDown={
        onSelect
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect();
              }
            }
          : undefined
      }
      className={`min-w-0 w-full max-w-full overflow-hidden break-words border border-blue-200 bg-white/95 p-5 text-left shadow-sm transition-shadow ${
        onSelect ? "cursor-pointer" : ""
      } ${selected ? "ring-2 ring-blue-800 ring-offset-2 ring-offset-sky-100" : "hover:border-blue-400"}`}
      aria-current={selected ? "true" : undefined}
    >
      <header className="mb-4 flex min-w-0 flex-wrap items-start justify-between gap-3 border-b border-blue-100 pb-3">
        <div className="min-w-0 flex-1 overflow-hidden">
          <h3 className="break-words text-base font-semibold text-blue-950">{activity.companyName}</h3>
          <p className="break-words text-xs text-slate-600">
            {activity.industry} · {activity.signalType}
          </p>
        </div>
        <div className="min-w-0 max-w-[min(100%,11rem)] shrink-0 text-right text-xs text-slate-600 sm:max-w-none">
          <span className="inline-block max-w-full break-words rounded-sm border border-blue-200 bg-sky-50 px-2 py-0.5 text-right font-medium text-blue-900">
            {statusLabel(activity.status)}
          </span>
          <span className="mt-1 block break-words">{activity.createdAt}</span>
        </div>
      </header>

      <div className="min-w-0 space-y-3 text-sm text-slate-800">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-blue-800/80">Signal</p>
          <p className="break-words [overflow-wrap:anywhere]">{activity.signalSummary}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-blue-800/80">
            Robot use case
          </p>
          <p className="break-words [overflow-wrap:anywhere]">{activity.robotUseCase}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-blue-800/80">
            Recommended action
          </p>
          <p className="break-words [overflow-wrap:anywhere]">{activity.recommendedAction}</p>
        </div>
        <p className="text-xs text-slate-600">
          Confidence <span className="font-mono text-blue-900">{activity.confidenceScore}%</span>
        </p>
      </div>

      <footer
        className="mt-5 flex min-w-0 flex-wrap gap-2 border-t border-blue-100 pt-4"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <Button
          type="button"
          size="sm"
          variant="default"
          className="rounded-sm bg-blue-800 text-white hover:bg-blue-900"
          onClick={() => onApprove(activity.id)}
        >
          Approve &amp; send
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="rounded-sm border-blue-300 text-blue-900 hover:bg-sky-50"
          onClick={() => onEdit(activity.id)}
        >
          Edit message
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="rounded-sm text-slate-600 hover:bg-sky-100 hover:text-blue-900"
          onClick={() => onSkip(activity.id)}
        >
          Skip
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          className="rounded-sm border border-blue-200 bg-sky-50 text-blue-900 hover:bg-sky-100"
          onClick={() => onPrioritize(activity.id)}
        >
          Prioritize
        </Button>
      </footer>
    </article>
  );
}
