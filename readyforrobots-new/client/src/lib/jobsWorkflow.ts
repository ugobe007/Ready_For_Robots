/**
 * Jobs submit workflow — FIND on `/`.
 *
 * Step 1 PROFILE → step 2 JOBS → activate the job list (live pipeline).
 * Inspect cards (why / unknowns / blockers). Check the jobs to take
 * forward. Process chrome lives on the page (01 → 02 → 03). The document
 * scrolls. Do not trap the next step inside a clipped 100vh box.
 *
 * Cap: 5 example jobs on `/`. Activate fills the live list to 15.
 */

export type JobsConfirmLanding = "review" | "jobs" | "portfolio";
export type JobLookupGrain = "robot_type" | "product";

export type LineupProduct = { name: string; displayClass?: string | null };

export type LineupJobLookup = {
  grain: JobLookupGrain;
  robotClass: string | null;
  productNames: string[];
};

/** Frontend aliases — keep in sync with `robot_class_qualify.normalize_class_id`. */
const ROBOT_CLASS_ALIASES: Record<string, string> = {
  humanoid: "humanoid",
  biped: "humanoid",
  bipedal: "humanoid",
  amr: "amr",
  agv: "amr",
  mobile_robot: "amr",
  mobile_manipulator: "mobile_manipulator",
  cobot: "cobot",
  arm: "cobot",
  collaborative: "cobot",
  quadruped: "quadruped",
  spot: "quadruped",
  scrubber: "autonomous_scrubber",
  autonomous_scrubber: "autonomous_scrubber",
  forklift: "amr",
};

const ROBOT_CLASS_JOBS_LABEL: Record<string, string> = {
  humanoid: "humanoids",
  amr: "AMRs",
  mobile_manipulator: "mobile manipulators",
  cobot: "collaborative arms",
  quadruped: "quadrupeds",
  autonomous_scrubber: "floor scrubbers",
};

const ROBOT_CLASS_TITLE: Record<string, string> = {
  humanoid: "Humanoid",
  amr: "AMR",
  mobile_manipulator: "Mobile manipulator",
  cobot: "Collaborative arm",
  quadruped: "Quadruped",
  autonomous_scrubber: "Floor scrubber",
};

export function normalizeRobotClass(raw?: string | null): string | null {
  const want = (raw || "").trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (!want) return null;
  return ROBOT_CLASS_ALIASES[want] || null;
}

export function robotClassTitle(classId?: string | null): string {
  const id = normalizeRobotClass(classId);
  if (!id) return "robot";
  return ROBOT_CLASS_TITLE[id] || id.replace(/_/g, " ");
}

export function robotClassJobsLabel(classId?: string | null): string {
  const id = normalizeRobotClass(classId);
  if (!id) return "this robot type";
  return ROBOT_CLASS_JOBS_LABEL[id] || `${id.replace(/_/g, " ")}s`;
}

/**
 * One lookup per robot type (class), not per SKU.
 * Unknown class falls back to a product-level lookup so we never mix types.
 */
export function lineupJobLookups(products: LineupProduct[]): LineupJobLookup[] {
  const groups = new Map<string, string[]>();
  const unknown: string[] = [];
  for (const row of products) {
    const name = (row.name || "").trim();
    if (!name) continue;
    const cls = normalizeRobotClass(row.displayClass);
    if (!cls) {
      unknown.push(name);
      continue;
    }
    const names = groups.get(cls) || [];
    names.push(name);
    groups.set(cls, names);
  }
  const out: LineupJobLookup[] = [];
  for (const [robotClass, productNames] of groups) {
    out.push({ grain: "robot_type", robotClass, productNames });
  }
  for (const name of unknown) {
    out.push({ grain: "product", robotClass: null, productNames: [name] });
  }
  return out;
}

export function productClassesFromLineup(
  products: LineupProduct[],
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const row of products) {
    const cls = normalizeRobotClass(row.displayClass);
    if (row.name && cls) out[row.name] = cls;
  }
  return out;
}

export const JOBS_EXAMPLE_CAP = 5;
export const BUYER_LEADS_ANON_CAP = 5;
/** See All on `/` — more than the 5-example cap, still the same page. */
export const JOBS_PIPELINE_CAP = 15;
/** Live list after Activate: checked jobs first, then fill to this cap. */
export const JOBS_ACTIVATE_CAP = 15;

