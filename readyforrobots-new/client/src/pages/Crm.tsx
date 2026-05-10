import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";

type Team = { id: string; name: string; role: string };
type Account = {
  id: string;
  name: string;
  company_id: number | null;
  industry?: string | null;
  outreach_stage?: string | null;
  contact_email?: string | null;
};

export default function Crm() {
  const { session, loading } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const t = session?.access_token;
      if (!t) throw new Error("Not signed in");
      const base = getApiBase();
      const r = await fetch(`${base}${path}`, liveFetchInit({ ...init, headers: { ...authHeader(t), ...init.headers } }));
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  useEffect(() => {
    if (!session?.access_token) return;
    (async () => {
      setMsg("");
      try {
        const list = (await authFetch("/api/crm/teams")) as Team[];
        setTeams(Array.isArray(list) ? list : []);
        setTeamId((prev) => prev || (list[0]?.id ?? ""));
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Failed to load teams");
      }
    })();
  }, [session?.access_token, authFetch]);

  useEffect(() => {
    if (!session?.access_token || !teamId) return;
    (async () => {
      setBusy(true);
      setMsg("");
      try {
        const q = `team_id=${encodeURIComponent(teamId)}`;
        const data = (await authFetch(`/api/crm/accounts?${q}`)) as Account[];
        setAccounts(Array.isArray(data) ? data : []);
      } catch (e) {
        setMsg(e instanceof Error ? e.message : "Failed to load accounts");
        setAccounts([]);
      } finally {
        setBusy(false);
      }
    })();
  }, [session?.access_token, teamId, authFetch]);

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        <p>Supabase not configured.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center" style={{ background: "#0d0520" }}>
        <Header />
        <p className="text-white/60 mb-4">Sign in for CRM workspaces.</p>
        <Link href="/login" className="text-violet-400 underline text-sm">
          Login
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 pt-24 pb-12 px-4 max-w-4xl mx-auto w-full">
        <h1 className="text-xl font-bold text-white mb-1" style={{ fontFamily: "'Sora', system-ui" }}>
          CRM · SCOUT accounts
        </h1>
        <p className="text-xs text-white/40 mb-6">Workspaces and buyer accounts — same API as production.</p>
        {msg && <p className="text-sm text-amber-200/90 mb-4 border border-amber-500/30 rounded p-2">{msg}</p>}

        <div className="flex flex-wrap gap-2 mb-6">
          {teams.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTeamId(t.id)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg border ${
                teamId === t.id ? "border-violet-500 text-violet-200 bg-violet-500/15" : "border-white/10 text-white/50"
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>

        <div className="rounded-xl border border-white/10 overflow-hidden" style={{ background: "rgba(255,255,255,0.02)" }}>
          {busy ? (
            <p className="p-4 text-sm text-white/40">Loading accounts…</p>
          ) : accounts.length === 0 ? (
            <p className="p-4 text-sm text-white/40">No accounts in this workspace.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase text-white/30 border-b border-white/10">
                  <th className="px-3 py-2">Account</th>
                  <th className="px-3 py-2">Company #</th>
                  <th className="px-3 py-2">Stage</th>
                  <th className="px-3 py-2">Contact</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.id} className="border-b border-white/5 text-white/80">
                    <td className="px-3 py-2">{a.name}</td>
                    <td className="px-3 py-2 font-mono text-xs text-violet-300/90">{a.company_id ?? "—"}</td>
                    <td className="px-3 py-2 text-xs">{a.outreach_stage || "—"}</td>
                    <td className="px-3 py-2 text-xs truncate max-w-[140px]">{a.contact_email || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <p className="text-[10px] text-white/25 mt-4">
          Full outreach editor (draft / Resend / PDF) ships next on this route; data is already on the server.
        </p>
      </main>
    </div>
  );
}
