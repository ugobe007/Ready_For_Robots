/**
 * Employer MATCH — work language → named catalog robots.
 * Not a second job matcher. Not company → category → jobs.
 */
import { getPublicReadApiBase } from "@/lib/apiBase";

export type EmployerMatchedRobot = {
  name: string;
  vendor_name: string;
  vendor_url?: string | null;
  robot_class?: string | null;
  description?: string | null;
  product_url?: string | null;
};

export type EmployerRobotMatchResult = {
  state: "matches" | "empty";
  robots: EmployerMatchedRobot[];
  robot_count: number;
  work_class?: string | null;
  empty_copy?: string | null;
};

export type EmployerJobDraftResult = {
  ok: boolean;
  job_key?: string | null;
  persisted?: boolean;
  detail?: string | null;
};

export async function fetchEmployerRobotMatch(opts: {
  workClass: string;
  description?: string;
  jobUrl?: string;
  signal?: AbortSignal;
}): Promise<EmployerRobotMatchResult> {
  const base = getPublicReadApiBase();
  const res = await fetch(`${base}/api/employer-robot-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      work_class: opts.workClass || null,
      description: opts.description || null,
      job_url: opts.jobUrl || null,
    }),
    signal: opts.signal,
  });
  if (!res.ok) {
    throw new Error(`employer-robot-match ${res.status}`);
  }
  return (await res.json()) as EmployerRobotMatchResult;
}

export async function postEmployerJobDraft(opts: {
  employer: string;
  title: string;
  workplace?: string;
  description?: string;
  workClass?: string;
  jobUrl?: string;
  shortlisted?: { name: string; vendor_name: string }[];
}): Promise<EmployerJobDraftResult> {
  const base = getPublicReadApiBase();
  const res = await fetch(`${base}/api/employer-job-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      employer: opts.employer,
      title: opts.title,
      workplace: opts.workplace || null,
      description: opts.description || null,
      work_class: opts.workClass || null,
      job_url: opts.jobUrl || null,
      shortlisted: opts.shortlisted || [],
    }),
  });
  const data = (await res.json().catch(() => ({}))) as EmployerJobDraftResult;
  if (!res.ok) {
    return {
      ok: false,
      persisted: false,
      detail:
        (data as { detail?: string }).detail ||
        `Could not post this job (${res.status}).`,
    };
  }
  return data;
}
