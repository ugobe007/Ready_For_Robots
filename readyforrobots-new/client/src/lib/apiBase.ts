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

/**
 * Public read surfaces (pipeline, leads list, summary) — hit Fly directly on the
 * marketing domain. Same-origin /api rewrites add 2–5s+ latency per request.
 */
export function getPublicReadApiBase(): string {
  if (typeof window !== "undefined") {
    const h = window.location.hostname;
    if (_isMarketingHostname(h)) {
      return DEFAULT_PRODUCTION_API;
    }
  }
  return getApiBase();
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
    // Git-connected Vercel previews. Same-origin /api/* is rewritten to Fly
    // (vercel.json) so Jobs works without adding each preview host to CORS.
    if (h.endsWith(".vercel.app")) {
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

/** Public cached surfaces (pipeline, newsletter) — allow CDN/browser stale-while-revalidate. */
export function publicFetchInit(overrides: RequestInit = {}): RequestInit {
  const { headers: hdr, ...rest } = overrides;
  return {
    mode: "cors",
    ...rest,
    headers: { ...(hdr as Record<string, string>) },
  };
}

const SESSION_CACHE_PREFIX = "rr_surface_v1:";

export type SessionCacheEntry<T> = { ts: number; data: T };

export function readSessionCache<T>(key: string, maxAgeMs: number): T | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(`${SESSION_CACHE_PREFIX}${key}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SessionCacheEntry<T>;
    if (!parsed?.data || Date.now() - parsed.ts > maxAgeMs) return null;
    return parsed.data;
  } catch {
    return null;
  }
}

export function writeSessionCache<T>(key: string, data: T): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(
      `${SESSION_CACHE_PREFIX}${key}`,
      JSON.stringify({ ts: Date.now(), data }),
    );
  } catch {
    /* quota or private mode */
  }
}

/** Session first, then localStorage — instant paint on repeat visits. */
export function readSurfaceCache<T>(key: string, maxAgeMs: number): SessionCacheEntry<T> | null {
  if (typeof window === "undefined") return null;
  try {
    for (const store of [window.sessionStorage, window.localStorage]) {
      const raw = store.getItem(`${SESSION_CACHE_PREFIX}${key}`);
      if (!raw) continue;
      const parsed = JSON.parse(raw) as SessionCacheEntry<T>;
      if (!parsed?.data || Date.now() - parsed.ts > maxAgeMs) continue;
      return parsed;
    }
  } catch {
    /* quota or private mode */
  }
  return null;
}

export function writeSurfaceCache<T>(key: string, data: T): void {
  writeSessionCache(key, data);
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      `${SESSION_CACHE_PREFIX}${key}`,
      JSON.stringify({ ts: Date.now(), data }),
    );
  } catch {
    /* quota or private mode */
  }
}

/** Abort slow proxy/API calls so pages can fall back instead of spinning forever. */
export async function fetchWithTimeout(
  url: string,
  init: RequestInit = {},
  timeoutMs = 8_000,
  opts?: { publicCache?: boolean },
): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  const onParentAbort = () => ctrl.abort();
  init.signal?.addEventListener("abort", onParentAbort);
  if (init.signal?.aborted) ctrl.abort();
  const { signal: _ignored, ...rest } = init;
  const baseInit = opts?.publicCache ? publicFetchInit(rest) : liveFetchInit(rest);
  try {
    return await fetch(url, { ...baseInit, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
    init.signal?.removeEventListener("abort", onParentAbort);
  }
}

/** Wi‑Fi/VPN changes and other browser network blips — safe to retry briefly. */
export function isTransientFetchError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === "AbortError") return true;
  if (err instanceof TypeError) return true;
  const msg = err instanceof Error ? err.message : String(err);
  return /network|failed to fetch|load failed|aborted|timeout/i.test(msg);
}

export async function fetchWithTimeoutRetry(
  url: string,
  init: RequestInit = {},
  timeoutMs = 8_000,
  opts?: { publicCache?: boolean; retries?: number; retryDelayMs?: number },
): Promise<Response> {
  const retries = opts?.retries ?? 2;
  const retryDelayMs = opts?.retryDelayMs ?? 1200;
  let lastErr: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fetchWithTimeout(url, init, timeoutMs, opts);
    } catch (err) {
      lastErr = err;
      if (attempt >= retries || !isTransientFetchError(err)) throw err;
      await new Promise((resolve) => window.setTimeout(resolve, retryDelayMs * (attempt + 1)));
    }
  }
  throw lastErr;
}
