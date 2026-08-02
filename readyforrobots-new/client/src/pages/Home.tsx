import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowRight, CheckCircle2, LogIn, Search, Sparkles } from "lucide-react";
import { Link, useLocation } from "wouter";
import { fetchHomepageLeadPool } from "@/lib/homepageLeads";

const rotatingLeads = [
  "Accor Hotels - housekeeping automation expansion",
  "DHL Supply Chain - warehouse AMR procurement",
  "Kroger Fulfillment - palletizing automation buildout",
  "Mayo Clinic - autonomous transport pilot",
  "Port of Rotterdam - yard automation RFP",
  "Boeing Charleston - inspection robotics initiative",
];

const howItWorks = [
  { id: "01", title: "Show me customers", body: "Start with companies most likely to buy automation right now." },
  { id: "02", title: "Why these customers", body: "Get the context your sales team needs to qualify quickly." },
  { id: "03", title: "Who do I call", body: "See likely buyer roles so reps can move from research to outreach." },
  { id: "04", title: "Help me contact them", body: "Use guided outreach to start better conversations and book meetings." },
];

const previewLeadPool = [
  {
    company: "Walmart Distribution",
    signal: "Facility expansion",
    fit: "Warehouse robotics",
    score: 97,
    specialReason: "Large-scale fulfillment expansion usually creates immediate AMR and picking demand across multiple sites.",
  },
  {
    company: "FedEx Ground",
    signal: "Labor shortage",
    fit: "Sortation robotics",
    score: 95,
    specialReason: "Sustained labor pressure in high-volume hubs pushes faster buy-cycles for dock and sortation automation.",
  },
  {
    company: "Target Supply Chain",
    signal: "CapEx announcement",
    fit: "Palletizing",
    score: 93,
    specialReason: "Fresh CapEx signals budgeted automation projects, which usually shortens vendor evaluation timelines.",
  },
  {
    company: "UPS Healthcare",
    signal: "Executive change",
    fit: "Autonomous transport",
    score: 90,
    specialReason: "Leadership transitions often reset operations priorities and open new automation initiatives.",
  },
  {
    company: "Maersk Terminals",
    signal: "RFP activity",
    fit: "Yard automation",
    score: 88,
    specialReason: "Live RFP activity means the buying window is active now, not theoretical.",
  },
  {
    company: "Kroger Fulfillment",
    signal: "Procurement filing",
    fit: "Case handling robotics",
    score: 92,
    specialReason: "Procurement filings are direct evidence that purchasing teams are actively sourcing solutions.",
  },
  {
    company: "Boeing Charleston",
    signal: "Inspection mandate",
    fit: "Vision inspection",
    score: 89,
    specialReason: "Compliance-driven inspection projects usually carry high urgency and executive visibility.",
  },
  {
    company: "Mayo Clinic Logistics",
    signal: "Throughput bottleneck",
    fit: "Autonomous carts",
    score: 87,
    specialReason: "Healthcare throughput bottlenecks are expensive, so transport automation often gets prioritized quickly.",
  },
];

const analysisChecklist = [
  "What you sell",
  "Who typically buys",
  "Where demand is growing",
  "Which accounts look ready now",
  "Who likely owns the decision",
  "How to start the conversation",
] as const;

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

function StepFrame({ title, copy, children }: { title: string; copy: string; children: ReactNode }) {
  return (
    <div className="mx-auto mt-8 w-full max-w-3xl text-center">
      <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-slate-50">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-300">{copy}</p>
      <div className="mt-6">{children}</div>
    </div>
  );
}

