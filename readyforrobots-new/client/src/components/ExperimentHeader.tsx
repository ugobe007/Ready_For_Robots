/**
 * Top panel for /jobs — Kare face + ReadyForRobots, dark brand chrome.
 * JOBS is the current surface (selected marker); ABOUT links to home about.
 */
import { Link, useRoute } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";

export default function ExperimentHeader() {
  const { session } = useAuth();
  const [onJobs] = useRoute("/jobs");
  const [onJobsSlug] = useRoute("/jobs/:slug");
  const jobsActive = onJobs || onJobsSlug;

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-600/90 bg-[#0b162f]">
      <div className="mx-auto flex h-11 max-w-[1200px] items-center justify-between px-3 sm:px-4">
        <Link href="/jobs" className="flex items-center gap-2.5">
          <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
          <span className="font-display text-sm font-bold tracking-tight text-slate-100">
            ReadyForRobots
          </span>
        </Link>
        <nav className="flex items-center gap-5 font-mono text-[11px] font-semibold uppercase tracking-[0.12em]">
          <Link
            href="/jobs"
            className={
              jobsActive
                ? "border-b border-emerald-400 pb-0.5 text-emerald-400"
                : "text-slate-400 transition hover:text-slate-200"
            }
          >
            Jobs
          </Link>
          <Link href="/#about" className="text-slate-400 transition hover:text-slate-200">
            About
          </Link>
          {session ? null : (
            <Link href={loginHref("/jobs")} className="text-slate-400 transition hover:text-slate-200">
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
