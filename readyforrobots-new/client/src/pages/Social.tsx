/**
 * Content Studio — daily social posts from /api/social/daily-posts + LinkedIn publish.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, getDirectApiBase, liveFetchInit, readSurfaceCache, writeSurfaceCache } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

const SOCIAL_SESSION_KEY = "social_daily_posts_v1";
const SOCIAL_SESSION_TTL_MS = 4 * 60 * 60 * 1000;
const SOCIAL_STALE_PAINT_MS = 7 * 24 * 60 * 60 * 1000;
const SOCIAL_FETCH_MS = 12_000;
const SOCIAL_RETRY_MS = 8_000;
const SOCIAL_REFRESH_MS = 150_000;

function socialApiBases(): string[] {
  if (typeof window === "undefined") return [getApiBase()];
  const h = window.location.hostname.toLowerCase();
  if (h === "readyforrobots.com" || h === "www.readyforrobots.com" || h.endsWith(".readyforrobots.com")) {
    // Same-origin proxy first (reliable CORS); Fly direct if proxy times out.
    return [getApiBase(), getDirectApiBase()];
  }
  return [getApiBase()];
}

/** Primary API base for LinkedIn OAuth (must match redirect / return_to host). */
const API = getApiBase();

async function socialPostFetch(
  path: string,
  init: RequestInit = {},
  timeoutMs = SOCIAL_FETCH_MS,
): Promise<Response> {
  const bases = socialApiBases();
  let lastErr: Error | null = null;
  for (let i = 0; i < bases.length; i++) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(`${bases[i]}${path}`, liveFetchInit({ ...init, signal: controller.signal }));
      if (i < bases.length - 1 && (res.status === 502 || res.status === 503 || res.status === 504)) {
        continue;
      }
      return res;
    } catch (e) {
      lastErr =
        e instanceof Error && e.name === "AbortError"
          ? new Error("Request timed out — generation can take up to a minute. Try again.")
          : e instanceof Error
            ? e
            : new Error("Request failed");
      if (i < bases.length - 1) continue;
      throw lastErr;
    } finally {
      window.clearTimeout(timer);
    }
  }
  throw lastErr || new Error("Request failed");
}

type PostType = "hot_lead" | "signal_alert" | "industry_insight" | "market_trend" | "thought_leadership";

type SocialPost = {
  type: PostType;
  title?: string;
  source_name?: string;
  source_industry?: string;
  score?: number;
  company_id?: number;
  twitter?: string;
  linkedin?: string;
  hashtags?: string[];
  share_url?: string;
};

type LinkedInStatus = {
  configured?: boolean;
  connected?: boolean;
  member_posting?: boolean;
  pending_marketing_api?: boolean;
  member_name?: string;
  organization_id?: string;
  organization_urn?: string;
  organization_page_status?: string;
  organization_url?: string;
};

const POST_TYPE_META: Record<
  PostType,
  { label: string; border: string; text: string; bg: string }
> = {
  hot_lead: { label: "🔥 Buyer Spotlight", border: "border-red-200", text: "text-red-700", bg: "bg-red-50" },
  signal_alert: { label: "📊 Buyer Alert", border: "border-amber-200", text: "text-amber-800", bg: "bg-amber-50" },
  industry_insight: { label: "🧠 Industry Brief", border: "border-sky-200", text: "text-sky-800", bg: "bg-sky-50" },
  market_trend: { label: "📈 Market Trend", border: "border-violet-200", text: "text-violet-800", bg: "bg-violet-50" },
  thought_leadership: { label: "🤖 Thought Leadership", border: "border-emerald-200", text: "text-emerald-800", bg: "bg-emerald-50" },
};

const TWITTER_SOFT_LIMIT = 257;

function charColor(len: number) {
  if (len <= 200) return "text-emerald-700";
  if (len <= 240) return "text-amber-700";
  return "text-red-600";
}

function CopyButton({ text, label = "Copy", successLabel = "Copied!" }: { text: string; label?: string; successLabel?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        });
      }}
      className={`text-xs px-3 py-1.5 rounded border transition-colors font-mono ${
        copied
          ? "border-emerald-300 text-emerald-700 bg-emerald-50"
          : "border-gray-300 text-gray-600 hover:border-gray-400 hover:text-gray-900 bg-white"
      }`}
    >
      {copied ? successLabel : label}
    </button>
  );
}

