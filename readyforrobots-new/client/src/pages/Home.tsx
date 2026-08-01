import { useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, LogIn, Search } from "lucide-react";
import { Link } from "wouter";

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
  const [urlInput, setUrlInput] = useState("");
  const [urlConfirmed, setUrlConfirmed] = useState(false);
  const [identityConfirmed, setIdentityConfirmed] = useState(false);

  const normalizedUrl = useMemo(() => normalizeUrlInput(urlInput), [urlInput]);

  const activateHref = useMemo(() => {
    if (!urlConfirmed || !identityConfirmed || !normalizedUrl) return "/signup";
    const params = new URLSearchParams();
    params.set("next", "/pipeline");
    params.set("wf", "robot_company");
    params.set("company_url", normalizedUrl);
    params.set("src", "home_workflow");
    return `/signup?${params.toString()}`;
  }, [identityConfirmed, normalizedUrl, urlConfirmed]);

  const handleContinueUrl = () => {
    if (!normalizedUrl) return;
    setUrlConfirmed(true);
  };

  const persistWorkflowContext = () => {
    if (typeof window === "undefined" || !urlConfirmed || !identityConfirmed || !normalizedUrl) return;
    const payload = {
      wf: "robot_company",
      company_url: normalizedUrl,
      src: "home_workflow",
      ts: Date.now(),
    };
    window.sessionStorage.setItem("rfr_workflow_context", JSON.stringify(payload));
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

        <section className="max-w-3xl">
          <h1 className="text-[clamp(2.2rem,5.4vw,4.4rem)] font-semibold leading-[0.95] tracking-[-0.04em] text-white">
            Automate Your Sales Pipeline.
          </h1>
          <p className="mt-4 text-sm leading-7 text-[#a4b8ce]">
            Step [1] enter URL  Step [2] user identification and confirmation  Step [3] activate pipeline  Step [4] sign up to save
          </p>

          <div className="mt-9 space-y-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#58c4ea]">Step 1</p>
              <p className="mt-1 text-sm text-[#c8d8ea]">Enter your robot company URL.</p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <div className="flex min-w-[260px] flex-1 items-center gap-2 border-b border-[#2d4b70] pb-2">
                  <Search className="h-4 w-4 shrink-0 text-[#7ea0c5]" />
                  <input
                    value={urlInput}
                    onChange={(e) => {
                      setUrlInput(e.target.value);
                      setUrlConfirmed(false);
                    }}
                    placeholder="example.com"
                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-[#6f89a8]"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleContinueUrl}
                  disabled={!normalizedUrl}
                  className="inline-flex items-center rounded-md bg-[#00c896] px-3 py-1.5 text-xs font-semibold text-[#05211b] disabled:opacity-50"
                >
                  Confirm URL
                </button>
              </div>
              {urlConfirmed && <p className="mt-2 text-xs text-[#7fd8be]">Confirmed: {normalizedUrl}</p>}
            </div>

            <div className={urlConfirmed ? "opacity-100" : "pointer-events-none opacity-45"}>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#58c4ea]">Step 2</p>
              <p className="mt-1 text-sm text-[#c8d8ea]">User identification and confirmation.</p>
              <label className="mt-3 inline-flex items-center gap-2 text-sm text-white">
                <input
                  type="checkbox"
                  checked={identityConfirmed}
                  onChange={(e) => setIdentityConfirmed(e.target.checked)}
                  className="h-4 w-4 rounded border-[#426185] bg-transparent"
                />
                I confirm I represent a robot company.
              </label>
            </div>

            <div className={identityConfirmed && urlConfirmed ? "opacity-100" : "pointer-events-none opacity-45"}>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#58c4ea]">Step 3</p>
              <p className="mt-1 text-sm text-[#c8d8ea]">Activate pipeline.</p>
              <div className="mt-3">
                {identityConfirmed && urlConfirmed && normalizedUrl ? (
                  <Link
                    href={activateHref}
                    onClick={persistWorkflowContext}
                    className="inline-flex items-center gap-2 rounded-md bg-[#00c896] px-4 py-2 text-sm font-semibold text-[#06261f]"
                  >
                    Activate pipeline
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : (
                  <span className="inline-flex items-center gap-2 text-xs text-[#8ea7c4]">Complete Step 1 and Step 2 first.</span>
                )}
              </div>
            </div>

            <div className={identityConfirmed && urlConfirmed ? "opacity-100" : "pointer-events-none opacity-45"}>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#58c4ea]">Step 4</p>
              <p className="mt-1 text-sm text-[#c8d8ea]">Sign up to save.</p>
              <p className="mt-2 inline-flex items-center gap-2 text-xs text-[#7fd8be]">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Your setup is saved after signup.
              </p>
            </div>

            <div className="pt-1 text-xs text-[#7fa2c8]">
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
