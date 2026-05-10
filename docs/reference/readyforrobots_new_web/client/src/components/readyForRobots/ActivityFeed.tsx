import type { ActivityItem } from "@/types/readyForRobots";
import ActionCard from "./ActionCard";

export type ActivityFeedProps = {
  activities: ActivityItem[];
  loading?: boolean;
  selectedId: string | null;
  onSelectActivity: (activity: ActivityItem) => void;
  onApprove: (id: string) => void;
  onEdit: (id: string) => void;
  onSkip: (id: string) => void;
  onPrioritize: (id: string) => void;
};

export default function ActivityFeed({
  activities,
  loading = false,
  selectedId,
  onSelectActivity,
  onApprove,
  onEdit,
  onSkip,
  onPrioritize,
}: ActivityFeedProps) {
  return (
    <section className="min-w-0 w-full max-w-full overflow-hidden" aria-labelledby="activity-feed-heading">
      <h2 id="activity-feed-heading" className="sr-only">
        Activity feed
      </h2>
      {activities.length === 0 && !loading ? (
        <p className="break-words rounded-lg border border-dashed border-blue-300 bg-sky-50/90 px-4 py-8 text-center text-sm text-slate-700">
          No leads returned yet. Confirm the API is running and{" "}
          <code className="text-xs">DATABASE_URL</code> points at your Supabase Postgres.
        </p>
      ) : null}

      <ul className="flex min-w-0 flex-col gap-4">
        {activities.map((activity) => (
          <li key={activity.id} className="min-w-0 max-w-full">
            <ActionCard
              activity={activity}
              selected={selectedId === activity.id}
              onSelect={() => onSelectActivity(activity)}
              onApprove={onApprove}
              onEdit={onEdit}
              onSkip={onSkip}
              onPrioritize={onPrioritize}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
