/** Map FastAPI /api/leads row → Pipeline UI deal shape (stages are local until CRM sync exists). */

import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import { outreachInsightForIndustry } from "@/lib/industryContext";
import { OUTREACH_CTA, OUTREACH_SIGNATURE } from "@/lib/agentMessaging";

export type PipelineStage = "New Signal" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";

export interface ApiLead {
  id: number;
  pipeline_slim?: boolean;
  company_name?: string;
  industry?: string | null;
  inferred_contact_email?: string | null;
  inferred_contact_cc?: string[];
  inferred_contact_role?: string | null;
  inferred_contact_phone?: string | null;
  inferred_linkedin_profile?: {
    url?: string;
    score?: number;
    confidence?: string;
    person?: string;
    person_title?: string;
  } | null;
  contact_intelligence?: {
    status?: string;
    updated_at?: string;
    phone?: {
      best?: {
        phone?: string;
        raw?: string;
        source?: string;
        score?: number;
        evidence?: string;
      } | null;
      candidates?: Array<{
        phone?: string;
        raw?: string;
        source?: string;
        score?: number;
        evidence?: string;
      }>;
    };
    linkedin?: {
      status?: string;
      best_profile?: {
        url?: string;
        title?: string;
        snippet?: string;
        score?: number;
        confidence?: string;
        person?: string;
        person_title?: string;
      } | null;
      disambiguation?: {
        status?: string;
        target_person?: string;
        target_company?: string;
        reason?: string;
        script?: string[];
        candidates?: Array<{
          url?: string;
          title?: string;
          snippet?: string;
          score?: number;
        }>;
      } | null;
    };
    sales_intuition?: {
      why_sales_lead?: {
        specific_problem?: string | null;
        reasons?: string[];
      };
      robot_history?: Array<{
        signal_type?: string | null;
        summary?: string;
        source_url?: string | null;
      }>;
      larger_opportunity?: {
        industry?: string | null;
        points?: string[];
      };
      competitor_robot_usage?: Array<{
        title?: string;
        summary?: string;
        source_url?: string | null;
        source_domain?: string | null;
      }>;
    };
  } | null;
  location_city?: string | null;
  location_state?: string | null;
  score?: number | { overall_score?: number; overall_intent_score?: number };
  priority_tier?: string | null;
  share_summary?: string | null;
  share_blurb?: string | null;
  pipeline_action?: string | null;
  lead_quality?: {
    schema?: string;
    overall_score?: number;
    confidence_band?: string;
    dimension_scores?: Record<string, number>;
    weights?: Record<string, number>;
    weight_source?: string;
    missing_fields_count?: number;
    evidence_traces?: Array<{ dimension?: string; score?: number; evidence?: string }>;
    quality_gate?: { passed?: boolean; reason?: string };
  };
  confidence_band?: string | null;
  evidence_trace?: Array<{ dimension?: string; score?: number; evidence?: string }>;
  humanoid_pilot_tier?: string | null;
  humanoid_pilot_score?: number | null;
  humanoid_pilot_label?: string | null;
  humanoid_pilot_action?: string | null;
  humanoid_origin_status?: string | null;
  humanoid_non_us_vendor_flag?: boolean;
  humanoid_non_us_vendor_count?: number;
  humanoid_non_us_vendor_models?: string[];
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
    source_kind?: string | null;
    source_label?: string | null;
    evidence_tension?: string | null;
    recommended_action?: string | null;
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
  crm_evidence?: {
    friction_point?: string | null;
    workflow_scope?: { count?: number; label?: string | null; items?: string[] };
    timing?: { label?: string | null; source?: string | null; confidence?: number | null };
    robot_type?: { label?: string | null; items?: string[] };
    budget?: {
      top_amount?: string | null;
      has_budget?: boolean;
      signals?: Array<{ amount?: string; context?: string; source_url?: string }>;
    };
    decision_makers?: Array<{ name?: string; title?: string; source_url?: string; confidence?: number }>;
    similar_deployments?: Array<{
      title?: string | null;
      summary?: string | null;
      source_domain?: string | null;
      source_url?: string | null;
      source_label?: string | null;
      evidence_tension?: string | null;
    }>;
    missing_fields?: Array<{
      key?: string;
      label?: string;
      status?: string;
      research_prompt?: string;
    }>;
    research_status?: {
      needs_research?: boolean;
      state?: string;
      missing_count?: number;
    };
  } | null;
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
  const action = (lead.pipeline_action || "").trim();

