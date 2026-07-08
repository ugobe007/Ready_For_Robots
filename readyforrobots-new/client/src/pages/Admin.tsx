import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, AlertTriangle, Bot, CheckCircle2, Clock3, Database, DownloadCloud, ExternalLink, Mail, Play, RefreshCw, Shield, UploadCloud, Users } from "lucide-react";
import { Link, useLocation } from "wouter";
import DailyBriefPanel, { type DailyBriefData } from "@/components/DailyBriefPanel";
import CalEmailPreview from "@/components/admin/CalEmailPreview";
import SupabaseInlineLink from "@/components/admin/SupabaseInlineLink";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import CalWorkflowPanel, { type CalWorkflowMetrics } from "@/components/admin/CalWorkflowPanel";
import SiteMetricsPanel from "@/components/admin/SiteMetricsPanel";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { useAdminSnapshotSync } from "@/hooks/useAdminSnapshotSync";
import {
  readLocalAdminSnapshot,
  mergeSectionIntoSnapshot,
  writeLocalAdminSnapshot,
  snapshotToApplied,
  type AdminSectionName,
} from "@/lib/adminSnapshot";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";
import { scrollToAdminSection } from "@/lib/adminNavigation";

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
  total_signals?: number;
  new_companies?: number;
  new_signals?: number;
  signup_funnel?: {
    available?: boolean;
    signup_start?: number;
    signup_complete?: number;
    first_save?: number;
    start_to_complete_rate?: number;
    complete_to_save_rate?: number;
    start_to_save_rate?: number;
  };
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
  contact_email_source?: "crm" | "inferred" | null;
  inferred_contact_email?: string;
  outreach_domain?: string;
  default_cc?: string;
  account_type?: "buyer" | "vendor";
  outreach_pipeline?: string;
  robot_company_id?: number;
  semantic_summary?: string;
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
    unsent_drafted?: number;
    sendable?: number;
    approved?: number;
    needs_approval?: number;
    no_email?: number;
    pending_draft?: number;
    sent?: number;
    opened?: number;
    clicked?: number;
    replied?: number;
    buyers?: number;
    vendors?: number;
    scope?: string;
  };
  prospects?: CalProspect[];
  stale?: boolean;
  bootstrap_required?: boolean;
  bootstrap_message?: string;
};

type OperatorDashboard = {
  cal_queue?: CalDraftStatus["summary"];
  buyer_vendor?: { buyers?: number; vendors?: number; scope?: string };
  sales_opportunities?: { total?: number };
  workflow?: WorkflowSummary;
  autopilot?: {
    enabled?: boolean;
    runtime_toggle_available?: boolean;
    template_version?: string;
  };
};

