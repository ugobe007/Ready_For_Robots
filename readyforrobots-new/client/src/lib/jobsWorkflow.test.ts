import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  FIND_JOBS_CTA,
  FIND_JOBS_HEADLINE_CLASS,
  FIND_JOBS_HOME_SUBHEAD,
  FIND_JOBS_SUBHEAD_CLASS,
  JOBS_EXAMPLE_CAP,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_NEXT_CTA,
  JOBS_NEXT_HINT,
  JOBS_PLACE_CTA,
  JOBS_PROCESS_STEPS,
  JOBS_PRODUCT_CAP_FREE,
  JOBS_PRODUCT_CAP_PAID,
  JOBS_LINEUP_DISPLAY_CAP,
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
  CRM_SUBHEAD_CLASS,
  CRM_WATCH_FREE_HINT,
  CRM_WATCH_OPT_IN_LABEL,
  CRM_UNLOCKED_JOBS,
  CRM_FREE_BATCH,
  CRM_FREE_BATCHES_PER_MONTH,
  CRM_FREE_MONTHLY_CAP,
  CRM_FREE_TTL_DAYS,
  PIPELINE_PAGE_HEADLINE,
  PIPELINE_PAGE_NEXT,
  buyerLeadsHref,
  buyerLeadsToShow,
  capExampleJobs,
  defaultCheckedJobKeys,
  defaultCheckedKeysForLineup,
  exampleJobCap,
  exampleJobsForLineup,
  filterJobsLineupProducts,
  pageJobsLineup,
  isJobsHandoffSrc,
  isJobsChromePath,
  isJobsAutomateSrc,
  isPlaceSrc,
  jobsActivateHref,
  jobsAutomateHref,
  jobsHeaderCrmHref,
  jobsCountEyebrow,
  jobsForActivatedPipeline,
  jobsFreshHomeHref,
  goJobsFreshHome,
  JOBS_FRESH_HOME_EVENT,
  canStartFindSubmit,
  findSubmitNavigationTarget,
  isJobsHomePath,
  stripJobsFreshQuery,
  jobsHeading,
  jobIndexLabel,
  jobIsForLabel,
  jobExplanation,
  isSalesPlaceholder,
  jobsListHint,
  jobsPlaceHref,
  jobsProcessActionLabel,
  jobsProcessStepFromStage,
  jobsProductLimitForPlan,
  jobsToActivate,
  jobsDumpedToCrm,
  jobsForCrmDesk,
  crmDeskJobKeys,
  crmSelectAllKeys,
  crmToggleSelectedKey,
  crmSyncSelectedKeys,
  crmActingKeepsSelection,
  crmCollectedCountLabel,
  crmSelectAllLabel,
  CRM_EMPLOYER_NAME_CLASS,
  CRM_SELECT_ALL_LABEL,
  CRM_LISTING_EYEBROW,
  CRM_INSPECT_HINT,
  CRM_PLACE_EGG_HINT,
  jobsSignupHref,
  jobsCrmOpenHref,
  jobsWorkspaceRestoreHref,
  landingStageAfterConfirm,
  lineupJobLookups,
  lineupSegments,
  usesLineupSegments,
  searchNamesForSegment,
  skuFamilyStem,
  normalizeRobotClass,
  portfolioShowsJobCounts,
  productClassesFromLineup,
  robotClassJobsLabel,
  isJobsHomeDest,
  persistJobsHandoffSrc,
  placeBuyersToShow,
  shouldRestoreJobsWorkspace,
  showSignalPipelineNav,
  showJobsSiteChrome,
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
    expect(workspace).toMatch(/rfr-bevel/);
    expect(workspace).toMatch(/rfr-led/);
    expect(workspace).not.toMatch(/rounded-full/);
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
    expect(tape).toMatch(/\$\{revealing\}:\$\{corpus\.length\}/);
    expect(tape).toMatch(/if \(seededKey\.current === key\) return;/);
    expect(tape).not.toMatch(/flex h-full min-h-0 flex-col/);
    expect(tape).not.toMatch(/min-h-0 flex-1 overflow-hidden/);
    expect(tape).toMatch(/nextUnseenTapeJob/);
    expect(workspace).toMatch(/<LiveJobTape/);
    expect(workspace).toMatch(/uniqueTapeJobCount/);
    expect(workspace).not.toMatch(/const MARKET_FOUND_BASE = 140/);
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
    expect(workflow).toMatch(/isJobsHomePath\(path\)/);
    expect(workflow).toMatch(/dispatchEvent\(new Event\(JOBS_FRESH_HOME_EVENT\)\)/);
  });

  it("FIND submit does not remount the workspace or require SIGNAL CRM shell", () => {
    expect(findSubmitNavigationTarget("https://www.dexmate.ai/")).toBeNull();
    expect(
      canStartFindSubmit({
        url: "https://www.dexmate.ai/",
        inFlight: false,
        stage: "find",
      }),
    ).toBe(true);
    expect(
      canStartFindSubmit({
        url: "https://www.dexmate.ai/",
        inFlight: true,
        stage: "find",
      }),
    ).toBe(false);
    expect(
      canStartFindSubmit({
        url: "https://www.dexmate.ai/",
        inFlight: false,
        stage: "research",
      }),
    ).toBe(false);
    expect(canStartFindSubmit({ url: "   ", inFlight: false, stage: "find" })).toBe(
      false,
    );
    expect(isJobsHomePath("/")).toBe(true);
    expect(isJobsHomePath("/jobs/dexmate")).toBe(true);
    expect(isJobsHomePath("/intelligence")).toBe(false);

    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(workspace).not.toMatch(/pipeline-detail-shell/);
    expect(workspace).not.toMatch(/diagnoseCRM/);
    expect(workspace).not.toMatch(/RFR DIAG/);
    expect(workspace).not.toMatch(/setLocation\("\/", \{ replace: true \}\)/);
    expect(workspace).toMatch(/canStartFindSubmit/);
    expect(workspace).toMatch(/JOBS_FRESH_HOME_EVENT/);
    expect(workspace).toMatch(/aria-label="Find jobs for your robot"/);
    const startJobs = workspace.slice(
      workspace.indexOf("function startJobs"),
      workspace.indexOf("function toggleProduct"),
    );
    expect(startJobs).not.toMatch(/location\.assign/);
    expect(startJobs).not.toMatch(/location\.reload/);
    expect(startJobs).not.toMatch(/setLocation/);
    const submitFind = workspace.slice(
      workspace.indexOf("async function submitFind"),
      workspace.indexOf("async function confirmSelection"),
    );
    expect(submitFind).not.toMatch(/location\.assign/);
    expect(submitFind).not.toMatch(/location\.reload/);
    expect(submitFind).not.toMatch(/setLocation/);
    expect(submitFind).not.toMatch(/pipeline-detail-shell/);
  });

  it("strips ?new=1 and resets Jobs home without a document reload", () => {
    const assigns: string[] = [];
    const replaced: string[] = [];
    const events: string[] = [];
    const loc = { pathname: "/", search: "?new=1", hash: "" };
    const fakeWindow = {
      location: {
        get pathname() {
          return loc.pathname;
        },
        get search() {
          return loc.search;
        },
        get hash() {
          return loc.hash;
        },
        assign: (url: string) => {
          assigns.push(url);
        },
      },
      history: {
        state: null,
        replaceState: (_state: unknown, _title: string, url: string) => {
          replaced.push(String(url));
          const qIndex = String(url).indexOf("?");
          loc.search = qIndex >= 0 ? String(url).slice(qIndex) : "";
        },
      },
      sessionStorage: {
        removeItem: () => undefined,
      },
      dispatchEvent: (event: Event) => {
        events.push(event.type);
        return true;
      },
    };
    Object.defineProperty(globalThis, "window", {
      value: fakeWindow,
      configurable: true,
    });
    expect(stripJobsFreshQuery()).toBe(true);
    expect(replaced).toEqual(["/"]);
    expect(stripJobsFreshQuery()).toBe(false);
    goJobsFreshHome();
    expect(assigns).toEqual([]);
    expect(events).toEqual([JOBS_FRESH_HOME_EVENT]);
    loc.pathname = "/intelligence";
    loc.search = "";
    goJobsFreshHome();
    expect(assigns).toEqual(["/"]);
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
    expect(jobsListHint({ robotCount: 1, productName: "Fourier N1" })).toMatch(
      /All five start checked/i,
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
    expect(workspace).toMatch(/jobIndexLabel/);
    expect(workspace).not.toMatch(/jobIsForLabel/);
    expect(workspace).toMatch(/JOBS_RUN_ONE_ROBOT_CTA/);
    expect(workspace).toMatch(/lineupPreview/);
    expect(handoff).toMatch(/Opening CRM/);
    expect(handoff).not.toMatch(/function JobRow/);
    expect(handoff).not.toMatch(/jobIsForLabel/);
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
    expect(showSignalPipelineNav({ pathname: "/" })).toBe(false);
    expect(showSignalPipelineNav({ pathname: "/jobs" })).toBe(false);
    expect(showSignalPipelineNav({ pathname: "/crm", src: "jobs_activate" })).toBe(false);
    expect(showSignalPipelineNav({ pathname: "/pipeline" })).toBe(true);
    expect(showSignalPipelineNav({ pathname: "/crm" })).toBe(true);
    expect(isJobsChromePath("/")).toBe(true);
    expect(jobsHeaderCrmHref("/")).toBe("/pipeline?src=jobs_activate");
    expect(jobsHeaderCrmHref("/", null, false)).toBe(
      jobsSignupHref("/pipeline?src=jobs_activate", "jobs_activate"),
    );
    expect(jobsHeaderCrmHref("/crm")).toBe("/crm");
    expect(jobsHeaderCrmHref("/crm", "jobs_activate")).toBe(
      "/pipeline?src=jobs_activate",
    );
    expect(jobsHeaderCrmHref("/pipeline")).toBe("/crm");
    expect(jobsHeaderCrmHref("/pipeline", "jobs_activate")).toBe(
      "/pipeline?src=jobs_activate",
    );
    expect(showSignalPipelineNav({ pathname: "/pipeline", src: "jobs_activate" })).toBe(
      false,
    );
    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    expect(header).toMatch(/showSignalPipelineNav/);
    expect(header).toMatch(/jobsHeaderCrmHref\(location, jobsSrc, Boolean\(session\)\)/);
    expect(header).toMatch(/showPipeline/);
    expect(header).toMatch(/useSearch/);
  });

  it("Jobs footer and Signal FAB follow header chrome (no Pipeline / SIGNAL)", () => {
    expect(showJobsSiteChrome({ pathname: "/" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/jobs" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/jobs/acme" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/intelligence" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/compare" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/vendor/design" })).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/design/abc" })).toBe(true);
    expect(
      showJobsSiteChrome({ pathname: "/crm", search: "src=jobs_activate" }),
    ).toBe(true);
    expect(
      showJobsSiteChrome({ pathname: "/signup", search: "src=jobs_activate" }),
    ).toBe(true);
    expect(
      showJobsSiteChrome({
        pathname: "/signup",
        search: "next=%2Fcrm%3Fsrc%3Djobs_activate&src=jobs_activate",
      }),
    ).toBe(true);
    expect(
      showJobsSiteChrome({
        pathname: "/signup",
        search: "next=%2Fcrm%3Fsrc%3Djobs_activate",
      }),
    ).toBe(true);
    expect(showJobsSiteChrome({ pathname: "/login", search: "next=%2F" })).toBe(
      true,
    );
    expect(
      showJobsSiteChrome({ pathname: "/signup", search: "next=%2F%3Frestore%3D1" }),
    ).toBe(true);

    expect(showJobsSiteChrome({ pathname: "/pipeline" })).toBe(false);
    expect(showJobsSiteChrome({ pathname: "/crm" })).toBe(false);
    expect(showJobsSiteChrome({ pathname: "/signals" })).toBe(false);
    expect(
      showJobsSiteChrome({ pathname: "/signup", search: "next=%2Fpipeline" }),
    ).toBe(false);
    expect(showJobsSiteChrome({ pathname: "/signup" })).toBe(false);

    const footer = readFileSync(
      join(here, "../components/layout/SiteFooter.tsx"),
      "utf8",
    );
    expect(footer).toMatch(/showJobsSiteChrome/);
    expect(footer).toMatch(/function jobsProductLinks/);
    expect(footer).toMatch(/const SIGNAL_LINKS/);
    expect(footer).toMatch(/jobsChrome \? jobsProductLinks\(Boolean\(session\)\) : SIGNAL_LINKS/);
    expect(footer).toMatch(/jobsChrome \? "JOBS" : "SIGNAL"/);
    const jobsLinks = footer.slice(
      footer.indexOf("function jobsProductLinks"),
      footer.indexOf("const SIGNAL_LINKS"),
    );
    expect(jobsLinks).toMatch(/jobsFreshHomeHref/);
    expect(jobsLinks).toMatch(/jobsCrmOpenHref/);
    expect(jobsLinks).not.toMatch(/\/pipeline/);
    expect(jobsLinks).not.toMatch(/Signals/);
    expect(footer).not.toMatch(/rounded-lg/);
    expect(footer).not.toMatch(/\/#case-studies/);

    const compare = readFileSync(join(here, "../pages/Compare.tsx"), "utf8");
    expect(compare).toMatch(/jobs for your robot/i);
    expect(compare).toMatch(/ExperimentHeader/);
    expect(compare).not.toMatch(/Full Stack Sales/);
    expect(compare).not.toMatch(/CRM 4.0/);
    const design = readFileSync(
      join(here, "../pages/VendorDesignBuilder.tsx"),
      "utf8",
    );
    expect(design).toMatch(/What this page does/);
    expect(design).toMatch(/ExperimentHeader/);
    expect(design).not.toMatch(/Supply pipeline/);
    const share = readFileSync(join(here, "../pages/DesignShare.tsx"), "utf8");
    expect(share).toMatch(/Job site sketch/);
    expect(share).toMatch(/ExperimentHeader/);
    expect(share).not.toMatch(/Explore live buyer signals/);
    expect(share).not.toMatch(/\/pipeline/);

    const scout = readFileSync(join(here, "../components/ScoutChat.tsx"), "utf8");
    expect(scout).toMatch(/showJobsSiteChrome/);
    expect(scout).toMatch(/useSearch/);
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
    expect(FIND_JOBS_HOME_SUBHEAD).toBe(
      "We match your robots to specific jobs and models using your URL",
    );
    expect(FIND_JOBS_HOME_SUBHEAD).not.toMatch(/manufacturer URL|SKU we can prove/i);
    expect(FIND_JOBS_HEADLINE_CLASS).toMatch(/text-5xl/);
    expect(FIND_JOBS_HEADLINE_CLASS).toMatch(/sm:text-6xl/);
    expect(FIND_JOBS_HEADLINE_CLASS).toMatch(/lg:text-7xl/);
    expect(FIND_JOBS_SUBHEAD_CLASS).toMatch(/text-lg/);
    expect(workspace).toMatch(/FIND_JOBS_HEADLINE_CLASS/);
    expect(workspace).toMatch(/FIND_JOBS_HOME_SUBHEAD/);
    expect(workspace).toMatch(/text-emerald-400">jobs/);
    expect(workspace).not.toMatch(/Paste the manufacturer URL/);
    expect(JOBS_NEXT_CTA).toBe("Open CRM →");
    expect(JOBS_NEXT_CTA).not.toMatch(/qualify|buyer/i);
    expect(JOBS_NEXT_HINT).toMatch(/start checked/i);
    expect(JOBS_NEXT_HINT).toMatch(/dump into CRM/i);
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

  it("opens the CRM desk on Pipeline with 5 jobs, not a SIGNAL save page", () => {
    expect(CRM_UNLOCKED_JOBS).toBe(5);
    expect(jobsActivateHref(42)).toBe("/pipeline?src=jobs_activate&submission=42");
    expect(jobsActivateHref()).toBe("/pipeline?src=jobs_activate");
    expect(jobsActivateHref(42)).not.toContain("url=");
    expect(jobsActivateHref()).toContain("/pipeline?src=jobs_activate");
    expect(jobsAutomateHref(12)).toBe("/pipeline?src=jobs_automate&submission=12");
    expect(jobsAutomateHref()).toBe("/pipeline?src=jobs_automate");
    expect(isJobsAutomateSrc("jobs_automate")).toBe(true);
    expect(isJobsHandoffSrc("jobs_automate")).toBe(true);
    expect(jobsPlaceHref({ leadId: 99, submissionId: 42 })).toBe(
      "/pipeline?src=jobs_activate&submission=42",
    );
    expect(isPlaceSrc("place")).toBe(true);
    expect(isJobsHandoffSrc("place")).toBe(false);
    expect(isJobsHandoffSrc("jobs_activate")).toBe(true);
    expect(isJobsHandoffSrc("jobs_all_robots")).toBe(true);
    const pool = [
      { job_key: "a" },
      { job_key: "b" },
      { job_key: "c" },
      { job_key: "d" },
      { job_key: "e" },
    ];
    expect(jobsToActivate(pool, pool, CRM_UNLOCKED_JOBS).map(j => j.job_key)).toEqual([
      "a",
      "b",
      "c",
      "d",
      "e",
    ]);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const pipeline = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    const desk = readFileSync(
      join(here, "../components/JobsCrmDesk.tsx"),
      "utf8",
    );
    const handoff = readFileSync(
      join(here, "../components/JobsHandoffBoard.tsx"),
      "utf8",
    );
    const crm = readFileSync(join(here, "../pages/Crm.tsx"), "utf8");
    expect(workspace).not.toMatch(/jobsPlaceHref\(robotUrl/);
    expect(workspace).not.toMatch(/PipelineOutreachValuePanel/);
    expect(workspace).toMatch(/CRM_UNLOCKED_JOBS/);
    expect(workspace).toMatch(/writeCrmHandoff/);
    expect(workspace).toMatch(/jobsForCrmDesk/);
    expect(workspace).toMatch(/jobsCrmOpenHref/);
    expect(workspace).toMatch(/recordPipelineActivity/);
    expect(workspace).toMatch(/JOBS_KEEP_LABEL/);
    expect(pipeline).toMatch(/JobsCrmDesk/);
    expect(pipeline).toMatch(/if \(arrivedFromJobs\)/);
    expect(pipeline).not.toMatch(/JobsHandoffBoard/);
    expect(pipeline).toMatch(/JOBS_AUTOMATE_JOBS_CTA/);
    expect(pipeline).toMatch(/PIPELINE_JOBS_AUTOMATE_STEPS/);
    expect(pipeline).toMatch(/jobsAutomate=\{arrivedFromJobsAutomate\}/);
    expect(pipeline).not.toMatch(/armJobsWorkspaceRestore\(\)/);
    expect(desk).toMatch(/JOBS_APPLY_CTA/);
    expect(desk).toMatch(/jobCredentialGaps/);
    expect(desk).toMatch(/placementOutreachDraft/);
    expect(desk).toMatch(/placementAgentBrief/);
    expect(desk).toMatch(/aria-label="Jobs process"/);
    expect(desk).toMatch(/Step 03 · CRM/);
    expect(desk).toMatch(/Collect jobs for \{product\}/);
    expect(desk).toMatch(/crmCollectedCountLabel/);
    expect(desk).toMatch(/crmSelectAllKeys/);
    expect(desk).toMatch(/Keep all collected jobs/);
    expect(desk).toMatch(/aria-label="Collected jobs"/);
    expect(desk).toMatch(/CRM_EMPLOYER_NAME_CLASS/);
    expect(desk).toMatch(/\{card\.jobTitle\}/);
    expect(desk).toMatch(/\{card\.employer\}/);
    expect(desk).toMatch(/Inspecting this egg/);
    expect(desk).toMatch(/JOBS_POC_SKIP_CTA/);
    expect(desk).toMatch(/JOBS_POC_PREFER_HINT/);
    expect(desk).toMatch(/Your move:/);
    expect(desk).toMatch(/lockQuoteUpdate/);
    expect(desk).toMatch(/PoC evidence \(optional\)/);
    expect(desk).toMatch(/pocSkipped: true/);
    expect(desk).not.toMatch(/grid-cols-3/);
    expect(desk).not.toMatch(/vendor_shortlist/);
    expect(desk).not.toMatch(/7-day|7 days|15.month|CRM_FREE_TTL/);
    expect(desk).not.toMatch(/badge|points|leaderboard/i);
    expect(desk).toMatch(/Not a SIGNAL buyer list/);
    expect(desk).toMatch(/jobsCrmOpenHref\(false/);
    expect(desk).toMatch(/Opening CRM/);
    expect(desk).toMatch(/Pipeline activity/);
    expect(desk).toMatch(/recordPipelineActivity/);
    expect(desk).toMatch(/setExpandedKey/);
    expect(desk).toMatch(/crmToggleSelectedKey/);
    expect(desk).not.toMatch(/setActiveKey/);
    expect(handoff).toMatch(/Opening CRM/);
    expect(handoff).toMatch(/jobsCrmOpenHref/);
    expect(handoff).toMatch(/isJobsAutomateSrc/);
    expect(handoff).not.toMatch(/Save this job list to CRM/i);
    expect(handoff).not.toMatch(/5 checked/);
    expect(handoff).not.toMatch(/function JobRow/);
    expect(crm).toMatch(/Opening CRM desk/);
    expect(crm).toMatch(/jobsActivateHref/);
    expect(crm).toMatch(/CRM_UNLOCKED_JOBS/);
    expect(crm).toMatch(/setLocation\(jobsDeskHref\)/);
    const signup = readFileSync(join(here, "../pages/Signup.tsx"), "utf8");
    expect(signup).toMatch(/5 job opportunities in CRM/);
    expect(signup).not.toMatch(/The pipeline is where more than 5 live/);
    expect(signup).toMatch(/readJobsHandoffSnapshot/);
    expect(signup).toMatch(/tasteJobs/);
    expect(signup).toMatch(/jobModelListLine/);
    expect(signup).toMatch(/robotJobsIntent\) return/);
    expect(signup).toMatch(/liveProof && !robotJobsIntent/);
    expect(signup).toMatch(/job opportunities for/);
    expect(signup).toMatch(/in CRM, with 5 job opportunities unlocked/);
    expect(signup).toMatch(/!resultsIntent && !robotJobsIntent/);
    expect(pipeline).toMatch(/arrivedFromPlace/);
    expect(pipeline).toMatch(/isPlaceSrc/);
    expect(JOBS_PROCESS_STEPS[2].label).toBe("CRM");
  });

  it("Jobs CRM src keeps 5 jobs and hides SIGNAL pipeline chrome", () => {
    const crm = readFileSync(join(here, "../pages/Crm.tsx"), "utf8");
    expect(crm).toMatch(/const fromJobs = isJobsHandoffSrc\(jobsSrc\)/);
    expect(crm).toMatch(/jobsSignupHref\(crmReturnHref, jobsSrc \|\| JOBS_ACTIVATE_SRC\)/);
    expect(crm).toMatch(/!teamId \|\| fromJobs\) return/);
    expect(crm).toMatch(/\{!fromJobs \? <AdminNav variant="dark" \/> : null\}/);
    expect(crm).toMatch(/fromJobs \? \(/);
    expect(crm).toMatch(/Connect HubSpot \/ GitHub/);
    expect(crm).toMatch(/\{!fromJobs \? \(/);
    expect(crm).toMatch(/CrmHero/);
    expect(crm).toMatch(/tasteJobs/);
    expect(crm).toMatch(/Opening CRM desk/);
    expect(crm).toMatch(/setLocation\(jobsDeskHref\)/);
    const back = crm.indexOf("← Back to pipeline");
    const fork = crm.indexOf("<CrmPathFork");
    const outreach = crm.indexOf("Job outreach checkpoint");
    const hide = crm.lastIndexOf("{!fromJobs ? (", fork);
    expect(back).toBeGreaterThan(-1);
    expect(fork).toBeGreaterThan(-1);
    expect(outreach).toBeGreaterThan(-1);
    expect(hide).toBeGreaterThan(-1);
    expect(fork).toBeGreaterThan(hide);
    expect(outreach).toBeGreaterThan(hide);
    const jobsTrueStart = crm.indexOf("fromJobs ? (");
    const jobsTrueEnd = crm.indexOf(") : (", jobsTrueStart);
    const jobsTrue = crm.slice(jobsTrueStart, jobsTrueEnd);
    expect(jobsTrue).toMatch(/href="\/integrations"/);
    expect(jobsTrue).not.toMatch(/href="\/pipeline"/);
    expect(jobsTrue).not.toMatch(/Cal queue/);
    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    expect(header).toMatch(/isJobsHandoffSrc\(jobsSrc\)/);
    expect(header).toMatch(/location.startsWith\("\/pipeline"\) && isJobsHandoffSrc/);
    expect(header).toMatch(/session \|\| !showPipeline/);
  });

  it("dumps checked jobs into CRM and opens the desk behind the signup wall", () => {
    const pool = [
      { job_key: "a" },
      { job_key: "b" },
      { job_key: "c" },
      { job_key: "d" },
      { job_key: "e" },
    ];
    expect(jobsDumpedToCrm(pool, ["a", "c"]).map(j => j.job_key)).toEqual([
      "a",
      "c",
    ]);
    expect(jobsDumpedToCrm(pool, []).map(j => j.job_key)).toEqual([]);
    expect(jobsForCrmDesk(pool, ["b"]).map(j => j.job_key)).toEqual(["b"]);
    expect(jobsForCrmDesk(pool, []).map(j => j.job_key)).toEqual([
      "a",
      "b",
      "c",
      "d",
      "e",
    ]);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(workspace).toMatch(/writeCrmHandoff\(next\)/);
    expect(workspace).toMatch(/setLocation\(jobsCrmOpenHref\(Boolean\(session\), submissionIdRef\.current\)\)/);
    expect(jobsCrmOpenHref(false, 42)).toBe(
      jobsSignupHref("/pipeline?src=jobs_activate&submission=42", "jobs_activate"),
    );
    expect(jobsCrmOpenHref(true, 42)).toBe(
      "/pipeline?src=jobs_activate&submission=42",
    );
    expect(CRM_FREE_BATCH).toBe(5);
    expect(CRM_FREE_BATCHES_PER_MONTH).toBe(3);
    expect(CRM_FREE_MONTHLY_CAP).toBe(15);
    expect(CRM_FREE_TTL_DAYS).toBe(7);
    const handoff = readFileSync(
      join(here, "../components/JobsHandoffBoard.tsx"),
      "utf8",
    );
    expect(handoff).toMatch(/window\.location\.replace\(jobsCrmOpenHref/);
    expect(handoff).toMatch(/jobsCrmOpenHref\(props\.signedIn/);
    expect(JOBS_PROCESS_STEPS[2].label).toBe("CRM");
    expect(JOBS_NEXT_CTA).toBe("Open CRM →");
  });

  it("lets the desk keep all 5 collected jobs and count eggs in the basket", () => {
    const keys = ["a", "b", "c", "d", "e"];
    expect(crmDeskJobKeys(keys.map(job_key => ({ job_key })))).toEqual(keys);
    expect(crmSelectAllKeys(keys)).toEqual(keys);
    expect(crmSelectAllKeys(["a", "a", "", "b"])).toEqual(["a", "b"]);
    expect(crmSelectAllLabel(5)).toBe(CRM_SELECT_ALL_LABEL);
    expect(crmSelectAllLabel(3)).toBe("Keep all 3");
    expect(crmCollectedCountLabel(5)).toBe("5 of 5 eggs in the basket");
    expect(crmCollectedCountLabel(1)).toBe("1 of 5 eggs in the basket");
    expect(crmCollectedCountLabel(3)).toBe("3 of 5 eggs in the basket");
    const kept = crmToggleSelectedKey(keys, "c", false);
    expect(kept).toEqual(["a", "b", "d", "e"]);
    expect(crmActingKeepsSelection(kept, "c")).toEqual(["a", "b", "d", "e", "c"]);
    expect(crmToggleSelectedKey(["a"], "b", true)).toEqual(["a", "b"]);
    expect(crmSyncSelectedKeys([], keys)).toEqual(keys);
    expect(crmSyncSelectedKeys(keys, keys)).toEqual(keys);
    expect(crmSyncSelectedKeys(["a", "b", "d", "e"], keys)).toEqual([
      "a",
      "b",
      "d",
      "e",
    ]);
    expect(crmSyncSelectedKeys(["old"], keys)).toEqual(keys);
    expect(CRM_EMPLOYER_NAME_CLASS).toMatch(/text-emerald-400/);
    expect(CRM_EMPLOYER_NAME_CLASS).toMatch(/font-display/);
    expect(CRM_LISTING_EYEBROW).toBe("Collected jobs");
    expect(CRM_INSPECT_HINT).toMatch(/Inspect a collected egg/i);
    expect(CRM_PLACE_EGG_HINT).toMatch(/hatches a collected egg/i);
    expect(CRM_HOW_TO_STEPS[1]).toMatch(/Collect several jobs/i);
    expect(CRM_PAGE_NEXT).toMatch(/Collect several/i);
    const desk = readFileSync(
      join(here, "../components/JobsCrmDesk.tsx"),
      "utf8",
    );
    expect(desk).toMatch(/crmSelectAllKeys\(allKeys\)/);
    expect(desk).toMatch(/crmSyncSelectedKeys/);
    expect(desk).toMatch(/type="checkbox"/);
    expect(desk).toMatch(/data-crm-select="inspect-only"/);
    expect(desk).toMatch(/setExpandedKey\(open \? null : job\.job_key\)/);
    expect(desk).not.toMatch(/setSelectedKeys\(\[job\.job_key\]\)/);
    expect(desk).not.toMatch(/setActiveKey/);
    expect(desk).toMatch(/useState<string \| null>\(null\)/);
    expect(desk).toMatch(/CollectedJobInspect/);
    expect(desk).toMatch(/Work being performed/);
    expect(desk).toMatch(/Open questions/);
    expect(desk).toMatch(/Task models/);
    expect(desk).not.toMatch(/setSelectedKeys\(\[\]\)/);
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
    expect(workspace).toMatch(/lineupSegments/);
    expect(workspace).toMatch(/Start jobs for \{seg\.title\}/);
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
    expect(CRM_PAGE_NEXT).toMatch(/jobs you keep stay jobs/i);
    expect(CRM_PAGE_NEXT).toMatch(/quote the monthly rental/i);
    expect(CRM_SUBHEAD_CLASS).toMatch(/text-lg/);
    expect(CRM_SUBHEAD_CLASS).toMatch(/sm:text-xl/);
    expect(PIPELINE_PAGE_NEXT).toMatch(/live list/i);
    expect(CRM_HEADLINE_CLASS).toMatch(/text-emerald-400/);
    expect(CRM_HOW_TO_STEPS).toHaveLength(3);
    expect(CRM_HOW_TO_STEPS[2]).toMatch(/apply/i);
    expect(CRM_WATCH_OPT_IN_LABEL).toMatch(/email me when these jobs change/i);
    expect(CRM_WATCH_FREE_HINT).toMatch(/free watches 1 robot/i);

    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const card = workspace.slice(workspace.indexOf("function JobCard"));
    expect(card).toMatch(/JOBS_ROBOT_NAME_CLASS\}>\{card\.jobTitle\}/);
    expect(card).not.toMatch(/JOBS_ROBOT_NAME_CLASS\}>\{robotName\}/);
    expect(card).not.toMatch(/JOBS_JOB_TITLE_CLASS/);
    expect(card).not.toMatch(/jobIsForLabel/);
    expect(card).toMatch(/jobIndexLabel\(index\)/);
    expect(card).not.toMatch(/robotName/);
    expect(card).toMatch(/JOBS_KEEP_LABEL/);
    expect(card).toMatch(/JOBS_SKIP_LABEL/);
    expect(card).not.toMatch(/text-\[10px\]/);

    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8",
    );
    expect(header).toMatch(/href=\{crmHref\}/);
    expect(header).toMatch(/useIsAdmin/);
    expect(header).toMatch(/href="\/admin"/);
    expect(header).toMatch(/showPipeline \? \(/);
    expect(header).toMatch(/h-14/);
    expect(header).toMatch(/sm:text-base/);
    expect(header).toMatch(/rfr-led/);

    const css = readFileSync(join(here, "../index.css"), "utf8");
    expect(css).toMatch(/--radius:\s*0;/);
    expect(css).toMatch(/border-radius:\s*0\s*!important/);
    expect(css).toMatch(/\.rfr-bevel/);
    expect(css).toMatch(/\.rfr-led \{/);
    expect(css).toMatch(/\.rfr-jobs-page-shell::after/);

    const pipeline = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    expect(pipeline).toMatch(/<ExperimentHeader/);
    expect(pipeline).toMatch(/pipelineHermesCard/);
    expect(pipeline).toMatch(/On-site evidence/);
    expect(pipeline).not.toMatch(/overlay \(not CRM truth\)/);
    expect(pipeline).not.toMatch(/Hermes intelligence/);
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
    expect(hero).toMatch(/CRM_SUBHEAD_CLASS/);
    expect(hero).toMatch(/JOBS_ACTIVATE_JOBS_CTA/);
    expect(hero).toMatch(/CRM_WATCH_OPT_IN_LABEL/);
    expect(hero).toMatch(/CRM_HOW_TO_STEPS/);
    expect(hero).toMatch(/tasteJobs/);
    expect(hero).toMatch(/CRM_UNLOCKED_JOBS/);
    expect(hero).toMatch(/jobModelListLine/);

    const intel = readFileSync(join(here, "../pages/Intelligence.tsx"), "utf8");
    expect(intel).toMatch(/ExperimentHeader/);
    expect(intel).toMatch(/KARE_FACE/);
    expect(intel).toMatch(/bg-\[#081126\]/);
    expect(intel).not.toMatch(/from "@\/components\/Header"/);
    expect(intel).toMatch(/jobsFreshHomeHref/);
    expect(intel).toMatch(/FIND_JOBS_CTA/);
    expect(intel).toMatch(/JOBS_ACTIVATE_SRC/);
    expect(intel).toMatch(/JOBS_PROCESS_STEPS/);
    expect(intel).toMatch(/JOBS_FOR_YOUR_ROBOT_HEADING/);
    expect(intel).not.toMatch(/Activate SIGNAL/);
    expect(intel).not.toMatch(/Lead scoring model/);
    expect(intel).not.toMatch(/buying signals/);
    expect(intel).not.toMatch(/href=["']\/signals/);
    expect(intel).not.toMatch(/href=\{\s*["']\/signals["']/);
    expect(intel).not.toMatch(/\bSIGNAL\b/);

    expect(crm).toMatch(/Job outreach checkpoint/);
    expect(crm).not.toMatch(/Buyer outreach checkpoint/);
    expect(crm).not.toMatch(/admin-workspace/);

    const pipelineSrc = readFileSync(join(here, "../pages/Pipeline.tsx"), "utf8");
    expect(pipelineSrc).toMatch(/JOBS_PIPELINE_CAP/);
    expect(pipelineSrc).not.toMatch(/Find buyers by industry/);
    expect(pipelineSrc).not.toMatch(/Customer opportunities/);
    expect(pipelineSrc).not.toMatch(/Why this is a sales lead/);
    expect(pipelineSrc).not.toMatch(/saving that buyer/);
    expect(pipelineSrc).not.toMatch(/Buyer workspace · preview/);
    expect(pipelineSrc).not.toMatch(/save this buyer/);

    const quickLinks = readFileSync(
      join(here, "../components/pipeline/WorkspaceQuickLinks.tsx"),
      "utf8",
    );
    expect(quickLinks).not.toMatch(/Everything happens on this page/i);
    expect(quickLinks).not.toMatch(/Activate CRM by saving/i);
    expect(pipelineSrc).toMatch(/Signed-in CRM lives in PipelineCrmMotion/);
    expect(pipelineSrc).toMatch(/!isSignedIn && !arrivedFromResultsScan/);
    expect(pipelineSrc).toMatch(/pipeline-hermes/);
    expect(pipelineSrc).not.toMatch(/bg-sky-50\/60/);
    expect(pipelineSrc).not.toMatch(/lg:h-\[calc\(100vh-100px\)\]/);
    expect(pipelineSrc).not.toMatch(/overflow-y-auto overscroll-contain/);
    expect(pipelineSrc).not.toMatch(/lg:min-h-\[calc\(100vh-200px\)\]/);
    expect(pipelineSrc).toMatch(/lg:min-h-\[calc\(100vh-5rem\)\]/);
    expect(pipelineSrc).toMatch(/lg:items-start/);
    expect(pipelineSrc).not.toMatch(/CalLeadDrop/);
    expect(pipelineSrc).not.toMatch(/Re-run SIGNAL/);
    expect(pipelineSrc).not.toMatch(/SIGNAL bulk queue/);
    expect(pipelineSrc).not.toMatch(/SIGNAL recommendation/);
    expect(pipelineSrc).toMatch(/pipeline-outreach-card/);
    expect(pipelineSrc).toMatch(/Generate outreach draft/);
    expect(pipelineSrc).toMatch(/Outreach queue/);
    expect(pipelineSrc).toMatch(/onCopy=\{copyDraft\}\s+tone="dark"/);

    const shareBar = readFileSync(
      join(here, "../components/LeadShareBar.tsx"),
      "utf8",
    );
    expect(shareBar).toMatch(/Share this job with colleagues/);
    expect(shareBar).not.toMatch(/Share this SIGNAL lead/);

    const cssSrc = readFileSync(join(here, "../index.css"), "utf8");
    expect(cssSrc).toMatch(/\.rfr-jobs-page-shell::after[\s\S]{0,180}z-index: 1;/);
    expect(cssSrc).toMatch(/\.pipeline-outreach-card/);
    expect(cssSrc).toMatch(/\.bg-slate-50\\\/80/);
    expect(cssSrc).toMatch(/\.bg-amber-50\\\/70/);

    const scoutChat = readFileSync(
      join(here, "../components/ScoutChat.tsx"),
      "utf8",
    );
    expect(scoutChat).toMatch(/onPipeline \|\|/);

    const cardSrc = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(cardSrc).toMatch(/setLocation\(jobsCrmOpenHref\(Boolean\(session\), submissionIdRef\.current\)\)/);
    expect(cardSrc).not.toMatch(/setLocation\(session \? dest/);
    expect(cardSrc).not.toMatch(/window\.location\.href = session/);
    expect(cardSrc).toMatch(/id="jobs-list"/);
    expect(cardSrc).toMatch(/const processOnActivate = goToActivate/);
    expect(cardSrc).toMatch(/cursor-pointer/);
    expect(cardSrc).not.toMatch(/if \(!onClick\) \{/);
    expect(cardSrc).toMatch(/robotJobCardFromMatch/);
    expect(cardSrc).toMatch(/Employer/);
    expect(cardSrc).toMatch(/Task models/);
    expect(cardSrc).not.toMatch(/How we qualify a candidate/);
    expect(cardSrc).not.toMatch(/Where to find price/);
    expect(cardSrc).not.toMatch(/certificate/i);
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
        action: "Open with dock-to-stock AMR ROI — ask who owns slotting and outbound flow.",
        industry: "Logistics",
        company: "Acme Logistics",
        title: "Dock to stock",
      }),
    ).toBe("Dock to stock — Acme Logistics · Logistics");
    expect(
      jobExplanation({
        action: "Operational automation opportunity — confirm specific pain on discovery call",
        friction: "Why now signal not yet summarized",
        workflow: "cleaning / housekeeping robots",
        company: "MGM Resorts",
      }),
    ).toBe("cleaning / housekeeping robots");
    expect(isSalesPlaceholder("Operational automation opportunity — confirm specific pain on discovery call")).toBe(true);
    expect(isSalesPlaceholder("Move pallets from receiving to reserve overnight")).toBe(false);
  });

  it("filters OEM hub noise; search is 3 free / 5 paid; lineup is not capped at 3", () => {
    expect(jobsProductLimitForPlan(null)).toBe(JOBS_PRODUCT_CAP_FREE);
    expect(jobsProductLimitForPlan("anonymous")).toBe(3);
    expect(jobsProductLimitForPlan("free")).toBe(3);
    expect(jobsProductLimitForPlan("paid")).toBe(JOBS_PRODUCT_CAP_PAID);
    expect(JOBS_LINEUP_DISPLAY_CAP).toBe(3);
    const omron = filterJobsLineupProducts([
      { name: "Products overview" },
      { name: "AMRs" },
      { name: "Industries" },
      { name: "About Us" },
      { name: "Collaborative" },
      { name: "Discontinued Products" },
      { name: "Activate your AMR License" },
      { name: "Deutsch" },
      { name: "Español" },
      { name: "Français" },
      { name: "LD-250" },
      { name: "HD-1500" },
      { name: "MD-650" },
      { name: "LD-90" },
    ]);
    expect(omron.map(p => p.name)).toEqual([
      "LD-250",
      "HD-1500",
      "MD-650",
      "LD-90",
    ]);
    expect(pageJobsLineup(omron, 0).map(p => p.name)).toEqual([
      "LD-250",
      "HD-1500",
      "MD-650",
    ]);
    expect(pageJobsLineup(omron, 1).map(p => p.name)).toEqual(["LD-90"]);
    const paidSearch = filterJobsLineupProducts(
      [
        { name: "LD-250" },
        { name: "HD-1500" },
        { name: "MD-650" },
        { name: "LD-90" },
        { name: "LD-60" },
        { name: "LD-105" },
      ],
      JOBS_PRODUCT_CAP_PAID,
    );
    expect(paidSearch.map(p => p.name)).toEqual([
      "LD-250",
      "HD-1500",
      "MD-650",
      "LD-90",
      "LD-60",
    ]);
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(workspace).toMatch(/filterJobsLineupProducts/);
    expect(workspace).toMatch(/pageJobsLineup/);
    expect(workspace).toMatch(/Next 3/);
    expect(workspace).toMatch(/ROBOT_PROFILE_TIMEOUT_MS/);
    expect(workspace).toMatch(/lookupKnownOem/);
    expect(workspace).toMatch(/fetchOemListing/);
    expect(workspace).toMatch(/OEM_LISTING_TIMEOUT_MS/);
    expect(workspace).toMatch(/Lookup took too long/);
    expect(workspace).not.toMatch(/Paste a specific product URL/);
    expect(workspace).toMatch(/productCap/);
    expect(workspace).toMatch(/phase=\{researchPhase\}/);
    const crm = readFileSync(join(here, "../pages/Crm.tsx"), "utf8");
    expect(crm).toMatch(/crm-navy/);
    expect(crm).not.toMatch(/bg-white/);
    const account = readFileSync(
      join(here, "../components/crm/CrmAccountWorkspace.tsx"),
      "utf8",
    );
    expect(account).not.toMatch(/bg-white/);
    expect(account).toMatch(/bg-\[#0b162f\]/);
  });

  it("segments large OEM catalogs by class and SKU family without a per-SKU crawl", () => {
    expect(skuFamilyStem("LD-250")).toBe("LD");
    expect(skuFamilyStem("HD-1500")).toBe("HD");
    expect(skuFamilyStem("Fourier GR-1")).toBe("GR");
    expect(skuFamilyStem("Fourier GR-3C Cosmo")).toBe("GR");
    expect(skuFamilyStem("N1")).toBe("N");
    expect(skuFamilyStem("Digit")).toBeNull();

    const omron = lineupSegments([
      { name: "LD-250", displayClass: "amr" },
      { name: "LD-90", displayClass: "amr" },
      { name: "LD-60", displayClass: "amr" },
      { name: "HD-1500", displayClass: "amr" },
      { name: "MD-650", displayClass: "amr" },
    ]);
    expect(usesLineupSegments(omron.flatMap(s => s.products), 3)).toBe(true);
    expect(omron.map(s => s.title)).toEqual([
      "LD AMRs",
      "HD-1500",
      "MD-650",
    ]);
    expect(searchNamesForSegment(omron[0], 3)).toEqual([
      "LD-250",
      "LD-90",
      "LD-60",
    ]);
    expect(lineupJobLookups(omron[0].products)).toEqual([
      {
        grain: "robot_type",
        robotClass: "amr",
        productNames: ["LD-250", "LD-90", "LD-60"],
      },
    ]);

    const fourier = lineupSegments([
      { name: "Fourier GR-3C Cosmo", displayClass: "humanoid" },
      { name: "Fourier GR-3", displayClass: "humanoid" },
      { name: "Fourier GR-2", displayClass: "humanoid" },
      { name: "Fourier GR-1", displayClass: "humanoid" },
      { name: "Fourier N1", displayClass: "humanoid" },
    ]);
    expect(fourier.map(s => s.title)).toEqual(["GR humanoids", "Fourier N1"]);
    expect(searchNamesForSegment(fourier[0], 3)).toEqual([
      "Fourier GR-3C Cosmo",
      "Fourier GR-3",
      "Fourier GR-2",
    ]);

    const mixed = lineupSegments([
      { name: "Atlas", displayClass: "humanoid" },
      { name: "Spot", displayClass: "quadruped" },
      { name: "Stretch", displayClass: "mobile_manipulator" },
    ]);
    expect(usesLineupSegments(mixed.flatMap(s => s.products), 3)).toBe(true);
    expect(mixed.map(s => s.robotClass).sort()).toEqual([
      "humanoid",
      "mobile_manipulator",
      "quadruped",
    ]);
    expect(usesLineupSegments([{ name: "Digit", displayClass: "humanoid" }], 3)).toBe(
      false,
    );
    expect(
      usesLineupSegments(
        [
          { name: "LD-250", displayClass: "amr" },
          { name: "LD-90", displayClass: "amr" },
          { name: "LD-60", displayClass: "amr" },
        ],
        3,
      ),
    ).toBe(false);

    const unlabeled = lineupSegments([
      { name: "LD-250" },
      { name: "LD-90" },
      { name: "HD-1500" },
    ]);
    expect(unlabeled.map(s => s.title)).toEqual(["LD robots", "HD-1500"]);
  });
});
