/**
 * Public GET /api/leads `limit` — keep ≤ server `LEADS_PUBLIC_MAX` (default 300).
 * Larger pulls = richer pipeline / dashboard samples for the same API.
 */
export const LEADS_PUBLIC_FETCH_LIMIT = "280";

/** Home deal-flow feed: smaller pull for faster first paint. */
export const DEAL_FLOW_LEADS_LIMIT = "40";
