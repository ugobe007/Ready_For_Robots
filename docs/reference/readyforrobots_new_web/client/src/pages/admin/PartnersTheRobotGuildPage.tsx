import SiteShell from "@/components/SiteShell";
import MarketingPageLayout from "@/components/MarketingPageLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getApiBase } from "@/lib/apiBase";
import { Link } from "wouter";
import { useCallback, useEffect, useState } from "react";

const TOKEN_KEY = "rfr_admin_jwt";

type TradeShowRow = {
  id: number;
  name: string;
  summary: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  event_url: string | null;
  source_page_url: string | null;
  exhibitor_hints: string[];
};

export default function PartnersTheRobotGuildPage() {
  const [token, setToken] = useState(() =>
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem(TOKEN_KEY) || "" : ""
  );
  const [tokenInput, setTokenInput] = useState("");
  const [rows, setRows] = useState<TradeShowRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Record<string, unknown> | null>(null);

  const authHeaders = useCallback((): Record<string, string> => {
    const t = token.trim();
    if (!t) return {};
    return { Authorization: `Bearer ${t}` };
  }, [token]);

  const saveToken = useCallback(() => {
    const t = tokenInput.trim();
    setToken(t);
    if (typeof sessionStorage !== "undefined") {
      if (t) sessionStorage.setItem(TOKEN_KEY, t);
      else sessionStorage.removeItem(TOKEN_KEY);
    }
    setTokenInput("");
  }, [tokenInput]);

  const load = useCallback(async () => {
    if (!token.trim()) {
      setRows([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${getApiBase()}/api/admin/partners/the-robot-guild/trade-shows`, {
        headers: { ...authHeaders() },
      });
      if (r.status === 401 || r.status === 403) {
        setError("Unauthorized — check that your JWT is an admin session (ADMIN_EMAILS).");
        setRows([]);
        return;
      }
      if (!r.ok) {
        setError(`Failed to load (${r.status}).`);
        setRows([]);
        return;
      }
      setRows((await r.json()) as TradeShowRow[]);
    } catch {
      setError("Network error loading trade shows.");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = async () => {
    if (!token.trim()) {
      setError("Save an admin token first.");
      return;
    }
    setRefreshing(true);
    setError(null);
    try {
      const r = await fetch(`${getApiBase()}/api/admin/partners/the-robot-guild/trade-shows/refresh`, {
        method: "POST",
        headers: { ...authHeaders() },
      });
      if (!r.ok) {
        setError(`Refresh failed (${r.status}).`);
        setLastRefresh(null);
        return;
      }
      const body = (await r.json()) as Record<string, unknown>;
      setLastRefresh(body);
      await load();
    } catch {
      setError("Network error during refresh.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <SiteShell>
      <MarketingPageLayout
        kicker="Partners"
        title="The Robot Guild"
        subtitle="Trade shows and expos with a robotics / automation angle — scraped for your partner GTM."
      >
        <div className="space-y-6 max-w-4xl">
          <p className="text-sm text-gray-700">
            Partner site:{" "}
            <a href="https://www.therobotguild.com/" className="font-semibold text-emerald-800 hover:underline" target="_blank" rel="noreferrer">
              The Robot Guild
            </a>{" "}
            connects robotics companies to brand moments. This workspace lists robot-relevant shows (JSON-LD Event data
            where available) plus <strong>best-effort OEM hints</strong> from page text — not official exhibitor APIs.
          </p>

          <Card className="border-gray-200 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Admin access</CardTitle>
              <CardDescription>
                Paste a Supabase (or legacy) JWT for an account in <code className="text-xs">ADMIN_EMAILS</code>. Stored
                only in this browser tab.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col sm:flex-row gap-2 sm:items-end">
              <div className="flex-1 space-y-1">
                <label className="text-xs font-semibold text-gray-700" htmlFor="admin-jwt">
                  Bearer token
                </label>
                <Input
                  id="admin-jwt"
                  type="password"
                  autoComplete="off"
                  placeholder="eyJ…"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                />
              </div>
              <Button type="button" onClick={saveToken} className="shrink-0">
                Save token
              </Button>
            </CardContent>
          </Card>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" variant="outline" onClick={() => void load()} disabled={loading || !token.trim()}>
              {loading ? "Loading…" : "Reload list"}
            </Button>
            <Button type="button" onClick={() => void refresh()} disabled={refreshing || !token.trim()}>
              {refreshing ? "Scraping…" : "Run scraper refresh"}
            </Button>
            <Link href="/admin" className="text-sm text-gray-600 hover:text-gray-900 hover:underline">
              ← Admin home
            </Link>
          </div>

          {error ? (
            <p className="text-sm text-red-800 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
          ) : null}

          {lastRefresh ? (
            <p className="text-xs text-gray-600 font-mono bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
              Last refresh: {JSON.stringify(lastRefresh)}
            </p>
          ) : null}

          <div className="space-y-4">
            {rows.length === 0 && !loading ? (
              <p className="text-sm text-gray-600">
                No rows yet. Save a token and run <strong>Run scraper refresh</strong> (requires outbound HTTP from the
                API to seed URLs; override with <code className="text-xs">TRADE_SHOW_SEED_URLS</code> on the server).
              </p>
            ) : null}
            {rows.map((r) => (
              <Card key={r.id} className="border-gray-200 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">{r.name}</CardTitle>
                  <CardDescription className="space-y-1">
                    {[r.start_date, r.end_date].filter(Boolean).join(" → ") || "Dates TBD"}
                    {r.location ? ` · ${r.location}` : ""}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-gray-800">
                  {r.summary ? <p className="leading-snug line-clamp-4">{r.summary}</p> : null}
                  <div>
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">OEM / brand hints</p>
                    <p className="text-gray-700">
                      {r.exhibitor_hints?.length
                        ? r.exhibitor_hints.join(", ")
                        : "None inferred from page text."}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                    {r.event_url ? (
                      <a href={r.event_url} className="text-emerald-800 font-semibold hover:underline" target="_blank" rel="noreferrer">
                        Event link
                      </a>
                    ) : null}
                    {r.source_page_url ? (
                      <a
                        href={r.source_page_url}
                        className="text-gray-600 hover:underline"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Source page
                      </a>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </MarketingPageLayout>
    </SiteShell>
  );
}
