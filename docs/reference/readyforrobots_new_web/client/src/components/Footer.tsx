/**
 * Footer — "Precision Craft" design
 * Clean minimal footer with nav links and copyright
 */

import { FOOTER_NAV } from "@/lib/siteNav";
import { Link } from "wouter";

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-100 py-10">
      <div className="container">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
            >
              <svg width="14" height="14" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="3" fill="white" />
                <path
                  d="M9 2v2M9 14v2M2 9h2M14 9h2M4.22 4.22l1.42 1.42M12.36 12.36l1.42 1.42M4.22 13.78l1.42-1.42M12.36 5.64l1.42-1.42"
                  stroke="white"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <span
              className="font-semibold text-gray-700 text-sm"
              style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
            >
              Ready For Robots
            </span>
          </Link>

          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            {FOOTER_NAV.map((link) => (
              <Link
                key={link.href + link.label}
                href={link.href}
                className="text-xs text-gray-500 hover:text-gray-800 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <p className="text-xs text-gray-400">© 2026 Signal intelligence for robotics sales.</p>
        </div>
      </div>
    </footer>
  );
}
