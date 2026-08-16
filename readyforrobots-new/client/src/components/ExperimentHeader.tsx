/**
 * Top panel for /jobs — Kare face + ReadyForRobots, dark brand chrome.
 */
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";

export default function ExperimentHeader() {
  const { session } = useAuth();

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
          <Link href="/jobs" className="text-emerald-400">
            Jobs
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
