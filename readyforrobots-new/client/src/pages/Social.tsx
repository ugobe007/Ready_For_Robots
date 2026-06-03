/**
 * Content Studio — daily social posts from /api/social/daily-posts + LinkedIn publish.
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { getApiBase, getDirectApiBase, liveFetchInit } from "@/lib/apiBase";

/** Social generation can exceed Vercel proxy limits — call Fly directly from marketing site. */
const API = typeof window !== "undefined" ? getDirectApiBase() : getApiBase();
const SOCIAL_FETCH_MS = 150_000;

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
  organization_url?: string;
};

const POST_TYPE_META: Record<
  PostType,
  { label: string; border: string; text: string; bg: string }
> = {
  hot_lead: { label: "🔥 Buyer Spotlight", border: "border-red-800", text: "text-red-400", bg: "bg-red-950/30" },
  signal_alert: { label: "📊 Buyer Alert", border: "border-amber-800", text: "text-amber-400", bg: "bg-amber-950/30" },
  industry_insight: { label: "🧠 Industry Brief", border: "border-cyan-800", text: "text-cyan-400", bg: "bg-cyan-950/20" },
  market_trend: { label: "📈 Market Trend", border: "border-violet-800", text: "text-violet-400", bg: "bg-violet-950/20" },
  thought_leadership: { label: "🤖 Thought Leadership", border: "border-emerald-800", text: "text-emerald-400", bg: "bg-emerald-950/20" },
};

const TWITTER_SOFT_LIMIT = 257;

