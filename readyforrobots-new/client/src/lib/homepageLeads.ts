export const HOMEPAGE_SPOTLIGHT_CACHE_KEY = "homepage_spotlight_leads_v1";
export const HOMEPAGE_SPOTLIGHT_CACHE_TTL_MS = 30 * 60 * 1000;

/** Collapse duplicate buyer rows for homepage spotlight / sales panel rotation. */
export function dedupeHomepageLeads<
  T extends { id?: number; company_name?: string; website?: string | null },
>(leads: T[] | null | undefined): T[] {
  if (!Array.isArray(leads)) return [];
  const seenNames = new Set<string>();
  const seenIds = new Set<number>();
  return leads.filter((lead) => {
    const id = lead.id;
    if (id != null && seenIds.has(id)) return false;
    const nameKey = (lead.company_name || "").trim().toLowerCase().replace(/\s+/g, " ");
    if (nameKey && seenNames.has(nameKey)) return false;
    if (id != null) seenIds.add(id);
    if (nameKey) seenNames.add(nameKey);
    return Boolean(nameKey || id != null);
  });
}
