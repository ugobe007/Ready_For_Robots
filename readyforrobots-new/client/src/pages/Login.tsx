/**
 * Sign in — same Supabase flows as the legacy Next login page.
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { supabase } from "@/lib/supabase";
import { getApiBase } from "@/lib/apiBase";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  const nextPath = () => {
    if (typeof window === "undefined") return "/profile";
    const next = new URLSearchParams(window.location.search).get("next");
    return next && next.startsWith("/") ? next : "/profile";
  };

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;
    if (typeof window !== "undefined" && window.location.hash) {
      const params = new URLSearchParams(window.location.hash.slice(1));
      const err = params.get("error");
      const desc = params.get("error_description");
      if (err) {
        setStatus("error");
        setErrMsg(desc || err);
        window.history.replaceState(null, "", window.location.pathname);
        return;
      }
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
      setLocation(nextPath());
    }

    void afterLogin();
    const { data: sub } = client.auth.onAuthStateChange((_e, session) => {
      if (session) void afterLogin();
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  async function oauth(provider: "google" | "github") {
    if (!supabase) {
      setStatus("error");
      setErrMsg("Configure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    setErrMsg("");
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/login${window.location.search}` : "/login";
    const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo } });
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
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/login${window.location.search}` : "/login";
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

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#0d0520" }}>
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-white tracking-tight" style={{ fontFamily: "'Sora', system-ui" }}>
            ReadyForRobots
          </h1>
          <p className="text-xs text-white/40 mt-1">Sign in to work with SCOUT</p>
        </div>

        {status === "sent" ? (
          <div className="rounded-lg border border-emerald-500/30 px-6 py-8 text-center" style={{ background: "rgba(52,211,153,0.06)" }}>
            <h2 className="text-base font-semibold text-white mb-2">Check your email</h2>
            <p className="text-sm text-white/50">
              We sent a magic link to <span className="text-emerald-300">{email}</span>.
            </p>
            <button type="button" onClick={() => setStatus("idle")} className="mt-5 text-xs text-white/40 hover:text-white/70">
              ← use a different email
            </button>
          </div>
        ) : (
          <div className="rounded-lg border border-white/10 px-6 py-8" style={{ background: "rgba(255,255,255,0.03)" }}>
            <div className="flex flex-col gap-2 mb-5">
              <button
                type="button"
                onClick={() => void oauth("google")}
                disabled={!supabase}
                className="w-full flex items-center justify-center gap-2 border border-white/15 rounded-lg px-4 py-2.5 text-sm text-white/90 hover:bg-white/5 disabled:opacity-40"
              >
                Sign in with Google
              </button>
              <button
                type="button"
                onClick={() => void oauth("github")}
                disabled={!supabase}
                className="w-full flex items-center justify-center gap-2 border border-white/15 rounded-lg px-4 py-2.5 text-sm text-white/90 hover:bg-white/5 disabled:opacity-40"
              >
                Sign in with GitHub
              </button>
            </div>
            <div className="flex items-center gap-3 mb-5">
              <span className="flex-1 h-px bg-white/10" />
              <span className="text-[10px] text-white/30 uppercase">or</span>
              <span className="flex-1 h-px bg-white/10" />
            </div>
            <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={status === "sending"}
                className="w-full bg-transparent border border-white/15 rounded-lg px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:border-violet-500/60"
              />
              {status === "error" && (
                <p className="text-xs text-red-300 border border-red-500/30 rounded px-3 py-2">{errMsg}</p>
              )}
              <button
                type="submit"
                disabled={status === "sending" || !email.trim()}
                className="w-full rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
                style={{ background: "#7c3aed" }}
              >
                {status === "sending" ? "Sending…" : "Send magic link"}
              </button>
            </form>
          </div>
        )}

        <div className="mt-6 text-center">
          <Link href="/" className="text-xs text-white/35 hover:text-white/60">
            ← Back home
          </Link>
        </div>
      </div>
    </div>
  );
}
