import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  fetchRobotJobsPreview,
  formatInlineJobLine,
  previewJobsFromTape,
  type PreviewJob,
} from "./robotJobsPreview";

const here = dirname(fileURLToPath(import.meta.url));

describe("robotJobsPreview", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("formats employer workplace work timing and contact as one line", () => {
    const job: PreviewJob = {
      job_key: "j1",
      employer: "Attindas Hygiene Partners",
      workplace: "Greenville",
      work: "Palletizing",
      description: "End-of-line case palletizing.",
      timing: "First seen 2026-10-01",
      decision_maker: "Not named on the posting",
      contact: "No page email or apply URL. We will not invent one.",
    };
    const line = formatInlineJobLine(job);
    expect(line).toContain("Attindas Hygiene Partners");
    expect(line).toContain("Greenville");
    expect(line).toContain("Palletizing");
    expect(line).not.toMatch(/RaaS|payback|Unlock/i);
  });

  it("FIND home fetches live preview, with named-employer tape only as HTML fallback", () => {
    const preview = readFileSync(join(here, "./robotJobsPreview.ts"), "utf8");
    const proof = readFileSync(
      join(here, "../components/jobs/FindProofJobs.tsx"),
      "utf8"
    );
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    expect(preview).toMatch(/\/api\/robot-jobs\/preview/);
    expect(preview).toMatch(/getPublicReadApiBase/);
    expect(preview).toMatch(/previewJobsFromTape/);
    expect(proof).toMatch(/fetchRobotJobsPreview\(3\)/);
    expect(workspace).not.toMatch(/FindProofJobs/);
    expect(workspace).toMatch(/MARKET_TAPE_JOBS/);
    expect(workspace).not.toMatch(/UNLOCK FULL FEASIBILITY/i);
  });

  it("labels every bundled tape row Example and keeps robot makers out", () => {
    const rows = previewJobsFromTape(8);
    expect(rows.length).toBeGreaterThan(0);
    for (const job of rows) {
      expect(job.is_example).toBe(true);
      expect(job.source_url).toBeNull();
      expect(formatInlineJobLine(job)).toMatch(/^Example — /);
    }
    const tape = readFileSync(join(here, "./market_tape_jobs.json"), "utf8");
    expect(tape).not.toMatch(/Intuitive Surgical/i);
  });

  it("home feed and job modal carry the Example label and no invented specs", () => {
    const modal = readFileSync(
      join(here, "../components/jobs/LiveJobDetailModal.tsx"),
      "utf8"
    );
    const tape = readFileSync(
      join(here, "../components/jobs/LiveJobTape.tsx"),
      "utf8"
    );
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    expect(modal).toMatch(/JOB_CARD_EXAMPLE_LABEL/);
    expect(modal).toMatch(/JOB_CARD_EXAMPLE_NOTE/);
    expect(modal).not.toMatch(
      /Verified Work Opportunity|payback|RaaS|109\+|turnkey|3-Shift|\bANSI\b|Unlock Full Feasibility/
    );
    expect(tape).toMatch(/data-job-example="true"/);
    expect(tape).not.toMatch(/Live robot work|"NEW"/);
    expect(landing).not.toMatch(/Verified Physical Work Feed|ROI breakdown/);
  });

  it("maps named employers from the tape corpus without a URL submit", () => {
    const rows = previewJobsFromTape(3);
    expect(rows).toHaveLength(3);
    for (const job of rows) {
      expect(job.employer.trim()).not.toBe("");
      expect(job.work.trim()).not.toBe("");
      expect(job.job_key.trim()).not.toBe("");
    }
  });

  it("uses live JSON jobs when Fly returns the preview table", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: { get: () => "application/json" },
        json: async () => ({
          jobs: [
            {
              job_key: "live-1",
              employer: "Rochester Regional Health",
              workplace: "Rochester, NY",
              work: "Pharmacy delivery",
              description: "Move pharmacy totes.",
              timing: "",
              decision_maker: "",
              contact: "",
            },
          ],
        }),
      })
    );
    const rows = await fetchRobotJobsPreview(3);
    expect(rows).toHaveLength(1);
    expect(rows[0].employer).toBe("Rochester Regional Health");
  });

  it("falls back to named-employer tape when preview returns the SPA shell", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: { get: () => "text/html; charset=utf-8" },
        json: async () => {
          throw new Error("not json");
        },
      })
    );
    const rows = await fetchRobotJobsPreview(3);
    expect(rows).toHaveLength(3);
    expect(rows[0].employer.trim()).not.toBe("");
  });

  it("falls back to named-employer tape when live JSON is an empty table", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: { get: () => "application/json" },
        json: async () => ({ jobs: [] }),
      })
    );
    const rows = await fetchRobotJobsPreview(3);
    expect(rows).toHaveLength(3);
    expect(rows[0].employer.trim()).not.toBe("");
  });
});
