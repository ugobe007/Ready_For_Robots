/**
 * URL scan results — value proof before signup (parity with pipeline strip).
 */
import { Link } from "wouter";
import { ArrowRight, Sparkles } from "lucide-react";

type Props = {
  leadCount: number;
  scanUrl?: string;
};

export default function ResultsValueStrip({ leadCount, scanUrl }: Props) {
  const signupNext = scanUrl
    ? `/results?url=${encodeURIComponent(scanUrl)}`
    : "/results";

  return (
    <div className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-emerald-700 mt-0.5" />
        <div>
          <p className="text-xs font-bold text-emerald-900">See value before you sign up</p>
          <p className="text-[11px] leading-relaxed text-emerald-800/90 mt-0.5">
            {leadCount} matched buyer{leadCount === 1 ? "" : "s"} with pitch actions and outreach drafts —
            read the full draft below, then sign up free to save and copy.
          </p>
        </div>
      </div>
      <Link
        href={`/signup?next=${encodeURIComponent(signupNext)}`}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-600 bg-white px-3 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
      >
        Sign up free — copy draft
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
