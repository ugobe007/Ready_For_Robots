import { describe, expect, it } from "vitest";
import {
  buyerLeadsHref,
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

  it("sends anonymous users to 5 buyer leads", () => {
    const href = buyerLeadsHref({
      robotUrl: "https://www.unitree.com/",
      signedIn: false,
    });
    expect(href.startsWith("/results?")).toBe(true);
    expect(href).toContain("url=https%3A%2F%2Fwww.unitree.com%2F");
    expect(href).toContain("limit=5");
    expect(href).toContain("src=jobs_all_robots");
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
  });
});
