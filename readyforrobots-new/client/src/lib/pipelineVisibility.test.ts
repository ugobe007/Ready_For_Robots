import { describe, expect, it } from "vitest";
import {
  PIPELINE_PREVIEW_LIMIT,
  capOpportunities,
  occupiedPipelineStages,
  opportunityLimitForPlan,
} from "./pipelineVisibility";

describe("pipelineVisibility", () => {
  it("caps anonymous and free workspaces at 15 opportunities", () => {
    expect(opportunityLimitForPlan("anonymous")).toBe(15);
    expect(opportunityLimitForPlan("free")).toBe(15);
    expect(opportunityLimitForPlan("paid")).toBeNull();
    expect(PIPELINE_PREVIEW_LIMIT).toBe(15);
  });

  it("slices non-Pro lists and leaves paid lists intact", () => {
    const deals = Array.from({ length: 40 }, (_, i) => ({ id: i }));
    expect(capOpportunities(deals, "free")).toHaveLength(15);
    expect(capOpportunities(deals, "anonymous")).toHaveLength(15);
    expect(capOpportunities(deals, "paid")).toHaveLength(40);
  });

  it("hides empty CRM stages so blank New Signal / Discovered columns do not render", () => {
    const stages = ["New Signal", "Discovered", "Draft Ready", "Outreach Sent"] as const;
    const deals = [
      { id: 1, stage: "Draft Ready" as const },
      { id: 2, stage: "Draft Ready" as const },
    ];
    expect(occupiedPipelineStages(stages, deals)).toEqual(["Draft Ready"]);
  });
});