export function landingStageAfterConfirm(robotCount: number): JobsConfirmLanding {
  // Picker already chose the robot(s). Land on jobs — do not ask Find jobs again.
  return robotCount >= 1 ? "jobs" : "review";
}

/** Hide "0 matching jobs" on unresearched shells; hide identical counts across a lineup. */
export function portfolioShowsJobCounts(
  robots: Array<{ matched?: boolean; jobCount?: number }>,
): boolean {
  const matched = robots.filter(a => a.matched);
  if (matched.length === 0) return false;
  if (matched.length === 1) return true;
  return new Set(matched.map(a => a.jobCount ?? 0)).size > 1;
}

export function jobsHeading(opts: {
  productName: string;
  companyName: string;
  robotCount: number;
  lookupGrain?: JobLookupGrain | null;
  robotClass?: string | null;
}): string {
  if (opts.robotCount > 1 && opts.companyName) {
    return `Jobs for ${opts.companyName}`;
  }
  // One selected SKU keeps the product name even when the match was type-first.
  // "Jobs for humanoids" is a lineup heading, not a single-robot heading.
  return `Jobs for ${opts.productName}`;
}

export function jobsCountEyebrow(opts: {
  visibleCount: number;
  productName: string;
  companyName?: string;
  robotCount?: number;
  lookupGrain?: JobLookupGrain | null;
  robotClass?: string | null;
}): string {
  if (opts.visibleCount === 0) return "";
  const who =
    (opts.robotCount || 1) > 1 && opts.companyName
      ? opts.companyName
      : opts.productName;
  return `${opts.visibleCount} JOBS FOR ${who.toUpperCase()}`;
}

export function capExampleJobs<T>(jobs: T[], cap = JOBS_EXAMPLE_CAP): T[] {
  return jobs.slice(0, cap);
}

/** Jobs / results `src` values that continue the Jobs terminal. */
export function isJobsHandoffSrc(src: string | null | undefined): boolean {
  const value = (src || "").trim();
  return (
    value.startsWith("jobs_") ||
    value.startsWith("robot_jobs") ||
    value === "jobs_all_robots" ||
    value === "robot_jobs_qualify"
  );
}

export const FIND_JOBS_CTA = "Start jobs →";
export const JOBS_FOR_YOUR_ROBOT_HEADING = "Jobs for your robot";
/** Page-level advance on the jobs list. Not on the card. */
export const JOBS_NEXT_CTA = "Next →";
export const JOBS_NEXT_HINT = "Your checked jobs sit at the top of 15 live jobs";
export const JOBS_SEE_JOBS_CTA = "See jobs →";

export type JobsProcessStepId = "find" | "jobs" | "activate";

/** FIND → jobs → activate. Always shown as navigational links. */
export const JOBS_PROCESS_STEPS = [
  {
    id: "find" as const,
    n: "01",
    label: "Show us your robot",
    linkLabel: FIND_JOBS_CTA,
  },
  {
    id: "jobs" as const,
    n: "02",
    label: "Here are its jobs",
    linkLabel: JOBS_SEE_JOBS_CTA,
  },
  {
    id: "activate" as const,
    n: "03",
    label: "Activate the job list",
    linkLabel: JOBS_NEXT_CTA,
  },
];

export function jobsProcessStepFromStage(stage: string): JobsProcessStepId {
  if (stage === "jobs" || stage === "portfolio") return "jobs";
  return "find";
}

export const JOBS_ACTIVATE_SRC = "jobs_activate";
export const JOBS_PLACE_SRC = "place";
export const JOBS_PLACE_CTA = "Activate job list →";

export const JOBS_FRESH_QUERY = "new";
export const JOBS_WORKSPACE_SESSION_KEY = "rfr_jobs_workspace";
export const JOBS_RESTORE_ONCE_KEY = "rfr_jobs_restore_once";

export function jobsFreshHomeHref(): string {
  return `/?${JOBS_FRESH_QUERY}=1`;
}

export function isJobsFreshQuery(search: string | null | undefined): boolean {
  return new URLSearchParams(search || "").get(JOBS_FRESH_QUERY) === "1";
}

/** Drop in-progress FIND state. Used by the wordmark before leaving the page. */
export function clearJobsWorkspaceSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(JOBS_WORKSPACE_SESSION_KEY);
    window.sessionStorage.removeItem(JOBS_RESTORE_ONCE_KEY);
  } catch {
    /* ignore */
  }
}

