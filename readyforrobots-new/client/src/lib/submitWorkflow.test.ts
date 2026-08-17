import { describe, expect, it } from "vitest";
import {
  canRevealResults,
  dotsBar,
  isResearchingPhase,
  researchStageIndex,
  researchStatusLine,
  tapeStaysMarket,
  type ComposedSearch,
} from "./submitWorkflow";

describe("submitWorkflow", () => {
  it("keeps the public tape until RESULTS", () => {
    expect(tapeStaysMarket("idle")).toBe(true);
    expect(tapeStaysMarket("researching")).toBe(true);
    expect(tapeStaysMarket("product_selection")).toBe(true);
    expect(tapeStaysMarket("composing")).toBe(true);
    expect(tapeStaysMarket("results")).toBe(false);
  });

  it("does not treat overlapping booleans as the research signal", () => {
    expect(isResearchingPhase("researching")).toBe(true);
    expect(isResearchingPhase("composing")).toBe(true);
    expect(isResearchingPhase("results")).toBe(false);
    expect(isResearchingPhase("idle")).toBe(false);
  });

  it("refuses to reveal without a composed first-page model", () => {
    expect(canRevealResults(null)).toBe(false);
    const composed: ComposedSearch = {
      robotName: "Vega",
      companyName: "Dexmate",
      robotClass: "mobile_manipulator",
      profileTier: "B",
      jobCount: 12,
      jobs: [{ job_key: "cnc_load" }],
      topJobs: [{ job_key: "cnc_load" }],
      capabilities: [],
      profile: { selected_product: { name: "Vega" } },
      timings: {
        resolve_ms: 400,
        profile_ms: 2100,
        match_ms: 80,
        total_ms: 2600,
        cached: true,
      },
      thin: false,
    };
    expect(canRevealResults(composed)).toBe(true);
  });

  it("uses completed stages, not a fake percent", () => {
    expect(researchStageIndex(0, false)).toBe(0);
    expect(researchStageIndex(400, false)).toBe(1);
    expect(researchStageIndex(1200, false)).toBe(2);
    expect(researchStageIndex(1200, true)).toBe(3);
    expect(dotsBar(2)).toBe("██████████░░░░░");
    expect(researchStatusLine({ robotName: "Digit", composing: false })).toMatch(
      /Researching Digit/,
    );
  });
});
