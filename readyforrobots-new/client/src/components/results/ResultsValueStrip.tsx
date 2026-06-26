/**
 * URL scan results — value proof before signup (parity with pipeline strip).
 */
import { Link } from "wouter";
import { ArrowRight, Sparkles } from "lucide-react";
import { RESULTS_ANONYMOUS_UNLOCK } from "@/components/results/ResultsFomoBanner";

type Props = {
  leadCount: number;
  scanUrl?: string;
  unlockedCount?: number;
};

export default function ResultsValueStrip({ leadCount, scanUrl, unlockedCount }: Props) {
  const signupNext = scanUrl
    ? `/results?url=${encodeURIComponent(scanUrl)}`
    : "/results";
  const unlocked = unlockedCount ?? Math.min(RESULTS_ANONYMOUS_UNLOCK, leadCount);
  const locked = Math.max(leadCount - unlocked, 0);

  return (
    <div className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-emerald-700 mt-0.5" />
        <div>
          <p className="text-xs font-bold text-emerald-900">Real pipeline matches — not a generic list</p>
          <p className="text-[11px] leading-relaxed text-emerald-800/90 mt-0.5">
            {locked > 0 ? (
              <>
                You&apos;re viewing <strong>{unlocked} of {leadCount}</strong> buyers with full signal detail and outreach drafts.
                Sign up free to unlock {locked} more match{locked === 1 ? "" : "es"} and save to your pipeline.
              </>
            ) : (
              <>
                {leadCount} matched buyer{leadCount === 1 ? "" : "s"} with pitch actions and outreach drafts —
                sign up free to copy, save, and track every lead.
              </>
            )}
          </p>
        </div>
      </div>
      <Link
        href={`/signup?next=${encodeURIComponent(signupNext)}`}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-600 bg-white px-3 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
      >
        {locked > 0 ? "Unlock all matches" : "Sign up free — copy draft"}
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