type ScoutStatus = {
  total_prospects?: number;
  activated?: number;
  drafted?: number;
  sent?: number;
  pending_approval?: number;
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

// ── Robot Benchmark + LinkedIn Panel ──────────────────────────────────────
function RobotBenchmarkPanel({ api, headers }: {
  api: string;
  headers: Record<string, string | undefined>;
  adminFetch?: (path: string, init?: RequestInit) => Promise<Response>;
}) {
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState("");
  const [linkedInPost, setLinkedInPost] = useState<{ post_text: string; linkedin_share_url: string; char_count: number } | null>(null);
  const [postOpen, setPostOpen] = useState(false);

  const safeHeaders = Object.fromEntries(
    Object.entries(headers).filter(([, v]) => v !== undefined)
  ) as Record<string, string>;

  const runScrape = async () => {
    setScraping(true); setScrapeMsg("");
    try {
      const res = await fetch(`${api}/api/humanoid/scrape-all`, { method: "POST", headers: safeHeaders });
      const d = await res.json().catch(() => ({})) as { scraped?: number };
      setScrapeMsg(`Scraped ${d.scraped ?? 0} robots — scores updated.`);
    } catch (_e) { setScrapeMsg("Scrape failed."); }
    finally { setScraping(false); }
  };

  const generatePost = async () => {
    try {
      const res = await fetch(`${api}/api/humanoid/linkedin-post`, { headers: safeHeaders });
      if (res.ok) { setLinkedInPost(await res.json() as { post_text: string; linkedin_share_url: string; char_count: number }); setPostOpen(true); }
    } catch (_e) { /* silent */ }
  };

  return (
    <div className="rounded-2xl border border-gray-200 p-5 mb-3" style={{ background: "rgba(5,150,105,0.05)" }}>
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-0.5" style={{ color: "#10b981" }}>Robot Benchmark Index</p>
          <p className="text-[12px] font-medium text-gray-700">Scrape fresh specs, update scores, generate report &amp; LinkedIn post.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={scraping}
            onClick={() => void runScrape()}
            className="inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-[11px] font-bold disabled:opacity-50"
            style={{ borderColor: "rgba(167,139,250,0.35)", color: "#047857" }}
          >
            {scraping ? "Scraping…" : "Scrape all robots"}
          </button>
          <button
            type="button"
            onClick={() => void generatePost()}
            className="inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-[11px] font-bold"
            style={{ borderColor: "rgba(52,211,153,0.35)", color: "#047857" }}
          >
            Generate LinkedIn post
          </button>
          <a
            href="/robots"
            className="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 px-3 py-1.5 text-[11px] font-bold text-gray-800"
          >
            View index →
          </a>
        </div>
      </div>
      {scrapeMsg && <p className="text-[11px] text-gray-500 mt-1">{scrapeMsg}</p>}

      {/* LinkedIn post modal */}
      {postOpen && linkedInPost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setPostOpen(false)}>
          <div
            className="w-full max-w-xl rounded-2xl border border-gray-200 bg-white p-6 max-h-[80vh] overflow-y-auto shadow-xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <p className="font-bold text-gray-900">LinkedIn Post</p>
              <span className="text-[10px] text-gray-400">{linkedInPost.char_count} chars</span>
            </div>
            <pre className="whitespace-pre-wrap text-[12px] text-gray-600 leading-relaxed mb-5 font-sans">{linkedInPost.post_text}</pre>
            <div className="flex gap-2 flex-wrap">
              <button
                type="button"
                onClick={() => void navigator.clipboard.writeText(linkedInPost.post_text)}
                className="rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-600"
              >
                Copy text
              </button>
              <a
                href={linkedInPost.linkedin_share_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl px-4 py-2 text-xs font-bold"
                style={{ background: "rgba(10,102,194,0.2)", border: "1px solid rgba(10,102,194,0.4)", color: "#60a5fa" }}
              >
                Open LinkedIn Share →
              </a>
              <button type="button" onClick={() => setPostOpen(false)} className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-bold text-gray-700">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AdminCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="admin-card">
      <p className="admin-card-label">{label}</p>
      <p className="admin-card-value" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
      {sub && <p className="admin-card-sub">{sub}</p>}
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
  if (type === "ai_report") return "#10b981";
  if (type === "newsletter_subscriber") return "#059669";
  if (type === "waitlist_signup") return "#34d399";
  return "#6b7280";
}

function stateLabel(state?: string) {
  return (state || "unknown").replace(/_/g, " ");
}

function stateStyle(state?: string) {
  if (state === "failed") return { color: "#b91c1c", borderColor: "#fecaca", background: "#fef2f2" };
  if (state === "needs_approval") return { color: "#b45309", borderColor: "#fde68a", background: "#fffbeb" };
  if (state === "queued") return { color: "#1d4ed8", borderColor: "#bfdbfe", background: "#eff6ff" };
  if (state === "in_process") return { color: "#047857", borderColor: "#a7f3d0", background: "#ecfdf5" };
  if (state === "completed") return { color: "#15803d", borderColor: "#bbf7d0", background: "#f0fdf4" };
  return { color: "#374151", borderColor: "#e5e7eb", background: "#f9fafb" };
}

function sourceLabel(source?: string) {
  return (source || "workflow").replace(/_/g, " ");
}

export default function Admin() {
  const api = getApiBase();
  const [, setLocation] = useLocation();
  const { session, loading: authLoading } = useAuth();
  const [localSnapshot] = useState(() => readLocalAdminSnapshot());
  const initialApplied = useMemo(() => snapshotToApplied(localSnapshot), [localSnapshot]);
  const [me, setMe] = useState<AdminMe | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(initialApplied.stats as AdminStats | null);
  const [userStats, setUserStats] = useState<AdminUserStats | null>(initialApplied.userStats as AdminUserStats | null);
  const [users, setUsers] = useState<AdminUser[]>(initialApplied.users as AdminUser[]);
  const [activity, setActivity] = useState<AdminActivity[]>(initialApplied.activity as AdminActivity[]);
  const [analytics, setAnalytics] = useState<SiteAnalytics | null>(initialApplied.analytics as SiteAnalytics | null);
  const [workflow, setWorkflow] = useState<WorkflowSummary | null>(initialApplied.workflow as WorkflowSummary | null);
  const [targets, setTargets] = useState<ScrapeTargets | null>(initialApplied.targets as ScrapeTargets | null);
  const [meLoading, setMeLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState<(typeof TIME_RANGES)[number]["value"]>("30d");
  const [urls, setUrls] = useState("");
  const [urlIndustry, setUrlIndustry] = useState("");
  const [scrapeNow, setScrapeNow] = useState(false);
  const [companyJson, setCompanyJson] = useState('[{"name":"Example Robotics Buyer","website":"https://example.com","industry":"Logistics"}]');
  const [triggerScraper, setTriggerScraper] = useState("news");
  const [triggerIndustry, setTriggerIndustry] = useState("");
  const [actionBusy, setActionBusy] = useState<"urls" | "companies" | "scraper" | "cache" | "reindex" | "export" | "cal-draft" | "cal-send" | "cal-send-one" | "cal-reinfer" | "cal-save" | "cal-run" | "supply-draft" | "supply-send" | "scout-activate" | "scout-send" | "cleanup" | "">("");
  const [sendConfirm, setSendConfirm] = useState<false | "bulk" | "scout-send" | string>(false);
  const [scoutStatus, setScoutStatus] = useState<ScoutStatus | null>(
    initialApplied.scoutStatus as ScoutStatus | null,
  );
  const [calStatus, setCalStatus] = useState<CalDraftStatus | null>(initialApplied.calStatus as CalDraftStatus | null);
  const [calExpanded, setCalExpanded] = useState<number | null>(null);
  const [calSelectedIdx, setCalSelectedIdx] = useState<number | null>(null);
  const [calFilter, setCalFilter] = useState<"all" | "pending" | "drafted" | "sent">("all");
  const [calStatusError, setCalStatusError] = useState("");
  const [calStatusLoading, setCalStatusLoading] = useState(false);
  const [bulkSendSkipVerify, setBulkSendSkipVerify] = useState(false);
  // Reply notification settings
  const [replyForwardEmail, setReplyForwardEmail] = useState("");
  const [replySettingBusy, setReplySettingBusy] = useState(false);
  const [replySettingSaved, setReplySettingSaved] = useState(false);
  const [dailyBrief, setDailyBrief] = useState<DailyBriefData | null>(initialApplied.dailyBrief);
  const [dailyBriefLoading, setDailyBriefLoading] = useState(!initialApplied.dailyBrief);
  const [draftBodies, setDraftBodies] = useState<Record<string, string>>({});
  const [draftBodyLoading, setDraftBodyLoading] = useState<string | null>(null);
  const [draftLoadErrors, setDraftLoadErrors] = useState<Record<string, string>>({});
  const [draftContactEmails, setDraftContactEmails] = useState<Record<string, string>>({});
  const [calAutonomy, setCalAutonomy] = useState<{
    enabled?: boolean;
    env_enabled?: boolean;
    runtime_override?: boolean | null;
    runtime_toggle_available?: boolean;
    scheduled_on_worker?: boolean;
    review_email?: string | null;
    send_limit?: number;
    every_hours?: number;
    template_version?: string;
  } | null>(null);
  const [supplyAutonomy, setSupplyAutonomy] = useState<{
    enabled?: boolean;
    review_email?: string | null;
    send_limit?: number;
    min_score?: number;
    every_hours?: number;
    template_version?: string;
  } | null>(null);
  const [salesOppTotal, setSalesOppTotal] = useState<number | null>(null);
  const [operatorDashboard, setOperatorDashboard] = useState<OperatorDashboard | null>(null);

  const headers = useMemo(() => ({
    "Content-Type": "application/json",
    ...authHeader(session?.access_token),
  }), [session?.access_token]);

  const adminFetch = useCallback(async (path: string, init: RequestInit = {}) => {
    // Always attach a *fresh* token — an in-memory session can go stale between
    // Supabase auto-refresh cycles and cause spurious 401s (e.g. draft retry).
    const token = await getFreshAccessToken(session?.access_token);
    return fetch(`${api}${path}`, liveFetchInit({
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...authHeader(token),
        ...((init.headers as Record<string, string>) || {}),
      },
    }));
  }, [api, session?.access_token]);

  const applySectionData = useCallback((section: AdminSectionName, data: unknown) => {
    switch (section) {
      case "daily_brief":
        setDailyBrief(data as DailyBriefData);
        setDailyBriefLoading(false);
        break;
      case "cal":
        setCalStatus(data as CalDraftStatus);
        break;
      case "stats":
        setStats(data as AdminStats);
        break;
      case "scout":
        setScoutStatus(data as ScoutStatus);
        break;
      case "user_stats":
        setUserStats(data as AdminUserStats);
        break;
      case "users": {
        const usersData = data as { users?: AdminUser[] };
        setUsers(usersData.users || []);
        break;
      }
      case "activity": {
        const activityData = data as { activity?: AdminActivity[] };
        setActivity(activityData.activity || []);
        break;
      }
      case "workflow":
        setWorkflow(data as WorkflowSummary);
        break;
      case "targets":
        setTargets(data as ScrapeTargets);
        break;
      case "analytics":
        setAnalytics(data as SiteAnalytics);
        break;
      default:
        break;
    }
  }, []);

  const applySnapshotToState = useCallback((snap: ReturnType<typeof readLocalAdminSnapshot>) => {
    const applied = snapshotToApplied(snap);
    if (applied.dailyBrief) {
      setDailyBrief(applied.dailyBrief);
      setDailyBriefLoading(false);
    }
    if (applied.calStatus) setCalStatus(applied.calStatus as CalDraftStatus);
    if (applied.stats) setStats(applied.stats as AdminStats);
    if (applied.scoutStatus) setScoutStatus(applied.scoutStatus as ScoutStatus);
    if (applied.userStats) setUserStats(applied.userStats as AdminUserStats);
    if (applied.workflow) setWorkflow(applied.workflow as WorkflowSummary);
    if (applied.targets) setTargets(applied.targets as ScrapeTargets);
    if (applied.analytics) setAnalytics(applied.analytics as SiteAnalytics);
    if (applied.activity.length) setActivity(applied.activity as AdminActivity[]);
    if (applied.users.length) setUsers(applied.users as AdminUser[]);
  }, []);

  const handleSyncComplete = useCallback(() => {
    setDailyBriefLoading(false);
  }, []);

  const { syncingSection, sync: syncAdminSnapshot, refreshSection } = useAdminSnapshotSync(
    adminFetch,
    {
      sessionToken: session?.access_token,
      timeRange,
      onSection: applySectionData,
      onSnapshotMerged: applySnapshotToState,
      onSyncComplete: handleSyncComplete,
    },
  );

  const adminLoadedForToken = useRef<string | null>(null);

  const loadAdmin = useCallback(async () => {
    if (!session?.access_token) {
      setMeLoading(false);
      return;
    }
    setMeLoading(true);
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
        setDailyBrief(null);
        return;
      }
      void syncAdminSnapshot();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin load failed.");
    } finally {
      setMeLoading(false);
    }
  }, [adminFetch, syncAdminSnapshot, session?.access_token]);

  const loadCalStatus = useCallback(async () => {
    if (!session?.access_token) return;
    setCalStatusLoading(true);
    setCalStatusError("");
    try {
      const cached = readLocalAdminSnapshot()?.sections?.cal?.data as CalDraftStatus | undefined;
      if (cached?.summary?.total) {
        setCalStatus((prev) => ({
          summary: cached.summary,
          prospects: prev?.prospects ?? cached.prospects ?? [],
        }));
      }

      const sumRes = await adminFetch("/api/admin/cal/queue-summary");
      const sumData = (await sumRes.json().catch(() => ({}))) as CalDraftStatus & { detail?: string };
      if (sumRes.ok && sumData.summary) {
        setCalStatus((prev) => ({ ...sumData, prospects: prev?.prospects ?? [] }));
      } else if (!sumRes.ok && sumRes.status !== 502) {
        setCalStatusError(sumData.detail || `Cal queue failed (${sumRes.status})`);
      } else if (!sumRes.ok && !cached?.summary) {
        setCalStatusError("Cal queue failed to load (502) — retrying from cache…");
      }

      const listRes = await adminFetch(
        "/api/admin/cal/draft-status?include_prospects=true&prospect_limit=50&fast_summary=true",
      );
      const listData = (await listRes.json().catch(() => ({}))) as CalDraftStatus & { detail?: string };
      if (listRes.ok && (listData.prospects?.length || listData.summary)) {
        setCalStatus(listData);
        if (listData.bootstrap_required) {
          setCalStatusError(listData.bootstrap_message || "Cal outreach team not initialized.");
        } else {
          setCalStatusError("");
        }
        const current = readLocalAdminSnapshot() ?? { sections: {} };
        writeLocalAdminSnapshot(
          mergeSectionIntoSnapshot(current, "cal", new Date().toISOString(), listData),
        );
      } else if (!listRes.ok && sumRes.ok) {
        setCalStatusError(
          listRes.status === 502
            ? "Lead list timed out — counts above are valid. Click a lead after Refresh."
            : "Lead list still loading — counts above are valid.",
        );
      } else if (listData.stale && sumRes.ok) {
        setCalStatusError("Partial load — click Refresh to reload the lead list.");
      }
    } catch (err) {
      const cached = readLocalAdminSnapshot()?.sections?.cal?.data as CalDraftStatus | undefined;
      if (cached?.summary) setCalStatus(cached);
      setCalStatusError(err instanceof Error ? err.message : "Cal queue failed to load.");
    } finally {
      setCalStatusLoading(false);
    }
  }, [adminFetch, session?.access_token]);

  const loadDraftBody = useCallback(async (crmAccountId: string, preview?: string) => {
    if (!crmAccountId) return;
    if (draftBodies[crmAccountId]?.trim()) return;
    setDraftBodyLoading(crmAccountId);
    setDraftLoadErrors((prev) => {
      const next = { ...prev };
      delete next[crmAccountId];
      return next;
    });
    try {
      const res = await adminFetch(`/api/admin/cal/draft/${crmAccountId}`);
      if (res.ok) {
        const data = await res.json() as { draft_full?: string; contact_email?: string | null };
        const full = (data.draft_full || "").trim();
        if (full) {
          setDraftBodies((prev) => ({ ...prev, [crmAccountId]: full }));
        } else if (preview) {
          setDraftBodies((prev) => ({ ...prev, [crmAccountId]: preview }));
          setDraftLoadErrors((prev) => ({ ...prev, [crmAccountId]: "Full draft empty — showing preview. Click Retry." }));
        } else {
          setDraftLoadErrors((prev) => ({ ...prev, [crmAccountId]: "No draft text on this CRM account." }));
        }
        if (data.contact_email != null) {
          setDraftContactEmails((prev) => (
            prev[crmAccountId] !== undefined
              ? prev
              : { ...prev, [crmAccountId]: data.contact_email || "" }
          ));
        }
      } else {
        const errText = await res.text().catch(() => "");
        if (preview) setDraftBodies((prev) => ({ ...prev, [crmAccountId]: preview }));
        setDraftLoadErrors((prev) => ({
          ...prev,
          [crmAccountId]: errText || `Could not load draft (HTTP ${res.status})`,
        }));
      }
    } catch (err) {
      if (preview) setDraftBodies((prev) => ({ ...prev, [crmAccountId]: preview }));
      setDraftLoadErrors((prev) => ({
        ...prev,
        [crmAccountId]: err instanceof Error ? err.message : "Draft load failed",
      }));
    } finally {
      setDraftBodyLoading(null);
    }
  }, [adminFetch, draftBodies]);

  const loadCalAutonomyStatus = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch("/api/admin/cal/autonomy-status");
      if (res.ok) setCalAutonomy(await res.json());
    } catch { /* advisory */ }
  }, [adminFetch, session?.access_token]);

  const toggleCalAutonomy = async (enabled: boolean) => {
    setError("");
    setMessage("");
    try {
      const res = await adminFetch("/api/admin/cal/autonomy-toggle", {
        method: "POST",
        body: JSON.stringify({ enabled }),
      });
      const data = await res.json().catch(() => ({})) as { detail?: string };
      if (!res.ok) throw new Error(data.detail || "Could not update autopilot.");
      setCalAutonomy(data as typeof calAutonomy);
      setMessage(`Cal autopilot turned ${enabled ? "ON" : "OFF"}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Autopilot toggle failed.");
    }
  };

  const loadOperatorDashboard = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch("/api/admin/cal/operator-dashboard");
      if (!res.ok) return;
      const data = (await res.json()) as OperatorDashboard;
      setOperatorDashboard(data);
      setSalesOppTotal(data.sales_opportunities?.total ?? null);
      if (data.cal_queue) {
        setCalStatus((prev) => ({
          summary: { ...prev?.summary, ...data.cal_queue },
          prospects: prev?.prospects ?? [],
          stale: prev?.stale,
          bootstrap_required: prev?.bootstrap_required,
          bootstrap_message: prev?.bootstrap_message,
        }));
      }
      if (data.workflow) {
        setWorkflow((prev) => ({
          ...prev,
          counts: data.workflow?.counts ?? prev?.counts,
          by_source: data.workflow?.by_source ?? prev?.by_source,
          items: data.workflow?.items?.length ? data.workflow.items : prev?.items,
        }));
      }
      if (data.autopilot) setCalAutonomy((prev) => ({ ...prev, ...data.autopilot }));
    } catch { /* advisory */ }
  }, [adminFetch, session?.access_token]);

  const refreshOperatorView = useCallback(async () => {
    await Promise.all([
      loadOperatorDashboard(),
      loadCalStatus(),
      refreshSection("daily_brief", true),
    ]);
  }, [loadCalStatus, loadOperatorDashboard, refreshSection]);

  const saveCalDraft = useCallback(async (crmAccountId: string) => {
    const draft = draftBodies[crmAccountId];
    if (!crmAccountId || !draft?.trim()) {
      setError("Draft is empty — add text before saving.");
      return;
    }
    setActionBusy("cal-save");
    setError("");
    try {
      const res = await adminFetch(`/api/admin/cal/draft/${crmAccountId}`, {
        method: "PATCH",
        body: JSON.stringify({
          outreach_draft: draft,
          contact_email: draftContactEmails[crmAccountId] ?? undefined,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setMessage("Cal draft saved.");
      void refreshOperatorView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save draft.");
    } finally {
      setActionBusy("");
    }
  }, [adminFetch, draftBodies, draftContactEmails, refreshOperatorView]);

  const loadSupplyAutonomyStatus = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch("/api/admin/supply/autonomy-status");
      if (res.ok) setSupplyAutonomy(await res.json());
    } catch { /* advisory */ }
  }, [adminFetch, session?.access_token]);

  const runCalAutonomy = async (dryRun: boolean) => {
    setActionBusy(dryRun ? "cal-draft" : "cal-run");
    setError("");
    try {
      const res = await adminFetch("/api/admin/cal/autonomy-run", {
        method: "POST",
        body: JSON.stringify({ dry_run: dryRun }),
      });
      const data = await res.json().catch(() => ({})) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(data.detail || data.reason || data.status || "Cal autonomy run failed"));
      const skips = [
        data.skipped_no_draft != null ? `${data.skipped_no_draft} skipped (no draft / needs approval)` : null,
        data.skipped_already_sent != null ? `${data.skipped_already_sent} already sent` : null,
        data.skipped_unverified != null ? `${data.skipped_unverified} unverified email` : null,
      ].filter(Boolean);
      const errSample = Array.isArray(data.errors)
        ? (data.errors as Array<{ name?: string; error?: string }>).slice(0, 2).map((e) => `${e.name}: ${e.error}`).join(" · ")
        : "";
      const suffix = [skips.join(", "), errSample].filter(Boolean).join(" — ");
      setMessage(
        dryRun
          ? `Dry run: would draft ${data.drafted ?? 0}, refresh ${data.refreshed ?? 0}, send ${data.sent ?? 0}.${suffix ? ` ${suffix}` : ""}`
          : `Cal cycle: drafted ${data.drafted ?? 0}, refreshed ${data.refreshed ?? 0}, sent ${data.sent ?? 0}.${suffix ? ` ${suffix}` : data.drafted === 0 && data.sent === 0 ? " Queue may already be drafted — check sendable count and assembly blocks." : ""}`,
      );
      void refreshOperatorView();
      void loadCalAutonomyStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cal autonomy run failed.");
    } finally {
      setActionBusy("");
    }
  };

  const runSupplyAutonomy = async (dryRun: boolean) => {
    setActionBusy(dryRun ? "supply-draft" : "supply-send");
    setError("");
    try {
      const res = await adminFetch("/api/admin/supply/autonomy-run", {
        method: "POST",
        body: JSON.stringify({ dry_run: dryRun }),
      });
      const data = await res.json().catch(() => ({})) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(data.detail || "Supply autonomy run failed"));
      setMessage(
        dryRun
          ? `Supply dry run: would send ${data.sent ?? 0} vendor emails (min score ${data.min_score ?? supplyAutonomy?.min_score ?? 60}).`
          : `Supply autonomy: sent ${data.sent ?? 0} vendor signup emails.`,
      );
      void loadSupplyAutonomyStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Supply autonomy run failed.");
    } finally {
      setActionBusy("");
    }
  };

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
    if (authLoading) return;
    const token = session?.access_token ?? null;
    if (!token) {
      adminLoadedForToken.current = null;
      setMeLoading(false);
      return;
    }
    if (adminLoadedForToken.current === token) return;
    adminLoadedForToken.current = token;
    void loadAdmin();
  }, [authLoading, loadAdmin, session?.access_token]);

  useEffect(() => {
    if (meLoading) return;
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const timer = window.setTimeout(() => scrollToHash(hash), 150);
    return () => window.clearTimeout(timer);
  }, [meLoading]);

  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash) scrollToHash(hash);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  function scrollToHash(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  useEffect(() => {
    if (!authLoading && session?.access_token) {
      void loadReplySettings();
    }
  }, [authLoading, loadReplySettings, session?.access_token]);

  useEffect(() => {
    if (!authLoading && session?.access_token && me?.is_admin) {
      void loadOperatorDashboard();
      void loadSupplyAutonomyStatus();
      void loadCalStatus();
    }
  }, [authLoading, loadCalAutonomyStatus, loadCalStatus, loadOperatorDashboard, loadSupplyAutonomyStatus, me?.is_admin, session?.access_token]);

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

  async function runCalBulkDraft(regenerate = false, companyIds?: number[]) {
    setMessage("");
    setError("");
    setActionBusy("cal-draft");
    try {
      const res = await adminFetch("/api/admin/cal/bulk-draft", {
        method: "POST",
        body: JSON.stringify({ regenerate, company_ids: companyIds ?? null }),
      });
      const data = await res.json().catch(() => ({})) as { drafted?: number; skipped?: number; errors?: unknown[] };
      if (!res.ok) throw new Error((data as { detail?: string }).detail || "Bulk draft failed.");
      setMessage(`Cal drafted ${data.drafted ?? 0} emails · ${data.skipped ?? 0} already had drafts · ${data.errors?.length ?? 0} errors.`);
      await refreshOperatorView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk draft failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalDraftOne(companyId: number) {
    await runCalBulkDraft(false, [companyId]);
  }

  async function runCalFixEmails() {
    setMessage("");
    setError("");
    setActionBusy("cleanup");
    try {
      const res = await adminFetch("/api/admin/cal/enrich-missing-emails?limit=80&dry_run=false", { method: "POST" });
      const d = await res.json().catch(() => ({})) as {
        resolved_emails?: number;
        apollo_hits?: number;
        inferred_hits?: number;
        unresolved?: number;
        detail?: string;
      };
      if (!res.ok) throw new Error(d.detail || "Fix emails failed.");
      setMessage(
        `Enriched ${d.resolved_emails ?? 0} emails (Apollo ${d.apollo_hits ?? 0}, inferred ${d.inferred_hits ?? 0}, unresolved ${d.unresolved ?? 0}).`,
      );
      void refreshOperatorView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fix emails failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalDiagnostic() {
    setMessage("");
    setError("");
    try {
      const res = await adminFetch("/api/admin/scout/diagnostic");
      const d = await res.json().catch(() => ({})) as {
        health?: string;
        issues?: string[];
        config?: { from_email?: string | null; api_key_set?: boolean };
        detail?: string;
      };
      if (!res.ok) throw new Error(d.detail || "Diagnostic failed.");
      const issues = d.issues ?? [];
      if (issues.length) {
        setError(`Cal delivery: ${d.health ?? "warn"} — ${issues.slice(0, 2).join(" · ")}`);
      } else {
        setMessage(`Cal delivery healthy — from ${d.config?.from_email ?? "?"}, API key ${d.config?.api_key_set ? "set" : "MISSING"}.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Diagnostic failed.");
    }
  }

  async function runCalReinferContacts() {
    setMessage("");
    setError("");
    setActionBusy("cal-reinfer");
    try {
      const res = await adminFetch("/api/admin/cal/reinfer-contacts?limit=500&dry_run=false", { method: "POST" });
      const data = await res.json().catch(() => ({})) as {
        updated?: number;
        unchanged?: number;
        skipped_sent?: number;
        skipped_person?: number;
        skipped_kept?: number;
        skipped_no_domain?: number;
        detail?: string;
      };
      if (!res.ok) throw new Error(data.detail || "Re-infer contacts failed.");
      setMessage(
        `Re-inferred ${data.updated ?? 0} contacts · ${data.unchanged ?? 0} already correct · `
        + `${data.skipped_sent ?? 0} skipped (sent) · ${(data.skipped_person ?? 0) + (data.skipped_kept ?? 0)} kept existing.`,
      );
      await refreshOperatorView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Re-infer contacts failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalBulkSend(tierFilter: "all" | "HOT" | "WARM" = "all", limit = 1000, skipVerification = false) {
    setMessage("");
    setError("");
    setSendConfirm(false);
    setActionBusy("cal-send");
    let totalSent = 0;
    let totalErrors = 0;
    let lastErrors: Array<{ name?: string; error?: string }> = [];
    try {
      while (true) {
        const res = await adminFetch("/api/admin/cal/bulk-send", {
          method: "POST",
          body: JSON.stringify({
            limit: 100,
            tier_filter: tierFilter,
            dry_run: false,
            skip_verification: skipVerification,
          }),
        });
        const data = await res.json().catch(() => ({})) as {
          sent?: number;
          errors?: Array<{ name?: string; error?: string }>;
          detail?: string;
        };
        if (!res.ok) throw new Error(data.detail || "Send failed.");
        const batchSent = data.sent ?? 0;
        totalSent += batchSent;
        lastErrors = data.errors ?? [];
        totalErrors += lastErrors.length;
        if (batchSent === 0) break;
        if (totalSent >= limit) break;
      }
      await refreshOperatorView();
      if (totalSent === 0) {
        const sample = lastErrors.slice(0, 3).map((e) => `${e.name || "Lead"}: ${e.error || "unknown"}`).join(" · ");
        throw new Error(
          sample
            ? `No emails sent (${totalErrors} blocked). ${sample}`
            : `No emails sent — ${calStatus?.summary?.sendable ?? 0} looked sendable but none passed send checks.`,
        );
      }
      setMessage(`Cal sent ${totalSent} email(s)${totalErrors ? ` · ${totalErrors} skipped/failed` : ""}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed.");
    } finally {
      setActionBusy("");
    }
  }

  async function runCalSendOne(
    crmAccountId: string,
    toEmail: string,
    draftText?: string,
  ) {
    setMessage("");
    setError("");
    setSendConfirm(false);
    setActionBusy("cal-send-one");
    try {
      const payload: Record<string, unknown> = {
        crm_account_id: crmAccountId,
        contact_email: toEmail.trim(),
      };
      if (draftText?.trim()) payload.outreach_draft = draftText.trim();

      const res = await adminFetch("/api/admin/cal/send-one", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({})) as { sent?: boolean; to?: string; detail?: string };
      if (!res.ok) throw new Error(data.detail || "Send failed.");
      setMessage(`Sent to ${data.to ?? toEmail}.`);
      await refreshOperatorView();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed.");
    } finally {
      setActionBusy("");
    }
  }

  const loadAnalyticsDirect = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await adminFetch(`/api/analytics?range=${timeRange}`);
      if (!res.ok) return;
      const data = await res.json() as SiteAnalytics;
      setAnalytics(data);
    } catch {
      /* snapshot path remains primary */
    }
  }, [adminFetch, session?.access_token, timeRange]);

  const loadScoutStatus = useCallback(async () => {
    await refreshSection("scout", true);
  }, [refreshSection]);

  useEffect(() => {
    if (!me?.is_admin || !session?.access_token) return;
    void refreshSection("analytics", true);
    void loadAnalyticsDirect();
  }, [me?.is_admin, refreshSection, session?.access_token, timeRange, loadAnalyticsDirect]);

  async function runScoutBulkActivate() {
    setMessage(""); setError(""); setActionBusy("scout-activate");
    try {
      const res = await adminFetch("/api/admin/scout/bulk-activate", { method: "POST", body: JSON.stringify({ limit: 200, tier_filter: "all", dry_run: false }) });
      const data = await res.json().catch(() => ({})) as { activated?: number; skipped?: number; errors?: number };
      if (!res.ok) throw new Error((data as { detail?: string }).detail || "Activation failed.");
      setMessage(`SIGNAL activated ${data.activated ?? 0} prospects · ${data.skipped ?? 0} already active · ${data.errors ?? 0} errors.`);
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
      setMessage(`SIGNAL sent ${totalSent} emails · ${totalErrors} errors.`);
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

  const calMetrics = useMemo(() => {
    const fromDashboard = operatorDashboard?.cal_queue ?? {};
    const fromStatus = calStatus?.summary ?? {};
    return { ...fromStatus, ...fromDashboard };
  }, [operatorDashboard?.cal_queue, calStatus?.summary]);

  const workflowCounts = useMemo(
    () => operatorDashboard?.workflow?.counts ?? workflow?.counts,
    [operatorDashboard?.workflow?.counts, workflow?.counts],
  );

  const calFilteredProspects = useMemo(() => {
    const rows = calStatus?.prospects ?? [];
    return rows.filter((p) => {
      if (calFilter === "pending") return !p.has_draft;
      if (calFilter === "drafted") return p.has_draft && !p.outreach_sent_at;
      if (calFilter === "sent") return !!p.outreach_sent_at;
      return true;
    });
  }, [calStatus?.prospects, calFilter]);

  const calBuyerCount = calMetrics.buyers ?? operatorDashboard?.buyer_vendor?.buyers;
  const calVendorCount = calMetrics.vendors ?? operatorDashboard?.buyer_vendor?.vendors;

  const calSelectedProspect =
    calSelectedIdx != null ? calFilteredProspects[calSelectedIdx] : calFilteredProspects[0] ?? null;

  const scrollToCalQueue = useCallback(() => {
    scrollToAdminSection("cal-outreach");
  }, []);

  useEffect(() => {
    if (!me?.is_admin) return;
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const timer = window.setTimeout(() => scrollToAdminSection(hash), 350);
    return () => window.clearTimeout(timer);
  }, [me?.is_admin, calStatusLoading]);

  useEffect(() => {
    if (calFilteredProspects.length === 0) {
      setCalSelectedIdx(null);
      return;
    }
    if (calSelectedIdx == null || calSelectedIdx >= calFilteredProspects.length) {
      setCalSelectedIdx(0);
      const p = calFilteredProspects[0];
      if (p?.crm_account_id && p.has_draft) void loadDraftBody(p.crm_account_id, p.draft_preview);
    }
  }, [calFilteredProspects, calSelectedIdx, loadDraftBody]);

  const hasCachedUi = !!(localSnapshot?.sections && Object.keys(localSnapshot.sections).length > 0);

  if ((authLoading || meLoading) && !hasCachedUi) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="mx-auto max-w-6xl px-6 pt-28 text-gray-500">Loading admin...</main>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <Shield className="mx-auto mb-4 h-7 w-7" style={{ color: "#FFB000" }} />
          <h1 className="text-2xl font-bold text-gray-900">Admin sign in required</h1>
          <p className="mt-3 text-sm text-gray-500">Sign in with an admin email to manage ReadyForRobots.</p>
          <Link href="/login" className="mt-6 inline-flex rounded-xl border px-5 py-3 text-sm font-bold" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  if (me && !me.is_admin) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <AlertTriangle className="mx-auto mb-4 h-7 w-7 text-red-300" />
          <h1 className="text-2xl font-bold text-gray-900">Admin access required</h1>
          <p className="mt-3 text-sm text-gray-500">
            {me.email || "This account"} is signed in but is not listed in `ADMIN_EMAILS`.
            Cal outreach and the agent command center live on `/admin` for admin accounts only.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link href="/sales-workflow" className="inline-flex rounded-xl border border-gray-200 px-5 py-3 text-sm font-bold text-gray-700">
              Open sales workflow
            </Link>
            <Link href="/pipeline" className="inline-flex rounded-xl border px-5 py-3 text-sm font-bold" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
              Back to pipeline
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="admin-workspace mx-auto max-w-[1500px] px-4 pb-20 pt-20 lg:px-6">
        <AdminNav />

        {syncingSection && !(syncingSection === "cal" && calStatus) ? (
          <p className="mb-4 rounded-xl border border-gray-200 px-4 py-2 text-xs text-gray-500" >
            Updating {syncingSection.replace(/_/g, " ")}…
          </p>
        ) : null}


        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-lg font-extrabold text-gray-900">Command center</h1>
            <p className="mt-0.5 text-[11px] text-gray-600">
              Daily brief → Cal queue (draft · fix emails · send) → agent queue below
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-xl border border-gray-200 p-1">
              {TIME_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className="rounded-lg px-3 py-1.5 text-[11px] font-bold transition"
                  style={{
                    color: timeRange === range.value ? "#111827" : "#4b5563",
                    background: timeRange === range.value ? "#FFB000" : "transparent",
                  }}
                >
                  {range.label}
                </button>
              ))}
            </div>
            <span className="text-sm text-gray-600">
              <SupabaseInlineLink tone="gray" onClick={() => void loadAdmin()}>Refresh page</SupabaseInlineLink>
              <span className="text-gray-400"> · </span>
              <a href={`${api}/api/docs`} target="_blank" rel="noreferrer" className="font-medium text-amber-700 underline underline-offset-2 hover:text-amber-900">
                API docs
              </a>
            </span>
          </div>
        </div>

        <Link
          href="/admin/special-projects"
          className="mb-4 flex items-center justify-between gap-3 rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3 transition hover:bg-indigo-100"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-extrabold text-white">
              C
            </span>
            <div>
              <div className="text-sm font-extrabold text-indigo-900">
                Cal → Special Projects (NIMO)
              </div>
              <div className="text-[11px] text-indigo-700">
                Review-first outreach queue, funnel & client portal for bespoke robot-company engagements
              </div>
            </div>
          </div>
          <span className="rounded-lg bg-indigo-600 px-3 py-1.5 text-[11px] font-bold text-white">
            Open →
          </span>
        </Link>

        <DailyBriefPanel
          data={dailyBrief}
          loading={dailyBriefLoading}
          calActions={{
            pendingDraft: calMetrics.pending_draft,
            sendable: calMetrics.sendable,
            onOpenQueue: scrollToCalQueue,
            onDraftAll: () => {
              scrollToCalQueue();
              void runCalBulkDraft(false);
            },
            onSendAll: () => {
              scrollToCalQueue();
              setSendConfirm("bulk");
            },
            draftBusy: actionBusy === "cal-draft",
            sendBusy: actionBusy === "cal-send",
          }}
        />

        {message && <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900">{message}</div>}
        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">{error}</div>}

        {/* ── Cal Outreach: primary operator workflow ── */}
        <section id="cal-outreach" className="mb-6 scroll-mt-28 rounded-2xl border border-gray-200 p-4" style={{ background: "linear-gradient(135deg, rgba(167,139,250,0.06), rgba(255,176,0,0.03))" }}>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <Mail className="h-4 w-4 shrink-0" style={{ color: "#10b981" }} />
              <div className="min-w-0">
                <h2 className="text-base font-extrabold text-gray-900 truncate">
                  Cal outreach queue
                </h2>
                <p className="text-[11px] text-gray-500">
                  HOT/WARM scored companies only — draft, edit, send (not the same as &quot;workflow&quot; or SIGNAL drafts)
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className="rounded-full border px-2.5 py-1 text-[10px] font-bold"
                style={{
                  color: calAutonomy?.enabled ? "#047857" : "#b45309",
                  borderColor: calAutonomy?.enabled ? "rgba(5,150,105,0.35)" : "rgba(245,158,11,0.45)",
                  background: calAutonomy?.enabled ? "rgba(5,150,105,0.08)" : "rgba(255,176,0,0.1)",
                }}
              >
                Autopilot {calAutonomy?.enabled ? "ON" : "OFF"}
              </span>
              {calAutonomy?.runtime_toggle_available ? (
                <SupabaseInlineLink
                  tone="gray"
                  onClick={() => void toggleCalAutonomy(!calAutonomy?.enabled)}
                >
                  Turn autopilot {calAutonomy?.enabled ? "off" : "on"}
                </SupabaseInlineLink>
              ) : null}
              <span className="text-xs text-gray-600">
                Filter:{" "}
                {(["all", "pending", "drafted", "sent"] as const).map((f, i) => (
                  <span key={f}>
                    {i > 0 ? <span className="text-gray-400"> · </span> : null}
                    <SupabaseInlineLink
                      tone={calFilter === f ? "emerald" : "gray"}
                      onClick={() => setCalFilter(f)}
                    >
                      {f}
                    </SupabaseInlineLink>
                  </span>
                ))}
                <span className="text-gray-400"> · </span>
                <SupabaseInlineLink tone="gray" onClick={() => void refreshOperatorView()} busy={calStatusLoading}>
                  Refresh queue
                </SupabaseInlineLink>
              </span>
            </div>
          </div>

          {calStatusError ? (
            <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
              {calStatusError}
            </div>
          ) : null}

          {calStatusLoading && !calStatus?.summary ? (
            <p className="mb-4 text-sm text-gray-500 flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading Cal queue…
            </p>
          ) : null}

          <CalWorkflowPanel
            metrics={calMetrics as CalWorkflowMetrics}
            autopilotEnabled={calAutonomy?.enabled}
            busy={actionBusy}
            onDraftAll={() => void runCalBulkDraft(false)}
            onRegenerate={() => void runCalBulkDraft(true)}
            onFixEmails={() => void runCalFixEmails()}
            onReinfer={() => void runCalReinferContacts()}
            onReview={() => scrollToAdminSection("cal-queue-list")}
            onSendAll={() => setSendConfirm("bulk")}
            onRunCal={() => void runCalAutonomy(false)}
            onOpenReplies={() => setLocation("/inbox")}
            onTestDelivery={() => void runCalDiagnostic()}
          />

          {/* ── Bulk-send confirm modal ── */}
          {sendConfirm === "bulk" && (
            <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 p-4">
              <p className="mb-1 text-sm font-bold text-amber-900">Confirm bulk send</p>
              <p className="mb-3 text-xs text-amber-950/80">
                <strong>{calMetrics.sendable ?? 0} emails will go out</strong> via Resend
                {(calMetrics.no_email ?? 0) > 0 && (
                  <span className="text-amber-800"> · {calMetrics.no_email} contacts skipped (no email address on file)</span>
                )}
                {(calMetrics.sent ?? 0) > 0 && <span className="text-amber-700"> · {calMetrics.sent} already sent (no duplicates)</span>}
                {". "}Cannot be undone.
              </p>
              <label className="mb-3 flex items-center gap-2 text-xs text-amber-950">
                <input
                  type="checkbox"
                  checked={bulkSendSkipVerify}
                  onChange={(e) => setBulkSendSkipVerify(e.target.checked)}
                />
                Skip email verification (use if role inboxes block sends)
              </label>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <SupabaseInlineLink
                  tone="amber"
                  onClick={() => void runCalBulkSend("all", 1000, bulkSendSkipVerify)}
                  busy={actionBusy === "cal-send"}
                >
                  Yes — send all now
                </SupabaseInlineLink>
                <SupabaseInlineLink tone="gray" onClick={() => setSendConfirm(false)}>
                  Cancel
                </SupabaseInlineLink>
              </div>
            </div>
          )}

          <div className="mb-4 grid grid-cols-3 gap-2 md:grid-cols-8">
            <AdminCard label="Total" value={formatNumber(calMetrics.total)} sub={`${formatNumber(calMetrics.hot)} hot · ${formatNumber(calMetrics.warm)} warm`} />
            <AdminCard label="Buyers" value={formatNumber(calBuyerCount)} sub="HOT/WARM" />
            <AdminCard label="Vendors" value={formatNumber(calVendorCount)} sub="HOT/WARM" />
            <AdminCard label="Drafted" value={formatNumber(calMetrics.drafted)} sub={`${formatNumber(calMetrics.unsent_drafted)} unsent`} />
            <AdminCard label="Pending" value={formatNumber(calMetrics.pending_draft)} sub="need draft" />
            <AdminCard label="Sent" value={formatNumber(calMetrics.sent)} sub="delivered" />
            <AdminCard label="Opened" value={formatNumber(calMetrics.opened)} sub="engagement" />
            <AdminCard label="Replied" value={formatNumber(calMetrics.replied)} sub="to Cal" />
          </div>

          <p className="mb-3 text-[11px] text-gray-500">
            Template v{calAutonomy?.template_version ?? "2"} — global voice in code; select a lead on the left to edit its draft on the right.
          </p>

          {/* Queue list + CRM sample panel */}
          <div id="cal-queue-list" className="grid scroll-mt-28 gap-4 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="max-h-[560px] overflow-y-auto rounded-xl border border-gray-200 bg-white/80 pr-1">
            {!calStatus ? (
              <p className="py-6 text-center text-xs text-gray-400">
                {syncingSection === "cal" ? "Loading prospect draft status…" : "No Cal outreach data yet."}
              </p>
            ) : calFilteredProspects.length === 0 ? (
              <p className="py-6 text-center text-xs text-gray-500">
                {calStatusLoading
                  ? "Loading lead list…"
                  : calFilter !== "all" && (calMetrics.drafted ?? 0) > 0
                    ? `No rows on "${calFilter}" filter — try All (${formatNumber(calMetrics.total)} leads) or Refresh.`
                    : "No prospects match this filter."}
              </p>
            ) : (
              <div className="space-y-1 p-2">
                <div className="admin-table-head grid grid-cols-[2fr_1fr_1fr] gap-2 px-2">
                  <span>Company</span>
                  <span>Tier</span>
                  <span>Stage</span>
                </div>
                {calFilteredProspects.map((prospect, idx) => {
                  const selected = (calSelectedIdx ?? 0) === idx;
                  const tierColor = prospect.tier === "HOT" ? "#b45309" : prospect.tier === "WARM" ? "#047857" : "#6b7280";
                  return (
                    <button
                      key={`${prospect.company_id}-${idx}`}
                      type="button"
                      className={`admin-table-row grid w-full grid-cols-[2fr_1fr_1fr] gap-2 px-3 py-2.5 text-left ${selected ? "ring-2 ring-emerald-400/50" : ""}`}
                      onClick={() => {
                        setCalSelectedIdx(idx);
                        if (prospect.crm_account_id && prospect.has_draft) void loadDraftBody(prospect.crm_account_id, prospect.draft_preview);
                      }}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-gray-800">{prospect.company_name || "—"}</p>
                        <p className="text-[10px] text-gray-400">{prospect.account_type === "vendor" ? "vendor" : "buyer"} · {prospect.industry}</p>
                      </div>
                      <span className="text-[10px] font-bold" style={{ color: tierColor }}>{prospect.tier}</span>
                      <span className="text-[10px] text-gray-500 truncate">
                        {prospect.outreach_sent_at ? "sent" : prospect.has_draft ? "drafted" : "pending"}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
            </div>

            <div className="lg:sticky lg:top-24 max-h-[560px] overflow-y-auto rounded-xl border border-emerald-200 bg-white p-4 shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">CRM sample · Cal draft</p>
              {!calSelectedProspect ? (
                <p className="mt-6 text-sm text-gray-500">Select a lead from the queue to preview and edit Cal&apos;s email.</p>
              ) : (
                <div className="mt-3 space-y-3">
                  <div>
                    <p className="text-base font-bold text-gray-900">{calSelectedProspect.company_name}</p>
                    <p className="text-xs text-gray-500">{calSelectedProspect.tier} · score {calSelectedProspect.score?.toFixed(0)} · {calSelectedProspect.account_type === "vendor" ? "vendor" : "buyer (RFR)"}</p>
                    {calSelectedProspect.semantic_summary ? (
                      <p className="mt-2 text-xs text-gray-600 leading-relaxed">{calSelectedProspect.semantic_summary}</p>
                    ) : null}
                  </div>
                  {calSelectedProspect.has_draft ? (
                    <>
                      {calSelectedProspect.crm_account_id && (
                        <label className="block">
                          <span className="mb-1 block text-[10px] uppercase tracking-widest text-gray-400">Contact email</span>
                          <input
                            value={draftContactEmails[calSelectedProspect.crm_account_id] ?? calSelectedProspect.contact_email ?? ""}
                            onChange={(e) => {
                              const id = calSelectedProspect.crm_account_id!;
                              setDraftContactEmails((prev) => ({ ...prev, [id]: e.target.value }));
                            }}
                            placeholder="name@company.com"
                            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 font-mono text-[11px] text-gray-800"
                          />
                        </label>
                      )}
                      {calSelectedProspect.crm_account_id && draftLoadErrors[calSelectedProspect.crm_account_id] ? (
                        <div className="text-xs text-amber-800">
                          {draftLoadErrors[calSelectedProspect.crm_account_id]}{" "}
                          <SupabaseInlineLink
                            tone="amber"
                            onClick={() => void loadDraftBody(
                              calSelectedProspect.crm_account_id!,
                              calSelectedProspect.draft_preview,
                            )}
                            busy={draftBodyLoading === calSelectedProspect.crm_account_id}
                          >
                            Retry full draft
                          </SupabaseInlineLink>
                        </div>
                      ) : null}
                      <textarea
                        value={
                          calSelectedProspect.crm_account_id && draftBodies[calSelectedProspect.crm_account_id]
                            ? draftBodies[calSelectedProspect.crm_account_id]
                            : draftBodyLoading === calSelectedProspect.crm_account_id
                              ? (calSelectedProspect.draft_preview || "Loading full draft…")
                              : calSelectedProspect.draft_preview || calSelectedProspect.has_draft
                                ? (calSelectedProspect.draft_preview || "Select Retry to load draft")
                                : ""
                        }
                        onChange={(e) => {
                          if (!calSelectedProspect.crm_account_id) return;
                          if (draftBodyLoading === calSelectedProspect.crm_account_id) return;
                          setDraftBodies((prev) => ({ ...prev, [calSelectedProspect.crm_account_id!]: e.target.value }));
                        }}
                        rows={14}
                        className="w-full rounded-xl border border-gray-200 bg-slate-50 px-3 py-3 font-mono text-[11px] leading-relaxed text-gray-800"
                      />
                      <div className="text-sm">
                        {calSelectedProspect.crm_account_id ? (
                          <>
                            <SupabaseInlineLink
                              onClick={() => void saveCalDraft(calSelectedProspect.crm_account_id!)}
                              disabled={
                                actionBusy === "cal-save"
                                || draftBodyLoading === calSelectedProspect.crm_account_id
                                || !draftBodies[calSelectedProspect.crm_account_id]?.trim()
                              }
                              busy={actionBusy === "cal-save"}
                            >
                              Save draft
                            </SupabaseInlineLink>
                            {!calSelectedProspect.outreach_sent_at ? (
                              <>
                                <span className="text-gray-400"> · </span>
                                <SupabaseInlineLink
                                  tone="amber"
                                  onClick={() => setSendConfirm(calSelectedProspect.crm_account_id!)}
                                  disabled={
                                    actionBusy === "cal-send-one"
                                    || actionBusy === "cal-send"
                                    || !(draftContactEmails[calSelectedProspect.crm_account_id] ?? calSelectedProspect.contact_email)?.trim()
                                  }
                                >
                                  Send this lead
                                </SupabaseInlineLink>
                              </>
                            ) : null}
                          </>
                        ) : null}
                      </div>
                      <CalEmailPreview
                        companyName={calSelectedProspect.company_name}
                        bodyText={
                          calSelectedProspect.crm_account_id && draftBodies[calSelectedProspect.crm_account_id]
                            ? draftBodies[calSelectedProspect.crm_account_id]
                            : calSelectedProspect.draft_preview || ""
                        }
                      />
                    </>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">No draft yet —</p>
                      <SupabaseInlineLink
                        onClick={() => calSelectedProspect.company_id && void runCalDraftOne(calSelectedProspect.company_id)}
                        disabled={actionBusy === "cal-draft" || !calSelectedProspect.company_id}
                        busy={actionBusy === "cal-draft"}
                      >
                        Draft this lead
                      </SupabaseInlineLink>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>

        <details id="workflow" className="mb-4 scroll-mt-28 rounded-xl border border-gray-200 bg-white px-4 py-3">
          <summary className="cursor-pointer list-none text-sm font-bold text-gray-900 marker:content-none">
            Other agent work
            <span className="ml-2 text-xs font-normal text-gray-500">
              {formatNumber(workflowCounts?.total)} tasks · {formatNumber(workflowCounts?.queued)} queued · not Cal email queue
            </span>
          </summary>
          <p className="mt-3 text-xs text-gray-600">
            <strong>Workflow ({formatNumber(workflowCounts?.total)})</strong> = sales agent actions, research updates, SIGNAL drafts, supply outreach — separate from Cal&apos;s HOT/WARM queue ({formatNumber(calMetrics.total)}).
            <strong> Sales opps ({formatNumber(operatorDashboard?.sales_opportunities?.total ?? salesOppTotal ?? 0)})</strong> = buyer reply threads in Sales Console, not drafts.
            <strong> Need approve ({formatNumber(workflowCounts?.needs_approval)})</strong> = items waiting for you in those other queues (Cal uses autopilot; pending draft ≠ approval).
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <Link href="/sales-console" className="font-medium text-emerald-700 underline underline-offset-2">Sales console</Link>
            <span className="text-gray-400">·</span>
            <Link href="/pipeline" className="font-medium text-emerald-700 underline underline-offset-2">Research pipeline</Link>
            <span className="text-gray-400">·</span>
            <Link href="/crm" className="font-medium text-emerald-700 underline underline-offset-2">CRM editor</Link>
          </div>
          <div className="mt-3 max-h-[240px] space-y-2 overflow-y-auto">
            {(workflow?.items?.length ? workflow.items : []).slice(0, 15).map((item) => {
              const style = stateStyle(item.state);
              return (
                <div key={`${item.source}-${item.id}`} className="rounded-lg border border-gray-100 px-3 py-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border px-2 py-0.5 text-[10px] capitalize" style={style}>{stateLabel(item.state)}</span>
                    <span className="text-[10px] capitalize text-gray-500">{sourceLabel(item.source)}</span>
                    <span className="text-sm font-medium text-gray-900">{item.title}</span>
                    {item.next_action_url ? (
                      <Link href={item.next_action_url} className="text-xs font-medium text-emerald-700 underline underline-offset-2">
                        {item.next_action_label || "Open"}
                      </Link>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </details>

        <details className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50/40 px-4 py-3 group">
          <summary className="cursor-pointer list-none text-[11px] font-bold text-emerald-900 marker:content-none">
            Cal autonomy
            <span className="ml-2 font-normal text-emerald-800/70">scheduled worker cycles · daily digest to ADMIN_EMAIL</span>
          </summary>
          <div className="mt-3 space-y-3 text-[11px] leading-relaxed text-gray-700">
            <p>
              Worker runs every {calAutonomy?.every_hours ?? 3}h — drafts, refreshes stale copy, sends up to{" "}
              <strong>{calAutonomy?.send_limit ?? 25}</strong> verified emails per cycle when autopilot is ON.
            </p>
            <p>
              Status:{" "}
              <span className="font-bold" style={{ color: calAutonomy?.enabled ? "#047857" : "#b45309" }}>
                {calAutonomy?.enabled ? "ON" : "OFF"}
              </span>
              {calAutonomy?.review_email ? (
                <> · ops inbox: <span className="font-mono">{calAutonomy.review_email}</span></>
              ) : null}
            </p>
            <div className="text-sm text-gray-700">
              {calAutonomy?.runtime_toggle_available ? (
                <>
                  <SupabaseInlineLink
                    tone="gray"
                    onClick={() => void toggleCalAutonomy(!calAutonomy?.enabled)}
                  >
                    Autopilot {calAutonomy?.enabled ? "off" : "on"}
                  </SupabaseInlineLink>
                  <span className="text-gray-400"> · </span>
                </>
              ) : null}
              <SupabaseInlineLink
                tone="gray"
                onClick={() => void runCalAutonomy(true)}
                busy={actionBusy === "cal-run"}
              >
                Dry run
              </SupabaseInlineLink>
              <span className="text-gray-400"> · </span>
              <SupabaseInlineLink
                onClick={() => void runCalAutonomy(false)}
                busy={actionBusy === "cal-run"}
              >
                Run Cal now
              </SupabaseInlineLink>
            </div>
          </div>
        </details>

        <details className="mb-4 rounded-xl border border-sky-200 bg-sky-50/40 px-4 py-3 group">
          <summary className="cursor-pointer list-none text-[11px] font-bold text-sky-900 marker:content-none">
            Supply autonomy
            <span className="ml-2 font-normal text-sky-800/70">vendor signup outreach</span>
          </summary>
          <div className="mt-3 space-y-3 text-[11px] leading-relaxed text-gray-700">
            <p>
              Vendor signup emails (score ≥ {supplyAutonomy?.min_score ?? 60}) — up to{" "}
              <strong>{supplyAutonomy?.send_limit ?? 6}</strong> per {supplyAutonomy?.every_hours ?? 6}h cycle.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link href="/supply-pipeline" className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-[10px] font-bold text-gray-700">
                Supply pipeline
              </Link>
              <button type="button" disabled={!!actionBusy} onClick={() => void runSupplyAutonomy(true)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-[10px] font-bold text-gray-700 disabled:opacity-50">
                Dry run
              </button>
              <button type="button" disabled={!!actionBusy} onClick={() => void runSupplyAutonomy(false)} className="rounded-xl border px-3 py-2 text-[10px] font-bold disabled:opacity-50" style={{ color: "#0369a1", borderColor: "rgba(14,165,233,0.35)", background: "rgba(14,165,233,0.08)" }}>
                Run supply now
              </button>
            </div>
          </div>
        </details>

        <details className="mb-8 rounded-xl border border-gray-200 bg-white px-4 py-3 group">
          <summary className="cursor-pointer list-none text-[11px] font-bold text-gray-500 marker:content-none">
            Reply notification email
            <span className="ml-2 font-normal text-gray-400">optional · forwards Cal replies</span>
          </summary>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="email"
              value={replyForwardEmail}
              onChange={(e) => setReplyForwardEmail(e.target.value)}
              placeholder="ugobe07@gmail.com"
              className="flex-1 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus:border-emerald-400/60"
            />
            <button
              type="button"
              disabled={replySettingBusy}
              onClick={() => void saveReplySettings()}
              className="shrink-0 px-4 py-2 rounded-xl text-sm font-bold border transition-all disabled:opacity-50"
              style={
                replySettingSaved
                  ? { background: "rgba(52,211,153,0.12)", borderColor: "rgba(52,211,153,0.35)", color: "#047857" }
                  : { background: "rgba(5,150,105,0.12)", borderColor: "rgba(5,150,105,0.35)", color: "#047857" }
              }
            >
              {replySettingSaved ? "✓ Saved" : "Save"}
            </button>
          </div>
        </details>

        <details className="mt-10 mb-6 rounded-xl border border-gray-200 bg-white px-4 py-3">
          <summary className="cursor-pointer text-sm font-bold text-gray-600">
            Advanced system settings
          </summary>
          <div className="mt-4 space-y-6">

        <section className="mb-8">
          <div className="mb-3 flex items-center gap-2">
            <Users className="h-4 w-4" style={{ color: "#FFB000" }} />
            <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Users and accounts</p>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <AdminCard label="Users" value={formatNumber(userStats?.total_users)} sub={`${formatNumber(userStats?.active_users)} active in 7 days`} />
            <AdminCard label="Saved Companies" value={formatNumber(userStats?.total_saved)} sub="Buyer accounts tracking leads" />
            <AdminCard label="Reports" value={formatNumber(userStats?.total_reports)} sub={`${formatNumber(userStats?.total_lists)} saved lists`} />
            <AdminCard label="Captured Leads" value={formatNumber((userStats?.waitlist_signups || 0) + (userStats?.newsletter_subscribers || 0))} sub={`${formatNumber(userStats?.waitlist_signups)} SIGNAL · ${formatNumber(userStats?.newsletter_subscribers)} newsletter`} />
          </div>
        </section>


        <section id="robot-benchmark" className="mb-8 scroll-mt-28">
          <div className="mb-3 flex items-center gap-2">
            <span style={{ color: "#10b981", fontSize: 16 }}>🤖</span>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em]" style={{ color: "#10b981" }}>Robot Benchmark Index</p>
          </div>
          <RobotBenchmarkPanel api={api} headers={headers as Record<string, string | undefined>} />
        </section>

        <SiteMetricsPanel
          loading={syncingSection === "analytics"}
          timeRangeLabel={timeRange.toUpperCase()}
          data={{
            siteVisits: analytics?.site_visits,
            funnelRuns: analytics?.total_calculations,
            buyerIntake: analytics?.robot_searches,
            emailCaptures: analytics?.email_captures,
            conversionRate: analytics?.conversion_rate,
            hotCount: analytics?.hot_count,
            warmCount: analytics?.warm_count,
            totalSignals: analytics?.total_signals ?? stats?.totals?.signals,
            signupStart: analytics?.signup_funnel?.signup_start,
            signupComplete: analytics?.signup_funnel?.signup_complete,
            firstSave: analytics?.signup_funnel?.first_save,
            startToCompleteRate: analytics?.signup_funnel?.start_to_complete_rate,
            completeToSaveRate: analytics?.signup_funnel?.complete_to_save_rate,
          }}
        />

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-gray-200 p-5" >
            <div className="mb-4 flex items-center justify-between gap-3">
              <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#10b981" }}>Recent users</p>
              <span className="rounded-full border border-gray-200 px-2.5 py-1 text-[10px] text-gray-400">{formatNumber(users.length)} shown</span>
            </div>
            <div className="max-h-[380px] overflow-y-auto pr-1">
              <div className="admin-table-head grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] gap-3">
                <span>User</span>
                <span>Saved</span>
                <span>Reports</span>
                <span>Last active</span>
              </div>
              {(users.length ? users : [{ email: "No users yet" }]).slice(0, 30).map((user, index) => (
                <div key={user.id || `${user.email}-${index}`} className="grid grid-cols-[1.4fr_0.7fr_0.7fr_0.7fr] gap-3 border-b border-gray-200 py-3 text-xs">
                  <div className="min-w-0">
                    <p className="truncate text-gray-900">{user.email || "Unknown user"}</p>
                    <p className="mt-1 truncate text-[10px] text-gray-500">{user.id || "—"}</p>
                  </div>
                  <span className="font-mono text-gray-500">{formatNumber(user.saved_count)}</span>
                  <span className="font-mono text-gray-500">{formatNumber(user.reports_count)}</span>
                  <span className="text-gray-400">{formatDate(user.last_active || user.created_at)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 p-5" >
            <div className="mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4" style={{ color: "#FFB000" }} />
              <p className="text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Recent activity</p>
            </div>
            <div className="max-h-[380px] space-y-2 overflow-y-auto pr-1">
              {(activity.length ? activity : [{ label: "No recent activity yet", detail: "User saves, reports, signups, and newsletter subscribers will appear here." }]).map((item, index) => (
                <div key={`${item.type}-${item.created_at}-${index}`} className="admin-table-row px-3 py-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold text-gray-700">{item.label}</p>
                    <span className="shrink-0 text-[10px] text-gray-500">{formatDate(item.created_at)}</span>
                  </div>
                  <p className="mt-1 truncate text-[11px]" style={{ color: activityColor(item.type) }}>{item.actor || "ReadyForRobots"}</p>
                  <p className="mt-1 break-words text-[11px] text-gray-400">{item.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {analytics?.insights && (
          <section className="mb-8 rounded-2xl border border-gray-200 p-5" style={{ background: "linear-gradient(135deg, rgba(255,176,0,0.08), rgba(3,218,197,0.04))" }}>
            <p className="mb-3 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Operator notes</p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {[analytics.insights.hottest_trend, analytics.insights.opportunity, analytics.insights.action_item].filter(Boolean).map((item) => (
                <p key={item} className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-3 text-xs leading-relaxed text-gray-700">{item}</p>
              ))}
            </div>
          </section>
        )}

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-2xl border border-gray-200 p-5" >
            <p className="mb-2 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>System controls</p>
            <p className="mb-4 text-xs leading-relaxed text-gray-600">
              These actions use the same authenticated admin session, so failures are shown here instead of opening unauthenticated tabs.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void runSystemAction("cache")}
                disabled={!!actionBusy}
                className="rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-600 disabled:opacity-50"
              >
                {actionBusy === "cache" ? "Clearing..." : "Clear cache"}
              </button>
              <button
                type="button"
                onClick={() => void runSystemAction("reindex")}
                disabled={!!actionBusy}
                className="rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-600 disabled:opacity-50"
              >
                {actionBusy === "reindex" ? "Reindexing..." : "Reindex database"}
              </button>
              <button
                type="button"
                onClick={() => void runSystemAction("cleanup")}
                disabled={!!actionBusy}
                className="rounded-xl border border-gray-200 px-4 py-2 text-xs font-bold text-gray-600 disabled:opacity-50"
              >
                {actionBusy === "cleanup" ? "Queueing..." : "Cleanup junk leads"}
              </button>
              <button
                type="button"
                onClick={() => void exportAllData()}
                disabled={!!actionBusy}
                className="rounded-xl border px-4 py-2 text-xs font-bold disabled:opacity-50"
                style={{ color: "#059669", borderColor: "rgba(3,218,197,0.45)" }}
              >
                {actionBusy === "export" ? "Exporting..." : "Export all data"}
              </button>
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
          <div className="rounded-2xl border border-gray-200 p-5" >
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#10b981" }}>Industry mix</p>
            <div className="space-y-2">
              {(stats?.by_industry || []).slice(0, 8).map((item) => (
                <div key={item.industry} className="flex items-center justify-between text-sm">
                  <span className="text-gray-800">{item.industry || "Unknown"}</span>
                  <span className="font-mono text-gray-400">{formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200 p-5" >
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#059669" }}>Signal types</p>
            <div className="space-y-2">
              {(stats?.by_signal_type || []).slice(0, 8).map((item) => (
                <div key={item.signal_type} className="flex items-center justify-between text-sm">
                  <span className="text-gray-800">{(item.signal_type || "unknown").replace(/_/g, " ")}</span>
                  <span className="font-mono text-gray-400">{formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <form onSubmit={importUrls} className="rounded-2xl border border-gray-200 p-5" >
            <UploadCloud className="mb-4 h-5 w-5" style={{ color: "#FFB000" }} />
            <p className="text-sm font-bold text-gray-900">Import URLs</p>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://example.com/feed&#10;https://example.com/news" className="sb-input mt-3 min-h-28 text-xs" />
            <select value={urlIndustry} onChange={(e) => setUrlIndustry(e.target.value)} className="sb-input mt-2 text-xs">
              {INDUSTRIES.map((item) => <option key={item} value={item}>{item || "Auto-detect industry"}</option>)}
            </select>
            <label className="mt-3 flex items-center gap-2 text-xs text-gray-500">
              <input type="checkbox" checked={scrapeNow} onChange={(e) => setScrapeNow(e.target.checked)} className="accent-violet-500" />
              Scrape now
            </label>
            <button type="submit" disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold disabled:opacity-50" style={{ color: "#FFB000", borderColor: "#FFB000" }}>
              {actionBusy === "urls" ? "Importing..." : "Import URLs"}
            </button>
          </form>

          <form onSubmit={importCompanies} className="rounded-2xl border border-gray-200 p-5" >
            <DownloadCloud className="mb-4 h-5 w-5" style={{ color: "#10b981" }} />
            <p className="text-sm font-bold text-gray-900">Import Companies</p>
            <textarea value={companyJson} onChange={(e) => setCompanyJson(e.target.value)} className="sb-input mt-3 min-h-40 font-mono text-[11px]" />
            <button type="submit" disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-violet-300/45 px-4 py-2.5 text-xs font-bold text-emerald-700 disabled:opacity-50">
              {actionBusy === "companies" ? "Importing..." : "Import Companies"}
            </button>
          </form>

          <form onSubmit={triggerScrape} className="rounded-2xl border border-gray-200 p-5" >
            <Play className="mb-4 h-5 w-5" style={{ color: "#059669" }} />
            <p className="text-sm font-bold text-gray-900">Trigger Scraper</p>
            <select value={triggerScraper} onChange={(e) => setTriggerScraper(e.target.value)} className="sb-input mt-3 text-xs">
              {SCRAPERS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={triggerIndustry} onChange={(e) => setTriggerIndustry(e.target.value)} className="sb-input mt-2 text-xs">
              {INDUSTRIES.map((item) => <option key={item} value={item}>{item || "All industries"}</option>)}
            </select>
            <button type="submit" disabled={!!actionBusy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-teal-600 bg-teal-50 px-4 py-2.5 text-xs font-bold text-teal-900 disabled:opacity-50">
              {actionBusy === "scraper" ? "Queueing..." : "Queue Scraper"}
            </button>
          </form>
        </section>


        <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.2fr]">
          <div className="rounded-2xl border border-gray-200 p-5" >
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#FFB000" }}>Recent companies</p>
            <div className="space-y-3">
              {(stats?.recent_companies || []).map((company) => (
                <div key={company.id} className="admin-table-row px-3 py-2">
                  <p className="text-sm font-semibold text-gray-800">{company.name}</p>
                  <p className="mt-1 text-[11px] text-gray-400">{company.industry} · {company.source || "unknown"}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 p-5" >
            <p className="mb-4 text-[10px] font-normal uppercase tracking-[0.18em]" style={{ color: "#10b981" }}>Scrape targets</p>
            <div className="mb-4 flex flex-wrap gap-2">
              {Object.entries(targets?.summary || {}).map(([key, value]) => (
                <span key={key} className="rounded-full border border-gray-200 px-2.5 py-1 text-[10px] text-gray-500">{key}: {value}</span>
              ))}
            </div>
            <div className="max-h-[460px] space-y-2 overflow-y-auto pr-1">
              {(targets?.targets || []).slice(0, 40).map((target, index) => (
                <div key={`${target.url}-${index}`} className="admin-table-row px-3 py-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-xs font-semibold text-gray-700">{target.label || target.url}</p>
                    <span className="shrink-0 rounded-full border border-gray-200 px-2 py-0.5 text-[9px] text-gray-400">{target.scraper}</span>
                  </div>
                  <p className="mt-1 break-all text-[11px] text-gray-500">{target.url}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
          </div>
        </details>
      </main>
    </div>
  );
}
