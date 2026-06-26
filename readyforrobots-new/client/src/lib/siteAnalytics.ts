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
