// ReadyForRobots — WhileYouWereAway Component
// Modal summarizing autonomous progress since last login with one-click actions

import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Radar,
  CheckCircle2,
  FileText,
  Send,
  TrendingUp,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import type { DailySummary, NextAction } from "../types/readyForRobots";

type WhileYouWereAwayProps = {
  summary: DailySummary;
  highlights?: NextAction[];
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
};

const summaryItems = [
  {
    key: "signalsDetected" as const,
    label: "Signals detected",
    icon: Radar,
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    key: "companiesQualified" as const,
    label: "Companies aligned",
    icon: CheckCircle2,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    key: "outreachDraftsCreated" as const,
    label: "Outreach drafts created",
    icon: FileText,
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    key: "followupsSent" as const,
    label: "Follow-ups activated",
    icon: Send,
    color: "text-purple-600",
    bg: "bg-purple-50",
  },
  {
    key: "opportunitiesAdvanced" as const,
    label: "Opportunities advanced",
    icon: TrendingUp,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
];

function actionPath(action: NextAction): string {
  if (!action.route) return "/sales-workflow";
  if (action.entity_type === "crm_account" && action.entity_id) {
    return `${action.route}?account=${action.entity_id}`;
  }
  if (action.entity_type === "sales_opportunity" && action.entity_id) {
    return `${action.route}?opportunity=${action.entity_id}`;
  }
  return action.route;
}

export default function WhileYouWereAway({
  summary,
  highlights = [],
  isOpen,
  onClose,
  onOpen,
}: WhileYouWereAwayProps) {
  const [, navigate] = useLocation();
  const actionable = highlights.length > 0 ? highlights : (summary.highlights ?? []);
  const topAction = actionable[0];

  const goToAction = (action: NextAction) => {
    onClose();
    navigate(actionPath(action));
  };

  return (
    <>
      <motion.button
        onClick={onOpen}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 bg-neutral-950 text-white px-4 py-2.5 rounded-full shadow-lg hover:bg-neutral-800 transition-colors text-sm font-medium"
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        style={{ display: isOpen ? "none" : "flex" }}
      >
        <Sparkles className="h-4 w-4 text-emerald-400" />
        While you were away
        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 8 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="fixed bottom-20 right-6 z-50 w-[min(360px,calc(100vw-2rem))] bg-white rounded-2xl shadow-2xl border border-neutral-200 overflow-hidden"
            >
              <div className="flex items-center justify-between p-5 border-b border-neutral-100">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-neutral-950 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-neutral-950">
                      While You Were Away
                    </h3>
                    <p className="text-xs text-neutral-400">Last 24 hours · tap to act</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-7 w-7 p-0 text-neutral-400 hover:text-neutral-700"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {actionable.length > 0 && (
                <div className="p-4 border-b border-neutral-100 flex flex-col gap-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700">
                    Do this now
                  </p>
                  {actionable.slice(0, 4).map((action, i) => (
                    <motion.button
                      key={action.id}
                      type="button"
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => goToAction(action)}
                      className="group flex w-full items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50/70 p-3 text-left hover:bg-emerald-50 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-neutral-950 leading-snug">
                          {action.label}
                        </p>
                        <p className="text-xs text-neutral-500 mt-0.5 truncate">
                          {action.companyName}
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5 group-hover:translate-x-0.5 transition-transform" />
                    </motion.button>
                  ))}
                </div>
              )}

              <div className="p-4 flex flex-col gap-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-neutral-500">
                  Activity summary
                </p>
                {summaryItems.map((item, i) => {
                  const Icon = item.icon;
                  const value = summary[item.key];
                  if (!value) return null;
                  return (
                    <motion.div
                      key={item.key}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className="flex items-center gap-3 p-2.5 rounded-xl bg-neutral-50"
                    >
                      <div
                        className={`h-7 w-7 rounded-lg ${item.bg} flex items-center justify-center shrink-0`}
                      >
                        <Icon className={`h-3.5 w-3.5 ${item.color}`} />
                      </div>
                      <p className="text-xs text-neutral-500 flex-1">{item.label}</p>
                      <span className="font-mono text-sm font-bold text-neutral-950">{value}</span>
                    </motion.div>
                  );
                })}
              </div>

              <div className="px-4 pb-4">
                <Button
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-9 text-sm font-medium"
                  onClick={() => {
                    if (topAction) goToAction(topAction);
                    else {
                      onClose();
                      navigate("/sales-workflow");
                    }
                  }}
                >
                  {topAction ? "Take top action →" : "Open workflow →"}
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
