import { getApiBase } from "@/lib/apiBase";

function postEvent(path: string, body: Record<string, unknown>) {
  fetch(`${getApiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => undefined);
}

export function trackSiteVisit(path: string) {
  postEvent("/api/track/visit", {
    path,
    referrer: typeof document !== "undefined" ? document.referrer || null : null,
  });
}

export function trackUrlScan(url: string, source?: string) {
  postEvent("/api/track/url-scan", { url, source: source || "results" });
}

export function trackRobotSearch(payload: Record<string, unknown>) {
  postEvent("/api/track/robot-search", payload);
}

export function trackRoiCalculation(payload: Record<string, unknown>) {
  postEvent("/api/track/roi-calculation", payload);
}

export function trackSupplyConversion(payload: Record<string, unknown>) {
  postEvent("/api/track/supply-conversion", payload);
}

export function trackMarketingEvent(action: string, payload: Record<string, unknown> = {}) {
  postEvent("/api/track/visit", {
    path: `/event/${action}`,
    referrer: typeof document !== "undefined" ? document.referrer || null : null,
    ...payload,
  });
}

/**
 * Robot → jobs funnel (/jobs, /jobs/{slug}).
 * Legacy /experiment redirects here.
 *
 * Two pull expressions after jobs are shown (not a single linear funnel):
 * - Access pull: job_viewed → see_all_clicked → signup_start
 * - Commercial pull: place_opened (Next from jobs) → buyer draft → pipeline / save
 *
 * Place payloads should include job_key, profile_key, persona, src.
 */
export type RobotJobsFunnelStep =
  | "experiment_view"
  | "robot_submitted"
  | "unsupported_robot"
  | "capabilities_viewed"
  | "discovery_started"
  | "discovery_complete"
  | "first_job_viewed"
  | "job_viewed"
  | "jobs_3plus_viewed"
  | "preview_complete"
  | "qualify_opened"
  | "qualify_requested"
  | "place_opened"
  | "place_buyer_opened"
  | "see_all_clicked";

export function trackRobotJobsFunnel(step: RobotJobsFunnelStep, payload: Record<string, unknown> = {}) {
  trackMarketingEvent(`rdd_${step}`, { funnel: "robot_jobs", step, ...payload });
}

/**
 * Buyer signup funnel (conversion board #20): browse → signup → activate.
 * signup_start (intent) → signup_complete (account) → first_save (activated).
 */
export type FunnelStage = "signup_start" | "signup_complete" | "first_save";

export function trackFunnelStage(stage: FunnelStage, payload: Record<string, unknown> = {}) {
  postEvent("/api/track/funnel", { stage, ...payload });
}

/** Fire an event at most once per browser (dedupes completion/activation across reloads). */
function trackFunnelOnce(stage: FunnelStage, payload: Record<string, unknown> = {}) {
  const key = `rfr_funnel_${stage}`;
  if (typeof window !== "undefined") {
    try {
      if (window.localStorage.getItem(key) === "1") return;
      window.localStorage.setItem(key, "1");
    } catch {
      /* private mode — fall through and fire (better a possible dup than a miss) */
    }
  }
  trackFunnelStage(stage, payload);
}

/**
 * Signup intent — once per browser session (sessionStorage), not every page view.
 * Reloads / OAuth round-trips no longer inflate the funnel denominator.
 */
export function trackSignupStart(payload: Record<string, unknown> = {}) {
  const key = "rfr_funnel_signup_start_session";
  if (typeof window !== "undefined") {
    try {
      if (window.sessionStorage.getItem(key) === "1") return;
      window.sessionStorage.setItem(key, "1");
    } catch {
      /* private mode — fall through */
    }
  }
  trackFunnelStage("signup_start", payload);
}

/** Account created — fired once per browser when auth first completes. */
export function trackSignupComplete(payload: Record<string, unknown> = {}) {
  trackFunnelOnce("signup_complete", payload);
}

/** Activation — fired once per browser on the user's first saved lead. */
export function trackFirstSave(payload: Record<string, unknown> = {}) {
  trackFunnelOnce("first_save", payload);
}

export function readSupplyAttribution(search: string): {
  robotCompanyId?: number;
  messageToken?: string;
  utmSource?: string;
} {
  const params = new URLSearchParams(search);
  const utmSource = params.get("utm_source") || undefined;
  const rcRaw = params.get("rc");
  const robotCompanyId = rcRaw ? Number(rcRaw) : undefined;
  const messageToken = params.get("msg") || undefined;
  if (!utmSource && !robotCompanyId && !messageToken) {
    return {};
  }
  return {
    robotCompanyId: Number.isFinite(robotCompanyId) ? robotCompanyId : undefined,
    messageToken,
    utmSource,
  };
}
