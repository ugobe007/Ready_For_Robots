/**
 * Minimal acquisition chrome for /jobs only.
 * No Pipeline / Signals / Find leads / Workspace / Signal chat.
 */
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";

export default function ExperimentHeader() {
  const { session } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-700/80 bg-[#081126]/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4 sm:px-6">
        <Link href="/jobs" className="flex items-center gap-2.5">
          <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
          <span className="font-display text-sm font-bold tracking-tight text-slate-100">
            ReadyForRobots
          </span>
        </Link>
        {session ? null : (
          <Link
            href={loginHref("/jobs")}
            className="text-sm font-medium text-slate-400 transition hover:text-emerald-300"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
