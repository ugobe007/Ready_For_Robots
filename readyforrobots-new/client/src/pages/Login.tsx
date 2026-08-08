/**
 * Sign in — Supabase magic link + OAuth (dark workflow theme).
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase, supabaseOAuthRedirect } from "@/lib/supabase";
import { getApiBase } from "@/lib/apiBase";
import { readNextParam, peekPendingNext, postAuthRedirectTarget, storePendingNext, readPlanParam, storeCheckoutIntent, resolvePostAuthPath, navigateAfterAuth } from "@/lib/authNext";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  const redirectTarget = () => postAuthRedirectTarget("/pipeline");

  useEffect(() => {
    const plan = readPlanParam();
    if (plan) storeCheckoutIntent(plan);
    const next = readNextParam();
    if (next) storePendingNext(next);
  }, []);

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    const params = new URLSearchParams(window.location.search);
    const authError = params.get("auth_error");

    const handleAuthErrorIfNeeded = async () => {
      if (!authError) return;
      const { data } = await client.auth.getSession();
      if (data?.session) {
        const dest = resolvePostAuthPath("/pipeline");
        navigateAfterAuth(dest);
        return;
      }
      setStatus("error");
      setErrMsg(decodeURIComponent(authError.replace(/\+/g, " ")));
      params.delete("auth_error");
      const next = params.toString();
      window.history.replaceState(null, "", next ? `/login?${next}` : "/login");
    };

    void handleAuthErrorIfNeeded();

    async function afterLogin() {
      const { data } = await client.auth.getSession();
      const session = data?.session;
      if (!session) return;
      const hasExplicitReturn = Boolean(readNextParam() || peekPendingNext());
      const dest = resolvePostAuthPath("/pipeline");
      try {
        const res = await fetch(`${getApiBase()}/api/user/auth-debug`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const j = await res.json();
          if (j?.is_admin && !hasExplicitReturn && dest === "/pipeline") {
            setLocation("/admin");
            return;
          }
        }
      } catch {
        /* ignore */
      }
      navigateAfterAuth(dest);
    }

    void afterLogin();
    const { data: sub } = client.auth.onAuthStateChange((_e, session) => {
      if (session) void afterLogin();
    });
    return () => sub.subscription.unsubscribe();
  }, [setLocation]);

  async function oauth(provider: "google" | "github" | "azure") {
    if (!supabase) {
      setStatus("error");
      setErrMsg("Configure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    setErrMsg("");
    setStatus("idle");
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: supabaseOAuthRedirect(redirectTarget()) },
    });
    if (error) {
      setStatus("error");
      setErrMsg(
        provider === "azure" && /provider is not enabled/i.test(error.message)
          ? "Microsoft sign-in is not enabled yet in Supabase Auth (Azure provider). Use Google or a magic link, or enable Azure in the Supabase dashboard."
          : error.message,
      );
    }
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !supabase) return;
    setStatus("sending");
    setErrMsg("");
    const redirectTo = supabaseOAuthRedirect(redirectTarget());
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

  const loginSearch = typeof window !== "undefined" ? window.location.search : "";

  return (
    <div className="min-h-screen flex flex-col bg-[#081126] text-slate-100">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4 pt-24 pb-16">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <p className="section-eyebrow mb-2">Sign in</p>
            <h1 className="font-display text-3xl font-bold text-slate-100 tracking-tight">Welcome back</h1>
            <p className="text-sm text-slate-300 mt-2">Sign in to work with SIGNAL in your pipeline workspace.</p>
          </div>

          {status === "sent" ? (
            <div className="rounded-2xl border border-emerald-400/35 bg-emerald-950/30 px-6 py-8 text-center">
              <h2 className="text-base font-semibold text-slate-100 mb-2">Check your email</h2>
              <p className="text-sm text-slate-300">
                We sent a magic link to <span className="font-semibold text-emerald-300">{email}</span>.
              </p>
              <button type="button" onClick={() => setStatus("idle")} className="mt-5 text-xs text-slate-400 hover:text-slate-200">
                Back to sign-in options
              </button>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-700/70 bg-[#0b162f]/85 px-6 py-8 shadow-[0_20px_45px_-25px_rgba(0,0,0,0.8)]">
              <div className="flex flex-col gap-2 mb-5">
                <button
                  type="button"
                  onClick={() => void oauth("google")}
                  disabled={!supabase}
                  className="w-full flex items-center justify-center gap-2 border border-slate-600 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/70 disabled:opacity-40"
                >
                  Sign in with Google
                </button>
                <button
                  type="button"
                  onClick={() => void oauth("azure")}
                  disabled={!supabase}
                  className="w-full flex items-center justify-center gap-2 border border-slate-600 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/70 disabled:opacity-40"
                >
                  Sign in with Microsoft 365
                </button>
                <button
                  type="button"
                  onClick={() => void oauth("github")}
                  disabled={!supabase}
                  className="w-full flex items-center justify-center gap-2 border border-slate-600 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800/70 disabled:opacity-40"
                >
                  Sign in with GitHub
                </button>
              </div>
              <div className="flex items-center gap-3 mb-5">
                <span className="flex-1 h-px bg-slate-700" />
                <span className="text-[10px] text-slate-500 uppercase tracking-widest">or</span>
                <span className="flex-1 h-px bg-slate-700" />
              </div>
              <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  disabled={status === "sending"}
                  className="w-full rounded-xl border border-slate-600 bg-[#0a1327] px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-400"
                />
                {status === "error" && (
                  <p className="text-xs text-red-200 border border-red-400/40 bg-red-900/30 rounded-lg px-3 py-2 whitespace-pre-wrap">{errMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={status === "sending" || !email.trim()}
                  className="w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-[#06261f] bg-emerald-400 hover:bg-emerald-300 disabled:opacity-40"
                >
                  {status === "sending" ? "Sending…" : "Send magic link"}
                </button>
              </form>
            </div>
          )}

          <div className="mt-6 text-center space-y-3">
            <p className="text-xs text-slate-400">
              New to ReadyForRobots?{" "}
              <Link href={`/signup${loginSearch}`} className="font-semibold text-emerald-300 hover:text-emerald-200">
                Start free workspace
              </Link>
            </p>
            <Link href="/" className="block text-xs text-slate-500 hover:text-slate-300">
              ← Back home
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
