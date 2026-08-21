/**
 * Jobs submit workflow — FIND → QUALIFY on `/`. PLACE is later.
 *
 * The job list on `/` is the product. Clicking a job is the next step
 * (Qualify this job). Do not hop to a second "Jobs for ______" list on
 * /results or /pipeline after login — that screen has no action and kills
 * the workflow.
 *
 * Cap: the terminal shows 5 example jobs. See All reveals more on the same
 * page. Never send Jobs traffic to /pipeline as a duplicate job board.
 */

export type JobsConfirmLanding = "review" | "jobs";

export const JOBS_EXAMPLE_CAP = 5;
export const BUYER_LEADS_ANON_CAP = 5;
/** See All on `/` — more than the 5-example cap, still the same page. */
export const JOBS_PIPELINE_CAP = 12;

export function landingStageAfterConfirm(robotCount: number): JobsConfirmLanding {
  return robotCount > 1 ? "jobs" : "review";
}

export function jobsHeading(opts: {
  productName: string;
  companyName: string;
  robotCount: number;
}): string {
  if (opts.robotCount > 1) {
    return `Jobs for ${opts.companyName || opts.productName}`;
  }
  return `Jobs for ${opts.productName}`;
}

export function capExampleJobs<T>(jobs: T[], cap = JOBS_EXAMPLE_CAP): T[] {
  return jobs.slice(0, cap);
}

/** Jobs / results `src` values that continue the Jobs terminal, not SIGNAL. */
export function isJobsHandoffSrc(src: string | null | undefined): boolean {
  const value = (src || "").trim();
  return (
    value.startsWith("jobs_") ||
    value.startsWith("robot_jobs") ||
    value === "jobs_all_robots" ||
    value === "robot_jobs_qualify"
  );
}

export const FIND_JOBS_CTA = "Find jobs →";
/** @deprecated leftover copy — Jobs no longer uses a page-level "jobs for your robot" hop. */
export const JOBS_FOR_YOUR_ROBOT_CTA = "Qualify this job →";
export const JOBS_FOR_YOUR_ROBOT_HEADING = "Jobs for your robot";
export const JOBS_FOR_YOUR_ROBOT_KEEP_CTA = "Keep this search →";
export const JOBS_LIST_NEXT_STEP_HEADING = "This job looks interesting";
export const QUALIFY_JOB_CTA = "Qualify this job →";
export const QUALIFY_JOB_REQUEST_CTA = "Request qualification";

export function buyerLeadsCtaLabel(_signedIn: boolean): string {
  return QUALIFY_JOB_CTA;
}

export function buyerLeadsCtaHeading(_signedIn: boolean): string {
  return JOBS_LIST_NEXT_STEP_HEADING;
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

export const JOBS_RESTORE_ONCE_KEY = "rfr_jobs_restore_once";

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

export function jobsQualifySignupHref(): string {
  return jobsSignupHref(jobsWorkspaceRestoreHref(), "robot_jobs_qualify");
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
 * Legacy name. Jobs CTAs used to dump signed-in users on /pipeline and
 * anonymous users on /results — a second FIND with no QUALIFY action.
 * Always return to the Jobs workspace instead.
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
