/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * JOBS selected on / and /jobs/:slug; ABOUT links to /intelligence.
 * Includes clean Explore ▾ dropdown menu for Pipeline, Robot Ready, CRM, ROI Calculator, and Intelligence.
 */
import { useState, useRef, useEffect } from "react";
import { useRoute, useLocation, useSearch } from "wouter";
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
const navActive = "border-b-2 border-emerald-400 pb-0.5 text-emerald-400";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const isAdmin = useIsAdmin();
  const [location] = useLocation();
  const search = useSearch();
  const [onJobsSlug] = useRoute("/jobs/:slug");
  
  const [exploreOpen, setExploreOpen] = useState(false);
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

  const jobsActive =
    location === "/" || location.startsWith("/?") || Boolean(onJobsSlug);
  const jobsSrc = new URLSearchParams(search).get("src");
  const pipelineActive =
    location.startsWith("/pipeline") && !isJobsHandoffSrc(jobsSrc);
  const crmActive =
    location.startsWith("/crm") ||
    (location.startsWith("/pipeline") && isJobsHandoffSrc(jobsSrc));
  const aboutActive = location.startsWith("/intelligence");
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
    clearPendingNext();
    await supabase?.auth.signOut();
    window.location.href = "/";
  }

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-600/90 bg-[#0b162f]">
      <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between gap-3 px-3 sm:px-4">
        <a
          href={jobsFreshHomeHref()}
          className="flex items-center gap-2.5"
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
        <nav className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 font-sans text-sm font-medium tracking-normal sm:gap-x-5 sm:text-base">
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
              <span className="text-xs opacity-70">▾</span>
            </button>

            {exploreOpen && (
              <div className="absolute right-0 top-full mt-2 w-64 border border-slate-700/80 bg-[#0d1b38] p-2 shadow-2xl rounded-xl z-50 normal-case tracking-normal">
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/50 mb-1">
                  Platform Links
                </div>
                <a
                  href="/pipeline"
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
                  href="/market-insights"
                  onClick={() => setExploreOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 text-xs text-slate-200 hover:text-cyan-400 hover:bg-slate-800/60 rounded-lg transition-colors"
                >
                  <span className="text-base">📈</span>
                  <div>
                    <div className="font-semibold text-slate-100">Market Insights</div>
                    <div className="text-[11px] text-slate-400 font-normal">Vendor deployment tracking</div>
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
            href="/intelligence"
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
                href="/signup?next=/&src=robot_jobs"
                className="rounded-lg bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-purple-500/25 transition hover:bg-purple-500"
              >
                Start free workspace
              </a>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
