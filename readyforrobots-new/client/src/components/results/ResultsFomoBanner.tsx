import { Link } from "wouter";
import { ArrowRight, LockKeyhole } from "lucide-react";

export const RESULTS_ANONYMOUS_UNLOCK = 2;

type ProspectLike = {
  priorityTier?: string;
  stage?: string;
};

type Props = {
  prospects: ProspectLike[];
  isSignedIn: boolean;
  scanUrl?: string;
};

export default function ResultsFomoBanner({ prospects, isSignedIn, scanUrl }: Props) {
  const hotCount = prospects.filter(
    (p) => p.priorityTier === "HOT" || (p.stage || "").toUpperCase().includes("HOT"),
  ).length;
  const unlocked = isSignedIn ? prospects.length : Math.min(RESULTS_ANONYMOUS_UNLOCK, prospects.length);
  const locked = Math.max(prospects.length - unlocked, 0);
  const signupNext = scanUrl ? `/results?url=${encodeURIComponent(scanUrl)}` : "/results";

  return (
    <div className="mb-6 rounded-2xl border border-amber-400/40 bg-[#111b30] p-4 shadow-[0_18px_42px_-30px_rgba(245,158,11,0.75)] sm:p-5">
      <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-300">
        Scan complete · act before someone else does
      </p>
      <h2 className="font-display text-xl sm:text-2xl font-bold text-white leading-snug">
        {prospects.length} buyer{prospects.length === 1 ? "" : "s"} align to your product
        {hotCount > 0 ? (
          <>
            {" · "}
            <span className="text-amber-300">{hotCount} HOT</span>
          </>
        ) : null}
      </h2>
      <p className="mt-2 max-w-2xl text-sm text-slate-300">
        Each row shows fit, timing, and why-now context. Next step is the large Pipeline — with instructions — not email drafting here.
      </p>
      {!isSignedIn && locked > 0 && (
        <div className="mt-4 flex flex-col gap-3 rounded-xl border border-amber-400/30 bg-[#081126]/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-2">
            <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
            <p className="text-xs leading-relaxed text-slate-200">
              <strong className="text-white">{unlocked} of {prospects.length} unlocked.</strong> Sign up free to reveal{" "}
              {locked} more aligned lead{locked === 1 ? "" : "s"}, then open Pipeline.
            </p>
          </div>
          <Link
            href={`/signup?next=${encodeURIComponent(signupNext)}`}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-amber-400 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-amber-300"
          >
            Unlock all matches
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
