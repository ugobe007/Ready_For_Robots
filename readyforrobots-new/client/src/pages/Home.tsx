import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowRight, CheckCircle2, LogIn, Search, Sparkles } from "lucide-react";
import { Link, useLocation } from "wouter";
import { fetchHomepageLeadPool } from "@/lib/homepageLeads";
import { getPublicReadApiBase } from "@/lib/apiBase";
import { useAuth } from "@/contexts/AuthContext";
import HomeMarketPulse from "@/components/HomeMarketPulse";
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";

type HomepageLeadRow = {
  id: number;
  company_name?: string;
  priority_tier?: string;
  core_need?: string | null;
  share_summary?: string | null;
  pipeline_action?: string | null;
  robot_types_needed?: string[];
  signals?: { display_text?: string }[];
};

const liveBuyerSignals = [
  {
    company: "LINEAGE LOGISTICS",
    heat: "HOT",
    summary: "New distribution capacity + warehouse hiring pressure",
    robotFit: "AMR / Material Handling",
    whyNow: "Facility expansion",
    buyers: "4 identified",
  },
  {
    company: "HYATT HOTELS",
    heat: "HOT",
    summary: "Housekeeping labor shortages across multiple properties",
    robotFit: "Cleaning / Service Robotics",
    whyNow: "Labor pressure",
    buyers: "6 identified",
  },
  {
    company: "MANUFACTURER",
    heat: "WARM",
    summary: "New $180M production facility announced",
    robotFit: "Material Handling / Inspection",
    whyNow: "New facility",
    buyers: "3 identified",
  },
];

const liveLeadFallback: HomepageLeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    priority_tier: "HOT",
    core_need: "New distribution capacity + warehouse hiring pressure",
    pipeline_action: "Facility expansion",
    robot_types_needed: ["AMR", "Material Handling"],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels",
    priority_tier: "HOT",
    core_need: "Housekeeping labor shortages across multiple properties",
    pipeline_action: "Labor pressure",
    robot_types_needed: ["Cleaning", "Service Robotics"],
  },
  {
    id: -3,
    company_name: "Manufacturer",
    priority_tier: "WARM",
    core_need: "New $180M production facility announced",
    pipeline_action: "New facility",
    robot_types_needed: ["Material Handling", "Inspection"],
  },
];

