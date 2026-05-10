import { useCallback, useEffect, useState } from "react";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  buildDailySummary,
  buildNextActionsFromLeads,
  leadRowToActivityItem,
  parseLeadsListJson,
  type DailyReportPayload,
  type PipelineStatsPayload,
} from "@/lib/dealFlowMappers";
import { DEAL_FLOW_LEADS_LIMIT } from "@/lib/leadsApiConstants";
import type { LeadRow } from "@/lib/leadTypes";
import type { ActivityItem, DailySummary, NextAction } from "@/types/readyForRobots";

export type DealFlowDataState = {
  loading: boolean;
  error: string | null;
  activities: ActivityItem[];
  nextActions: NextAction[];
  dailySummary: DailySummary | null;
  refetch: () => void;
};

function parseJsonResponse<T>(text: string): T | null {
  if (!text || text.trimStart().startsWith("<")) return null;
  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

export function useDealFlowData(): DealFlowDataState {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [nextActions, setNextActions] = useState<NextAction[]>([]);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const API = getApiBase();
    const leadsUrl = `${API}/api/leads?limit=${DEAL_FLOW_LEADS_LIMIT}&sort=score&exclude_junk=true`;
    const pipelineUrl = `${API}/api/pipeline-stats`;
    const dailyUrl = `${API}/api/daily-report?days=1&format=json`;

    try {
      const [leadsRes, pipeRes, dailyRes] = await Promise.all([
        fetch(leadsUrl, liveFetchInit()),
        fetch(pipelineUrl, liveFetchInit()),
        fetch(dailyUrl, liveFetchInit()),
      ]);

      if (!leadsRes.ok) {
        setError(`Leads API error (${leadsRes.status}). Is the backend running at ${API}?`);
        setActivities([]);
        setNextActions([]);
        setDailySummary(null);
        return;
      }

      const leadsText = await leadsRes.text();
      if (leadsText.trimStart().startsWith("<")) {
        setError("Leads API returned HTML instead of JSON.");
        setActivities([]);
        setNextActions([]);
        setDailySummary(null);
        return;
      }

      let leads: LeadRow[] = [];
      try {
        leads = parseLeadsListJson(leadsText);
      } catch {
        setError("Could not parse leads JSON.");
        setActivities([]);
        setNextActions([]);
        setDailySummary(null);
        return;
      }

      const pipeText = pipeRes.ok ? await pipeRes.text() : "";
      const dailyText = dailyRes.ok ? await dailyRes.text() : "";
      const pipeJson = parseJsonResponse<PipelineStatsPayload>(pipeText);
      const dailyJson = parseJsonResponse<DailyReportPayload>(dailyText);

      setActivities(leads.map(leadRowToActivityItem));
      setNextActions(buildNextActionsFromLeads(leads));
      setDailySummary(buildDailySummary(pipeJson, dailyJson));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg || "Network error loading deal flow.");
      setActivities([]);
      setNextActions([]);
      setDailySummary(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    loading,
    error,
    activities,
    nextActions,
    dailySummary,
    refetch: load,
  };
}
