import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Database, DownloadCloud, Play, RefreshCw, Shield, UploadCloud } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

type AdminStats = {
  totals?: { companies?: number; signals?: number; scored?: number };
  pipeline_value?: number;
  conversion_metrics?: { hot_rate?: number; avg_score?: number };
  by_industry?: Array<{ industry?: string; count?: number }>;
  by_signal_type?: Array<{ signal_type?: string; count?: number }>;
  recent_companies?: Array<{ id?: number; name?: string; industry?: string; source?: string; created_at?: string }>;
};

type ScrapeTargets = {
  summary?: Record<string, number>;
  targets?: Array<{ url?: string; label?: string; scraper?: string; industries?: string[]; signal_types?: string[]; active?: boolean }>;
};

type AdminMe = { email?: string; is_admin?: boolean };

const INDUSTRIES = ["", "Logistics", "Hospitality", "Healthcare", "Food Service", "Automotive & Manufacturing"];
const SCRAPERS = ["all", "job_board", "hotel_dir", "rss_feed", "news", "serp", "logistics", "score_recalc"];

function formatNumber(value?: number) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

function AdminCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
      <p className="text-[10px] font-normal uppercase tracking-[0.18em] text-white/32">{label}</p>
      <p className="mt-2 font-mono text-2xl font-bold text-white" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
      {sub && <p className="mt-1 text-xs text-white/35">{sub}</p>}
    </div>
  );
}

