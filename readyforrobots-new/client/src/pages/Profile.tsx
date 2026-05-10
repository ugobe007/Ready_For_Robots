import { useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";

export default function Profile() {
  const { session, loading } = useAuth();
  const [me, setMe] = useState<{ email?: string; display_name?: string | null } | null>(null);
  const [counts, setCounts] = useState({ saved: 0, reports: 0, lists: 0 });
  const [err, setErr] = useState("");

  useEffect(() => {
    if (loading || !session?.access_token) return;
    const t = session.access_token;
    const base = getApiBase();
    (async () => {
      setErr("");
      try {
        const [rMe, rSaved, rReports, rLists] = await Promise.all([
          fetch(`${base}/api/user/me`, liveFetchInit({ headers: { ...authHeader(t) } })),
          fetch(`${base}/api/user/saved`, liveFetchInit({ headers: { ...authHeader(t) } })),
          fetch(`${base}/api/user/reports`, liveFetchInit({ headers: { ...authHeader(t) } })),
          fetch(`${base}/api/user/lists`, liveFetchInit({ headers: { ...authHeader(t) } })),
        ]);
        if (!rMe.ok) throw new Error(await rMe.text());
        setMe(await rMe.json());
        const saved = rSaved.ok ? (await rSaved.json() as unknown[]).length : undefined;
        const reports = rReports.ok ? (await rReports.json() as unknown[]).length : undefined;
        const lists = rLists.ok ? (await rLists.json() as unknown[]).length : undefined;
        setCounts((c) => ({
          saved: saved ?? c.saved,
          reports: reports ?? c.reports,
          lists: lists ?? c.lists,
        }));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Failed to load profile");
      }
    })();
  }, [session, loading]);

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        <p>Supabase is not configured in this build.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 text-center text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center" style={{ background: "#0d0520" }}>
        <Header />
        <p className="text-white/60 mb-4">Sign in to view your workspace.</p>
        <Link href="/login" className="text-violet-400 underline text-sm">
          Go to login
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 pt-24 pb-12 px-4 max-w-lg mx-auto w-full">
        <h1 className="text-xl font-bold text-white mb-1" style={{ fontFamily: "'Sora', system-ui" }}>
          Your workspace
        </h1>
        <p className="text-xs text-white/40 mb-6">Same data as before — powered by SCOUT + FastAPI.</p>
        {err && <p className="text-sm text-red-300 mb-4 border border-red-500/30 rounded p-2">{err}</p>}
        <div className="rounded-xl border border-white/10 p-4 space-y-2 mb-6" style={{ background: "rgba(255,255,255,0.03)" }}>
          <p className="text-[10px] uppercase tracking-widest text-white/30">Signed in as</p>
          <p className="text-sm text-white font-medium">{me?.display_name || me?.email || session.user.email}</p>
          <p className="text-xs text-white/40">{session.user.email}</p>
        </div>
        <div className="grid grid-cols-3 gap-2 mb-8">
          {[
            { n: counts.saved, l: "Saved" },
            { n: counts.reports, l: "Reports" },
            { n: counts.lists, l: "Lists" },
          ].map((x) => (
            <div key={x.l} className="rounded-lg border border-white/10 p-3 text-center" style={{ background: "rgba(255,255,255,0.03)" }}>
              <p className="text-lg font-mono font-bold text-violet-300">{x.n}</p>
              <p className="text-[10px] text-white/35 uppercase">{x.l}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-white/35 mb-4">
          Proposal sender settings and full report browser live under{" "}
          <span className="text-white/60">Profile → Settings</span> in the roadmap; CRM outreach is on{" "}
          <Link href="/crm" className="text-violet-400 underline">
            /crm
          </Link>
          .
        </p>
        <button
          type="button"
          onClick={() => void supabase?.auth.signOut()}
          className="text-xs text-red-400/90 border border-red-500/30 rounded px-3 py-2 hover:bg-red-500/10"
        >
          Sign out
        </button>
      </main>
    </div>
  );
}
