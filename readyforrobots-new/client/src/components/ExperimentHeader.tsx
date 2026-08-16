/**
 * Minimal acquisition chrome for /experiment only.
 * No Pipeline / Signals / Find leads / Workspace — those contradict the jobs experiment.
 */
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";

/** Brand emerald — matches Find leads / primary CTA (#059669). */
const BRAND = "#059669";

export default function ExperimentHeader() {
  const { session } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-200/70 bg-white/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4 sm:px-6">
        <Link href="/experiment" className="flex items-center gap-2.5">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-[9px] shadow-sm"
            style={{ background: BRAND }}
          >
            <PixelIcon map={KARE_FACE} scale={2} fill="#ffffff" background="transparent" />
          </span>
          <span className="font-display text-sm font-bold tracking-tight text-slate-900">
            ReadyForRobots
          </span>
        </Link>
        {session ? null : (
          <Link
            href={loginHref("/experiment")}
            className="text-sm font-medium text-slate-500 transition hover:text-emerald-700"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
