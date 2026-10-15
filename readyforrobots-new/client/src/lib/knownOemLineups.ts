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
  const labels = host
    .toLowerCase()
    .replace(/^www\./, "")
    .split(".")
    .filter(Boolean);
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
    robots: hit.robots,
  };
}

/** Instant FIND listing for indexed manufacturers — no network. Full named lineup. */
export function lookupKnownOem(url: string): KnownOemListing | null {
  const host = hostFromOemUrl(url);
  if (!host) return null;
  const exact = listingFromHost(host);
  if (exact) return exact;

  const root = registrableOemHost(host);
  if (root && root !== host) {
    const rootHit = listingFromHost(root);
    if (rootHit) return rootHit;
  }

  // Fuzzy domain key match: e.g. "sanctuary" in "sanctuary.ai" or "sanctuary-robotics.com"
  const cleanDomain = host.split(".")[0];
  if (cleanDomain && cleanDomain.length >= 3) {
    for (const [key, listing] of Object.entries(BY_HOST)) {
      const keyDomain = key.split(".")[0];
      if (keyDomain === cleanDomain && listing.robots?.length) {
        return {
          vendor_name: listing.vendor_name || null,
          robots: listing.robots,
        };
      }
    }
  }

  return null;
}

/** Path segments that name a section, not a product. */
const GENERIC_PATH_SEGMENTS = new Set([
  "robots",
  "robot",
  "products",
  "product",
  "solutions",
  "solution",
  "hardware",
  "platform",
  "models",
  "series",
  "family",
  "overview",
  "index",
  "home",
  "en",
  "zh",
  "ja",
  "ko",
  "de",
  "fr",
  "es",
]);

export type CatalogLineupProduct = {
  name: string;
  displayClass?: string | null;
  description?: string | null;
};

export type CatalogUrlDecision =
  | { kind: "named"; product: CatalogLineupProduct }
  | { kind: "choose" }
  | { kind: "unrecognized"; label: string };

function nameTokens(value: string): string[] {
  return (value || "")
    .toLowerCase()
    .replace(/[™®©]/g, "")
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function contiguous(needle: string[], hay: string[]): boolean {
  if (!needle.length || needle.length > hay.length) return false;
  for (let i = 0; i <= hay.length - needle.length; i += 1) {
    if (needle.every((token, j) => hay[i + j] === token)) return true;
  }
  return false;
}

/** Last non-generic path segment, as tokens. Empty on a homepage or catalog index. */
export function productSlugTokens(raw: string): string[] {
  const text = (raw || "").trim();
  if (!text) return [];
  let path = "";
  try {
    path = new URL(text.includes("://") ? text : `https://${text}`).pathname || "";
  } catch {
    path = text.split("?")[0].replace(/^[^/]*/, "");
  }
  const segments = path
    .split("/")
    .map(part => part.trim().toLowerCase())
    .filter(part => part && !GENERIC_PATH_SEGMENTS.has(part));
  const slug = segments[segments.length - 1] || "";
  return nameTokens(slug);
}

/** DUST-E S from dust-e-s. Single-letter tokens stay hyphenated to the word before them. */
export function labelFromSlugTokens(tokens: string[]): string {
  if (!tokens.length) return "";
  if (tokens.length >= 2 && tokens[1].length === 1) {
    const head = `${tokens[0]}-${tokens[1]}`.toUpperCase();
    const tail = tokens
      .slice(2)
      .map(token => token.toUpperCase())
      .join(" ");
    return tail ? `${head} ${tail}` : head;
  }
  return tokens.map(token => token.toUpperCase()).join(" ");
}

function matchScore(slug: string[], product: string[]): number {
  if (!slug.length || !product.length) return 0;
  if (slug.length === product.length && slug.every((token, i) => token === product[i])) {
    return 100 + product.length;
  }
  if (contiguous(product, slug)) return 80 + product.length;
  const distinctive =
    slug.length >= 2 || (slug.length === 1 && slug[0].length >= 4);
  if (distinctive && contiguous(slug, product)) return 60 + slug.length;
  return 0;
}

/**
 * A catalog product is used only when the submitted URL names it.
 * A homepage asks the operator to choose. A product path that names
 * nothing in the lineup is unrecognized — never the first sibling.
 */
export function catalogProductForSubmittedUrl(
  url: string,
  lineup: CatalogLineupProduct[]
): CatalogUrlDecision {
  const products = (lineup || []).filter(product => (product.name || "").trim());
  const slug = productSlugTokens(url);
  if (!slug.length) {
    if (products.length === 1) return { kind: "named", product: products[0] };
    return { kind: "choose" };
  }
  let best: CatalogLineupProduct | null = null;
  let bestScore = 0;
  let bestLen = 0;
  for (const product of products) {
    const tokens = nameTokens(product.name);
    const score = matchScore(slug, tokens);
    if (score > bestScore || (score === bestScore && score > 0 && tokens.length > bestLen)) {
      best = product;
      bestScore = score;
      bestLen = tokens.length;
    }
  }
  if (best && bestScore > 0) return { kind: "named", product: best };
  return { kind: "unrecognized", label: labelFromSlugTokens(slug) || "This robot" };
}
