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
  humanoidPilotTier?: string;
  humanoid_pilot_tier?: string;
  humanoidPilotScore?: number;
  humanoid_pilot_score?: number;
};

function tierForLead(lead: PipelineActionLead): string {
  const raw = (lead.priorityTier || lead.priority_tier || "WARM").toUpperCase();
  return raw in TIER_ORDER ? raw : "WARM";
}

const HUMANOID_TIER_ORDER: Record<string, number> = {
  ACTIVE_PILOT: 0,
  PILOT_INTENT: 1,
  HUMANOID_MENTION: 2,
};

function humanoidTierForLead(lead: PipelineActionLead): string {
  return (
    lead.humanoidPilotTier ||
    lead.humanoid_pilot_tier ||
    "NONE"
  ).toUpperCase();
}

function humanoidScoreForLead(lead: PipelineActionLead): number {
  return lead.humanoidPilotScore ?? lead.humanoid_pilot_score ?? 0;
}

function labelForLead(lead: PipelineActionLead): string {
  const hpAction =
    (lead as { humanoidPilotAction?: string; humanoid_pilot_action?: string })
      .humanoidPilotAction ||
    (lead as { humanoid_pilot_action?: string }).humanoid_pilot_action;
  const hpTier = humanoidTierForLead(lead);
  if (hpAction && (hpTier === "ACTIVE_PILOT" || hpTier === "PILOT_INTENT")) {
    return `Humanoid · ${hpAction}`;
  }
  const action = (lead.pipelineAction || lead.pipeline_action || "").trim();
  if (action) return action;
  const tier = tierForLead(lead);
  if (tier === "HOT") return "Prioritize outreach — HOT intent detected";
  if (tier === "WARM") return "Review signals and draft intro";
  return "Monitor and qualify when timing improves";
}

export function buildNextActionsFromPipelineLeads(
  leads: PipelineActionLead[],
  max = 3
): NextAction[] {
  const ranked = [...leads]
    .filter(lead => lead.id)
    .sort((a, b) => {
      const hpDiff =
        (HUMANOID_TIER_ORDER[humanoidTierForLead(a)] ?? 9) -
        (HUMANOID_TIER_ORDER[humanoidTierForLead(b)] ?? 9);
      if (hpDiff !== 0) return hpDiff;
      const hpScoreDiff = humanoidScoreForLead(b) - humanoidScoreForLead(a);
      if (hpScoreDiff !== 0) return hpScoreDiff;
      const tierDiff =
        (TIER_ORDER[tierForLead(a)] ?? 9) - (TIER_ORDER[tierForLead(b)] ?? 9);
      if (tierDiff !== 0) return tierDiff;
      return (b.score ?? 0) - (a.score ?? 0);
    });

  return ranked.slice(0, max).map(lead => {
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
      meta: { tier, humanoid_pilot_tier: humanoidTierForLead(lead) },
    };
  });
}

export function mapApiNextActions(
  payload: { actions?: NextAction[] } | null
): NextAction[] {
  return Array.isArray(payload?.actions) ? payload.actions : [];
}
