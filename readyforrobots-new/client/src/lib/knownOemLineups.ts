import data from "./knownOemLineups.json";

export type KnownOemRobot = {
  name: string;
  description?: string | null;
  display_class?: string | null;
};

export type KnownOemListing = {
  vendor_name: string | null;
  robots: KnownOemRobot[];
};

const LINEUP_CAP = 3;
const BY_HOST = data as Record<string, KnownOemListing>;

/** Compound public suffixes used by OEM sites. Keep in sync with app/services/robot_url_safety.py. */
const COMPOUND_SUFFIXES = new Set([
  "com.cn",
  "net.cn",
  "org.cn",
  "gov.cn",
  "ac.cn",
  "edu.cn",
  "co.uk",
  "org.uk",
  "ac.uk",
  "gov.uk",
  "co.jp",
  "or.jp",
  "ne.jp",
  "ac.jp",
  "com.au",
  "net.au",
  "org.au",
  "co.kr",
  "co.in",
  "com.tw",
  "com.hk",
  "com.br",
  "co.za",
  "com.sg",
  "co.nz",
  "com.mx",
  "co.id",
  "com.my",
  "com.vn",
  "com.tr",
  "co.th",
  "com.ar",
  "com.ua",
  "co.il",
]);

/** Registrable host from a pasted OEM URL (www stripped). */
export function hostFromOemUrl(raw: string): string {
  const text = (raw || "").trim();
  if (!text) return "";
  try {
    const url = new URL(text.includes("://") ? text : `https://${text}`);
    return (url.hostname || "").toLowerCase().replace(/^www\./, "");
  } catch {
    return text
      .toLowerCase()
      .replace(/^www\./, "")
      .split("/")[0]
      .split("?")[0]
      .trim();
  }
}

/** eTLD+1 so shop.oem.com still hits the oem.com catalog row. */
export function registrableOemHost(host: string): string {
  const labels = host.toLowerCase().replace(/^www\./, "").split(".").filter(Boolean);
  if (labels.length >= 3 && COMPOUND_SUFFIXES.has(labels.slice(-2).join("."))) {
    return labels.slice(-3).join(".");
  }
  if (labels.length >= 2) return labels.slice(-2).join(".");
  return labels.join(".");
}

function listingFromHost(host: string): KnownOemListing | null {
  const hit = BY_HOST[host];
  if (!hit?.robots?.length) return null;
  return {
    vendor_name: hit.vendor_name || null,
    robots: hit.robots.slice(0, LINEUP_CAP),
  };
}

/** Instant FIND listing for indexed manufacturers — no network. */
export function lookupKnownOem(url: string): KnownOemListing | null {
  const host = hostFromOemUrl(url);
  if (!host) return null;
  const exact = listingFromHost(host);
  if (exact) return exact;
  const root = registrableOemHost(host);
  if (root && root !== host) return listingFromHost(root);
  return null;
}
