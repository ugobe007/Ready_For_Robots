/**
 * Backend base URL for `next.config.js` static export (`output: 'export'`).
 * Static files are served without a Node/API layer, so relative `/api/*` calls 404.
 * Set NEXT_PUBLIC_API_URL at build time to your FastAPI host (e.g. https://readyforrobots.com).
 */
export function getApiBase() {
  const envUrl =
    typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL
      ? String(process.env.NEXT_PUBLIC_API_URL).trim()
      : '';
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  if (typeof process !== 'undefined' && process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
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
