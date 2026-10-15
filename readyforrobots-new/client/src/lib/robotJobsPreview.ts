/**
 * Anonymous named-employer jobs for FIND home, /jobs, and the public board.
 * GET /api/robot-jobs/preview — live RobotJob rows when Fly has the route.
 * SPA HTML 200 is not an empty table: fall back to the named-employer corpus
 * so the board is readable without submitting a robot URL.
 */
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";
import { exampleEmployerLabel } from "@/lib/exampleEmployer";
import tapeJson from "@/lib/market_tape_jobs.json";
import { JOB_CARD_EXAMPLE_LABEL } from "@/lib/robotJobCard";

export type PreviewJob = {
  job_key: string;
  employer: string;
  workplace: string;
  work: string;
  description: string;
  timing: string;
  decision_maker: string;
  contact: string;
  source_url?: string | null;
  is_example?: boolean;
};

type TapeRow = {
  key?: string;
  title?: string;
  industry?: string;
  path?: string;
};

function isJsonContentType(value: string | null): boolean {
  return (value || "").toLowerCase().includes("json");
}

function namedPreviewJob(job: PreviewJob): PreviewJob | null {
  const employer = (job.employer || "").trim();
  if (!employer) return null;
  return { ...job, employer };
}

export function formatInlineJobLine(job: PreviewJob): string {
  const head = [job.employer, job.workplace].filter(Boolean).join(" · ");
  const work = [job.work, job.description]
    .filter(Boolean)
    .filter((part, i, all) => i === 0 || part !== all[0])
    .join(". ");
  const facts = [job.timing, job.decision_maker, job.contact].filter(Boolean);
  const line = [head, work, ...facts].filter(Boolean).join(" — ");
  return job.is_example ? `${JOB_CARD_EXAMPLE_LABEL} — ${line}` : line;
}

export function previewJobsFromTape(limit = 3): PreviewJob[] {
  const cap = Math.max(1, Math.min(limit, 8));
  const rows = Array.isArray(tapeJson.jobs) ? (tapeJson.jobs as TapeRow[]) : [];
  const out: PreviewJob[] = [];
  for (const raw of rows) {
    const key = String(raw.key || "").trim();
    const title = String(raw.title || "").trim();
    const industry = String(raw.industry || "").trim();
    if (!key || !title || !industry) continue;
    const place = industry.split("·").slice(1).map(part => part.trim());
    const employer = exampleEmployerLabel(title, raw.path, industry);
    if (!employer) continue;
    out.push({
      job_key: key,
      employer,
      workplace: place.join(" · "),
      work: title,
      description: "",
      timing: "",
      decision_maker: "",
      contact: "",
      source_url: null,
      is_example: true,
    });
    if (out.length >= cap) break;
  }
  return out;
}

function jobsFromPreviewBody(body: unknown, cap: number): PreviewJob[] | null {
  if (!body || typeof body !== "object") return null;
  const rows = (body as { jobs?: PreviewJob[] }).jobs;
  if (!Array.isArray(rows)) return null;
  return rows
    .map(job => namedPreviewJob(job))
    .filter((job): job is PreviewJob => Boolean(job))
    .slice(0, cap);
}

export async function fetchRobotJobsPreview(limit = 3): Promise<PreviewJob[]> {
  const cap = Math.max(1, Math.min(limit, 8));
  const base = getPublicReadApiBase();
  try {
    const res = await fetch(
      `${base}/api/robot-jobs/preview?limit=${cap}`,
      liveFetchInit({ headers: { Accept: "application/json" } })
    );
    if (res.ok && isJsonContentType(res.headers.get("content-type"))) {
      const body = (await res.json()) as unknown;
      const live = jobsFromPreviewBody(body, cap);
      if (live && live.length) return live;
    }
  } catch {
    /* Fly missing the route, HTML catch-all, or network — show the board. */
  }
  return previewJobsFromTape(cap);
}
