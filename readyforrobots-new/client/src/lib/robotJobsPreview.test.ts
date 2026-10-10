import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { formatInlineJobLine, type PreviewJob } from "./robotJobsPreview";

const here = dirname(fileURLToPath(import.meta.url));

describe("robotJobsPreview", () => {
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

  it("FIND home fetches live preview, not the stale tape", () => {
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
    expect(proof).toMatch(/fetchRobotJobsPreview\(3\)/);
    expect(workspace).toMatch(/FindProofJobs/);
    expect(workspace).not.toMatch(/MARKET_TAPE_JOBS/);
    expect(workspace).not.toMatch(/UNLOCK FULL FEASIBILITY/i);
  });
});
