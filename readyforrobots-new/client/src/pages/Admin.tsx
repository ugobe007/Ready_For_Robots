import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, BarChart3, Bot, CheckCircle2, Clock3, Database, DownloadCloud, ExternalLink, Mail, Play, RefreshCw, Shield, UploadCloud, Users } from "lucide-react";
import { Link } from "wouter";
import AdminNav from "@/components/AdminNav";
import Header from "@/components/Header";
import ScoutActionBar from "@/components/ScoutActionBar";
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

type AdminUserStats = {
  total_users?: number;
  active_users?: number;
  total_saved?: number;
  total_reports?: number;
  total_lists?: number;
  waitlist_signups?: number;
  newsletter_subscribers?: number;
};

type AdminUser = {
  id?: string;
  email?: string;
  created_at?: string;
  last_active?: string;
  saved_count?: number;
  reports_count?: number;
  lists_count?: number;
};

type AdminActivity = {
  type?: string;
  label?: string;
  actor?: string;
  detail?: string;
  created_at?: string;
};

type SiteAnalytics = {
  site_visits?: number;
  total_calculations?: number;
  robot_searches?: number;
  email_captures?: number;
  conversion_rate?: number;
  avg_payback_months?: number;
  hot_count?: number;
  warm_count?: number;
  cold_count?: number;
  new_companies?: number;
  new_signals?: number;
  insights?: {
    hottest_trend?: string;
    opportunity?: string;
    action_item?: string;
  };
};

type WorkflowAction = {
  id?: string;
  source?: string;
  title?: string;
  description?: string;
  status?: string;
  state?: string;
  priority?: string;
  requires_approval?: boolean;
  owner?: string;
  entity?: string;
  next_action_label?: string;
  next_action_url?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
};

type WorkflowSummary = {
  counts?: Record<string, number>;
  by_source?: Record<string, number>;
  items?: WorkflowAction[];
  errors?: Array<{ source?: string; detail?: string }>;
};

type ScrapeTargets = {
  summary?: Record<string, number>;
  targets?: Array<{ url?: string; label?: string; scraper?: string; industries?: string[]; signal_types?: string[]; active?: boolean }>;
};

type AdminMe = { email?: string; is_admin?: boolean };

type CalProspect = {
  company_id?: number;
  company_name?: string;
  website?: string;
  industry?: string;
  score?: number;
  tier?: string;
  crm_account_id?: string;
  contact_email?: string;
  default_cc?: string;
  account_type?: "buyer" | "vendor";
  outreach_stage?: string;
  outreach_sent_at?: string;
  has_draft?: boolean;
  draft_preview?: string;
  draft_full?: string;
  email_delivery_status?: string;
};

type CalDraftStatus = {
  summary?: {
    total?: number;
    hot?: number;
    warm?: number;
    drafted?: number;
    pending_draft?: number;
    sent?: number;
  };
  prospects?: CalProspect[];
};

const INDUSTRIES = ["", "Logistics", "Hospitality", "Healthcare", "Food Service", "Automotive & Manufacturing"];
const SCRAPERS = ["all", "job_board", "hotel_dir", "rss_feed", "news", "serp", "logistics", "score_recalc"];
const TIME_RANGES = [
  { label: "7D", value: "7d" },
  { label: "30D", value: "30d" },
  { label: "90D", value: "90d" },
  { label: "All", value: "all" },
] as const;

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

function formatDate(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(date);
}

function activityColor(type?: string) {
  if (type === "saved_company") return "#FFB000";
  if (type === "ai_report") return "#a78bfa";
  if (type === "newsletter_subscriber") return "#03DAC5";
  if (type === "waitlist_signup") return "#34d399";
  return "rgba(255,255,255,0.42)";
}

function stateLabel(state?: string) {
  return (state || "unknown").replace(/_/g, " ");
}

function stateStyle(state?: string) {
  if (state === "failed") return { color: "#fecaca", borderColor: "rgba(248,113,113,0.35)", background: "rgba(248,113,113,0.08)" };
  if (state === "needs_approval") return { color: "#fde68a", borderColor: "rgba(251,191,36,0.38)", background: "rgba(251,191,36,0.08)" };
  if (state === "queued") return { color: "#bfdbfe", borderColor: "rgba(96,165,250,0.35)", background: "rgba(96,165,250,0.08)" };
  if (state === "in_process") return { color: "#99f6e4", borderColor: "rgba(45,212,191,0.35)", background: "rgba(45,212,191,0.08)" };
  if (state === "completed") return { color: "#bbf7d0", borderColor: "rgba(74,222,128,0.35)", background: "rgba(74,222,128,0.08)" };
  return { color: "rgba(255,255,255,0.58)", borderColor: "rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.04)" };
}

function sourceLabel(source?: string) {
  return (source || "workflow").replace(/_/g, " ");
}

