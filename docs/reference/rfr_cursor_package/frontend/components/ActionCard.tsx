// ReadyForRobots — ActionCard Component
// Design: Clean Workflow / Elevated SaaS
// Individual card in the activity feed
// Shows: Company, Signal, Recommended action, Status, Approve/Edit/Skip/Prioritize buttons

import { motion } from "framer-motion";
import {
  CheckCircle,
  Edit3,
  SkipForward,
  Star,
  Building2,
  TrendingUp,
  AlertTriangle,
  Users,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ActivityItem, ActivityStatus } from "../types/readyForRobots";

type ActionCardProps = {
  activity: ActivityItem;
  onApprove: (id: string) => void;
  onEdit: (id: string) => void;
  onSkip: (id: string) => void;
  onPrioritize: (id: string) => void;
};

const statusConfig: Record<
  ActivityStatus,
  { label: string; color: string; bg: string; border: string }
> = {
  new_signal: {
    label: "New Signal",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  draft_ready: {
    label: "Draft Ready",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  followup_sent: {
    label: "Follow-up Sent",
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  qualified: {
    label: "Qualified",
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  meeting_suggested: {
    label: "Meeting Suggested",
    color: "text-purple-700",
    bg: "bg-purple-50",
    border: "border-purple-200",
  },
};

const signalIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  "Hiring Signal": Users,
  "Expansion Signal": TrendingUp,
  "Operational Signal": Building2,
  "Safety Signal": AlertTriangle,
};

function ConfidenceArc({ score }: { score: number }) {
  const radius = 18;
  const circumference = Math.PI * radius; // half circle
  const progress = (score / 100) * circumference;
  const color =
    score >= 90 ? "#059669" : score >= 75 ? "#2563EB" : "#F59E0B";

  return (
    <div className="flex flex-col items-center gap-0.5">
      <svg width="44" height="26" viewBox="0 0 44 26">
        {/* Track */}
        <path
          d="M 4 24 A 18 18 0 0 1 40 24"
          fill="none"
          stroke="#E5E5E5"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Progress */}
        <path
          d="M 4 24 A 18 18 0 0 1 40 24"
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
        />
      </svg>
      <span className="font-mono text-xs font-semibold text-neutral-700 -mt-1">
        {score}
      </span>
    </div>
  );
}

export default function ActionCard({
  activity,
  onApprove,
  onEdit,
  onSkip,
  onPrioritize,
}: ActionCardProps) {
  const status = statusConfig[activity.status];
  const SignalIcon = signalIcons[activity.signalType] || Building2;

  const leftBorderColor =
    activity.status === "new_signal"
      ? "border-l-amber-400"
      : activity.status === "draft_ready"
      ? "border-l-blue-400"
      : activity.status === "followup_sent" || activity.status === "qualified"
      ? "border-l-emerald-400"
      : "border-l-purple-400";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className={`group relative bg-white rounded-xl border border-neutral-200 border-l-4 ${leftBorderColor} shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden`}
    >
      <div className="p-5">
        {/* Top row: company + status + confidence */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-8 w-8 rounded-lg bg-neutral-100 flex items-center justify-center shrink-0">
              <Building2 className="h-4 w-4 text-neutral-500" />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-neutral-950 text-sm leading-tight truncate">
                {activity.companyName}
              </h3>
              <p className="text-xs text-neutral-400 mt-0.5">{activity.industry}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Badge
              variant="outline"
              className={`text-xs px-2 py-0.5 ${status.color} ${status.bg} ${status.border}`}
            >
              {status.label}
            </Badge>
            <ConfidenceArc score={activity.confidenceScore} />
          </div>
        </div>

        {/* Signal row */}
        <div className="flex items-start gap-2 mb-3 p-3 bg-neutral-50 rounded-lg">
          <SignalIcon className="h-3.5 w-3.5 text-neutral-400 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">
              {activity.signalType}
            </span>
            <p className="text-sm text-neutral-700 mt-0.5 leading-snug">
              {activity.signalSummary}
            </p>
          </div>
        </div>

        {/* Robot use case */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-neutral-400">Use case:</span>
          <span className="text-xs font-medium text-neutral-600 bg-neutral-100 px-2 py-0.5 rounded-full">
            {activity.robotUseCase}
          </span>
        </div>

        {/* Recommended action */}
        <div className="flex items-start gap-2 mb-4">
          <ChevronRight className="h-3.5 w-3.5 text-emerald-500 mt-0.5 shrink-0" />
          <p className="text-sm text-neutral-700 leading-snug">
            <span className="font-medium text-neutral-950">Recommended: </span>
            {activity.recommendedAction}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 pt-3 border-t border-neutral-100">
          <Button
            size="sm"
            onClick={() => onApprove(activity.id)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white h-7 px-3 text-xs font-medium gap-1.5"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Approve
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEdit(activity.id)}
            className="h-7 px-3 text-xs font-medium gap-1.5 text-neutral-600 border-neutral-200 hover:border-neutral-300"
          >
            <Edit3 className="h-3.5 w-3.5" />
            Edit
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onPrioritize(activity.id)}
            className="h-7 px-3 text-xs font-medium gap-1.5 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
          >
            <Star className="h-3.5 w-3.5" />
            Prioritize
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onSkip(activity.id)}
            className="h-7 px-3 text-xs font-medium gap-1.5 text-neutral-400 hover:text-neutral-600 ml-auto"
          >
            <SkipForward className="h-3.5 w-3.5" />
            Skip
          </Button>
        </div>
      </div>

      {/* Timestamp */}
      <div className="absolute top-4 right-[140px]">
        <span className="font-mono text-xs text-neutral-400">{activity.createdAt}</span>
      </div>
    </motion.div>
  );
}