function charColor(len: number) {
  if (len <= 200) return "text-emerald-400";
  if (len <= 240) return "text-yellow-400";
  return "text-red-400";
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
          ? "border-emerald-600 text-emerald-400 bg-emerald-950/40"
          : "border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-300"
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
    <div className={`border ${isPosted ? "border-neutral-800 opacity-60" : meta.border} rounded-xl overflow-hidden transition-opacity`}>
      <div className={`${isPosted ? "bg-neutral-900/20" : meta.bg} border-b ${isPosted ? "border-neutral-800" : meta.border} px-4 py-3 flex items-center justify-between gap-3 flex-wrap`}>
        <div className="flex items-center gap-3">
          <span className="text-neutral-500 font-mono text-xs tabular-nums">#{index + 1}</span>
          <span className={`text-sm font-semibold ${isPosted ? "text-neutral-500" : meta.text}`}>
            {isPosted ? "✓ Posted — " : ""}
            {meta.label}
          </span>
          {post.source_name && <span className="text-xs text-neutral-400 truncate max-w-[200px]">{post.source_name}</span>}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {post.source_industry && (
            <span className="text-[10px] border border-neutral-700 text-neutral-500 px-2 py-0.5 rounded font-mono">{post.source_industry}</span>
          )}
          {post.score != null && (
            <span className="text-[10px] border border-neutral-700 text-neutral-500 px-2 py-0.5 rounded font-mono">Score {post.score}/100</span>
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
              className="text-[10px] px-2 py-0.5 rounded border border-emerald-900 text-emerald-600 hover:border-emerald-700 hover:text-emerald-400 transition-colors font-mono disabled:opacity-50"
            >
              {marking ? "…" : "✓ Mark as posted"}
            </button>
          )}
        </div>
      </div>

      <div className="flex border-b border-neutral-800">
        <button
          type="button"
          onClick={() => setActiveTab("twitter")}
          className={`flex-1 text-xs py-2.5 transition-colors ${activeTab === "twitter" ? "text-sky-400 border-b-2 border-sky-500 bg-sky-950/20" : "text-neutral-500 hover:text-neutral-300"}`}
        >
          𝕏 Twitter / X
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("linkedin")}
          className={`flex-1 text-xs py-2.5 transition-colors ${activeTab === "linkedin" ? "text-blue-400 border-b-2 border-blue-500 bg-blue-950/20" : "text-neutral-500 hover:text-neutral-300"}`}
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
              className="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-3 text-sm text-neutral-200 font-mono resize-y focus:outline-none focus:border-sky-700 leading-relaxed"
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className={`text-xs font-mono tabular-nums ${charColor(twitterText.length)}`}>
                {twitterText.length} chars
                {twitterText.length > TWITTER_SOFT_LIMIT && <span className="ml-1 text-red-400">⚠ may be truncated</span>}
              </span>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={`${twitterText}\n\n${shareUrl}`} label="Copy post" successLabel="✓ Copied" />
                <a
                  href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`${twitterText}\n\n${shareUrl}`)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded border border-sky-800 text-sky-400 hover:border-sky-600 font-mono"
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
              className="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-3 text-sm text-neutral-200 resize-y focus:outline-none focus:border-blue-700 leading-relaxed whitespace-pre-wrap"
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-mono text-neutral-500 tabular-nums">{linkedinText.length} chars</span>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={linkedinText} label="Copy post" successLabel="✓ Copied" />
                <a
                  href={`https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${encodeURIComponent((post.title || post.source_name || "").slice(0, 200))}&summary=${encodeURIComponent(linkedinText.slice(0, 700))}&source=readyforrobots.com`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded border border-blue-800 text-blue-400 hover:border-blue-600 font-mono"
                >
                  Share on LinkedIn ↗
                </a>
                {linkedinConnected && (
                  <button
                    type="button"
                    onClick={() => onPublishLinkedIn(linkedinText, shareUrl)}
                    disabled={publishing}
                    className="text-xs px-3 py-1.5 rounded border border-emerald-800 text-emerald-400 hover:border-emerald-600 font-mono disabled:opacity-50"
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
            <span key={tag} className="text-[10px] font-mono text-neutral-600">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Social() {
  const [posts, setPosts] = useState<SocialPost[] | null>(null);
  const [postedIds, setPostedIds] = useState<Set<number>>(new Set());
  const [currentCompanyIds, setCurrentCompanyIds] = useState<number[]>([]);
  const [currentTrendOffset, setCurrentTrendOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState("");
  const [generatedAt, setGeneratedAt] = useState("");
  const [batchPosted, setBatchPosted] = useState(false);
  const [linkedinStatus, setLinkedinStatus] = useState<LinkedInStatus | null>(null);
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
  }, []);

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

  const connectLinkedIn = async () => {
    const key = resolveAdminKey();
    if (!key) {
      showLinkedinMessage("Enter your admin key below, then click Connect LinkedIn again.", true);
      return;
    }
    setConnecting(true);
    showLinkedinMessage("");
    try {
      const returnTo = `${window.location.origin}/social`;
      const res = await fetch(`${API}/api/linkedin/connect-url?return_to=${encodeURIComponent(returnTo)}`, {
        headers: { "X-Admin-Key": key },
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
        persistAdminKey(key);
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
    const key = resolveAdminKey();
    if (!key) {
      showLinkedinMessage("Enter your admin key in the LinkedIn panel before publishing.", true);
      return;
    }
    showLinkedinMessage("");
    setPublishing(true);
    try {
      const res = await fetch(`${API}/api/linkedin/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Admin-Key": key },
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
      persistAdminKey(key);
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
  }) => {
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

  const fetchPosts = useCallback(async () => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), SOCIAL_FETCH_MS);
    try {
      setLoading(true);
      setError(null);
      setCacheStatus(null);
      const res = await fetch(
        `${API}/api/social/daily-posts`,
        liveFetchInit({ signal: controller.signal }),
      );
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(detail.slice(0, 160) || `API error ${res.status}`);
      }
      const data = await res.json();
      setCacheStatus(
        data.cache_status === "stale" || res.headers.get("X-Social-Cache") === "stale"
          ? "stale"
          : null,
      );
      applyData(data);
    } catch (e) {
      const msg =
        e instanceof Error && e.name === "AbortError"
          ? "Request timed out — try again in a minute (cache may still be warming)"
          : e instanceof Error
            ? e.message
            : "Failed to load";
      setError(msg);
    } finally {
      window.clearTimeout(timer);
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
        await fetch(`${API}/api/social/daily-posts/mark-posted`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ company_ids: leadIds }),
        });
      }
      const res = await fetch(`${API}/api/social/daily-posts/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exclude_ids: leadIds, trend_offset: currentTrendOffset + 1 }),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      applyData(await res.json());
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
    setPostedIds((prev) => new Set([...prev, post.company_id!]));
  };

  const postedCount = postedIds.size;
  const totalLeadPosts = (posts || []).filter((p) => p.company_id != null).length;

  return (
    <div className="min-h-screen bg-[#0d0520] text-white">
      <Header />
      <main className="max-w-4xl mx-auto px-4 py-8 pt-24">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#03DAC5] mb-2">Content Studio</p>
          <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
            <h1 className="text-2xl font-bold">Daily Content Queue</h1>
            <div className="text-[11px] text-white/40 font-mono flex gap-x-3">
              {date && <span>{date}</span>}
              {generatedAt && <span>Generated {generatedAt}</span>}
            </div>
          </div>
          <p className="text-sm text-white/55 max-w-2xl">
            Five posts from today&apos;s hot leads and strategic insights. Edit, copy, share, or publish to LinkedIn.
          </p>
          {cacheStatus === "stale" && (
            <p className="mt-2 text-xs text-amber-400/90 font-mono">
              Showing cached posts while a fresh batch generates in the background.
            </p>
          )}
        </div>

        <div className="mb-6 p-4 border border-blue-900/60 rounded-xl bg-blue-950/20">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-blue-300">LinkedIn Publishing</p>
              <p className="text-xs text-neutral-400 mt-1">
                {linkedinStatus?.connected
                  ? linkedinStatus.member_posting
                    ? `Connected as ${linkedinStatus.member_name || "your profile"} — personal feed until Marketing API is approved.`
                    : `Connected · company page org ${linkedinStatus.organization_id}`
                  : linkedinStatus?.configured
                    ? "Not connected — sign in with LinkedIn to enable one-click publish"
                    : "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET on the API server"}
              </p>
              {linkedinMsg && (
                <p className={`text-xs mt-2 font-mono ${linkedinMsgIsError ? "text-red-400" : "text-emerald-400"}`}>{linkedinMsg}</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap items-end">
              {!linkedinStatus?.connected && (
                <label className="flex flex-col gap-1 min-w-[220px]">
                  <span className="text-[10px] uppercase tracking-wide text-neutral-500">Admin key</span>
                  <input
                    type="password"
                    value={adminKey}
                    onChange={(e) => persistAdminKey(e.target.value)}
                    placeholder="Same as Fly ADMIN_KEY"
                    autoComplete="off"
                    className="text-xs px-3 py-1.5 rounded border border-neutral-700 bg-neutral-950 text-neutral-200 font-mono"
                  />
                </label>
              )}
              <a
                href={linkedinStatus?.organization_url || "https://www.linkedin.com/company/114404417/admin/dashboard/"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs px-3 py-1.5 rounded border border-neutral-700 text-neutral-400 hover:text-neutral-200"
              >
                Open Page Admin ↗
              </a>
              {!linkedinStatus?.connected && (
                <button
                  type="button"
                  onClick={connectLinkedIn}
                  disabled={connecting}
                  className="text-xs px-3 py-1.5 rounded border border-blue-700 text-blue-300 hover:border-blue-500 disabled:opacity-50"
                >
                  {connecting ? "Connecting…" : "Connect LinkedIn"}
                </button>
              )}
            </div>
          </div>
        </div>

        {!loading && !error && posts && posts.length > 0 && (
          <div className="mb-6 flex items-center justify-between gap-3 flex-wrap p-4 border border-neutral-800 rounded-xl bg-neutral-900/30">
            <span className="text-xs text-neutral-500">
              {batchPosted ? "✓ All posts marked as shared" : `${postedCount} of ${totalLeadPosts} lead posts marked`}
            </span>
            <div className="flex gap-2">
              <button type="button" onClick={markAllPosted} disabled={batchPosted || refreshing} className="text-xs px-3 py-1.5 rounded border border-emerald-900 text-emerald-500 disabled:opacity-40">
                ✓ Mark all as posted
              </button>
              <button type="button" onClick={getNewPosts} disabled={refreshing || loading} className="text-xs px-4 py-1.5 rounded border border-violet-700 text-violet-400 disabled:opacity-50 font-semibold">
                {refreshing ? "⟳ Generating…" : "⟳ Get New Posts"}
              </button>
            </div>
          </div>
        )}

        {(loading || refreshing) && (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="border border-neutral-800 rounded-xl h-48 animate-pulse bg-neutral-900/40" />
            ))}
          </div>
        )}

        {error && !loading && !refreshing && (
          <div className="border border-red-900 rounded-xl p-6 text-center">
            <p className="text-red-400 text-sm mb-3">Failed to load posts: {error}</p>
            <button type="button" onClick={fetchPosts} className="text-xs border border-neutral-700 px-3 py-1.5 rounded">
              Try again
            </button>
          </div>
        )}

        {!loading && !refreshing && !error && posts && (
          <div className="space-y-6">
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
            <div className="border border-neutral-800 rounded-xl p-4 text-center text-xs text-neutral-600 space-y-2">
              <p>Posts refresh every 4 hours. Mark as posted to rotate companies for 7 days.</p>
              <div className="flex justify-center gap-4">
                <Link href="/pipeline" className="text-emerald-400 hover:text-emerald-300">
                  View Pipeline →
                </Link>
                <Link href="/newsletter" className="text-cyan-400 hover:text-cyan-300">
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
