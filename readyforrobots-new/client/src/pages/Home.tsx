import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, LogIn, Search } from "lucide-react";
import { Link, useLocation } from "wouter";

const rotatingLeads = [
  "Siemens Energy",
  "ABB Robotics",
  "Daifuku North America",
  "KUKA Systems",
  "Dematic",
  "Swisslog",
];

const coreValueCards = [
  {
    id: "01",
    title: "Know who is buying before your competitors do",
    body: "Live signals from 150+ sources surface buying intent the moment it appears.",
  },
  {
    id: "02",
    title: "Every lead ranked by readiness, with evidence",
    body: "Every opportunity arrives scored with signal type, strength, and source context.",
  },
  {
    id: "03",
    title: "Qualified leads flow directly into your pipeline",
    body: "Your team gets guidance and next actions without manual prospecting loops.",
  },
];

const howItWorks = [
  {
    id: "01",
    title: "Find",
    body: "We monitor procurement filings, hiring spikes, CapEx announcements, and facility permits to surface active buyers.",
  },
  {
    id: "02",
    title: "Score",
    body: "Each organization is scored by buying readiness with evidence, so your team acts on signal, not guesswork.",
  },
  {
    id: "03",
    title: "Track",
    body: "Every opportunity is tracked through its project lifecycle so you know exactly when to engage.",
  },
  {
    id: "04",
    title: "Automate",
    body: "Ranked opportunities and outreach guidance keep your pipeline moving without manual research.",
  },
];