export default function Home() {
  const [location, setLocation] = useLocation();
  const [urlInput, setUrlInput] = useState("");
  const [leadIndex, setLeadIndex] = useState(0);
  const [previewLeadOffset, setPreviewLeadOffset] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [unlockMoreCount, setUnlockMoreCount] = useState(417);

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const journeyUrl = params.get("company_url") || "";
  const workflowFromQuery = params.get("wf") === "buyer" ? "looking_for_robots" : params.get("wf") === "robot_company" ? "robot_company" : null;
  const resolvedWorkflow = workflowFromQuery;
  const normalizedUrl = useMemo(() => normalizeUrlInput(urlInput || journeyUrl), [journeyUrl, urlInput]);
  const pageMode: "url" | "identity" | "preview" = location === "/journey/identity" ? "identity" : location === "/journey/preview" || location === "/journey/activate" ? "preview" : "url";

  const previewLeads = useMemo(() => {
    return Array.from({ length: 5 }, (_, index) => {
      const i = (previewLeadOffset + index) % previewLeadPool.length;
      return previewLeadPool[i];
    });
  }, [previewLeadOffset]);

  useEffect(() => {
    const timer = window.setInterval(() => setLeadIndex((prev) => (prev + 1) % rotatingLeads.length), 1800);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    setPreviewLeadOffset(Math.floor(Math.random() * previewLeadPool.length));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPreviewLeadOffset((prev) => (prev + 1) % previewLeadPool.length);
    }, 7500);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let active = true;
    void fetchHomepageLeadPool<{
      id?: number;
      company_name?: string;
      website?: string | null;
      website_domain?: string | null;
    }>([]).then((pool) => {
      if (!active) return;
      const total = Number(pool.summary?.total ?? pool.leads.length);
      if (!Number.isFinite(total) || total <= 0) return;
      setUnlockMoreCount(Math.max(1, total - 1));
    }).catch(() => {
      // Keep fallback count when live summary is unavailable.
    });
    return () => {
      active = false;
    };
  }, []);

  const activateHref = useMemo(() => {
    if (!normalizedUrl) return "/signup";
    const nextParams = new URLSearchParams();
    nextParams.set("next", "/pipeline");
    const resolvedWf = resolvedWorkflow === "looking_for_robots" ? "buyer" : "robot_company";
    nextParams.set("wf", resolvedWf);
    nextParams.set("company_url", normalizedUrl);
    nextParams.set("preview_limit", "5");
    nextParams.set("src", "home_workflow");
    return `/signup?${nextParams.toString()}`;
  }, [normalizedUrl, resolvedWorkflow]);

  const goToIdentity = () => {
    if (!normalizedUrl) return;
    setLocation(`/journey/identity?company_url=${encodeURIComponent(normalizedUrl)}`);
  };

  const persistWorkflowContext = () => {
    if (typeof window === "undefined" || !normalizedUrl || !resolvedWorkflow) return;
    window.sessionStorage.setItem(
      "rfr_workflow_context",
      JSON.stringify({
        wf: resolvedWorkflow === "robot_company" ? "robot_company" : "buyer",
        company_url: normalizedUrl,
        preview_limit: 5,
        src: "home_workflow",
        ts: Date.now(),
      }),
    );
  };

  useEffect(() => {
    if (pageMode !== "identity") {
      setAnalysisProgress(0);
      return;
    }
    setAnalysisProgress(0);
    const timer = window.setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= analysisChecklist.length) {
          window.clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 420);
    return () => window.clearInterval(timer);
  }, [pageMode]);

  useEffect(() => {
    if (pageMode !== "identity" || !normalizedUrl || analysisProgress < analysisChecklist.length) return;
    const doneTimer = window.setTimeout(() => {
      const wf = resolvedWorkflow === "looking_for_robots" ? "buyer" : "robot_company";
      setLocation(`/journey/preview?company_url=${encodeURIComponent(normalizedUrl)}&wf=${wf}`);
    }, 480);
    return () => window.clearTimeout(doneTimer);
  }, [analysisProgress, normalizedUrl, pageMode, resolvedWorkflow, setLocation]);

  const valueLine = "Find companies that are ready for automation before your competitors do. We show you who they are, why they're ready, and how to start the conversation.";

  return (
    <main className="min-h-screen bg-[#081126] text-[#edf4f3]">
      <div className="mx-auto max-w-[1120px] px-5 pb-16 pt-8 lg:px-8 lg:pb-24">
        <header className="mb-10 flex items-center justify-between">
          <Link href="/" className="shrink-0">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login" className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10">
              <LogIn className="h-3.5 w-3.5" />
              Sign in
            </Link>
          </div>
        </header>

        <section className={`flex items-center justify-center ${pageMode === "url" ? "min-h-[72vh]" : "min-h-[60vh]"}`}>
          <div className="w-full max-w-2xl text-center">
            <h1 className={`${pageMode === "url" ? "text-[clamp(2.7rem,7.6vw,6rem)]" : "text-[clamp(2.2rem,6.5vw,4.4rem)]"} font-semibold leading-[0.92] tracking-[-0.038em] text-slate-50`} style={{ textShadow: "0 8px 28px rgba(5, 10, 20, 0.45)" }}>
              Sell More Robots.
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-[15px] leading-8 text-slate-300">{valueLine}</p>
            {pageMode === "url" && (
              <div className="mx-auto mt-5 max-w-xl rounded-xl border border-white/15 bg-[#0b162f] px-4 py-3 text-left text-xs leading-relaxed text-slate-300">
                <p>
                  <span className="font-semibold text-[#00d0a2]">Robot companies make money.</span>
                </p>
                <p className="mt-1">
                  <span className="font-semibold text-slate-100">Businesses save money.</span>
                </p>
              </div>
            )}
            <div className="mt-7 inline-flex min-h-[24px] items-center gap-2 text-sm font-medium text-[#71e7cb]">
              <span className="h-2 w-2 rounded-full bg-[#00d0a2]" />
              <span className="transition-opacity duration-300">{rotatingLeads[leadIndex]}</span>
            </div>

            {pageMode === "url" && (
              <div className="mx-auto mt-8 max-w-xl text-center">
                <p className="mt-2 text-sm text-slate-300">Enter your website.</p>
                <div className="mx-auto mt-4 flex max-w-lg items-center gap-2 border-b border-[#37587b] pb-3 text-left">
                  <Search className="h-4 w-4 shrink-0 text-[#7ea0c5]" />
                  <input value={urlInput} onChange={(e) => setUrlInput(e.target.value)} placeholder="Enter your company URL" className="w-full bg-transparent text-base text-white outline-none placeholder:text-[#6f89a8]" />
                </div>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  <button type="button" onClick={goToIdentity} disabled={!normalizedUrl} className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f] disabled:opacity-50">
                    Find Customers
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {pageMode === "identity" && (
              <StepFrame title="Finding customers for your team..." copy="Give us a moment to map your best buyers and next outreach angle.">
                <div className="mx-auto mt-6 max-w-xl rounded-xl border border-emerald-500/35 bg-[#0b162f] p-5 text-left">
                  <div className="mb-3 flex items-center gap-2 text-emerald-300">
                    <Sparkles className="h-4 w-4" />
                    <span className="text-xs font-semibold uppercase tracking-[0.2em]">Live Analysis</span>
                  </div>
                  <div className="space-y-2">
                    {analysisChecklist.map((item, index) => {
                      const done = index < analysisProgress;
                      return (
                        <div key={item} className={`flex items-center gap-2 text-sm ${done ? "text-emerald-200" : "text-slate-400"}`}>
                          <CheckCircle2 className={`h-4 w-4 ${done ? "text-emerald-300" : "text-slate-500"}`} />
                          <span>{item}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </StepFrame>
            )}

            {pageMode === "preview" && (
              <StepFrame title="Your next customer" copy="Why this customer, who to call, and how to start the conversation.">
                {(() => {
                  const topLead = previewLeads[0];
                  const confidence = Math.min(99, topLead.score + 2);
                  return (
                    <div className="mx-auto max-w-2xl rounded-2xl border border-emerald-400/45 bg-[#0b162f] p-5 text-left shadow-[0_20px_45px_-25px_rgba(0,200,150,0.8)]">
                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-900/50 pb-3">
                        <p className="text-2xl font-semibold text-emerald-200">{topLead.company}</p>
                        <div className="rounded-lg border border-emerald-400/50 bg-emerald-900/30 px-3 py-1">
                          <p className="text-[10px] uppercase tracking-wider text-emerald-200/80">Ready To Buy</p>
                          <p className="text-lg font-semibold text-emerald-200">{topLead.score}%</p>
                        </div>
                      </div>
                      <p className="mt-3 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Why this match</p>
                      <ul className="mt-2 space-y-1.5 text-sm text-slate-200">
                        <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />{topLead.signal}</li>
                        <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />New automation hiring indicators detected</li>
                        <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />Robot fit: {topLead.fit}</li>
                        <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />Similar deployment signals confirmed</li>
                      </ul>
                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2">
                          <p className="text-[10px] uppercase tracking-wider text-slate-400">Likely Contact</p>
                          <p className="text-sm font-semibold text-slate-100">Director of Operations</p>
                        </div>
                        <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2">
                          <p className="text-[10px] uppercase tracking-wider text-slate-400">Confidence</p>
                          <p className="text-sm font-semibold text-slate-100">{confidence}%</p>
                        </div>
                      </div>
                    </div>
                  );
                })()}
                <p className="mt-5 text-lg font-semibold text-emerald-200">We found {unlockMoreCount.toLocaleString()} more. Unlock them.</p>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPreviewLeadOffset((prev) => (prev + 1) % previewLeadPool.length)}
                    className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3.5 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-emerald-400 hover:text-emerald-200"
                  >
                    Show another match
                  </button>
                  <Link href={activateHref} onClick={persistWorkflowContext} className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f] transition hover:bg-[#00d9a3]">
                    Unlock {unlockMoreCount.toLocaleString()} More Buyers
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </StepFrame>
            )}

            <div className="mt-10 text-xs text-[#7fa2c8]">
              Already active? <Link href="/login" className="font-semibold text-[#9fcaef] hover:text-white">Sign in</Link>
            </div>
          </div>
        </section>

        {pageMode === "url" && (
          <>
            <section className="mt-14 border-t border-slate-800/80 pt-12">
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-[#00d0a2]">How It Works In 4 Steps</p>
              <h2 className="mt-4 max-w-3xl text-[clamp(1.8rem,3.8vw,3rem)] font-semibold leading-[1.08] tracking-[-0.02em] text-slate-50">
                Show me customers. Explain why. Tell me who to call. Help me start outreach.
              </h2>
              <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                {howItWorks.map((item) => (
                  <article key={item.id} className="rounded-xl border border-slate-700/70 bg-[#0b162f]/70 p-5">
                    <p className="text-[11px] font-semibold tracking-[0.28em] text-[#00d0a2]">{item.id}</p>
                    <h3 className="mt-3 text-xl font-semibold text-[#00d0a2]">{item.title}</h3>
                    <p className="mt-2 text-sm leading-7 text-slate-300">{item.body}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="mt-14 border-t border-slate-800/80 py-16 text-center">
              <h2 className="mx-auto max-w-3xl text-[clamp(2.1rem,4.8vw,4.2rem)] font-semibold leading-[0.98] tracking-[-0.03em] text-slate-50">Ready to sell more robots?</h2>
              <button type="button" onClick={() => setLocation("/journey/identity")} className="mt-10 inline-flex items-center gap-2 rounded-md bg-[#00c896] px-8 py-3 text-base font-semibold text-[#06261f]">
                Find Customers
                <ArrowRight className="h-5 w-5" />
              </button>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
