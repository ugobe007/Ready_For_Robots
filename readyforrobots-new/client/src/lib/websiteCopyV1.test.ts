import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("website copy v1: routes (§2)", () => {
  const app = read("../App.tsx");

  it("ships /icons, /icon-review and /experiment in dev builds only", () => {
    const devBlock = app.slice(
      app.indexOf("{import.meta.env.DEV ? ("),
      app.indexOf(") : null}", app.indexOf("{import.meta.env.DEV ? ("))
    );
    for (const path of ["/experiment", "/icons", "/icon-review"]) {
      expect(devBlock).toContain(`path="${path}"`);
      expect(app.split(`path="${path}"`).length - 1).toBe(1);
    }
  });

  it("keeps workspace routes but requires sign-in", () => {
    const gated: Record<string, string> = {
      "/robot-ready": "RobotsPage",
      "/robots": "RobotsPage",
      "/robots/report": "HumanoidReportPage",
      "/roi-calculator": "BenchmarkPage",
      "/roi": "BenchmarkPage",
      "/benchmark": "BenchmarkPage",
      "/marketplace": "MarketplacePage",
      "/social": "SocialPage",
      "/compare": "ComparePage",
      "/signals": "SignalsPage",
      "/sales-console": "SalesConsolePage",
      "/sales-workflow": "SalesWorkflowPage",
      "/supply-pipeline": "SupplyPipelinePage",
      "/vendor/design": "VendorDesignPage",
    };
    for (const [path, page] of Object.entries(gated)) {
      expect(app).toContain(`<Route path="${path}" component={${page}} />`);
      expect(app).toMatch(new RegExp(`const ${page} = signedIn\\(`));
    }
  });

  it("gates bare /pipeline but leaves the Jobs CRM desk wall in place", () => {
    expect(app).toMatch(/const SignedInPipeline = signedIn\(Pipeline\)/);
    expect(app).toMatch(
      /isJobsHandoffSrc\(src\) \? <Pipeline \/> : <SignedInPipeline \/>/
    );
  });

  it("sends How it works to About until the Phase 5 flow ships", () => {
    expect(app).toMatch(
      /<Route path="\/how-it-works">\s*<Redirect to="\/about" \/>/
    );
  });
});

describe("website copy v1: no sign-up wall on results (rule 5)", () => {
  const workspace = read("../components/RobotJobsWorkspace.tsx");

  it("shows every matched card, signed in or not", () => {
    expect(workspace).not.toMatch(/jobs_free_cap_blur/);
    expect(workspace).not.toMatch(/Free users can view up to 3/);
    expect(workspace).not.toMatch(/Sign Up to Unlock All Jobs/);
    expect(workspace).not.toMatch(/isPaidUser/);
    expect(workspace).toMatch(
      /const displayedJobs = rawBaseJobs\.slice\(0, JOBS_PIPELINE_CAP\)/
    );
  });

  it("example job modal points to the robot URL, not a sign-up", () => {
    const modal = read("../components/jobs/LiveJobDetailModal.tsx");
    expect(modal).toMatch(/Find buyers for your robot →/);
    expect(modal).not.toMatch(/Sign up free/);
    expect(workspace).not.toMatch(/QuickSignupModal/);
  });
});

describe("website copy v1: pricing (§6) and About (§7)", () => {
  it("pricing is one early-access card with the founding price placeholder", () => {
    const pricing = read("../pages/Pricing.tsx");
    expect(pricing).toMatch(/title="Early access"/);
    expect(pricing).toMatch(/Founding customer/);
    expect(pricing).toMatch(/\[founding price, e\.g\. \$X\/month\]/);
    expect(pricing).not.toMatch(
      /Basic|Premium|Activated Buyer Leads|Managed Outreach|Vault Contact|Hunter|Reevo|pipeline_action|robot_types_needed/
    );
    expect(pricing.match(/\bq: "/g)).toHaveLength(3);
  });

  it("About drops the hard-coded stat tiles", () => {
    const about = read("../pages/Intelligence.tsx");
    expect(about).toMatch(/Robots need jobs\./);
    expect(about).not.toMatch(
      /Active Open Trials|Daily Action Signals|Verified Buyer Leads|Robot Models/
    );
  });
});
