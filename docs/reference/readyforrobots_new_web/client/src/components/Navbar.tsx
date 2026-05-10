/**
 * Navbar — "Precision Craft" design
 * Clean white nav with emerald primary CTA, subtle border on scroll
 */

import { PRIMARY_NAV } from "@/lib/siteNav";
import { useState, useEffect } from "react";
import { Link } from "wouter";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/95 backdrop-blur-sm border-b border-gray-100 shadow-sm"
          : "bg-white"
      }`}
    >
      <div className="container">
        <nav className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 group">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
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
              className="font-semibold text-gray-900"
              style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif", fontSize: "1rem" }}
            >
              Ready For Robots
            </span>
          </Link>

          <div className="hidden lg:flex items-center gap-6">
            {PRIMARY_NAV.map((link) => (
              <Link
                key={link.href + link.label}
                href={link.href}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-150 relative group"
              >
                {link.label}
                <span
                  className="absolute -bottom-0.5 left-0 w-0 h-0.5 group-hover:w-full transition-all duration-200"
                  style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
                />
              </Link>
            ))}
            <Link
              href="/about"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-150"
            >
              About
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden md:inline-flex text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2"
            >
              Sign in
            </Link>
            <Link
              href="/newsletter"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-white px-4 py-2 rounded-lg transition-all duration-150 hover:opacity-90 active:scale-95"
              style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
            >
              Get started
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path
                  d="M3 7h8M7 3l4 4-4 4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
