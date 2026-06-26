import { useCallback, useEffect, useState } from "react";
import { useLocation } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import ActivityFeed from "@/components/ActivityFeed";
import NextBestActions from "@/components/NextBestActions";
import WhileYouWereAway from "@/components/WhileYouWereAway";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import type { ActivityItem, DailySummary, NextAction } from "@/types/readyForRobots";

const EMPTY_SUMMARY: DailySummary = {
  signalsDetected: 0,
  companiesQualified: 0,
  outreachDraftsCreated: 0,
  followupsSent: 0,
  opportunitiesAdvanced: 0,
};

export default function SalesWorkflow() {
  const { session, loading: authLoading } = useAuth();
  const [, navigate] = useLocation();
  const [actions, setActions] = useState<NextAction[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [summary, setSummary] = useState<DailySummary>(EMPTY_SUMMARY);
  const [awayOpen, setAwayOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadWorkflow = useCallback(async () => {
    const token = session?.access_token;
    if (!token) return;
    setLoading(true);
    try {
      const headers = authHeader(token);
      const base = getApiBase();
      const init = liveFetchInit({ headers });
      const [actionsRes, feedRes, summaryRes] = await Promise.all([
        fetch(`${base}/api/sales/next-actions`, init),
        fetch(`${base}/api/sales/activity-feed`, init),
        fetch(`${base}/api/sales/workflow-summary`, init),
      ]);
      if (actionsRes.ok) {
        const payload = (await actionsRes.json()) as { actions?: NextAction[] };
        setActions(payload.actions ?? []);
      }
      if (feedRes.ok) {
        const payload = (await feedRes.json()) as { activities?: ActivityItem[] };
        setActivities(payload.activities ?? []);
      }
      if (summaryRes.ok) {
        const payload = (await summaryRes.json()) as DailySummary & { repliesReceived?: number };
        setSummary({
          signalsDetected: payload.signalsDetected ?? 0,
          companiesQualified: payload.companiesQualified ?? 0,
          outreachDraftsCreated: payload.outreachDraftsCreated ?? 0,
          followupsSent: payload.followupsSent ?? 0,
          opportunitiesAdvanced: payload.opportunitiesAdvanced ?? 0,
        });
        const total =
          (payload.signalsDetected ?? 0) +
          (payload.outreachDraftsCreated ?? 0) +
          (payload.followupsSent ?? 0) +
          (payload.repliesReceived ?? 0);
        if (total > 0) setAwayOpen(true);
      }
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    void loadWorkflow();
  }, [loadWorkflow]);

  const handleSelectActivity = (activity: ActivityItem) => {
    if (activity.route) navigate(activity.route);
  };

  if (authLoading) {
    return <div className="min-h-screen bg-neutral-50" />;
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <Header />
        <main className="max-w-3xl mx-auto px-4 py-16 text-center text-neutral-600">
          Sign in to view your sales workflow dashboard.
        </main>
      </div>
    );
  }

  return (
    <div className="admin-workspace min-h-screen bg-neutral-50">
      <Header />
      <AdminNav />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-neutral-950">Sales Workflow</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Ranked actions, live activity, and automation status across CRM, inbox, and SCOUT.
          </p>
        </div>
        {loading ? (
          <p className="text-sm text-neutral-500">Loading workflow data…</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
            <ActivityFeed activities={activities} onSelectActivity={handleSelectActivity} />
            <NextBestActions actions={actions} />
          </div>
        )}
      </main>
      <WhileYouWereAway
        summary={summary}
        isOpen={awayOpen}
        onClose={() => setAwayOpen(false)}
      />
    </div>
  );
}
