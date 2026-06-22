/** Map pipeline leads/deals → ranked next actions for the right-rail panel. */

import type { NextAction } from "@/types/readyForRobots";

const TIER_ORDER: Record<string, number> = { HOT: 0, WARM: 1, COLD: 2 };
const TIER_PRIORITY: Record<string, NextAction["priority"]> = {
  HOT: "high",
  WARM: "medium",
  COLD: "low",
};

export type PipelineActionLead = {
  id: number;
  company?: string;
  company_name?: string;
  score?: number;
  priorityTier?: string;
  priority_tier?: string;
  pipelineAction?: string;
  pipeline_action?: string;
};

function tierForLead(lead: PipelineActionLead): string {
  const raw = (lead.priorityTier || lead.priority_tier || "WARM").toUpperCase();
  return raw in TIER_ORDER ? raw : "WARM";
}

function labelForLead(lead: PipelineActionLead): string {
  const action = (lead.pipelineAction || lead.pipeline_action || "").trim();
  if (action) return action;
  const tier = tierForLead(lead);
  if (tier === "HOT") return "Prioritize outreach — HOT intent detected";
  if (tier === "WARM") return "Review signals and draft intro";
  return "Monitor and qualify when timing improves";
}

export function buildNextActionsFromPipelineLeads(
  leads: PipelineActionLead[],
  max = 3,
): NextAction[] {
  const ranked = [...leads]
    .filter((lead) => lead.id)
    .sort((a, b) => {
      const tierDiff = (TIER_ORDER[tierForLead(a)] ?? 9) - (TIER_ORDER[tierForLead(b)] ?? 9);
      if (tierDiff !== 0) return tierDiff;
      return (b.score ?? 0) - (a.score ?? 0);
    });

  return ranked.slice(0, max).map((lead) => {
    const tier = tierForLead(lead);
    return {
      id: `pipeline:${lead.id}`,
      label: labelForLead(lead),
      companyName: lead.company || lead.company_name || `Company #${lead.id}`,
      priority: TIER_PRIORITY[tier] ?? "medium",
      route: "/pipeline",
      entity_type: "company",
      entity_id: String(lead.id),
      score: lead.score,
      meta: { tier },
    };
  });
}

export function mapApiNextActions(payload: { actions?: NextAction[] } | null): NextAction[] {
  return Array.isArray(payload?.actions) ? payload.actions : [];
}
