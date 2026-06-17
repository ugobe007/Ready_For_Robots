/**
 * Header — ReadyForRobots
 * Floating nav · transparent · desktop links + mobile slide-in drawer
 * Color system: #0d0520 bg · #7c3aed purple (brand) · #03DAC5 teal (action/live/CTA)
 * Mobile drawer: full-height slide-in from right, includes SIGNAL chat entry
 */
import { useState, useEffect } from "react";
import { Menu, X, Zap, LayoutDashboard, Radio, HelpCircle, UserRound, BriefcaseBusiness, ChevronRight, ChevronDown, Newspaper, ClipboardList, LogOut } from "lucide-react"; // eslint-disable-line @typescript-eslint/no-unused-vars
import { Link, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { useScoutChat } from "@/components/ScoutChat";
import { supabase } from "@/lib/supabase";

function smoothScroll(href: string) {
  if (href.startsWith("#")) {
    const el = document.querySelector(href);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }
}

const faqs = [
  {
    q: "How does ReadyForRobots find buying signals?",
    a: "We monitor 150+ sources continuously — job boards, earnings calls, press releases, OSHA filings, real estate permits, and industry news. Signal detects patterns that indicate a company is ready to invest in automation.",
  },
  {
    q: "What types of robots does this work for?",
    a: "Any robot category with a B2B sales motion: warehouse AMRs, service robots, industrial arms, cleaning robots, food processing automation, healthcare robots, and more. You tell us your category and we tune the signals accordingly.",
  },
  {
    q: "How is this different from a lead list?",
    a: "A lead list gives you names. We give you timing, context, and a reason to reach out. Every opportunity comes with the exact signal that triggered it, a confidence score, and a Signal-prepared outreach draft — so you reach the right buyer at the right moment.",
  },
  {
    q: "Do I need to sign up to see results?",
    a: "No. Enter your company URL above and we'll show you a sample of matched opportunities immediately — no account required. You only sign up when you want to act on them.",
  },
  {
    q: "How quickly does Signal act on new market signals?",
    a: "Signals are detected and scored within minutes. Signal prepares outreach drafts within the hour. In Auto mode, approved actions are sent within 24 hours of signal detection.",
  },
];

const priorityNavLinks = [
  { label: "Pipeline", href: "/pipeline", icon: LayoutDashboard, desc: "Your live prospect queue" },
  { label: "Signals", href: "/signals", icon: Radio, desc: "Buying signals detected today" },
  { label: "Newsletter", href: "/newsletter", icon: Newspaper, desc: "Daily Robot Intelligence Brief" },
  { label: "Robots", href: "/robots", icon: ClipboardList, desc: "Humanoid benchmarks & HEIR" },
  { label: "How It Works", href: "/how-it-works", icon: HelpCircle, desc: "Prospecting, qualifying, and outreach" },
];

const moreNavLinks = [
  { label: "Intelligence", href: "/intelligence", icon: Newspaper, desc: "Report and market signals" },
  { label: "Studio", href: "/social", icon: ClipboardList, desc: "Content Studio — social posts" },
  { label: "Marketplace", href: "/marketplace", icon: BriefcaseBusiness, desc: "RFPs, proposals, and quotes" },
  { label: "Integrations", href: "/integrations", icon: BriefcaseBusiness, desc: "HubSpot live · more CRMs soon" },
  { label: "Pricing", href: "/pricing", icon: BriefcaseBusiness, desc: "Plans and billing" },
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [faqOpen, setFaqOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [location] = useLocation();
  const { openChat } = useScoutChat();
  const { session } = useAuth();

  // Lock body scroll when drawer is open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  useEffect(() => {
    setMoreOpen(false);
  }, [location]);

  useEffect(() => {
    if (!moreOpen) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (!t.closest("[data-nav-more]")) setMoreOpen(false);
    };
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, [moreOpen]);

  const closeDrawer = () => setOpen(false);

  const navLinkStyle = (href: string) =>
    location === href
      ? { color: "#03DAC5", background: "rgba(3,218,197,0.1)" }
      : { color: "rgba(255,255,255,0.45)" };

  const moreNavActive = moreNavLinks.some((l) => location === l.href);

  const handleSignOut = async () => {
    closeDrawer();
    await supabase?.auth.signOut();
    window.location.href = "/";
  };

  const signedInEmail = session?.user?.email;

  const accountLinks = [
    { label: "Sign up", href: "/signup", icon: UserRound, desc: "Create your Signal workspace" },
    { label: "Sign in", href: "/login", icon: UserRound, desc: "Access your account" },
    { label: "Workspace", href: "/profile", icon: BriefcaseBusiness, desc: "View saved Signal work" },
    { label: "Calendar", href: "/calendar", icon: BriefcaseBusiness, desc: "Schedule meetings and send invites" },
    { label: "Marketplace", href: "/marketplace", icon: BriefcaseBusiness, desc: "Manage RFPs and vendor docs" },
    { label: "Integrations", href: "/integrations", icon: BriefcaseBusiness, desc: "Connect HubSpot, GitHub, and your CRM" },
  ];

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "linear-gradient(to bottom, rgba(13,5,32,0.92) 0%, transparent 100%)" }}
        />
        <div className="relative max-w-6xl mx-auto px-6 py-5 flex items-center justify-between gap-4">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group shrink-0">
            <img src="/logo-r.png" alt="" width={32} height={32} className="h-8 w-8 object-contain opacity-95" />
            <span className="text-sm font-semibold text-white tracking-tight" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              ReadyForRobots
            </span>
          </Link>

          {/* Desktop nav — priority links + More */}
          <nav className="hidden lg:flex items-center gap-0.5 min-w-0">
            {priorityNavLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-2 rounded-lg text-xs font-semibold transition-colors whitespace-nowrap"
                style={navLinkStyle(link.href)}
              >
                {link.label}
              </Link>
            ))}
            <div className="relative" data-nav-more>
              <button
                type="button"
                onClick={() => setMoreOpen((v) => !v)}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-semibold transition-colors whitespace-nowrap"
                style={
                  moreNavActive || moreOpen
                    ? { color: "#03DAC5", background: "rgba(3,218,197,0.1)" }
                    : { color: "rgba(255,255,255,0.45)" }
                }
                aria-expanded={moreOpen}
                aria-haspopup="true"
              >
                More
                <ChevronDown className={`h-3.5 w-3.5 transition-transform ${moreOpen ? "rotate-180" : ""}`} />
              </button>
              {moreOpen && (
                <div
                  className="absolute right-0 top-full mt-2 min-w-[200px] rounded-xl border border-white/10 py-1.5 shadow-2xl z-[60]"
                  style={{ background: "rgba(13,5,32,0.98)", backdropFilter: "blur(16px)" }}
                >
                  {moreNavLinks.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="block px-4 py-2.5 text-xs font-semibold transition-colors hover:bg-white/5"
                      style={location === link.href ? { color: "#03DAC5" } : { color: "rgba(255,255,255,0.7)" }}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/find-robots"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-bold transition-all hover:brightness-110 hover:-translate-y-0.5"
              style={{
                color: "#0d0520",
                background: "#03DAC5",
                border: "1px solid rgba(3,218,197,0.6)",
                fontFamily: "'Sora', system-ui, sans-serif",
              }}
            >
              Find Robots
            </Link>

            {/* Live badge */}
            <span
              className="hidden md:flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full"
              style={{ color: "#03DAC5", background: "rgba(3,218,197,0.1)", border: "1px solid rgba(3,218,197,0.25)" }}
            >
              <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: "#03DAC5" }} />
              Live
            </span>

            {!session ? (
              <Link
                href="/signup"
                className="hidden sm:inline-flex items-center rounded-xl border px-3.5 py-2 text-xs font-bold transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
                style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
              >
                Sign up
              </Link>
            ) : (
              <div className="hidden sm:flex items-center gap-2">
                <Link
                  href="/profile"
                  className="max-w-[140px] truncate rounded-lg px-3 py-2 text-xs font-semibold text-white/55 hover:text-white hover:bg-white/8 transition-colors"
                  title={signedInEmail}
                >
                  {signedInEmail ?? "Account"}
                </Link>
                <button
                  type="button"
                  onClick={() => void handleSignOut()}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/12 px-3 py-2 text-xs font-semibold text-white/55 hover:text-white hover:bg-white/8 transition-colors"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            )}

            {/* Hamburger */}
            <button
              onClick={() => setOpen(!open)}
              className="h-9 w-9 flex items-center justify-center rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              aria-label={open ? "Close menu" : "Open menu"}
            >
              {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile drawer ── */}
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(4px)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
        onClick={closeDrawer}
      />

      {/* Drawer panel */}
      <div
        className="fixed top-0 right-0 bottom-0 z-50 flex flex-col overflow-y-auto"
        style={{
          width: "min(320px, 90vw)",
          background: "rgba(13,5,32,0.98)",
          backdropFilter: "blur(24px)",
          borderLeft: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "-24px 0 80px rgba(0,0,0,0.6)",
          transform: open ? "translateX(0)" : "translateX(100%)",
          transition: "transform 0.3s cubic-bezier(0.4,0,0.2,1)",
        }}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-white/8 shrink-0">
          <Link href="/" onClick={closeDrawer} className="flex items-center gap-2.5">
            <img src="/logo-r.png" alt="" width={28} height={28} className="h-7 w-7 object-contain opacity-95" />
            <span className="text-sm font-semibold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              ReadyForRobots
            </span>
          </Link>
          <button
            onClick={closeDrawer}
            className="h-8 w-8 flex items-center justify-center rounded-lg text-white/40 hover:text-white hover:bg-white/8 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* CTAs */}
        <div className="px-4 pt-4 pb-2 space-y-2">
          <Link
            href="/results?url="
            onClick={closeDrawer}
            className="w-full flex items-center gap-3 px-4 py-3.5 rounded-xl border transition-all hover:bg-amber-400/8"
            style={{
              border: "1.5px solid rgba(255,176,0,0.4)",
              background: "rgba(255,176,0,0.05)",
            }}
          >
            <div
              className="h-8 w-8 rounded-xl flex items-center justify-center shrink-0"
              style={{ color: "#FFB000", border: "1.5px solid rgba(255,176,0,0.55)", background: "rgba(255,176,0,0.08)" }}
            >
              <Zap className="h-4 w-4" strokeWidth={2.5} />
            </div>
            <div className="text-left flex-1">
              <p className="text-sm font-bold leading-none" style={{ color: "#FFB000" }}>Activate SIGNAL</p>
              <p className="text-[11px] text-white/40 mt-0.5">Scan your URL and match live opportunities</p>
            </div>
            <span className="h-1.5 w-1.5 rounded-full animate-pulse shrink-0" style={{ background: "#FFB000" }} />
          </Link>
          <Link
            href="/find-robots"
            onClick={closeDrawer}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-all active:scale-[0.98]"
            style={{ color: "#0d0520", background: "#03DAC5" }}
          >
            <BriefcaseBusiness className="h-4 w-4" />
            Find Robots
          </Link>
        </div>

        {/* Priority nav */}
        <div className="px-4 pb-2 border-b border-white/6">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 px-1 mb-2">Product</p>
          {priorityNavLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className="flex items-center gap-3 px-3 py-3 rounded-xl transition-all mb-0.5"
                style={isActive
                  ? { background: "rgba(3,218,197,0.08)", color: "#03DAC5" }
                  : { color: "rgba(255,255,255,0.6)" }}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold leading-none">{item.label}</p>
                  <p className="text-[11px] text-white/30 mt-0.5">{item.desc}</p>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-white/20 shrink-0" />
              </Link>
            );
          })}
        </div>

        {/* More links */}
        <div className="px-4 py-2 border-b border-white/6">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 px-1 mb-2">More</p>
          {moreNavLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all mb-0.5"
                style={isActive
                  ? { background: "rgba(3,218,197,0.08)", color: "#03DAC5" }
                  : { color: "rgba(255,255,255,0.5)" }}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-70" />
                <span className="text-sm font-medium">{item.label}</span>
                <ChevronRight className="h-3.5 w-3.5 text-white/20 shrink-0 ml-auto" />
              </Link>
            );
          })}
        </div>

        {/* Account links */}
        <div className="px-4 pb-2">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 px-1 mb-2">Account</p>
          {session && signedInEmail && (
            <p className="px-3 mb-2 text-[11px] text-white/35 truncate" title={signedInEmail}>
              Signed in as <span className="text-white/60">{signedInEmail}</span>
            </p>
          )}
          {(session
            ? accountLinks.filter((item) => item.href !== "/signup" && item.href !== "/login")
            : accountLinks
          ).map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className="flex items-center gap-3 px-3 py-3 rounded-xl transition-all mb-0.5"
                style={isActive
                  ? { background: "rgba(3,218,197,0.08)", color: "#03DAC5" }
                  : { color: "rgba(255,255,255,0.6)" }}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold leading-none">{item.label}</p>
                  <p className="text-[11px] text-white/30 mt-0.5">{item.desc}</p>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-white/20 shrink-0" />
              </Link>
            );
          })}
          {session && (
            <button
              type="button"
              onClick={() => void handleSignOut()}
              className="mt-2 flex w-full items-center gap-3 px-3 py-3 rounded-xl border border-red-500/25 text-red-300/90 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="h-4 w-4 shrink-0" />
              <div className="flex-1 text-left">
                <p className="text-sm font-semibold leading-none">Sign out</p>
                <p className="text-[11px] text-white/30 mt-0.5">End your session on this device</p>
              </div>
            </button>
          )}
        </div>

        {/* Home anchors */}
        <div className="px-4 pt-1 pb-2 border-t border-white/6 mt-1">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 px-1 mb-2 mt-3">Company</p>
          {[
            { label: "About Us", href: "/#about" },
            { label: "Case Studies", href: "/#case-studies" },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              onClick={() => {
                closeDrawer();
                if (item.href.startsWith("/#")) {
                  setTimeout(() => smoothScroll(item.href.replace("/", "")), 150);
                }
              }}
              className="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm text-white/45 hover:text-white/70 hover:bg-white/4 transition-colors"
            >
              {item.label}
              <ChevronRight className="h-3.5 w-3.5 text-white/20" />
            </Link>
          ))}
          <button
            type="button"
            onClick={() => setFaqOpen((current) => !current)}
            className="flex w-full items-center justify-between px-3 py-2.5 rounded-xl text-sm text-white/45 hover:text-white/70 hover:bg-white/4 transition-colors"
          >
            FAQ
            <ChevronDown className={`h-3.5 w-3.5 text-white/20 transition-transform ${faqOpen ? "rotate-180" : ""}`} />
          </button>
          {faqOpen && (
            <div className="mt-1 overflow-hidden rounded-xl border border-white/8 bg-white/[0.02]">
              {faqs.map((faq, i) => {
                const isOpen = openFaq === i;
                return (
                  <div key={faq.q} className="border-b border-white/6 last:border-b-0">
                    <button
                      type="button"
                      onClick={() => setOpenFaq(isOpen ? null : i)}
                      className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left"
                    >
                      <span className="text-xs font-semibold leading-snug text-white/65">{faq.q}</span>
                      <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-white/20 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                    </button>
                    {isOpen && (
                      <p className="px-3 pb-3 text-[11px] leading-relaxed text-white/40">{faq.a}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Bottom CTA */}
        <div className="mt-auto px-4 py-5 border-t border-white/8">
          <Link href="/results?url=" onClick={closeDrawer}>
            <button
              className="w-full flex items-center justify-center gap-2 text-sm font-bold py-3 rounded-xl transition-all active:scale-95"
              style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "rgba(3,218,197,0.06)" }}
            >
              <Zap className="h-3.5 w-3.5" /> Start a Scan
            </button>
          </Link>
          <p className="text-center text-[10px] text-white/20 mt-2.5">No signup required · Free to start</p>
        </div>
      </div>
    </>
  );
}
