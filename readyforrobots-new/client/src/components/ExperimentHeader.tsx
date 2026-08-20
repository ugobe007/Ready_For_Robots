/**
 * Top panel for product front door — Kare face + ReadyForRobots, dark brand chrome.
 * JOBS selected on / and /jobs/:slug; ABOUT links to /intelligence.
 * Sign In / Sign Out stay in the upper-right so a session can be cleared for a fresh run.
 */
import { Link, useRoute, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref, clearPendingNext } from "@/lib/authNext";
import { supabase } from "@/lib/supabase";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";

const navIdle = "text-slate-400 transition hover:text-slate-200";
const navActive = "border-b border-emerald-400 pb-0.5 text-emerald-400";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const [location] = useLocation();
  const [onJobsSlug] = useRoute("/jobs/:slug");
  const jobsActive = location === "/" || location.startsWith("/?") || Boolean(onJobsSlug);
  const pipelineHref = "/pipeline";

  async function signOut() {
    clearPendingNext();
    await supabase?.auth.signOut();
    window.location.href = "/";
  }

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-600/90 bg-[#0b162f]">
      <div className="mx-auto flex h-11 max-w-[1200px] items-center justify-between px-3 sm:px-4">
        <Link href="/" className="flex items-center gap-2.5">
          <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
          <span className="font-display text-sm font-bold tracking-tight text-slate-100">
            ReadyForRobots
          </span>
        </Link>
        <nav className="flex items-center gap-5 font-mono text-[11px] font-semibold uppercase tracking-[0.12em]">
          <Link href="/" className={jobsActive ? navActive : navIdle}>
            Jobs
          </Link>
          <Link href="/intelligence" className={navIdle}>
            About
          </Link>
          {session ? (
            <>
              <Link
                href={pipelineHref}
                className={location.startsWith("/pipeline") ? navActive : navIdle}
              >
                Pipeline
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