const previewLeadPool = [
  {
    company: "Walmart Distribution",
    signal: "Facility expansion",
    fit: "Warehouse robotics",
    score: 97,
    likelyContact: "VP of Distribution Operations",
    specialReason: "Large-scale fulfillment expansion usually creates immediate AMR and picking demand across multiple sites.",
  },
  {
    company: "FedEx Ground",
    signal: "Labor shortage",
    fit: "Sortation robotics",
    score: 95,
    likelyContact: "Director of Hub Operations",
    specialReason: "Sustained labor pressure in high-volume hubs pushes faster buy-cycles for dock and sortation automation.",
  },
  {
    company: "Target Supply Chain",
    signal: "CapEx announcement",
    fit: "Palletizing",
    score: 93,
    likelyContact: "Senior Manager, Automation Programs",
    specialReason: "Fresh CapEx signals budgeted automation projects, which usually shortens vendor evaluation timelines.",
  },
  {
    company: "UPS Healthcare",
    signal: "Executive change",
    fit: "Autonomous transport",
    score: 90,
    likelyContact: "Operations Excellence Lead",
    specialReason: "Leadership transitions often reset operations priorities and open new automation initiatives.",
  },
  {
    company: "Maersk Terminals",
    signal: "RFP activity",
    fit: "Yard automation",
    score: 88,
    likelyContact: "Terminal Operations Director",
    specialReason: "Live RFP activity means the buying window is active now, not theoretical.",
  },
  {
    company: "Kroger Fulfillment",
    signal: "Procurement filing",
    fit: "Case handling robotics",
    score: 92,
    likelyContact: "Director of Fulfillment Engineering",
    specialReason: "Procurement filings are direct evidence that purchasing teams are actively sourcing solutions.",
  },
  {
    company: "Boeing Charleston",
    signal: "Inspection mandate",
    fit: "Vision inspection",
    score: 89,
    likelyContact: "Manufacturing Quality Director",
    specialReason: "Compliance-driven inspection projects usually carry high urgency and executive visibility.",
  },
  {
    company: "Mayo Clinic Logistics",
    signal: "Throughput bottleneck",
    fit: "Autonomous carts",
    score: 87,
    likelyContact: "Logistics Program Manager",
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

const PIPELINE_SUBMIT_CONTEXT_KEY = "rfr_pipeline_submit_context";

function signalSummary(lead: HomepageLeadRow): string {
  const summary = (lead.share_summary || "").trim();
  if (summary) return summary.slice(0, 108);
  const need = (lead.core_need || "").trim();
  if (need) return need.slice(0, 108);
  const signalText = (lead.signals?.[0]?.display_text || "").trim();
  if (signalText) return signalText.slice(0, 108);
  return "Active automation buying signals detected";
}

function whyNowText(lead: HomepageLeadRow): string {
  const action = (lead.pipeline_action || "").trim();
  if (!action) return "Buying window active";
  const noPrefix = action.replace(/^priority:\s*/i, "").trim();
  return noPrefix.slice(0, 52);
}

function robotFitText(lead: HomepageLeadRow): string {
  if (Array.isArray(lead.robot_types_needed) && lead.robot_types_needed.length > 0) {
    return lead.robot_types_needed.slice(0, 2).join(" / ");
  }
  return "Automation Systems";
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
      <h2 className="mt-3 text-xl font-semibold tracking-[-0.03em] text-slate-50 sm:text-2xl">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-300">{copy}</p>
      <div className="mt-6">{children}</div>
    </div>
  );
}

export default function Home() {
  const { session } = useAuth();
  const [location, setLocation] = useLocation();
  const [urlInput, setUrlInput] = useState("");
  const [previewLeadOffset, setPreviewLeadOffset] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [unlockMoreCount, setUnlockMoreCount] = useState(417);
  const [livePool, setLivePool] = useState<HomepageLeadRow[]>(liveLeadFallback);
  const [livePoolCursor, setLivePoolCursor] = useState(0);
  const [isLiveFeed, setIsLiveFeed] = useState(false);

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
    setPreviewLeadOffset(Math.floor(Math.random() * previewLeadPool.length));
  }, []);

  useEffect(() => {
    let active = true;
    void fetch(`${getPublicReadApiBase()}/api/leads/summary?exclude_junk=true`)
      .then((res) => (res.ok ? res.json() : null))
      .then((summary) => {
        if (!active || !summary) return;
        const total = Number(summary.total ?? summary.companies_in_database ?? 0);
        if (!Number.isFinite(total) || total <= 0) return;
        setUnlockMoreCount(Math.max(1, total - 3));
      })
      .catch(() => {
        // Keep fallback count when live summary is unavailable.
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadLiveLeads = async () => {
      try {
        const { leads, live } = await fetchHomepageLeadPool<HomepageLeadRow>(liveLeadFallback);
        if (cancelled) return;
        setIsLiveFeed(Boolean(live));
        if (Array.isArray(leads) && leads.length > 0) {
          setLivePool(leads);
        }
      } catch {
        if (!cancelled) setIsLiveFeed(false);
        // Keep fallback lead stream if live fetch is unavailable.
      }
    };

    void loadLiveLeads();
    const refreshTimer = window.setInterval(() => {
      void loadLiveLeads();
    }, 90_000);

    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, []);

  useEffect(() => {
    if (livePool.length <= 1) return;
    const rotateTimer = window.setInterval(() => {
      setLivePoolCursor((prev) => (prev + 1) % livePool.length);
    }, 5600);
    return () => window.clearInterval(rotateTimer);
  }, [livePool]);

  const rotatingSignalRows = useMemo(() => {
    if (!livePool.length) return liveBuyerSignals;
    return Array.from({ length: Math.min(3, livePool.length) }, (_, index) => {
      const lead = livePool[(livePoolCursor + index) % livePool.length];
      const heat = (lead.priority_tier || "WARM").toUpperCase();
      return {
        company: (lead.company_name || "Manufacturer").toUpperCase(),
        heat: heat === "HOT" ? "HOT" : "WARM",
        summary: signalSummary(lead),
        robotFit: robotFitText(lead),
        whyNow: whyNowText(lead),
        buyers: heat === "HOT" ? "4 identified" : "3 identified",
      };
    });
  }, [livePool, livePoolCursor]);

  const activateHref = useMemo(() => {
    if (!normalizedUrl) return "/signup";
    const nextParams = new URLSearchParams();
    nextParams.set("next", `/results?url=${encodeURIComponent(normalizedUrl)}&limit=5&src=home_signup_return`);
    const resolvedWf = resolvedWorkflow === "looking_for_robots" ? "buyer" : "robot_company";
    nextParams.set("wf", resolvedWf);
    nextParams.set("company_url", normalizedUrl);
    nextParams.set("preview_limit", "5");
    nextParams.set("src", "home_workflow");
    return `/signup?${nextParams.toString()}`;
  }, [normalizedUrl, resolvedWorkflow]);

  /** Submit URL only — never route "Start free workspace" through this. */
  const submitRobotUrl = () => {
    if (!normalizedUrl) return;
    persistWorkflowContext();
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(
        PIPELINE_SUBMIT_CONTEXT_KEY,
        JSON.stringify({
          url: normalizedUrl,
          src: "home_url_submit",
          ts: Date.now(),
        }),
      );
    }
    // Flow: URL → signup (if needed) → 5 sales leads → customer info → 15 leads.
    if (!session?.access_token) {
      const next = `/results?url=${encodeURIComponent(normalizedUrl)}&limit=5&src=home_signup_return`;
      window.location.assign(
        `/signup?next=${encodeURIComponent(next)}&src=home_url_submit&company_url=${encodeURIComponent(normalizedUrl)}`,
      );
      return;
    }
    window.location.assign(
      `/results?url=${encodeURIComponent(normalizedUrl)}&limit=5&src=home_url_submit`,
    );
  };

  const focusHeroInput = () => {
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    const el = typeof document !== "undefined" ? document.getElementById("hero-company-url") : null;
    if (el instanceof HTMLInputElement) {
      window.setTimeout(() => el.focus(), 220);
    }
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

  return (
    <main className="min-h-screen bg-[#081126] text-[#edf4f3]">
      <div className="mx-auto max-w-[1180px] px-5 pb-14 pt-6 sm:pt-10 lg:px-10 lg:pb-28 lg:pt-12">
        <header className="mb-6 flex items-center justify-between sm:mb-12">
          <Link href="/" className="shrink-0">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            {session?.access_token ? (
              <Link
                href="/pipeline"
                className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/40 px-3.5 py-2 text-xs font-semibold text-emerald-200 hover:bg-emerald-400/10"
              >
                Open workspace
              </Link>
            ) : (
              <Link
                href="/signup?src=home_header&next=/pipeline"
                className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/40 px-3.5 py-2 text-xs font-semibold text-emerald-200 hover:bg-emerald-400/10"
              >
                Start free workspace
              </Link>
            )}
            {session?.access_token ? (
              <Link
                href="/profile"
                className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10"
              >
                Account
              </Link>
            ) : (
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10"
              >
                <LogIn className="h-3.5 w-3.5" />
                Sign in
              </Link>
            )}
          </div>
        </header>

        <section className={`flex items-center justify-start ${pageMode === "url" ? "min-h-[60vh] sm:min-h-[72vh] lg:min-h-[78vh]" : "min-h-[60vh]"}`}>
          <div className="w-full max-w-3xl text-left">
            {pageMode === "url" && (
              <div className="w-full max-w-3xl text-left">
                <p className="text-[10px] font-semibold uppercase tracking-[0.36em] text-[#7adfc8] sm:text-[11px]">
                  READYFORROBOTS SIGNAL
                </p>
                <div className="mt-2.5 sm:mt-3">
                  <HomeMarketPulse />
                </div>
                <h1 className="mt-4 text-[clamp(2.1rem,8.4vw,6.3rem)] font-semibold leading-[0.9] tracking-[-0.045em] text-slate-50 sm:mt-5" style={{ textShadow: "0 10px 34px rgba(5, 10, 20, 0.48)" }}>
                  Find Jobs for <span className="text-[#00d0a2]">Robots.</span>
                </h1>
                <div className="mt-5 flex w-full items-start justify-start gap-4 sm:mt-7 sm:gap-7 lg:gap-8">
                  <p className="min-w-0 max-w-[54ch] flex-1 text-left text-[16px] leading-7 text-slate-300 sm:text-[18px] sm:leading-8 lg:text-[19px] lg:leading-9">
                    Live buyer intent matched to what your robot can do — who needs it, why now, and what to pitch — so you sell into demand, not cold lists.
                  </p>
                  <div className="shrink-0 pt-0.5" aria-hidden="true">
                    <PixelIcon map={KARE_FACE} scale={5} fill="#3ecf8e" background="transparent" />
                  </div>
                </div>
                <div className="mt-7 w-full max-w-[780px] border-b border-emerald-400/45 pb-3 sm:mt-10 lg:mt-11">
                  <label htmlFor="hero-company-url" className="mb-2 block text-left text-xs font-semibold uppercase tracking-[0.18em] text-[#8ec8b9]">
                    Enter your robot URL
                  </label>
                  <div className="flex min-w-0 items-center gap-2">
                    <Search className="h-4 w-4 shrink-0 text-[#7fd7ea]" />
                    <input
                      id="hero-company-url"
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && normalizedUrl) {
                          e.preventDefault();
                          submitRobotUrl();
                        }
                      }}
                      placeholder="yourrobotcompany.com/robot"
                      className="w-full min-w-0 bg-transparent text-base text-white outline-none placeholder:text-[#9fb4ca]"
                    />
                    <button
                      type="button"
                      onClick={submitRobotUrl}
                      disabled={!normalizedUrl}
                      className="inline-flex shrink-0 items-center justify-center gap-2 text-[15px] font-semibold text-[#00d0a2] transition hover:text-[#4cf0c8] disabled:cursor-not-allowed disabled:opacity-50 sm:text-base"
                    >
                      Find Jobs
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-300 sm:mt-4 sm:text-[15px]">
                  Find demand. Match your robot. Sell into the buying window.
                </p>
                <p className="mt-2 text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                  1. Submit URL · 2. {session?.access_token ? "5 sales leads" : "Sign up → 5 sales leads"} · 3. Customer info · 4. 15 sales leads
                </p>

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
              <StepFrame
                title={`Your next ${Math.min(3, previewLeads.length)} customers`}
                copy="Why these customers, who to call, and how to start the conversation."
              >
                <div className="mx-auto grid max-w-5xl gap-4 lg:grid-cols-3">
                  {previewLeads.slice(0, 3).map((lead) => {
                    const confidence = Math.min(99, lead.score + 2);
                    return (
                      <article key={`${lead.company}-${lead.signal}`} className="rounded-2xl border border-emerald-400/45 bg-[#0b162f] p-5 text-left shadow-[0_20px_45px_-25px_rgba(0,200,150,0.8)]">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-900/50 pb-3">
                          <p className="text-xl font-semibold text-emerald-200">{lead.company}</p>
                          <div className="rounded-lg border border-emerald-400/50 bg-emerald-900/30 px-3 py-1">
                            <p className="text-[10px] uppercase tracking-wider text-emerald-200/80">Ready To Buy</p>
                            <p className="text-lg font-semibold text-emerald-200">{lead.score}%</p>
                          </div>
                        </div>
                        <p className="mt-3 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Why this match</p>
                        <ul className="mt-2 space-y-1.5 text-sm text-slate-200">
                          <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />{lead.signal}</li>
                          <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />New automation hiring indicators detected</li>
                          <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />Robot fit: {lead.fit}</li>
                          <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-300" />{lead.specialReason}</li>
                        </ul>
                        <div className="mt-4 grid gap-3 sm:grid-cols-2">
                          <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2">
                            <p className="text-[10px] uppercase tracking-wider text-slate-400">Likely Contact</p>
                            <p className="text-sm font-semibold text-slate-100">{lead.likelyContact}</p>
                          </div>
                          <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2">
                            <p className="text-[10px] uppercase tracking-wider text-slate-400">Confidence</p>
                            <p className="text-sm font-semibold text-slate-100">{confidence}%</p>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
                <p className="mt-5 text-lg font-semibold text-emerald-200">We found {unlockMoreCount.toLocaleString()} more buyers in the pipeline. Unlock them.</p>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPreviewLeadOffset((prev) => (prev + 1) % previewLeadPool.length)}
                    className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3.5 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-emerald-400 hover:text-emerald-200"
                  >
                    Show another set
                  </button>
                  <Link href={activateHref} onClick={persistWorkflowContext} className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f] transition hover:bg-[#00d9a3]">
                    Unlock {unlockMoreCount.toLocaleString()} More Buyers
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </StepFrame>
            )}

            <div className="mt-8 text-xs text-[#7fa2c8] sm:mt-12">
              Already active? <Link href="/login" className="font-semibold text-[#9fcaef] hover:text-white">Sign in</Link>
            </div>
          </div>
        </section>

        {pageMode === "url" && (
          <>
            <section className="mt-10 border-t border-slate-800/70 pt-12 sm:pt-14">
              <h2 className="max-w-5xl text-[clamp(1.35rem,2.8vw,2rem)] font-semibold leading-[1.15] tracking-[-0.03em] text-slate-50">
                Companies Looking for Robots Right Now.
              </h2>
              <p className="mt-3 text-[15px] text-slate-300 sm:text-[16px]">ReadyForRobots detects the signals. You get the opportunity.</p>

              <div className="mt-8 border-y border-emerald-400/35 bg-[#061124] sm:mt-9">
                <div className="flex items-center justify-between border-b border-emerald-900/45 py-1.5 font-mono text-[10px] uppercase tracking-[0.2em] text-[#87dbca]">
                  <span>Live Buyer Signals</span>
                  <span className="inline-flex items-center gap-2 text-[#8ce6d2]">
                    <span className={`h-2 w-2 rounded-full ${isLiveFeed ? "bg-[#22d3a7] animate-pulse" : "bg-amber-300"}`} />
                    {isLiveFeed ? "Live" : "Preview"}
                  </span>
                </div>

                <div className="font-mono">
                  {rotatingSignalRows.map((row, index) => (
                    <article key={row.company} className="border-b border-[#16304b] py-2 last:border-b-0">
                      <div className="flex items-baseline justify-between gap-4">
                        <h3 className="text-[14px] font-semibold tracking-[0.06em] text-emerald-300 sm:text-[15px]">{row.company}</h3>
                        <p className={`text-[11px] font-semibold tracking-[0.14em] ${row.heat === "HOT" ? "text-[#f59e0b]" : "text-[#7dd3fc]"}`}>
                          {row.heat === "HOT" ? "HOT" : "WARM"}
                        </p>
                      </div>
                      <p className="mt-1 truncate text-[12px] leading-5 text-slate-300">{row.summary}</p>
                      <p className="mt-0.5 text-[12px] leading-5 text-[#a7c7de]">
                        Robot Fit: {row.robotFit} · Why Now: {row.whyNow} · Decision Makers: {row.buyers}
                      </p>
                      {index < rotatingSignalRows.length - 1 ? (
                        <div className="mt-2 h-px w-full bg-gradient-to-r from-transparent via-[#2a455d] to-transparent" aria-hidden />
                      ) : null}
                    </article>
                  ))}
                </div>
              </div>

              <div className="mt-8">
                <Link href="/signals" className="inline-flex items-center gap-2 text-base font-semibold text-[#85e8ce] transition hover:text-[#b5f7e4]">
                  See why they&apos;re buying
                  <ArrowRight className="h-4 w-4" />
                </Link>
                {!isLiveFeed ? <p className="mt-2 text-xs text-amber-200/90">Live API unavailable right now. Showing fallback examples until the feed reconnects.</p> : null}
              </div>
            </section>

            <section className="mt-16 border-t border-slate-800/70 pt-14 sm:mt-20 sm:pt-16">
              <h2 className="max-w-5xl text-[clamp(1.3rem,2.6vw,1.85rem)] font-semibold leading-[1.2] tracking-[-0.03em] text-slate-50">
                Stop Selling Robots to Companies That Aren&apos;t Buying.
              </h2>
              <p className="mt-4 max-w-4xl text-[15px] leading-7 text-slate-300 sm:text-[16px]">
                Most robot sales teams start with a list of companies and try to figure out who might need automation.
              </p>
              <p className="mt-3 text-base font-semibold text-[#9af2dc] sm:text-lg">ReadyForRobots starts with the need.</p>

              <div className="mt-10 space-y-5">
                <div className="rounded-xl border border-red-300/25 bg-[#130f14] px-5 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-red-200/90">Traditional prospecting</p>
                  <p className="mt-2 font-mono text-sm leading-8 text-red-100/85">Company -&gt; Research -&gt; Cold Call -&gt; Follow Up -&gt; Wait -&gt; Maybe</p>
                </div>
                <div className="rounded-xl border border-emerald-300/30 bg-[#071a19] px-5 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-100">ReadyForRobots</p>
                  <p className="mt-2 font-mono text-sm leading-8 text-emerald-100">Need Detected -&gt; Robot Matched -&gt; Buyer Identified -&gt; Sell</p>
                </div>
              </div>

              <h3 className="mt-10 text-[clamp(1.25rem,2.4vw,1.75rem)] font-semibold leading-tight tracking-[-0.02em] text-slate-50">
                Don&apos;t find leads. <span className="text-[#00d0a2]">Find demand.</span>
              </h3>
              <p className="mt-6 text-[12px] font-semibold uppercase tracking-[0.2em] text-[#8fe0cb] sm:text-[13px]">
                FIND DEMAND -&gt; SEE THE SIGNAL -&gt; UNDERSTAND WHY -&gt; CONTACT THE BUYER
              </p>

              <div className="mt-12 border-t border-slate-800/60 pt-8 text-center">
                <p className="text-sm text-slate-300">Start with one URL. See active demand before your team makes the first call.</p>
                <button
                  type="button"
                  onClick={focusHeroInput}
                  className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#00c896] px-7 py-3 text-base font-semibold text-[#05271e] transition hover:bg-[#00d9a3]"
                >
                  Find Jobs
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
