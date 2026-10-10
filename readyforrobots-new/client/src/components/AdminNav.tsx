import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { ChevronDown, Menu } from "lucide-react";
import {
  isAdminNavActive,
  openWorkspaceHref,
  visibleAdminNavSections,
} from "@/lib/adminNavLinks";
import { useIsAdmin } from "@/hooks/useIsAdmin";

type Props = {
  /** Dark command-rail styling for pipeline and other high-focus workspace pages. */
  variant?: "light" | "dark";
};

const STORAGE_KEY = "rfr.adminNav.collapsed";

export default function AdminNav({ variant = "light" }: Props) {
  const [location, setLocation] = useLocation();
  const isAdmin = useIsAdmin();
  const sections = visibleAdminNavSections(isAdmin);
  const dark = variant === "dark";

  // Collapsible so the multi-row nav doesn't block the page. Defaults to
  // collapsed on first load; an explicit choice persists across pages.
  const [collapsed, setCollapsed] = useState(true);
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored != null) setCollapsed(stored === "1");
    } catch {
      /* ignore storage errors */
    }
  }, []);
  const toggle = () => {
    setCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  };

  // Label the active page so the collapsed bar still tells you where you are.
  const activeLink = sections
    .flatMap(s => s.links)
    .find(l => isAdminNavActive(location, l.href));

  return (
    <nav
      className={
        dark
          ? "pipeline-command-nav sticky top-16 z-40 rounded-xl border border-white/10 bg-[#121826] p-3 shadow-lg"
          : "sticky top-16 z-40 mb-6 rounded-xl border border-gray-300 bg-white/95 p-3 shadow-sm backdrop-blur-sm"
      }
      aria-label="Workspace navigation"
    >
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={toggle}
          aria-expanded={!collapsed}
          className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-bold transition ${
            dark
              ? "border-white/10 bg-white/5 text-slate-100 hover:bg-white/10"
              : "border-gray-300 bg-gray-50 text-gray-800 hover:bg-gray-100"
          }`}
          title={collapsed ? "Show workspace menu" : "Hide workspace menu"}
        >
          <Menu className="h-3.5 w-3.5" />
          {collapsed ? "Menu" : "Hide menu"}
          <ChevronDown
            className={`h-3.5 w-3.5 transition ${collapsed ? "" : "rotate-180"}`}
          />
        </button>
        {collapsed && activeLink && (
          <span
            className={`truncate rounded-md px-2 py-1 text-xs font-semibold ${
              dark
                ? "bg-emerald-600/90 text-white"
                : "bg-emerald-700 text-white"
            }`}
          >
            {activeLink.label}
          </span>
        )}
      </div>

      {!collapsed && (
        <div className="mt-3 flex flex-wrap items-start gap-x-6 gap-y-3">
          {sections.map(section => (
            <div
              key={section.label}
              className="flex flex-wrap items-center gap-2"
            >
              <span
                className={`px-1 text-[10px] font-bold uppercase tracking-[0.18em] ${
                  dark ? "text-slate-400" : "text-gray-600"
                }`}
              >
                {section.label}
              </span>
              {section.links.map(link => {
                const active = isAdminNavActive(location, link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href.split("#", 1)[0]}
                    onClick={e => {
                      if (link.href.includes("#")) {
                        e.preventDefault();
                        openWorkspaceHref(link.href, setLocation);
                      }
                    }}
                    className={`rounded-lg border px-3 py-2 text-xs font-bold transition ${
                      active
                        ? dark
                          ? "border-emerald-400 bg-emerald-600 text-white shadow-md shadow-emerald-900/40"
                          : "border-emerald-700 bg-emerald-700 text-white shadow-sm"
                        : dark
                          ? "border-white/10 bg-white/5 text-slate-100 hover:border-emerald-400/50 hover:bg-emerald-950/60 hover:text-white"
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
      )}
    </nav>
  );
}
