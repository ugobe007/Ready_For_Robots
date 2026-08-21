import { describe, expect, it } from "vitest";
import {
  FIND_JOBS_CTA,
  JOBS_EXAMPLE_CAP,
  JOBS_FOR_YOUR_ROBOT_CTA,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_FOR_YOUR_ROBOT_KEEP_CTA,
  JOBS_LIST_NEXT_STEP_HEADING,
  JOBS_SCAN_STEPS,
  QUALIFY_JOB_CTA,
  buyerLeadsCtaHeading,
  buyerLeadsCtaLabel,
  buyerLeadsHref,
  buyerLeadsToShow,
  capExampleJobs,
  isJobsHandoffSrc,
  jobsHeading,
  jobsQualifySignupHref,
  jobsSignupHref,
  jobsWorkspaceRestoreHref,
  landingStageAfterConfirm,
  isJobsHomeDest,
  persistJobsHandoffSrc,
  shouldRestoreJobsWorkspace,
  armJobsWorkspaceRestore,
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

  it("never hops Jobs traffic to /pipeline or /results", () => {
    for (const signedIn of [false, true]) {
      const href = buyerLeadsHref({
        robotUrl: "https://www.unitree.com/",
        signedIn,
        submissionId: 42,
        industry: "warehousing",
        src: "jobs_all_robots",
        leadId: 9,
      });
      expect(href).toBe("/?restore=1");
      expect(href).not.toContain("/pipeline");
      expect(href).not.toContain("/results");
    }
    expect(jobsWorkspaceRestoreHref()).toBe("/?restore=1");
    expect(buyerLeadsCtaLabel(false)).toBe(QUALIFY_JOB_CTA);
    expect(buyerLeadsCtaHeading(true)).toBe("This job looks interesting");
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
    expect(FIND_JOBS_CTA).toBe("Find jobs →");
    expect(FIND_JOBS_CTA).not.toMatch(/buyer|lead/i);
    expect(JOBS_FOR_YOUR_ROBOT_HEADING).toBe("Jobs for your robot");
    expect(JOBS_LIST_NEXT_STEP_HEADING).toBe("This job looks interesting");
    expect(JOBS_LIST_NEXT_STEP_HEADING).not.toMatch(/buyer|lead/i);
    expect(JOBS_LIST_NEXT_STEP_HEADING).not.toMatch(/Next step: buyer leads/i);
    expect(JOBS_LIST_NEXT_STEP_HEADING).not.toMatch(/Next step: Jobs for your robot/i);
    expect(JOBS_FOR_YOUR_ROBOT_KEEP_CTA.toLowerCase()).toContain("search");
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

  it("keeps a Jobs src on signup hops instead of results_scan", () => {
    expect(persistJobsHandoffSrc("jobs_all_robots")).toBe("jobs_all_robots");
    expect(persistJobsHandoffSrc("results_scan")).toBe("jobs_all_robots");
    const home = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: true,
      src: "jobs_all_robots",
      leadId: 9,
    });
    expect(home).toBe("/?restore=1");
    expect(home).not.toContain("results_scan");
    expect(jobsSignupHref(home, "jobs_all_robots")).toContain("src=jobs_all_robots");
    expect(jobsSignupHref(home, "jobs_all_robots")).toContain("next=%2F%3Frestore%3D1");
    expect(jobsQualifySignupHref()).toContain("src=robot_jobs_qualify");
    expect(jobsQualifySignupHref()).toContain("next=%2F%3Frestore%3D1");
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
    expect(isJobsHomeDest("/?restore=1")).toBe(true);
    expect(isJobsHomeDest("/pipeline?src=jobs_all_robots")).toBe(false);
    expect(isJobsHomeDest("/results?limit=5")).toBe(false);
  });

  it("arms leftover Jobs hops to restore `/` instead of a second job list", () => {
    const store = new Map<string, string>();
    const memory = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    };
    Object.defineProperty(globalThis, "window", {
      value: { sessionStorage: memory },
      configurable: true,
    });
    expect(armJobsWorkspaceRestore()).toBe("/?restore=1");
    expect(memory.getItem("rfr_jobs_restore_once")).toBe("1");
  });
});
