import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Filter, SortDesc, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";
import ActionCard from "./ActionCard";
import type { ActivityItem } from "../types/readyForRobots";
import { toast } from "sonner";

type FeedAction = "approve" | "edit" | "skip" | "prioritize";

type ActivityFeedProps = {
  activities: ActivityItem[];
  onSelectActivity: (activity: ActivityItem) => void;
  onFeedAction?: (
    activity: ActivityItem,
    action: FeedAction
  ) => Promise<{ route?: string; entity_id?: string } | void>;
};

export default function ActivityFeed({
  activities,
  onSelectActivity,
  onFeedAction,
}: ActivityFeedProps) {
  const [items, setItems] = useState<ActivityItem[]>(activities);
  const [filter, setFilter] = useState<string>("all");
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    setItems(activities);
  }, [activities]);

  async function runAction(id: string, action: FeedAction) {
    const item = items.find(a => a.id === id);
    if (!item) return;
    if (!onFeedAction) {
      toast.error("Feed actions are unavailable.");
      return;
    }
    setBusyId(id);
    try {
      const result = await onFeedAction(item, action);
      if (action === "skip" || action === "approve") {
        setItems(prev => prev.filter(a => a.id !== id));
      }
      if (action === "prioritize") {
        setItems(prev => {
          const target = prev.find(a => a.id === id);
          if (!target) return prev;
          return [target, ...prev.filter(a => a.id !== id)];
        });
      }
      if (action === "approve") {
        toast.success(`Draft approved for ${item.companyName}.`);
      } else if (action === "skip") {
        toast.success(`${item.companyName} dismissed from feed.`);
      } else if (action === "prioritize") {
        toast.success(`${item.companyName} prioritized.`);
      } else if (action === "edit") {
        toast(`Opening ${item.companyName} in CRM.`);
      }
      if (result?.route) {
        const url = result.entity_id
          ? `${result.route}?account=${encodeURIComponent(result.entity_id)}`
          : result.route;
        window.location.href = url;
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  const handleApprove = (id: string) => void runAction(id, "approve");
  const handleEdit = (id: string) => void runAction(id, "edit");
  const handleSkip = (id: string) => void runAction(id, "skip");
  const handlePrioritize = (id: string) => void runAction(id, "prioritize");

  const filterOptions = [
    { value: "all", label: "All" },
    { value: "new_signal", label: "New Signals" },
    { value: "draft_ready", label: "Draft Ready" },
    { value: "followup_sent", label: "Follow-ups" },
    { value: "qualified", label: "Qualified" },
  ];

  const filtered =
    filter === "all" ? items : items.filter(a => a.status === filter);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-neutral-950">
            Activity Feed
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            {filtered.length} action{filtered.length !== 1 ? "s" : ""} need your
            attention
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs text-neutral-500 gap-1.5"
          >
            <SortDesc className="h-3.5 w-3.5" />
            Sort
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs text-neutral-500 gap-1.5"
          >
            <Filter className="h-3.5 w-3.5" />
            Filter
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {filterOptions.map(opt => (
          <button
            key={opt.value}
            onClick={() => setFilter(opt.value)}
            className={`shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              filter === opt.value
                ? "bg-neutral-950 text-white"
                : "bg-neutral-100 text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <AnimatePresence mode="popLayout">
          {filtered.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-16 text-center"
            >
              <div className="h-12 w-12 rounded-full bg-neutral-100 flex items-center justify-center mb-3">
                <Inbox className="h-6 w-6 text-neutral-400" />
              </div>
              <p className="text-sm font-medium text-neutral-600">
                All caught up
              </p>
              <p className="text-xs text-neutral-400 mt-1">
                No actions pending in this category.
              </p>
            </motion.div>
          ) : (
            filtered.map((activity, i) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => onSelectActivity(activity)}
              >
                <ActionCard
                  activity={activity}
                  disabled={busyId === activity.id}
                  onApprove={handleApprove}
                  onEdit={handleEdit}
                  onSkip={handleSkip}
                  onPrioritize={handlePrioritize}
                />
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
