/**
 * Jobs submit workflow helpers — keep FIND → JOBS → jobs for your robot.
 * Multi-robot confirm must never dump the user on a catalog with no next step.
 *
 * Cap rules (signup-critical):
 *   Jobs terminal always shows 5 example jobs.
 *   Anonymous preview is 5 jobs (/results).
 *   More than 5 jobs exists only on /pipeline after that handoff.
 *
 * User-facing CTA is always "Jobs for your robot". Never "buyer leads" / "sales leads".
 */

export type JobsConfirmLanding = "review" | "jobs";

export const JOBS_EXAMPLE_CAP = 5;
export const BUYER_LEADS_ANON_CAP = 5;

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

export const JOBS_FOR_YOUR_ROBOT_CTA = "Jobs for your robot →";
export const JOBS_FOR_YOUR_ROBOT_HEADING = "Jobs for your robot";
export const JOBS_FOR_YOUR_ROBOT_KEEP_CTA = "Keep these jobs for your robot →";
/** Jobs-list (step 2) next-step box — never "Next step: buyer leads". */
export const JOBS_LIST_NEXT_STEP_HEADING = "Next step: Jobs for your robot";

export function buyerLeadsCtaLabel(_signedIn: boolean): string {
  return JOBS_FOR_YOUR_ROBOT_CTA;
}

export function buyerLeadsCtaHeading(_signedIn: boolean): string {
  return JOBS_LIST_NEXT_STEP_HEADING;
}

/** Scan status on /results when arriving from Jobs — jobs, not sales leads. */
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

/** Anonymous → 5-job review. Signed-in → pipeline (more than 5). */
export function buyerLeadsHref(opts: {
  robotUrl: string;
  signedIn: boolean;
  submissionId?: number | null;
  src?: string;
  industry?: string;
  leadId?: number | null;
}): string {
  const params = new URLSearchParams();
  const url = (opts.robotUrl || "").trim();
  if (url) params.set("url", url);
  params.set("src", persistJobsHandoffSrc(opts.src));
  if (opts.submissionId) params.set("submission", String(opts.submissionId));
  if (opts.leadId) params.set("lead", String(opts.leadId));
  const industry = (opts.industry || "").trim();
  if (opts.signedIn) {
    if (industry) params.set("industries", industry);
    return `/pipeline?${params.toString()}`;
  }
  params.set("limit", String(BUYER_LEADS_ANON_CAP));
  return `/results?${params.toString()}`;
}
