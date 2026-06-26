/**
 * Sign up — account creation entry point using Supabase auth (Precision Intelligence light theme).
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase } from "@/lib/supabase";

const SIGNUP_NAME_KEY = "rfr_signup_full_name";

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  const search = typeof window !== "undefined" ? window.location.search : "";
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const hubspotIntent = params.get("intent") === "hubspot";
  const nextRaw = params.get("next") || "";
  const pipelineIntent = nextRaw.startsWith("/pipeline");

  const nextPath = () => {
    if (typeof window === "undefined") return "/pipeline";
    const next = params.get("next");
    return next && next.startsWith("/") ? next : "/pipeline";
  };

  const persistFullName = () => {
    if (typeof window === "undefined" || !fullName.trim()) return;
    window.localStorage.setItem(SIGNUP_NAME_KEY, fullName.trim());
  };

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    async function afterSignup() {
      const { data } = await client.auth.getSession();
      if (data?.session) setLocation(nextPath());
    }

    void afterSignup();
    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) setLocation(nextPath());
    });
    return () => sub.subscription.unsubscribe();
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
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/signup${window.location.search}` : "/signup";
    const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo } });
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
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/signup${window.location.search}` : "/signup";
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
              {hubspotIntent ? "HubSpot + SIGNAL workspace" : "Create your SIGNAL workspace"}
            </p>
            <h1 className="max-w-xl font-display text-4xl font-bold leading-tight text-gray-900 md:text-5xl">
              {hubspotIntent
                ? "Sign up, then SIGNAL links HubSpot automatically."
                : pipelineIntent
                  ? "Copy the draft. Save the lead. Run your pipeline."
                  : "Turn robot demand signals into a working pipeline."}
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-gray-600">
              {hubspotIntent
                ? "Use your work email and full name. After signup, SIGNAL provisions the HubSpot API connection and MCP bridge — no manual app setup."
                : pipelineIntent
                  ? "Free workspace: save up to 5 HOT/WARM leads, copy outreach drafts, and sync to HubSpot when you are ready. No card required."
                  : "Save matched leads, review signal context, and let SIGNAL prioritize the workflow from signal to outreach."}
            </p>
            {pipelineIntent && !hubspotIntent && (
              <ul className="mt-4 space-y-2 text-xs text-gray-600">
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Pick up exactly where you left off — same lead after signup
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  Copy signal-matched outreach drafts in one click
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-emerald-700">✓</span>
                  50 live pipeline leads · pitch actions · robot categories
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
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                >
                  Sign up with Google
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
                  className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-gray-900 transition-all hover:bg-emerald-700 disabled:opacity-40"
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
