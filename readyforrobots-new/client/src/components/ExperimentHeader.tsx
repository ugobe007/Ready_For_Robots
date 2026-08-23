/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * JOBS selected on / and /jobs/:slug; ABOUT links to /intelligence.
 * Jobs chrome hides Pipeline. CRM on Jobs is `/crm?src=jobs_activate`.
 * SIGNAL `/pipeline` and `/crm` still show Pipeline.
 */
import { Link, useRoute, useLocation, useSearch } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref, clearPendingNext } from "@/lib/authNext";
import { supabase } from "@/lib/supabase";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  jobsFreshHomeHref,
  jobsHeaderCrmHref,
  onJobsFreshHomeClick,
  showSignalPipelineNav,
} from "@/lib/jobsWorkflow";

const navIdle = "text-slate-400 transition hover:text-slate-200";
const navActive = "border-b-2 border-emerald-400 pb-0.5 text-emerald-400";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const [location] = useLocation();
  const search = useSearch();
  const [onJobsSlug] = useRoute("/jobs/:slug");
  const jobsActive = location === "/" || location.startsWith("/?") || Boolean(onJobsSlug);
  const pipelineActive = location.startsWith("/pipeline");
  const crmActive = location.startsWith("/crm");
  const aboutActive = location.startsWith("/intelligence");
  const jobsSrc = new URLSearchParams(search).get("src");
  const showPipeline = showSignalPipelineNav({ pathname: location, src: jobsSrc });
  const crmHref = jobsHeaderCrmHref(location, jobsSrc);

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
          <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
          <span className="font-display text-lg font-bold tracking-tight text-slate-100 sm:text-xl">
            ReadyForRobots
          </span>
        </a>
        <nav className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 font-mono text-sm font-semibold uppercase tracking-[0.08em] sm:gap-x-5 sm:text-base">
          <a
            href={jobsFreshHomeHref()}
            className={`inline-flex items-center gap-1.5 ${jobsActive ? navActive : navIdle}`}
            onClick={onJobsFreshHomeClick}
          >
            {jobsActive ? <span className="rfr-led" aria-hidden="true" /> : null}
            Jobs
          </a>
          <Link href="/intelligence" className={`${aboutActive ? navActive : navIdle} max-sm:hidden`}>
            About
          </Link>
          {showPipeline ? (
            <Link
              href="/pipeline"
              className={pipelineActive ? navActive : navIdle}
            >
              Pipeline
            </Link>
          ) : null}
          {session ? (
            <>
              <Link href={crmHref} className={crmActive ? navActive : navIdle}>
                CRM
              </Link>
              <button type="button" onClick={() => void signOut()} className={navIdle}>
                Sign Out
              </button>
            </>
          ) : (
            <Link href={loginHref("/")} className={navIdle}>
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
