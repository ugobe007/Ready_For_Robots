/**
 * FastAPI base URL for the Ready For Robots backend (same contract as frontend/nextjs/lib/apiBase.js).
 * Build: set VITE_PUBLIC_API_URL. Runtime: prefers <meta name="rfr-api-base"> when present.
 */
const DEFAULT_PRODUCTION_API = "https://ready-2-robot.fly.dev";

const MARKETING_HOSTS = new Set(["readyforrobots.com", "www.readyforrobots.com"]);

function _hostnameFromUrlCandidate(s: string): string {
  const t = String(s || "").trim();
  if (!t) return "";
  try {
    const u = new URL(t.includes("://") ? t : `https://${t}`);
    return u.hostname.toLowerCase();
  } catch {
    return "";
  }
}

function _isMarketingHostname(hostname: string): boolean {
  const h = String(hostname || "").toLowerCase();
  if (!h) return false;
  if (MARKETING_HOSTS.has(h)) return true;
  return h.endsWith(".readyforrobots.com");
}

function _sanitizeEnvApiUrl(raw: string): string {
  const trimmed = String(raw || "").trim().replace(/\/$/, "");
  const host = _hostnameFromUrlCandidate(trimmed);
  if (host && _isMarketingHostname(host)) return "";
  return trimmed;
}

function _metaTagApiBase(): string {
  if (typeof document === "undefined") return "";
  try {
    const el = document.querySelector('meta[name="rfr-api-base"]');
    const raw = el?.getAttribute("content")?.trim();
    if (!raw || !/^https?:\/\//i.test(raw)) return "";
    const cleaned = _sanitizeEnvApiUrl(raw) || raw.replace(/\/$/, "");
    const host = _hostnameFromUrlCandidate(cleaned);
    if (host && _isMarketingHostname(host)) return "";
    return cleaned.replace(/\/$/, "");
  } catch {
    return "";
  }
}

/** Long-running endpoints (PDF, social queue) — bypass Vercel ~120s proxy timeout. */
export function getDirectApiBase(): string {
  return DEFAULT_PRODUCTION_API;
}

export function getApiBase(): string {
  // Marketing site (Vercel): same-origin /api/* is proxied to Fly — avoids cross-origin failures.
  if (typeof window !== "undefined") {
    const h = window.location.hostname;
    if (_isMarketingHostname(h)) {
      return window.location.origin.replace(/\/$/, "");
    }
    if (h === "localhost" || h === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }
    if (h.endsWith(".fly.dev")) {
      return window.location.origin.replace(/\/$/, "");
    }
  }

  const metaFirst = _metaTagApiBase();
  if (metaFirst) return metaFirst;

  const envUrl = _sanitizeEnvApiUrl(import.meta.env.VITE_PUBLIC_API_URL || "");
  if (envUrl) return envUrl;

  if (import.meta.env.DEV) return "http://127.0.0.1:8000";

  return DEFAULT_PRODUCTION_API;
}

export function liveFetchInit(overrides: RequestInit = {}): RequestInit {
  const { headers: hdr, ...rest } = overrides;
  return {
    cache: "no-store",
    mode: "cors",
    ...rest,
    headers: { "Cache-Control": "no-cache", ...(hdr as Record<string, string>) },
  };
}

/** Abort slow proxy/API calls so pages can fall back instead of spinning forever. */
export async function fetchWithTimeout(
  url: string,
  init: RequestInit = {},
  timeoutMs = 8_000,
): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(url, { ...liveFetchInit(init), signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}
