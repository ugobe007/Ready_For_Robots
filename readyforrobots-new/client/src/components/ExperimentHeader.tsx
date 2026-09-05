/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * JOBS selected on / and /jobs/:slug; ABOUT links to /intelligence.
 * Jobs chrome hides Pipeline. CRM is step 03 (`/pipeline?src=jobs_activate`)
 * and is in the header on Jobs chrome even when signed out.
 */
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
        <nav className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 font-mono text-sm font-semibold uppercase tracking-[0.08em] sm:gap-x-5 sm:text-base">
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
          <a
            href="/intelligence"
            className={`${aboutActive ? navActive : navIdle}`}
          >
            About
          </a>
          {showPipeline ? (
            <a
              href="/pipeline"
              className={pipelineActive ? navActive : navIdle}
            >
              Pipeline
            </a>
          ) : null}
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
            <a
              href={signInHref}
              className="border px-4 py-2 text-emerald-400 transition hover:bg-white/5"
              style={{ borderColor: "#1E8F6B" }}
            >
              Sign In
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}
