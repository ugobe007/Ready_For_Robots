import { Link, useLocation } from "wouter";
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

export default function AdminNav({ variant = "light" }: Props) {
  const [location, setLocation] = useLocation();
  const isAdmin = useIsAdmin();
  const sections = visibleAdminNavSections(isAdmin);
  const dark = variant === "dark";

  return (
    <nav
      className={
        dark
          ? "pipeline-command-nav sticky top-16 z-40 overflow-x-auto rounded-xl border border-white/10 bg-[#121826] p-3 shadow-lg"
          : "sticky top-16 z-40 mb-6 overflow-x-auto rounded-xl border border-gray-300 bg-white/95 p-3 shadow-sm backdrop-blur-sm"
      }
      aria-label="Workspace navigation"
    >
      <div className="flex min-w-max flex-col gap-3">
        {sections.map((section) => (
          <div key={section.label} className="flex min-w-max flex-wrap items-center gap-2">
            <span
              className={`px-1 text-[10px] font-bold uppercase tracking-[0.18em] ${
                dark ? "text-slate-400" : "text-gray-600"
              }`}
            >
              {section.label}
            </span>
            {section.links.map((link) => {
              const active = isAdminNavActive(location, link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href.split("#", 1)[0]}
                  onClick={(e) => {
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
    </nav>
  );
}