/**
 * Wordmark / Jobs home. Wouter Link to `/?new=1` is a no-op while already on
 * `/` (profile, jobs, picker) — same pathname, query ignored — so the chrome
 * looks dead. Always assign so FIND remounts.
 */
export function goJobsFreshHome(): void {
  clearJobsWorkspaceSession();
  if (typeof window === "undefined") return;
  window.location.assign(jobsFreshHomeHref());
}

export function onJobsFreshHomeClick(event: {
  preventDefault: () => void;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  button?: number;
}): void {
  const newTab = Boolean(
    event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      (event.button != null && event.button !== 0),
  );
  clearJobsWorkspaceSession();
  if (newTab) return;
  event.preventDefault();
  goJobsFreshHome();
}

/** Place leftovers still must not bounce as a Jobs handoff. */
export function isPlaceSrc(src: string | null | undefined): boolean {
  return (src || "").trim() === JOBS_PLACE_SRC;
}

export function isJobsActivateSrc(src: string | null | undefined): boolean {
  return (src || "").trim() === JOBS_ACTIVATE_SRC;
}

/** Live pipeline as the activated job list — never the OEM as `url=`. */
export function jobsActivateHref(submissionId?: number | null): string {
  const params = new URLSearchParams();
  params.set("src", JOBS_ACTIVATE_SRC);
  if (submissionId && submissionId > 0) params.set("submission", String(submissionId));
  return `/pipeline?${params.toString()}`;
}

/** @deprecated Use jobsActivateHref. Kept so leftover Place links compile. */
export function jobsPlaceHref(opts?: {
  leadId?: number | null;
  submissionId?: number | null;
}): string {
  return jobsActivateHref(opts?.submissionId);
}

export function jobsForActivatedPipeline<T extends { job_key: string }>(
  selected: T[],
  pool: T[],
  cap = JOBS_ACTIVATE_CAP,
): T[] {
  const picked = selected.filter(job => job?.job_key);
  const seen = new Set(picked.map(job => job.job_key));
  const extra = pool.filter(job => job?.job_key && !seen.has(job.job_key));
  return [...picked, ...extra].slice(0, cap);
}

/** Activate never no-ops: checked jobs first, else the example cap, else the pool. */
export function jobsToActivate<T extends { job_key: string }>(
  selected: T[],
  pool: T[],
  cap = JOBS_ACTIVATE_CAP,
): T[] {
  const picked = selected.filter(job => job?.job_key);
  const seed = picked.length > 0 ? picked : capExampleJobs(pool);
  return jobsForActivatedPipeline(seed, pool, cap);
}

export function defaultCheckedJobKeys<T extends { job_key: string }>(
  jobs: T[],
  cap = JOBS_EXAMPLE_CAP,
): string[] {
  return capExampleJobs(jobs, cap).map(job => job.job_key);
}

export const RAIL_STEP_HINT = {
  find: "Paste the manufacturer URL. We research the company and every robot SKU we can prove.",
  profile: "Confirm we understood this robot. Then find jobs against these capabilities.",
  jobs: "Expand a card to inspect. Check every job you want. Next activates the list.",
  pipeline: "Checked jobs stay at the top. We fill the rest so you see 15 live jobs, not one buyer.",
} as const;

/** The job Next will place: expanded card, else the first visible job. */
export function jobForNextStep<T extends { job_key: string }>(
  jobs: T[],
  expandedKey: string | null | undefined,
): T | null {
  if (expandedKey) {
    const hit = jobs.find(j => j.job_key === expandedKey);
    if (hit) return hit;
  }
  return jobs[0] ?? null;
}

/** Scan status on /results when arriving from Jobs — unused; Jobs stays on `/`. */
export const JOBS_SCAN_STEPS = [
  "Waiting for your robot URL…",
  "Reading what this robot can do…",
  "Finding jobs for your robot…",
  "Matching work to confirmed capabilities…",
  "Preparing five jobs to review…",
] as const;

/**
 * After a robot-URL lookup, never leave the jobs list empty when a live
 * feed exists. Scoped matches win; otherwise show the live pipeline.
 */
