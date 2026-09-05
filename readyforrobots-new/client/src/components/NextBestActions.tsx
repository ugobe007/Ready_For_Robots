// ReadyForRobots — NextBestActions Component
// Design: Clean Workflow / Elevated SaaS
// Right-side sticky decision panel with prioritized next moves
// Colors: High priority = amber, Medium = blue, Low = neutral

import { ArrowRight, Flame, Circle, ChevronRight } from "lucide-react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import type { NextAction } from "../types/readyForRobots";
import { toast } from "sonner";

type NextBestActionsProps = {
  actions: NextAction[];
};

const priorityConfig = {
  high: {
    label: "High",
    dotColor: "bg-amber-500",
    textColor: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-100",
    icon: Flame,
  },
  medium: {
    label: "Medium",
    dotColor: "bg-blue-500",
    textColor: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-100",
    icon: Circle,
  },
  low: {
    label: "Low",
    dotColor: "bg-neutral-400",
    textColor: "text-neutral-500",
    bg: "bg-neutral-50",
    border: "border-neutral-100",
    icon: Circle,
  },
};

export default function NextBestActions({ actions }: NextBestActionsProps) {
  const [, navigate] = useLocation();
  const sorted = [...actions].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.priority] - order[b.priority];
  });

  return (
    <div className="flex flex-col gap-4">
      {/* Panel header */}
      <div>
        <h2 className="text-base font-semibold text-neutral-950">
          Next Best Actions
        </h2>
        <p className="text-xs text-neutral-400 mt-0.5">
          Ranked by urgency and opportunity
        </p>
      </div>

      {/* Action list */}
      <div className="flex flex-col gap-2">
        {sorted.map((action, i) => {
          const config = priorityConfig[action.priority];
          const Icon = config.icon;

          return (
            <button
              key={action.id}
              onClick={() => {
                if (action.route) {
                  const path =
                    action.entity_type === "crm_account" && action.entity_id
                      ? `${action.route}?account=${action.entity_id}`
                      : action.route;
                  navigate(path);
                } else {
                  toast(`Action: ${action.label} for ${action.companyName}`);
                }
              }}
              className={`group w-full text-left p-3.5 rounded-xl border ${config.border} ${config.bg} hover:shadow-sm transition-all duration-150 hover:-translate-y-0.5`}
            >
              <div className="flex items-start gap-3">
                {/* Priority indicator */}
                <div className="flex flex-col items-center gap-1 pt-0.5">
                  <span className="font-mono text-xs text-neutral-400 leading-none">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div
                    className={`h-1.5 w-1.5 rounded-full ${config.dotColor}`}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-950 leading-snug">
                    {action.label}
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5 truncate">
                    {action.companyName}
                  </p>
                </div>

                {/* Arrow */}
                <ChevronRight className="h-4 w-4 text-neutral-300 group-hover:text-neutral-500 transition-colors shrink-0 mt-0.5" />
              </div>
            </button>
          );
        })}
      </div>

      {/* View all */}
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-between text-xs text-neutral-500 hover:text-neutral-950 border border-neutral-200 hover:border-neutral-300 rounded-lg h-8"
        onClick={() => navigate("/sales-console")}
      >
        View all actions
        <ArrowRight className="h-3.5 w-3.5" />
      </Button>

      {/* System status card */}
      <div className="mt-2 p-4 rounded-xl bg-neutral-950 text-white">
        <div className="flex items-center gap-2 mb-3">
          <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">
            System Active
          </span>
        </div>
        <p className="text-xs text-neutral-300 leading-relaxed">
          ReadyForRobots is monitoring{" "}
          <span className="text-white font-medium">150+ sources</span> for new
          buying signals across your target verticals.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="bg-neutral-800 rounded-lg p-2 text-center">
            <p className="font-mono text-base font-bold text-white">
              {actions.length}
            </p>
            <p className="text-xs text-neutral-400">Open actions</p>
          </div>
          <div className="bg-neutral-800 rounded-lg p-2 text-center">
            <p className="font-mono text-base font-bold text-emerald-400">
              {actions.filter(a => a.priority === "high").length}
            </p>
            <p className="text-xs text-neutral-400">High priority</p>
          </div>
        </div>
      </div>
    </div>
  );
}
