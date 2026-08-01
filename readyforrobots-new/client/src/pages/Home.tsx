import { useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, LogIn, Search } from "lucide-react";
import { Link, useLocation } from "wouter";

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

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const journeyUrl = params.get("company_url") || "";
  const normalizedUrl = useMemo(() => normalizeUrlInput(urlInput || journeyUrl), [journeyUrl, urlInput]);
  const pageMode: "url" | "identity" | "activate" =
    location === "/journey/identity" ? "identity" : location === "/journey/activate" ? "activate" : "url";

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

  const valueLine = "Convert your company URL into a live buyer pipeline with ranked opportunities and outreach guidance.";

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
            <h1 className="text-[clamp(2.2rem,5.4vw,4.4rem)] font-semibold leading-[0.95] tracking-[-0.04em] text-white">
              Automate Your Sales Pipeline.
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-[#a4b8ce]">{valueLine}</p>

            {pageMode === "url" && (
              <div className="mx-auto mt-9 max-w-xl">
                <div className="flex items-center gap-2 border-b border-[#2d4b70] pb-2">
                  <Search className="h-4 w-4 shrink-0 text-[#7ea0c5]" />
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="Enter your company URL"
                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-[#6f89a8]"
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
      </div>
    </main>
  );
}
