/** Routes whose hero / top band uses the dark navy palette (transparent header at scroll top). */
const DARK_HERO_PATHS = new Set([
  "/",
  "/pipeline",
  "/signals",
  "/robots",
  "/robots/report",
  "/pricing",
  "/results",
  "/intelligence",
  "/compare",
  "/vendor/design",
  "/experiment",
  "/jobs",
  "/newsletter",
]);

export function isDarkHeroRoute(pathname: string): boolean {
  const base = pathname.split("?")[0].split("#")[0];
  if (DARK_HERO_PATHS.has(base)) return true;
  return (
    base === "/jobs" || base.startsWith("/jobs/") || base.startsWith("/design/")
  );
}
