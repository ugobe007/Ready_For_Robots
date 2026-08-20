import { describe, expect, it } from "vitest";
import {
  BUYER_LEADS_ANON_CAP,
  JOBS_EXAMPLE_CAP,
  JOBS_FOR_YOUR_ROBOT_CTA,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_FOR_YOUR_ROBOT_KEEP_CTA,
  JOBS_LIST_NEXT_STEP_HEADING,
  JOBS_SCAN_STEPS,
  buyerLeadsCtaHeading,
  buyerLeadsCtaLabel,
  buyerLeadsHref,
  buyerLeadsToShow,
  capExampleJobs,
  isJobsHandoffSrc,
  jobsHeading,
  jobsSignupHref,
  landingStageAfterConfirm,
  isJobsHomeDest,
  persistJobsHandoffSrc,
  shouldRestoreJobsWorkspace,
} from "./jobsWorkflow";

describe("jobsWorkflow", () => {
  it("sends one robot to the profile checkpoint", () => {
    expect(landingStageAfterConfirm(1)).toBe("review");
  });

  it("sends several or all robots to jobs, not a catalog", () => {
    expect(landingStageAfterConfirm(2)).toBe("jobs");
    expect(landingStageAfterConfirm(4)).toBe("jobs");
  });

  it("titles multi-robot jobs with the company, not a SKU list", () => {
    expect(
      jobsHeading({
        productName: "G1",
        companyName: "Unitree",
        robotCount: 4,
      }),
    ).toBe("Jobs for Unitree");
    expect(
      jobsHeading({
        productName: "G1",
        companyName: "Unitree",
        robotCount: 1,
      }),
    ).toBe("Jobs for G1");
  });

  it("caps the Jobs terminal at 5 example jobs even when more exist", () => {
    expect(JOBS_EXAMPLE_CAP).toBe(5);
    expect(capExampleJobs([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])).toEqual([
      1, 2, 3, 4, 5,
    ]);
    expect(capExampleJobs(["a", "b"])).toEqual(["a", "b"]);
  });

  it("sends anonymous users to 5 jobs, not buyer leads", () => {
    const href = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: false,
    });
    expect(href.startsWith("/results?")).toBe(true);
    expect(href).toContain("url=https%3A%2F%2Fwww.unitree.com%2F");
    expect(href).toContain(`limit=${BUYER_LEADS_ANON_CAP}`);
    expect(href).toContain("src=jobs_all_robots");
    expect(buyerLeadsCtaLabel(false)).toBe("Jobs for your robot →");
    expect(buyerLeadsCtaHeading(false)).toBe("Next step: Jobs for your robot");
  });

  it("sends signed-in users to the pipeline with the same robot URL", () => {
    const href = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: true,
      submissionId: 42,
      industry: "warehousing",
    });
    expect(href.startsWith("/pipeline?")).toBe(true);
    expect(href).toContain("url=https%3A%2F%2Fwww.unitree.com%2F");
    expect(href).toContain("submission=42");
    expect(href).toContain("industries=warehousing");
    expect(href).not.toContain("limit=");
    expect(buyerLeadsCtaLabel(true)).toBe("Jobs for your robot →");
    expect(buyerLeadsCtaHeading(true)).toBe("Next step: Jobs for your robot");
  });

  it("never uses buyer or sales-lead language on the Jobs CTA", () => {
    for (const signedIn of [false, true]) {
      const label = buyerLeadsCtaLabel(signedIn);
      const heading = buyerLeadsCtaHeading(signedIn);
      expect(label.toLowerCase()).toContain("job");
      expect(heading.toLowerCase()).toContain("job");
      expect(label).not.toMatch(/buyer|lead/i);
      expect(heading).not.toMatch(/buyer|lead/i);
    }
    expect(JOBS_FOR_YOUR_ROBOT_CTA).toBe("Jobs for your robot →");
    expect(JOBS_FOR_YOUR_ROBOT_HEADING).toBe("Jobs for your robot");
    expect(JOBS_LIST_NEXT_STEP_HEADING).toBe("Next step: Jobs for your robot");
    expect(JOBS_LIST_NEXT_STEP_HEADING).not.toMatch(/buyer|lead/i);
    expect(JOBS_LIST_NEXT_STEP_HEADING).not.toMatch(/Next step: buyer leads/i);
    expect(JOBS_FOR_YOUR_ROBOT_KEEP_CTA.toLowerCase()).toContain("job");
    expect(JOBS_FOR_YOUR_ROBOT_KEEP_CTA).not.toMatch(/buyer|lead/i);
    expect(JOBS_FOR_YOUR_ROBOT_CTA).not.toMatch(/See Buyer Leads|SEE BUYER LEADS/i);
    for (const step of JOBS_SCAN_STEPS) {
      expect(step).not.toMatch(/buyer|sales lead/i);
    }
  });

  it("recognizes Jobs terminal handoff src values", () => {
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    expect(isJobsHandoffSrc("robot_jobs_qualify")).toBe(true);
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    expect(isJobsHandoffSrc("results_scan")).toBe(false);
    expect(isJobsHandoffSrc("signal_activation")).toBe(false);
  });

  it("keeps a Jobs src on pipeline/signup hops instead of results_scan", () => {
    expect(persistJobsHandoffSrc("jobs_all_robots")).toBe("jobs_all_robots");
    expect(persistJobsHandoffSrc("results_scan")).toBe("jobs_all_robots");
    const pipeline = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: true,
      src: "jobs_all_robots",
      leadId: 9,
    });
    expect(pipeline).toContain("src=jobs_all_robots");
    expect(pipeline).toContain("lead=9");
    expect(pipeline).not.toContain("results_scan");
    expect(jobsSignupHref(pipeline, "jobs_all_robots")).toContain("src=jobs_all_robots");
  });

  it("does not restore the Jobs workspace on a fresh visit or reload of /", () => {
    expect(shouldRestoreJobsWorkspace({ navigationType: "navigate" })).toBe(false);
    expect(shouldRestoreJobsWorkspace({ navigationType: 0 })).toBe(false);
    expect(shouldRestoreJobsWorkspace({ navigationType: "reload" })).toBe(false);
    expect(shouldRestoreJobsWorkspace({ navigationType: 1 })).toBe(false);
    expect(shouldRestoreJobsWorkspace({ navigationType: "back_forward" })).toBe(true);
    expect(shouldRestoreJobsWorkspace({ navigationType: "navigate", restoreOnce: true })).toBe(true);
    expect(shouldRestoreJobsWorkspace({ navigationType: "navigate", restoreQuery: true })).toBe(true);
  });

  it("falls back to the live buyer feed when URL lookup returns no rows", () => {
    expect(
      buyerLeadsToShow({
        scopedRows: [],
        liveRows: ["acme", "bold"],
        lookupPending: true,
        scopeToUrl: true,
      }),
    ).toEqual([]);
    expect(
      buyerLeadsToShow({
        scopedRows: [],
        liveRows: ["acme", "bold"],
        lookupPending: false,
        scopeToUrl: true,
      }),
    ).toEqual(["acme", "bold"]);
    expect(
      buyerLeadsToShow({
        scopedRows: ["scoped"],
        liveRows: ["acme"],
        lookupPending: false,
        scopeToUrl: true,
      }),
    ).toEqual(["scoped"]);
    expect(
      buyerLeadsToShow({
        scopedRows: ["scoped"],
        liveRows: ["acme"],
        lookupPending: false,
        scopeToUrl: false,
      }),
    ).toEqual(["acme"]);
  });

  it("treats / and /jobs paths as Jobs home after auth, not /pipeline", () => {
    expect(isJobsHomeDest("/")).toBe(true);
    expect(isJobsHomeDest("/jobs/unitree")).toBe(true);
    expect(isJobsHomeDest("/pipeline?src=jobs_all_robots")).toBe(false);
    expect(isJobsHomeDest("/results?limit=5")).toBe(false);
  });
});