  let hook: string;
  if (action) {
    const actionBody = action.includes(":") ? action.slice(action.indexOf(":") + 1).trim() : action;
    const normalized =
      actionBody.length > 0
        ? `${actionBody.charAt(0).toLowerCase()}${actionBody.slice(1)}`
        : actionBody;
    hook = `I've been following ${company} — ${normalized}`;
  } else if (lowerType.includes("labor") || lowerType.includes("job")) {
    hook = `I've been watching staffing pressure at ${company} in ${industry} — that's usually when teams start looking at automation on the floor.`;
  } else if (lowerType.includes("expansion") || lowerType.includes("capex") || lowerType.includes("funding")) {
    hook = `I noticed expansion and CapEx activity around ${company}. In ${industry}, that's often when one workflow automation project makes the case for itself.`;
  } else {
    hook = `I've had ${company} on my radar in ${industry} — there may be an automation angle worth a quick look on your side.`;
  }

  return ["Hey,", "", hook, "", OUTREACH_CTA, "", OUTREACH_SIGNATURE].join("\n");
}

export function pipelineStageFromCrmOutreach(stage?: string | null): PipelineStage | null {
  const s = (stage || "").toLowerCase();
  if (!s) return null;
  if (["draft_ready", "review_required", "draft_approved"].includes(s)) return "Draft Ready";
  if (["intro_sent", "sequence_step_sent", "sent"].includes(s)) return "Outreach Sent";
  if (["replied", "qualified", "nurture", "discovery"].includes(s)) return "Qualified";
  if (["meeting", "meeting_booked", "proposal"].includes(s)) return "Meeting Set";
  return null;
}

export function crmOutreachStageFromPipelineStage(stage: PipelineStage): string {
  const map: Record<PipelineStage, string> = {
    "New Signal": "new",
    "Draft Ready": "draft_ready",
    "Outreach Sent": "intro_sent",
    "Qualified": "qualified",
    "Meeting Set": "meeting",
  };
  return map[stage];
}

export function mapApiLeadToDeal(lead: ApiLead, crmOutreachStage?: string | null) {
  const loc = [lead.location_city, lead.location_state].filter(Boolean).join(", ") || "—";
  const { type, text, color } = topSignal(lead);
  const score = numericScore(lead);
  const crmStage = pipelineStageFromCrmOutreach(crmOutreachStage);
  return {
    id: lead.id,
    company: lead.company_name || `Company #${lead.id}`,
    location: loc,
    industry: lead.industry || "—",
    score,
    signal: text,
    signalType: type,
    signalColor: color,
    stage: (crmStage ?? stageForLead(lead)) as PipelineStage,
    updatedAt: "live",
    contact: lead.inferred_contact_email || undefined,
    contactPhone: lead.inferred_contact_phone || undefined,
    linkedInProfile: lead.inferred_linkedin_profile || undefined,
    contactIntelligence: lead.contact_intelligence || undefined,
    contactTitle: lead.inferred_contact_role
      ? `${lead.inferred_contact_role.replace(/_/g, " ")} (inferred)`
      : undefined,
    outreachSubject: outreachSubject(lead.company_name, type),
    outreachBody: outreachBody(lead, type, text),
    notes: cleanScrapedText(lead.pipeline_action || lead.share_summary) || undefined,
    shareSummary: lead.share_summary || undefined,
    shareBlurb: lead.share_blurb || undefined,
    pipelineAction: lead.pipeline_action || undefined,
    leadQuality: lead.lead_quality || undefined,
    confidenceBand: lead.confidence_band || lead.lead_quality?.confidence_band || undefined,
    evidenceTrace: lead.evidence_trace || lead.lead_quality?.evidence_traces || undefined,
    humanoidPilotTier: lead.humanoid_pilot_tier || undefined,
    humanoidPilotScore: lead.humanoid_pilot_score ?? undefined,
    humanoidPilotLabel: lead.humanoid_pilot_label || undefined,
    humanoidPilotAction: lead.humanoid_pilot_action || undefined,
    humanoidOriginStatus: lead.humanoid_origin_status || undefined,
    humanoidNonUsVendorFlag: Boolean(lead.humanoid_non_us_vendor_flag),
    humanoidNonUsVendorCount: lead.humanoid_non_us_vendor_count ?? undefined,
    humanoidNonUsVendorModels: lead.humanoid_non_us_vendor_models || [],
    priorityTier: lead.priority_tier || undefined,
    robotTypesNeeded: lead.robot_types_needed || [],
    researchUpdates: lead.research_updates,
    lastResearchedAt: lead.last_researched_at || null,
    latestMaterialUpdate: lead.latest_material_update || null,
    projectTiming: lead.project_timing || undefined,
    leadHighlights: lead.lead_highlights || undefined,
    crmEvidence: lead.crm_evidence || undefined,
  };
}
