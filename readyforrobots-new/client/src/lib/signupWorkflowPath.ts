/**
 * Post-signup destination for the URL → signup → 5 leads → info → 15 leads flow.
 * Explicit ?next=/results… must never be rewritten to bare /pipeline.
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

/** Build /results?url=…&limit=5 for the five-lead review step. */
export function workflowResultsPath(prefill: WorkflowPrefill, nextRaw = ""): string {
  const fromNext = urlFromResultsNext(nextRaw);
  const companyUrl = (prefill.company_url || fromNext || "").trim();
  if (!companyUrl) return "/pipeline";
  const params = new URLSearchParams();
  params.set("url", companyUrl);
  params.set("limit", "5");
  const src = prefill.src || srcFromResultsNext(nextRaw) || "signup_return";
  params.set("src", src.includes("signup_return") ? src : `${src}_signup_return`);
  return `/results?${params.toString()}`;
}

function urlFromResultsNext(nextRaw: string): string {
  if (!nextRaw.startsWith("/results")) return "";
  try {
    const q = nextRaw.includes("?") ? nextRaw.slice(nextRaw.indexOf("?") + 1) : "";
    return (new URLSearchParams(q).get("url") || "").trim();
  } catch {
    return "";
  }
}

function srcFromResultsNext(nextRaw: string): string {
  if (!nextRaw.startsWith("/results")) return "";
  try {
    const q = nextRaw.includes("?") ? nextRaw.slice(nextRaw.indexOf("?") + 1) : "";
    return (new URLSearchParams(q).get("src") || "").trim();
  } catch {
    return "";
  }
}

export function shouldHonorWorkflowResults(nextRaw: string, prefill: WorkflowPrefill): boolean {
  if (nextRaw.startsWith("/results")) return true;
  if (!(prefill.company_url || "").trim()) return false;
  if (nextRaw.startsWith("/pipeline") || nextRaw === "/" || nextRaw.startsWith("/pricing")) {
    return false;
  }
  if ((prefill.src || "").includes("home_header")) return false;
  return true;
}

/**
 * Resolve where signup/OAuth should land.
 * Priority: explicit /results → explicit /pipeline|/pricing → matched unlock → rebuild results → /pipeline.
 */
export function resolveSignupWorkflowReturnPath(args: {
  nextRaw: string;
  prefill: WorkflowPrefill;
  matchedPipelineReturnPath?: string | null;
}): string {
  const nextRaw = (args.nextRaw || "").trim();
  // Never skip the 5-lead Results step when signup was opened for it.
  if (nextRaw.startsWith("/results")) return nextRaw;
  if (nextRaw.startsWith("/pipeline") || nextRaw.startsWith("/pricing")) return nextRaw;
  if (nextRaw === "/") return "/pipeline";
  if (args.matchedPipelineReturnPath) return args.matchedPipelineReturnPath;
  if (!shouldHonorWorkflowResults(nextRaw, args.prefill)) return "/pipeline";
  return workflowResultsPath(args.prefill, nextRaw);
}
