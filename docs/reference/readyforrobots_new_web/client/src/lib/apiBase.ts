/**
 * FastAPI base URL for the Vite app (same rules as `frontend/nextjs/lib/apiBase.js`).
 *
 * - **`import.meta.env.VITE_API_URL`** in `.env` / `.env.local`
 * - **Dev:** `http://127.0.0.1:8000` when page is localhost
 * - **Production static host:** Fly API default
 * - **`<meta name="rfr-api-base" content="https://…">`** in `index.html` overrides a bad bundle env
 */

const MARKETING_HOSTS = new Set(["readyforrobots.com", "www.readyforrobots.com"]);
const DEFAULT_PRODUCTION_API = "https://ready-2-robot.fly.dev";
const API_COHOST_SUFFIXES = [".fly.dev"];

function hostnameFromUrlCandidate(s: string): string {
  const t = String(s || "").trim();
  if (!t) return "";
  try {
    const u = new URL(t.includes("://") ? t : `https://${t}`);
    return u.hostname.toLowerCase();
  } catch {
    return "";
  }
}

function isMarketingHostname(hostname: string): boolean {
  const h = String(hostname || "").toLowerCase();
  if (!h) return false;
  if (MARKETING_HOSTS.has(h)) return true;
  return h === "readyforrobots.com" || h.endsWith(".readyforrobots.com");
}

function sanitizeEnvApiUrl(raw: string): string {
  const trimmed = String(raw || "").trim();
  if (!trimmed) return "";
  const base = trimmed.replace(/\/$/, "");
  const host = hostnameFromUrlCandidate(base);
  if (host && isMarketingHostname(host)) return "";
  return base;
}

function metaTagApiBase(): string {
  if (typeof document === "undefined") return "";
  try {
    const el = document.querySelector('meta[name="rfr-api-base"]');
    const raw = el?.getAttribute("content")?.trim();
    if (!raw || !/^https?:\/\//i.test(raw)) return "";
    const cleaned = sanitizeEnvApiUrl(raw) || raw.replace(/\/$/, "");
    const host = hostnameFromUrlCandidate(cleaned);
    if (host && isMarketingHostname(host)) return "";
    return cleaned.replace(/\/$/, "");
  } catch {
    return "";
  }
}

function apiCoHostedWithPage(hostname: string): boolean {
  const h = String(hostname || "").toLowerCase();
  if (!h) return false;
  return API_COHOST_SUFFIXES.some((suf) => h.endsWith(suf));
}

function computeApiBase(): string {
  const metaFirst = metaTagApiBase();
  if (metaFirst) return metaFirst;

  const envUrl = sanitizeEnvApiUrl(String(import.meta.env.VITE_API_URL || ""));
  if (envUrl) return envUrl;

  if (import.meta.env.DEV) {
    // Match page hostname so origin (e.g. localhost:5173) aligns with API host for CORS.
    if (typeof window !== "undefined") {
      const h = window.location.hostname;
      if (h === "127.0.0.1") return "http://127.0.0.1:8000";
    }
    return "http://localhost:8000";
  }
  if (typeof window !== "undefined") {
    const h = window.location.hostname;
    if (h === "localhost" || h === "127.0.0.1") {
      return "http://localhost:8000";
    }
    if (isMarketingHostname(h)) {
      return DEFAULT_PRODUCTION_API;
    }
    if (apiCoHostedWithPage(h)) {
      return window.location.origin.replace(/\/$/, "");
    }
    return DEFAULT_PRODUCTION_API;
  }
  if (import.meta.env.PROD) {
    return DEFAULT_PRODUCTION_API;
  }
  return "http://127.0.0.1:8000";
}

export function getApiBase(): string {
  let base = computeApiBase();
  base = String(base || "")
    .trim()
    .replace(/\/$/, "");
  if (!base) base = DEFAULT_PRODUCTION_API;
  const host = hostnameFromUrlCandidate(base);
  if (host && isMarketingHostname(host)) {
    base = DEFAULT_PRODUCTION_API;
  }
  return base;
}

export function liveFetchInit(overrides: RequestInit = {}): RequestInit {
  const { headers: hdr, ...rest } = overrides;
  return {
    cache: "no-store",
    mode: "cors",
    ...rest,
    headers: { "Cache-Control": "no-cache", ...(hdr || {}) },
  };
}
