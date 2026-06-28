/**
 * Anonymous pipeline — summarize proof visible before signup.
 */
import { Link } from "wouter";
import { ArrowRight, Sparkles } from "lucide-react";

type Props = {
  leadCount: number;
  limit: number;
};

export default function AnonymousValueStrip({ leadCount, limit }: Props) {
  return (
    <div className="pipeline-value-strip flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="flex items-start gap-2 flex-1 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-emerald-700 mt-0.5" />
        <div>
          <p className="pipeline-value-strip-title">See value before you sign up</p>
          <p className="pipeline-value-strip-body">
            Browse {Math.min(leadCount, limit)} live leads with pitch actions, robot types, and outreach drafts —
            no account required. Free workspace adds save, copy, and HubSpot sync.
          </p>
        </div>
      </div>
      <Link
        href="/signup?next=/pipeline"
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-emerald-600 bg-white px-3 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
      >
        Start free
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}
