import { useEffect, useState } from "react";
import {
  fetchWithTimeout,
  getApiBase,
  publicFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";

export type DimRationale = {
  label: string;
  heif: number;
  index_score: number;
  drivers: string[];
};

export type TopRobot = {
  rank: number;
  name: string;
  vendor: string;
  score_total: number;
  heif_total: number;
  deployment_tier_label: string;
  why_top_rank: string;
  score_rationale: Record<string, DimRationale>;
  trials_and_pocs: {
    news_trial_headlines: number;
    news_deployment_headlines: number;
    catalog_pilot: boolean;
    estimated_poc_signals: number;
  };
  customer_integrations: {
    catalog_deployment_count: number;
    named_customers: string[];
  };
  top_headlines: { title?: string; url?: string; evidence_level?: string }[];
};

export type ReportComparisons = {
  dimension_leaders?: {
    dimension: string;
    name: string;
    vendor: string;
    heif: number;
    index_score: number;
  }[];
  index_vs_deployment?: {
    rank: number;
    name: string;
    vendor: string;
    score_total: number;
    heif_total: number;
    deployment_tier_label: string;
    commercial_deployments: number;
    capability_ahead_of_deployment?: boolean;
  }[];
  peer_heif_matrix?: {
    dimension_labels: string[];
    robots: { rank: number; name: string; heif_total: number; dimensions: Record<string, number> }[];
  };
  vendor_leaderboard?: {
    vendor: string;
    robot_count: number;
    poc_or_deployment: number;
    poc_or_deployment_pct: number;
    deployment_signal: number;
    total_deployments: number;
  }[];
  fleet_deployment_tier_breakdown?: Record<string, number>;
  ranking_divergence?: {
    name: string;
    index_rank: number;
    deployment_weighted_rank: number;
    rank_delta: number;
    commentary: string;
  }[];
};

export type NarrativeFinding = { title: string; body: string };

export type MonthOverMonth = {
  current_period?: string;
  previous_period?: string | null;
  has_prior: boolean;
  baseline_note?: string;
  narrative_bullets?: string[];
  fleet_metrics?: Record<string, { current: number; previous: number; delta: number }>;
  leader?: {
    changed?: boolean;
    current?: { name?: string; score?: number };
    previous?: { name?: string; score?: number };
  };
  new_to_top10?: string[];
  dropped_from_top10?: string[];
  movers?: {
    name: string;
    rank_current?: number;
    rank_previous?: number;
    rank_delta?: number;
    score_delta?: number;
    type?: string;
  }[];
};

export type ReportNarrative = {
  subtitle?: string;
  market_overview?: string[];
  month_over_month?: string[];
  key_findings?: NarrativeFinding[];
  competitive_dynamics?: string[];
  deployment_reality?: string[];
  ranking_commentary?: string[];
  buyer_guidance?: string[];
  at_a_glance?: Record<string, unknown>;
};

export type HumanoidIntelligenceReportData = {
  title: string;
  subtitle?: string;
  executive_summary: string[];
  narrative?: ReportNarrative;
  month_over_month?: MonthOverMonth;
  adoption_metrics: Record<string, unknown>;
  comparisons?: ReportComparisons;
  customer_landscape: {
    customer: string;
    robots: string[];
    vendors: string[];
    deployment_headlines: number;
    trial_headlines: number;
  }[];
  top_ranked: TopRobot[];
};

const HUMANOID_INTEL_CACHE_TTL_MS = 3 * 60 * 60 * 1000;

function intelligenceCacheKey(topN: number): string {
  return `humanoid_intelligence_v2_${topN}`;
}

export function isValidHumanoidReport(data: unknown): data is HumanoidIntelligenceReportData {
  if (!data || typeof data !== "object") return false;
  const r = data as HumanoidIntelligenceReportData;
  return Array.isArray(r.top_ranked) && r.top_ranked.length > 0 && Array.isArray(r.executive_summary);
}

export function useHumanoidIntelligenceReport(topN = 12) {
  const cacheKey = intelligenceCacheKey(topN);
  const cachedEntry = readSurfaceCache<HumanoidIntelligenceReportData>(
    cacheKey,
    HUMANOID_INTEL_CACHE_TTL_MS,
  );
  const [report, setReport] = useState<HumanoidIntelligenceReportData | null>(
    cachedEntry?.data && isValidHumanoidReport(cachedEntry.data) ? cachedEntry.data : null,
  );
  const [loading, setLoading] = useState(!report);
  const [error, setError] = useState<string | null>(null);
  const api = getApiBase();

  useEffect(() => {
    let cancelled = false;
    const freshCache = readSurfaceCache<HumanoidIntelligenceReportData>(
      cacheKey,
      HUMANOID_INTEL_CACHE_TTL_MS,
    );
    const paintedFromCache = Boolean(
      freshCache?.data && isValidHumanoidReport(freshCache.data),
    );
    if (!paintedFromCache) {
      setLoading(true);
      setError(null);
    } else {
      return;
    }

    void fetchWithTimeout(
      `${api}/api/humanoid/intelligence-report?top_n=${topN}`,
      publicFetchInit(),
      10_000,
      { publicCache: true },
    )
      .then(async (r) => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error((body as { detail?: string }).detail?.toString() || `HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((d) => {
        if (cancelled) return;
        const payload = d?.report;
        if (!isValidHumanoidReport(payload)) {
          if (!paintedFromCache) {
            setReport(null);
            setError("Report data was empty or incomplete.");
          }
          return;
        }
        setReport(payload);
        setError(null);
        writeSurfaceCache(cacheKey, payload);
      })
      .catch((e) => {
        if (cancelled) return;
        if (!paintedFromCache) {
          setReport(null);
          setError(e instanceof Error ? e.message : "Could not load report");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [api, topN, cacheKey]);

  return { report, loading, error };
}

/** Fly origin for binary PDF — avoids Vercel rewrite timeouts on long renders. */
export const HEIR_PDF_ORIGIN = "https://ready-2-robot.fly.dev";

export function humanoidReportPdfUrl(topN = 12, renderer: "fast" | "manus" = "fast"): string {
  const params = new URLSearchParams({
    top_n: String(topN),
    renderer,
  });
  return `${HEIR_PDF_ORIGIN}/api/humanoid/intelligence-report/pdf?${params}`;
}
