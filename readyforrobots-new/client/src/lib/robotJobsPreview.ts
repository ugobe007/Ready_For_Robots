/**
 * Anonymous named-employer jobs for FIND home.
 * GET /api/robot-jobs/preview — live RobotJob rows, not the stale tape.
 */
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";

export type PreviewJob = {
  job_key: string;
  employer: string;
  workplace: string;
  work: string;
  description: string;
  timing: string;
  decision_maker: string;
  contact: string;
};

export function formatInlineJobLine(job: PreviewJob): string {
  const head = [job.employer, job.workplace].filter(Boolean).join(" · ");
  const work = [job.work, job.description]
    .filter(Boolean)
    .filter((part, i, all) => i === 0 || part !== all[0])
    .join(". ");
  const facts = [job.timing, job.decision_maker, job.contact].filter(Boolean);
  return [head, work, ...facts].filter(Boolean).join(" — ");
}

export async function fetchRobotJobsPreview(
  limit = 3
): Promise<PreviewJob[]> {
  const cap = Math.max(1, Math.min(limit, 8));
  const base = getPublicReadApiBase();
  const res = await fetch(
    `${base}/api/robot-jobs/preview?limit=${cap}`,
    liveFetchInit({ headers: { Accept: "application/json" } })
  );
  if (!res.ok) return [];
  const body = (await res.json()) as { jobs?: PreviewJob[] };
  const rows = Array.isArray(body.jobs) ? body.jobs : [];
  return rows.filter(job => (job.employer || "").trim()).slice(0, cap);
}
