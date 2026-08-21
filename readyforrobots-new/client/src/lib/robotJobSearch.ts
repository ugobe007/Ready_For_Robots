/**
 * POST /api/robot-job-search — one composed profile + jobs transaction.
 */
import { getPublicReadApiBase } from "@/lib/apiBase";
import type { MatchCapability, MatchJob, RobotJobMatchResult } from "@/lib/robotJobMatch";
import type { RobotProfileResult } from "@/lib/robotProfile";
import type { SearchTimings } from "@/lib/submitWorkflow";

export type RobotJobSearchResult = Omit<RobotJobMatchResult, "products"> & {
  profile?: RobotProfileResult | null;
  top_jobs?: MatchJob[];
  timings?: SearchTimings;
  capabilities?: MatchCapability[];
  products?: Array<{
    name: string;
    display_class?: string | null;
    robot_class?: string | null;
  }>;
};

export async function fetchRobotJobSearch(opts: {
  url: string;
  product?: string;
  maxSources?: number;
  assertedClass?: string;
  signal?: AbortSignal;
}): Promise<RobotJobSearchResult> {
  const base = getPublicReadApiBase();
  const res = await fetch(`${base}/api/robot-job-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      url: opts.url,
      product: opts.product || null,
      max_sources: opts.maxSources ?? 6,
      asserted_class: opts.assertedClass || null,
    }),
    signal: opts.signal,
  });
  if (!res.ok) {
    let detail = `robot-job-search ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body?.detail === "string" && body.detail.trim()) {
        detail = body.detail.trim();
      }
    } catch {
      /* keep status fallback */
    }
    throw new Error(detail);
  }
  return (await res.json()) as RobotJobSearchResult;
}
