/**
 * Carry Jobs-terminal matches onto /results and /pipeline so those pages
 * show robot jobs, not SIGNAL buyer companies.
 */
import type { MatchJob } from "@/lib/robotJobMatch";

export const JOBS_HANDOFF_STORAGE_KEY = "rfr_jobs_handoff_v1";

export type JobsHandoffSnapshot = {
  url: string;
  productName: string;
  jobs: MatchJob[];
  /** How many jobs at the top were checked on `/`. */
  selectedCount?: number;
};

export function normalizeRobotHandoffUrl(url: string): string {
  const raw = (url || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw);
    parsed.hash = "";
    const path = parsed.pathname.replace(/\/+$/, "") || "";
    return `${parsed.protocol}//${parsed.host.toLowerCase()}${path}${parsed.search}`;
  } catch {
    return raw.replace(/\/+$/, "");
  }
}

export function sameRobotHandoffUrl(
  a?: string | null,
  b?: string | null,
): boolean {
  const left = normalizeRobotHandoffUrl(a || "");
  const right = normalizeRobotHandoffUrl(b || "");
  return Boolean(left && right && left === right);
}

export function saveJobsHandoffSnapshot(snap: JobsHandoffSnapshot): void {
  if (typeof window === "undefined") return;
  const url = normalizeRobotHandoffUrl(snap.url);
  // Empty jobs are valid: FIND may finish with incomplete identity.
  // Still overwrite the previous robot so CRM cannot keep a stale SKU.
  if (!url || !Array.isArray(snap.jobs)) return;
  try {
    window.sessionStorage.setItem(
      JOBS_HANDOFF_STORAGE_KEY,
      JSON.stringify({
        url,
        productName: snap.productName || "",
        jobs: snap.jobs,
        selectedCount: snap.selectedCount ?? snap.jobs.length,
      } satisfies JobsHandoffSnapshot),
    );
  } catch {
    /* ignore quota / private mode */
  }
}

export function loadJobsHandoffSnapshot(url: string): JobsHandoffSnapshot | null {
  const parsed = readJobsHandoffSnapshot();
  if (!parsed) return null;
  const wanted = normalizeRobotHandoffUrl(url);
  if (!wanted) return null;
  if (normalizeRobotHandoffUrl(parsed.url) !== wanted) return null;
  return parsed;
}

/** Most recent Jobs handoff, if any — used by the Jobs header Pipeline link. */
export function readJobsHandoffSnapshot(): JobsHandoffSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(JOBS_HANDOFF_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as JobsHandoffSnapshot;
    if (!parsed || !Array.isArray(parsed.jobs) || !parsed.url) return null;
    return parsed;
  } catch {
    return null;
  }
}
