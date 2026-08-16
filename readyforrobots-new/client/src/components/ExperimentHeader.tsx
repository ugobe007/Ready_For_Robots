/**
 * Minimal acquisition chrome for /experiment only.
 * No Pipeline / Signals / Find leads / Workspace — those contradict the jobs experiment.
 */
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { loginHref } from "@/lib/authNext";
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";

export default function ExperimentHeader() {
  const { session } = useAuth();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-gray-100/80 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4 sm:px-6">
        <Link href="/experiment" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-200/80 bg-white">
            <PixelIcon map={KARE_FACE} scale={2} fill="#059669" background="transparent" />
          </span>
          <span className="font-display text-sm font-bold tracking-tight text-gray-900">
            ReadyForRobots
          </span>
        </Link>
        {session ? null : (
          <Link
            href={loginHref("/experiment")}
            className="text-sm font-medium text-gray-500 hover:text-gray-900"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
