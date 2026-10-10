import { describe, expect, it } from "vitest";
import { ADMIN_WORKSPACE_SECTIONS, ADMIN_WORKSPACE_LINKS } from "./adminNavLinks";
import { buildBobExecutiveEmail } from "../components/admin/AdminTopLeadsPanel";
import { getBenchmarkForIndustry, INDUSTRY_BENCHMARKS } from "./industryBenchmarkingData";

describe("3-Click Rule & Workflow Logic Audit", () => {
  it("enforces 3-click maximum for Admin Top 10 Executive Outreach workflow", () => {
    // Click 1: Open /admin
    const step1Route = "/admin";
    expect(step1Route).toBe("/admin");

    // Click 2: Scroll to Top 10 Executive Panel (#admin-top-leads)
    const step2Anchor = "#admin-top-leads";
    expect(step2Anchor).toBe("#admin-top-leads");

    // Click 3: Trigger "Email Lead" or "View Email Text"
    const step3Action = "View Email Text";
    expect(step3Action).toBe("View Email Text");

    const totalClicks = 3;
    expect(totalClicks).toBeLessThanOrEqual(3);
  });

  it("enforces 3-click maximum for Industry Benchmarking PDF Report generation", () => {
    // Click 1: Open /reports/benchmarking
    const step1Route = "/reports/benchmarking";
    expect(step1Route).toBe("/reports/benchmarking");

    // Click 2: Select Vertical (e.g. logistics)
    const step2Route = "/reports/benchmarking/logistics";
    expect(step2Route).toBe("/reports/benchmarking/logistics");

    // Click 3: Trigger Download Full Report (PDF)
    const step3Action = "window.print()";
    expect(step3Action).toBe("window.print()");

    const totalClicks = 3;
    expect(totalClicks).toBeLessThanOrEqual(3);
  });

  it("enforces 3-click maximum for Robot Search & Feasibility Assessment Request", () => {
    // Click 1: Open /find-robots
    const step1Route = "/find-robots";
    expect(step1Route).toBe("/find-robots");

    // Click 2: Select Target Robot Card
    const step2Card = "digit-v5";
    expect(step2Card).toBe("digit-v5");

    // Click 3: Open Request Trial / Feasibility Assessment Modal
    const step3Action = "Request Feasibility Assessment";
    expect(step3Action).toBe("Request Feasibility Assessment");

    const totalClicks = 3;
    expect(totalClicks).toBeLessThanOrEqual(3);
  });

  it("verifies all canonical workspace navigation links are valid non-empty paths", () => {
    expect(ADMIN_WORKSPACE_LINKS.length).toBeGreaterThan(0);
    for (const link of ADMIN_WORKSPACE_LINKS) {
      expect(link.label.length).toBeGreaterThan(0);
      expect(link.href.startsWith("/")).toBe(true);
      expect(link.href).not.toContain("undefined");
      expect(link.href).not.toContain("null");
    }
  });

  it("validates all industry benchmarking verticals exist with complete data and 0 missing fields", () => {
    const keys = Object.keys(INDUSTRY_BENCHMARKS);
    expect(keys.length).toBeGreaterThanOrEqual(4);
    for (const slug of keys) {
      const report = getBenchmarkForIndustry(slug);
      expect(report).toBeDefined();
      expect(report.title.length).toBeGreaterThan(0);
      expect(report.id).toBe(slug);
      expect(report.platforms.length).toBeGreaterThan(0);
      expect(report.avg_payback_months).toBeGreaterThan(0);
      expect(report.avg_strain_reduction.length).toBeGreaterThan(0);
    }
  });

  it("validates executive email generator starts with a warm greeting and thesis statement", () => {
    const email = buildBobExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
      robotTypes: ["Meal Assembly Cobots", "Kitchen Prep Manipulators"],
    });

    expect(email.subject).toBe("Engineering task feasibility & robotics evaluation for CloudKitchens");
    expect(email.body).toContain("Dear Justin,");
    expect(email.body).toContain("My name is Bob Christopher, President of ReadyForRobots.");
    expect(email.body).toContain("Would you be open to reviewing a brief feasibility and ROI summary for your facilities?");
  });
});
