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
    <div className="mb-6 rounded-2xl border border-amber-300 bg-gradient-to-br from-amber-50 to-white p-4 sm:p-5 shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-800 mb-2">
        Scan complete · act before someone else does
      </p>
      <h2 className="font-display text-xl sm:text-2xl font-bold text-gray-900 leading-snug">
        {prospects.length} buyer{prospects.length === 1 ? "" : "s"} align to your product
        {hotCount > 0 ? (
          <>
            {" · "}
            <span className="text-amber-800">{hotCount} HOT</span>
          </>
        ) : null}
      </h2>
      <p className="mt-2 text-sm text-gray-700 max-w-2xl">
        Each row includes robot types, timing, and a rep-voice outreach draft with alignment context. Generic list tools do not provide this.
      </p>
      {!isSignedIn && locked > 0 && (
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-blue-200 bg-blue-50/80 px-4 py-3">
          <div className="flex items-start gap-2">
            <LockKeyhole className="h-4 w-4 shrink-0 text-blue-800 mt-0.5" />
            <p className="text-xs leading-relaxed text-blue-950">
              <strong>{unlocked} of {prospects.length} unlocked.</strong> Sign up free to reveal{" "}
              {locked} more aligned lead{locked === 1 ? "" : "s"}, copy drafts, and save to your pipeline.
            </p>
          </div>
          <Link
            href={`/signup?next=${encodeURIComponent(signupNext)}`}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-blue-700 px-4 py-2 text-xs font-bold text-white hover:bg-blue-800"
          >
            Unlock all matches
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
