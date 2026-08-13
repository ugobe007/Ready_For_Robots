/**
 * Results sticky CTA — Pipeline only. No prepare/draft/email actions on Results.
 * Flow: URL → signup → 5 leads → customer info → 15 matched leads.
 */
import { ArrowRight, CheckCircle2, Circle } from "lucide-react";
import { Link } from "wouter";

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
    { label: "3. 5 sales leads", done: matchCount > 0 && isSignedIn, active: isSignedIn && matchCount > 0 },
    { label: "4. Customer info", done: false, active: false },
    { label: "5. 15 sales leads", done: false },
  ];

  const href = isSignedIn ? pipelineHref : signupHref;
  const label = isSignedIn
    ? "Next: provide customer name & information"
    : "Sign up to see 5 sales leads";

  return (
    <div className="sticky bottom-3 z-40 mt-8">
      <div className="rounded-2xl border border-amber-400/45 bg-[#0b162f]/95 p-4 shadow-[0_24px_60px_-20px_rgba(0,0,0,0.9)] backdrop-blur-md sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-300">Next step</p>
            <h3 className="mt-1 text-lg font-bold text-white sm:text-xl">
              {isSignedIn ? "Unlock 15 matched sales leads" : "Create your free account"}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-300">
              {isSignedIn
                ? `${matchCount > 0 ? `${matchCount} leads reviewed. ` : ""}Next: provide customer name and information, then open your 15 matched sales leads.`
                : "Sign up, review 5 sales leads, provide customer name and information, then unlock 15 matched leads."}
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
                  {step.done ? <CheckCircle2 className="h-3 w-3" /> : <Circle className="h-3 w-3" />}
                  {step.label}
                </li>
              ))}
            </ol>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[280px]">
            <Link
              href={href}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-amber-300"
            >
              {label}
              <ArrowRight className="h-4 w-4" />
            </Link>
            <p className="text-center text-[11px] text-slate-400">
              Customer info on Pipeline · then 15 matched leads
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