function PostCard({
  post,
  index,
  onMarkPosted,
  isPosted,
  linkedinConnected,
  onPublishLinkedIn,
  publishing,
}: {
  post: SocialPost;
  index: number;
  onMarkPosted: (post: SocialPost) => Promise<void>;
  isPosted: boolean;
  linkedinConnected: boolean;
  onPublishLinkedIn: (text: string, url: string) => Promise<void>;
  publishing: boolean;
}) {
  const meta = POST_TYPE_META[post.type] || POST_TYPE_META.thought_leadership;
  const [activeTab, setActiveTab] = useState<"twitter" | "linkedin">("twitter");
  const [twitterText, setTwitterText] = useState(post.twitter || "");
  const [linkedinText, setLinkedinText] = useState(post.linkedin || "");
  const [marking, setMarking] = useState(false);
  const shareUrl = post.share_url || "https://readyforrobots.com";

  return (
    <div className={`border bg-white shadow-sm ${isPosted ? "border-gray-200 opacity-70" : meta.border} rounded-xl overflow-hidden transition-opacity`}>
      <div className={`${isPosted ? "bg-gray-50" : meta.bg} border-b ${isPosted ? "border-gray-200" : meta.border} px-4 py-3 flex items-center justify-between gap-3 flex-wrap`}>
        <div className="flex items-center gap-3">
          <span className="text-gray-500 font-mono text-xs tabular-nums">#{index + 1}</span>
          <span className={`text-sm font-semibold ${isPosted ? "text-gray-500" : meta.text}`}>
            {isPosted ? "✓ Posted — " : ""}
            {meta.label}
          </span>
          {post.source_name && <span className="text-xs text-gray-600 truncate max-w-[200px]">{post.source_name}</span>}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {post.source_industry && (
            <span className="text-[10px] border border-gray-200 bg-white text-gray-600 px-2 py-0.5 rounded font-mono">{post.source_industry}</span>
          )}
          {post.score != null && (
            <span className="text-[10px] border border-gray-200 bg-white text-gray-600 px-2 py-0.5 rounded font-mono">Score {post.score}/100</span>
          )}
          {!isPosted && post.company_id && (
            <button
              type="button"
              onClick={async () => {
                setMarking(true);
                await onMarkPosted(post);
                setMarking(false);
              }}
              disabled={marking}
              className="text-[10px] px-2 py-0.5 rounded border border-emerald-200 text-emerald-700 hover:border-emerald-400 hover:bg-emerald-50 transition-colors font-mono disabled:opacity-50"
            >
              {marking ? "…" : "✓ Mark as posted"}
            </button>
          )}
        </div>
      </div>

      <div className="flex border-b border-gray-200 bg-gray-50">
        <button
          type="button"
          onClick={() => setActiveTab("twitter")}
          className={`flex-1 text-xs py-2.5 transition-colors ${activeTab === "twitter" ? "text-sky-700 border-b-2 border-sky-500 bg-sky-50" : "text-gray-500 hover:text-gray-800"}`}
        >
          𝕏 Twitter / X
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("linkedin")}
          className={`flex-1 text-xs py-2.5 transition-colors ${activeTab === "linkedin" ? "text-blue-700 border-b-2 border-blue-500 bg-blue-50" : "text-gray-500 hover:text-gray-800"}`}
        >
          in LinkedIn
        </button>
      </div>

      <div className="p-4">
        {activeTab === "twitter" ? (
          <div className="space-y-3">
            <textarea
              value={twitterText}
              onChange={(e) => setTwitterText(e.target.value)}
              rows={6}
              className="w-full bg-white border border-gray-200 rounded-lg p-3 text-sm text-gray-800 font-mono resize-y focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200 leading-relaxed"
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className={`text-xs font-mono tabular-nums ${charColor(twitterText.length)}`}>
                {twitterText.length} chars
                {twitterText.length > TWITTER_SOFT_LIMIT && <span className="ml-1 text-red-600">⚠ may be truncated</span>}
              </span>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={`${twitterText}\n\n${shareUrl}`} label="Copy post" successLabel="✓ Copied" />
                <a
                  href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`${twitterText}\n\n${shareUrl}`)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded border border-sky-200 text-sky-700 hover:border-sky-400 hover:bg-sky-50 font-mono bg-white"
                >
                  Post on X ↗
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea
              value={linkedinText}
              onChange={(e) => setLinkedinText(e.target.value)}
              rows={10}
              className="w-full bg-white border border-gray-200 rounded-lg p-3 text-sm text-gray-800 resize-y focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 leading-relaxed whitespace-pre-wrap"
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-mono text-gray-500 tabular-nums">{linkedinText.length} chars</span>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={linkedinText} label="Copy post" successLabel="✓ Copied" />
                <a
                  href={`https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${encodeURIComponent((post.title || post.source_name || "").slice(0, 200))}&summary=${encodeURIComponent(linkedinText.slice(0, 700))}&source=readyforrobots.com`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded border border-blue-200 text-blue-700 hover:border-blue-400 hover:bg-blue-50 font-mono bg-white"
                >
                  Share on LinkedIn ↗
                </a>
                {linkedinConnected && (
                  <button
                    type="button"
                    onClick={() => onPublishLinkedIn(linkedinText, shareUrl)}
                    disabled={publishing}
                    title="Requires Studio access in the panel above"
                    className="text-xs px-3 py-1.5 rounded border border-emerald-200 text-emerald-700 hover:border-emerald-400 hover:bg-emerald-50 font-mono disabled:opacity-50 bg-white"
                  >
                    {publishing ? "Publishing…" : "Publish to LinkedIn ↗"}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {post.hashtags && post.hashtags.length > 0 && (
        <div className="px-4 pb-3 flex gap-2 flex-wrap">
          {post.hashtags.map((tag) => (
            <span key={tag} className="text-[10px] font-mono text-gray-500">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Social() {
  const { session } = useAuth();
  const [posts, setPosts] = useState<SocialPost[] | null>(null);
  const [postedIds, setPostedIds] = useState<Set<number>>(new Set());
  const [currentCompanyIds, setCurrentCompanyIds] = useState<number[]>([]);
  const [currentTrendOffset, setCurrentTrendOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [apiSlow, setApiSlow] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState("");
  const [generatedAt, setGeneratedAt] = useState("");
  const [batchPosted, setBatchPosted] = useState(false);
  const [linkedinStatus, setLinkedinStatus] = useState<LinkedInStatus | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminKey, setAdminKey] = useState("");
  const [linkedinMsg, setLinkedinMsg] = useState("");
  const [linkedinMsgIsError, setLinkedinMsgIsError] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [cacheStatus, setCacheStatus] = useState<string | null>(null);

  useEffect(() => {
    document.title = "Content Studio | Ready For Robots";
    const stored = window.sessionStorage.getItem("rr_admin_key") || "";
    if (stored) setAdminKey(stored);

    const params = new URLSearchParams(window.location.search);
    const linkedinParam = params.get("linkedin");
    const detail = params.get("detail");
    if (linkedinParam === "connected") {
      setLinkedinMsg("LinkedIn connected — you can publish posts below.");
      setLinkedinMsgIsError(false);
    } else if (linkedinParam === "error") {
      setLinkedinMsg(detail ? decodeURIComponent(detail) : "LinkedIn connect failed");
      setLinkedinMsgIsError(true);
    }
    if (linkedinParam) {
      params.delete("linkedin");
      params.delete("detail");
      const next = params.toString();
      window.history.replaceState({}, "", next ? `/social?${next}` : "/social");
    }
  }, []);

  useEffect(() => {
    if (!session?.access_token) {
      setIsAdmin(false);
      return;
    }
    void fetch(`${getApiBase()}/api/user/me`, liveFetchInit({ headers: authHeader(session.access_token) }))
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setIsAdmin(Boolean(data?.is_admin)))
      .catch(() => setIsAdmin(false));
  }, [session?.access_token]);

  const fetchLinkedinStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/linkedin/status`);
      if (res.ok) setLinkedinStatus(await res.json());
    } catch {
      /* optional */
    }
  }, []);

  const persistAdminKey = (value: string) => {
    const trimmed = value.trim();
    setAdminKey(trimmed);
    if (trimmed) window.sessionStorage.setItem("rr_admin_key", trimmed);
    else window.sessionStorage.removeItem("rr_admin_key");
  };

  const clearStoredAdminKey = () => {
    window.sessionStorage.removeItem("rr_admin_key");
    setAdminKey("");
  };

  const showLinkedinMessage = (message: string, isError = false) => {
    setLinkedinMsg(message);
    setLinkedinMsgIsError(isError);
  };

  const resolveAdminKey = () => adminKey.trim();

  const studioAuthHeaders = useMemo((): Record<string, string> => {
    if (session?.access_token && isAdmin) {
      return Object.fromEntries(new Headers(authHeader(session.access_token)).entries());
    }
    const key = resolveAdminKey();
    if (key) return { "X-Admin-Key": key };
    return {};
  }, [session?.access_token, isAdmin, adminKey]);

  const studioAuthReady = Boolean(studioAuthHeaders.Authorization || studioAuthHeaders["X-Admin-Key"]);

  const connectLinkedIn = async () => {
    if (!studioAuthReady) {
      showLinkedinMessage(
        "Sign in with an admin account, or enter your Fly ADMIN_KEY below, then connect again.",
        true,
      );
      return;
    }
    setConnecting(true);
    showLinkedinMessage("");
    try {
      const returnTo = `${window.location.origin}/social`;
      const res = await fetch(`${API}/api/linkedin/connect-url?return_to=${encodeURIComponent(returnTo)}`, {
        headers: studioAuthHeaders,
      });
      let data: { auth_url?: string; detail?: string | { msg?: string } } = {};
      try {
        data = await res.json();
      } catch {
        throw new Error(`Connect failed (${res.status})`);
      }
      if (res.status === 401) {
        clearStoredAdminKey();
        throw new Error(typeof data.detail === "string" ? data.detail : "Invalid admin key — update the field below to match Fly ADMIN_KEY");
      }
      if (!res.ok) {
        const detail = typeof data.detail === "string" ? data.detail : `Connect failed (${res.status})`;
        throw new Error(detail);
      }
      if (data.auth_url) {
        if (resolveAdminKey()) persistAdminKey(resolveAdminKey());
        window.location.assign(data.auth_url);
        return;
      }
      throw new Error("LinkedIn connect URL missing from API response");
    } catch (e) {
      showLinkedinMessage(e instanceof Error ? e.message : "Connect failed", true);
    } finally {
      setConnecting(false);
    }
  };

  const publishToLinkedIn = async (text: string, articleUrl: string) => {
    if (!studioAuthReady) {
      showLinkedinMessage(
        "Sign in with an admin account, or enter your Fly ADMIN_KEY in the panel above before publishing.",
        true,
      );
      return;
    }
    showLinkedinMessage("");
    setPublishing(true);
    try {
      const res = await fetch(`${API}/api/linkedin/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...studioAuthHeaders },
        body: JSON.stringify({ commentary: text, article_url: articleUrl || undefined }),
      });
      let data: { detail?: string; published_as?: string } = {};
      try {
        data = await res.json();
      } catch {
        throw new Error(`Publish failed (${res.status})`);
      }
      if (res.status === 401) {
        clearStoredAdminKey();
        throw new Error(typeof data.detail === "string" ? data.detail : "Invalid admin key — update the field below to match Fly ADMIN_KEY");
      }
      if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Publish failed (${res.status})`);
      if (resolveAdminKey()) persistAdminKey(resolveAdminKey());
      showLinkedinMessage(`Published to LinkedIn (${data.published_as || "ok"})`);
    } catch (e) {
      showLinkedinMessage(e instanceof Error ? e.message : "Publish failed", true);
    } finally {
      setPublishing(false);
    }
  };

  const applyData = (data: {
    posts?: SocialPost[];
    posted_company_ids?: number[];
    trend_offset?: number;
    date?: string;
    generated_at?: string;
    cache_pending?: boolean;
    message?: string;
  }) => {
    if (data.cache_pending) {
      if ((data.posts || []).length) {
        setPosts(data.posts || []);
        setCurrentCompanyIds(data.posted_company_ids || []);
        setCurrentTrendOffset(data.trend_offset || 0);
        setDate(data.date || "");
        if (data.generated_at) {
          setGeneratedAt(new Date(data.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
        }
      }
      setError(data.message || "Content is being prepared in the background. Retrying shortly.");
      return;
    }
    setPosts(data.posts || []);
    setCurrentCompanyIds(data.posted_company_ids || []);
    setCurrentTrendOffset(data.trend_offset || 0);
    setDate(data.date || "");
    if (data.generated_at) {
      setGeneratedAt(new Date(data.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    }
    setBatchPosted(false);
    setPostedIds(new Set());
  };

  const fetchPosts = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent === true;
    const cachedEntry =
      readSurfaceCache<{ posts?: SocialPost[]; date?: string; generated_at?: string }>(
        SOCIAL_SESSION_KEY,
        SOCIAL_SESSION_TTL_MS,
      )
      ?? readSurfaceCache<{ posts?: SocialPost[]; date?: string; generated_at?: string }>(
        SOCIAL_SESSION_KEY,
        SOCIAL_STALE_PAINT_MS,
      );
    if (cachedEntry?.data?.posts?.length) {
      applyData(cachedEntry.data);
      setLoading(false);
      setApiSlow(false);
    }

    try {
      if (!cachedEntry?.data?.posts?.length) {
        setLoading(true);
        setApiSlow(false);
      }
      setError(null);
      setCacheStatus(null);
      const res = await socialPostFetch("/api/social/daily-posts");
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(detail.slice(0, 160) || `API error ${res.status}`);
      }
      const data = await res.json();
      if ((data.posts || []).length) {
        writeSurfaceCache(SOCIAL_SESSION_KEY, data);
      }
      setCacheStatus(
        data.cache_status === "stale" || res.headers.get("X-Social-Cache") === "stale"
          ? "stale"
          : null,
      );
      applyData(data);
      setApiSlow(false);
      if (data.cache_pending) {
        setApiSlow(true);
        window.setTimeout(() => {
          void fetchPosts({ silent: true });
        }, SOCIAL_RETRY_MS);
      }
    } catch (e) {
      if (!cachedEntry?.data?.posts?.length) {
        setError(e instanceof Error ? e.message : "Failed to load");
        setApiSlow(true);
        window.setTimeout(() => {
          void fetchPosts({ silent: true });
        }, SOCIAL_RETRY_MS);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPosts();
    fetchLinkedinStatus();
  }, [fetchPosts, fetchLinkedinStatus]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const li = params.get("linkedin");
    if (li === "connected") {
      showLinkedinMessage("LinkedIn connected.");
      fetchLinkedinStatus();
      window.history.replaceState({}, "", "/social");
    } else if (li === "error") {
      showLinkedinMessage(params.get("detail") || "LinkedIn connect failed", true);
      window.history.replaceState({}, "", "/social");
    }
  }, [fetchLinkedinStatus]);

  const getNewPosts = async () => {
    try {
      setRefreshing(true);
      setError(null);
      const leadIds = currentCompanyIds.filter((id) => id != null);
      if (leadIds.length > 0) {
        await socialPostFetch(
          "/api/social/daily-posts/mark-posted",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ company_ids: leadIds }),
          },
          30_000,
        );
      }
      const res = await socialPostFetch(
        "/api/social/daily-posts/refresh",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ exclude_ids: leadIds, trend_offset: currentTrendOffset + 1 }),
        },
        SOCIAL_REFRESH_MS,
      );
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(detail.slice(0, 160) || `API error ${res.status}`);
      }
      const data = await res.json();
      if (!data.posts?.length) {
        throw new Error("No posts returned — try again in a minute.");
      }
      applyData(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  };

  const markAllPosted = async () => {
    const leadIds = currentCompanyIds.filter((id) => id != null);
    if (leadIds.length > 0) {
      await fetch(`${API}/api/social/daily-posts/mark-posted`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_ids: leadIds }),
      });
    }
    setPostedIds(new Set(currentCompanyIds));
    setBatchPosted(true);
  };

  const handleMarkOnePosted = async (post: SocialPost) => {
    if (!post.company_id) return;
    await fetch(`${API}/api/social/daily-posts/mark-posted`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_ids: [post.company_id], post_types: [post.type] }),
    });
    setPostedIds((prev) => {
      const next = new Set(prev);
      next.add(post.company_id!);
      return next;
    });
  };

  const postedCount = postedIds.size;
  const totalLeadPosts = (posts || []).filter((p) => p.company_id != null).length;

  return (
    <div className="admin-workspace social-page min-h-screen">
      <Header />
      <PageHeroDark
        maxWidthClass="max-w-4xl"
        eyebrow="Content Studio"
        title="Daily Content Queue"
        description="Five SIGNAL-powered posts from today's hottest leads — edit, copy, publish to LinkedIn, or post to X."
        stats={[
          { label: "Posts / day", value: posts?.length ?? "5", tone: "emerald" },
          { label: "Marked", value: `${postedCount}/${totalLeadPosts || "—"}`, tone: "amber" },
          { label: "Refresh", value: "4h", tone: "white" },
        ]}
        innerClassName="pb-4 pt-20"
      />
      <div className="page-hero-fade -mt-2" aria-hidden />
      <main className="max-w-4xl mx-auto px-4 pb-8 pt-4">
        <AdminNav />
        <div className="mb-6 flex flex-wrap items-center justify-between gap-2 text-[11px] text-gray-600 font-mono">
          {date && <span>{date}</span>}
          {generatedAt && <span>Generated {generatedAt}</span>}
        </div>
        {cacheStatus === "stale" && (
          <p className="mb-3 text-xs text-amber-800 font-medium rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            Showing cached posts while a fresh batch generates in the background.
          </p>
        )}
        {apiSlow && !error && (
          <p className="mb-3 text-xs text-amber-800 font-medium rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            SIGNAL API is catching up — showing cached posts and retrying in the background.
          </p>
        )}

        <div className="workspace-panel-dark mb-6 p-4 sm:p-5">
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-sm font-semibold text-white">LinkedIn publishing setup</p>
              <p className="text-xs text-slate-300 mt-1 max-w-2xl">
                Step 1: authenticate Content Studio. Step 2: connect LinkedIn. Step 3: use{" "}
                <strong className="text-white">Publish to LinkedIn</strong> on any post below.
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">1 · Studio access</p>
                {studioAuthReady ? (
                  <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
                    {session?.access_token && isAdmin ? "Admin session" : "Admin key set"}
                  </span>
                ) : (
                  <span className="rounded-full bg-amber-500/20 px-2.5 py-0.5 text-[10px] font-bold text-amber-200">
                    Required
                  </span>
                )}
              </div>
              {session?.access_token && isAdmin ? (
                <p className="text-xs text-emerald-300">
                  Signed in as admin ({session.user.email}) — no admin key needed unless you prefer one.
                </p>
              ) : session?.access_token ? (
                <p className="text-xs text-amber-200">
                  Signed in, but this account is not in ADMIN_EMAILS — paste your Fly ADMIN_KEY below.
                </p>
              ) : (
                <p className="text-xs text-slate-400">
                  Not signed in — paste your Fly <code className="text-slate-200">ADMIN_KEY</code> below, or{" "}
                  <Link href="/login?next=/social" className="text-emerald-300 underline underline-offset-2">
                    sign in as admin
                  </Link>
                  .
                </p>
              )}
              <label className="flex flex-col gap-1.5">
                <span className="text-[10px] uppercase tracking-wide text-slate-500">Admin key (Fly ADMIN_KEY)</span>
                <input
                  type="password"
                  value={adminKey}
                  onChange={(e) => persistAdminKey(e.target.value)}
                  placeholder="Paste ADMIN_KEY — not the fly secrets list digest"
                  autoComplete="off"
                  className="w-full max-w-md text-xs px-3 py-2 rounded-lg border border-white/15 bg-[#0b1020] text-white font-mono placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30"
                />
              </label>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">2 · LinkedIn account</p>
                {linkedinStatus?.connected ? (
                  <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
                    Connected
                  </span>
                ) : linkedinStatus?.configured ? (
                  <span className="rounded-full bg-amber-500/20 px-2.5 py-0.5 text-[10px] font-bold text-amber-200">
                    Not connected
                  </span>
                ) : null}
              </div>
              <p className="text-xs text-slate-300">
                {linkedinStatus?.connected
                  ? linkedinStatus.member_posting
                    ? `Publishing as ${linkedinStatus.member_name || "your profile"} (personal feed until company page API is active).`
                    : `Connected · company page ${linkedinStatus.organization_urn || linkedinStatus.organization_id}`
                  : linkedinStatus?.configured
                    ? "Connect once to enable one-click publish from post cards."
                    : "LinkedIn app credentials are not configured on the API server yet."}
              </p>
              {linkedinStatus?.organization_page_status &&
                linkedinStatus.organization_page_status !== "active" && (
                  <p className="text-[11px] text-amber-200/90 leading-relaxed">
                    {linkedinStatus.organization_page_status}
                  </p>
                )}
              {linkedinMsg && (
                <p className={`text-xs font-mono ${linkedinMsgIsError ? "text-red-400" : "text-emerald-400"}`}>
                  {linkedinMsg}
                </p>
              )}
              <div className="flex flex-wrap gap-2 items-center">
                <a
                  href={linkedinStatus?.organization_url || "https://www.linkedin.com/company/114404417/admin/dashboard/"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded-lg border border-white/15 text-slate-300 hover:text-white hover:bg-white/10 bg-white/5"
                >
                  Open Page Admin ↗
                </a>
                {linkedinStatus?.configured && (
                  <button
                    type="button"
                    onClick={connectLinkedIn}
                    disabled={connecting || !studioAuthReady}
                    className="text-xs px-3 py-1.5 rounded-lg border border-blue-400/40 text-blue-100 hover:border-blue-400 hover:bg-blue-500/10 bg-white/5 disabled:opacity-40"
                  >
                    {connecting
                      ? "Connecting…"
                      : linkedinStatus?.connected
                        ? "Reconnect LinkedIn"
                        : "Connect LinkedIn"}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {!loading && !error && posts && posts.length > 0 && (
          <div className="mb-6 flex items-center justify-between gap-3 flex-wrap p-4 border border-gray-200 rounded-xl bg-white shadow-sm">
            <span className="text-xs text-gray-600">
              {batchPosted ? "✓ All posts marked as shared" : `${postedCount} of ${totalLeadPosts} lead posts marked`}
            </span>
            <div className="flex gap-2">
              <button type="button" onClick={markAllPosted} disabled={batchPosted || refreshing} className="text-xs px-3 py-1.5 rounded border border-emerald-200 text-emerald-700 hover:bg-emerald-50 disabled:opacity-40 bg-white">
                ✓ Mark all as posted
              </button>
              <button type="button" onClick={getNewPosts} disabled={refreshing || loading} className="text-xs px-4 py-1.5 rounded border border-violet-200 text-violet-700 hover:bg-violet-50 disabled:opacity-50 font-semibold bg-white">
                {refreshing ? "⟳ Generating…" : "⟳ Get New Posts"}
              </button>
            </div>
          </div>
        )}

        {refreshing && (
          <div className="mb-4 p-3 border border-violet-200 rounded-xl bg-violet-50 text-xs text-violet-800 font-mono">
            Generating a fresh batch — usually takes 30–60 seconds. Your current posts stay visible below.
          </div>
        )}

        {loading && !posts?.length && (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="border border-gray-200 rounded-xl h-48 animate-pulse bg-gray-100" />
            ))}
          </div>
        )}

        {error && !loading && !refreshing && !posts?.length && (
          <div className="border border-red-200 bg-red-50 rounded-xl p-6 text-center">
            <p className="text-red-700 text-sm mb-3">Failed to load posts: {error}</p>
            <button type="button" onClick={() => void fetchPosts()} className="text-xs border border-gray-300 px-3 py-1.5 rounded bg-white text-gray-700 hover:bg-gray-50">
              Try again
            </button>
          </div>
        )}

        {!loading && !error && posts && posts.length > 0 && (
          <div className={`space-y-6 ${refreshing ? "opacity-60 pointer-events-none" : ""}`}>
            {posts.map((post, i) => (
              <PostCard
                key={`${post.company_id || post.type}-${i}`}
                post={post}
                index={i}
                onMarkPosted={handleMarkOnePosted}
                isPosted={post.company_id != null && postedIds.has(post.company_id)}
                linkedinConnected={Boolean(linkedinStatus?.connected)}
                onPublishLinkedIn={publishToLinkedIn}
                publishing={publishing}
              />
            ))}
            <div className="border border-gray-200 bg-white rounded-xl p-4 text-center text-xs text-gray-600 space-y-2 shadow-sm">
              <p>Posts refresh every 4 hours. Mark as posted to rotate companies for 7 days.</p>
              <div className="flex justify-center gap-4">
                <Link href="/pipeline" className="text-emerald-700 hover:text-emerald-900 font-semibold">
                  View Pipeline →
                </Link>
                <Link href="/newsletter" className="text-sky-700 hover:text-sky-900 font-semibold">
                  View Newsletter →
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
