/**
 * Employer MATCH — work language → named catalog robots.
 * Catalog only. No live OEM scrape. Not a second job matcher.
 */
import { fetchWithTimeout, getPublicReadApiBase } from "@/lib/apiBase";

const PRODUCTION_MATCH_API = "https://ready-2-robot.fly.dev";

/** Localhost has no API process. Catalog match is a production read. */
function matchApiBase(): string {
  const base = getPublicReadApiBase();
  if (typeof window === "undefined") return base;
  const host = window.location.hostname;
  if (
    (host === "localhost" || host === "127.0.0.1") &&
    base.startsWith("http://127.0.0.1:8000")
  ) {
    return PRODUCTION_MATCH_API;
  }
  return base;
}

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
  task?: string | null;
  setting?: string | null;
  specs?: Record<string, string | number | boolean> | null;
  image_url?: string | null;
};

export function employerRobotKey(
  robot: Pick<EmployerMatchedRobot, "vendor_name" | "name">
): string {
  return `${robot.vendor_name}|${robot.name}`;
}

/** Additive shortlist. Checking one robot never clears the others. */
export function toggleEmployerRobotKey(prev: string[], key: string): string[] {
  return prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key];
}

export function catalogHttpUrl(raw?: string | null): string | null {
  const text = (raw || "").trim();
  if (!text) return null;
  try {
    const parsed = new URL(text);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return null;
    }
    return parsed.toString();
  } catch {
    return null;
  }
}

const CATALOG_SPEC_LABELS: Record<string, string> = {
  payload_kg: "Payload",
  battery_life_h: "Runtime",
  height_cm: "Height",
  weight_kg: "Weight",
  top_speed_mps: "Top speed",
  finger_count: "Fingers",
  charge_time_h: "Charge time",
  can_climb_stairs: "Climbs stairs",
  has_sdk: "SDK",
};

function formatCatalogSpecValue(key: string, value: string | number | boolean): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    if (key.endsWith("_kg")) return `${value} kg`;
    if (key.endsWith("_cm")) return `${value} cm`;
    if (key.endsWith("_h")) return `${value} h`;
    if (key.endsWith("_mps")) return `${value} m/s`;
    return String(value);
  }
  return value.trim();
}

export function catalogSpecRows(
  specs?: EmployerMatchedRobot["specs"]
): { label: string; value: string }[] {
  if (!specs) return [];
  const rows: { label: string; value: string }[] = [];
  for (const [key, raw] of Object.entries(specs)) {
    if (raw === null || raw === undefined || raw === "") continue;
    if (typeof raw !== "string" && typeof raw !== "number" && typeof raw !== "boolean") {
      continue;
    }
    const value = formatCatalogSpecValue(key, raw);
    if (!value) continue;
    rows.push({
      label:
        CATALOG_SPEC_LABELS[key] ||
        key.replace(/_/g, " ").replace(/\b\w/g, ch => ch.toUpperCase()),
      value,
    });
  }
  return rows;
}

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
  const base = matchApiBase();
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
  contactName?: string;
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
      contact_name: opts.contactName || null,
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
