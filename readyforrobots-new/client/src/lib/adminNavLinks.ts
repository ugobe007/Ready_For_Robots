export type AdminNavLink = {
  label: string;
  href: string;
  /** Shown in compact header dropdown only */
  shortLabel?: string;
  /** Hidden unless the signed-in user is in ADMIN_EMAILS */
  adminOnly?: boolean;
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
      { label: "Pipeline", href: "/pipeline" },
      { label: "Sales workflow", href: "/sales-workflow", shortLabel: "Buyer actions feed" },
      { label: "Command center", href: "/admin", shortLabel: "Admin dashboard", adminOnly: true },
      { label: "Cal queue", href: "/admin#cal-outreach", shortLabel: "Cal outreach queue", adminOnly: true },
      { label: "Agent queue", href: "/admin#workflow", shortLabel: "Agent actions", adminOnly: true },
      { label: "Prospects", href: "/admin/prospects", shortLabel: "Admin prospects", adminOnly: true },
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
  if (href.includes("#cal-outreach")) return path === "/admin" && hash === "#cal-outreach";
  if (href.includes("#workflow")) return path === "/admin" && hash === "#workflow";
  if (target === "/admin") return path === "/admin" && hash !== "#workflow" && hash !== "#cal-outreach";
  if (target === "/admin/prospects") return path === "/admin/prospects";
  if (target === "/pipeline") return path === "/pipeline" || path === "/admin/prospects";
  if (target === "/integrations") return path === "/integrations" || path.startsWith("/integrations/");

  return path === target || path.startsWith(`${target}/`);
}

export function isAdminWorkspacePath(path: string): boolean {
  const normalized = normalizePath(path);
  return ADMIN_WORKSPACE_LINKS.some((link) => isAdminNavActive(normalized, link.href));
}

/** Workspace nav links visible for the current user (admin-only links filtered out). */
export function visibleAdminNavLinks(isAdmin: boolean): AdminNavLink[] {
  return ADMIN_WORKSPACE_LINKS.filter((link) => !link.adminOnly || isAdmin);
}

export function visibleAdminNavSections(isAdmin: boolean): AdminNavSection[] {
  return ADMIN_WORKSPACE_SECTIONS.map((section) => ({
    ...section,
    links: section.links.filter((link) => !link.adminOnly || isAdmin),
  })).filter((section) => section.links.length > 0);
}
