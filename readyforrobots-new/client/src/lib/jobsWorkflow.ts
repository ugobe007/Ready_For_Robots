/**
 * Jobs submit workflow — FIND on `/`.
 *
 * Step 1 PROFILE → step 2 JOBS → step 3 PLACE (buyers).
 * The jobs list inspects (expand for why / unknowns / blockers).
 * One Next at the bottom of the page leaves step 2 for buyers — not a
 * second CTA on the card, not a Qualify loop back to jobs.
 *
 * Cap: 5 example jobs. See All reveals more on the same page.
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
export const JOBS_FOR_YOUR_ROBOT_HEADING = "Jobs for your robot";
/** Page-level advance on the jobs list (step 2 → Place). Not on the card. */
export const JOBS_NEXT_CTA = "Next →";
export const JOBS_NEXT_HINT = "Buyers who need this work";
export const JOBS_PLACE_CTA = "See buyers →";

/** Pipeline as sales leads — never a Jobs handoff src (those bounce back to `/`). */
export function jobsPlaceHref(robotUrl: string, submissionId?: number | null): string {
  const params = new URLSearchParams();
  const url = (robotUrl || "").trim();
  if (url) params.set("url", url);
  params.set("src", "place");
  if (submissionId && submissionId > 0) params.set("submission", String(submissionId));
  const qs = params.toString();
  return qs ? `/pipeline?${qs}` : "/pipeline";
}

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
 * second job list. Buyer Place uses jobsPlaceHref (`src=place`) instead.
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
