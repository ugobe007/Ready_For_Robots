import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { Check, ExternalLink, Link2, Loader2, Zap } from "lucide-react";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";
import { toast } from "sonner";

type SavedLead = {
  company_id: number;
  company_name: string;
  industry?: string | null;
  tier?: string | null;
};

type SetupPayload = {
  oauth_configured: boolean;
  profile_complete: boolean;
  display_name?: string | null;
  email?: string | null;
  sync_entitled: boolean;
  connection: { connected: boolean; account_login?: string | null; account_name?: string | null };
  sync: { sync_mode: "auto_all" | "manual_select"; sync_lead_ids: number[] };
  saved_leads: SavedLead[];
};

const cardClass = "rounded-2xl border border-white/10 bg-white/[0.025] p-5";

export default function HubSpotConnect() {
  const { session, loading } = useAuth();
  const [, setLocation] = useLocation();
  const [setup, setSetup] = useState<SetupPayload | null>(null);
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [syncMode, setSyncMode] = useState<"auto_all" | "manual_select">("auto_all");
  const [selectedLeadIds, setSelectedLeadIds] = useState<number[]>([]);

  const authFetch = useCallback(
    async (path: string, init: RequestInit = {}) => {
      const t = session?.access_token;
      if (!t) throw new Error("Not signed in");
      const response = await fetch(
        `${getApiBase()}${path}`,
        liveFetchInit({ ...init, headers: { ...authHeader(t), ...init.headers } }),
      );
      const text = await response.text();
      if (!response.ok) {
        let message = text || response.statusText;
        try {
          const parsed = JSON.parse(text);
          message = parsed.detail?.message || parsed.detail || message;
        } catch {
          // keep raw
        }
        throw new Error(typeof message === "string" ? message : "Request failed");
      }
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  const loadSetup = useCallback(async () => {
    const data = (await authFetch("/api/integrations/hubspot/setup")) as SetupPayload;
    setSetup(data);
    setFullName(data.display_name || "");
    setSyncMode(data.sync?.sync_mode || "auto_all");
    setSelectedLeadIds(data.sync?.sync_lead_ids || []);
  }, [authFetch]);

  useEffect(() => {
    if (loading || !session?.access_token) return;
    const stored =
      typeof window !== "undefined" ? window.localStorage.getItem("rfr_signup_full_name") : null;
    if (stored) setFullName(stored);
    void loadSetup().catch((e) => toast.error(e instanceof Error ? e.message : "Could not load HubSpot setup"));
  }, [loading, session, loadSetup]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "1") {
      toast.success("HubSpot connected — choose how SCOUT syncs your saved leads.");
      window.history.replaceState({}, "", "/integrations/hubspot");
    }
    const err = params.get("error");
    if (err) {
      toast.error(decodeURIComponent(err));
      window.history.replaceState({}, "", "/integrations/hubspot");
    }
  }, []);

  const saveProfile = async () => {
    if (!fullName.trim()) {
      toast.error("Enter your full name so SCOUT can authenticate your HubSpot workspace.");
      return;
    }
    setBusy(true);
    try {
      await authFetch("/api/user/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: fullName.trim() }),
      });
      if (typeof window !== "undefined") window.localStorage.removeItem("rfr_signup_full_name");
      await loadSetup();
      toast.success("Profile saved");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save profile");
    } finally {
      setBusy(false);
    }
  };

  const startHubSpotOAuth = async () => {
    setBusy(true);
    try {
      const data = await authFetch("/api/integrations/hubspot/connect-url?return_to=/integrations/hubspot");
      if (!data.auth_url) throw new Error("HubSpot connect URL missing");
      window.location.href = data.auth_url;
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not start HubSpot connect");
      setBusy(false);
    }
  };

  const saveSyncSettings = async () => {
    setBusy(true);
    try {
      await authFetch("/api/integrations/hubspot/sync-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sync_mode: syncMode,
          sync_lead_ids: syncMode === "manual_select" ? selectedLeadIds : [],
        }),
      });
      toast.success("HubSpot sync preferences saved");
      await loadSetup();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save sync settings");
    } finally {
      setBusy(false);
    }
  };

  const toggleLead = (companyId: number) => {
    setSelectedLeadIds((ids) =>
      ids.includes(companyId) ? ids.filter((id) => id !== companyId) : [...ids, companyId],
    );
  };

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center text-white/50" style={{ background: "#0d0520" }}>
        <Header />
        <p>Supabase is not configured.</p>
      </div>
    );
  }

  if (!loading && !session) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
        <Header />
        <main className="mx-auto w-full max-w-lg flex-1 px-4 pb-16 pt-24 text-center">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
            HubSpot + SCOUT
          </p>
          <h1 className="mt-2 text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
            Connect HubSpot automatically
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-white/45">
            Create your SCOUT workspace first with email and full name. We provision the HubSpot API link and MCP bridge —
            no manual private-app setup.
          </p>
          <Link
            href="/signup?intent=hubspot&next=/integrations/hubspot"
            className="mt-6 inline-flex rounded-xl px-5 py-3 text-sm font-bold"
            style={{ color: "#160b2c", background: "#FFB000" }}
          >
            Sign up to connect HubSpot
          </Link>
        </main>
      </div>
    );
  }

  const connected = setup?.connection?.connected;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-16 pt-24">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
          HubSpot integration
        </p>
        <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
          Link HubSpot to SCOUT
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-white/45">
          SCOUT connects to your HubSpot account via OAuth, provisions the MCP server bridge, and syncs saved sales leads —
          automatically or only the accounts you pick.
        </p>

        {!setup ? (
          <p className="mt-8 text-sm text-white/40">Loading setup…</p>
        ) : (
          <div className="mt-6 space-y-4">
            <section className={cardClass}>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Step 1 · Workspace</p>
              {!setup.profile_complete ? (
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-white/55">Confirm your name and email before we authenticate with HubSpot.</p>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Full name"
                    className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none"
                  />
                  <p className="text-xs text-white/35">{setup.email}</p>
                  <button
                    type="button"
                    onClick={() => void saveProfile()}
                    disabled={busy}
                    className="rounded-lg px-4 py-2 text-xs font-bold disabled:opacity-50"
                    style={{ background: "#03DAC5", color: "#0d0520" }}
                  >
                    Save profile
                  </button>
                </div>
              ) : (
                <p className="mt-2 text-sm text-white/60">
                  <Check className="inline h-3.5 w-3.5 text-emerald-400 mr-1" />
                  {setup.display_name} · {setup.email}
                </p>
              )}
            </section>

            <section className={cardClass}>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Step 2 · HubSpot API</p>
              {connected ? (
                <div className="mt-2">
                  <p className="inline-flex items-center gap-2 text-sm font-bold text-emerald-300">
                    <Check className="h-4 w-4" /> Connected and active
                  </p>
                  {(setup.connection.account_login || setup.connection.account_name) && (
                    <p className="mt-1 text-xs text-white/50">
                      HubSpot account: {setup.connection.account_login || setup.connection.account_name}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-white/35">MCP bridge provisioned on SCOUT — no manual HubSpot app setup.</p>
                </div>
              ) : (
                <div className="mt-3">
                  <p className="text-sm text-white/55 mb-3">
                    One click authorizes SCOUT with HubSpot. We build the API link automatically.
                  </p>
                  <button
                    type="button"
                    onClick={() => void startHubSpotOAuth()}
                    disabled={busy || !setup.profile_complete || !setup.oauth_configured}
                    className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold disabled:opacity-50"
                    style={{ color: "#160b2c", background: "#FFB000" }}
                  >
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
                    Connect HubSpot automatically
                  </button>
                  {!setup.oauth_configured && (
                    <p className="mt-2 text-xs text-amber-300/80">HubSpot OAuth is finishing rollout on the server — try again soon.</p>
                  )}
                </div>
              )}
            </section>

            {connected && (
              <section className={cardClass}>
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Step 3 · Sync saved leads</p>
                <p className="mt-2 text-sm text-white/55">
                  Choose whether SCOUT sends every saved lead to HubSpot or only the accounts you select.
                </p>
                <div className="mt-3 flex flex-col gap-2">
                  <label className="flex items-start gap-2 rounded-lg border border-white/10 px-3 py-2.5 cursor-pointer">
                    <input
                      type="radio"
                      name="sync_mode"
                      checked={syncMode === "auto_all"}
                      onChange={() => setSyncMode("auto_all")}
                      className="mt-1"
                    />
                    <span>
                      <span className="block text-sm font-bold text-white">Auto-sync all saved leads</span>
                      <span className="block text-xs text-white/40">SCOUT pushes every lead in your workspace to HubSpot.</span>
                    </span>
                  </label>
                  <label className="flex items-start gap-2 rounded-lg border border-white/10 px-3 py-2.5 cursor-pointer">
                    <input
                      type="radio"
                      name="sync_mode"
                      checked={syncMode === "manual_select"}
                      onChange={() => setSyncMode("manual_select")}
                      className="mt-1"
                    />
                    <span>
                      <span className="block text-sm font-bold text-white">Choose leads from my profile</span>
                      <span className="block text-xs text-white/40">Pick which saved accounts sync to HubSpot.</span>
                    </span>
                  </label>
                </div>

                {syncMode === "manual_select" && (
                  <div className="mt-3 max-h-48 overflow-y-auto space-y-1.5 rounded-lg border border-white/8 p-2">
                    {setup.saved_leads.length === 0 ? (
                      <p className="text-xs text-white/40 px-2 py-3">
                        No saved leads yet.{" "}
                        <Link href="/pipeline" className="text-violet-300 underline">
                          Save leads from Pipeline
                        </Link>{" "}
                        first.
                      </p>
                    ) : (
                      setup.saved_leads.map((lead) => (
                        <label
                          key={lead.company_id}
                          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-white/70 hover:bg-white/[0.03] cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedLeadIds.includes(lead.company_id)}
                            onChange={() => toggleLead(lead.company_id)}
                          />
                          <span className="font-semibold text-white/85">{lead.company_name}</span>
                          {lead.tier && <span className="text-white/35">· {lead.tier}</span>}
                        </label>
                      ))
                    )}
                  </div>
                )}

                {!setup.sync_entitled && syncMode === "auto_all" && (
                  <p className="mt-2 text-xs text-amber-300/85">
                    Auto-sync all leads is included on Pro and Premium.{" "}
                    <Link href="/pricing" className="underline">Upgrade</Link> or choose specific leads on the free plan.
                  </p>
                )}

                <button
                  type="button"
                  onClick={() => void saveSyncSettings()}
                  disabled={busy || (syncMode === "manual_select" && selectedLeadIds.length === 0)}
                  className="mt-4 inline-flex items-center gap-2 rounded-lg border border-teal-400/30 bg-teal-400/10 px-4 py-2 text-xs font-bold text-teal-100 disabled:opacity-50"
                >
                  <Zap className="h-3.5 w-3.5" />
                  Save sync preferences
                </button>
              </section>
            )}

            <p className="text-center text-xs text-white/30">
              <Link href="/profile" className="text-violet-300 underline">
                Manage on Profile
              </Link>
              {" · "}
              <Link href="/pipeline" className="text-violet-300 underline">
                Back to Pipeline
              </Link>
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
