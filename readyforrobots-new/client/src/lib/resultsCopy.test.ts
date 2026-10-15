import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  cardIndustry,
  RESULTS_EMPTY_HEADLINE,
  RESULTS_EXAMPLE_NOTE_BODY,
  RESULTS_SAVE_CTA,
  resultsHeading,
  resultsSelectedHint,
  robotSummaryLine,
  showQualificationOnResults,
} from "@/lib/resultsCopy";

const here = dirname(fileURLToPath(import.meta.url));
const workspace = readFileSync(
  join(here, "../components/RobotJobsWorkspace.tsx"),
  "utf8"
);
const jobsPanel = workspace.slice(
  workspace.indexOf("function JobsPanel("),
  workspace.indexOf("function ClassPicker(")
);

describe("results copy (website copy v1 §5)", () => {
  it("heads results with the product, or the company for a lineup", () => {
    expect(
      resultsHeading({ productName: "ADAM", companyName: "Richtech" })
    ).toBe("Buyers for ADAM");
    expect(
      resultsHeading({
        productName: "ADAM",
        companyName: "Richtech",
        robotCount: 3,
      })
    ).toBe("Buyers for Richtech");
    expect(resultsHeading({})).toBe("Buyers for your robot");
  });

  it("builds the summary line from the parts it has", () => {
    expect(
      robotSummaryLine({
        robotClass: "humanoid",
        work: ["pick and place", "tote handling", "third"],
        industries: ["Warehousing", "warehousing", "Retail"],
      })
    ).toBe("Humanoid · Pick and place, tote handling · Warehousing, retail");
    expect(robotSummaryLine({ work: ["Floor cleaning"] })).toBe(
      "Floor cleaning"
    );
    expect(robotSummaryLine({})).toBe("");
  });

  it("only shows a plain industry label on cards", () => {
    expect(cardIndustry("food_service")).toBe("Food service");
    expect(cardIndustry("CBRE · Dallas")).toBeNull();
    expect(cardIndustry("Dallas", ["CBRE", "Dallas"])).toBeNull();
    expect(cardIndustry("")).toBeNull();
  });

  it("hides the internal pending qualification", () => {
    expect(showQualificationOnResults("pending_robot")).toBe(false);
    expect(showQualificationOnResults("conditional")).toBe(true);
  });

  it("uses the doc's save, empty and example copy", () => {
    expect(RESULTS_SAVE_CTA).toBe("Save buyers →");
    expect(resultsSelectedHint(4)).toBe("4 selected.");
    expect(RESULTS_EMPTY_HEADLINE).toBe("No buyers yet for this robot.");
    expect(RESULTS_EXAMPLE_NOTE_BODY).toMatch(/starting with warehouses/);
    expect(jobsPanel).toMatch(/data-results-example-note/);
    expect(jobsPanel).toMatch(/data-results-summary/);
  });

  it("drops the removed results chrome", () => {
    expect(workspace).not.toMatch(/How to use this feed/);
    expect(workspace).not.toMatch(/Uncheck a row to skip it/);
    expect(workspace).not.toMatch(/Company identity not fully verified/);
    expect(workspace).not.toMatch(
      /<span className=\{eyebrow\}>Profile<\/span>/
    );
    expect(workspace).not.toMatch(/JOBS_NEXT_HINT/);
    expect(workspace).not.toMatch(/jobsCountEyebrow/);
    expect(workspace).not.toMatch(/\} on the CRM desk`/);
    expect(jobsPanel.match(/<JobsActivateBar/g)?.length).toBe(1);
  });
});
