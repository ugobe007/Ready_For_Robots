import data from "./knownDistributorLineups.json";
import { hostFromOemUrl, registrableOemHost } from "./knownOemLineups";

export type DistributorProductItem = {
  brand: string;
  name: string;
  description?: string | null;
  display_class?: string | null;
};

export type KnownDistributorListing = {
  distributor_name: string;
  domain: string;
  territory?: string | null;
  supported_brands: string[];
  robot_categories: string[];
  services?: string[];
  product_mix: DistributorProductItem[];
};

const BY_HOST = data as Record<string, KnownDistributorListing>;

function listingFromHost(host: string): KnownDistributorListing | null {
  const hit = BY_HOST[host];
  if (!hit?.product_mix?.length) return null;
  return hit;
}

/** Look up a known robotics distributor / VAR by URL or domain host. */
export function lookupKnownDistributor(url: string): KnownDistributorListing | null {
  const host = hostFromOemUrl(url);
  if (!host) return null;
  const exact = listingFromHost(host);
  if (exact) return exact;

  const root = registrableOemHost(host);
  if (root && root !== host) {
    const rootHit = listingFromHost(root);
    if (rootHit) return rootHit;
  }

  // Fuzzy domain key match (e.g. "crossco" in "crossco.com")
  const cleanDomain = host.split(".")[0];
  if (cleanDomain && cleanDomain.length >= 3) {
    for (const [key, listing] of Object.entries(BY_HOST)) {
      const keyDomain = key.split(".")[0];
      if (keyDomain === cleanDomain && listing.product_mix?.length) {
        return listing;
      }
    }
  }

  return null;
}

/** Search all indexed distributors that distribute a given OEM brand name (e.g. "Universal Robots" or "MiR"). */
export function searchDistributorsForBrand(brandName: string): KnownDistributorListing[] {
  const target = (brandName || "").toLowerCase().trim();
  if (!target) return [];
  const matches: KnownDistributorListing[] = [];
  for (const listing of Object.values(BY_HOST)) {
    const hasBrand = listing.supported_brands.some(b => b.toLowerCase().includes(target));
    if (hasBrand) {
      matches.push(listing);
    }
  }
  return matches;
}

/** Get all distributors indexed in the lookup table. */
export function listKnownDistributors(): KnownDistributorListing[] {
  return Object.values(BY_HOST);
}
