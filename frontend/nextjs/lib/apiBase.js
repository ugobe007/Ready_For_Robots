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

function _isMarketingHostname(hostname) {
  const h = String(hostname || '').toLowerCase();
  if (!h) return false;
  if (MARKETING_HOSTS.has(h)) return true;
  return h === 'readyforrobots.com' || h.endsWith('.readyforrobots.com');
}
/** Use same-origin only when the static app is served from the Fly app (API + static in one image). */
const API_COHOST_SUFFIXES = ['.fly.dev'];

function _hostnameFromUrlCandidate(s) {
  const t = String(s || '').trim();
  if (!t) return '';
  try {
    const u = new URL(t.includes('://') ? t : `https://${t}`);
    return u.hostname.toLowerCase();
  } catch {
    return '';
  }
}

/**
 * NEXT_PUBLIC_API_URL is sometimes set to the marketing site by mistake. That yields
 * `fetch("https://readyforrobots.com/api/...")` → static HTML → JSON parse "Unexpected token '<'".
 */
function _sanitizeEnvApiUrl(raw) {
  const trimmed = String(raw || '').trim();
  if (!trimmed) return '';
  const base = trimmed.replace(/\/$/, '');
  const host = _hostnameFromUrlCandidate(base);
  if (host && _isMarketingHostname(host)) {
    return '';
  }
  const siteRaw =
    typeof process !== 'undefined' && process.env.NEXT_PUBLIC_SITE_URL
      ? String(process.env.NEXT_PUBLIC_SITE_URL).trim()
      : '';
  if (siteRaw && base === siteRaw.replace(/\/$/, '')) {
    return '';
  }
  const siteHost = _hostnameFromUrlCandidate(siteRaw);
  if (host && siteHost && host === siteHost) {
    return '';
  }
  return base;
}

function _apiCoHostedWithPage(hostname) {
  const h = String(hostname || '').toLowerCase();
  if (!h) return false;
  return API_COHOST_SUFFIXES.some((suf) => h.endsWith(suf));
}

/**
 * HTML meta tag (set in _app.js for production) wins over a bad inlined NEXT_PUBLIC_API_URL.
 * Lets CRM/dashboard call Fly even when the marketing CDN served an old chunk.
 */
function _metaTagApiBase() {
  if (typeof document === 'undefined') return '';
  try {
    const el = document.querySelector('meta[name="rfr-api-base"]');
    const raw = el?.getAttribute('content')?.trim();
    if (!raw || !/^https?:\/\//i.test(raw)) return '';
    const cleaned = _sanitizeEnvApiUrl(raw) || raw.replace(/\/$/, '');
    const host = _hostnameFromUrlCandidate(cleaned);
    if (host && _isMarketingHostname(host)) return '';
    return cleaned.replace(/\/$/, '');
  } catch {
    return '';
  }
}

function _computeApiBase() {
  const metaFirst = _metaTagApiBase();
  if (metaFirst) {
    return metaFirst;
  }

  const envUrl =
    typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL
      ? _sanitizeEnvApiUrl(process.env.NEXT_PUBLIC_API_URL)
      : '';
  if (envUrl) {
    return envUrl;
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
    if (_isMarketingHostname(h)) {
      return DEFAULT_PRODUCTION_API;
    }
    // Preview / alternate marketing domains (e.g. *.vercel.app): same-origin would load HTML, not JSON.
    if (_apiCoHostedWithPage(h)) {
      return window.location.origin.replace(/\/$/, '');
    }
    return DEFAULT_PRODUCTION_API;
  }
  // SSG: NEXT_PUBLIC_SITE_URL is the marketing domain, not the API — do not use it as API base.
  if (typeof process !== 'undefined' && process.env.NODE_ENV === 'production') {
    return DEFAULT_PRODUCTION_API;
  }
  return 'http://127.0.0.1:8000';
}

export function getApiBase() {
  let base = _computeApiBase();
  base = String(base || '').trim().replace(/\/$/, '');
  if (!base) {
    base = DEFAULT_PRODUCTION_API;
  }
  const host = _hostnameFromUrlCandidate(base);
  if (host && _isMarketingHostname(host)) {
    base = DEFAULT_PRODUCTION_API;
  }
  return base;
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
