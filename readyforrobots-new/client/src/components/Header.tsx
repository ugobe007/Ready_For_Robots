/**
 * Header — Precision Intelligence (emerald light)
 * Floating nav · scroll-aware backdrop · desktop links + mobile drawer
 */
import { useState, useEffect } from "react";
import {
  Menu,
  X,
  Zap,
  LayoutDashboard,
  Radio,
  HelpCircle,
  UserRound,
  BriefcaseBusiness,
  ChevronRight,
  ChevronDown,
  Newspaper,
  ClipboardList,
  LogOut,
} from "lucide-react";
import { Link, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";
import {
  ADMIN_QUICK_ACTIONS,
  isAdminNavActive,
  isAdminWorkspacePath,
  openWorkspaceHref,
  visibleAdminNavSections,
} from "@/lib/adminNavLinks";
import { isDarkHeroRoute } from "@/lib/darkHeroRoutes";
import { loginHref, clearPendingNext } from "@/lib/authNext";
import { useIsAdmin } from "@/hooks/useIsAdmin";

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
    a: "Any robot category with a B2B sales motion: warehouse AMRs, service robots, industrial arms, cleaning robots, food processing automation, healthcare robots, and more.",
  },
  {
    q: "How is this different from a lead list?",
    a: "A lead list gives you names. We give you timing, context, and a reason to reach out — with confidence scores and Signal-prepared outreach drafts.",
  },
  {
    q: "Do I need to sign up to see results?",
    a: "No. Enter your company URL and we'll show matched opportunities immediately — no account required.",
  },
];

const priorityNavLinks = [
  { label: "Pipeline", href: "/pipeline", icon: LayoutDashboard, desc: "Your live prospect queue" },
  { label: "Signals", href: "/signals", icon: Radio, desc: "Buying signals detected today" },
  { label: "Robots", href: "/robots", icon: ClipboardList, desc: "Humanoid benchmarks & HEIR" },
  { label: "Pricing", href: "/pricing", icon: BriefcaseBusiness, desc: "Plans and billing" },
];

const supportNavLinks = [
  { label: "Intelligence", href: "/intelligence", icon: Newspaper, desc: "Report and market signals" },
  { label: "Compare", href: "/compare", icon: HelpCircle, desc: "Pipeline vs GTM data tools" },
  { label: "Integrations", href: "/integrations", icon: BriefcaseBusiness, desc: "HubSpot live · more CRMs soon" },
  { label: "FAQ", href: "/pricing#faq", icon: HelpCircle, desc: "Pricing and product questions" },
];

const moreNavLinks = [
  { label: "Newsletter", href: "/newsletter", icon: Newspaper, desc: "Daily Robot Intelligence Brief" },
  { label: "Studio", href: "/social", icon: ClipboardList, desc: "Content Studio — social posts" },
  { label: "Marketplace", href: "/marketplace", icon: BriefcaseBusiness, desc: "RFPs, proposals, and quotes" },
];