export function buyerLeadsToShow<T>(opts: {
  scopedRows: T[];
  liveRows: T[];
  lookupPending: boolean;
  scopeToUrl: boolean;
}): T[] {
  if (!opts.scopeToUrl) return opts.liveRows;
  if (opts.lookupPending) return opts.scopedRows;
  return opts.scopedRows.length > 0 ? opts.scopedRows : opts.liveRows;
}

/**
 * Place prefers buyers in the job's industry. If the filter is too thin,
 * keep the live feed so step 3 is never empty.
 */
export function placeBuyersToShow<T extends { industry?: string | null }>(
  rows: T[],
  industry?: string | null,
  cap = BUYER_LEADS_ANON_CAP,
): T[] {
  const needle = (industry || "").trim().toLowerCase();
  const scoped = needle
    ? rows.filter(row => {
        const ind = (row.industry || "").trim().toLowerCase();
        if (!ind) return false;
        return ind.includes(needle) || needle.includes(ind);
      })
    : [];
  const pool = scoped.length >= 2 ? scoped : rows;
  return pool.slice(0, cap);
}

/** Keep a Jobs src on later hops. Never rewrite Jobs → results_scan. */
export function persistJobsHandoffSrc(src: string | null | undefined): string {
  const value = (src || "").trim();
  return isJobsHandoffSrc(value) ? value : "jobs_all_robots";
}

export function jobsSignupHref(nextHref: string, src: string): string {
  return `/signup?next=${encodeURIComponent(nextHref)}&src=${encodeURIComponent(src)}`;
}

/** Auth / leftover-link return to the Jobs workspace on `/`. */
export function jobsWorkspaceRestoreHref(): string {
  return "/?restore=1";
}

/**
 * Revisit of `/` must show FIND (hero), not replay the last robot URL.
 * Restore only on browser back/forward, auth return (one-shot), or ?restore=1.
 * Reload / tab-discard / typed URL / bookmark stay on FIND — same-tab session
 * cache must not auto-run the previous submit.
 */
export function shouldRestoreJobsWorkspace(opts: {
  navigationType?: string | number | null;
  restoreOnce?: boolean;
  restoreQuery?: boolean;
}): boolean {
  if (opts.restoreQuery || opts.restoreOnce) return true;
  const t = opts.navigationType;
  return t === "back_forward" || t === 2;
}

/** True when post-auth `next` is the Jobs front door (not pipeline). */
export function isJobsHomeDest(dest: string | null | undefined): boolean {
  const path = (dest || "").trim().split("?")[0] || "";
  return path === "/" || path === "/jobs" || path.startsWith("/jobs/");
}

/** Auth return to `/` or `/jobs…` may restore in-progress work once. */
export function markJobsWorkspaceRestoreIfHome(dest: string | null | undefined): void {
  if (isJobsHomeDest(dest)) markJobsWorkspaceRestoreOnce();
}

export function markJobsWorkspaceRestoreOnce(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(JOBS_RESTORE_ONCE_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function consumeJobsWorkspaceRestoreOnce(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const on = window.sessionStorage.getItem(JOBS_RESTORE_ONCE_KEY) === "1";
    if (on) window.sessionStorage.removeItem(JOBS_RESTORE_ONCE_KEY);
    return on;
  } catch {
    return false;
  }
}

export function readNavigationType(): string | number | null {
  if (typeof performance === "undefined") return null;
  const entry = performance.getEntriesByType("navigation")[0] as
    | PerformanceNavigationTiming
    | undefined;
  if (entry?.type) return entry.type;
  const legacy = (performance as Performance & { navigation?: { type?: number } }).navigation?.type;
  return typeof legacy === "number" ? legacy : null;
}

/**
 * Stamp restore and return `/`. Use when a leftover Jobs link still points
 * at /pipeline or /results — bounce, do not render a second job list.
 */
export function armJobsWorkspaceRestore(): string {
  markJobsWorkspaceRestoreOnce();
  return jobsWorkspaceRestoreHref();
}

/**
 * Legacy name. Jobs CTAs used to dump signed-in users on /pipeline as a
 * second job list. Activate uses jobsActivateHref (`src=jobs_activate`) instead.
 * This helper still returns the Jobs workspace for leftover links.
 */
export function buyerLeadsHref(_opts: {
  robotUrl: string;
  signedIn: boolean;
  submissionId?: number | null;
  src?: string;
  industry?: string;
  leadId?: number | null;
}): string {
  return jobsWorkspaceRestoreHref();
}
