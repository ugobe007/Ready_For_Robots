import { describe, expect, it } from "vitest";
import {
  resolveSignupWorkflowReturnPath,
  shouldHonorWorkflowResults,
  workflowResultsPath,
} from "./signupWorkflowPath";

describe("signupWorkflowPath", () => {
  it("never rewrites an explicit /results next to /pipeline", () => {
    const next =
      "/results?url=https%3A%2F%2Fexample.com%2Frobot&limit=5&src=home_signup_return";
    expect(
      resolveSignupWorkflowReturnPath({
        nextRaw: next,
        prefill: {
          company_url: "https://example.com/robot",
          src: "home_url_submit",
        },
        matchedPipelineReturnPath:
          "/pipeline?src=results_scan&url=https://example.com/robot",
      })
    ).toBe(next);
  });

  it("rebuilds /results from company_url when next is empty", () => {
    const path = resolveSignupWorkflowReturnPath({
      nextRaw: "",
      prefill: {
        company_url: "https://acme.robot/arm",
        src: "home_url_submit",
      },
    });
    expect(path.startsWith("/results?")).toBe(true);
    expect(path).toContain("url=https%3A%2F%2Facme.robot%2Farm");
    expect(path).toContain("limit=5");
  });

  it("honors /results even when company_url prefill is missing", () => {
    expect(shouldHonorWorkflowResults("/results?url=https://x.test", {})).toBe(
      true
    );
    expect(
      workflowResultsPath({}, "/results?url=https%3A%2F%2Fx.test&limit=5")
    ).toContain("url=https%3A%2F%2Fx.test");
  });

  it("keeps explicit /pipeline next for matched unlock", () => {
    const next = "/pipeline?src=results_scan&url=https://example.com";
    expect(
      resolveSignupWorkflowReturnPath({
        nextRaw: next,
        prefill: {
          company_url: "https://example.com",
          src: "pipeline_matched_unlock",
        },
        matchedPipelineReturnPath: next,
      })
    ).toBe(next);
  });

  it("returns jobs product paths to / or /jobs/:slug (not /pipeline)", () => {
    expect(
      resolveSignupWorkflowReturnPath({
        nextRaw: "/",
        prefill: { src: "robot_jobs" },
      })
    ).toBe("/");
    expect(
      resolveSignupWorkflowReturnPath({
        nextRaw: "/jobs?src=c1_job_mfg_kits",
        prefill: { src: "robot_jobs" },
      })
    ).toBe("/?src=c1_job_mfg_kits");
    expect(
      resolveSignupWorkflowReturnPath({
        nextRaw: "/jobs/locus-origin?src=robot_jobs",
        prefill: { src: "robot_jobs" },
      })
    ).toBe("/jobs/locus-origin?src=robot_jobs");
  });
});
