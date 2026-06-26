import { Link, useLocation } from "wouter";

const ADMIN_LINKS = [
  { label: "Admin", href: "/admin" },
  { label: "Prospects", href: "/admin/prospects" },
  { label: "Workflow", href: "/sales-workflow" },
  { label: "Inbox", href: "/inbox" },
  { label: "Calendar", href: "/calendar" },
  { label: "Buyer CRM", href: "/crm" },
  { label: "Supply Pipeline", href: "/supply-pipeline" },
  { label: "Sales Console", href: "/sales-console" },
  { label: "Marketplace", href: "/marketplace" },
  { label: "Profile", href: "/profile" },
];

function isActive(currentPath: string, href: string) {
  const path = href.split("#", 1)[0];
  const hash = typeof window !== "undefined" ? window.location.hash : "";
  if (path === "/sales-workflow") return currentPath === "/sales-workflow" || currentPath === "/readyforrobots/sales-workflow";
  if (href.includes("#workflow")) return (currentPath === "/admin" || currentPath === "/readyforrobots/admin") && hash === "#workflow";
  if (path === "/admin") return (currentPath === "/admin" || currentPath === "/readyforrobots/admin") && hash !== "#workflow";
  if (path === "/admin/prospects") return currentPath === "/admin/prospects" || currentPath === "/readyforrobots/admin/prospects";
  return currentPath === path || currentPath === `/readyforrobots${path}`;
}

export default function AdminNav() {
  const [location] = useLocation();

  return (
    <nav className="mb-5 overflow-x-auto rounded-xl border border-gray-300 bg-white p-2 shadow-sm">
      <div className="flex min-w-max items-center gap-2">
        <span className="px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Workspace</span>
        {ADMIN_LINKS.map((link) => {
          const active = isActive(location, link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-lg border px-3 py-2 text-xs font-bold transition ${
                active
                  ? "border-emerald-700 bg-emerald-700 text-white shadow-sm"
                  : "border-gray-200 bg-gray-50 text-gray-800 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-900"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
