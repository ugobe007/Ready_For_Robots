/** Map FastAPI /api/leads row → Pipeline UI deal shape (stages are local until CRM sync exists). */

import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import { outreachInsightForIndustry } from "@/lib/industryContext";
import { OUTREACH_INTRO, OUTREACH_SIGNATURE } from "@/lib/agentMessaging";

export type PipelineStage = "New Signal" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";

export interface ApiLead {
  id: number;
  company_name?: string;
  industry?: string | null;
  inferred_contact_email?: string | null;
  inferred_contact_cc?: string[];
  inferred_contact_role?: string | null;
  location_city?: string | null;
  location_state?: string | null;
  score?: number | { overall_score?: number; overall_intent_score?: number };
  priority_tier?: string | null;
  share_summary?: string | null;
  share_blurb?: string | null;
  robot_types_needed?: string[];
  signals?: Array<{
    signal_type?: string;
    signal_label?: string;
    display_text?: string;
    text?: string;
  }>;
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
  project_timing?: {
    label?: string;
    display_phrase?: string;
    source?: string;
    day_min?: number | null;
    day_max?: number | null;
    confidence?: number;
  } | null;
  lead_highlights?: {
    specific_problem?: string | null;
    why_lead?: string[];
    procurement?: Record<string, unknown>;
    problem_size?: Record<string, unknown>;
    robot_categories?: string[];
    application_areas?: string[];
    agent_enrichment?: {
      rich_facts?: Array<{ claim?: string; evidence_span?: string }>;
      procurement_clues?: string[];
      timing_clues?: string[];
      ontology_gaps?: string[];
    } | null;
  } | null;
  lead_inference?: Record<string, unknown> | null;
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
    cleanAndClampText(
      (first as { display_text?: string })?.display_text || first?.text || "",
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
  const typ = (signalType || "").toLowerCase();
  if (typ.includes("labor") || typ.includes("job")) return `labor question for ${company}`;
  if (typ.includes("expansion") || typ.includes("capex") || typ.includes("funding")) return `automation signal we picked up on ${company}`;
  if (typ.includes("hospitality") || typ.includes("hotel")) return `automation angle at ${company}?`;
  return `quick question about ${company}`;
}

function outreachBody(lead: ApiLead, signalType: string, signalText: string): string {
  const company = lead.company_name || "your team";
  const lowerType = signalType.toLowerCase();
  const industry = (lead.industry || "your industry").toLowerCase();

  // Signal hook — one grounded observation
  let hook: string;
  if (lowerType.includes("labor") || lowerType.includes("job")) {
    hook = `We picked up a labor signal on ${company} — looks like staffing pressure in ${industry}. That's usually when automation starts making sense.`;
  } else if (lowerType.includes("expansion") || lowerType.includes("capex") || lowerType.includes("funding")) {
    hook = `We saw some expansion and CapEx signals on ${company}. ${industry.charAt(0).toUpperCase() + industry.slice(1)} teams in that position usually have at least one workflow where automation pays for itself.`;
  } else {
    hook = `${company} came up in our signal tracking. There may be an automation angle in ${industry} worth a quick look.`;
  }

  return [
    "Hey,",
    "",
    OUTREACH_INTRO,
    "",
    hook,
    "",
    "Worth a quick reply if there's any interest?",
    "",
    OUTREACH_SIGNATURE,
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
    contact: lead.inferred_contact_email || undefined,
    contactTitle: lead.inferred_contact_role
      ? `${lead.inferred_contact_role.replace(/_/g, " ")} (inferred)`
      : undefined,
    outreachSubject: outreachSubject(lead.company_name, type),
    outreachBody: outreachBody(lead, type, text),
    notes: cleanScrapedText(lead.share_summary) || undefined,
    shareSummary: lead.share_summary || undefined,
    shareBlurb: lead.share_blurb || undefined,
    priorityTier: lead.priority_tier || undefined,
    robotTypesNeeded: lead.robot_types_needed || [],
    researchUpdates: lead.research_updates,
    lastResearchedAt: lead.last_researched_at || null,
    latestMaterialUpdate: lead.latest_material_update || null,
    projectTiming: lead.project_timing || undefined,
    leadHighlights: lead.lead_highlights || undefined,
  };
}
