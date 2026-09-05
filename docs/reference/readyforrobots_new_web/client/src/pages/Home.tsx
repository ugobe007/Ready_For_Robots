/**
 * Ready For Robots — primary product surface (autonomous deal flow).
 * Live data: GET /api/leads, /api/pipeline-stats, /api/daily-report
 */

import { useState } from "react";
import { toast } from "sonner";
import AutonomyDial from "@/components/readyForRobots/AutonomyDial";
import ActivityFeed from "@/components/readyForRobots/ActivityFeed";
import Header from "@/components/readyForRobots/Header";
import NextBestActions from "@/components/readyForRobots/NextBestActions";
import WhileYouWereAway from "@/components/readyForRobots/WhileYouWereAway";
import { Button } from "@/components/ui/button";
import { useDealFlowData } from "@/hooks/useDealFlowData";
import type { ActivityItem, AutonomyMode } from "@/types/readyForRobots";

export default function Home() {
  const { loading, error, activities, nextActions, dailySummary, refetch } = useDealFlowData();
  const [mode, setMode] = useState<AutonomyMode>("assisted");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [wywaOpen, setWywaOpen] = useState(false);

  const handleSelect = (activity: ActivityItem) => {
    setSelectedId(activity.id);
  };

  return (
    <main className="min-h-screen min-w-0 overflow-x-hidden bg-sky-100 text-slate-800">
      <Header activePage="/" />
      <AutonomyDial mode={mode} onChange={setMode} />

      {/* Hero: what this page is + what the CTAs do */}
      <div className="border-b border-blue-200/80 bg-gradient-to-b from-sky-50 to-sky-100/90">
        <div className="mx-auto min-w-0 max-w-[1400px] px-4 py-10 sm:px-8">
          <div className="min-w-0 max-w-full overflow-hidden break-words rounded-lg border border-blue-200 bg-white/90 p-6 shadow-sm md:p-8">
            <h1 className="break-words text-2xl font-semibold tracking-tight text-blue-900 md:text-4xl md:leading-tight">
              Automate Your Sales Pipeline
            </h1>
            <p className="mt-3 max-w-full text-sm leading-relaxed text-slate-700 md:text-base">
              This is your <strong className="text-blue-900">command center</strong> for robot and
              automation deals: live buyer signals from your database, suggested next touches, and a
              dial for how much the system runs on its own—so outreach and follow-ups stay consistent
              without living in spreadsheets.
            </p>
            <ul className="mt-4 max-w-full list-outside list-disc space-y-2 pl-5 text-sm text-slate-600 marker:text-blue-800 md:text-[0.9375rem]">
              <li className="break-words pl-0.5">
                <span className="font-medium text-blue-900">Activity feed</span> — ranked accounts
                with signal text, intent score, and a recommended move (approve, edit, skip, or
                prioritize).
              </li>
              <li className="break-words pl-0.5">
                <span className="font-medium text-blue-900">Next best actions</span> — a short queue
                of who to contact or review first, derived from the same live lead list.
              </li>
            </ul>

            <div className="mt-8 flex min-w-0 flex-col gap-4 border-t border-blue-100 pt-6 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
              <div className="flex min-w-0 flex-shrink-0 flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="rounded-sm border-blue-300 bg-white text-blue-900 hover:border-blue-500 hover:bg-sky-50"
                  title="Re-fetch leads, pipeline stats, and the 24-hour summary from the API."
                  onClick={() => void refetch()}
                  disabled={loading}
                >
                  Refresh data
                </Button>
                <Button
                  type="button"
                  className="rounded-sm bg-blue-800 text-white hover:bg-blue-900"
                  title="Opens a modal with signal counts, qualified companies, and new accounts in the last day."
                  onClick={() => setWywaOpen(true)}
                >
                  While you were away
                </Button>
              </div>
              <p className="min-w-0 max-w-full flex-1 text-xs leading-relaxed text-slate-600 break-words sm:max-w-md sm:text-right">
                <strong className="text-blue-900">Refresh data</strong> pulls the latest cards and
                side panel from the server. <strong className="text-blue-900">While you were away</strong>{" "}
                summarizes pipeline movement for roughly the last 24 hours so you can scan progress in
                one glance.
              </p>
            </div>
          </div>
        </div>
      </div>

      {error ? (
        <div
          className="mx-auto min-w-0 max-w-[1400px] break-words px-4 py-4 text-sm text-red-900 border-b border-red-200 bg-red-50 sm:px-8"
          role="alert"
        >
          {error} Start the API:{" "}
          <code className="inline-block max-w-full break-all rounded bg-red-100 px-1 align-baseline text-xs">
            uvicorn app.main:app --reload --port 8000
          </code>{" "}
          from the repo root (with{" "}
          <code className="inline-block max-w-full break-all rounded bg-red-100 px-1 text-xs">
            DATABASE_URL
          </code>{" "}
          set).
        </div>
      ) : null}

      {loading && !activities.length ? (
        <div className="mx-auto min-w-0 max-w-[1400px] break-words px-4 py-12 text-sm text-blue-900/70 sm:px-8">
          Loading live pipeline…
        </div>
      ) : null}

      {!error ? (
        <section className="mx-auto grid min-w-0 max-w-[1400px] grid-cols-1 gap-6 px-4 py-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,360px)]">
          <ActivityFeed
            activities={activities}
            loading={loading}
            selectedId={selectedId}
            onSelectActivity={handleSelect}
            onApprove={(id) => toast.success(`Approve (wire CRM): ${id}`)}
            onEdit={(id) => toast.message(`Edit draft (next): ${id}`)}
            onSkip={(id) => toast(`Skipped: ${id}`)}
            onPrioritize={(id) => toast.success(`Prioritized: ${id}`)}
          />
          <NextBestActions actions={nextActions} />
        </section>
      ) : null}

      <WhileYouWereAway summary={dailySummary} isOpen={wywaOpen} onClose={() => setWywaOpen(false)} />
    </main>
  );
}
