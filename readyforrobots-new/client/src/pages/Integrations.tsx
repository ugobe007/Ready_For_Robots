import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import { Check, ExternalLink, Github, Link2, Plug, Unplug } from "lucide-react";
import Header from "@/components/Header";
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

const cardClass = "rounded-2xl border border-white/10 bg-white/[0.025] p-5";

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
      <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
        <Header />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-16 pt-24 text-center">
          <Plug className="mx-auto mb-4 h-8 w-8 text-violet-300" />
          <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
            Connect your stack
          </h1>
          <p className="mt-3 text-sm text-white/45">
            Sign in to connect HubSpot and GitHub — same one-click flow as Vercel or GitHub app installs.
          </p>
          <Link
            href="/login?next=/integrations"
            className="mt-6 inline-flex rounded-xl px-4 py-2.5 text-xs font-bold"
            style={{ color: "#160b2c", background: "#FFB000" }}
          >
            Sign in to connect
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-24">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>
          Integrations
        </p>
        <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Sora', system-ui" }}>
          Connect HubSpot and GitHub
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/45">
          Paste a private app token or personal access token once. SCOUT handles outbound CRM sync and developer context —
          no MCP URLs or secret manager references required.
        </p>

        <div className="mt-8 space-y-4">
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
                        <h2 className="text-lg font-black text-white">{integration.name}</h2>
                        {integration.connected ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-300">
                            <Check className="h-3 w-3" /> Connected
                          </span>
                        ) : (
                          <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white/35">
                            Not connected
                          </span>
                        )}
                      </div>
                      <p className="mt-1 max-w-xl text-sm text-white/45">{integration.description}</p>
                      {integration.connected && (integration.account_login || integration.account_name) && (
                        <p className="mt-2 text-xs text-white/55">
                          Account: <span className="font-mono text-white/75">{integration.account_login || integration.account_name}</span>
                        </p>
                      )}
                      {!integration.entitled && integration.entitlement_message && (
                        <p className="mt-2 text-xs text-amber-300/90">{integration.entitlement_message}</p>
                      )}
                      <a
                        href={integration.docs_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-violet-300 hover:text-violet-200"
                      >
                        Create API token <ExternalLink className="h-3 w-3" />
                      </a>
                      <p className="mt-1 text-[11px] text-white/30">Scopes: {integration.scopes_hint}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {integration.connected ? (
                      <button
                        type="button"
                        onClick={() => void disconnect(integration)}
                        disabled={isBusy}
                        className="inline-flex items-center gap-2 rounded-xl border border-white/15 px-4 py-2 text-xs font-bold text-white/70 disabled:opacity-50"
                      >
                        <Unplug className="h-3.5 w-3.5" />
                        {isBusy ? "Disconnecting…" : "Disconnect"}
                      </button>
                    ) : integration.provider === "hubspot" ? (
                      <Link
                        href="/integrations/hubspot"
                        className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold"
                        style={{ color: "#160b2c", background: "#FFB000" }}
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
                        style={{ color: "#160b2c", background: "#FFB000" }}
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

        <section className={`${cardClass} mt-6 border-violet-500/20 bg-violet-500/[0.04]`}>
          <p className="text-sm font-bold text-white">Need ERP or MCP partner keys?</p>
          <p className="mt-1 text-xs text-white/40">
            Advanced marketplace connections (scoped MCP servers, secret references) live on the{" "}
            <Link href="/marketplace" className="text-violet-300 underline">
              Marketplace workspace
            </Link>
            .
          </p>
        </section>
      </main>

      {connecting && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#160b2c] p-5 shadow-2xl">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/30">Connect {connecting.name}</p>
            <h3 className="mt-1 text-lg font-black text-white">Paste your API token</h3>
            <p className="mt-2 text-xs leading-relaxed text-white/45">
              We verify the token with {connecting.name}, store it encrypted for your workspace, and never show it again.
            </p>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder={connecting.provider === "hubspot" ? "pat-na1-..." : "github_pat_..."}
              autoComplete="off"
              className="mt-4 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm font-mono text-white outline-none placeholder:text-white/25"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setConnecting(null);
                  setToken("");
                }}
                className="rounded-lg border border-white/15 px-3 py-2 text-xs font-bold text-white/60"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void submitConnect()}
                disabled={!token.trim() || busyProvider === connecting.provider}
                className="rounded-lg px-3 py-2 text-xs font-bold disabled:opacity-50"
                style={{ color: "#160b2c", background: "#FFB000" }}
              >
                {busyProvider === connecting.provider ? "Verifying…" : "Connect"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
