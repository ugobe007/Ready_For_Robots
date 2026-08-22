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
  JOBS_PROCESS_STEPS,
  JOBS_SCAN_STEPS,
  JOBS_SEE_JOBS_CTA,
  JOBS_EYEBROW_CLASS,
  JOBS_JOB_TITLE_CLASS,
  JOBS_META_CLASS,
  JOBS_ROBOT_NAME_CLASS,
  CRM_HEADLINE_CLASS,
  CRM_HOW_TO_STEPS,
  CRM_PAGE_HEADLINE,
  CRM_PAGE_NEXT,
  CRM_WATCH_FREE_HINT,
  CRM_WATCH_OPT_IN_LABEL,
  PIPELINE_PAGE_HEADLINE,
  PIPELINE_PAGE_NEXT,
  buyerLeadsHref,
  buyerLeadsToShow,
  capExampleJobs,
  defaultCheckedJobKeys,
  defaultCheckedKeysForLineup,
  exampleJobCap,
  exampleJobsForLineup,
  isJobsHandoffSrc,
  isPlaceSrc,
  jobsActivateHref,
  jobsCountEyebrow,
  jobsForActivatedPipeline,
  jobsFreshHomeHref,
  goJobsFreshHome,
  jobsHeading,
  jobIndexLabel,
  jobIsForLabel,
  jobExplanation,
  jobsListHint,
  jobsPlaceHref,
  jobsProcessActionLabel,
  jobsProcessStepFromStage,
  jobsToActivate,
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
  it("sends one, several, or all selected robots to jobs — not a second Find jobs click", () => {
    expect(landingStageAfterConfirm(1)).toBe("jobs");
    expect(landingStageAfterConfirm(2)).toBe("jobs");
    expect(landingStageAfterConfirm(4)).toBe("jobs");
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const confirm = workspace.slice(
      workspace.indexOf("async function confirmSelection"),
      workspace.indexOf("function enterReview"),
    );
    const oneSku = confirm.slice(
      confirm.indexOf("if (names.length === 1)"),
      confirm.indexOf("Several / all"),
    );
    expect(oneSku).toMatch(/openJobsFromAnalyses/);
    expect(oneSku).toMatch(/fetchRobotJobSearch/);
    expect(oneSku).toMatch(/lookupGrain: cls \? "robot_type" : "product"/);
    expect(oneSku).not.toMatch(/enterReview/);
    expect(oneSku).not.toMatch(/fetchRobotProfile/);
    const submitFind = workspace.slice(
      workspace.indexOf("async function submitFind"),
      workspace.indexOf("async function confirmSelection"),
    );
    expect(submitFind).toMatch(/openJobsFromAnalyses/);
    expect(submitFind).not.toMatch(/enterReview/);
    expect(workspace).toMatch(/rfr-jobs-activate-bar/);
    expect(workspace).not.toMatch(
      /enterReview\(profileToAnalysis\(profile\), submitUrl, names\)/,
    );
  });

  it("always names the three process steps as navigational links", () => {
    expect(JOBS_PROCESS_STEPS.map(s => s.id)).toEqual(["find", "jobs", "activate"]);
    expect(JOBS_SEE_JOBS_CTA).toBe("See jobs →");
    expect(jobsProcessStepFromStage("select")).toBe("find");
    expect(jobsProcessStepFromStage("review")).toBe("find");
    expect(jobsProcessStepFromStage("jobs")).toBe("jobs");
    expect(jobsProcessStepFromStage("portfolio")).toBe("jobs");
    expect(jobsProcessActionLabel("find")).toBe(FIND_JOBS_CTA);
    expect(jobsProcessActionLabel("jobs")).toBe(JOBS_NEXT_CTA);
    expect(jobsProcessActionLabel("activate")).toBe(JOBS_NEXT_CTA);
    const pool = [{ job_key: "a" }, { job_key: "b" }, { job_key: "c" }];
    expect(jobsToActivate([], pool, 15).map(j => j.job_key)).toEqual(["a", "b", "c"]);
    expect(jobsToActivate([pool[2]], pool, 15).map(j => j.job_key)).toEqual([
      "c",
      "a",
      "b",
    ]);
    expect(jobsToActivate([], [], 15)).toEqual([]);
  });

  it("is a scrolling process page, not a clipped two-pane box", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(workspace).not.toMatch(/h-\[calc\(100vh/);
    expect(workspace).toMatch(/rfr-jobs-page-shell/);
    expect(workspace).toMatch(/rfr-jobs-process-bar/);
    expect(workspace).toMatch(/rfr-jobs-page-footer/);
    expect(workspace).toMatch(/layout="page"/);
    expect(workspace).toMatch(/rfr-jobs-process-action/);
    expect(jobsPage).toMatch(/jobs-page min-h-screen/);
    expect(jobsPage).not.toMatch(/overflow-hidden/);
    expect(jobsPage).not.toMatch(/fresh-find/);
    expect(workspace).not.toMatch(
      /min-h-0 flex-1 overflow-y-auto p-6 sm:p-8/,
    );
  });

  it("gives the home live tape its own height so 12 jobs show without a 100vh parent", () => {
    const tape = readFileSync(
      join(here, "../components/jobs/LiveJobTape.tsx"),
      "utf8",
    );
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(tape).toMatch(/export const TAPE_VIEWPORT_PX = VISIBLE \* ROW_PX/);
    expect(tape).toMatch(/height: TAPE_VIEWPORT_PX/);
    expect(tape).toMatch(/\$\{revealing\}:\$\{baseCount\}:\$\{corpus\.length\}/);
    expect(tape).toMatch(/if \(seededKey\.current === key\) return;/);
    expect(tape).not.toMatch(/flex h-full min-h-0 flex-col/);
    expect(tape).not.toMatch(/min-h-0 flex-1 overflow-hidden/);
    expect(workspace).toMatch(/<LiveJobTape/);
    expect(workspace).not.toMatch(/min-h-\[28rem\]/);
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
    expect(workflow).toMatch(/location\.assign\("\/"\)/);
  });

  it("titles type-level jobs for the company group, product-level jobs for a SKU", () => {
    expect(
      jobsHeading({
        productName: "Fourier GR-1",
        companyName: "Fourier Intelligence",
        robotCount: 5,
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("Jobs for Fourier Intelligence");
    expect(
      jobsCountEyebrow({
        visibleCount: 5,
        productName: "Fourier GR-1",
        companyName: "Fourier Intelligence",
        robotCount: 5,
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("5 ROBOTS · 1 JOB EACH");
    expect(
      jobsHeading({
        productName: "Fourier GR-1",
        companyName: "Fourier Intelligence",
        robotCount: 1,
        lookupGrain: "product",
      }),
    ).toBe("Jobs for Fourier GR-1");
    expect(
      jobsHeading({
        productName: "Fourier N1",
        companyName: "Fourier Intelligence",
        robotCount: 1,
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("Jobs for Fourier N1");
    expect(
      jobsCountEyebrow({
        visibleCount: 5,
        productName: "Fourier N1",
        companyName: "Fourier Intelligence",
        robotCount: 1,
        lookupGrain: "robot_type",
        robotClass: "humanoid",
      }),
    ).toBe("5 JOBS FOR FOURIER N1");
  });

  it("caps the Jobs terminal at 5 example jobs even when more exist", () => {
    expect(JOBS_EXAMPLE_CAP).toBe(5);
    expect(exampleJobCap(1)).toBe(5);
    expect(exampleJobCap(5)).toBe(1);
    expect(capExampleJobs([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])).toEqual([
      1, 2, 3, 4, 5,
    ]);
    expect(capExampleJobs(["a", "b"])).toEqual(["a", "b"]);
  });

  it("tags each job with its robot: five for one SKU, one each for a lineup", () => {
    expect(jobIsForLabel(1, "Fourier N1")).toBe("Job 00001 is for Fourier N1");
    expect(jobIsForLabel(887, "GR-1")).toBe("Job 00887 is for GR-1");
    const n1Jobs = [
      { job_key: "a", title: "A" },
      { job_key: "b", title: "B" },
      { job_key: "c", title: "C" },
      { job_key: "d", title: "D" },
      { job_key: "e", title: "E" },
      { job_key: "f", title: "F" },
    ];
    const one = exampleJobsForLineup([{ productName: "Fourier N1", jobs: n1Jobs }]);
    expect(one).toHaveLength(5);
    expect(one.every(j => j.forRobot === "Fourier N1")).toBe(true);
    expect(one.map(j => j.job_key)).toEqual(["a", "b", "c", "d", "e"]);
    const shared = [
      { job_key: "a", title: "A" },
      { job_key: "b", title: "B" },
      { job_key: "c", title: "C" },
    ];
    const lineup = exampleJobsForLineup([
      { productName: "Fourier GR-1", jobs: shared },
      { productName: "Fourier N1", jobs: shared },
      { productName: "Fourier GR-3", jobs: shared },
    ]);
    expect(lineup.map(j => j.forRobot)).toEqual([
      "Fourier GR-1",
      "Fourier N1",
      "Fourier GR-3",
    ]);
    expect(lineup.map(j => j.job_key)).toEqual(["a", "b", "c"]);
    expect(defaultCheckedKeysForLineup([
      { productName: "Fourier N1", jobs: n1Jobs },
    ])).toEqual(["a", "b", "c", "d", "e"]);
    expect(jobsListHint({ robotCount: 1, productName: "Fourier N1" })).toMatch(
      /Five example jobs Fourier N1/,
    );
    expect(jobsListHint({ robotCount: 5, productName: "Fourier N1" })).toMatch(
      /one sample job per robot/i,
    );
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const handoff = readFileSync(
      join(here, "../components/JobsHandoffBoard.tsx"),
      "utf8",
    );
    expect(workspace).toMatch(/jobIsForLabel/);
    expect(workspace).toMatch(/JOBS_RUN_ONE_ROBOT_CTA/);
    expect(workspace).toMatch(/lineupPreview/);
    expect(handoff).toMatch(/JOBS_SAVE_TO_CRM_CTA/);
    expect(handoff).toMatch(/jobIsForLabel/);
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
    expect(FIND_JOBS_CTA).toBe("Start jobs →");
    expect(FIND_JOBS_CTA).not.toMatch(/qualify|buyer|lead/i);
    expect(JOBS_NEXT_CTA).toBe("Next →");
    expect(JOBS_NEXT_CTA).not.toMatch(/qualify|buyer/i);
    expect(JOBS_NEXT_HINT).toMatch(/checked jobs/i);
    expect(JOBS_NEXT_HINT).not.toMatch(/buyer/i);
    expect(JOBS_PLACE_CTA).toBe("Activate job list →");
    expect(workspace).toMatch(/JOBS_NEXT_CTA/);
    expect(workspace).toMatch(/JobsProcessNav/);
    expect(workspace).toMatch(/JOBS_PROCESS_STEPS/);
    expect(workspace).toMatch(/rfr-jobs-start-bar/);
    expect(workspace).toMatch(/rfr-jobs-process-action/);
    expect(workspace).toMatch(/function JobsActivateBar/);
    expect(workspace).toMatch(/function startJobs/);
    expect(workspace).toMatch(/Start jobs for all/);
    expect(workspace).toMatch(/const researching = stage === "research"/);
    expect(workspace).not.toMatch(/03 Live list/);
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
    expect(workspace).toMatch(/Start jobs for all/);
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

  it("makes Jobs type readable and uses Jobs chrome on Pipeline and CRM", () => {
    expect(jobIndexLabel(1)).toBe("Job 00001");
    expect(JOBS_ROBOT_NAME_CLASS).toMatch(/text-xl/);
    expect(JOBS_JOB_TITLE_CLASS).toMatch(/text-lg/);
    expect(JOBS_META_CLASS).toMatch(/text-sm/);
    expect(JOBS_EYEBROW_CLASS).toMatch(/text-sm/);
    expect(CRM_PAGE_HEADLINE).toBe("CRM");
    expect(PIPELINE_PAGE_HEADLINE).toBe("Pipeline");
    expect(CRM_PAGE_NEXT).toMatch(/this is your CRM/i);
    expect(PIPELINE_PAGE_NEXT).toMatch(/live list/i);
    expect(CRM_HEADLINE_CLASS).toMatch(/text-emerald-400/);
    expect(CRM_HOW_TO_STEPS).toHaveLength(3);
    expect(CRM_WATCH_OPT_IN_LABEL).toMatch(/email me when these jobs change/i);
    expect(CRM_WATCH_FREE_HINT).toMatch(/free watches 1 robot/i);

    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const card = workspace.slice(workspace.indexOf("function JobCard"));
    expect(card).toMatch(/JOBS_ROBOT_NAME_CLASS/);
    expect(card).toMatch(/JOBS_JOB_TITLE_CLASS/);
    expect(card).toMatch(/jobIsForLabel/);
    expect(card).not.toMatch(/text-\[10px\]/);

    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    expect(header).toMatch(/href="\/crm"/);
    expect(header).toMatch(/h-14/);
    expect(header).toMatch(/sm:text-base/);

    const pipeline = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    expect(pipeline).toMatch(/<ExperimentHeader/);
    expect(pipeline).toMatch(/PIPELINE_PAGE_HEADLINE/);
    expect(pipeline).not.toMatch(/from "@\/components\/Header"/);
    expect(pipeline).not.toMatch(/SIGNAL · Sales intelligence/);

    const crm = readFileSync(join(here, "../pages/Crm.tsx"), "utf8");
    expect(crm).toMatch(/ExperimentHeader/);
    expect(crm).toMatch(/CrmHero/);
    expect(crm).toMatch(/\/api\/crm\/jobs-watch/);
    expect(crm).not.toMatch(/admin-workspace/);
    expect(crm).not.toMatch(/from "@\/components\/Header"/);
    expect(crm).not.toMatch(/Outreach editor/);

    const hero = readFileSync(join(here, "../components/crm/CrmHero.tsx"), "utf8");
    expect(hero).toMatch(/KARE_FACE/);
    expect(hero).toMatch(/FACE_EMERALD/);
    expect(hero).toMatch(/CRM_HEADLINE_CLASS/);
    expect(hero).toMatch(/CRM_WATCH_OPT_IN_LABEL/);
    expect(hero).toMatch(/CRM_HOW_TO_STEPS/);

    const intel = readFileSync(join(here, "../pages/Intelligence.tsx"), "utf8");
    expect(intel).toMatch(/ExperimentHeader/);
    expect(intel).toMatch(/KARE_FACE/);
    expect(intel).not.toMatch(/from "@\/components\/Header"/);

    const pipelineSrc = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    expect(pipelineSrc).toMatch(/JOBS_PIPELINE_CAP/);
    expect(pipelineSrc).not.toMatch(/Find buyers by industry/);
    expect(pipelineSrc).not.toMatch(/Customer opportunities/);

    const cardSrc = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(cardSrc).toMatch(/jobExplanation/);
    expect(cardSrc).toMatch(/The job/);
  });

  it("explains the job instead of a sales pitch", () => {
    expect(
      jobExplanation({
        action: "Priority: Pitch AMR fleet for new distribution centers",
        friction: "Move pallets from receiving to reserve overnight",
        company: "Acme Logistics",
      }),
    ).toBe("Move pallets from receiving to reserve overnight");
    expect(
      jobExplanation({
        title: "Tray return",
        why: ["Carry dirty trays from dining room to the dish pit all shift"],
        company: "Panera Bread",
      }),
    ).toMatch(/dish pit/i);
    expect(
      jobExplanation({
        action: "Priority: Pitch overnight cleaning robots",
      }),
    ).not.toMatch(/pitch/i);
  });
});
