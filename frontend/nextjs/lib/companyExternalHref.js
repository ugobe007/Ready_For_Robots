/**
 * Best URL to open for a lead’s company: API `primary_link_url` (site or evidence),
 * else `website`, else a DuckDuckGo search so the name is always link-out capable.
 *
 * Ingest quality: optional DNS/Wikidata checks on the FastAPI side — set
 * `COMPANY_NAME_DNS_HTTPS_VERIFY=1` and (stricter) `COMPANY_NAME_DNS_HTTPS_STRICT=1`
 * in production so names without a plausible domain footprint can be rejected
 * at insert time (see `app/services/company_validator.py`).
 */
export function companyExternalHref(lead) {
  if (!lead || typeof lead !== 'object') return null;
  const direct = lead.primary_link_url || lead.website;
  if (direct && /^https?:\/\//i.test(String(direct).trim())) {
    return String(direct).trim();
  }
  const name = String(lead.company_name || '').trim();
  if (!name) return null;
  return `https://duckduckgo.com/?q=${encodeURIComponent(`${name} company`)}`;
}

/** True when we only have a search URL (no real site, article, or OpenAI-inferred URL from API). */
export function isWebSearchOnlyHref(lead) {
  if (!lead?.primary_link_url && !lead?.website) return true;
  return false;
}
