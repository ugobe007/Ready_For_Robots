/**
 * Header — ReadyForRobots
 * Floating nav · transparent · links to all pages
 * Violet palette: #0d0520 bg · #7c3aed accent
 */
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Menu, X, ArrowRight, ChevronRight } from "lucide-react";
import { Link, useLocation } from "wouter";

function smoothScroll(href: string) {
  if (href.startsWith("#")) {
    const el = document.querySelector(href);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }
}

export default function Header() {
  const [open, setOpen] = useState(false);
  const [location] = useLocation();
  const { session } = useAuth();

  const isHome = location === "/";

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, rgba(13,5,32,0.9) 0%, transparent 100%)" }}
        />
        <div className="relative max-w-6xl mx-auto px-6 py-5 flex items-center justify-between gap-4">

          {/* Logo — /logo-r.png from client/public (same asset as legacy Next site) */}
          <Link href="/" className="flex items-center gap-2.5 group shrink-0">
            <img
              src="/logo-r.png"
              alt=""
              width={28}
              height={28}
              className="h-7 w-7 shrink-0 object-contain opacity-95 group-hover:opacity-100 transition-opacity"
            />
            <span className="text-sm font-semibold text-white tracking-tight" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              ReadyForRobots
            </span>
            <span className="hidden sm:inline rfr-scout-wordmark text-[9px] px-2 py-1 rounded-md border border-violet-500/45 text-violet-200/95 bg-violet-500/10">
              SCOUT
            </span>
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-1">
            {[
              { label: "Pipeline", href: "/pipeline" },
              { label: "Signals", href: "/signals" },
              { label: "How It Works", href: "/how-it-works" },
              { label: "Pricing", href: "/pricing" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors"
                style={
                  location === link.href
                    ? { color: "#c4b5fd", background: "rgba(124,58,237,0.15)" }
                    : { color: "rgba(255,255,255,0.45)" }
                }
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {session ? (
              <>
                <Link
                  href="/crm"
                  className="hidden sm:inline text-[11px] font-semibold text-white/50 hover:text-white/90 px-2 py-1 rounded-lg hover:bg-white/5"
                >
                  CRM
                </Link>
                <Link
                  href="/profile"
                  className="hidden sm:inline text-[11px] font-semibold text-white/50 hover:text-white/90 px-2 py-1 rounded-lg hover:bg-white/5"
                >
                  Workspace
                </Link>
              </>
            ) : (
              <Link
                href="/login"
                className="hidden sm:inline text-[11px] font-semibold text-white/50 hover:text-white/90 px-2 py-1 rounded-lg hover:bg-white/5"
              >
                Sign in
              </Link>
            )}
            {/* Live badge */}
            <span
              className="hidden sm:flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-full"
              style={{ color: "#34d399", background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.25)" }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="rfr-scout-wordmark text-[9px] text-emerald-200/95">SCOUT</span>
              <span className="normal-case tracking-normal font-semibold text-emerald-100/90">live</span>
            </span>

            {/* CTA */}
            {isHome ? (
              <button
                onClick={() => smoothScroll("#hero-cta")}
                className="hidden sm:flex items-center gap-1.5 text-sm font-semibold text-white px-4 py-2 rounded-lg transition-all shadow-lg hover:-translate-y-0.5"
                style={{ background: "#7c3aed", boxShadow: "0 4px 16px rgba(124,58,237,0.35)" }}
              >
                Start automating <ArrowRight className="h-3.5 w-3.5" />
              </button>
            ) : (
              <Link
                href="/"
                className="hidden sm:flex items-center gap-1.5 text-sm font-semibold text-white px-4 py-2 rounded-lg transition-all shadow-lg hover:-translate-y-0.5"
                style={{ background: "#7c3aed", boxShadow: "0 4px 16px rgba(124,58,237,0.35)" }}
              >
                Start automating <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            )}

            {/* Hamburger */}
            <button
              onClick={() => setOpen(!open)}
              className="h-9 w-9 flex items-center justify-center rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Open menu"
            >
              {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* Dropdown menu */}
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div
            className="fixed top-16 right-4 z-50 rounded-2xl border border-white/10 shadow-2xl shadow-black/70 overflow-hidden"
            style={{ background: "rgba(13,5,32,0.97)", backdropFilter: "blur(24px)", width: "260px" }}
          >
            {/* Product links */}
            <div>
              <p className="px-4 pt-3 pb-1 text-[10px] font-bold uppercase tracking-widest text-white/25">Product</p>
              {[
                { label: "Pipeline", href: "/pipeline" },
                { label: "Signals", href: "/signals" },
                ...(session
                  ? [
                      { label: "CRM", href: "/crm" },
                      { label: "Workspace", href: "/profile" },
                    ]
                  : [{ label: "Sign in", href: "/login" }]),
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center justify-between px-4 py-2.5 text-sm text-white/55 hover:text-white hover:bg-white/6 transition-colors"
                >
                  <span>{item.label}</span>
                  <ChevronRight className="h-3.5 w-3.5 text-white/20" />
                </Link>
              ))}
            </div>

            {/* Company links */}
            <div className="border-t border-white/8">
              <p className="px-4 pt-3 pb-1 text-[10px] font-bold uppercase tracking-widest text-white/25">Company</p>
              {[
                { label: "How It Works", href: "/how-it-works" },
                { label: "Pricing", href: "/pricing" },
                { label: "About Us", href: "/#about" },
                { label: "Questions", href: "/#faq" },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => {
                    setOpen(false);
                    if (item.href.startsWith("/#")) {
                      setTimeout(() => smoothScroll(item.href.replace("/", "")), 100);
                    }
                  }}
                  className="flex items-center justify-between px-4 py-2.5 text-sm text-white/55 hover:text-white hover:bg-white/6 transition-colors"
                >
                  <span>{item.label}</span>
                  <ChevronRight className="h-3.5 w-3.5 text-white/20" />
                </Link>
              ))}
            </div>

            <div className="border-t border-white/8 p-3">
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="w-full flex items-center justify-center gap-2 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors hover:opacity-90"
                style={{ background: "#7c3aed", display: "flex" }}
              >
                Start automating <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </>
      )}
    </>
  );
}
