/**
 * Sign in — Supabase magic link + OAuth (Precision Intelligence light theme).
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { supabase, supabaseOAuthRedirect } from "@/lib/supabase";
import { getApiBase } from "@/lib/apiBase";
import { markFreshSignup } from "@/lib/firstSaveGuide";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  const nextPath = () => {
    if (typeof window === "undefined") return "/pipeline";
    const next = new URLSearchParams(window.location.search).get("next");
    return next && next.startsWith("/") ? next : "/pipeline";
  };

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    const params = new URLSearchParams(window.location.search);
    const authError = params.get("auth_error");
    if (authError) {
      setStatus("error");
      setErrMsg(decodeURIComponent(authError.replace(/\+/g, " ")));
      params.delete("auth_error");
      const next = params.toString();
      window.history.replaceState(null, "", next ? `/login?${next}` : "/login");
    }

    async function afterLogin() {
      const { data } = await client.auth.getSession();
      const session = data?.session;
      if (!session) return;
      try {
        const res = await fetch(`${getApiBase()}/api/user/auth-debug`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const j = await res.json();
          if (j?.is_admin) {
            setLocation("/admin");
            return;
          }
        }
      } catch {
        /* ignore */
      }
      markFreshSignup();
      setLocation(nextPath());
    }

    void afterLogin();
    const { data: sub } = client.auth.onAuthStateChange((_e, session) => {
      if (session) void afterLogin();
    });
    return () => sub.subscription.unsubscribe();
  }, [setLocation]);

  async function oauth(provider: "google" | "github") {
    if (!supabase) {
      setStatus("error");
      setErrMsg("Configure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    setErrMsg("");
    setStatus("idle");
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: supabaseOAuthRedirect(nextPath()) },
    });
    if (error) {
      setStatus("error");
      setErrMsg(error.message);
    }
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !supabase) return;
    setStatus("sending");
    setErrMsg("");
    const redirectTo = supabaseOAuthRedirect(nextPath());
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
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4 pt-24 pb-16">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <p className="section-eyebrow mb-2">Sign in</p>
            <h1 className="font-display text-2xl font-bold text-gray-900 tracking-tight">Welcome back</h1>
            <p className="text-sm text-gray-500 mt-2">Sign in to work with SIGNAL in your pipeline workspace.</p>
          </div>

          {status === "sent" ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-6 py-8 text-center">
              <h2 className="text-base font-semibold text-gray-900 mb-2">Check your email</h2>
              <p className="text-sm text-gray-600">
                We sent a magic link to <span className="font-semibold text-emerald-700">{email}</span>.
              </p>
              <button type="button" onClick={() => setStatus("idle")} className="mt-5 text-xs text-gray-500 hover:text-gray-800">
                ← use a different email
              </button>
            </div>
          ) : (
            <div className="rounded-2xl border border-gray-200 bg-white px-6 py-8 shadow-sm">
              <div className="flex flex-col gap-2 mb-5">
                <button
                  type="button"
                  onClick={() => void oauth("google")}
                  disabled={!supabase}
                  className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-xl px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                >
                  Sign in with Google
                </button>
                <button
                  type="button"
                  onClick={() => void oauth("github")}
                  disabled={!supabase}
                  className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-xl px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                >
                  Sign in with GitHub
                </button>
              </div>
              <div className="flex items-center gap-3 mb-5">
                <span className="flex-1 h-px bg-gray-200" />
                <span className="text-[10px] text-gray-400 uppercase tracking-widest">or</span>
                <span className="flex-1 h-px bg-gray-200" />
              </div>
              <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  disabled={status === "sending"}
                  className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-emerald-500"
                />
                {status === "error" && (
                  <p className="text-xs text-red-600 border border-red-200 bg-red-50 rounded-lg px-3 py-2 whitespace-pre-wrap">{errMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={status === "sending" || !email.trim()}
                  className="w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-gray-900 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40"
                >
                  {status === "sending" ? "Sending…" : "Send magic link"}
                </button>
              </form>
            </div>
          )}

          <div className="mt-6 text-center space-y-3">
            <p className="text-xs text-gray-500">
              New to ReadyForRobots?{" "}
              <Link href={`/signup${loginSearch}`} className="font-semibold text-emerald-600 hover:text-emerald-700">
                Start free workspace
              </Link>
            </p>
            <Link href="/" className="block text-xs text-gray-400 hover:text-gray-600">
              ← Back home
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
