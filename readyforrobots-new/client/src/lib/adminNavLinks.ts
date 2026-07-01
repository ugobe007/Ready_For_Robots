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
    label: "Pipeline",
    links: [
      { label: "Live pipeline", href: "/pipeline", shortLabel: "Pick leads · draft · send" },
      { label: "Activity feed", href: "/sales-workflow", shortLabel: "What happened while you were away" },
      { label: "Inbox", href: "/inbox", shortLabel: "Replies & threads" },
    ],
  },
  {
    label: "Tools",
    links: [
      { label: "Outreach editor", href: "/crm", shortLabel: "Advanced approve/send UI" },
      { label: "Calendar", href: "/calendar" },
      { label: "Sales console", href: "/sales-console", shortLabel: "Reply automation" },
    ],
  },
  {
    label: "Admin",
    links: [
      { label: "Command center", href: "/admin", shortLabel: "Admin dashboard", adminOnly: true },
      { label: "Cal queue", href: "/admin#cal-outreach", shortLabel: "Bulk HOT/WARM outreach", adminOnly: true },
      { label: "Agent queue", href: "/admin#workflow", shortLabel: "Agent actions", adminOnly: true },
      { label: "Prospects", href: "/admin/prospects", shortLabel: "Admin prospects", adminOnly: true },
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

/** SPA navigation that preserves hash anchors (wouter path-only routes drop #sections). */
export function openWorkspaceHref(href: string, setLocation: (path: string) => void): void {
  const hashIdx = href.indexOf("#");
  if (hashIdx === -1) {
    setLocation(href);
    return;
  }
  const path = href.slice(0, hashIdx) || "/";
  const hash = href.slice(hashIdx);
  setLocation(path);
  if (typeof window === "undefined") return;
  const full = `${path}${hash}`;
  if (`${window.location.pathname}${window.location.hash}` !== full) {
    window.history.replaceState(null, "", full);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }
  const id = hash.replace(/^#/, "");
  window.setTimeout(() => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 120);
}

export const ADMIN_QUICK_ACTIONS: AdminNavLink[] = [
  { label: "Cal queue — draft & send", href: "/admin#cal-outreach", shortLabel: "Cal outreach" },
  { label: "Agent queue", href: "/admin#workflow", shortLabel: "Agent actions" },
  { label: "Command center", href: "/admin", shortLabel: "Admin home" },
];
