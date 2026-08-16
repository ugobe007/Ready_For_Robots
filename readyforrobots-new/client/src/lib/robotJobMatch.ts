/**
 * POST /api/robot-job-match — capability profile → corpus jobs.
 */
import { getPublicReadApiBase } from "@/lib/apiBase";

export type MatchCapability = {
  key: string;
  label: string;
  confidence: number;
  excerpt?: string | null;
};

export type MatchJob = {
  job_key: string;
  title: string;
  industry: string;
  path: string;
  company_name?: string | null;
  locality?: string | null;
  tape_family?: string;
  score?: number;
  unknowns?: string[];
  source?: string;
};

export type RobotJobMatchResult = {
  state: "matches" | "thin_corpus" | "could_not_understand";
  robot_name: string;
  capabilities: MatchCapability[];
  families: { id: string; confidence: number }[];
  jobs: MatchJob[];
  job_count: number;
  source_url?: string | null;
};

export type RecoveryChip = "moves_materials" | "manipulates" | "cleans" | "inspects" | "other";

export async function fetchRobotJobMatch(opts: {
  url?: string;
  chip?: RecoveryChip;
  robotName?: string;
  signal?: AbortSignal;
}): Promise<RobotJobMatchResult> {
  const base = getPublicReadApiBase();
  const res = await fetch(`${base}/api/robot-job-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      url: opts.url || null,
      chip: opts.chip || null,
      robot_name: opts.robotName || null,
    }),
    signal: opts.signal,
  });
  if (!res.ok) {
    throw new Error(`robot-job-match ${res.status}`);
  }
  return (await res.json()) as RobotJobMatchResult;
}
