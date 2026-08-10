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
    <div className="mb-6 flex flex-col gap-3 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 sm:flex-row sm:items-center">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
        <div>
          <p className="text-xs font-bold text-emerald-100">Qualified alignment matches — not a generic list</p>
          <p className="mt-0.5 text-[11px] leading-relaxed text-emerald-100/80">
            {locked > 0 ? (
              <>
                You&apos;re viewing <strong>{unlocked} of {leadCount}</strong> buyers with full signal detail, alignment context, and outreach drafts.
                Sign up free to unlock {locked} more match{locked === 1 ? "" : "es"} and save to your pipeline.
              </>
            ) : (
              <>
                {leadCount} matched buyer{leadCount === 1 ? "" : "s"} with alignment actions and outreach drafts —
                sign up free to copy, save, and track every lead.
              </>
            )}
          </p>
        </div>
      </div>
      <Link
        href={`/signup?next=${encodeURIComponent(signupNext)}`}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-300 px-3 py-2 text-xs font-bold text-emerald-950 hover:bg-emerald-200"
      >
        {locked > 0 ? "Unlock all matches" : "Sign up free — copy draft"}
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
