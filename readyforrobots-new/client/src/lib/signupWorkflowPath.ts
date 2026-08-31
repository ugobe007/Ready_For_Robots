/**
 * Post-signup destination helpers.
 * Jobs funnel (next=/ or /jobs…) must return to the product — never /pipeline.
 * Legacy URL → /results → questionnaire → /pipeline remains for explicit /results next.
 */

export type WorkflowPrefill = {
  wf?: "robot_company" | "buyer";
  intent_focus?: string;
  company_url?: string;
  src?: string;
};

const REVIEWED_5_LEADS_KEY = "rfr_reviewed_5_leads";
const BUILD15_KEYS = ["rfr_build15_started", "rfr_build25_started"] as const;

export function markReviewedFiveLeads(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(REVIEWED_5_LEADS_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function hasReviewedFiveLeads(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.sessionStorage.getItem(REVIEWED_5_LEADS_KEY) === "1";
  } catch {
    return false;
  }
}

export function clearBuild15UnlockFlags(): void {
  if (typeof window === "undefined") return;
  try {
    for (const key of BUILD15_KEYS) window.sessionStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

/** True when signup next should land on the Jobs product (/, /jobs, /jobs/:slug). */
export function isJobsProductReturnPath(nextRaw: string): boolean {
  const path = (nextRaw || "").trim().split("?")[0] || "";
  return path === "/" || path === "/jobs" || path.startsWith("/jobs/");
}

/** Normalize legacy /jobs index → /. */
export function normalizeJobsReturnPath(nextRaw: string): string {
  const raw = (nextRaw || "").trim();
  if (!raw) return "/";
  if (raw === "/jobs") return "/";
  if (raw.startsWith("/jobs?")) return `/${raw.slice("/jobs".length)}`;
  return raw;
}

/** Build /results?url=…&limit=5 for the five-lead review step. */
export function workflowResultsPath(
  prefill: WorkflowPrefill,
  nextRaw = ""
): string {
  const fromNext = urlFromResultsNext(nextRaw);
  const companyUrl = (prefill.company_url || fromNext || "").trim();
  if (!companyUrl) return "/pipeline";
  const params = new URLSearchParams();
  params.set("url", companyUrl);
  params.set("limit", "5");
  const src = prefill.src || srcFromResultsNext(nextRaw) || "signup_return";
  params.set(
    "src",
    src.includes("signup_return") ? src : `${src}_signup_return`
  );
  return `/results?${params.toString()}`;
}

function urlFromResultsNext(nextRaw: string): string {
  if (!nextRaw.startsWith("/results")) return "";
  try {
    const q = nextRaw.includes("?")
      ? nextRaw.slice(nextRaw.indexOf("?") + 1)
      : "";
    return (new URLSearchParams(q).get("url") || "").trim();
  } catch {
    return "";
  }
}

function srcFromResultsNext(nextRaw: string): string {
  if (!nextRaw.startsWith("/results")) return "";
  try {
    const q = nextRaw.includes("?")
      ? nextRaw.slice(nextRaw.indexOf("?") + 1)
      : "";
    return (new URLSearchParams(q).get("src") || "").trim();
  } catch {
    return "";
  }
}

export function shouldHonorWorkflowResults(
  nextRaw: string,
  prefill: WorkflowPrefill
): boolean {
  if (nextRaw.startsWith("/results")) return true;
  if (isJobsProductReturnPath(nextRaw)) return false;
  if (!(prefill.company_url || "").trim()) return false;
  if (
    nextRaw.startsWith("/pipeline") ||
    nextRaw === "/" ||
    nextRaw.startsWith("/pricing")
  ) {
    return false;
  }
  if ((prefill.src || "").includes("home_header")) return false;
  if ((prefill.src || "") === "robot_jobs") return false;
  return true;
}

/**
 * Resolve where signup/OAuth should land.
 * Priority: jobs product → /results → /pipeline|/pricing → matched unlock → rebuild results → /pipeline.
 */
export function resolveSignupWorkflowReturnPath(args: {
  nextRaw: string;
  prefill: WorkflowPrefill;
  matchedPipelineReturnPath?: string | null;
}): string {
  const nextRaw = (args.nextRaw || "").trim();
  if (isJobsProductReturnPath(nextRaw)) return normalizeJobsReturnPath(nextRaw);
  // Never skip the 5-lead Results step when signup was opened for it.
  if (nextRaw.startsWith("/results")) return nextRaw;
  if (nextRaw.startsWith("/pipeline") || nextRaw.startsWith("/pricing"))
    return nextRaw;
  if (args.matchedPipelineReturnPath) return args.matchedPipelineReturnPath;
  if (!shouldHonorWorkflowResults(nextRaw, args.prefill)) return "/pipeline";
  return workflowResultsPath(args.prefill, nextRaw);
}
