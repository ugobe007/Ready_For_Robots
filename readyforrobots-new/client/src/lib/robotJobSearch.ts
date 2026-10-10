/**
 * POST /api/robot-job-search — one composed profile + jobs transaction.
 */
import { getPublicReadApiBase, fetchWithTimeout } from "@/lib/apiBase";
import type {
  MatchCapability,
  MatchJob,
  RobotJobMatchResult,
} from "@/lib/robotJobMatch";
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
  url?: string;
  product?: string;
  maxSources?: number;
  assertedClass?: string;
  lookupGrain?: "robot_type" | "product";
  signal?: AbortSignal;
  timeoutMs?: number;
}): Promise<RobotJobSearchResult> {
  const base = getPublicReadApiBase();
  const res = await fetchWithTimeout(
    `${base}/api/robot-job-search`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        url: opts.url || null,
        product: opts.product || null,
        max_sources: opts.maxSources ?? 6,
        asserted_class: opts.assertedClass || null,
        lookup_grain: opts.lookupGrain || null,
      }),
      signal: opts.signal,
    },
    opts.timeoutMs ?? 12_000
  );
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
