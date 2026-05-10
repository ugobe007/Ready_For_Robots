// ReadyForRobots — WhileYouWereAway Component
// Design: Clean Workflow / Elevated SaaS
// Modal summarizing autonomous progress since last login
// Triggered by a fixed bottom-right button with pulsing dot

import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Radar,
  CheckCircle2,
  FileText,
  Send,
  TrendingUp,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { DailySummary } from "../types/readyForRobots";

type WhileYouWereAwayProps = {
  summary: DailySummary;
  isOpen: boolean;
  onClose: () => void;
};

const summaryItems = [
  {
    key: "signalsDetected" as keyof DailySummary,
    label: "Signals detected",
    icon: Radar,
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    key: "companiesQualified" as keyof DailySummary,
    label: "Companies qualified",
    icon: CheckCircle2,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    key: "outreachDraftsCreated" as keyof DailySummary,
    label: "Outreach drafts created",
    icon: FileText,
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    key: "followupsSent" as keyof DailySummary,
    label: "Follow-ups sent",
    icon: Send,
    color: "text-purple-600",
    bg: "bg-purple-50",
  },
  {
    key: "opportunitiesAdvanced" as keyof DailySummary,
    label: "Opportunities advanced",
    icon: TrendingUp,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
];

export default function WhileYouWereAway({
  summary,
  isOpen,
  onClose,
}: WhileYouWereAwayProps) {
  return (
    <>
      {/* Trigger button — fixed bottom right */}
      <motion.button
        onClick={onClose}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 bg-neutral-950 text-white px-4 py-2.5 rounded-full shadow-lg hover:bg-neutral-800 transition-colors text-sm font-medium"
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        style={{ display: isOpen ? 'none' : 'flex' }}
      >
        <Sparkles className="h-4 w-4 text-emerald-400" />
        While you were away
        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
      </motion.button>

      {/* Modal overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm"
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 8 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="fixed bottom-20 right-6 z-50 w-80 bg-white rounded-2xl shadow-2xl border border-neutral-200 overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-neutral-100">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-neutral-950 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-neutral-950">
                      While You Were Away
                    </h3>
                    <p className="text-xs text-neutral-400">System activity summary</p>
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

              {/* Summary items */}
              <div className="p-4 flex flex-col gap-2">
                {summaryItems.map((item, i) => {
                  const Icon = item.icon;
                  const value = summary[item.key];
                  return (
                    <motion.div
                      key={item.key}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-colors"
                    >
                      <div
                        className={`h-8 w-8 rounded-lg ${item.bg} flex items-center justify-center shrink-0`}
                      >
                        <Icon className={`h-4 w-4 ${item.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-neutral-500">{item.label}</p>
                      </div>
                      <span className="font-mono text-lg font-bold text-neutral-950">
                        {value}
                      </span>
                    </motion.div>
                  );
                })}
              </div>

              {/* Footer */}
              <div className="px-4 pb-4">
                <Button
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-9 text-sm font-medium"
                  onClick={onClose}
                >
                  Review actions →
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