export default function Admin() {
  const api = getApiBase();
  const { session, loading: authLoading } = useAuth();
  const [me, setMe] = useState<AdminMe | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [userStats, setUserStats] = useState<AdminUserStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [activity, setActivity] = useState<AdminActivity[]>([]);
  const [analytics, setAnalytics] = useState<SiteAnalytics | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowSummary | null>(null);
  const [targets, setTargets] = useState<ScrapeTargets | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState<(typeof TIME_RANGES)[number]["value"]>("30d");
  const [urls, setUrls] = useState("");
  const [urlIndustry, setUrlIndustry] = useState("");
  const [scrapeNow, setScrapeNow] = useState(false);
  const [companyJson, setCompanyJson] = useState('[{"name":"Example Robotics Buyer","website":"https://example.com","industry":"Logistics"}]');
  const [triggerScraper, setTriggerScraper] = useState("news");
  const [triggerIndustry, setTriggerIndustry] = useState("");
  const [actionBusy, setActionBusy] = useState<"urls" | "companies" | "scraper" | "cache" | "reindex" | "export" | "cal-draft" | "cal-send" | "cal-send-one" | "scout-activate" | "scout-send" | "cleanup" | "">("");
  const [sendConfirm, setSendConfirm] = useState<false | "bulk" | "scout-send" | string>(false);
  const [scoutStatus, setScoutStatus] = useState<{ total_prospects?: number; activated?: number; drafted?: number; sent?: number; pending_approval?: number } | null>(null);
  const [calStatus, setCalStatus] = useState<CalDraftStatus | null>(null);
  const [calExpanded, setCalExpanded] = useState<number | null>(null);
  const [calFilter, setCalFilter] = useState<"all" | "pending" | "drafted" | "sent">("all");
  // Reply notification settings
  const [replyForwardEmail, setReplyForwardEmail] = useState("");
  const [replySettingBusy, setReplySettingBusy] = useState(false);
  const [replySettingSaved, setReplySettingSaved] = useState(false);

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
        setUserStats(null);
        setUsers([]);
        setActivity([]);
        setAnalytics(null);
        setWorkflow(null);
        setTargets(null);
        return;
      }

      // Fire workflow + all supplemental fetches in parallel — removes one sequential round-trip.
      setLoading(false);
      const all = await Promise.allSettled([
        adminFetch("/api/admin/workflow/actions?limit=40"),
        adminFetch("/api/admin/stats"),
        adminFetch("/api/admin/users/stats"),
        adminFetch("/api/admin/users"),
        adminFetch("/api/admin/activity?limit=40"),
        adminFetch(`/api/analytics?range=${timeRange}`),
        adminFetch("/api/admin/scrape/targets"),
      ]);
      const [workflowRes, statsRes, userStatsRes, usersRes, activityRes, analyticsRes, targetsRes] = all.map(
        (result) => (result.status === "fulfilled" ? result.value : null),
      );
      if (workflowRes?.ok) setWorkflow(await workflowRes.json());
      if (statsRes?.ok) setStats(await statsRes.json());
      if (userStatsRes?.ok) setUserStats(await userStatsRes.json());
      if (usersRes?.ok) {
        const usersData = await usersRes.json() as { users?: AdminUser[] };
        setUsers(usersData.users || []);
      }
      if (activityRes?.ok) {
        const activityData = await activityRes.json() as { activity?: AdminActivity[] };
        setActivity(activityData.activity || []);
      }
      if (analyticsRes?.ok) setAnalytics(await analyticsRes.json());
      if (targetsRes?.ok) setTargets(await targetsRes.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin load failed.");
    } finally {
      setLoading(false);
    }
  }, [adminFetch, session?.access_token, timeRange]);

  const loadCalStatus = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch("/api/admin/cal/draft-status");
      if (res.ok) setCalStatus(await res.json() as CalDraftStatus);
    } catch { /* silent — status loads separately */ }
  }, [adminFetch, session?.access_token]);

  const loadReplySettings = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch("/api/user/settings");
      if (res.ok) {
        const d = await res.json() as { reply_forward_email?: string | null };
        setReplyForwardEmail(d.reply_forward_email || "");
      }
    } catch { /* advisory */ }
  }, [adminFetch, session?.access_token]);

  const saveReplySettings = async () => {
    if (!session?.access_token) return;
    setReplySettingBusy(true);
    try {
      const res = await adminFetch("/api/user/settings", {
        method: "PUT",
        body: JSON.stringify({ reply_forward_email: replyForwardEmail || null, reply_forwarding_enabled: true }),
      });
      if (!res.ok) throw new Error(await res.text());
      setReplySettingSaved(true);
      setTimeout(() => setReplySettingSaved(false), 3000);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    } finally {
      setReplySettingBusy(false);
    }
  };

  useEffect(() => {
    if (!authLoading) void loadAdmin();
  }, [authLoading, loadAdmin]);

  useEffect(() => {
    if (!authLoading && session?.access_token) {
      void loadCalStatus();
      void loadReplySettings();
    }
  }, [authLoading, loadCalStatus, loadReplySettings, session?.access_token]);

  async function importUrls(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    setActionBusy("urls");
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
    } finally {
      setActionBusy("");
    }
  }

  async function importCompanies(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    setActionBusy("companies");
    try {
      const companies = JSON.parse(companyJson);
      const res = await adminFetch("/api/admin/import/companies", { method: "POST", body: JSON.stringify({ companies }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Company import failed.");
      setMessage(`Imported ${data.added || 0} companies; skipped ${data.skipped || 0}.`);
      await loadAdmin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Company import failed. Check the JSON format.");
    } finally {
      setActionBusy("");
    }
  }

  async function triggerScrape(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage("");
    setError("");
    setActionBusy("scraper");
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
    } finally {
      setActionBusy("");
    }
  }

  async function runSystemAction(kind: "cache" | "reindex" | "cleanup") {
    setMessage("");
    setError("");
    setActionBusy(kind);
    try {
      const path = kind === "cache"
        ? "/api/admin/system/cache/clear"
        : kind === "cleanup"
        ? "/api/admin/system/cleanup-junk-leads"
        : "/api/admin/system/reindex";
      const res = await adminFetch(path, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error((data as { detail?: string; message?: string })?.detail || (data as { detail?: string; message?: string })?.message || `${kind} action failed.`);
      setMessage(
        kind === "cache" ? "Cache cleared." :
        kind === "cleanup" ? `Junk-lead cleanup queued (task ${((data as { task_id?: string }).task_id ?? "").slice(0, 8)}...).` :
        "Database reindex queued."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : `${kind} action failed.`);
    } finally {
      setActionBusy("");
    }
  }

  async function runCalBulkDraft(regenerate = false) {
    setMessage("");
    setError("");
    setActionBusy("cal-draft");
    try {
      const res = await adminFetch("/api/admin/cal/bulk-draft", {
        method: "POST",
        body: JSON.stringify({ regenerate }),
      });
      const data = await res.json().catch(() => ({})) as { drafted?: number; skipped?: number; errors?: unknown[] };
      if (!res.ok) throw new Error((data as { detail?: string }).detail || "Bulk draft failed.");
      setMessage(`Cal drafted ${data.drafted ?? 0} emails · ${data.skipped ?? 0} already had drafts · ${data.errors?.length ?? 0} errors.`);
      await loadCalStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk draft failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalBulkSend(tierFilter: "all" | "HOT" | "WARM" = "all", limit = 1000) {
    setMessage("");
    setError("");
    setSendConfirm(false);
    setActionBusy("cal-send");
    let totalSent = 0;
    let totalErrors = 0;
    // Loop in batches of 100 until nothing left to send
    try {
      while (true) {
        const res = await adminFetch("/api/admin/cal/bulk-send", {
          method: "POST",
          body: JSON.stringify({ limit: 100, tier_filter: tierFilter, dry_run: false }),
        });
        const data = await res.json().catch(() => ({})) as { sent?: number; skipped_no_draft?: number; skipped_already_sent?: number; errors?: unknown[] };
        if (!res.ok) throw new Error((data as { detail?: string }).detail || "Send failed.");
        const batchSent = data.sent ?? 0;
        totalSent += batchSent;
        totalErrors += data.errors?.length ?? 0;
        // Stop when no more emails went out in this batch
        if (batchSent === 0) break;
        // Stop if we've hit the overall limit
        if (totalSent >= limit) break;
      }
      setMessage(`Cal sent ${totalSent} emails · ${totalErrors} errors.`);
      await loadCalStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalSendOne(crmAccountId: string, toEmail: string) {
    setMessage("");
    setError("");
    setSendConfirm(false);
    setActionBusy("cal-send-one");
    try {
      const res = await adminFetch("/api/admin/cal/send-one", {
        method: "POST",
        body: JSON.stringify({ crm_account_id: crmAccountId }),
      });
      const data = await res.json().catch(() => ({})) as { sent?: boolean; to?: string };
      if (!res.ok) throw new Error((data as { detail?: string }).detail || "Send failed.");
      setMessage(`Sent to ${data.to ?? toEmail}.`);
      await loadCalStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed.");
    } finally {
      setActionBusy("");
    }
  }

  const loadScoutStatus = useCallback(async () => {
    const res = await adminFetch("/api/admin/scout/status");
    if (res.ok) setScoutStatus(await res.json() as typeof scoutStatus);
  }, [adminFetch]);

  useEffect(() => {
    if (!authLoading && session?.access_token) void loadScoutStatus();
  }, [authLoading, loadScoutStatus, session?.access_token]);

  async function runScoutBulkActivate() {
    setMessage(""); setError(""); setActionBusy("scout-activate");
    try {
      const res = await adminFetch("/api/admin/scout/bulk-activate", { method: "POST", body: JSON.stringify({ limit: 200, tier_filter: "all", dry_run: false }) });
      const data = await res.json().catch(() => ({})) as { activated?: number; skipped?: number; errors?: number };
      if (!res.ok) throw new Error((data as { detail?: string }).detail || "Activation failed.");
      setMessage(`SCOUT activated ${data.activated ?? 0} prospects · ${data.skipped ?? 0} already active · ${data.errors ?? 0} errors.`);
      await loadScoutStatus();
    } catch (err) { setError(err instanceof Error ? err.message : "Activation failed."); }
    finally { setActionBusy(""); }
  }

  async function runScoutBulkSend() {
    setMessage(""); setError(""); setSendConfirm(false); setActionBusy("scout-send");
    let totalSent = 0;
    let totalErrors = 0;
    try {
      while (true) {
        const res = await adminFetch("/api/admin/scout/bulk-send", { method: "POST", body: JSON.stringify({ limit: 100, dry_run: false }) });
        const data = await res.json().catch(() => ({})) as { sent?: number; skipped?: number; errors?: number };
        if (!res.ok) throw new Error((data as { detail?: string }).detail || "Send failed.");
        const batchSent = data.sent ?? 0;
        totalSent += batchSent;
        totalErrors += data.errors ?? 0;
        if (batchSent === 0) break;
      }
      setMessage(`SCOUT sent ${totalSent} emails · ${totalErrors} errors.`);
      await loadScoutStatus();
    } catch (err) { setError(err instanceof Error ? err.message : "Send failed."); }
    finally { setActionBusy(""); }
  }

  async function exportAllData() {
    setMessage("");
    setError("");
    setActionBusy("export");
    try {
      const res = await adminFetch("/api/admin/export/all");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || "Export failed.");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `readyforrobots-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setMessage("Export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setActionBusy("");
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
      <main className="mx-auto max-w-[1500px] px-4 pb-20 pt-20 lg:px-6">
        <AdminNav />

        {/* ── SCOUT action bar — top of page, always visible ── */}
        <div className="mb-4 rounded-2xl border border-white/8 overflow-hidden" style={{ background: "rgba(13,5,32,0.6)" }}>
          <ScoutActionBar
            accessToken={session?.access_token}
            stats={calStatus?.summary ? {
              total: calStatus.summary.total ?? 0,
              drafted: calStatus.summary.drafted ?? 0,
              sent: calStatus.summary.sent ?? 0,
              opened: (calStatus.summary as Record<string, number>).opened ?? 0,
              clicked: (calStatus.summary as Record<string, number>).clicked ?? 0,
              replied: (calStatus.summary as Record<string, number>).replied ?? 0,
            } : null}
            busy={actionBusy === "cal-draft" ? "draft" : actionBusy === "cal-send" ? "send" : null}
            onRunScout={() => void runCalBulkDraft(false)}
            onActivateScout={() => setSendConfirm("bulk")}
            onTrackScout={() => void loadCalStatus()}
          />
        </div>

        {/* ── Reply notification settings ── */}
        <div className="mb-4 rounded-2xl border border-white/8 px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-4" style={{ background: "rgba(255,255,255,0.025)" }}>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] mb-0.5" style={{ color: "#a78bfa" }}>Reply notifications</p>
            <p className="text-[11px] text-white/40">
              When a prospect replies to Cal, forward a copy to this email immediately.
              {" "}<span className="text-white/25">Replies are also stored in the Sales Console.</span>
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
            <input
              type="email"
              value={replyForwardEmail}
              onChange={(e) => setReplyForwardEmail(e.target.value)}
              placeholder="ugobe07@gmail.com"
              className="flex-1 sm:w-64 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25 focus:border-violet-400/60"
            />
            <button
              type="button"
              disabled={replySettingBusy}
              onClick={() => void saveReplySettings()}
              className="shrink-0 px-4 py-2 rounded-xl text-sm font-bold border transition-all disabled:opacity-50"
              style={
                replySettingSaved
                  ? { background: "rgba(52,211,153,0.12)", borderColor: "rgba(52,211,153,0.35)", color: "#6ee7b7" }
                  : { background: "rgba(124,58,237,0.12)", borderColor: "rgba(124,58,237,0.35)", color: "#c4b5fd" }
              }
            >
              {replySettingBusy ? "Saving…" : replySettingSaved ? "✓ Saved" : "Save"}
            </button>
          </div>
        </div>

        <div className="mb-4 flex flex-col gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#a78bfa" }}>Operations</p>
            <h1 className="text-xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>ReadyForRobots Command Center</h1>
            <p className="mt-0.5 max-w-md text-[11px] text-white/35">
              Same operating surface as the live prospects pipeline: compact, signal-first, and action-oriented.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/prospects" className="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-xs font-bold" style={{ color: "#FFB000", borderColor: "rgba(255,176,0,0.45)" }}>
              Prospects <ExternalLink className="h-3.5 w-3.5" />
            </Link>
            <div className="mr-1 flex rounded-xl border border-white/10 p-1">
              {TIME_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className="rounded-lg px-3 py-1.5 text-[11px] font-bold transition"
                  style={{
                    color: timeRange === range.value ? "#0d0520" : "rgba(255,255,255,0.52)",
                    background: timeRange === range.value ? "#FFB000" : "transparent",
                  }}
                >
                  {range.label}
                </button>
              ))}
            </div>
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

        <section className="mb-8">
          <div className="mb-3 flex items-center gap-2">
            <Users className="h-4 w-4" style={{ color: "#FFB000" }} />
            <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Users and accounts</p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <AdminCard label="Users" value={formatNumber(userStats?.total_users)} sub={`${formatNumber(userStats?.active_users)} active in 7 days`} />
            <AdminCard label="Saved Companies" value={formatNumber(userStats?.total_saved)} sub="Buyer accounts tracking leads" />
            <AdminCard label="Reports" value={formatNumber(userStats?.total_reports)} sub={`${formatNumber(userStats?.total_lists)} saved lists`} />
            <AdminCard label="Captured Leads" value={formatNumber((userStats?.waitlist_signups || 0) + (userStats?.newsletter_subscribers || 0))} sub={`${formatNumber(userStats?.waitlist_signups)} SCOUT · ${formatNumber(userStats?.newsletter_subscribers)} newsletter`} />
          </div>
        </section>

        <section id="workflow" className="mb-8 scroll-mt-28 rounded-2xl border border-white/8 p-5" style={{ background: "linear-gradient(135deg, rgba(255,176,0,0.07), rgba(3,218,197,0.035))" }}>
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Bot className="h-4 w-4" style={{ color: "#03DAC5" }} />
                <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#03DAC5" }}>AI workflow command center</p>
              </div>
              <h2 className="text-2xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>Agent actions and operating queue</h2>
              <p className="mt-2 max-w-3xl text-xs leading-relaxed text-white/45">
                One view for Cal/Max sales actions, buyer outreach, supply outreach, lead research, and user notifications.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/sales-console" className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold" style={{ color: "#FFB000", borderColor: "rgba(255,176,0,0.45)" }}>
                Sales Console <ExternalLink className="h-3 w-3" />
              </Link>
              <Link href="/supply-pipeline" className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold" style={{ color: "#03DAC5", borderColor: "rgba(3,218,197,0.45)" }}>
                Supply Pipeline <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </div>

          <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-6">
            <AdminCard label="Total" value={formatNumber(workflow?.counts?.total)} sub="tracked actions" />
            <AdminCard label="Approve" value={formatNumber(workflow?.counts?.needs_approval)} sub="waiting on you" />
            <AdminCard label="Queued" value={formatNumber(workflow?.counts?.queued)} sub="ready to run" />
            <AdminCard label="Running" value={formatNumber(workflow?.counts?.in_process)} sub="in process" />
            <AdminCard label="Review" value={formatNumber(workflow?.counts?.needs_review)} sub="new intelligence" />
            <AdminCard label="Failed" value={formatNumber(workflow?.counts?.failed)} sub="needs attention" />
          </div>

          {workflow?.errors?.length ? (
            <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/8 px-4 py-3 text-xs text-red-200">
              Some workflow sources could not load: {workflow.errors.map((item) => sourceLabel(item.source)).join(", ")}
            </div>
          ) : null}

          <div className="mb-4 flex flex-wrap gap-2">
            {Object.entries(workflow?.by_source || {}).map(([source, count]) => (
              <span key={source} className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] capitalize text-white/45">
                {sourceLabel(source)}: {formatNumber(count)}
              </span>
            ))}
          </div>

          <div className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
            {(workflow?.items?.length ? workflow.items : [{ id: "empty", title: "No agent work is currently queued", description: "Cal, Max, outreach, and research activity will appear here as work is created.", state: "completed" }]).slice(0, 60).map((item) => {
              const style = stateStyle(item.state);
              return (
                <div key={`${item.source}-${item.id}`} className="rounded-xl border border-white/8 px-4 py-3" style={{ background: "rgba(13,5,32,0.55)" }}>
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] capitalize" style={style}>
                          {item.state === "completed" ? <CheckCircle2 className="h-3 w-3" /> : <Clock3 className="h-3 w-3" />}
                          {stateLabel(item.state)}
                        </span>
                        <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] capitalize text-white/38">{sourceLabel(item.source)}</span>
                        {item.requires_approval && <span className="rounded-full border border-amber-300/30 px-2 py-0.5 text-[10px] text-amber-100">approval required</span>}
                        {item.priority === "high" && <span className="rounded-full border border-red-300/25 px-2 py-0.5 text-[10px] text-red-100">high priority</span>}
                      </div>
                      <p className="truncate text-sm font-bold text-white/82">{item.title || "Untitled workflow action"}</p>
                      <p className="mt-1 text-xs text-white/42">{item.entity || "ReadyForRobots"} · {formatDate(item.updated_at || item.created_at)}</p>
                      {item.description && <p className="mt-2 text-xs leading-relaxed text-white/52">{item.description}</p>}
                    </div>
                    {item.next_action_url && (
                      <Link href={item.next_action_url} className="shrink-0 rounded-xl border border-white/10 px-3 py-2 text-center text-xs font-bold text-white/65">
                        {item.next_action_label || "Open"}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── SCOUT Automation ─────────────────────────────────────────────── */}
        <section id="scout-automation" className="mb-8 scroll-mt-28 rounded-2xl border border-white/8 p-5" style={{ background: "linear-gradient(135deg, rgba(3,218,197,0.07), rgba(167,139,250,0.035))" }}>
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Bot className="h-4 w-4" style={{ color: "#03DAC5" }} />
                <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#03DAC5" }}>SCOUT Automation</p>
              </div>
              <h2 className="text-2xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>Fully automated prospect outreach</h2>
              <p className="mt-1 max-w-2xl text-xs leading-relaxed text-white/45">
                Use the buttons at the top of this page to run the full workflow.
              </p>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <AdminCard label="Total Prospects" value={formatNumber(scoutStatus?.total_prospects)} sub="HOT + WARM" />
            <AdminCard label="Activated" value={formatNumber(scoutStatus?.activated)} sub="SCOUT running" />
            <AdminCard label="Drafted" value={formatNumber(scoutStatus?.drafted)} sub="ready to send" />
            <AdminCard label="Pending Approval" value={formatNumber(scoutStatus?.pending_approval)} sub="awaiting review" />
            <AdminCard label="Sent" value={formatNumber(scoutStatus?.sent)} sub="emails delivered" />
          </div>
        </section>

        {/* ── Cal Outreach: draft status for 166 HOT+WARM prospects ── */}
        <section id="cal-outreach" className="mb-8 scroll-mt-28 rounded-2xl border border-white/8 p-5" style={{ background: "linear-gradient(135deg, rgba(167,139,250,0.07), rgba(255,176,0,0.035))" }}>
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Mail className="h-4 w-4" style={{ color: "#a78bfa" }} />
                <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#a78bfa" }}>Cal outreach</p>
              </div>
              <h2 className="text-2xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                HOT + WARM prospect drafts
              </h2>
              <p className="mt-1 max-w-2xl text-xs leading-relaxed text-white/45">
                Cal's template voice — no LLM. Defaults to <span className="font-mono text-white/65">sales@domain</span> (TO) and <span className="font-mono text-white/65">marketing@domain</span> (CC) when no contact is on file.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex rounded-xl border border-white/10 p-1">
                {(["all", "pending", "drafted", "sent"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setCalFilter(f)}
                    className="rounded-lg px-3 py-1.5 text-[11px] font-bold capitalize transition"
                    style={{
                      color: calFilter === f ? "#0d0520" : "rgba(255,255,255,0.45)",
                      background: calFilter === f ? "#a78bfa" : "transparent",
                    }}
                  >
                    {f}
                  </button>
                ))}
              </div>
              <button
                onClick={() => void loadCalStatus()}
                disabled={!!actionBusy}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2 text-xs font-bold text-white/55 disabled:opacity-40"
              >
                <RefreshCw className="h-3 w-3" /> Refresh
              </button>
              <button
                onClick={() => void runCalBulkDraft(false)}
                disabled={!!actionBusy}
                className="inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-xs font-bold disabled:opacity-40"
                style={{ color: "#a78bfa", borderColor: "rgba(167,139,250,0.5)" }}
              >
                {actionBusy === "cal-draft" ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Drafting…</> : <><Mail className="h-3.5 w-3.5" /> Draft pending</>}
              </button>
              <button
                onClick={() => void runCalBulkDraft(true)}
                disabled={!!actionBusy}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2 text-xs font-bold text-white/45 disabled:opacity-40"
                title="Regenerate all drafts including existing ones"
              >
                Regenerate all
              </button>
              <button
                onClick={() => setSendConfirm("bulk")}
                disabled={!!actionBusy || !calStatus?.summary?.drafted}
                className="inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-xs font-bold disabled:opacity-40"
                style={{ color: "#FFB000", borderColor: "rgba(255,176,0,0.55)", background: "rgba(255,176,0,0.08)" }}
                title={`Send all ${calStatus?.summary?.drafted ?? 0} drafted emails`}
              >
                {actionBusy === "cal-send" ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Sending…</> : <><Play className="h-3.5 w-3.5" /> Send drafted ({calStatus?.summary?.drafted ?? 0})</>}
              </button>
            </div>
          </div>

          {/* ── Bulk-send confirm modal ── */}
          {sendConfirm === "bulk" && (
            <div className="mb-5 rounded-xl border border-amber-400/30 bg-amber-400/8 p-4">
              <p className="mb-1 text-sm font-bold text-amber-200">Confirm bulk send</p>
              <p className="mb-3 text-xs text-amber-100/60">
                This will send up to <strong>{calStatus?.summary?.drafted ?? 0}</strong> emails via Resend — one per drafted prospect that hasn't been contacted yet. This action cannot be undone.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => void runCalBulkSend("all", 50)}
                  className="rounded-xl border border-amber-400/50 px-4 py-2 text-xs font-bold text-amber-200"
                >
                  Yes — send all now
                </button>
                <button onClick={() => setSendConfirm(false)} className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/45">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Summary pills */}
          <div className="mb-5 grid grid-cols-3 gap-3 md:grid-cols-6 lg:grid-cols-9">
            <AdminCard label="Total" value={formatNumber(calStatus?.summary?.total)} sub="HOT + WARM" />
            <AdminCard label="HOT" value={formatNumber(calStatus?.summary?.hot)} sub="highest priority" />
            <AdminCard label="WARM" value={formatNumber(calStatus?.summary?.warm)} sub="strong signals" />
            <AdminCard label="Drafted" value={formatNumber(calStatus?.summary?.drafted)} sub="ready to send" />
            <AdminCard label="Pending" value={formatNumber(calStatus?.summary?.pending_draft)} sub="need drafts" />
            <AdminCard label="Sent" value={formatNumber(calStatus?.summary?.sent)} sub="emails out" />
            <AdminCard label="Opened" value={formatNumber((calStatus?.summary as Record<string, number> | undefined)?.opened)} sub="email opened" />
            <AdminCard label="Clicked" value={formatNumber((calStatus?.summary as Record<string, number> | undefined)?.clicked)} sub="link clicked" />
            <AdminCard label="Replied" value={formatNumber((calStatus?.summary as Record<string, number> | undefined)?.replied)} sub="replied to Cal" />
          </div>

          {/* Prospect table */}
          <div className="max-h-[600px] overflow-y-auto pr-1">
            {!calStatus ? (
              <p className="py-6 text-center text-xs text-white/35">Loading prospect draft status…</p>
            ) : (calStatus.prospects ?? []).filter((p) => {
              if (calFilter === "pending") return !p.has_draft;
              if (calFilter === "drafted") return p.has_draft && !p.outreach_sent_at;
              if (calFilter === "sent") return !!p.outreach_sent_at;
              return true;
            }).length === 0 ? (
              <p className="py-6 text-center text-xs text-white/35">No prospects match this filter.</p>
            ) : (
              <div className="space-y-1.5">
                {/* Column headers */}
                <div className="grid grid-cols-[2fr_1fr_1.5fr_1fr_0.8fr_0.8fr] gap-3 border-b border-white/7 pb-2 text-[10px] uppercase tracking-widest text-white/28">
                  <span>Company</span>
                  <span>Tier / Score</span>
                  <span>Contact</span>
                  <span>Stage</span>
                  <span>Draft</span>
                  <span>Delivery</span>
                </div>
                {(calStatus.prospects ?? [])
                  .filter((p) => {
                    if (calFilter === "pending") return !p.has_draft;
                    if (calFilter === "drafted") return p.has_draft && !p.outreach_sent_at;
                    if (calFilter === "sent") return !!p.outreach_sent_at;
                    return true;
                  })
                  .map((prospect, idx) => {
                    const isOpen = calExpanded === idx;
                    const tierColor = prospect.tier === "HOT" ? "#FFB000" : prospect.tier === "WARM" ? "#03DAC5" : "rgba(255,255,255,0.35)";
                    return (
                      <div key={`${prospect.company_id}-${idx}`} className="rounded-xl border border-white/7" style={{ background: "rgba(13,5,32,0.55)" }}>
                        <button
                          className="grid w-full grid-cols-[2fr_1fr_1.5fr_1fr_0.8fr_0.8fr] gap-3 px-4 py-3 text-left"
                          onClick={() => setCalExpanded(isOpen ? null : idx)}
                        >
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-white/85">{prospect.company_name || "—"}</p>
                            <div className="mt-0.5 flex items-center gap-1.5 flex-wrap">
                              <span className="text-[10px] text-white/35">{prospect.industry}</span>
                              <button
                                type="button"
                                title="Toggle buyer / vendor"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (!prospect.crm_account_id) return;
                                  const next = prospect.account_type === "vendor" ? "buyer" : "vendor";
                                  void adminFetch(`/api/crm/accounts/${prospect.crm_account_id}`, {
                                    method: "PATCH",
                                    body: JSON.stringify({ account_type: next }),
                                  }).then(() => void loadCalStatus());
                                }}
                                className="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider border transition-colors"
                                style={
                                  prospect.account_type === "vendor"
                                    ? { background: "rgba(167,139,250,0.12)", borderColor: "rgba(167,139,250,0.3)", color: "#a78bfa" }
                                    : { background: "rgba(52,211,153,0.08)", borderColor: "rgba(52,211,153,0.2)", color: "#6ee7b7" }
                                }
                              >
                                {prospect.account_type === "vendor" ? "vendor" : "buyer"}
                              </button>
                            </div>
                          </div>
                          <div>
                            <span className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold" style={{ color: tierColor, background: `${tierColor}18`, border: `1px solid ${tierColor}35` }}>
                              {prospect.tier}
                            </span>
                            <p className="mt-1 font-mono text-[10px] text-white/35">{prospect.score?.toFixed(0)}</p>
                          </div>
                          <div className="min-w-0">
                            <p className="truncate font-mono text-[11px] text-white/55">{prospect.contact_email || <span className="text-white/25 not-italic">no contact</span>}</p>
                            {prospect.default_cc && <p className="truncate font-mono text-[10px] text-white/28">cc: {prospect.default_cc}</p>}
                          </div>
                          <div>
                            <span className="text-[11px] text-white/45">
                              {prospect.outreach_sent_at ? "sent" : prospect.outreach_stage?.replace(/_/g, " ") || "—"}
                            </span>
                            {prospect.outreach_sent_at && <p className="mt-0.5 text-[10px] text-white/28">{formatDate(prospect.outreach_sent_at)}</p>}
                          </div>
                          <div className="flex items-center">
                            {prospect.has_draft ? (
                              <CheckCircle2 className="h-4 w-4" style={{ color: "#34d399" }} />
                            ) : (
                              <Clock3 className="h-4 w-4 text-white/20" />
                            )}
                          </div>
                          <div className="flex items-center">
                            {(prospect as Record<string, unknown>).email_delivery_status === "opened" || (prospect as Record<string, unknown>).email_delivery_status === "clicked" ? (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(52,211,153,0.12)", color: "#34d399" }}>
                                {String((prospect as Record<string, unknown>).email_delivery_status)}
                              </span>
                            ) : (prospect as Record<string, unknown>).email_delivery_status === "bounced" ? (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(248,113,113,0.12)", color: "#f87171" }}>bounced</span>
                            ) : (prospect as Record<string, unknown>).email_delivery_status === "sent" || (prospect as Record<string, unknown>).email_delivery_status === "delivered" ? (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(96,165,250,0.1)", color: "#93c5fd" }}>sent</span>
                            ) : (
                              <span className="text-[9px] text-white/20">—</span>
                            )}
                          </div>
                        </button>
                        {isOpen && (
                          <div className="border-t border-white/7 px-4 pb-4 pt-3">
                            {prospect.has_draft ? (
                              <>
                                <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-white/28">Cal draft</p>
                                <pre className="whitespace-pre-wrap rounded-xl border border-white/8 bg-white/[0.025] px-4 py-3 font-mono text-[11px] leading-relaxed text-white/65">
                                  {prospect.draft_full}
                                </pre>
                                <div className="mt-3 flex flex-wrap items-center gap-3">
                                  {prospect.contact_email && (
                                    <div className="flex flex-wrap gap-2 text-[10px] text-white/38">
                                      <span>TO: <span className="font-mono text-white/55">{prospect.contact_email}</span></span>
                                      {prospect.default_cc && <span>CC: <span className="font-mono text-white/55">{prospect.default_cc}</span></span>}
                                    </div>
                                  )}
                                  <div className="ml-auto flex gap-2">
                                    {prospect.outreach_sent_at ? (
                                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/25 px-2.5 py-1 text-[10px] text-emerald-300">
                                        <CheckCircle2 className="h-3 w-3" /> Sent {formatDate(prospect.outreach_sent_at)}
                                      </span>
                                    ) : sendConfirm === prospect.crm_account_id ? (
                                      <>
                                        <span className="text-[10px] text-amber-200/70">Send to {prospect.contact_email}?</span>
                                        <button
                                          onClick={() => prospect.crm_account_id && prospect.contact_email && void runCalSendOne(prospect.crm_account_id, prospect.contact_email)}
                                          disabled={!!actionBusy}
                                          className="rounded-xl border border-amber-400/40 px-3 py-1.5 text-[10px] font-bold text-amber-200 disabled:opacity-40"
                                        >
                                          {actionBusy === "cal-send-one" ? "Sending…" : "Yes, send"}
                                        </button>
                                        <button onClick={() => setSendConfirm(false)} className="rounded-xl border border-white/10 px-3 py-1.5 text-[10px] text-white/40">Cancel</button>
                                      </>
                                    ) : (
                                      <button
                                        onClick={() => setSendConfirm(prospect.crm_account_id ?? false)}
                                        disabled={!!actionBusy || !prospect.contact_email}
                                        className="inline-flex items-center gap-1 rounded-xl border px-3 py-1.5 text-[10px] font-bold disabled:opacity-40"
                                        style={{ color: "#FFB000", borderColor: "rgba(255,176,0,0.40)" }}
                                      >
                                        <Mail className="h-3 w-3" /> Send this email
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </>
                            ) : (
                              <p className="text-xs text-white/38">No draft yet. Click <strong className="text-white/55">Draft pending</strong> to generate.</p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </section>

        <section className="mb-8">
          <div className="mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4" style={{ color: "#03DAC5" }} />
            <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#03DAC5" }}>Site metrics</p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <AdminCard label="Site Visits" value={formatNumber(analytics?.site_visits)} sub={`Range: ${timeRange.toUpperCase()}`} />
            <AdminCard label="ROI Runs" value={formatNumber(analytics?.total_calculations)} sub={`${formatNumber(analytics?.email_captures)} emails captured`} />
            <AdminCard label="Robot Searches" value={formatNumber(analytics?.robot_searches)} />
            <AdminCard label="Conversion" value={`${analytics?.conversion_rate ?? 0}%`} sub="Email capture rate" />
            <AdminCard label="Lead Mix" value={formatNumber((analytics?.hot_count || 0) + (analytics?.warm_count || 0))} sub={`${formatNumber(analytics?.hot_count)} hot · ${formatNumber(analytics?.warm_count)} warm`} />
          </div>
        </section>

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <div className="mb-4 flex items-center justify-between gap-3">
              <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#a78bfa" }}>Recent users</p>
              <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] text-white/35">{formatNumber(users.length)} shown</span>
            </div>
            <div className="max-h-[380px] overflow-y-auto pr-1">
              <div className="grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] gap-3 border-b border-white/7 pb-2 text-[10px] uppercase tracking-widest text-white/28">
                <span>User</span>
                <span>Saved</span>
                <span>Reports</span>
                <span>Last active</span>
              </div>
              {(users.length ? users : [{ email: "No users yet" }]).slice(0, 30).map((user, index) => (
                <div key={user.id || `${user.email}-${index}`} className="grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] gap-3 border-b border-white/6 py-3 text-xs">
                  <div className="min-w-0">
                    <p className="truncate text-white/72">{user.email || "Unknown user"}</p>
                    <p className="mt-1 truncate text-[10px] text-white/28">{user.id || "—"}</p>
                  </div>
                  <span className="font-mono text-white/45">{formatNumber(user.saved_count)}</span>
                  <span className="font-mono text-white/45">{formatNumber(user.reports_count)}</span>
                  <span className="text-white/35">{formatDate(user.last_active || user.created_at)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <div className="mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4" style={{ color: "#FFB000" }} />
              <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Recent activity</p>
            </div>
            <div className="max-h-[380px] space-y-2 overflow-y-auto pr-1">
              {(activity.length ? activity : [{ label: "No recent activity yet", detail: "User saves, reports, signups, and newsletter subscribers will appear here." }]).map((item, index) => (
                <div key={`${item.type}-${item.created_at}-${index}`} className="rounded-xl border border-white/7 px-3 py-2" style={{ background: "rgba(13,5,32,0.45)" }}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold text-white/75">{item.label}</p>
                    <span className="shrink-0 text-[10px] text-white/28">{formatDate(item.created_at)}</span>
                  </div>
                  <p className="mt-1 truncate text-[11px]" style={{ color: activityColor(item.type) }}>{item.actor || "ReadyForRobots"}</p>
                  <p className="mt-1 break-words text-[11px] text-white/35">{item.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {analytics?.insights && (
          <section className="mb-8 rounded-2xl border border-white/8 p-5" style={{ background: "linear-gradient(135deg, rgba(255,176,0,0.08), rgba(3,218,197,0.04))" }}>
            <p className="mb-3 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Operator notes</p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {[analytics.insights.hottest_trend, analytics.insights.opportunity, analytics.insights.action_item].filter(Boolean).map((item) => (
                <p key={item} className="rounded-xl border border-white/8 px-3 py-3 text-xs leading-relaxed text-white/55" style={{ background: "rgba(13,5,32,0.38)" }}>{item}</p>
              ))}
            </div>
          </section>
        )}

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-2 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>System controls</p>
            <p className="mb-4 text-xs leading-relaxed text-white/42">
              These actions use the same authenticated admin session, so failures are shown here instead of opening unauthenticated tabs.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void runSystemAction("cache")}
                disabled={!!actionBusy}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65 disabled:opacity-50"
              >
                {actionBusy === "cache" ? "Clearing..." : "Clear cache"}
              </button>
              <button
                type="button"
                onClick={() => void runSystemAction("reindex")}
                disabled={!!actionBusy}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65 disabled:opacity-50"
              >
                {actionBusy === "reindex" ? "Reindexing..." : "Reindex database"}
              </button>
              <button
                type="button"
                onClick={() => void runSystemAction("cleanup")}
                disabled={!!actionBusy}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65 disabled:opacity-50"
              >
                {actionBusy === "cleanup" ? "Queueing..." : "Cleanup junk leads"}
              </button>
              <button
                type="button"
                onClick={() => void exportAllData()}
                disabled={!!actionBusy}
                className="rounded-xl border px-4 py-2 text-xs font-bold disabled:opacity-50"
                style={{ color: "#03DAC5", borderColor: "rgba(3,218,197,0.45)" }}
              >
                {actionBusy === "export" ? "Exporting..." : "Export all data"}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <p className="mb-2 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#03DAC5" }}>Operational shortcuts</p>
            <p className="mb-4 text-xs leading-relaxed text-white/42">
              Admin remains the single ops home. Use these links for the dedicated work consoles.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link href="/crm" className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65">
                Buyer CRM
              </Link>
              <Link href="/admin/prospects" className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65">
                Prospects
              </Link>
              <Link href="/sales-console" className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65">
                Sales Console
              </Link>
              <Link href="/supply-pipeline" className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65">
                Supply Pipeline
              </Link>
              <Link href="/marketplace" className="rounded-xl border border-white/10 px-4 py-2 text-xs font-bold text-white/65">
                Marketplace
              </Link>
            </div>
          </div>
        </section>

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
            <button disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold disabled:opacity-50" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
              {actionBusy === "urls" ? "Importing..." : "Import URLs"}
            </button>
          </form>

          <form onSubmit={importCompanies} className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
            <DownloadCloud className="mb-4 h-5 w-5" style={{ color: "#a78bfa" }} />
            <p className="text-sm font-bold text-white">Import Companies</p>
            <textarea value={companyJson} onChange={(e) => setCompanyJson(e.target.value)} className="mt-3 min-h-40 w-full rounded-xl border border-white/10 bg-white/[0.035] px-3 py-2 font-mono text-[11px] text-white outline-none" />
            <button disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-violet-300/45 px-4 py-2.5 text-xs font-bold text-violet-200 disabled:opacity-50">
              {actionBusy === "companies" ? "Importing..." : "Import Companies"}
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
            <button disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-teal-300/45 px-4 py-2.5 text-xs font-bold text-teal-200 disabled:opacity-50">
              {actionBusy === "scraper" ? "Queueing..." : "Queue Scraper"}
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
