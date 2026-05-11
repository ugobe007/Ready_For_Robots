/**
 * Sign up — account creation entry point using the existing Supabase auth flows.
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { supabase } from "@/lib/supabase";

export default function Signup() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");

  useEffect(() => {
    if (!supabase) return;
    const client: NonNullable<typeof supabase> = supabase;

    async function afterSignup() {
      const { data } = await client.auth.getSession();
      if (data?.session) setLocation("/profile");
    }

    void afterSignup();
    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) setLocation("/profile");
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
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/signup` : "/signup";
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
    const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/signup` : "/signup";
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
    <div className="min-h-screen px-4 py-16" style={{ background: "radial-gradient(circle at 50% 0%, rgba(255,176,0,0.12), transparent 32%), #0d0520" }}>
      <div className="mx-auto grid min-h-[calc(100vh-8rem)] w-full max-w-5xl items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <Link href="/" className="mb-8 inline-flex items-center gap-2.5">
            <img src="/logo-r.png" alt="" width={34} height={34} className="h-8 w-8 object-contain opacity-95" />
            <span className="text-sm font-semibold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              ReadyForRobots
            </span>
          </Link>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.24em]" style={{ color: "#FFB000" }}>
            Create your SCOUT workspace
          </p>
          <h1 className="max-w-xl text-4xl font-black leading-tight text-white md:text-5xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
            Turn robot demand signals into a working pipeline.
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-relaxed text-white/48">
            Save matched leads, review signal context, and let SCOUT help prioritize outreach for sales and partnership opportunities.
          </p>
          <div className="mt-7 grid max-w-lg grid-cols-3 gap-2">
            {[
              ["4,427", "qualified leads"],
              ["629", "hot accounts"],
              ["7,515", "signals"],
            ].map(([value, label]) => (
              <div key={label} className="rounded-2xl border border-white/8 p-3" style={{ background: "rgba(255,255,255,0.035)" }}>
                <div className="font-mono text-lg font-black" style={{ color: "#10b981" }}>{value}</div>
                <div className="mt-1 text-[9px] font-bold uppercase tracking-widest text-white/26">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {status === "sent" ? (
          <div className="rounded-3xl border border-emerald-500/30 px-6 py-8 text-center" style={{ background: "rgba(52,211,153,0.06)" }}>
            <h2 className="text-xl font-bold text-white">Check your email</h2>
            <p className="mt-3 text-sm text-white/50">
              We sent a magic link to <span className="text-emerald-300">{email}</span>.
            </p>
            <button type="button" onClick={() => setStatus("idle")} className="mt-6 text-xs text-white/40 hover:text-white/70">
              Use a different email
            </button>
          </div>
        ) : (
          <div className="rounded-3xl border border-white/10 p-6 shadow-2xl shadow-black/40" style={{ background: "rgba(255,255,255,0.04)" }}>
            <h2 className="text-xl font-bold text-white">Start free</h2>
            <p className="mt-2 text-sm text-white/42">Create an account with Google, GitHub, or a magic link.</p>
            <div className="mt-6 flex flex-col gap-2">
              <button
                type="button"
                onClick={() => void oauth("google")}
                disabled={!supabase}
                className="w-full rounded-xl border border-white/15 px-4 py-3 text-sm font-semibold text-white/90 hover:bg-white/5 disabled:opacity-40"
              >
                Sign up with Google
              </button>
              <button
                type="button"
                onClick={() => void oauth("github")}
                disabled={!supabase}
                className="w-full rounded-xl border border-white/15 px-4 py-3 text-sm font-semibold text-white/90 hover:bg-white/5 disabled:opacity-40"
              >
                Sign up with GitHub
              </button>
            </div>
            <div className="my-5 flex items-center gap-3">
              <span className="h-px flex-1 bg-white/10" />
              <span className="text-[10px] uppercase tracking-widest text-white/30">or</span>
              <span className="h-px flex-1 bg-white/10" />
            </div>
            <form onSubmit={(e) => void magicLink(e)} className="space-y-3">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@robotcompany.com"
                disabled={status === "sending"}
                className="w-full rounded-xl border border-white/15 bg-transparent px-3 py-3 text-sm text-white placeholder-white/25 outline-none focus:border-amber-400/60"
              />
              {status === "error" && (
                <p className="rounded-lg border border-red-500/30 px-3 py-2 text-xs text-red-300">{errMsg}</p>
              )}
              <button
                type="submit"
                disabled={status === "sending" || !email.trim()}
                className="w-full rounded-xl px-4 py-3 text-sm font-black text-black transition-all hover:-translate-y-0.5 disabled:opacity-40"
                style={{ background: "#FFB000" }}
              >
                {status === "sending" ? "Sending..." : "Send signup link"}
              </button>
            </form>
            <p className="mt-5 text-center text-xs text-white/35">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold" style={{ color: "#03DAC5" }}>
                Sign in
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
