/**
 * GET /api/leads and GET /api/leads/by-id/{id} row shape (_fmt_company).
 */

export type LeadSignal = {
  signal_type?: string;
  signal_label?: string;
  strength?: number;
  signal_strength?: number;
  /** Raw ingestion text (may include HTML, scaffolding). */
  raw_text?: string;
  /** Sales-facing excerpt from the API (`format_signal_for_sales`). */
  display_text?: string;
  source_url?: string;
};

export type CrmMetadata = {
  budget?: { top_amount?: string; signals?: unknown[] };
  timing?: { top_window?: string; signals?: unknown[] };
  automation_requirements?: string;
  decision_makers?: { name?: string; title?: string; source_url?: string; confidence?: number }[];
  quality_flags?: Record<string, unknown>;
};

export type GtmPayload = {
  readiness_label?: string;
  suggested_motion?: string;
  why_now?: string[] | string;
};

export type LeadScore = {
  overall_score?: number;
  signal_score?: number;
  lead_value_score?: number;
  automation_score?: number;
  labor_pain_score?: number;
  expansion_score?: number;
  market_fit_score?: number;
};

export type LeadRow = {
  id: number;
  company_name?: string;
  industry?: string;
  website?: string;
  location_city?: string;
  location_state?: string;
  employee_estimate?: number | null;
  source?: string;
  priority_tier?: string;
  priority_score?: number;
  priority_reasons?: string[];
  is_junk?: boolean;
  junk_reason?: string;
  score?: LeadScore | Record<string, unknown>;
  signals?: LeadSignal[];
  signal_count?: number;
  /** One-line buying story from strongest evidence signal. */
  core_need?: string;
  share_summary?: string;
  share_blurb?: string;
  /** ISO timestamps from API when present */
  created_at?: string | null;
  updated_at?: string | null;
  automation_profile?: Record<string, unknown> | null;
  gtm?: GtmPayload | Record<string, unknown> | null;
  crm_metadata?: CrmMetadata | null;
  primary_link_url?: string | null;
  primary_link_kind?: string | null;
  procurement_hints?: string[];
};

/** Prefer API-cleaned copy; fall back to raw for older backends. */
export function signalDisplayExcerpt(s: LeadSignal): string {
  return (s.display_text || s.raw_text || "").replace(/\n/g, " ").trim();
}

export function signalStrengthPct(s: LeadSignal): number {
  const v = Number(s.strength ?? s.signal_strength ?? 0);
  const x = v > 1 ? v / 100 : v;
  return Math.round(Math.min(100, Math.max(0, x * 100)));
}

export function scoreNum(lead: LeadRow, key: keyof LeadScore): number {
  const sc = lead.score as LeadScore | undefined;
  if (!sc) return 0;
  const v = sc[key];
  return typeof v === "number" ? v : 0;
}
