import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import ActivityFeed from "@/components/ActivityFeed";
import NextBestActions from "@/components/NextBestActions";
import WhileYouWereAway from "@/components/WhileYouWereAway";
import WorkflowFunnelPanel from "@/components/WorkflowFunnelPanel";
import { useAuth } from "@/contexts/AuthContext";
import {
  fetchWithTimeout,
  getApiBase,
  liveFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import type { ActivityItem, DailySummary, NextAction } from "@/types/readyForRobots";

const EMPTY_SUMMARY: DailySummary = {
  signalsDetected: 0,
  companiesQualified: 0,
  outreachDraftsCreated: 0,
  followupsSent: 0,
  opportunitiesAdvanced: 0,
};

const WORKFLOW_CACHE_KEY = "sales-workflow-v1";
const WORKFLOW_CACHE_TTL_MS = 120_000;
const WORKFLOW_FETCH_TIMEOUT_MS = 12_000;

type WorkflowPayload = {
  actions: NextAction[];
  activities: ActivityItem[];
  summary: DailySummary;
  highlights: NextAction[];
  funnel?: { saved: number; sent: number; replied: number; meetings: number };
};

const EMPTY_FUNNEL = { saved: 0, sent: 0, replied: 0, meetings: 0 };

function applySummary(payload: DailySummary & { repliesReceived?: number }): DailySummary {
  return {
    signalsDetected: payload.signalsDetected ?? 0,
    companiesQualified: payload.companiesQualified ?? 0,
    outreachDraftsCreated: payload.outreachDraftsCreated ?? 0,
    followupsSent: payload.followupsSent ?? 0,
    opportunitiesAdvanced: payload.opportunitiesAdvanced ?? 0,
  };
}

function summaryActivityTotal(summary: DailySummary & { repliesReceived?: number }): number {
  return (
    (summary.signalsDetected ?? 0) +
    (summary.outreachDraftsCreated ?? 0) +
    (summary.followupsSent ?? 0) +
    (summary.repliesReceived ?? 0)
  );
}

export default function SalesWorkflow() {
  const { session, loading: authLoading } = useAuth();
  const [, navigate] = useLocation();
  const [actions, setActions] = useState<NextAction[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [summary, setSummary] = useState<DailySummary>(EMPTY_SUMMARY);
  const [awayOpen, setAwayOpen] = useState(false);
  const [highlights, setHighlights] = useState<NextAction[]>([]);
  const [funnel, setFunnel] = useState(EMPTY_FUNNEL);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const hydratedRef = useRef(false);

  useEffect(() => {
    if (hydratedRef.current) return;
    const cached = readSurfaceCache<WorkflowPayload>(WORKFLOW_CACHE_KEY, WORKFLOW_CACHE_TTL_MS);
    if (!cached?.data) return;
    hydratedRef.current = true;
    setActions(cached.data.actions);
    setActivities(cached.data.activities);
    setSummary(cached.data.summary);
    setHighlights(cached.data.highlights ?? cached.data.summary.highlights ?? []);
    setFunnel(cached.data.funnel ?? EMPTY_FUNNEL);
    setLoading(false);
  }, []);

  const loadWorkflow = useCallback(async (opts?: { background?: boolean }) => {
    const token = session?.access_token;
    if (!token) return;
    const background = opts?.background ?? !hydratedRef.current;
    if (background) setRefreshing(true);
    else setLoading(true);

    try {
      const headers = authHeader(token);
      const base = getApiBase();
      const init = liveFetchInit({ headers });
      const [actionsRes, feedRes, summaryRes] = await Promise.all([
        fetchWithTimeout(`${base}/api/sales/next-actions`, init, WORKFLOW_FETCH_TIMEOUT_MS),
        fetchWithTimeout(`${base}/api/sales/activity-feed`, init, WORKFLOW_FETCH_TIMEOUT_MS),
        fetchWithTimeout(`${base}/api/sales/workflow-summary`, init, WORKFLOW_FETCH_TIMEOUT_MS),
      ]);

      let nextActions: NextAction[] = [];
      let nextActivities: ActivityItem[] = [];
      let nextSummary: DailySummary = EMPTY_SUMMARY;
      let nextHighlights: NextAction[] = [];
      let nextFunnel = EMPTY_FUNNEL;

      if (actionsRes.ok) {
        const payload = (await actionsRes.json()) as { actions?: NextAction[] };
        nextActions = payload.actions ?? [];
        setActions(nextActions);
      }
      if (feedRes.ok) {
        const payload = (await feedRes.json()) as { activities?: ActivityItem[] };
        nextActivities = payload.activities ?? [];
        setActivities(nextActivities);
      }
      if (summaryRes.ok) {
        const payload = (await summaryRes.json()) as DailySummary & {
          repliesReceived?: number;
          highlights?: NextAction[];
          funnel?: typeof EMPTY_FUNNEL;
        };
        nextSummary = applySummary(payload);
        nextHighlights = payload.highlights ?? [];
        nextFunnel = payload.funnel ?? EMPTY_FUNNEL;
        setSummary(nextSummary);
        setHighlights(nextHighlights);
        setFunnel(nextFunnel);
        if (summaryActivityTotal(payload) > 0 || nextHighlights.length > 0) setAwayOpen(true);
      }

      writeSurfaceCache(WORKFLOW_CACHE_KEY, {
        actions: nextActions,
        activities: nextActivities,
        summary: nextSummary,
        highlights: nextHighlights,
        funnel: nextFunnel,
      });
      hydratedRef.current = true;
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (!session?.access_token) return;
    void loadWorkflow({ background: hydratedRef.current });
  }, [session?.access_token, loadWorkflow]);

  const handleSelectActivity = (activity: ActivityItem) => {
    if (activity.route) {
      const url = activity.entity_id
        ? `${activity.route}?account=${encodeURIComponent(activity.entity_id)}`
        : activity.route;
      navigate(url);
    }
  };

  const handleFeedAction = useCallback(
    async (activity: ActivityItem, action: "approve" | "edit" | "skip" | "prioritize") => {
      const token = session?.access_token;
      if (!token) throw new Error("Not signed in");
      const res = await fetchWithTimeout(
        `${getApiBase()}/api/sales/feed-actions`,
        liveFetchInit({
          method: "POST",
          headers: { ...authHeader(token), "Content-Type": "application/json" },
          body: JSON.stringify({
            feed_id: activity.id,
            action,
            entity_id: activity.entity_id,
          }),
        }),
        WORKFLOW_FETCH_TIMEOUT_MS,
      );
      if (!res.ok) {
        const raw = await res.text();
        throw new Error(raw || `Action failed (${res.status})`);
      }
      const payload = (await res.json()) as { route?: string; entity_id?: string };
      if (action === "approve" || action === "skip" || action === "prioritize") {
        void loadWorkflow({ background: true });
      }
      return payload;
    },
    [session?.access_token, loadWorkflow],
  );

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

  const showEmptyState = !loading && actions.length === 0 && activities.length === 0;

  return (
    <div className="admin-workspace min-h-screen bg-neutral-50">
      <Header />
      <main className="max-w-6xl mx-auto px-4 pt-28 pb-8">
        <AdminNav />
        <div className="workspace-page-header mb-6">
          <div className="workspace-page-header-inner flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="workspace-kicker">Operator workspace</p>
              <h1>Sales Workflow</h1>
              <p>
                Ranked actions, live activity, and automation status across CRM, inbox, and SCOUT.
              </p>
            </div>
            {refreshing && !loading && (
              <p className="text-xs text-slate-400">Refreshing…</p>
            )}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 animate-pulse">
            <div className="h-96 rounded-2xl bg-neutral-200/70" />
            <div className="h-72 rounded-2xl bg-neutral-200/70" />
          </div>
        ) : showEmptyState ? (
          <p className="text-sm text-neutral-500">No workflow activity yet — save leads to CRM or run SCOUT to populate this view.</p>
        ) : (
          <div className="space-y-6">
            <WorkflowFunnelPanel funnel={funnel} />
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
            <ActivityFeed
              activities={activities}
              onSelectActivity={handleSelectActivity}
              onFeedAction={handleFeedAction}
            />
            <NextBestActions actions={actions} />
            </div>
          </div>
        )}
      </main>
      <WhileYouWereAway
        summary={summary}
        highlights={highlights}
        isOpen={awayOpen}
        onClose={() => setAwayOpen(false)}
        onOpen={() => setAwayOpen(true)}
      />
    </div>
  );
}
