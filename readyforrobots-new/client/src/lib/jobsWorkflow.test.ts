import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  FIND_JOBS_CTA,
  JOBS_EXAMPLE_CAP,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_NEXT_CTA,
  JOBS_NEXT_HINT,
  JOBS_PLACE_CTA,
  JOBS_SCAN_STEPS,
  buyerLeadsHref,
  buyerLeadsToShow,
  capExampleJobs,
  defaultCheckedJobKeys,
  isJobsHandoffSrc,
  isPlaceSrc,
  jobsActivateHref,
  jobsCountEyebrow,
  jobsForActivatedPipeline,
  jobsFreshHomeHref,
  goJobsFreshHome,
  jobsHeading,
  jobsPlaceHref,
  jobsSignupHref,
  jobsWorkspaceRestoreHref,
  landingStageAfterConfirm,
  lineupJobLookups,
  normalizeRobotClass,
  portfolioShowsJobCounts,
  productClassesFromLineup,
  robotClassJobsLabel,
  isJobsHomeDest,
  persistJobsHandoffSrc,
  placeBuyersToShow,
  shouldRestoreJobsWorkspace,
  armJobsWorkspaceRestore,
} from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("jobsWorkflow", () => {
  it("sends one robot to the profile checkpoint", () => {
    expect(landingStageAfterConfirm(1)).toBe("review");
  });

  it("sends several or all robots to jobs for the robot type", () => {
    expect(landingStageAfterConfirm(2)).toBe("jobs");
    expect(landingStageAfterConfirm(4)).toBe("jobs");
  });

  it("forces a real FIND navigation from the wordmark even on /", () => {
    expect(typeof goJobsFreshHome).toBe("function");
    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    expect(header).toMatch(/onClick=\{onJobsFreshHomeClick\}/);
    expect(header).not.toMatch(/<Link\s+href=\{jobsFreshHomeHref/);
    const chrome = readFileSync(
      join(here, "../components/Header.tsx"),
      "utf8",
    );
    expect(chrome).toMatch(/onJobsFreshHomeClick/);
    const workflow = readFileSync(join(here, "./jobsWorkflow.ts"), "utf8");
    expect(workflow).toMatch(/location\.assign\(jobsFreshHomeHref\(\)\)/);
  });

  it("titles type-level jobs for the group, product-level jobs for a SKU", () => {
    expect(
      jobsHeading({
        productName: "Fourier GR-1",
        companyName: "Fourier Intelligence",
        robotCount: 5,
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("Jobs for humanoids");
    expect(
      jobsCountEyebrow({
        visibleCount: 5,
        productName: "Fourier GR-1",
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("5 JOBS FOR HUMANOIDS");
    expect(
      jobsHeading({
        productName: "Fourier GR-1",
        companyName: "Fourier Intelligence",
        robotCount: 5,
        lookupGrain: "product",
      }),
    ).toBe("Jobs for Fourier GR-1");
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
  });

  it("advances step 2 with Activate job list, not a Place buyer dump", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const workflow = readFileSync(join(here, "./jobsWorkflow.ts"), "utf8");
    const handoff = readFileSync(
      join(here, "../components/JobsHandoffBoard.tsx"),
      "utf8",
    );
    const pipeline = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    const results = readFileSync(join(here, "../pages/Results.tsx"), "utf8");
    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    for (const src of [workspace, workflow, handoff, pipeline, results]) {
      expect(src).not.toMatch(/Qualify this job/i);
      expect(src).not.toMatch(/that is the next step/i);
      expect(src).not.toMatch(/Request qualification/i);
      expect(src).not.toMatch(/Qualify a job on the Jobs terminal/i);
    }
    expect(workspace).not.toMatch(/function QualifyPanel/);
    expect(workspace).not.toMatch(/03 Qualify/);
    expect(workspace).not.toMatch(/function PlacePanel/);
    expect(workspace).not.toMatch(/03 Place/);
    expect(workspace).not.toMatch(/Open this buyer/i);
    expect(workspace).toMatch(/type="checkbox"/);
    expect(header).toMatch(/onJobsFreshHomeClick/);
    expect(header).toMatch(/jobsFreshHomeHref/);
    expect(jobsFreshHomeHref()).toBe("/?new=1");
    expect(FIND_JOBS_CTA).toBe("Find jobs →");
    expect(FIND_JOBS_CTA).not.toMatch(/qualify|buyer|lead/i);
    expect(JOBS_NEXT_CTA).toBe("Activate job list →");
    expect(JOBS_NEXT_CTA).not.toMatch(/qualify|buyer/i);
    expect(JOBS_NEXT_HINT).toMatch(/checked jobs/i);
    expect(JOBS_NEXT_HINT).not.toMatch(/buyer/i);
    expect(JOBS_PLACE_CTA).toBe("Activate job list →");
    expect(workspace).toMatch(/JOBS_NEXT_CTA/);
    expect(workspace).not.toMatch(/onNext=\{\(\) => onNext\(job\)\}/);
    expect(JOBS_FOR_YOUR_ROBOT_HEADING).toBe("Jobs for your robot");
    for (const step of JOBS_SCAN_STEPS) {
      expect(step).not.toMatch(/buyer|sales lead|qualify/i);
    }
  });

  it("activates the job list on pipeline without the OEM as a scan", () => {
    expect(jobsActivateHref(42)).toBe("/pipeline?src=jobs_activate&submission=42");
    expect(jobsActivateHref()).toBe("/pipeline?src=jobs_activate");
    expect(jobsActivateHref(42)).not.toContain("url=");
    expect(jobsPlaceHref({ leadId: 99, submissionId: 42 })).toBe(
      "/pipeline?src=jobs_activate&submission=42",
    );
    expect(isPlaceSrc("place")).toBe(true);
    expect(isJobsHandoffSrc("place")).toBe(false);
    expect(isJobsHandoffSrc("jobs_activate")).toBe(true);
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const pipeline = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    const handoff = readFileSync(
      join(here, "../components/JobsHandoffBoard.tsx"),
      "utf8",
    );
    expect(workspace).not.toMatch(/jobsPlaceHref\(robotUrl/);
    expect(workspace).not.toMatch(/PipelineOutreachValuePanel/);
    expect(pipeline).toMatch(/JobsHandoffBoard/);
    expect(pipeline).not.toMatch(/armJobsWorkspaceRestore\(\)/);
    expect(handoff).toMatch(/From your list/);
    expect(handoff).not.toMatch(/Taking you back/);
    expect(pipeline).toMatch(/arrivedFromPlace/);
    expect(pipeline).toMatch(/isPlaceSrc/);
  });

  it("looks up a lineup once per robot type, not once per SKU", () => {
    expect(normalizeRobotClass("Humanoid")).toBe("humanoid");
    expect(robotClassJobsLabel("humanoid")).toBe("humanoids");
    const fourier = lineupJobLookups([
      { name: "Fourier GR-1", displayClass: "humanoid" },
      { name: "Fourier GR-2", displayClass: "humanoid" },
      { name: "Fourier GR-3", displayClass: "humanoid" },
      { name: "Fourier N1", displayClass: "humanoid" },
    ]);
    expect(fourier).toEqual([
      {
        grain: "robot_type",
        robotClass: "humanoid",
        productNames: [
          "Fourier GR-1",
          "Fourier GR-2",
          "Fourier GR-3",
          "Fourier N1",
        ],
      },
    ]);
    const mixed = lineupJobLookups([
      { name: "Atlas", displayClass: "humanoid" },
      { name: "Spot", displayClass: "quadruped" },
      { name: "Stretch", displayClass: "mobile_manipulator" },
    ]);
    expect(mixed.map(row => row.robotClass).sort()).toEqual([
      "humanoid",
      "mobile_manipulator",
      "quadruped",
    ]);
    expect(mixed.every(row => row.grain === "robot_type")).toBe(true);
    expect(mixed.every(row => row.productNames.length === 1)).toBe(true);
    const unknown = lineupJobLookups([{ name: "MysteryBot", displayClass: null }]);
    expect(unknown).toEqual([
      { grain: "product", robotClass: null, productNames: ["MysteryBot"] },
    ]);
    expect(
      productClassesFromLineup([
        { name: "Fourier GR-1", displayClass: "humanoid" },
        { name: "Spot", displayClass: "quadruped" },
      ]),
    ).toEqual({ "Fourier GR-1": "humanoid", Spot: "quadruped" });
  });

  it("shares type-level jobs across a class and does not copy one SKU onto another type", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(workspace).not.toMatch(/\.\.\.base,\s*productName: name/);
    expect(workspace).not.toMatch(/fillLineupJobs/);
    expect(workspace).toMatch(/lineupJobLookups/);
    expect(workspace).toMatch(/lookupGrain: "robot_type"/);
    expect(workspace).toMatch(/Find jobs for all/);
    expect(workspace).not.toMatch(/List all \$\{products\.length\} robots/);
  });

  it("hides 0 matching jobs on unresearched lineup shells", () => {
    expect(
      portfolioShowsJobCounts([
        { matched: false, jobCount: 0 },
        { matched: false, jobCount: 0 },
      ]),
    ).toBe(false);
    expect(portfolioShowsJobCounts([{ matched: true, jobCount: 5 }])).toBe(true);
    expect(
      portfolioShowsJobCounts([
        { matched: true, jobCount: 5 },
        { matched: true, jobCount: 5 },
      ]),
    ).toBe(false);
    expect(
      portfolioShowsJobCounts([
        { matched: true, jobCount: 5 },
        { matched: true, jobCount: 12 },
      ]),
    ).toBe(true);
  });

  it("puts checked jobs first and fills the live list to 15", () => {
    const pool = Array.from({ length: 20 }, (_, i) => ({ job_key: `j${i}` }));
    const selected = [pool[2], pool[0]];
    const filled = jobsForActivatedPipeline(selected, pool, 15);
    expect(filled).toHaveLength(15);
    expect(filled.map(j => j.job_key).slice(0, 2)).toEqual(["j2", "j0"]);
    expect(filled.map(j => j.job_key)).not.toContain("j15");
    expect(defaultCheckedJobKeys(pool)).toEqual(["j0", "j1", "j2", "j3", "j4"]);
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

  it("keeps industry-matched Place buyers when at least two rows hit", () => {
    const rows = [
      { id: 1, industry: "Manufacturing" },
      { id: 2, industry: "Manufacturing / CNC" },
      { id: 3, industry: "Hospitality" },
    ];
    expect(placeBuyersToShow(rows, "Manufacturing").map(r => r.id)).toEqual([1, 2]);
    expect(placeBuyersToShow(rows, "Warehousing").map(r => r.id)).toEqual([1, 2, 3]);
    expect(placeBuyersToShow(rows, "Manufacturing", 1).map(r => r.id)).toEqual([1]);
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
