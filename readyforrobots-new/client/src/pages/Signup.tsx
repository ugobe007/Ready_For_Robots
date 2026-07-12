/**
 * Sign up — account creation entry point using Supabase auth (Precision Intelligence light theme).
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase, supabaseOAuthRedirect } from "@/lib/supabase";
import { getPublicReadApiBase } from "@/lib/apiBase";
import { readSupplyAttribution, trackSupplyConversion, trackSignupStart } from "@/lib/siteAnalytics";
import { clearSupabaseOAuthParams, readSupabaseOAuthError, finishSupabaseOAuthCallback } from "@/lib/authCallback";
import { resolvePostAuthPath, storePendingNext, postAuthRedirectTarget, readPlanParam, storeCheckoutIntent, navigateAfterAuth } from "@/lib/authNext";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";

/**
 * Map an email address to its webmail inbox so a user on the "check your email"
 * screen can open their inbox in one tap instead of hunting for it (a common
 * magic-link completion leak). Returns null for domains we don't recognize.
 */
function emailProviderInbox(email: string): { label: string; url: string } | null {
  const domain = email.split("@")[1]?.toLowerCase().trim();
  if (!domain) return null;
  const map: Record<string, { label: string; url: string }> = {
    "gmail.com": { label: "Open Gmail", url: "https://mail.google.com/mail/u/0/" },
    "googlemail.com": { label: "Open Gmail", url: "https://mail.google.com/mail/u/0/" },
    "outlook.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "hotmail.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "live.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "msn.com": { label: "Open Outlook", url: "https://outlook.live.com/mail/0/" },
    "yahoo.com": { label: "Open Yahoo Mail", url: "https://mail.yahoo.com/" },
    "icloud.com": { label: "Open iCloud Mail", url: "https://www.icloud.com/mail/" },
    "me.com": { label: "Open iCloud Mail", url: "https://www.icloud.com/mail/" },
    "proton.me": { label: "Open Proton Mail", url: "https://mail.proton.me/u/0/" },
    "protonmail.com": { label: "Open Proton Mail", url: "https://mail.proton.me/u/0/" },
  };
  return map[domain] ?? null;
}

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendNote, setResendNote] = useState("");
  const [liveProof, setLiveProof] = useState<{ hot?: number; companies?: number } | null>(null);
  // A real named HOT buyer from the live pipeline — turns abstract counts into a
  // concrete win the user can picture acting on (value-first proof at the decision point).
  const [liveBuyer, setLiveBuyer] = useState<
    { company: string; industry?: string; tier?: string; blurb?: string; robots: string[] } | null
  >(null);

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

  // Funnel #20: record signup intent (denominator). Fires once per page view.
  useEffect(() => {
    trackSignupStart({
      plan: params.get("plan") || null,
      next: params.get("next") || null,
      intent: params.get("intent") || null,
      referrer: typeof document !== "undefined" ? document.referrer || null : null,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  // Pull one real named HOT buyer from the live pipeline for cold/generic signups.
  // Skipped when the user already carried a specific buyer (buyerCo) or HubSpot intent,
  // so we never show a competing company than the one they came to act on.
  useEffect(() => {
    if (hubspotIntent || buyerCo) return;
    let cancelled = false;
    void fetch(`${getPublicReadApiBase()}/api/leads/pipeline`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        const leads = Array.isArray(data.leads) ? data.leads : [];
        const pick = leads.find(
          (l: any) =>
            String(l?.company_name || "").trim() &&
            String(l?.share_blurb || l?.share_summary || "").trim(),
        );
        if (!pick) return;
        const robots = Array.isArray(pick.robot_types_needed)
          ? pick.robot_types_needed.filter(Boolean)
          : [];
        setLiveBuyer({
          company: String(pick.company_name).trim().slice(0, 60),
          industry: pick.industry ? String(pick.industry) : undefined,
          tier: pick.priority_tier ? String(pick.priority_tier).toUpperCase() : undefined,
          blurb: String(pick.share_blurb || pick.share_summary || "").trim().slice(0, 160),
          robots: robots.slice(0, 2).map((r: any) => String(r)),
        });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [hubspotIntent, buyerCo]);

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

  // Tick down the resend cooldown so users aren't left guessing when they can retry.
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = window.setTimeout(() => setResendCooldown((n) => Math.max(0, n - 1)), 1000);
    return () => window.clearTimeout(t);
  }, [resendCooldown]);

  async function sendMagicLink(): Promise<boolean> {
    if (!email.trim() || !supabase) return false;
    const redirectTo = supabaseOAuthRedirect(postAuthRedirectTarget("/pipeline"));
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectTo },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
      return false;
    }
    return true;
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
    setResendNote("");
    const ok = await sendMagicLink();
    if (ok) {
      setStatus("sent");
      setResendCooldown(30);
    }
  }

  async function resendMagicLink() {
    if (resendCooldown > 0 || !email.trim()) return;
    setResendNote("Sending…");
    const ok = await sendMagicLink();
    if (ok) {
      setResendNote("Sent again — check your inbox and spam folder.");
      setResendCooldown(30);
    } else {
      setResendNote("");
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
                  Live pipeline leads · pitch actions · robot categories
                </li>
              </ul>
            )}
            {liveBuyer && (
              <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-emerald-700">
                  <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </span>
                  Live {liveBuyer.tier || "HOT"} buyer in the pipeline right now
                </div>
                <p className="mt-2 font-display text-base font-bold text-gray-900">
                  {liveBuyer.company}
                  {liveBuyer.industry ? (
                    <span className="ml-2 text-xs font-medium text-gray-500">{liveBuyer.industry}</span>
                  ) : null}
                </p>
                {liveBuyer.blurb && (
                  <p className="mt-1 text-xs leading-relaxed text-gray-600">{liveBuyer.blurb}</p>
                )}
                {liveBuyer.robots.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {liveBuyer.robots.map((r) => (
                      <span
                        key={r}
                        className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                )}
                <p className="mt-3 text-[11px] font-medium text-gray-500">
                  Sign up free to save this buyer and copy the outreach draft SIGNAL wrote for them.
                </p>
              </div>
            )}
          </div>

          {status === "sent" ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-6 py-8 text-center">
              <h2 className="text-xl font-bold text-gray-900">Check your email</h2>
              <p className="mt-3 text-sm text-gray-600">
                We sent a one-tap sign-in link to <span className="font-semibold text-emerald-700">{email}</span>.
                Open it and you'll land{" "}
                {pipelineIntent && buyerCo
                  ? `back on ${buyerCo}, ready to save and copy the draft.`
                  : "in your pipeline, ready to save your first lead and copy the outreach draft."}
              </p>
              {(() => {
                const inbox = emailProviderInbox(email);
                return inbox ? (
                  <a
                    href={inbox.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-6 inline-block w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700"
                  >
                    {inbox.label} →
                  </a>
                ) : null;
              })()}
              <div className="mt-5 flex flex-col items-center gap-2 text-xs text-gray-600">
                <p>Didn't get it? Check spam, or resend.</p>
                <button
                  type="button"
                  onClick={() => void resendMagicLink()}
                  disabled={resendCooldown > 0}
                  className="font-semibold text-emerald-700 hover:text-emerald-800 disabled:text-gray-400"
                >
                  {resendCooldown > 0 ? `Resend link in ${resendCooldown}s` : "Resend link"}
                </button>
                {resendNote && <p className="text-emerald-700">{resendNote}</p>}
              </div>
              <button
                type="button"
                onClick={() => {
                  setStatus("idle");
                  setResendCooldown(0);
                  setResendNote("");
                }}
                className="mt-6 text-xs text-gray-500 hover:text-gray-800"
              >
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
              {liveProof && (liveProof.hot || liveProof.companies) && (
                <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[11px] font-semibold text-emerald-900">
                  <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  </span>
                  <span>
                    {liveProof.hot ? `${liveProof.hot.toLocaleString()} HOT buyers live now` : "Live buyer signals scored"}
                    {liveProof.companies ? ` · ${liveProof.companies.toLocaleString()} companies tracked` : ""}
                  </span>
                </div>
              )}
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
