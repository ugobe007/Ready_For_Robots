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

/** Instant FIND listing for indexed manufacturers — no network. */
export function lookupKnownOem(url: string): KnownOemListing | null {
  const host = hostFromOemUrl(url);
  if (!host) return null;
  const hit = BY_HOST[host];
  if (!hit?.robots?.length) return null;
  return {
    vendor_name: hit.vendor_name || null,
    robots: hit.robots.slice(0, LINEUP_CAP),
  };
}
