/**
 * Results page — always-visible next-step CTA so the scan → pipeline workflow is obvious.
 */
import { ArrowRight, CheckCircle2, Circle } from "lucide-react";
import { Link } from "wouter";

type Props = {
  isSignedIn: boolean;
  matchCount: number;
  activating?: boolean;
  onPrepareTop: () => void;
  pipelineHref: string;
  signupHref: string;
};

export default function ResultsNextStepCta({
  isSignedIn,
  matchCount,
  activating = false,
  onPrepareTop,
  pipelineHref,
  signupHref,
}: Props) {
  const steps = [
    { label: "Find jobs", done: true },
    { label: "Review matches", done: matchCount > 0 },
    { label: "Work pipeline", done: false, active: true },
  ];

  return (
    <div className="sticky bottom-3 z-40 mt-8">
      <div className="rounded-2xl border border-amber-400/45 bg-[#0b162f]/95 p-4 shadow-[0_24px_60px_-20px_rgba(0,0,0,0.9)] backdrop-blur-md sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-300">Next step</p>
            <h3 className="mt-1 text-lg font-bold text-white sm:text-xl">
              {isSignedIn
                ? "Prepare your top buyers, then work them in Pipeline"
                : "Create a free workspace to save matches and open Pipeline"}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-300">
              {matchCount > 0
                ? `${matchCount} job opportunities found. Find the work → match the robot → win the customer.`
                : "Once matches load, move the strongest buyers into your working pipeline."}
            </p>
            <ol className="mt-3 flex flex-wrap items-center gap-2">
              {steps.map((step) => (
                <li
                  key={step.label}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                    step.done
                      ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200"
                      : step.active
                        ? "border-amber-400/50 bg-amber-400/15 text-amber-100"
                        : "border-white/10 text-slate-500"
                  }`}
                >
                  {step.done ? (
                    <CheckCircle2 className="h-3 w-3" />
                  ) : (
                    <Circle className="h-3 w-3" />
                  )}
                  {step.label}
                </li>
              ))}
            </ol>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[260px]">
            {isSignedIn ? (
              <button
                type="button"
                onClick={onPrepareTop}
                disabled={activating || matchCount === 0}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {activating ? "Preparing…" : "Next step: Prepare top 3"}
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <Link
                href={signupHref}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-amber-300"
              >
                Next step: Start free workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
            )}
            <Link
              href={pipelineHref}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-2.5 text-xs font-semibold text-slate-100 transition hover:bg-white/10"
            >
              {isSignedIn ? "Open Pipeline now" : "Preview Pipeline"}
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