export default function Header() {
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [faqOpen, setFaqOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const [location, setLocation] = useLocation();
  const { session } = useAuth();
  const isAdmin = useIsAdmin();
  const workspaceSections = visibleAdminNavSections(isAdmin);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    setMoreOpen(false);
    setWorkspaceOpen(false);
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

  useEffect(() => {
    if (!workspaceOpen) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (!t.closest("[data-nav-workspace]")) setWorkspaceOpen(false);
    };
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, [workspaceOpen]);

  const closeDrawer = () => setOpen(false);
  const signedInEmail = session?.user?.email;
  const workspaceNavActive = isAdminWorkspacePath(location);
  const pathBase = location.split("?")[0].split("#")[0];
  const pipelineCommand = pathBase === "/pipeline";
  const darkHero = isDarkHeroRoute(location);
  const onDarkSurface = darkHero && !scrolled && !pipelineCommand;
  const lightNav = onDarkSurface || pipelineCommand;
  const moreNavActive = moreNavLinks.some((l) => location === l.href);
  const supportNavActive = supportNavLinks.some((l) => {
    const path = l.href.split("#", 1)[0];
    return location === path || (typeof window !== "undefined" && l.href.includes("#") && location === path && window.location.hash === l.href.slice(l.href.indexOf("#")));
  });

  const handleSignOut = async () => {
    closeDrawer();
    clearPendingNext();
    await supabase?.auth.signOut();
    window.location.href = "/";
  };

  const navLinkClass = (href: string) => {
    const active = location === href;
    if (lightNav) {
      return `px-3.5 py-2 text-sm font-medium rounded-md transition-colors duration-150 ${
        active ? "text-emerald-300 bg-white/10" : "text-slate-200 hover:text-white hover:bg-white/10"
      }`;
    }
    return `px-3.5 py-2 text-sm font-medium rounded-md transition-colors duration-150 ${
      active ? "text-emerald-700 bg-emerald-50" : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
    }`;
  };

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          pipelineCommand
            ? "bg-[#0b1020]/98 backdrop-blur-xl shadow-lg border-b border-white/10"
            : scrolled
              ? "bg-[#0b1020]/96 backdrop-blur-xl shadow-lg border-b border-white/10"
              : onDarkSurface
                ? "bg-transparent border-b border-white/5"
                : "bg-white/80 backdrop-blur-md"
        }`}
      >
        <div className="container">
          <div className="flex items-center justify-between h-16 gap-4">
            <Link href="/" className="flex items-center gap-2.5 shrink-0">
              <img src="/logo-r.png" alt="ReadyForRobots" className="h-8 w-8 object-contain" />
              <div className="flex flex-col leading-none">
                <span className={`font-display font-bold text-[15px] tracking-tight ${lightNav ? "text-white" : "text-gray-900"}`}>
                  ReadyForRobots
                </span>
                <span className={`rfr-scout-wordmark mt-1 text-[9px] ${lightNav ? "text-emerald-400" : "text-emerald-600"}`}>
                  SIGNAL
                </span>
              </div>
            </Link>

            <nav className="hidden lg:flex items-center gap-1 min-w-0">
              {priorityNavLinks.map((link) => (
                <Link key={link.href} href={link.href} className={navLinkClass(link.href)}>
                  {link.label}
                </Link>
              ))}
              {supportNavLinks.slice(0, 2).map((link) => (
                <Link key={link.href} href={link.href} className={navLinkClass(link.href.split("#", 1)[0])}>
                  {link.label}
                </Link>
              ))}
              <div className="relative" data-nav-more>
                <button
                  type="button"
                  onClick={() => setMoreOpen((v) => !v)}
                  className={`inline-flex items-center gap-1 px-3.5 py-2 text-sm font-medium rounded-md transition-colors ${
                    lightNav
                      ? moreNavActive || supportNavActive || moreOpen
                        ? "text-emerald-300 bg-white/10"
                        : "text-slate-200 hover:text-white hover:bg-white/10"
                      : moreNavActive || supportNavActive || moreOpen
                        ? "text-emerald-700 bg-emerald-50"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                  aria-expanded={moreOpen}
                >
                  More
                  <ChevronDown className={`h-3.5 w-3.5 transition-transform ${moreOpen ? "rotate-180" : ""}`} />
                </button>
                {moreOpen && (
                  <div className="absolute right-0 top-full mt-2 min-w-[220px] rounded-xl border border-gray-100 bg-white py-1.5 shadow-lg z-[60]">
                    <p className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-gray-400">Support</p>
                    {supportNavLinks.slice(2).map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={`block px-4 py-2.5 text-sm font-medium transition-colors hover:bg-gray-50 ${
                          location === link.href.split("#", 1)[0] ? "text-emerald-700" : "text-gray-700"
                        }`}
                      >
                        {link.label}
                      </Link>
                    ))}
                    <div className="my-1 border-t border-gray-100" />
                    <p className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-gray-400">More</p>
                    {moreNavLinks.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={`block px-4 py-2.5 text-sm font-medium transition-colors hover:bg-gray-50 ${
                          location === link.href ? "text-emerald-700" : "text-gray-700"
                        }`}
                      >
                        {link.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </nav>

            <div className="flex items-center gap-2 shrink-0">
              <Link
                href="/find-robots"
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-all"
              >
                Find leads
              </Link>

              {!session ? (
                <>
                  <Link href={loginHref()} className={`hidden md:inline text-sm font-medium ${lightNav ? "text-slate-200 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}>
                    Sign in
                  </Link>
                  <Link
                    href="/signup"
                    className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg transition-all active:scale-[0.97]"
                  >
                    <Zap size={14} />
                    Activate SIGNAL
                  </Link>
                </>
              ) : (
                <div className="hidden sm:flex items-center gap-2">
                  <div className="relative" data-nav-workspace>
                    <button
                      type="button"
                      onClick={() => setWorkspaceOpen((v) => !v)}
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-bold transition ${
                        workspaceNavActive || workspaceOpen
                          ? lightNav
                            ? "border-emerald-400 bg-emerald-600/90 text-white"
                            : "border-emerald-600 bg-emerald-50 text-emerald-800"
                          : lightNav
                            ? "border-white/15 bg-white/5 text-slate-100 hover:border-emerald-400/50 hover:bg-white/10"
                            : "border-gray-200 bg-white text-gray-700 hover:border-emerald-300 hover:bg-emerald-50"
                      }`}
                      aria-expanded={workspaceOpen}
                    >
                      <LayoutDashboard className="h-3.5 w-3.5" />
                      Workspace
                      <ChevronDown className={`h-3.5 w-3.5 transition-transform ${workspaceOpen ? "rotate-180" : ""}`} />
                    </button>
                    {workspaceOpen && (
                      <div className="absolute right-0 top-full mt-2 w-[min(320px,calc(100vw-2rem))] max-h-[70vh] overflow-y-auto rounded-xl border border-gray-100 bg-white py-2 shadow-lg z-[60]">
                        {workspaceSections.map((section) => (
                          <div key={section.label} className="px-2 py-1">
                            <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                              {section.label}
                            </p>
                            {section.links.map((link) => (
                              <Link
                                key={link.href}
                                href={link.href.split("#", 1)[0]}
                                onClick={(e) => {
                                  setWorkspaceOpen(false);
                                  if (link.href.includes("#")) {
                                    e.preventDefault();
                                    openWorkspaceHref(link.href, setLocation);
                                  }
                                }}
                                className={`block rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-gray-50 ${
                                  isAdminNavActive(location, link.href) ? "bg-emerald-50 text-emerald-700" : "text-gray-700"
                                }`}
                              >
                                {link.label}
                              </Link>
                            ))}
                          </div>
                        ))}
                        {isAdmin && (
                          <div className="border-t border-gray-100 px-2 py-2 mt-1">
                            <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-amber-700">
                              Admin actions
                            </p>
                            {ADMIN_QUICK_ACTIONS.map((link) => (
                              <Link
                                key={link.href}
                                href={link.href.split("#", 1)[0]}
                                onClick={(e) => {
                                  setWorkspaceOpen(false);
                                  e.preventDefault();
                                  openWorkspaceHref(link.href, setLocation);
                                }}
                                className="block rounded-lg px-3 py-2 text-sm font-semibold text-amber-900 transition-colors hover:bg-amber-50"
                              >
                                {link.label}
                              </Link>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <Link
                    href="/profile"
                    className={`max-w-[140px] truncate rounded-lg px-3 py-2 text-xs font-semibold ${
                      lightNav
                        ? "text-slate-300 hover:bg-white/10 hover:text-white"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                    title={signedInEmail}
                  >
                    {signedInEmail ?? "Account"}
                  </Link>
                  <button
                    type="button"
                    onClick={() => void handleSignOut()}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold ${
                      lightNav
                        ? "border-white/15 text-slate-300 hover:bg-white/10 hover:text-white"
                        : "border-gray-200 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Sign out
                  </button>
                </div>
              )}

              <button
                onClick={() => setOpen(!open)}
                className={`lg:hidden p-2 rounded-md ${lightNav ? "text-slate-200 hover:bg-white/10" : "text-gray-600 hover:bg-gray-100"}`}
                aria-label={open ? "Close menu" : "Open menu"}
              >
                {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 lg:hidden ${
          open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={closeDrawer}
      />

      <div
        className={`fixed top-0 right-0 bottom-0 z-50 flex w-[min(320px,90vw)] flex-col overflow-y-auto bg-white border-l border-gray-100 shadow-xl transition-transform duration-300 lg:hidden ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-5 border-b border-gray-100">
          <Link href="/" onClick={closeDrawer} className="flex items-center gap-2.5">
            <img src="/logo-r.png" alt="" className="h-7 w-7" />
            <span className="font-display font-bold text-gray-900 text-sm">ReadyForRobots</span>
          </Link>
          <button onClick={closeDrawer} className="p-2 rounded-lg text-gray-400 hover:bg-gray-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-4 pt-4 pb-2 space-y-2">
          <Link
            href="/signup"
            onClick={closeDrawer}
            className="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm"
          >
            <Zap className="h-4 w-4" />
            Activate SIGNAL
          </Link>
          <Link
            href="/find-robots"
            onClick={closeDrawer}
            className="flex items-center justify-center gap-2 py-3 rounded-xl border border-emerald-200 text-emerald-700 text-sm font-bold"
          >
            Find Robots
          </Link>
        </div>

        <div className="px-4 pb-2 border-b border-gray-100">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 px-1 mb-2">Product</p>
          {priorityNavLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl mb-0.5 ${
                  isActive ? "bg-emerald-50 text-emerald-700" : "text-gray-700 hover:bg-gray-50"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold leading-none">{item.label}</p>
                  <p className="text-[11px] text-gray-400 mt-0.5">{item.desc}</p>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-gray-300 shrink-0" />
              </Link>
            );
          })}
        </div>

        <div className="px-4 py-2 border-b border-gray-100">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 px-1 mb-2">Support</p>
          {supportNavLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm ${
                  location === item.href.split("#", 1)[0] ? "bg-emerald-50 text-emerald-700" : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="flex-1">{item.label}</span>
                <ChevronRight className="h-3.5 w-3.5 text-gray-300 shrink-0" />
              </Link>
            );
          })}
        </div>

        <div className="px-4 py-2 border-b border-gray-100">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 px-1 mb-2">More</p>
          {moreNavLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeDrawer}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm ${
                location === item.href ? "bg-emerald-50 text-emerald-700" : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {item.label}
              <ChevronRight className="h-3.5 w-3.5 text-gray-300 ml-auto" />
            </Link>
          ))}
        </div>

        {session && (
          <div className="px-4 py-2 border-b border-gray-100">
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 px-1 mb-2">Workspace</p>
            {workspaceSections.map((section) => (
              <div key={section.label} className="mb-2">
                <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">{section.label}</p>
                {section.links.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href.split("#", 1)[0]}
                    onClick={(e) => {
                      closeDrawer();
                      if (link.href.includes("#")) {
                        e.preventDefault();
                        openWorkspaceHref(link.href, setLocation);
                      }
                    }}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm ${
                      isAdminNavActive(location, link.href) ? "bg-emerald-50 text-emerald-700" : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {link.label}
                    <ChevronRight className="h-3.5 w-3.5 text-gray-300 ml-auto" />
                  </Link>
                ))}
              </div>
            ))}
            {isAdmin && (
              <div className="mb-2 rounded-xl border border-amber-100 bg-amber-50/80 p-2">
                <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-amber-800">Admin actions</p>
                {ADMIN_QUICK_ACTIONS.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href.split("#", 1)[0]}
                    onClick={(e) => {
                      closeDrawer();
                      e.preventDefault();
                      openWorkspaceHref(link.href, setLocation);
                    }}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-amber-950"
                  >
                    {link.label}
                    <ChevronRight className="h-3.5 w-3.5 text-amber-400 ml-auto" />
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="px-4 py-3">
          {!session ? (
            <div className="space-y-2">
              <Link href={loginHref()} onClick={closeDrawer} className="block text-center py-2 text-sm text-gray-600">
                Sign in
              </Link>
              <Link
                href="/signup?next=/pipeline"
                onClick={closeDrawer}
                className="block text-center py-3 rounded-xl border border-gray-200 text-sm font-bold text-gray-800"
              >
                Start free workspace
              </Link>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => void handleSignOut()}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-red-200 text-red-600 text-sm font-semibold"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          )}
        </div>

        <div className="px-4 pt-1 pb-4 mt-auto border-t border-gray-100">
          <button
            type="button"
            onClick={() => setFaqOpen((current) => !current)}
            className="flex w-full items-center justify-between px-3 py-2.5 rounded-xl text-sm text-gray-600 hover:bg-gray-50"
          >
            FAQ
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${faqOpen ? "rotate-180" : ""}`} />
          </button>
          {faqOpen &&
            faqs.map((faq, i) => {
              const isOpen = openFaq === i;
              return (
                <div key={faq.q} className="border-b border-gray-100 last:border-0">
                  <button
                    type="button"
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left text-xs font-semibold text-gray-700"
                  >
                    {faq.q}
                    <ChevronDown className={`h-3.5 w-3.5 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                  {isOpen && <p className="px-3 pb-3 text-[11px] leading-relaxed text-gray-500">{faq.a}</p>}
                </div>
              );
            })}
        </div>
      </div>
    </>
  );
}
