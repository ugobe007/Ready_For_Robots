/**
 * Backend base URL for static export (`output: 'export'`).
 *
 * - **`NEXT_PUBLIC_API_URL`:** preferred — Docker/Fly `[build.args]` and local `.env.local`.
 * - **next dev:** `http://127.0.0.1:8000` (rewrites proxy `/api` to FastAPI).
 * - **Marketing site** (`readyforrobots.com`): HTML is static-only; if the env var is missing
 *   from the bundle, still call the Fly API — never use `window.location.origin` here.
 * - **Same host as API** (`ready-2-robot.fly.dev`): same origin.
 */
const MARKETING_HOSTS = new Set(['readyforrobots.com', 'www.readyforrobots.com']);
/** When env is not inlined; keep in sync with Fly app URL. */
const DEFAULT_PRODUCTION_API = 'https://ready-2-robot.fly.dev';

export function getApiBase() {
  const envUrl =
    typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL
      ? String(process.env.NEXT_PUBLIC_API_URL).trim()
      : '';
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  const isDev =
    typeof process !== 'undefined' && process.env.NODE_ENV === 'development';
  if (isDev) {
    return 'http://127.0.0.1:8000';
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    if (MARKETING_HOSTS.has(h)) {
      return DEFAULT_PRODUCTION_API;
    }
    return window.location.origin.replace(/\/$/, '');
  }
  // SSG: NEXT_PUBLIC_SITE_URL is the marketing domain, not the API — do not use it as API base.
  if (typeof process !== 'undefined' && process.env.NODE_ENV === 'production') {
    return DEFAULT_PRODUCTION_API;
  }
  return 'http://127.0.0.1:8000';
}

/**
 * Options for client-side fetches that must reflect current API data (static export + CDN).
 * Merge with method/body; headers are shallow-merged with Cache-Control first.
 */
export function liveFetchInit(overrides = {}) {
  const { headers: hdr, ...rest } = overrides;
  return {
    cache: 'no-store',
    mode: 'cors',
    ...rest,
    headers: { 'Cache-Control': 'no-cache', ...(hdr || {}) },
  };
}
