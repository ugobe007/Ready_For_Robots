import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import { Check, ExternalLink, Github, Link2, Plug, Unplug } from "lucide-react";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import SiteFooter from "@/components/layout/SiteFooter";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader, supabase } from "@/lib/supabase";
import { toast } from "sonner";

type IntegrationCard = {
  provider: "hubspot" | "github";
  name: string;
  description: string;
  docs_url: string;
  scopes_hint: string;
  connected: boolean;
  status: string;
  connected_at?: string | null;
  account_login?: string | null;
  account_name?: string | null;
  entitled: boolean;
  entitlement_message?: string | null;
};

const cardClass = "rounded-2xl border border-gray-200 bg-white p-5";

function HubSpotMark() {
  return (
    <div
      className="flex h-11 w-11 items-center justify-center rounded-xl text-sm font-black"
      style={{ background: "#ff7a59", color: "#fff" }}
    >
      HS
    </div>
  );
}

function GitHubMark() {
  return (
    <div
      className="flex h-11 w-11 items-center justify-center rounded-xl"
      style={{ background: "rgba(255,255,255,0.08)", color: "#fff" }}
    >
      <Github className="h-5 w-5" />
    </div>
  );
}

function CrmMark({ label, color }: { label: string; color: string }) {
  return (
    <div
      className="flex h-11 w-11 items-center justify-center rounded-xl text-xs font-black"
      style={{ background: `${color}22`, color, border: `1px solid ${color}44` }}
    >
      {label}
    </div>
  );
}

const upcomingCrms = [
  {
    id: "salesforce",
    name: "Salesforce",
    mark: "SF",
    color: "#00A1E0",
    description: "Push qualified leads, Signal scores, and outreach briefs into Salesforce opportunities—same OAuth pattern as HubSpot.",
  },
  {
    id: "pipedrive",
    name: "Pipedrive",
    mark: "PD",
    color: "#017737",
    description: "Sync robot-ready accounts and trigger-based outreach into Pipedrive deals and activities.",
  },
];

