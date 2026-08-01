import { useMemo, useState } from "react";
import { ArrowRight, Building2, Factory, LogIn, Search } from "lucide-react";
import { Link } from "wouter";

type WorkflowKind = "robot_company" | "buyer";

const buyerReasons = [
  "Labor shortage",
  "Throughput bottlenecks",
  "Quality issues",
  "Safety risk",
  "Cost pressure",
  "Expansion planning",
];

const robotCompanyFocus = [
  "Warehouse and logistics buyers",
  "Manufacturing buyers",
  "Food and beverage buyers",
  "Healthcare and medtech buyers",
  "Airport and mobility buyers",
  "Retail and service buyers",
];

function normalizeUrlInput(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) return trimmed;
  return `https://${trimmed}`;
}

function Logo() {
  return (
    <div className="flex items-center gap-3">
      <img src="/logo-r.png" alt="ReadyForRobots" className="h-8 w-8 rounded-[9px] object-contain" />
      <div className="leading-none">
        <div className="text-[13px] font-bold tracking-[.13em] text-white">READYFORROBOTS</div>
        <div className="mt-1 text-[9px] tracking-[.3em] text-[#58c4ea]">SIGNAL / WORKFLOW</div>
      </div>
    </div>
  );
}

export default function Home() {
  const [workflow, setWorkflow] = useState<WorkflowKind | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [urlConfirmed, setUrlConfirmed] = useState(false);
  const [selectedIntent, setSelectedIntent] = useState<string | null>(null);

  const normalizedUrl = useMemo(() => normalizeUrlInput(urlInput), [urlInput]);
  const currentStep = !workflow ? 1 : !urlConfirmed ? 2 : 3;
  const options = workflow === "buyer" ? buyerReasons : robotCompanyFocus;

  const primaryHref = useMemo(() => {
    if (workflow === "robot_company") {
      return "/signup?next=/pipeline";
    }
    return "/signup?next=/results";
  }, [workflow]);

  const handleContinueUrl = () => {
    if (!normalizedUrl) return;
    setUrlConfirmed(true);
  };

  return (
    <main className="min-h-screen bg-[#081126] text-[#edf4f3]">
      <div className="mx-auto max-w-[1120px] px-5 pb-16 pt-8 lg:px-8 lg:pb-24">
        <header className="mb-10 flex items-center justify-between">
          <Link href="/" className="shrink-0">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10"
            >
              <LogIn className="h-3.5 w-3.5" />
              Sign in
            </Link>
          </div>
        </header>

        <section className="relative overflow-hidden rounded-3xl border border-[#214066] bg-[#0c1a33] p-6 shadow-[0_40px_100px_rgba(8,17,38,0.65)] lg:p-10">
          <div className="pointer-events-none absolute -right-24 -top-20 h-64 w-64 rounded-full bg-[#38bdf8]/20 blur-3xl" aria-hidden />
          <div className="pointer-events-none absolute -left-24 bottom-[-90px] h-64 w-64 rounded-full bg-[#00c896]/14 blur-3xl" aria-hidden />

          <div className="relative grid gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#58c4ea]">Step 1-2-3 Workflow</p>
              <h1 className="mt-4 text-[clamp(2.1rem,5.2vw,4.2rem)] font-semibold leading-[0.95] tracking-[-0.04em] text-white">
                Start with your URL.
                <br />
                Then we guide your next move.
              </h1>
              <p className="mt-5 max-w-[560px] text-[15px] leading-7 text-[#9ab2c9]">
                Two workflows: one for robot companies building pipeline, and one for potential customers evaluating automation.
                Active users can skip this flow and sign in immediately.
              </p>

              <div className="mt-8 rounded-2xl border border-[#27466f] bg-[#0a1730] p-4">
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#86a5c5]">Current step</p>
                  <p className="text-xs font-semibold text-[#58c4ea]">Step {currentStep} of 3</p>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-[#112645]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#00c896] to-[#38bdf8] transition-all duration-300"
                    style={{ width: `${(currentStep / 3) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="relative rounded-2xl border border-[#2a4b73] bg-[#0b1a36] p-5 lg:p-6">
              <div className="space-y-5">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#7fa2c8]">Step 1</p>
                  <p className="mt-1 text-base font-semibold text-white">Who are you?</p>
                  <div className="mt-3 grid gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setWorkflow("robot_company");
                        setUrlConfirmed(false);
                        setSelectedIntent(null);
                      }}
                      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition ${
                        workflow === "robot_company"
                          ? "border-[#00c896] bg-[#0f2b3e]"
                          : "border-[#2b4a71] bg-[#0a1832] hover:border-[#3c6494]"
                      }`}
                    >
                      <Factory className="mt-0.5 h-4 w-4 text-[#00c896]" />
                      <div>
                        <p className="text-sm font-semibold text-white">Robot company</p>
                        <p className="mt-0.5 text-xs text-[#8eabc8]">Identify and rank buyers, then move deals in pipeline.</p>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setWorkflow("buyer");
                        setUrlConfirmed(false);
                        setSelectedIntent(null);
                      }}
                      className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition ${
                        workflow === "buyer"
                          ? "border-[#38bdf8] bg-[#0e2a42]"
                          : "border-[#2b4a71] bg-[#0a1832] hover:border-[#3c6494]"
                      }`}
                    >
                      <Building2 className="mt-0.5 h-4 w-4 text-[#58c4ea]" />
                      <div>
                        <p className="text-sm font-semibold text-white">Potential customer</p>
                        <p className="mt-0.5 text-xs text-[#8eabc8]">Evaluate where automation fits and why now.</p>
                      </div>
                    </button>
                  </div>
                </div>

                <div className={workflow ? "opacity-100" : "opacity-45 pointer-events-none"}>
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#7fa2c8]">Step 2</p>
                  <p className="mt-1 text-base font-semibold text-white">Enter your company URL</p>
                  <div className="mt-3 flex gap-2 rounded-xl border border-[#2b4a71] bg-[#09152b] p-2">
                    <Search className="ml-2 mt-2 h-4 w-4 shrink-0 text-[#7ea0c5]" />
                    <input
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      placeholder="example.com"
                      className="w-full bg-transparent py-2 text-sm text-white outline-none placeholder:text-[#6f89a8]"
                    />
                    <button
                      type="button"
                      onClick={handleContinueUrl}
                      disabled={!workflow || !normalizedUrl}
                      className="rounded-lg bg-[#00c896] px-3.5 py-2 text-xs font-bold text-[#07221c] disabled:opacity-50"
                    >
                      Continue
                    </button>
                  </div>
                  {urlConfirmed && (
                    <p className="mt-2 text-xs text-[#7fd8be]">URL captured: {normalizedUrl}</p>
                  )}
                </div>

                <div className={urlConfirmed ? "opacity-100" : "opacity-45 pointer-events-none"}>
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#7fa2c8]">Step 3</p>
                  <p className="mt-1 text-base font-semibold text-white">
                    {workflow === "robot_company"
                      ? "Which buyer segment should we prioritize first?"
                      : "What problem are you trying to automate first?"}
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {options.map((option) => (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setSelectedIntent(option)}
                        className={`rounded-lg border px-3 py-2 text-left text-xs transition ${
                          selectedIntent === option
                            ? "border-[#00c896] bg-[#0f2b3e] text-white"
                            : "border-[#2b4a71] bg-[#0a1832] text-[#9bb5cf] hover:border-[#3c6494]"
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl border border-[#2b4a71] bg-[#09182f] p-4">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#7fa2c8]">Next</p>
                  <p className="mt-1 text-sm text-[#c8d8ea]">
                    {workflow === "robot_company"
                      ? "Create your workspace to save ranked buyers and guidance in pipeline."
                      : "Create your workspace to save automation guidance and matched opportunities."}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <Link
                      href={primaryHref}
                      className="inline-flex items-center gap-2 rounded-lg bg-[#00c896] px-4 py-2.5 text-sm font-bold text-[#06261f]"
                    >
                      Activate workflow
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link href="/login" className="text-xs font-semibold text-[#7fa2c8] hover:text-white">
                      Already active? Sign in
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border border-[#24466f] bg-[#0d1d3a] p-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#58c4ea]">Robot companies</p>
            <p className="mt-1 text-sm text-[#a7bfd7]">Find qualified buyers, understand intent, and move deals with pipeline guidance.</p>
          </div>
          <div className="rounded-xl border border-[#24466f] bg-[#0d1d3a] p-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#58c4ea]">Potential customers</p>
            <p className="mt-1 text-sm text-[#a7bfd7]">Identify automation problems, urgency drivers, and likely robot fit.</p>
          </div>
          <div className="rounded-xl border border-[#24466f] bg-[#0d1d3a] p-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#58c4ea]">Returning users</p>
            <p className="mt-1 text-sm text-[#a7bfd7]">Skip the workflow via Sign in and continue directly in your workspace.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
