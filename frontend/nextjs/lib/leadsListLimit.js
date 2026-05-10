/**
 * GET /api/leads `limit` — keep ≤ server LEADS_PUBLIC_MAX (default 300 on current FastAPI).
 * Next.js marketing + dashboard use this so readyforrobots.com is not stuck at legacy 50-row loads.
 */
export const LEADS_LIST_LIMIT = '280';
