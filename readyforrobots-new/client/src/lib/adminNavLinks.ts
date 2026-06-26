export type AdminNavLink = {
  label: string;
  href: string;
  /** Shown in compact header dropdown only */
  shortLabel?: string;
};

export type AdminNavSection = {
  label: string;
  links: AdminNavLink[];
};

/** Canonical workspace navigation — keep AdminNav and Header dropdown in sync. */
export const ADMIN_WORKSPACE_SECTIONS: AdminNavSection[] = [
  {
    label: "Command",
    links: [
      { label: "Admin", href: "/admin", shortLabel: "Admin dashboard" },
      { label: "Prospects", href: "/admin/prospects", shortLabel: "Admin prospects" },
      { label: "Pipeline", href: "/pipeline" },
      { label: "Workflow", href: "/sales-workflow" },
    ],
  },
  {
    label: "Sales",
    links: [
      { label: "Buyer CRM", href: "/crm" },
      { label: "Inbox", href: "/inbox" },
      { label: "Calendar", href: "/calendar" },
      { label: "Sales Console", href: "/sales-console" },
    ],
  },
  {
    label: "Growth",
    links: [
      { label: "Supply Pipeline", href: "/supply-pipeline" },
      { label: "Marketplace", href: "/marketplace" },
      { label: "Studio", href: "/social" },
      { label: "Integrations", href: "/integrations" },
    ],
  },
  {
    label: "Account",
    links: [{ label: "Profile", href: "/profile" }],
  },
];

export const ADMIN_WORKSPACE_LINKS: AdminNavLink[] = ADMIN_WORKSPACE_SECTIONS.flatMap(
  (section) => section.links,
);

function normalizePath(path: string): string {
  if (path.startsWith("/readyforrobots")) {
    return path.slice("/readyforrobots".length) || "/";
  }
  return path;
}

/** Active route matching for workspace pages (supports /readyforrobots/* aliases). */
export function isAdminNavActive(currentPath: string, href: string): boolean {
  const path = normalizePath(currentPath);
  const target = href.split("#", 1)[0];
  const hash = typeof window !== "undefined" ? window.location.hash : "";

  if (target === "/sales-workflow") return path === "/sales-workflow";
  if (href.includes("#workflow")) return path === "/admin" && hash === "#workflow";
  if (target === "/admin") return path === "/admin" && hash !== "#workflow";
  if (target === "/admin/prospects") return path === "/admin/prospects";
  if (target === "/pipeline") return path === "/pipeline" || path === "/admin/prospects";
  if (target === "/integrations") return path === "/integrations" || path.startsWith("/integrations/");

  return path === target || path.startsWith(`${target}/`);
}

export function isAdminWorkspacePath(path: string): boolean {
  const normalized = normalizePath(path);
  return ADMIN_WORKSPACE_LINKS.some((link) => isAdminNavActive(normalized, link.href));
}
