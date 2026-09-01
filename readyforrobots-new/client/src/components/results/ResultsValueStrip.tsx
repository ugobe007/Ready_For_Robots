/**
 * URL scan results — OemCal value proof before signup.
 */
import { Link } from "wouter";
import { ArrowRight, Sparkles } from "lucide-react";
import { RESULTS_ANONYMOUS_UNLOCK } from "@/components/results/ResultsFomoBanner";
import {
  OEM_CAL_RESULTS_CTA_ANON,
  OEM_CAL_RESULTS_STRIP_TITLE,
  oemCalResultsStripBody,
} from "@/lib/oemCalCopy";

type Props = {
  leadCount: number;
  scanUrl?: string;
  unlockedCount?: number;
};

export default function ResultsValueStrip({
  leadCount,
  scanUrl,
  unlockedCount,
}: Props) {
  const signupNext = scanUrl
    ? `/results?url=${encodeURIComponent(scanUrl)}`
    : "/results";
  const unlocked =
    unlockedCount ?? Math.min(RESULTS_ANONYMOUS_UNLOCK, leadCount);
  const locked = Math.max(leadCount - unlocked, 0);

  return (
    <div className="mb-6 flex flex-col gap-3 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 sm:flex-row sm:items-center">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
        <div>
          <p className="text-xs font-bold text-emerald-100">
            {OEM_CAL_RESULTS_STRIP_TITLE}
          </p>
          <p className="mt-0.5 text-[11px] leading-relaxed text-emerald-100/80">
            {oemCalResultsStripBody(unlocked, leadCount, locked)}
          </p>
        </div>
      </div>
      <Link
        href={`/signup?next=${encodeURIComponent(signupNext)}`}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-300 px-3 py-2 text-xs font-bold text-emerald-950 hover:bg-emerald-200"
      >
        {locked > 0
          ? OEM_CAL_RESULTS_CTA_ANON
          : "Sign up free — copy Cal's note"}
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