const watchStats = [
  { title: "Labor shortage", count: "1,284", tone: "emerald" },
  { title: "Facility expansion", count: "642", tone: "emerald" },
  { title: "CapEx announcement", count: "517", tone: "amber" },
  { title: "Executive change", count: "208", tone: "slate" },
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

export default function Home() {
  const [location, setLocation] = useLocation();
  const [urlInput, setUrlInput] = useState("");
  const [identityConfirmed, setIdentityConfirmed] = useState(false);
  const [leadIndex, setLeadIndex] = useState(0);

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const journeyUrl = params.get("company_url") || "";
  const normalizedUrl = useMemo(() => normalizeUrlInput(urlInput || journeyUrl), [journeyUrl, urlInput]);
  const pageMode: "url" | "identity" | "activate" =
    location === "/journey/identity" ? "identity" : location === "/journey/activate" ? "activate" : "url";

  useEffect(() => {
    const timer = window.setInterval(() => {
      setLeadIndex((prev) => (prev + 1) % rotatingLeads.length);
    }, 1800);
    return () => window.clearInterval(timer);
  }, []);

  const activateHref = useMemo(() => {
    if (!normalizedUrl) return "/signup";
    const params = new URLSearchParams();
    params.set("next", "/pipeline");
    params.set("wf", "robot_company");
    params.set("company_url", normalizedUrl);
    params.set("src", "home_workflow");
    return `/signup?${params.toString()}`;
  }, [normalizedUrl]);

  const goToIdentity = () => {
    if (!normalizedUrl) return;
    setLocation(`/journey/identity?company_url=${encodeURIComponent(normalizedUrl)}`);
  };

  const goToActivate = () => {
    if (!normalizedUrl || !identityConfirmed) return;
    setLocation(`/journey/activate?company_url=${encodeURIComponent(normalizedUrl)}`);
  };

  const persistWorkflowContext = () => {
    if (typeof window === "undefined" || !normalizedUrl) return;
    const payload = {
      wf: "robot_company",
      company_url: normalizedUrl,
      src: "home_workflow",
      ts: Date.now(),
    };
    window.sessionStorage.setItem("rfr_workflow_context", JSON.stringify(payload));
  };

  const valueLine = "Convert your company URL into a live sales pipeline with ranked opportunities and outreach guidance.";

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

        <section className="flex min-h-[72vh] items-center justify-center">
          <div className="w-full max-w-2xl text-center">
            <h1
              className="text-[clamp(2.4rem,6vw,5rem)] font-semibold leading-[0.92] tracking-[-0.04em] text-slate-50"
              style={{ textShadow: "0 8px 28px rgba(5, 10, 20, 0.45)" }}
            >
              Automate Your Sales <span className="text-[#00d0a2]">PIPELINE</span>.
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-[15px] leading-8 text-slate-300">{valueLine}</p>
            <div className="mt-7 inline-flex min-h-[24px] items-center gap-2 text-sm font-medium text-[#71e7cb]">
              <span className="h-2 w-2 rounded-full bg-[#00d0a2]" />
              <span className="transition-opacity duration-300">{rotatingLeads[leadIndex]}</span>
            </div>

            {pageMode === "url" && (
              <div className="mx-auto mt-9 max-w-xl">
                <div className="flex items-center gap-2 border-b border-[#37587b] pb-3">
                  <Search className="h-4 w-4 shrink-0 text-[#7ea0c5]" />
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="Enter your company URL"
                    className="w-full bg-transparent text-base text-white outline-none placeholder:text-[#6f89a8]"
                  />
                </div>
                <button
                  type="button"
                  onClick={goToIdentity}
                  disabled={!normalizedUrl}
                  className="mt-6 inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f] disabled:opacity-50"
                >
                  Continue
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            )}

            {pageMode === "identity" && (
              <div className="mx-auto mt-9 max-w-xl">
                <p className="text-sm text-[#c8d8ea]">Confirm you represent a robot company for {normalizedUrl}.</p>
                <label className="mt-4 inline-flex items-center gap-2 text-sm text-white">
                  <input
                    type="checkbox"
                    checked={identityConfirmed}
                    onChange={(e) => setIdentityConfirmed(e.target.checked)}
                    className="h-4 w-4 rounded border-[#426185] bg-transparent"
                  />
                  I confirm this is a robot company account.
                </label>
                <div className="mt-6">
                  <button
                    type="button"
                    onClick={goToActivate}
                    disabled={!identityConfirmed || !normalizedUrl}
                    className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f] disabled:opacity-50"
                  >
                    Continue
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {pageMode === "activate" && (
              <div className="mx-auto mt-9 max-w-xl">
                <p className="text-sm text-[#c8d8ea]">Pipeline ready for {normalizedUrl}. Activate to continue.</p>
                <div className="mt-6">
                  <Link
                    href={activateHref}
                    onClick={persistWorkflowContext}
                    className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-5 py-2.5 text-sm font-semibold text-[#06261f]"
                  >
                    Activate pipeline
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
                <p className="mt-4 inline-flex items-center gap-2 text-xs text-[#7fd8be]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Sign up to save your pipeline.
                </p>
              </div>
            )}

            <div className="mt-10 text-xs text-[#7fa2c8]">
              Already active?{" "}
              <Link href="/login" className="font-semibold text-[#9fcaef] hover:text-white">
                Sign in
              </Link>
            </div>
          </div>
        </section>

        {pageMode === "url" && (
          <>
            <section className="border-t border-slate-800/80 pt-20">
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-[#58c4ea]">What is ReadyForRobots</p>
              <h2 className="mt-5 max-w-4xl text-[clamp(2rem,4.2vw,3.8rem)] font-semibold leading-[1.05] tracking-[-0.03em] text-slate-50">
                The sales pipeline that runs itself, built for robot companies and distributors.
              </h2>
              <p className="mt-6 max-w-4xl text-xl leading-9 text-slate-300">
                SIGNAL watches procurement filings, hiring spikes, CapEx announcements, and facility buildouts across live
                sources. When a company enters the robot buying cycle, we catch it, score it, and push it to your pipeline.
              </p>

              <div className="mt-12 grid gap-0 rounded-xl border border-slate-700/70 bg-slate-900/60 md:grid-cols-3">
                {coreValueCards.map((card) => (
                  <article key={card.id} className="border-b border-slate-800/80 p-8 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0">
                    <p className="text-[11px] font-semibold tracking-[0.28em] text-[#00d0a2]">{card.id}</p>
                    <h3 className="mt-6 text-3xl font-semibold leading-tight text-slate-100">{card.title}</h3>
                    <p className="mt-5 text-xl leading-8 text-slate-300">{card.body}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="border-t border-slate-800/80 pt-24">
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-[#58c4ea]">How it works</p>
              <div className="mt-10 grid gap-8 md:grid-cols-2 xl:grid-cols-4">
                {howItWorks.map((item) => (
                  <article key={item.id} className="border-t border-slate-700/70 pt-8">
                    <p className="text-[11px] font-semibold tracking-[0.28em] text-[#00d0a2]">{item.id}</p>
                    <h3 className="mt-4 text-4xl font-semibold text-slate-100">{item.title}</h3>
                    <p className="mt-4 text-xl leading-8 text-slate-300">{item.body}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="border-t border-slate-800/80 pt-24">
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-[#58c4ea]">What we watch</p>
              <h2 className="mt-4 text-[clamp(2rem,4vw,3.4rem)] font-semibold tracking-[-0.02em] text-slate-50">150+ live data sources. Always on.</h2>
              <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                {watchStats.map((stat) => (
                  <article key={stat.title} className="rounded-xl border border-slate-700/80 bg-slate-900/60 p-6">
                    <p className="text-3xl font-semibold text-slate-100">{stat.title}</p>
                    <div className="mt-8 flex items-end justify-between">
                      <p className="text-6xl font-semibold tracking-[-0.02em] text-slate-50">{stat.count}</p>
                      <p className="pb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Matches</p>
                    </div>
                    <div className="mt-8 h-[3px] w-full bg-slate-700">
                      <div
                        className={`h-full ${
                          stat.tone === "amber"
                            ? "bg-amber-400"
                            : stat.tone === "slate"
                              ? "bg-slate-400"
                              : "bg-[#00d0a2]"
                        }`}
                      />
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="mt-24 border-t border-slate-800/80 py-24 text-center">
              <h2 className="mx-auto max-w-3xl text-[clamp(2rem,4.5vw,4rem)] font-semibold leading-tight tracking-[-0.03em] text-slate-50">
                Ready to automate your pipeline?
              </h2>
              <button
                type="button"
                onClick={() => setLocation("/")}
                className="mt-10 inline-flex items-center gap-2 rounded-md bg-[#00c896] px-8 py-3 text-base font-semibold text-[#06261f]"
              >
                Continue
                <ArrowRight className="h-5 w-5" />
              </button>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
