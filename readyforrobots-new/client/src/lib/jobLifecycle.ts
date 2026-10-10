/**
 * Job Opportunity Lifecycle & Scarcity Engine
 * - Applicant Cap: max 3 applicants per job.
 * - [Pending] Status: marked pending review when 3 spots are filled.
 * - Aging & Archive: 0-2 weeks fresh, 2-8 weeks aging, 8+ weeks archived.
 * - Archive Access: Paid workspaces only.
 */
import type { MatchJob } from "@/lib/robotJobMatch";

export const MAX_APPLICANTS_PER_JOB = 3;
export const JOB_AGING_FRESH_DAYS = 14; // 2 weeks
export const JOB_ARCHIVE_DAYS = 56; // 8 weeks

export type JobLifecycleState = {
  applicantsCount: number;
  maxApplicants: number;
  isPending: boolean;
  spotsRemaining: number;
  postedDate: Date;
  expiresDate: Date;
  daysOld: number;
  daysRemaining: number;
  isFresh: boolean;
  isAging: boolean;
  isArchived: boolean;
  statusLabel: string;
  subLabel: string;
  badgeClass: string;
};

/** Deterministic hash of string for consistent aging & applicant count generation */
function stringHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function getJobLifecycleState(job: MatchJob): JobLifecycleState {
  const hash = stringHash(job.job_key || job.title || "job");

  // 1. Applicants count (0..3)
  let applicantsCount = job.applicants_count ?? (hash % 4);
  if (applicantsCount > MAX_APPLICANTS_PER_JOB) applicantsCount = MAX_APPLICANTS_PER_JOB;
  const isPending = applicantsCount >= MAX_APPLICANTS_PER_JOB;
  const spotsRemaining = Math.max(0, MAX_APPLICANTS_PER_JOB - applicantsCount);

  // 2. Posted date & Aging (1 to 60 days seed if posted_at not provided)
  const now = new Date();
  let postedDate: Date;
  if (job.posted_at) {
    postedDate = new Date(job.posted_at);
  } else {
    const ageDaysSeed = (hash % 58) + 1;
    postedDate = new Date(now.getTime() - ageDaysSeed * 86400000);
  }

  const daysOld = Math.max(0, Math.floor((now.getTime() - postedDate.getTime()) / 86400000));
  const expiresDate = new Date(postedDate.getTime() + JOB_ARCHIVE_DAYS * 86400000);
  const daysRemaining = Math.max(0, Math.ceil((expiresDate.getTime() - now.getTime()) / 86400000));

  const isFresh = daysOld < JOB_AGING_FRESH_DAYS;
  const isArchived = daysOld >= JOB_ARCHIVE_DAYS;
  const isAging = !isFresh && !isArchived;

  const dateStr = expiresDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  let statusLabel = "";
  let subLabel = "";
  let badgeClass = "";

  if (isPending) {
    statusLabel = "PENDING REVIEW";
    subLabel = "3/3 Applicant Spots Filled · Proposals Under Review";
    badgeClass = "border-amber-500/50 bg-amber-500/20 text-amber-300";
  } else if (isArchived) {
    statusLabel = "ARCHIVED";
    subLabel = `8+ Weeks Old · Deadline: ${dateStr} · Paid Access Only`;
    badgeClass = "border-purple-500/50 bg-purple-500/20 text-purple-300";
  } else if (isFresh) {
    statusLabel = "FRESH MATCH";
    subLabel = `${spotsRemaining} Spot${spotsRemaining === 1 ? "" : "s"} Open · Deadline: ${dateStr} (${daysRemaining}d left)`;
    badgeClass = "border-emerald-500/50 bg-emerald-500/20 text-emerald-300";
  } else {
    statusLabel = "AGING";
    subLabel = `${spotsRemaining} Spot${spotsRemaining === 1 ? "" : "s"} Open · Deadline: ${dateStr} (${daysRemaining}d left)`;
    badgeClass = "border-sky-500/50 bg-sky-500/20 text-sky-300";
  }

  return {
    applicantsCount,
    maxApplicants: MAX_APPLICANTS_PER_JOB,
    isPending,
    spotsRemaining,
    postedDate,
    expiresDate,
    daysOld,
    daysRemaining,
    isFresh,
    isAging,
    isArchived,
    statusLabel,
    subLabel,
    badgeClass,
  };
}
