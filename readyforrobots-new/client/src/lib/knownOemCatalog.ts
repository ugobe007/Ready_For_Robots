/**
 * Evidence catalog for FIND named SKUs.
 * Named SKUs from knownOemLineups only. No invented models.
 */
import data from "./knownOemLineups.json";
import type { KnownOemListing } from "./knownOemLineups";
import {
  configurationClassForLookup,
  normalizeRobotClass,
} from "./jobsWorkflow";

export type CatalogSku = {
  vendorName: string;
  host: string;
  findUrl: string;
  name: string;
  displayClass: string | null;
};

const BY_HOST = data as Record<string, KnownOemListing>;

function findTileForClass(raw?: string | null): string | null {
  const cfg = configurationClassForLookup(raw);
  if (cfg) {
    const tile = normalizeRobotClass(cfg) || cfg;
    return tile;
  }
  return normalizeRobotClass(raw);
}

export function listKnownOemCatalog(): CatalogSku[] {
  const out: CatalogSku[] = [];
  const seen = new Set<string>();
  for (const [host, listing] of Object.entries(BY_HOST)) {
    const vendor = (listing.vendor_name || host).trim();
    const findUrl = `https://${host}/`;
    for (const robot of listing.robots || []) {
      const name = (robot.name || "").trim();
      if (!name) continue;
      const key = `${host}|${name.toLowerCase()}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        vendorName: vendor,
        host,
        findUrl,
        name,
        displayClass: robot.display_class || null,
      });
    }
  }
  return out;
}

export function catalogSkusForClass(classId: string): CatalogSku[] {
  const want = (classId || "").trim();
  if (!want) return [];
  return listKnownOemCatalog().filter(sku => {
    const tile = findTileForClass(sku.displayClass);
    return tile === want;
  });
}

export function catalogSkuMatchesClass(
  sku: CatalogSku,
  classId?: string | null
): boolean {
  const want = (classId || "").trim();
  if (!want) return true;
  return findTileForClass(sku.displayClass) === want;
}
