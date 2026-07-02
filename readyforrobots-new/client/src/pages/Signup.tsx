/**
 * Sign up — account creation entry point using Supabase auth (Precision Intelligence light theme).
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase, supabaseOAuthRedirect } from "@/lib/supabase";
import { getPublicReadApiBase } from "@/lib/apiBase";
import { readSupplyAttribution, trackSupplyConversion } from "@/lib/siteAnalytics";
import { clearSupabaseOAuthParams, readSupabaseOAuthError, finishSupabaseOAuthCallback } from "@/lib/authCallback";
import { resolvePostAuthPath, storePendingNext, postAuthRedirectTarget, readPlanParam, storeCheckoutIntent, navigateAfterAuth } from "@/lib/authNext";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");
  const [liveProof, setLiveProof] = useState<{ hot?: number; companies?: number } | null>(null);

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const hubspotIntent = params.get("intent") === "hubspot";
  const nextRaw = params.get("next") || "";
  const pipelineIntent = nextRaw.startsWith("/pipeline") || /[?&]lead=\d+/.test(nextRaw);
  const resultsIntent = nextRaw.startsWith("/results");
  // Specific buyer the anonymous user was acting on — carried through the signup wall
  // so we restate exactly what they unlock (value-first conversion continuity).
  const buyerCo = (params.get("co") || "").trim().slice(0, 80);

  const nextPath = () => resolvePostAuthPath("/pipeline");

  useEffect(() => {
    const plan = readPlanParam(search);
    if (plan) {
      storeCheckoutIntent(plan);
      return;
    }
    const next = params.get("next");
    if (next && next.startsWith("/")) storePendingNext(next);
  }, [params, search]);

  useEffect(() => {
    const attribution = readSupplyAttribution(search);
    if (!attribution.utmSource && !attribution.robotCompanyId) return;
    trackSupplyConversion({
      page: "signup",
      utm_source: attribution.utmSource,
      rc: attribution.robotCompanyId,
      msg: attribution.messageToken,
      referrer: typeof document !== "undefined" ? document.referrer || null : null,
    });
  }, [search]);

  const persistFullName = () => {
    if (typeof window === "undefined" || !fullName.trim()) return;
    window.localStorage.setItem(SIGNUP_NAME_KEY, fullName.trim());
  };

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    void (async () => {
      const oauthErr = readSupabaseOAuthError();
      if (oauthErr) {
        setStatus("error");
        setErrMsg(oauthErr);
        window.history.replaceState(null, "", clearSupabaseOAuthParams(window.location.pathname, window.location.search));
        return;
      }

      const { data } = await client.auth.getSession();
      if (data?.session) navigateAfterAuth(nextPath());
    })();

    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) {
        const attribution = readSupplyAttribution(search);
        if (attribution.utmSource || attribution.robotCompanyId) {
          trackSupplyConversion({
            page: "signup",
            completed: true,
            utm_source: attribution.utmSource,
            rc: attribution.robotCompanyId,
            msg: attribution.messageToken,
          });
        }
        navigateAfterAuth(nextPath());
      }
    });
    return () => sub.subscription.unsubscribe();
  }, [setLocation]);

  useEffect(() => {
    let cancelled = false;
    void fetch(`${getPublicReadApiBase()}/api/leads/summary?exclude_junk=true`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        const hot = Number(data.hot);
        const companies = Number(data.companies_in_database ?? data.total);
        if (hot > 0 || companies > 0) {
          setLiveProof({
            hot: Number.isFinite(hot) ? hot : undefined,
            companies: Number.isFinite(companies) ? companies : undefined,
          });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function oauth(provider: "google" | "github") {
    if (!supabase) {
      setStatus("error");
      setErrMsg("Configure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg("Enter your full name so SIGNAL can authenticate your HubSpot workspace.");
      return;
    }
    persistFullName();
    setErrMsg("");
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: supabaseOAuthRedirect(postAuthRedirectTarget("/pipeline")) },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
    }
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !supabase) return;
    if (hubspotIntent && !fullName.trim()) {
      setStatus("error");
      setErrMsg("Enter your full name so SIGNAL can authenticate your HubSpot workspace.");
      return;
    }
    persistFullName();
    setStatus("sending");
    setErrMsg("");
    const redirectTo = supabaseOAuthRedirect(postAuthRedirectTarget("/pipeline"));
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectTo },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
    } else {
      setStatus("sent");
    }
  }

  const loginHref = `/login${search}`;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 px-4 pt-24 pb-16">
        <div className="mx-auto grid w-full max-w-5xl items-start gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <p className="section-eyebrow mb-3">
              {hubspotIntent ? "HubSpot + SIGNAL workspace" : "Robot OEMs & integrators"}
            </p>
            <h1 className="max-w-xl font-display text-4xl font-bold leading-tight text-gray-900 md:text-5xl">
              {hubspotIntent
                ? "Sign up, then SIGNAL links HubSpot automatically."
                : pipelineIntent
                  ? buyerCo
                    ? `Save ${buyerCo}. Copy the draft. Run your pipeline.`
                    : "Save the lead. Copy the draft. Run your pipeline."
                  : resultsIntent
                    ? "Unlock your matched buyers in one workspace."
                    : "Automate your robot sales funnel."}
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-gray-600">
              {hubspotIntent
                ? "Use your work email and full name. After signup, SIGNAL provisions the HubSpot API connection and MCP bridge — no manual app setup."
                : pipelineIntent
                  ? buyerCo
                    ? `Free workspace: land back on ${buyerCo}, save it in one click, copy the outreach draft SIGNAL wrote for them, and sync to HubSpot when you are ready.`
                    : "Free workspace: land on your matched lead, save it in one click, copy the outreach draft, and sync to HubSpot when you are ready."
                  : resultsIntent
                    ? "Sign up to unlock every URL scan match, save leads to CRM, and copy signal-matched outreach drafts."
                    : "For robot OEMs and integrators — SIGNAL ranks buyer intent, drafts outreach, and advances deals in native CRM or HubSpot."}
            </p>
            {liveProof && (liveProof.hot || liveProof.companies) && (
              <p className="mt-3 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-900">
                Live now ·{" "}
                {liveProof.hot ? `${liveProof.hot.toLocaleString()} hot buyers` : "buyer signals scored"}
                {liveProof.companies ? ` · ${liveProof.companies.toLocaleString()} companies tracked` : ""}
              </p>
            )}
            {!hubspotIntent && !pipelineIntent && !resultsIntent && (
              <ul className="mt-4 space-y-2 text-xs text-gray-600">
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Native pipeline + kanban — or connect HubSpot in one click
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  HOT/WARM buyers with pitch actions and robot categories
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Free to start · no credit card
                </li>
              </ul>
            )}
            {(pipelineIntent || resultsIntent) && !hubspotIntent && (
              <ul className="mt-4 space-y-2 text-xs text-gray-600">
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  {buyerCo
                    ? `Pick up right where you left off on ${buyerCo} — draft waiting in pipeline`
                    : "Pick up on the same lead after signup — draft waiting in pipeline"}
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Copy signal-matched outreach drafts in one click
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  10 live pipeline leads · pitch actions · robot categories
                </li>
              </ul>
            )}
          </div>

          {status === "sent" ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-6 py-8 text-center">
              <h2 className="text-xl font-bold text-gray-900">Check your email</h2>
              <p className="mt-3 text-sm text-gray-600">
                We sent a magic link to <span className="font-semibold text-emerald-700">{email}</span>.
              </p>
              <button type="button" onClick={() => setStatus("idle")} className="mt-6 text-xs text-gray-500 hover:text-gray-800">
                Use a different email
              </button>
            </div>
          ) : (
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="font-display text-xl font-bold text-gray-900">
                {hubspotIntent ? "Sign up for HubSpot sync" : "Start free"}
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                {hubspotIntent
                  ? "Email + full name required. Next step: one-click HubSpot authorize."
                  : params.get("next")
                    ? "Continue in one tap with Google — or use a magic link below."
                    : "Create an account with Google, GitHub, or a magic link."}
              </p>
              {hubspotIntent && (
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full name"
                  className="mt-4 w-full rounded-xl border border-gray-200 px-3 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-emerald-500"
                />
              )}
              <div className={`${hubspotIntent ? "mt-4" : "mt-6"} flex flex-col gap-2`}>
                <button
                  type="button"
                  onClick={() => void oauth("google")}
                  disabled={!supabase}
                  className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 disabled:opacity-40"
                >
                  Continue with Google — fastest
                </button>
                <button
                  type="button"
                  onClick={() => void oauth("github")}
                  disabled={!supabase}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                >
                  Sign up with GitHub
                </button>
              </div>
              <div className="my-5 flex items-center gap-3">
                <span className="h-px flex-1 bg-gray-200" />
                <span className="text-[10px] uppercase tracking-widest text-gray-400">or</span>
                <span className="h-px flex-1 bg-gray-200" />
              </div>
              <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@robotcompany.com"
                  disabled={status === "sending"}
                  className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-emerald-500"
                />
                {status === "error" && (
                  <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">{errMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={status === "sending" || !email.trim()}
                  className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 disabled:opacity-40"
                >
                  {status === "sending" ? "Sending..." : hubspotIntent ? "Sign up & connect HubSpot" : "Send signup link"}
                </button>
              </form>
              <p className="mt-5 text-center text-xs text-gray-500">
                Already have an account?{" "}
                <Link href={loginHref} className="font-semibold text-emerald-600 hover:text-emerald-700">
                  Sign in
                </Link>
              </p>
            </div>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
