/** Map FastAPI /api/leads row → Pipeline UI deal shape (stages are local until CRM sync exists). */

export type PipelineStage = "New Signal" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";

export interface ApiLead {
  id: number;
  company_name?: string;
  industry?: string | null;
  location_city?: string | null;
  location_state?: string | null;
  score?: number | { overall_score?: number; overall_intent_score?: number };
  priority_tier?: string | null;
  share_summary?: string | null;
  signals?: Array<{ signal_type?: string; display_text?: string; text?: string }>;
  gtm?: { suggested_motion?: string };
}

const SIGNAL_COLORS: Record<string, string> = {
  labor_shortage: "#f87171",
  job_posting: "#fbbf24",
  capex: "#a78bfa",
  funding_round: "#34d399",
  news: "#60a5fa",
  default: "#a78bfa",
};

function numericScore(lead: ApiLead): number {
  const s = lead.score;
  if (typeof s === "number") return Math.round(s);
  if (s && typeof s === "object") {
    const v = s.overall_score ?? s.overall_intent_score;
    if (typeof v === "number") return Math.round(v);
  }
  return 0;
}

function stageForLead(lead: ApiLead): PipelineStage {
  const t = (lead.priority_tier || "").toUpperCase();
  if (t === "HOT") return "Draft Ready";
  if (t === "WARM") return "New Signal";
  return "New Signal";
}

function topSignal(lead: ApiLead): { type: string; text: string; color: string } {
  const sigs = lead.signals || [];
  const first = sigs[0];
  const typ = (first?.signal_type || "news").replace(/ /g, "_").toLowerCase();
  const text =
    (first as { display_text?: string })?.display_text ||
    first?.text ||
    lead.share_summary ||
    "Buying signal detected";
  const color = SIGNAL_COLORS[typ] || SIGNAL_COLORS.default;
  const label = typ.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return { type: label, text: String(text).slice(0, 220), color };
}

export function mapApiLeadToDeal(lead: ApiLead) {
  const loc = [lead.location_city, lead.location_state].filter(Boolean).join(", ") || "—";
  const { type, text, color } = topSignal(lead);
  const score = numericScore(lead);
  return {
    id: lead.id,
    company: lead.company_name || `Company #${lead.id}`,
    location: loc,
    industry: lead.industry || "—",
    score,
    signal: text,
    signalType: type,
    signalColor: color,
    stage: stageForLead(lead) as PipelineStage,
    updatedAt: "live",
    contact: undefined as string | undefined,
    contactTitle: undefined as string | undefined,
    outreachSubject: `${lead.company_name || "Team"} — automation fit`,
    outreachBody: `Hi,\n\n${text}\n\nI'd like to share how teams in your space are using automation to move faster — worth a brief call?\n\n— SCOUT`,
    notes: lead.share_summary || undefined,
  };
}
