import { fetchWithTimeoutRetry, getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";

export const HOMEPAGE_SPOTLIGHT_CACHE_KEY = "homepage_spotlight_leads_v2";
/** Match server daily edition — rolls at 6am America/Los_Angeles. */
export const HOMEPAGE_SPOTLIGHT_CACHE_TTL_MS = 24 * 60 * 60 * 1000;

const HOMEPAGE_POOL_TIMEOUT_MS = 8_000;
const HOMEPAGE_POOL_COOLDOWN_MS = 90 * 1000;
const HOMEPAGE_POOL_BREAKER_OPEN_MS = 45 * 1000;
const HOMEPAGE_POOL_BREAKER_FAIL_STREAK = 3;

type HomepagePoolResult = {
  leads: Array<{ id?: number; company_name?: string; website?: string | null; website_domain?: string | null }>;
  live: boolean;
  summary?: { total?: number; hot?: number };
};

let homepagePoolInFlight: Promise<HomepagePoolResult> | null = null;
let homepagePoolLastSuccess: HomepagePoolResult | null = null;
let homepagePoolCooldownUntil = 0;
let homepagePoolBreakerOpenUntil = 0;
let homepagePoolFailStreak = 0;
const homepagePoolTelemetry = {
  attempts: 0,
  successes: 0,
  failures: 0,
  inflightDedupes: 0,
  cooldownSkips: 0,
  breakerOpenCount: 0,
  lastError: "",
};

function publishHomepagePoolTelemetry() {
  if (typeof window === "undefined") return;
  const attempts = homepagePoolTelemetry.attempts;
  const failures = homepagePoolTelemetry.failures;
  (window as Window & { __rfrHomepageLeadPoolTelemetry?: Record<string, unknown> }).__rfrHomepageLeadPoolTelemetry = {
    ...homepagePoolTelemetry,
    failRate: attempts > 0 ? Number((failures / attempts).toFixed(3)) : 0,
    breakerOpen: Date.now() < homepagePoolBreakerOpenUntil,
    breakerOpenForMs: Math.max(0, homepagePoolBreakerOpenUntil - Date.now()),
    cooldownForMs: Math.max(0, homepagePoolCooldownUntil - Date.now()),
    failStreak: homepagePoolFailStreak,
    inFlight: Boolean(homepagePoolInFlight),
    lastSuccessLeadCount: homepagePoolLastSuccess?.leads?.length ?? 0,
  };
}

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

/** Merge homepage spotlight + HOT feed for hero / live pipeline rotation. */
export async function fetchHomepageLeadPool<
  T extends { id?: number; company_name?: string; website?: string | null; website_domain?: string | null },
>(fallback: T[]): Promise<{ leads: T[]; live: boolean; summary?: { total?: number; hot?: number } }> {
  const toTyped = (result: HomepagePoolResult | null): { leads: T[]; live: boolean; summary?: { total?: number; hot?: number } } => {
    if (!result || !Array.isArray(result.leads) || result.leads.length === 0) {
      return { leads: fallback, live: false };
    }
    return { leads: result.leads as T[], live: result.live, summary: result.summary };
  };

  if (homepagePoolInFlight) {
    homepagePoolTelemetry.inflightDedupes += 1;
    publishHomepagePoolTelemetry();
    const shared = await homepagePoolInFlight;
    return toTyped(shared);
  }

  const now = Date.now();
  if (now < homepagePoolBreakerOpenUntil || now < homepagePoolCooldownUntil) {
    homepagePoolTelemetry.cooldownSkips += 1;
    publishHomepagePoolTelemetry();
    return toTyped(homepagePoolLastSuccess);
  }

  homepagePoolTelemetry.attempts += 1;
  publishHomepagePoolTelemetry();

  const run = (async (): Promise<HomepagePoolResult> => {
    try {
      const [homepageRes, hotRes] = await Promise.all([
        fetchWithTimeoutRetry(
          `${getPublicReadApiBase()}/api/leads/homepage`,
          liveFetchInit(),
          HOMEPAGE_POOL_TIMEOUT_MS,
          { retries: 1, retryDelayMs: 800 },
        ),
        fetchWithTimeoutRetry(
          `${getPublicReadApiBase()}/api/leads?limit=24&tier=HOT&sort=score&exclude_junk=true`,
          liveFetchInit(),
          HOMEPAGE_POOL_TIMEOUT_MS,
          { retries: 1, retryDelayMs: 800 },
        ),
      ]);

      const merged: HomepagePoolResult["leads"] = [];
      let summary: { total?: number; hot?: number } | undefined;
      if (homepageRes.ok) {
        const data = (await homepageRes.json()) as {
          hotLeads?: HomepagePoolResult["leads"];
          summary?: { total?: number; hot?: number };
        };
        if (Array.isArray(data.hotLeads)) merged.push(...data.hotLeads);
        if (data.summary) summary = data.summary;
      }
      if (hotRes.ok) {
        const hotData = await hotRes.json();
        if (Array.isArray(hotData)) merged.push(...(hotData as HomepagePoolResult["leads"]));
      }
      const deduped = dedupeHomepageLeads(merged);
      if (!deduped.length) throw new Error("homepage pool returned no leads");
      const result: HomepagePoolResult = { leads: deduped, live: true, summary };
      homepagePoolLastSuccess = result;
      homepagePoolFailStreak = 0;
      homepagePoolCooldownUntil = 0;
      homepagePoolTelemetry.successes += 1;
      homepagePoolTelemetry.lastError = "";
      publishHomepagePoolTelemetry();
      return result;
    } catch (e) {
      homepagePoolTelemetry.failures += 1;
      homepagePoolTelemetry.lastError = e instanceof Error ? e.message : "homepage pool fetch failed";
      homepagePoolFailStreak += 1;
      homepagePoolCooldownUntil = Date.now() + HOMEPAGE_POOL_COOLDOWN_MS;
      if (homepagePoolFailStreak >= HOMEPAGE_POOL_BREAKER_FAIL_STREAK) {
        homepagePoolBreakerOpenUntil = Date.now() + HOMEPAGE_POOL_BREAKER_OPEN_MS;
        homepagePoolTelemetry.breakerOpenCount += 1;
        homepagePoolFailStreak = 0;
      }
      publishHomepagePoolTelemetry();
      return homepagePoolLastSuccess ?? { leads: fallback, live: false };
    } finally {
      homepagePoolInFlight = null;
    }
  })();

  homepagePoolInFlight = run;
  const result = await run;
  return toTyped(result);
}
