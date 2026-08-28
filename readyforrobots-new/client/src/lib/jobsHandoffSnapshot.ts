/**
 * Carry Jobs-terminal matches onto /results and /pipeline so those pages
 * show robot jobs, not SIGNAL buyer companies.
 *
 * Identity key: the submitted company URL (canonicalRobotUrl). A new FIND
 * must overwrite this snapshot even when jobs are empty.
 */
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  canonicalRobotUrl,
  emptyRobotIdentity,
  sameRobotUrl,
} from "@/lib/robotUrlIdentity";

export const JOBS_HANDOFF_STORAGE_KEY = "rfr_jobs_handoff_v1";

export type JobsHandoffSnapshot = {
  url: string;
  productName: string;
  jobs: MatchJob[];
  /** How many jobs at the top were checked on `/`. */
  selectedCount?: number;
};

export function normalizeRobotHandoffUrl(url: string): string {
  return canonicalRobotUrl(url);
}

export function sameRobotHandoffUrl(
  a?: string | null,
  b?: string | null,
): boolean {
  return sameRobotUrl(a, b);
}

export function saveJobsHandoffSnapshot(snap: JobsHandoffSnapshot): void {
  if (typeof window === "undefined") return;
  const url = canonicalRobotUrl(snap.url);
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

/** Bind CRM to this URL immediately — honest empty until FIND returns. */
export function beginJobsHandoffForUrl(
  url: string,
  productName = "",
): JobsHandoffSnapshot | null {
  const identity = emptyRobotIdentity(url, productName);
  if (!identity.url) return null;
  const snap: JobsHandoffSnapshot = {
    url: identity.url,
    productName: identity.productName,
    jobs: [],
    selectedCount: 0,
  };
  saveJobsHandoffSnapshot(snap);
  return snap;
}

export function clearJobsHandoffSnapshot(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(JOBS_HANDOFF_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function loadJobsHandoffSnapshot(url: string): JobsHandoffSnapshot | null {
  const parsed = readJobsHandoffSnapshot();
  if (!parsed) return null;
  const wanted = canonicalRobotUrl(url);
  if (!wanted) return null;
  if (!sameRobotUrl(parsed.url, wanted)) return null;
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
