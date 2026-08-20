/**
 * Jobs submit workflow helpers — keep FIND → JOBS → 5 buyer leads on one path.
 * Multi-robot confirm must never dump the user on a catalog with no next step.
 */

export type JobsConfirmLanding = "review" | "jobs";

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

/** Anonymous → 5-lead review. Signed-in → pipeline. */
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
  params.set("limit", "5");
  return `/results?${params.toString()}`;
}
