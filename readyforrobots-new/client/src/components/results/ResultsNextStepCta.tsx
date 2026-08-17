/**
 * Results sticky CTA — Pipeline only. OemCal commercial proof voice.
 * Flow: URL → signup → 5 leads → customer info → 15 matched leads.
 */
import { ArrowRight, CheckCircle2, Circle } from "lucide-react";
import { Link } from "wouter";
import {
  OEM_CAL_RESULTS_CTA_ANON,
  OEM_CAL_RESULTS_CTA_SIGNED,
  oemCalResultsAnonLine,
  oemCalResultsSignedLine,
} from "@/lib/oemCalCopy";

type Props = {
  matchCount: number;
  pipelineHref: string;
  isSignedIn: boolean;
  signupHref?: string;
};

export default function ResultsNextStepCta({
  matchCount,
  pipelineHref,
  isSignedIn,
  signupHref = "/signup",
}: Props) {
  const steps = [
    { label: "1. URL", done: true },
    { label: "2. Sign up", done: isSignedIn },
    { label: "3. 5 leads", done: matchCount > 0 && isSignedIn, active: isSignedIn && matchCount > 0 },
    { label: "4. Info", done: false },
    { label: "5. 15 leads", done: false },
  ];

  const href = isSignedIn ? pipelineHref : signupHref;
  const label = isSignedIn ? OEM_CAL_RESULTS_CTA_SIGNED : OEM_CAL_RESULTS_CTA_ANON;

  return (
    <div className="sticky bottom-2 z-40 mt-6">
      <div className="rounded-lg border border-amber-400/50 bg-[#0b162f]/95 px-3 py-2 backdrop-blur-md">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold text-emerald-200">
              <span className="uppercase tracking-[0.14em] text-amber-300">Cal · OEM · </span>
              {isSignedIn ? oemCalResultsSignedLine(matchCount) : oemCalResultsAnonLine(matchCount)}
            </p>
            <ol className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
              {steps.map((step) => (
                <li
                  key={step.label}
                  className={`inline-flex items-center gap-0.5 text-[10px] font-medium ${
                    step.done
                      ? "text-emerald-300"
                      : step.active
                        ? "text-amber-200"
                        : "text-slate-500"
                  }`}
                >
                  {step.done ? <CheckCircle2 className="h-2.5 w-2.5" /> : <Circle className="h-2.5 w-2.5" />}
                  {step.label}
                </li>
              ))}
            </ol>
          </div>
          <Link
            href={href}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md border border-amber-400 bg-amber-400 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-amber-300"
          >
            {label}
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
