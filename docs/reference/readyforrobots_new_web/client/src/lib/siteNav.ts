/**
 * Primary navigation for the Vite marketing shell.
 * Paths mirror `frontend/nextjs/pages` so cutover stays predictable.
 */

export type NavItem = { label: string; href: string };

/** Top bar — shown on every page */
export const PRIMARY_NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Pipeline", href: "/pipeline" },
  { label: "Signals", href: "/signals" },
  { label: "Markets", href: "/markets" },
  { label: "ROI", href: "/roi-calculator" },
];

/** Footer — product + company */
export const FOOTER_NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Pipeline", href: "/pipeline" },
  { label: "CRM", href: "/crm" },
  { label: "Market insights", href: "/market-insights" },
  { label: "Signals", href: "/signals" },
  { label: "Markets", href: "/markets" },
  { label: "Pipeline results", href: "/pipeline-results" },
  { label: "Pipeline health", href: "/pipeline-health" },
  { label: "Browse leads", href: "/dashboard" },
  { label: "Newsletter", href: "/newsletter" },
  { label: "ROI calculator", href: "/roi-calculator" },
  { label: "About", href: "/about" },
];