export default function Integrations() {
  const { session, loading } = useAuth();
  const [integrations, setIntegrations] = useState<IntegrationCard[]>([]);
  const [busyProvider, setBusyProvider] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<IntegrationCard | null>(null);
  const [token, setToken] = useState("");

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
          message = parsed.detail?.message || parsed.detail || parsed.message || message;
        } catch {
          // keep raw text
        }
        throw new Error(typeof message === "string" ? message : "Request failed");
      }
      return text ? JSON.parse(text) : null;
    },
    [session?.access_token],
  );

  const loadIntegrations = useCallback(async () => {
    if (!session?.access_token) return;
    const data = await authFetch("/api/integrations");
    setIntegrations(data.integrations || []);
  }, [authFetch, session?.access_token]);

  useEffect(() => {
    if (loading || !session?.access_token) return;
    void loadIntegrations().catch((e) => toast.error(e instanceof Error ? e.message : "Could not load integrations"));
  }, [loading, session, loadIntegrations]);

  const openConnect = (integration: IntegrationCard) => {
    if (!integration.entitled) {
      toast.error(integration.entitlement_message || "Upgrade required");
      return;
    }
    setConnecting(integration);
    setToken("");
  };

  const submitConnect = async () => {
    if (!connecting) return;
    setBusyProvider(connecting.provider);
    try {
      const updated = await authFetch(`/api/integrations/${connecting.provider}/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      setIntegrations((rows) =>
        rows.map((row) => (row.provider === connecting.provider ? { ...row, ...updated } : row)),
      );
      setConnecting(null);
      setToken("");
      toast.success(`${connecting.name} connected`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Connect failed");
    } finally {
      setBusyProvider(null);
    }
  };

  const disconnect = async (integration: IntegrationCard) => {
    setBusyProvider(integration.provider);
    try {
      const updated = await authFetch(`/api/integrations/${integration.provider}/disconnect`, {
        method: "DELETE",
      });
      setIntegrations((rows) =>
        rows.map((row) => (row.provider === integration.provider ? { ...row, ...updated } : row)),
      );
      toast.success(`${integration.name} disconnected`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Disconnect failed");
    } finally {
      setBusyProvider(null);
    }
  };

  if (!supabase) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center text-gray-500 bg-slate-50">
        <Header />
        <p>Supabase is not configured in this build.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 text-center text-gray-500 bg-slate-50">
        <Header />
        Loading…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Header />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-16 pt-24 text-center">
          <Plug className="mx-auto mb-4 h-8 w-8 text-emerald-600" />
          <h1 className="text-2xl font-black text-gray-900">
            Connect your stack
          </h1>
          <p className="mt-3 text-sm text-gray-500">
            Sign in to connect HubSpot (live) and GitHub. Salesforce and Pipedrive are next—run Signal in the native workspace until your CRM connector ships.
          </p>
          <Link
            href="/login?next=/integrations"
            className="mt-6 inline-flex rounded-xl px-4 py-2.5 text-xs font-bold"
            style={{ color: "#111827", background: "#FFB000" }}
          >
            Sign in to connect
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="admin-workspace min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-28">
        <AdminNav />
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
          Integrations
        </p>
        <h1 className="text-2xl font-black text-gray-900">
          Connect Signal to your stack
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-500">
          <span className="font-semibold text-gray-600">HubSpot</span> sync is live—OAuth connect, no manual app setup.
          Use the native Signal workspace if you run another CRM today; Salesforce and Pipedrive connectors are coming soon.
        </p>

        <p className="mt-6 text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">Available now</p>
        <div className="mt-3 space-y-4">
          {integrations.map((integration) => {
            const Icon = integration.provider === "github" ? GitHubMark : HubSpotMark;
            const isBusy = busyProvider === integration.provider;
            return (
              <section key={integration.provider} className={cardClass}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <Icon />
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-lg font-black text-gray-900">{integration.name}</h2>
                        {integration.connected ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-300">
                            <Check className="h-3 w-3" /> Connected
                          </span>
                        ) : (
                          <span className="rounded-full border border-gray-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-gray-400">
                            Not connected
                          </span>
                        )}
                      </div>
                      <p className="mt-1 max-w-xl text-sm text-gray-500">{integration.description}</p>
                      {integration.connected && (integration.account_login || integration.account_name) && (
                        <p className="mt-2 text-xs text-gray-500">
                          Account: <span className="font-mono text-gray-700">{integration.account_login || integration.account_name}</span>
                        </p>
                      )}
                      {!integration.entitled && integration.entitlement_message && (
                        <p className="mt-2 text-xs text-amber-300/90">{integration.entitlement_message}</p>
                      )}
                      <a
                        href={integration.docs_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-700"
                      >
                        Create API token <ExternalLink className="h-3 w-3" />
                      </a>
                      <p className="mt-1 text-[11px] text-gray-400">Scopes: {integration.scopes_hint}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {integration.connected ? (
                      <button
                        type="button"
                        onClick={() => void disconnect(integration)}
                        disabled={isBusy}
                        className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-600 disabled:opacity-50"
                      >
                        <Unplug className="h-3.5 w-3.5" />
                        {isBusy ? "Disconnecting…" : "Disconnect"}
                      </button>
                    ) : integration.provider === "hubspot" ? (
                      <Link
                        href="/integrations/hubspot"
                        className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold"
                        style={{ color: "#111827", background: "#FFB000" }}
                      >
                        <Link2 className="h-3.5 w-3.5" />
                        Connect {integration.name}
                      </Link>
                    ) : integration.entitled ? (
                      <button
                        type="button"
                        onClick={() => openConnect(integration)}
                        disabled={isBusy}
                        className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50"
                        style={{ color: "#111827", background: "#FFB000" }}
                      >
                        <Link2 className="h-3.5 w-3.5" />
                        Connect {integration.name}
                      </button>
                    ) : (
                      <Link
                        href="/pricing"
                        className="inline-flex items-center gap-2 rounded-xl border border-amber-400/35 bg-amber-400/10 px-4 py-2 text-xs font-bold text-amber-100"
                      >
                        Upgrade to connect
                      </Link>
                    )}
                  </div>
                </div>
              </section>
            );
          })}
        </div>

        <p className="mt-8 text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">CRM connectors · coming soon</p>
        <div className="mt-3 space-y-4">
          {upcomingCrms.map((crm) => (
            <section key={crm.id} className={cardClass}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <CrmMark label={crm.mark} color={crm.color} />
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-black text-gray-900">{crm.name}</h2>
                      <span className="rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-gray-500">
                        Coming soon
                      </span>
                    </div>
                    <p className="mt-1 max-w-xl text-sm text-gray-500">{crm.description}</p>
                    <p className="mt-2 text-xs text-gray-400">
                      Until launch: prospect, qualify, and run outreach in Signal—export leads and briefs into {crm.name}.
                    </p>
                  </div>
                </div>
                <Link
                  href="/pipeline"
                  className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-500 hover:text-gray-800"
                >
                  Use Signal workspace
                </Link>
              </div>
            </section>
          ))}
        </div>

        <section className={`${cardClass} mt-6 border-teal-400/15 bg-teal-400/[0.04]`}>
          <p className="text-sm font-bold text-gray-900">No external CRM yet?</p>
          <p className="mt-1 text-xs text-gray-500">
            Signal includes a native pipeline for prospecting, qualifying, and outreach. Connect{" "}
            <span style={{ color: "#FFB000", fontWeight: 600 }}>HubSpot</span> when you are ready—your system of record stays yours.
          </p>
        </section>

        <section className={`${cardClass} mt-4 border-emerald-500/20 bg-emerald-600/[0.04]`}>
          <p className="text-sm font-bold text-gray-900">Need ERP or MCP partner keys?</p>
          <p className="mt-1 text-xs text-gray-500">
            Advanced marketplace connections (scoped MCP servers, secret references) live on the{" "}
            <Link href="/marketplace" className="text-emerald-600 underline">
              Marketplace workspace
            </Link>
            .
          </p>
        </section>
      </main>

      {connecting && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-5 shadow-2xl">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">Connect {connecting.name}</p>
            <h3 className="mt-1 text-lg font-black text-gray-900">Paste your API token</h3>
            <p className="mt-2 text-xs leading-relaxed text-gray-500">
              We verify the token with {connecting.name}, store it encrypted for your workspace, and never show it again.
            </p>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder={connecting.provider === "hubspot" ? "pat-na1-..." : "github_pat_..."}
              autoComplete="off"
              className="mt-4 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm font-mono text-gray-900 outline-none placeholder:text-gray-400"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setConnecting(null);
                  setToken("");
                }}
                className="rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void submitConnect()}
                disabled={!token.trim() || busyProvider === connecting.provider}
                className="rounded-lg px-3 py-2 text-xs font-bold disabled:opacity-50"
                style={{ color: "#111827", background: "#FFB000" }}
              >
                {busyProvider === connecting.provider ? "Verifying…" : "Connect"}
              </button>
            </div>
          </div>
        </div>
      )}

      <SiteFooter />
    </div>
  );
}
