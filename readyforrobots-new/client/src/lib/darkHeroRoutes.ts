/** Routes whose hero / top band uses the dark navy palette (transparent header at scroll top). */
const DARK_HERO_PATHS = new Set([
  "/",
  "/pipeline",
  "/signals",
  "/robots",
  "/pricing",
  "/results",
  "/how-it-works",
  "/intelligence",
  "/compare",
]);

export function isDarkHeroRoute(pathname: string): boolean {
  const base = pathname.split("?")[0].split("#")[0];
  return DARK_HERO_PATHS.has(base);
}
