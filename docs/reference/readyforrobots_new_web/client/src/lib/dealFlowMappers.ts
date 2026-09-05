import type { LeadRow } from "@/lib/leadTypes";
import { scoreNum, signalDisplayExcerpt } from "@/lib/leadTypes";
import type {
  ActivityItem,
  ActivityStatus,
  DailySummary,
  NextAction,
  PriorityLevel,
} from "@/types/readyForRobots";

function formatCreatedAt(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    const now = new Date();
    const sameDay =
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate();
    if (sameDay) return "Today";
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (
      d.getFullYear() === yesterday.getFullYear() &&
      d.getMonth() === yesterday.getMonth() &&
      d.getDate() === yesterday.getDate()
    ) {
      return "Yesterday";
    }
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

function tierToStatus(tier: string | undefined): ActivityStatus {
  const t = (tier || "").toUpperCase();
  if (t === "HOT") return "qualified";
  if (t === "WARM") return "new_signal";
  if (t === "COLD") return "opportunity_created";
  return "new_signal";
}

function robotUseCaseFromLead(lead: LeadRow): string {
  const ap = lead.automation_profile as Record<string, unknown> | null | undefined;
  const cats = ap?.robot_categories;
  if (Array.isArray(cats) && cats.length) {
    return (cats as string[])
      .slice(0, 4)
      .map((s) => String(s).replace(/_/g, " "))
      .join(", ");
  }
  const sigs = lead.signals || [];
  if (sigs[0]?.signal_label) return String(sigs[0].signal_label);
  if (sigs[0]?.signal_type) return String(sigs[0].signal_type).replace(/_/g, " ");
  return "Automation opportunity (see signals)";
}

function signalSummaryFromLead(lead: LeadRow): string {
  const core = (lead.core_need || "").trim();
  if (core) return core;
  const sigs = lead.signals || [];
  if (sigs.length) return signalDisplayExcerpt(sigs[0]).slice(0, 280) || "Signal captured in pipeline.";
  return "Buying-intent signal in pipeline.";
}

function signalTypeFromLead(lead: LeadRow): string {
  const sigs = lead.signals || [];
  if (sigs[0]?.signal_label) return String(sigs[0].signal_label);
  if (sigs[0]?.signal_type) return String(sigs[0].signal_type).replace(/_/g, " ");
  return "Pipeline signal";
}

function recommendedActionFromLead(lead: LeadRow): string {
  const gtm = lead.gtm as { suggested_motion?: string } | undefined;
  const motion = gtm?.suggested_motion?.trim();
  if (motion) return motion;
  const reasons = lead.priority_reasons;
  if (Array.isArray(reasons) && reasons.length) {
    return `Review: ${reasons.slice(0, 2).join(" · ")}`;
  }
  return "Review lead and decide outreach in CRM or dashboard.";
}

export function leadRowToActivityItem(lead: LeadRow): ActivityItem {
  const id = String(lead.id);
  const overall = Math.round(scoreNum(lead, "overall_score"));
  return {
    id,
    companyName: lead.company_name || `Company ${id}`,
    industry: lead.industry || "—",
    signalType: signalTypeFromLead(lead),
    signalSummary: signalSummaryFromLead(lead),
    robotUseCase: robotUseCaseFromLead(lead),
    recommendedAction: recommendedActionFromLead(lead),
    status: tierToStatus(lead.priority_tier),
    confidenceScore: Math.min(100, Math.max(0, overall)),
    createdAt: formatCreatedAt(lead.created_at ?? null),
  };
}

function tierToPriority(tier: string | undefined): PriorityLevel {
  const t = (tier || "").toUpperCase();
  if (t === "HOT") return "high";
  if (t === "WARM") return "medium";
  return "low";
}

export function buildNextActionsFromLeads(leads: LeadRow[], max = 6): NextAction[] {
  return leads.slice(0, max).map((lead, i) => {
    const tier = (lead.priority_tier || "").toUpperCase();
    const label =
      tier === "HOT"
        ? "Prioritize outreach — HOT intent"
        : tier === "WARM"
          ? "Review signals and draft intro"
          : "Add to watchlist / qualify";
    return {
      id: `next-${lead.id}-${i}`,
      label,
      companyName: lead.company_name || `Company ${lead.id}`,
      priority: tierToPriority(lead.priority_tier),
    };
  });
}

/** `GET /api/pipeline-stats` body (partial). */
export type PipelineStatsPayload = {
  database?: {
    new_last_24h?: number | null;
    new_last_7d?: number | null;
    hot?: number | null;
    warm?: number | null;
    cold?: number | null;
    total_signals?: number | null;
  };
};

/** `GET /api/daily-report?days=1&format=json` body (partial). */
export type DailyReportPayload = {
  totals?: {
    signals?: number;
    companies_with_signals?: number;
  };
};

export const EMPTY_DAILY_SUMMARY: DailySummary = {
  signalsDetected: 0,
  companiesQualified: 0,
  outreachDraftsCreated: 0,
  followupsSent: 0,
  opportunitiesAdvanced: 0,
};

export function buildDailySummary(
  pipeline: PipelineStatsPayload | null,
  daily: DailyReportPayload | null,
): DailySummary {
  const db = pipeline?.database ?? {};
  const totals = daily?.totals ?? {};
  const signalsDetected = typeof totals.signals === "number" ? totals.signals : 0;
  const companiesQualified =
    typeof totals.companies_with_signals === "number"
      ? totals.companies_with_signals
      : Math.max(0, (db.hot ?? 0) + (db.warm ?? 0)) || 0;

  return {
    signalsDetected,
    companiesQualified,
    outreachDraftsCreated: 0,
    followupsSent: 0,
    opportunitiesAdvanced: typeof db.new_last_24h === "number" ? db.new_last_24h : 0,
  };
}

export function parseLeadsListJson(text: string): LeadRow[] {
  const raw = JSON.parse(text) as unknown;
  if (!Array.isArray(raw)) return [];
  return raw as LeadRow[];
}
