/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * Responsive mobile drawer + desktop navigation bar.
 * Public nav: Find buyers · How it works · Pricing · Sign in · Get early access.
 * Signed-in adds My robots · Saved buyers. Workspace pages stay off this nav.
 */
import { useState, useEffect } from "react";
import { useRoute, useLocation, useSearch } from "wouter";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useIsAdmin } from "@/hooks/useIsAdmin";
import { loginHref, clearPendingNext } from "@/lib/authNext";
import { supabase } from "@/lib/supabase";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  isJobsHandoffSrc,
  jobsFreshHomeHref,
  jobsHeaderCrmHref,
  jobsHeaderJobsHref,
  onJobsFreshHomeClick,
} from "@/lib/jobsWorkflow";

const navIdle = "text-slate-400 transition hover:text-slate-200";
const navActive =
  "border-b-2 border-emerald-400 pb-0.5 text-emerald-400 font-semibold";
const drawerLink =
  "block rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80";

const EARLY_ACCESS_HREF = "/signup?next=/&src=header_early_access";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const isAdmin = useIsAdmin();
  const [location] = useLocation();
  const search = useSearch();
  const [onJobsSlug] = useRoute("/jobs/:slug");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  const findActive =
    location === "/" || location.startsWith("/?") || Boolean(onJobsSlug);
  const jobsSrc = new URLSearchParams(search).get("src");
  const onJobsCrmDesk =
    location.startsWith("/pipeline") && isJobsHandoffSrc(jobsSrc);
  const savedActive = location.startsWith("/crm") || onJobsCrmDesk;
  const howActive =
    location.startsWith("/how-it-works") || location.startsWith("/about");
  const pricingActive = location.startsWith("/pricing");
  const robotsActive = location.startsWith("/my-robots");
  const adminActive = location.startsWith("/admin");
  const savedHref = jobsHeaderCrmHref(location, jobsSrc, Boolean(session));
  const findHref = onJobsCrmDesk
    ? jobsHeaderJobsHref(location, search, onJobsCrmDesk)
    : jobsFreshHomeHref();
  const signInHref = loginHref(
    `${location}${search ? `?${search.replace(/^\?/, "")}` : ""}`
  );
  const findClickIntercepts =
    findHref === jobsFreshHomeHref() ? onJobsFreshHomeClick : undefined;

  async function signOut() {
    setMobileMenuOpen(false);
    clearPendingNext();
    await supabase?.auth.signOut();
    window.location.href = "/";
  }

  const links = [
    {
      label: "Find buyers",
      href: findHref,
      active: findActive,
      onClick: findClickIntercepts,
      led: true,
    },
    { label: "How it works", href: "/how-it-works", active: howActive },
    { label: "Pricing", href: "/pricing", active: pricingActive },
    ...(session
      ? [
          { label: "My robots", href: "/my-robots", active: robotsActive },
          { label: "Saved buyers", href: savedHref, active: savedActive },
        ]
      : []),
    ...(session && isAdmin
      ? [{ label: "Admin", href: "/admin", active: adminActive }]
      : []),
  ];

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-700/80 bg-[#0b162f]/98 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between gap-3 px-3 sm:px-4">
          <a
            href="/"
            className="flex items-center gap-2.5 shrink-0 hover:opacity-90 transition-opacity"
          >
            <PixelIcon
              map={KARE_FACE}
              scale={2}
              fill={FACE_EMERALD}
              background="transparent"
            />
            <span className="font-display text-lg font-bold tracking-tight text-slate-100 sm:text-xl">
              ReadyForRobots
            </span>
          </a>

          <nav className="hidden md:flex items-center gap-4 lg:gap-5 font-sans text-sm sm:text-base font-medium">
            {links.map(link => (
              <a
                key={link.label}
                href={link.href}
                onClick={link.onClick}
                className={`inline-flex items-center gap-1.5 ${link.active ? navActive : navIdle}`}
              >
                {link.led && link.active ? (
                  <span className="rfr-led" aria-hidden="true" />
                ) : null}
                {link.label}
              </a>
            ))}
            {session ? (
              <button
                type="button"
                onClick={() => void signOut()}
                className={navIdle}
              >
                Sign out
              </button>
            ) : (
              <>
                <a
                  href={signInHref}
                  className="text-slate-300 transition hover:text-white"
                >
                  Sign in
                </a>
                <a
                  href={EARLY_ACCESS_HREF}
                  className="rounded-xl bg-emerald-400 hover:bg-emerald-300 px-3.5 py-1.5 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-400/20 transition-all"
                >
                  Get early access
                </a>
              </>
            )}
          </nav>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </header>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <div
        className={`fixed top-0 right-0 bottom-0 z-50 flex w-[min(300px,85vw)] flex-col bg-[#0b162f] border-l border-slate-700/80 p-5 shadow-2xl transition-transform duration-300 ease-in-out md:hidden ${
          mobileMenuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/80">
          <div className="flex items-center gap-2">
            <PixelIcon
              map={KARE_FACE}
              scale={2}
              fill={FACE_EMERALD}
              background="transparent"
            />
            <span className="font-display text-base font-bold text-slate-100">
              ReadyForRobots
            </span>
          </div>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-1">
          {links.map(link => (
            <a
              key={link.label}
              href={link.href}
              onClick={e => {
                setMobileMenuOpen(false);
                link.onClick?.(e);
              }}
              className={drawerLink}
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="pt-3 border-t border-slate-700/80 space-y-2">
          {session ? (
            <button
              type="button"
              onClick={() => void signOut()}
              className="w-full rounded-xl border border-slate-600 bg-slate-800/60 py-2.5 text-center text-sm font-semibold text-slate-200 hover:bg-slate-800"
            >
              Sign out
            </button>
          ) : (
            <>
              <a
                href={EARLY_ACCESS_HREF}
                onClick={() => setMobileMenuOpen(false)}
                className="block w-full rounded-xl bg-emerald-400 py-2.5 text-center text-sm font-bold text-slate-950"
              >
                Get early access
              </a>
              <a
                href={signInHref}
                onClick={() => setMobileMenuOpen(false)}
                className="block w-full rounded-xl border border-slate-600 bg-slate-800/60 py-2.5 text-center text-sm font-semibold text-slate-200 hover:bg-slate-800"
              >
                Sign in
              </a>
            </>
          )}
        </div>
      </div>
    </>
  );
}
