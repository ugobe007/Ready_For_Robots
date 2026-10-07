import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  JOBS_PRESENTATION_CTA,
  JOBS_PRESENTATION_HINT,
  jobsPresentationHref,
  jobsPresentationPaid,
} from "./jobsPresentation";

const here = dirname(fileURLToPath(import.meta.url));

describe("jobs presentation offer", () => {
  it("stays behind signup and pay, never in front of FIND", () => {
    expect(JOBS_PRESENTATION_CTA).toMatch(/product presentation/i);
    expect(JOBS_PRESENTATION_HINT).toMatch(/After Job Cards/i);
    expect(JOBS_PRESENTATION_HINT).toMatch(/Sign up and pay/i);
    expect(JOBS_PRESENTATION_HINT).not.toMatch(/FIND/);
    expect(jobsPresentationPaid(null)).toBe(false);
    expect(jobsPresentationPaid("free")).toBe(false);
    expect(jobsPresentationPaid("pro")).toBe(true);
    expect(jobsPresentationHref({ signedIn: false, paid: false })).toMatch(
      /\/signup\?/
    );
    expect(jobsPresentationHref({ signedIn: true, paid: false })).toMatch(
      /\/pricing\?upgrade=pro/
    );
    expect(jobsPresentationHref({ signedIn: true, paid: true })).toBe(
      "#jobs-presentation"
    );
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    const findForm = workspace.slice(
      workspace.indexOf('aria-label="Find jobs for your robot"'),
      workspace.indexOf("function JobsPanel")
    );
    expect(findForm).not.toMatch(/JobsPresentationOffer/);
    expect(workspace).toMatch(/JobsPresentationOffer/);
    const offer = readFileSync(
      join(here, "../components/JobsPresentationOffer.tsx"),
      "utf8"
    );
    expect(offer).toMatch(/Sign up and pay to order/);
    expect(offer).toMatch(/Pay to order this presentation/);
    expect(offer).toMatch(/requestRobotPresentation/);
    expect(offer).not.toMatch(/deck is ready/i);
  });
});
