import { Link, useLocation } from "wouter";
import {
  ADMIN_WORKSPACE_SECTIONS,
  isAdminNavActive,
} from "@/lib/adminNavLinks";

export default function AdminNav() {
  const [location] = useLocation();

  return (
    <nav
      className="sticky top-16 z-40 mb-6 overflow-x-auto rounded-xl border border-gray-300 bg-white/95 p-3 shadow-sm backdrop-blur-sm"
      aria-label="Workspace navigation"
    >
      <div className="flex min-w-max flex-col gap-3">
        {ADMIN_WORKSPACE_SECTIONS.map((section) => (
          <div key={section.label} className="flex min-w-max flex-wrap items-center gap-2">
            <span className="px-1 text-[10px] font-bold uppercase tracking-[0.18em] text-gray-600">
              {section.label}
            </span>
            {section.links.map((link) => {
              const active = isAdminNavActive(location, link.href);
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
        ))}
      </div>
    </nav>
  );
}
