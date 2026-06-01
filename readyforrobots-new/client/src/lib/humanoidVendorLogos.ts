/** Resolve vendor logo paths for humanoid index panels (transparent PNGs in /public/logos/vendors). */

export type VendorLogoMeta = {
  src: string;
  /** When true, logo is already tinted for dark UI — skip mono filter. */
  tinted?: boolean;
};

/** Simple-icons slugs — CDN fallback when bundled PNG is missing. */
const SIMPLE_ICON_FALLBACK: Record<string, string> = {
  tesla: "tesla",
  toyota: "toyota",
  honda: "honda",
  xiaomi: "xiaomi",
  nvidia: "nvidia",
  hyundai: "hyundai",
  samsung: "samsung",
  intel: "intel",
  amazon: "amazon",
  apple: "apple",
  google: "google",
  microsoft: "microsoft",
  meta: "meta",
  byd: "byd",
  xpeng: "xpeng",
};

/** Match scripts/sync_humanoid_vendor_logos.py vendor_key(). */
export function vendorKeyFromName(vendor: string): string {
  let base = vendor.split("(")[0].trim().toLowerCase();
  base = base.replace(/\brobotics?\b/g, "").trim();
  return base.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function resolveHumanoidLogo(opts: {
  vendor: string;
  modelSlug?: string;
  productUrl?: string;
  imageUrl?: string | null;
}): VendorLogoMeta | null {
  if (opts.imageUrl) {
    return { src: opts.imageUrl, tinted: true };
  }

  const key = vendorKeyFromName(opts.vendor);
  return { src: `/logos/vendors/${key}.png`, tinted: true };
}

export function resolveHumanoidLogoFallbackCdn(vendor: string): VendorLogoMeta | null {
  const key = vendorKeyFromName(vendor);
  const slug = SIMPLE_ICON_FALLBACK[key];
  if (slug) {
    return {
      src: `https://cdn.simpleicons.org/${slug}/c4b5fd`,
      tinted: true,
    };
  }
  return null;
}

export function vendorInitials(vendor: string): string {
  const words = vendor
    .replace(/\([^)]*\)/g, "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return vendor.slice(0, 2).toUpperCase();
}

export function vendorHue(vendor: string): number {
  let hash = 0;
  for (let i = 0; i < vendor.length; i += 1) {
    hash = vendor.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
}
