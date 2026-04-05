/**
 * Backend base URL for static export (`output: 'export'`).
 *
 * - **`NEXT_PUBLIC_API_URL`:** use when set (local or production).
 * - **next dev:** defaults to `http://127.0.0.1:8000` so the browser calls FastAPI directly
 *   (avoids `rewrites`, which Next does not apply to static export builds and warns about).
 * - **Production static / other hosts:** set `NEXT_PUBLIC_API_URL`, or rely on `NEXT_PUBLIC_SITE_URL`
 *   when the API is on the same host as the site.
 */
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
    // Static export served from the same FastAPI host (e.g. Fly): API is same origin.
    // Without this, production builds with no NEXT_PUBLIC_API_URL fall back to readyforrobots.com
    // and every metric fetch fails (UI shows 0).
    return window.location.origin.replace(/\/$/, '');
  }
  const site =
    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_SITE_URL) ||
    'https://readyforrobots.com';
  return String(site).replace(/\/$/, '');
}

/**
 * Options for client-side fetches that must reflect current API data (static export + CDN).
 * Merge with method/body; headers are shallow-merged with Cache-Control first.
 */
export function liveFetchInit(overrides = {}) {
  const { headers: hdr, ...rest } = overrides;
  return {
    cache: 'no-store',
    ...rest,
    headers: { 'Cache-Control': 'no-cache', ...(hdr || {}) },
  };
}
