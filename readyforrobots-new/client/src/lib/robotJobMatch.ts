/**
 * POST /api/robot-job-match — identity → capability research → corpus jobs.
 * Research-first: pass the Understanding profile so matching inspects requirements.
 */
import { getPublicReadApiBase } from "@/lib/apiBase";
import type { RobotProfileResult } from "@/lib/robotProfile";

export type MatchCapability = {
  key: string;
  label: string;
  confidence: number;
  excerpt?: string | null;
  truth_state?: "confirmed" | "inferred";
};

export type MatchProduct = {
  name: string;
  robot_class?: string | null;
  evidence_url?: string | null;
  confidence?: number;
};

export type ResearchStage = {
  id: string;
  label: string;
  status: string;
  detail?: string | null;
};

export type MatchJob = {
  job_key: string;
  title: string;
  industry: string;
  path: string;
  company_name?: string | null;
  locality?: string | null;
  tape_family?: string;
  unknowns?: string[];
  source?: string;
  verdict?: "POSSIBLE_MATCH" | "NOT_A_MATCH" | "INSUFFICIENT";
  why?: string[];
  still_unknown?: string[];
  blockers?: string[];
  required_task_models?: {
    id: string;
    label: string;
    physical_task: string;
    vertical: string;
    presence: "unknown" | "present" | "absent";
    hardware_not_enough: string;
    candidate_families?: string[];
    where_to_look: {
      kind: string;
      name: string;
      url: string | null;
      note: string;
    }[];
    qualify_filters?: {
      id: string;
      label: string;
      note: string;
    }[];
    pricing_lookups?: {
      kind: string;
      name: string;
      url: string | null;
      note: string;
    }[];
  }[];
  fit?: {
    hardware_fit?: number;
    intelligence_fit?: number;
    environment_fit?: number;
    deployment_readiness?: number;
    honesty?: string;
    task_coverage?: {
      task_family?: string;
      coverage?: string;
      trained_task_count?: number;
    }[];
    model_matches?: {
      model_name?: string | null;
      coverage?: number;
      url?: string | null;
      embodiment_compatible?: string;
    }[];
  };
  /** SKU this card is for. Set on the Jobs terminal, carried onto the pipeline list. */
  forRobot?: string;
};

export type ClassOption = {
  id: string;
  label: string;
  hint: string;
};

export type RobotJobMatchResult = {
  state:
    | "matches"
    | "thin_corpus"
    | "could_not_understand"
    | "select_product"
    | "qualify_robot";
  robot_name: string;
  capabilities: MatchCapability[];
  families: { id: string; confidence: number }[];
  jobs: MatchJob[];
  job_count: number;
  source_url?: string | null;
  company_name?: string | null;
  products?: MatchProduct[];
  needs_product_choice?: boolean;
  needs_class_choice?: boolean;
  class_options?: ClassOption[];
  preview_image_url?: string | null;
  research_stages?: ResearchStage[];
  robot_class?: string | null;
  evidence_urls?: string[];
  matcher?: string | null;
  /** Durable submitter ledger id — stamped onto funnel events for attribution. */
  robot_submission_id?: number | null;
  /** Truthful zero-state explainer (set only when job_count === 0). */
  zero_reason?: "insufficient_profile_evidence" | "no_compatible_jobs" | "corpus_gap" | null;
};

export type RecoveryChip = "moves_materials" | "manipulates" | "cleans" | "inspects" | "other";

export async function fetchRobotJobMatch(opts: {
  url?: string;
  chip?: RecoveryChip;
  robotName?: string;
  productName?: string;
  profile?: RobotProfileResult | null;
  assertedClass?: string;
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
      product_name: opts.productName || null,
      profile: opts.profile || null,
      asserted_class: opts.assertedClass || null,
    }),
    signal: opts.signal,
  });
  if (!res.ok) {
    throw new Error(`robot-job-match ${res.status}`);
  }
  return (await res.json()) as RobotJobMatchResult;
}
