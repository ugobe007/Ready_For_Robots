/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * Responsive mobile drawer + desktop navigation bar.
 */
import { useState, useRef, useEffect } from "react";
import { useRoute, useLocation, useSearch } from "wouter";
import { Menu, X, ChevronDown } from "lucide-react";
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
  showSignalPipelineNav,
} from "@/lib/jobsWorkflow";

const navIdle = "text-slate-400 transition hover:text-slate-200";
const navActive = "border-b-2 border-emerald-400 pb-0.5 text-emerald-400 font-semibold";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const isAdmin = useIsAdmin();
  const [location] = useLocation();
  const search = useSearch();
  const [onJobsSlug] = useRoute("/jobs/:slug");
  
  const [exploreOpen, setExploreOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setExploreOpen(false);
      }
    }
    if (exploreOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [exploreOpen]);

  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  const jobsActive =
    location === "/" || location.startsWith("/?") || Boolean(onJobsSlug);
  const jobsSrc = new URLSearchParams(search).get("src");
  const crmActive =
    location.startsWith("/crm") ||
    (location.startsWith("/pipeline") && isJobsHandoffSrc(jobsSrc));
  const aboutActive = location.startsWith("/about");
  const adminActive = location.startsWith("/admin");
  const showPipeline = showSignalPipelineNav({
    pathname: location,
    src: jobsSrc,
  });
  const crmHref = jobsHeaderCrmHref(location, jobsSrc, Boolean(session));
  const onJobsCrmDesk =
    location.startsWith("/pipeline") && isJobsHandoffSrc(jobsSrc);
  const jobsHref = jobsHeaderJobsHref(location, search, onJobsCrmDesk);
  const signInHref = loginHref(
    `${location}${search ? `?${search.replace(/^\?/, "")}` : ""}`
  );
  const jobsClickIntercepts =
    jobsHref === jobsFreshHomeHref() ? onJobsFreshHomeClick : undefined;

  async function signOut() {
    setMobileMenuOpen(false);
    clearPendingNext();
    await supabase?.auth.signOut();
    window.location.href = "/";
  }

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-700/80 bg-[#0b162f]/98 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between gap-3 px-3 sm:px-4">
          <a
            href={jobsFreshHomeHref()}
            className="flex items-center gap-2.5 shrink-0"
            onClick={onJobsFreshHomeClick}
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

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-4 lg:gap-5 font-sans text-sm sm:text-base font-medium">
            <a
              href={jobsHref}
              className={`inline-flex items-center gap-1.5 ${jobsActive ? navActive : navIdle}`}
              onClick={jobsClickIntercepts}
            >
              {jobsActive ? (
                <span className="rfr-led" aria-hidden="true" />
              ) : null}
              Jobs
            </a>

            {/* Explore Platform Dropdown Menu */}
            <div ref={dropdownRef} className="relative inline-block text-left">
              <button
                type="button"
                onClick={() => setExploreOpen(!exploreOpen)}
                className={`inline-flex items-center gap-1 ${exploreOpen ? "text-emerald-400 font-semibold" : navIdle}`}
                aria-expanded={exploreOpen}
              >
                <span>Explore</span>
                <ChevronDown className={`h-3.5 w-3.5 transition-transform ${exploreOpen ? "rotate-180" : ""}`} />
              </button>

              {exploreOpen && (
                <div className="absolute right-0 top-full mt-2 w-64 border border-slate-700/80 bg-[#0d1b38] p-2 shadow-2xl rounded-xl z-50 normal-case tracking-normal">
                  <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50 mb-1">
                    Platform Links
                  </div>
                  <a
                    href={session ? "/pipeline" : "/?visit=jobs"}
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-emerald-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">📊</span>
                    <div>
                      <div className="font-semibold text-slate-100">Lead Pipeline</div>
                      <div className="text-[11px] text-slate-400 font-normal">Active buyer signals & workspace</div>
                    </div>
                  </a>
                  <a
                    href="/robot-ready"
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-emerald-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">🤖</span>
                    <div>
                      <div className="font-semibold text-slate-100">Robot Ready</div>
                      <div className="text-[11px] text-slate-400 font-normal">Match product URLs to robot jobs</div>
                    </div>
                  </a>
                  <a
                    href={crmHref}
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-emerald-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">🗂️</span>
                    <div>
                      <div className="font-semibold text-slate-100">CRM Accounts</div>
                      <div className="text-[11px] text-slate-400 font-normal">Buyer pool & account staging</div>
                    </div>
                  </a>
                  <a
                    href="/intelligence"
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-cyan-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">📰</span>
                    <div>
                      <div className="font-semibold text-slate-100">Intelligence & HEIR</div>
                      <div className="text-[11px] text-slate-400 font-normal">Humanoid readiness & reports</div>
                    </div>
                  </a>
                  <a
                    href="/roi-calculator"
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-amber-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">💰</span>
                    <div>
                      <div className="font-semibold text-slate-100">RaaS ROI Engine</div>
                      <div className="text-[11px] text-slate-400 font-normal">$8.5k/mo RaaS vs CapEx TCO</div>
                    </div>
                  </a>
                  <a
                    href="/pricing"
                    onClick={() => setExploreOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-purple-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    <span className="text-base">💳</span>
                    <div>
                      <div className="font-semibold text-slate-100">Pricing & Plans</div>
                      <div className="text-[11px] text-slate-400 font-normal">Pro plans & Cal outreach entitlement</div>
                    </div>
                  </a>
                  {isAdmin && (
                    <a
                      href="/admin"
                      onClick={() => setExploreOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 text-xs text-emerald-400 hover:bg-slate-800/60 rounded-lg transition-colors border-t border-slate-700/50 mt-1"
                    >
                      <span className="text-base">⚙️</span>
                      <div>
                        <div className="font-semibold">Admin Panel</div>
                      </div>
                    </a>
                  )}
                </div>
              )}
            </div>

            <a
              href="/newsletter"
              className="rounded-lg border border-emerald-400 px-3 py-1 text-xs font-bold text-emerald-400 hover:bg-emerald-400/10 transition-all"
            >
              Newsletter
            </a>
            <a
              href="/about"
              className={`${aboutActive ? navActive : navIdle}`}
            >
              About
            </a>
            {session || !showPipeline ? (
              <a href={crmHref} className={crmActive ? navActive : navIdle}>
                CRM
              </a>
            ) : null}
            {session ? (
              <>
                {isAdmin ? (
                  <a href="/admin" className={adminActive ? navActive : navIdle}>
                    Admin
                  </a>
                ) : null}
                <button
                  type="button"
                  onClick={() => void signOut()}
                  className={navIdle}
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <a
                  href={signInHref}
                  className="text-slate-300 transition hover:text-white"
                >
                  Sign In
                </a>
                <a
                  href="/signup?next=/&src=header_hero_boost"
                  className="rounded-xl bg-emerald-400 hover:bg-emerald-300 px-3.5 py-1.5 text-xs font-extrabold text-slate-950 shadow-lg shadow-emerald-400/20 transition-all uppercase tracking-wide flex items-center gap-1.5"
                >
                  Create Free Account →
                </a>
              </>
            )}
          </nav>

          {/* Mobile Hamburger Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Menu Drawer */}
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
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          <a
            href="/signup?next=/&src=mobile_hero_boost"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center justify-center gap-2 rounded-xl bg-emerald-400 py-3 text-xs font-extrabold text-slate-950 uppercase tracking-wide shadow-md shadow-emerald-400/20"
          >
            Create Free Account →
          </a>

          <div className="space-y-1">
            <p className="px-1 text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
              Core Pages
            </p>
            <a
              href={jobsHref}
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80"
            >
              <span>Jobs</span>
              {jobsActive ? <span className="rfr-led" /> : null}
            </a>
            <a
              href={session ? "/pipeline" : "/?visit=jobs"}
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80"
            >
              Lead Pipeline
            </a>
            <a
              href="/robot-ready"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80"
            >
              Robot Ready
            </a>
            <a
              href={crmHref}
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80"
            >
              CRM Accounts
            </a>
            <a
              href="/pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/80"
            >
              Pricing & Plans
            </a>
          </div>

          <div className="space-y-1 pt-2 border-t border-slate-700/50">
            <p className="px-1 text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
              Intelligence & Tools
            </p>
            <a
              href="/intelligence"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/80"
            >
              Intelligence & HEIR
            </a>
            <a
              href="/newsletter"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/80"
            >
              Daily Newsletter
            </a>
            <a
              href="/roi-calculator"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/80"
            >
              RaaS ROI Engine
            </a>
            <a
              href="/about"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/80"
            >
              About
            </a>
            {isAdmin && (
              <a
                href="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className="block rounded-lg px-3 py-2.5 text-sm font-semibold text-emerald-400 hover:bg-slate-800/80"
              >
                Admin Panel
              </a>
            )}
          </div>
        </div>

        <div className="pt-3 border-t border-slate-700/80">
          {session ? (
            <button
              type="button"
              onClick={() => void signOut()}
              className="w-full rounded-xl border border-red-500/40 bg-red-500/10 py-2.5 text-center text-sm font-semibold text-red-400 hover:bg-red-500/20"
            >
              Sign Out
            </button>
          ) : (
            <a
              href={signInHref}
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full rounded-xl border border-slate-600 bg-slate-800/60 py-2.5 text-center text-sm font-semibold text-slate-200 hover:bg-slate-800"
            >
              Sign In
            </a>
          )}
        </div>
      </div>
    </>
  );
}
