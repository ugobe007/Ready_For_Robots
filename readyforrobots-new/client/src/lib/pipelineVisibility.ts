/** Free/anonymous market preview. Pro (`paid`) sees the full scored feed. */
export const PIPELINE_PREVIEW_LIMIT = 15;

export type PipelinePlan = "anonymous" | "free" | "paid";

export function opportunityLimitForPlan(plan: PipelinePlan): number | null {
  return plan === "paid" ? null : PIPELINE_PREVIEW_LIMIT;
}

export function capOpportunities<T>(deals: T[], plan: PipelinePlan): T[] {
  const limit = opportunityLimitForPlan(plan);
  if (limit == null) return deals;
  return deals.slice(0, limit);
}

export function occupiedPipelineStages<T extends { stage: S }, S>(stages: readonly S[], deals: T[]): S[] {
  return stages.filter((stage) => deals.some((deal) => deal.stage === stage));
}
