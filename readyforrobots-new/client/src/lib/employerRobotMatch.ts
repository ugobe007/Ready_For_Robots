/**
 * Employer MATCH — work language → named catalog robots.
 * Catalog only. No live OEM scrape. Not a second job matcher.
 */
import { fetchWithTimeout, getPublicReadApiBase } from "@/lib/apiBase";

export const EMPLOYER_MATCH_TIMEOUT_MS = 2_500;
export const EMPLOYER_JD_ACCEPT =
  ".pdf,.doc,.docx,.txt,application/pdf,text/plain";
export const EMPLOYER_JD_TEXT_CAP = 12_000;

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
  catalog_only?: boolean;
  live_scrape?: boolean;
};

export type EmployerJobDraftResult = {
  ok: boolean;
  job_key?: string | null;
  persisted?: boolean;
  detail?: string | null;
};

export type EmployerJdFile = {
  filename: string;
  text: string;
  mediaType: string;
};

export async function readEmployerJdFile(file: File): Promise<EmployerJdFile> {
  const filename = (file.name || "job-description").slice(0, 240);
  const mediaType = file.type || "";
  const lower = filename.toLowerCase();
  if (lower.endsWith(".txt") || mediaType.startsWith("text/")) {
    const text = (await file.text()).slice(0, EMPLOYER_JD_TEXT_CAP);
    return { filename, text, mediaType: mediaType || "text/plain" };
  }
  return {
    filename,
    text: "",
    mediaType: mediaType || "application/octet-stream",
  };
}

export async function fetchEmployerRobotMatch(opts: {
  workClass: string;
  description?: string;
  jobUrl?: string;
  signal?: AbortSignal;
}): Promise<EmployerRobotMatchResult> {
  const base = getPublicReadApiBase();
  const res = await fetchWithTimeout(
    `${base}/api/employer-robot-match`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        work_class: opts.workClass || null,
        description: opts.description || null,
        job_url: opts.jobUrl || null,
      }),
      signal: opts.signal,
    },
    EMPLOYER_MATCH_TIMEOUT_MS
  );
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
  jdFilename?: string;
  jdText?: string;
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
      jd_filename: opts.jdFilename || null,
      jd_text: opts.jdText || null,
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
