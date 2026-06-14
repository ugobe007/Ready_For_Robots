export const HOMEPAGE_SPOTLIGHT_CACHE_KEY = "homepage_spotlight_leads_v2";
/** Match server daily edition — rolls at 6am America/Los_Angeles. */
export const HOMEPAGE_SPOTLIGHT_CACHE_TTL_MS = 24 * 60 * 60 * 1000;

const DOMAIN_ENTITY_NAME_KEYS: Record<string, string> = {
  "jal.co.jp": "japan airlines",
  "choicehotels.com": "choice hotels",
};

const NAME_ENTITY_ALIASES: Record<string, string> = {
  jal: "japan airlines",
  "japan airline": "japan airlines",
};

function normalizeWebsiteDomain(website?: string | null): string {
  const raw = (website || "").trim().toLowerCase();
  if (!raw) return "";
  try {
    const host = raw.includes("://") ? new URL(raw).hostname : raw.split("/")[0].split("?")[0];
    return host.replace(/^www\./, "");
  } catch {
    return raw.replace(/^www\./, "").split("/")[0].split("?")[0];
  }
}

function normalizeCompanyNameKey(name?: string | null): string {
  let s = (name || "").trim().toLowerCase();
  if (!s) return "";
  s = s.replace(/[^\w\s&'-]/g, " ");
  s = s.replace(/\s+/g, " ").trim();
  s = s
    .replace(
      /(?:,?\s*(?:inc\.?|llc\.?|ltd\.?|corp\.?|corporation|co\.?|plc\.?|gmbh|bv|nv|ag|sa|srl)|\s+(?:international|holdings|group|enterprises))$/gi,
      "",
    )
    .trim();
  s = s.replace(/\bairline\b/g, "airlines");
  s = s.replace(/\s+/g, " ").trim();
  return NAME_ENTITY_ALIASES[s] || s;
}

function companyEntityDedupeKeys(lead: {
  company_name?: string;
  website?: string | null;
  website_domain?: string | null;
}): Set<string> {
  const keys = new Set<string>();
  const nameKey = normalizeCompanyNameKey(lead.company_name);
  if (nameKey) keys.add(`name:${nameKey}`);
  const dom = normalizeWebsiteDomain(lead.website) || (lead.website_domain || "").trim().toLowerCase();
  if (dom) {
    keys.add(`dom:${dom}`);
    const mapped = DOMAIN_ENTITY_NAME_KEYS[dom];
    if (mapped) keys.add(`name:${mapped}`);
  }
  return keys;
}

/** Collapse duplicate buyer rows for homepage spotlight / sales panel rotation. */
export function dedupeHomepageLeads<
  T extends { id?: number; company_name?: string; website?: string | null; website_domain?: string | null },
>(leads: T[] | null | undefined): T[] {
  if (!Array.isArray(leads)) return [];
  const seen = new Set<string>();
  return leads.filter((lead) => {
    const keys = companyEntityDedupeKeys(lead);
    if (!keys.size) return Boolean(lead.company_name || lead.id != null);
    for (const key of keys) {
      if (seen.has(key)) return false;
    }
    for (const key of keys) seen.add(key);
    return true;
  });
}
