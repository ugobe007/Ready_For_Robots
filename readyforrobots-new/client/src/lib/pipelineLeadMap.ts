/** Map FastAPI /api/leads row → Pipeline UI deal shape (stages are local until CRM sync exists). */

import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import { outreachInsightForIndustry } from "@/lib/industryContext";

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
  research_updates?: Array<{
    id: number;
    update_type?: string;
    title?: string;
    summary?: string;
    source_url?: string | null;
    source_domain?: string | null;
    detected_at?: string | null;
    significance_score?: number;
  }>;
  last_researched_at?: string | null;
  latest_material_update?: {
    id: number;
    title?: string;
    summary?: string;
    source_domain?: string | null;
    detected_at?: string | null;
    significance_score?: number;
  } | null;
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
  const text = cleanAndClampText(
    (first as { display_text?: string })?.display_text ||
    first?.text ||
    lead.share_summary ||
    "Buying signal detected",
    220,
  ) || "Buying signal detected";
  const color = SIGNAL_COLORS[typ] || SIGNAL_COLORS.default;
  const label = typ.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return { type: label, text, color };
}

function industryInsight(industry?: string | null): string {
  return outreachInsightForIndustry(industry);
}

function signalOpening(signalType: string, signalText: string): string {
  const lowerType = signalType.toLowerCase();
  if (lowerType.includes("labor") || lowerType.includes("job")) {
    return `I saw the labor and hiring signal around your team: ${signalText}`;
  }
  if (lowerType.includes("expansion") || lowerType.includes("capacity")) {
    return `I saw the expansion signal around your operation: ${signalText}`;
  }
  if (lowerType.includes("capex") || lowerType.includes("funding")) {
    return `I saw the budget or investment signal around your organization: ${signalText}`;
  }
  if (lowerType.includes("automation") || lowerType.includes("robot")) {
    return `I saw the automation signal around your team: ${signalText}`;
  }
  return `I saw this market signal connected to your organization: ${signalText}`;
}

function outreachSubject(companyName?: string, signalType?: string): string {
  const company = companyName || "your team";
  const signal = signalType && signalType !== "News" ? signalType.toLowerCase() : "operations signal";
  return `${company}: practical automation angle from a ${signal}`;
}

function outreachBody(lead: ApiLead, signalType: string, signalText: string): string {
  const company = lead.company_name || "your team";
  const insight = industryInsight(lead.industry);
  const opening = signalOpening(signalType, signalText);
  const suggestedMotion = cleanAndClampText(lead.gtm?.suggested_motion, 180);

  const motionLine = suggestedMotion
    ? `The practical next step may be to pressure-test this against ${suggestedMotion.toLowerCase()}.`
    : "The practical next step may be to identify one contained workflow where automation can prove value without disrupting the broader operation.";

  return [
    "Hi,",
    "",
    opening,
    "",
    insight,
    "",
    `That is why ${company} stood out. This does not look like a generic robotics pitch; it looks like a timing question: where is the team feeling the most operational drag, and which workflow could be improved first?`,
    "",
    motionLine,
    "",
    "Would it be useful if I sent over a short view of the workflows that usually map to this kind of signal?",
    "",
    "Best,",
    "SCOUT",
  ].join("\n");
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
    outreachSubject: outreachSubject(lead.company_name, type),
    outreachBody: outreachBody(lead, type, text),
    notes: cleanScrapedText(lead.share_summary) || undefined,
    researchUpdates: lead.research_updates,
    lastResearchedAt: lead.last_researched_at || null,
    latestMaterialUpdate: lead.latest_material_update || null,
  };
}
