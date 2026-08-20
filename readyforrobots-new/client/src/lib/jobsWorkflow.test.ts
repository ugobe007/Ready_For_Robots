import { describe, expect, it } from "vitest";
import {
  BUYER_LEADS_ANON_CAP,
  JOBS_EXAMPLE_CAP,
  buyerLeadsCtaLabel,
  buyerLeadsHref,
  capExampleJobs,
  isJobsHandoffSrc,
  jobsHeading,
  landingStageAfterConfirm,
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

  it("sends anonymous users to 5 buyer leads", () => {
    const href = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: false,
    });
    expect(href.startsWith("/results?")).toBe(true);
    expect(href).toContain("url=https%3A%2F%2Fwww.unitree.com%2F");
    expect(href).toContain(`limit=${BUYER_LEADS_ANON_CAP}`);
    expect(href).toContain("src=jobs_all_robots");
    expect(buyerLeadsCtaLabel(false)).toBe("See 5 buyer leads →");
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
    expect(buyerLeadsCtaLabel(true)).toBe("See buyer leads →");
  });

  it("recognizes Jobs terminal handoff src values", () => {
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    expect(isJobsHandoffSrc("robot_jobs_qualify")).toBe(true);
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    expect(isJobsHandoffSrc("results_scan")).toBe(false);
    expect(isJobsHandoffSrc("signal_activation")).toBe(false);
  });
});
