/**
 * Jobs submit workflow helpers — keep FIND → JOBS → 5 buyer leads on one path.
 * Multi-robot confirm must never dump the user on a catalog with no next step.
 *
 * Cap rules (signup-critical):
 *   Jobs terminal always shows 5 example jobs.
 *   Anonymous buyer preview is 5 companies (/results).
 *   More than 5 buyer leads exists only on /pipeline after that handoff.
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

export function buyerLeadsCtaLabel(signedIn: boolean): string {
  return signedIn ? "See buyer leads →" : "See 5 buyer leads →";
}

/** Anonymous → 5-lead review. Signed-in → pipeline (more than 5). */
export function buyerLeadsHref(opts: {
  robotUrl: string;
  signedIn: boolean;
  submissionId?: number | null;
  src?: string;
  industry?: string;
}): string {
  const params = new URLSearchParams();
  const url = (opts.robotUrl || "").trim();
  if (url) params.set("url", url);
  params.set("src", opts.src || "jobs_all_robots");
  if (opts.submissionId) params.set("submission", String(opts.submissionId));
  const industry = (opts.industry || "").trim();
  if (opts.signedIn) {
    if (industry) params.set("industries", industry);
    return `/pipeline?${params.toString()}`;
  }
  params.set("limit", String(BUYER_LEADS_ANON_CAP));
  return `/results?${params.toString()}`;
}