export default function Admin() {
  const api = getApiBase();
  const { session, loading: authLoading } = useAuth();
  const [me, setMe] = useState<AdminMe | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [targets, setTargets] = useState<ScrapeTargets | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [urls, setUrls] = useState("");
  const [urlIndustry, setUrlIndustry] = useState("");
  const [scrapeNow, setScrapeNow] = useState(false);
  const [companyJson, setCompanyJson] = useState('[{"name":"Example Robotics Buyer","website":"https://example.com","industry":"Logistics"}]');
  const [triggerScraper, setTriggerScraper] = useState("news");
  const [triggerIndustry, setTriggerIndustry] = useState("");

  const headers = useMemo(() => ({
    "Content-Type": "application/json",
    ...authHeader(session?.access_token),
  }), [session?.access_token]);

  const adminFetch = useCallback((path: string, init: RequestInit = {}) => (
    fetch(`${api}${path}`, liveFetchInit({
      ...init,
      headers: {
        ...headers,
        ...((init.headers as Record<string, string>) || {}),
      },
    }))
  ), [api, headers]);

  const loadAdmin = useCallback(async () => {
    if (!session?.access_token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const meRes = await adminFetch("/api/user/me");
      if (!meRes.ok) throw new Error(meRes.status === 401 ? "Please sign in again." : "Could not verify admin access.");
      const meData = await meRes.json() as AdminMe;
      setMe(meData);
      if (!meData.is_admin) {
        setStats(null);
        setTargets(null);
        return;
      }

      const [statsRes, targetsRes] = await Promise.all([
        adminFetch("/api/admin/stats"),
        adminFetch("/api/admin/scrape/targets"),
      ]);
      if (!statsRes.ok) throw new Error(`Stats failed with ${statsRes.status}`);
      if (!targetsRes.ok) throw new Error(`Targets failed with ${targetsRes.status}`);
      setStats(await statsRes.json());
      setTargets(await targetsRes.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin load failed.");
    } finally {
      setLoading(false);
    }
  }, [adminFetch, session?.access_token]);

  useEffect(() => {
    if (!authLoading) void loadAdmin();
  }, [authLoading, loadAdmin]);

  async function importUrls(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const payload = {
        urls: urls.split(/\s+/).map((url) => url.trim()).filter(Boolean),
        industry: urlIndustry || undefined,
        scrape_now: scrapeNow,
      };
      const res = await adminFetch("/api/admin/import/urls", { method: "POST", body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "URL import failed.");
      setMessage(`Imported ${data.added || 0} URLs; skipped ${data.skipped || 0}.`);
      setUrls("");
      await loadAdmin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "URL import failed.");
    }
  }

  async function importCompanies(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const companies = JSON.parse(companyJson);
      const res = await adminFetch("/api/admin/import/companies", { method: "POST", body: JSON.stringify({ companies }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Company import failed.");
      setMessage(`Imported ${data.added || 0} companies; skipped ${data.skipped || 0}.`);
      await loadAdmin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Company import failed. Check the JSON format.");
    }
  }

  async function triggerScrape(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const res = await adminFetch("/api/admin/scrape/trigger", {
        method: "POST",
        body: JSON.stringify({ scraper: triggerScraper, industry: triggerIndustry || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Scraper trigger failed.");
      setMessage(data.status === "queued" ? `${triggerScraper} scraper queued.` : data.reason || "Scraper request accepted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scraper trigger failed.");
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen" style={{ background: "#0d0520" }}>
        <Header />
        <main className="mx-auto max-w-6xl px-6 pt-28 text-white/50">Loading admin...</main>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen" style={{ background: "#0d0520" }}>
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <Shield className="mx-auto mb-4 h-7 w-7" style={{ color: "#FFB000" }} />
          <h1 className="text-2xl font-bold text-white">Admin sign in required</h1>
          <p className="mt-3 text-sm text-white/45">Sign in with an admin email to manage ReadyForRobots.</p>
          <Link href="/login" className="mt-6 inline-flex rounded-xl border px-5 py-3 text-sm font-bold" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  if (me && !me.is_admin) {
    return (
      <div className="min-h-screen" style={{ background: "#0d0520" }}>
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <AlertTriangle className="mx-auto mb-4 h-7 w-7 text-red-300" />
          <h1 className="text-2xl font-bold text-white">Admin access required</h1>
          <p className="mt-3 text-sm text-white/45">{me.email || "This account"} is signed in but is not listed in `ADMIN_EMAILS`.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "#0d0520" }}>
      <Header />
      <main className="mx-auto max-w-6xl px-6 pb-20 pt-28">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-2 text-[10px] font-normal uppercase tracking-[0.22em]" style={{ color: "#FFB000" }}>Admin console</p>
            <h1 className="text-4xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>ReadyForRobots Ops</h1>
            <p className="mt-3 text-sm text-white/42">Manage data, scrapers, and operational health for the live service.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => void loadAdmin()} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/60">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
            <a href={`${api}/api/docs`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-xs font-bold" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
              <Database className="h-3.5 w-3.5" /> API docs
            </a>
          </div>
        </div>

        {message && <div className="mb-4 rounded-xl border border-emerald-400/20 bg-emerald-400/8 px-4 py-3 text-sm text-emerald-200">{message}</div>}
        {error && <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/8 px-4 py-3 text-sm text-red-200">{error}</div>}

        <section className="mb-8 grid grid-cols-1 gap-3 md:grid-cols-4">
          <AdminCard label="Companies" value={formatNumber(stats?.totals?.companies)} />
          <AdminCard label="Signals" value={formatNumber(stats?.totals?.signals)} />
          <AdminCard label="Scored" value={formatNumber(stats?.totals?.scored)} />
          <AdminCard label="Avg Score" value={stats?.conversion_metrics?.avg_score?.toFixed(1) || "—"} sub={`${stats?.conversion_metrics?.hot_rate ?? "—"}% hot rate`} />
        </section>

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#a78bfa" }}>Industry mix</p>
            <div className="space-y-2">
              {(stats?.by_industry || []).slice(0, 8).map((item) => (
                <div key={item.industry} className="flex items-center justify-between text-sm">
                  <span className="text-white/62">{item.industry || "Unknown"}</span>
                  <span className="font-mono text-white/35">{formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#03DAC5" }}>Signal types</p>
            <div className="space-y-2">
              {(stats?.by_signal_type || []).slice(0, 8).map((item) => (
                <div key={item.signal_type} className="flex items-center justify-between text-sm">
                  <span className="text-white/62">{(item.signal_type || "unknown").replace(/_/g, " ")}</span>
                  <span className="font-mono text-white/35">{formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <form onSubmit={importUrls} className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <UploadCloud className="mb-4 h-5 w-5" style={{ color: "#FFB000" }} />
            <p className="text-sm font-bold text-white">Import URLs</p>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://example.com/feed&#10;https://example.com/news" className="mt-3 min-h-28 w-full rounded-xl border border-white/10 bg-white/[0.035] px-3 py-2 text-xs text-white outline-none placeholder:text-white/25" />
            <select value={urlIndustry} onChange={(e) => setUrlIndustry(e.target.value)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#160d2a] px-3 py-2 text-xs text-white/70">
              {INDUSTRIES.map((item) => <option key={item} value={item}>{item || "Auto-detect industry"}</option>)}
            </select>
            <label className="mt-3 flex items-center gap-2 text-xs text-white/45">
              <input type="checkbox" checked={scrapeNow} onChange={(e) => setScrapeNow(e.target.checked)} className="accent-violet-500" />
              Scrape now
            </label>
            <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
              Import URLs
            </button>
          </form>

          <form onSubmit={importCompanies} className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <DownloadCloud className="mb-4 h-5 w-5" style={{ color: "#a78bfa" }} />
            <p className="text-sm font-bold text-white">Import Companies</p>
            <textarea value={companyJson} onChange={(e) => setCompanyJson(e.target.value)} className="mt-3 min-h-40 w-full rounded-xl border border-white/10 bg-white/[0.035] px-3 py-2 font-mono text-[11px] text-white outline-none" />
            <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-violet-300/45 px-4 py-2.5 text-xs font-bold text-violet-200">
              Import Companies
            </button>
          </form>

          <form onSubmit={triggerScrape} className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <Play className="mb-4 h-5 w-5" style={{ color: "#03DAC5" }} />
            <p className="text-sm font-bold text-white">Trigger Scraper</p>
            <select value={triggerScraper} onChange={(e) => setTriggerScraper(e.target.value)} className="mt-3 w-full rounded-xl border border-white/10 bg-[#160d2a] px-3 py-2 text-xs text-white/70">
              {SCRAPERS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={triggerIndustry} onChange={(e) => setTriggerIndustry(e.target.value)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#160d2a] px-3 py-2 text-xs text-white/70">
              {INDUSTRIES.map((item) => <option key={item} value={item}>{item || "All industries"}</option>)}
            </select>
            <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-teal-300/45 px-4 py-2.5 text-xs font-bold text-teal-200">
              Queue Scraper
            </button>
          </form>
        </section>

        <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.2fr]">
          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Recent companies</p>
            <div className="space-y-3">
              {(stats?.recent_companies || []).map((company) => (
                <div key={company.id} className="rounded-xl border border-white/7 px-3 py-2" style={{ background: "rgba(13,5,32,0.45)" }}>
                  <p className="text-sm font-semibold text-white/80">{company.name}</p>
                  <p className="mt-1 text-[11px] text-white/35">{company.industry} · {company.source || "unknown"}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#a78bfa" }}>Scrape targets</p>
            <div className="mb-4 flex flex-wrap gap-2">
              {Object.entries(targets?.summary || {}).map(([key, value]) => (
                <span key={key} className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] text-white/45">{key}: {value}</span>
              ))}
            </div>
            <div className="max-h-[460px] space-y-2 overflow-y-auto pr-1">
              {(targets?.targets || []).slice(0, 40).map((target, index) => (
                <div key={`${target.url}-${index}`} className="rounded-xl border border-white/7 px-3 py-2" style={{ background: "rgba(13,5,32,0.45)" }}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-xs font-semibold text-white/75">{target.label || target.url}</p>
                    <span className="shrink-0 rounded-full border border-white/10 px-2 py-0.5 text-[9px] text-white/35">{target.scraper}</span>
                  </div>
                  <p className="mt-1 break-all text-[11px] text-white/28">{target.url}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
