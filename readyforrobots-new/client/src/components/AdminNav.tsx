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
    <nav className="mb-5 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.035] p-2">
      <div className="flex min-w-max items-center gap-2">
        <span className="px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/30">Admin nav</span>
        {ADMIN_LINKS.map((link) => {
          const active = isActive(location, link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-xl border px-3 py-2 text-xs font-bold transition ${
                active
                  ? "border-amber-400 bg-amber-400 text-[#160b2c]"
                  : "border-white/10 bg-white/[0.025] text-white/60 hover:border-white/20 hover:text-white"
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
