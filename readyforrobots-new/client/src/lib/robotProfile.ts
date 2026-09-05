/**
 * POST /api/robot-profile — Understanding v1 Phases 1–3 research agent.
 * Identity → sources → facts → Robot Profile (no jobs).
 */
import { getApiBase, fetchWithTimeout } from "@/lib/apiBase";

export type ProfileSourceType =
  | "product"
  | "specifications"
  | "solutions"
  | "documentation"
  | "case_study"
  | "press_release"
  | "support"
  | "homepage"
  | "other";

export type ResearchStage = {
  id: string;
  label: string;
  status: string;
  detail?: string | null;
};

export type RobotProfileFact = {
  id: string;
  subject: string;
  predicate: string;
  value: string | number | boolean;
  units?: string | null;
  epistemic: string;
  confidence: number;
  evidence_span?: string | null;
  source_id: string;
};

export type RobotProfileSource = {
  id: string;
  url: string;
  source_type: ProfileSourceType;
  title?: string | null;
  publisher_role: string;
  confidence: number;
  fetched_at?: string;
  document_date?: string | null;
};

export type RobotProfileProduct = {
  id: string;
  name: string;
  generation?: string | null;
  display_class?: string | null;
  description?: string | null;
};

export type RobotProfileResult = {
  submitted_url: string;
  built_at: string;
  robot_submission_id?: number | null;
  profile_confidence: "A" | "B" | "C";
  source_grounding_rate: number;
  coverage_rate?: number;
  coverage_level?: "high" | "medium" | "low";
  source_quality_rate?: number;
  source_quality_level?: "high" | "medium" | "low";
  research_morphology?: string | null;
  needs_product_choice: boolean;
  notes: string[];
  research_stages: ResearchStage[];
  company: {
    id: string;
    name: string;
    primary_domain: string;
    aliases?: string[];
  };
  products: RobotProfileProduct[];
  selected_product: RobotProfileProduct | null;
  sources: RobotProfileSource[];
  facts: RobotProfileFact[];
};

export type OemListingRobot = {
  name: string;
  description?: string | null;
  display_class?: string | null;
};

export type OemListingResult = {
  matched: boolean;
  vendor_name?: string | null;
  vendor_url?: string | null;
  robots: OemListingRobot[];
};

/** Indexed OEM homepage → named robots. Skips live manufacturer fetch. */
export async function fetchOemListing(opts: {
  url: string;
  signal?: AbortSignal;
  timeoutMs?: number;
}): Promise<OemListingResult> {
  const base = getApiBase();
  const res = await fetchWithTimeout(
    `${base}/api/oem-listing?url=${encodeURIComponent(opts.url)}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: opts.signal,
    },
    opts.timeoutMs ?? 5_000
  );
  if (!res.ok) {
    throw new Error(`oem-listing ${res.status}`);
  }
  const body = (await res.json()) as OemListingResult;
  return {
    matched: Boolean(body?.matched),
    vendor_name: body?.vendor_name || null,
    vendor_url: body?.vendor_url || null,
    robots: Array.isArray(body?.robots) ? body.robots : [],
  };
}

export async function fetchRobotProfile(opts: {
  url: string;
  product?: string;
  maxSources?: number;
  signal?: AbortSignal;
  timeoutMs?: number;
}): Promise<RobotProfileResult> {
  const base = getApiBase();
  const res = await fetchWithTimeout(
    `${base}/api/robot-profile`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        url: opts.url,
        product: opts.product || null,
        max_sources: opts.maxSources ?? 6,
      }),
      signal: opts.signal,
    },
    opts.timeoutMs ?? 22_000
  );
  if (!res.ok) {
    let detail = `robot-profile ${res.status}`;
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
  return (await res.json()) as RobotProfileResult;
}

/** User-facing labels for confirmed fact predicates. */
export function formatFactLine(f: RobotProfileFact): string {
  const units = f.units ? ` ${f.units}` : "";
  const val =
    typeof f.value === "boolean"
      ? f.value
        ? "yes"
        : "no"
      : `${f.value}${units}`;
  const labels: Record<string, string> = {
    carrying_capacity: "Carrying capacity",
    battery_runtime: "Battery / runtime",
    product_class: "Robot class",
    supports_tote_handling: "Tote / material handling",
    warehouse_or_factory_deployment: "Warehouse / factory environments",
    supports_hard_floor_scrubbing: "Hard-floor scrubbing",
    arm_count: "Arm count",
    has_mobile_base: "Mobile base",
    autonomous_navigation: "Autonomous navigation",
    claims_load_unload: "Load / unload (claimed)",
    claims_warehouse_transport: "Warehouse transport (claimed)",
    reach_or_workspace: "Reach / workspace",
    end_effector: "End effector",
    has_dexterous_hands: "Dexterous hands",
    mobility_architecture: "Mobility architecture",
    operating_environment: "Operating environment",
    autonomy_or_control: "Autonomy / control",
    payload: "Payload / carry capacity",
    runtime: "Runtime / power",
    mobility: "Mobility architecture",
    environment: "Operating environment",
    workflows: "Demonstrated workflows",
    scrubbing: "Hard-floor scrubbing",
    autonomy: "Autonomy / control",
  };
  const name = labels[f.predicate] || f.predicate.replace(/_/g, " ");
  if (f.epistemic === "unknown" || f.value === "UNKNOWN") {
    return `${name}: UNKNOWN`;
  }
  if (f.epistemic === "contradicted") {
    return `${name}: ${val} (CONFLICTED)`;
  }
  return `${name}: ${val}`;
}

export function sourceTypeLabel(t: string): string {
  const map: Record<string, string> = {
    product: "Product page",
    specifications: "Specifications",
    solutions: "Solutions / use cases",
    documentation: "Documentation",
    case_study: "Case study",
    press_release: "Press",
    support: "Support / manual",
    homepage: "Homepage",
    other: "Other",
  };
  return map[t] || t;
}

/** Honest incompleteness copy for profile confidence tiers (Understanding v1.0). */
export function profileConfidenceCopy(
  tier: "A" | "B" | "C",
  opts?: { emptyResearch?: boolean }
): string {
  if (opts?.emptyResearch) {
    return "We recognized the manufacturer from the URL, but could not read its product pages — treat this as identity only, not a confirmed spec sheet.";
  }
  if (tier === "A") {
    return "Strong identity and good research coverage of key facts — treat as a solid starting profile.";
  }
  if (tier === "B") {
    return "We confirmed the robot identity and key facts, but some technical constraints are still unknown.";
  }
  return "We confirmed the robot's identity and what it does, but research coverage is still limited — treat detailed specifications as unconfirmed.";
}
