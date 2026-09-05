/**
 * Content Studio — Daily Social Media Post Generator
 * Pulls 5 ready-to-post items from /api/social/daily-posts.
 * Each post has Twitter (X) and LinkedIn variants with editable text + copy/share.
 * "Get New Posts" skips already-posted leads so content stays fresh.
 */
import { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { getApiBase } from '../lib/apiBase';
import RrSiteLayout from '../components/RrSiteLayout';

const API = getApiBase();

const POST_TYPE_META = {
  hot_lead:           { label: '🔥 Hot Lead Spotlight',    border: 'border-red-800',    text: 'text-red-400',     bg: 'bg-red-950/30' },
  signal_alert:       { label: '📊 Signal Alert',          border: 'border-amber-800',  text: 'text-amber-400',   bg: 'bg-amber-950/30' },
  industry_insight:   { label: '🧠 Industry Intelligence', border: 'border-cyan-800',   text: 'text-cyan-400',    bg: 'bg-cyan-950/20' },
  market_trend:       { label: '📈 Market Trend',          border: 'border-violet-800', text: 'text-violet-400',  bg: 'bg-violet-950/20' },
  thought_leadership: { label: '🤖 Thought Leadership',    border: 'border-emerald-800',text: 'text-emerald-400', bg: 'bg-emerald-950/20' },
};

const TWITTER_SOFT_LIMIT = 257;

function charColor(len) {
  if (len <= 200) return 'text-emerald-400';
  if (len <= 240) return 'text-yellow-400';
  return 'text-red-400';
}

function CopyButton({ text, label = 'Copy', successLabel = 'Copied!' }) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handle}
      className={`text-xs px-3 py-1.5 rounded border transition-colors font-mono ${
        copied
          ? 'border-emerald-600 text-emerald-400 bg-emerald-950/40'
          : 'border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-300'
      }`}
    >
      {copied ? successLabel : label}
    </button>
  );
}

function TwitterShareButton({ text, url }) {
  const encoded = encodeURIComponent(`${text}\n\n${url}`);
  return (
    <a
      href={`https://twitter.com/intent/tweet?text=${encoded}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-xs px-3 py-1.5 rounded border border-sky-800 text-sky-400 hover:border-sky-600 hover:text-sky-300 transition-colors font-mono"
    >
      Post on X ↗
    </a>
  );
}

function LinkedInShareButton({ url, title, summary }) {
  const liUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(url)}${title ? `&title=${encodeURIComponent(title.slice(0, 200))}` : ''}${summary ? `&summary=${encodeURIComponent(summary.slice(0, 700))}` : ''}&source=readyforrobots.com`;
  return (
    <a
      href={liUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="text-xs px-3 py-1.5 rounded border border-blue-800 text-blue-400 hover:border-blue-600 hover:text-blue-300 transition-colors font-mono"
    >
      Post on LinkedIn ↗
    </a>
  );
}

function PostCard({ post, index, onMarkPosted, isPosted, linkedinConnected, onPublishLinkedIn, publishing }) {
  const meta = POST_TYPE_META[post.type] || POST_TYPE_META.thought_leadership;
  const [activeTab, setActiveTab] = useState('twitter');
  const [twitterText, setTwitterText] = useState(post.twitter || '');
  const [linkedinText, setLinkedinText] = useState(post.linkedin || '');
  const [marking, setMarking] = useState(false);

  const twitterLen = twitterText.length;
  const shareUrl = post.share_url || 'https://readyforrobots.com';

  const handleMarkPosted = async () => {
    setMarking(true);
    await onMarkPosted(post);
    setMarking(false);
  };

  return (
    <div className={`border ${isPosted ? 'border-neutral-800 opacity-60' : meta.border} rounded-xl overflow-hidden transition-opacity`}>
      {/* Card header */}
      <div className={`${isPosted ? 'bg-neutral-900/20' : meta.bg} border-b ${isPosted ? 'border-neutral-800' : meta.border} px-4 py-3 flex items-center justify-between gap-3 flex-wrap`}>
        <div className="flex items-center gap-3">
          <span className="text-neutral-500 font-mono text-xs tabular-nums">#{index + 1}</span>
          <span className={`text-sm font-semibold ${isPosted ? 'text-neutral-500' : meta.text}`}>
            {isPosted ? '✓ Posted — ' : ''}{meta.label}
          </span>
          {post.source_name && (
            <span className="text-xs text-neutral-400 truncate max-w-[200px]">{post.source_name}</span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {post.source_industry && (
            <span className="text-[10px] border border-neutral-700 text-neutral-500 px-2 py-0.5 rounded font-mono">
              {post.source_industry}
            </span>
          )}
          {post.score != null && (
            <span className="text-[10px] border border-neutral-700 text-neutral-500 px-2 py-0.5 rounded font-mono">
              Score {post.score}/100
            </span>
          )}
          {!isPosted && post.company_id && (
            <button
              onClick={handleMarkPosted}
              disabled={marking}
              className="text-[10px] px-2 py-0.5 rounded border border-emerald-900 text-emerald-600 hover:border-emerald-700 hover:text-emerald-400 transition-colors font-mono disabled:opacity-50"
            >
              {marking ? '…' : '✓ Mark as posted'}
            </button>
          )}
        </div>
      </div>

      {/* Tab selector */}
      <div className="flex border-b border-neutral-800">
        <button
          onClick={() => setActiveTab('twitter')}
          className={`flex-1 text-xs py-2.5 transition-colors ${
            activeTab === 'twitter'
              ? 'text-sky-400 border-b-2 border-sky-500 bg-sky-950/20'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          𝕏 Twitter / X
        </button>
        <button
          onClick={() => setActiveTab('linkedin')}
          className={`flex-1 text-xs py-2.5 transition-colors ${
            activeTab === 'linkedin'
              ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-950/20'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          in LinkedIn
        </button>
      </div>

      {/* Content area */}
      <div className="p-4">
        {activeTab === 'twitter' ? (
          <div className="space-y-3">
            <textarea
              value={twitterText}
              onChange={e => setTwitterText(e.target.value)}
              rows={6}
              className="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-3 text-sm text-neutral-200 font-mono resize-y focus:outline-none focus:border-sky-700 leading-relaxed"
              placeholder="Twitter post text..."
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <span className={`text-xs font-mono tabular-nums ${charColor(twitterLen)}`}>
                  {twitterLen} chars
                  {twitterLen > TWITTER_SOFT_LIMIT && (
                    <span className="ml-1 text-red-400">⚠ may be truncated</span>
                  )}
                </span>
                <span className="text-[10px] text-neutral-600">+~23 for URL</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={`${twitterText}\n\n${shareUrl}`} label="Copy post" successLabel="✓ Copied" />
                <TwitterShareButton text={twitterText} url={shareUrl} />
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea
              value={linkedinText}
              onChange={e => setLinkedinText(e.target.value)}
              rows={10}
              className="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-3 text-sm text-neutral-200 resize-y focus:outline-none focus:border-blue-700 leading-relaxed whitespace-pre-wrap"
              placeholder="LinkedIn post text..."
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-mono text-neutral-500 tabular-nums">
                {linkedinText.length} chars
              </span>
              <div className="flex gap-2 flex-wrap">
                <CopyButton text={linkedinText} label="Copy post" successLabel="✓ Copied" />
                <LinkedInShareButton url={shareUrl} title={post.title || post.company_name} summary={linkedinText} />
                {linkedinConnected && onPublishLinkedIn && (
                  <button
                    type="button"
                    onClick={() => onPublishLinkedIn(linkedinText, shareUrl)}
                    disabled={publishing}
                    className="text-xs px-3 py-1.5 rounded border border-emerald-800 text-emerald-400 hover:border-emerald-600 hover:text-emerald-300 transition-colors font-mono disabled:opacity-50"
                  >
                    {publishing ? 'Publishing…' : 'Publish to LinkedIn ↗'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hashtags */}
      {post.hashtags && post.hashtags.length > 0 && (
        <div className="px-4 pb-3 flex gap-2 flex-wrap">
          {post.hashtags.map(tag => (
            <span key={tag} className="text-[10px] font-mono text-neutral-600">#{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SocialContentStudio() {
  const [posts, setPosts] = useState(null);
  const [postedIds, setPostedIds] = useState(new Set());
  const [currentCompanyIds, setCurrentCompanyIds] = useState([]);
  const [currentTrendOffset, setCurrentTrendOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [date, setDate] = useState('');
  const [generatedAt, setGeneratedAt] = useState('');
  const [batchPosted, setBatchPosted] = useState(false);
  const [linkedinStatus, setLinkedinStatus] = useState(null);
  const [adminKey, setAdminKey] = useState('');
  const [linkedinMsg, setLinkedinMsg] = useState('');
  const [publishingIdx, setPublishingIdx] = useState(null);

  const fetchLinkedinStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/linkedin/status`);
      if (res.ok) setLinkedinStatus(await res.json());
    } catch {
      /* optional */
    }
  }, []);

  const getAdminKey = () => {
    if (adminKey.trim()) return adminKey.trim();
    if (typeof window !== 'undefined') {
      const stored = window.sessionStorage.getItem('rr_admin_key') || '';
      if (stored) return stored;
    }
    const entered = window.prompt('Admin key (X-Admin-Key) for LinkedIn connect/publish:');
    if (entered) {
      window.sessionStorage.setItem('rr_admin_key', entered);
      setAdminKey(entered);
      return entered;
    }
    return '';
  };

  const connectLinkedIn = async () => {
    const key = getAdminKey();
    if (!key) return;
    setLinkedinMsg('');
    try {
      const returnTo = typeof window !== 'undefined' ? `${window.location.origin}/social` : 'https://readyforrobots.com/social';
      const res = await fetch(`${API}/api/linkedin/connect-url?return_to=${encodeURIComponent(returnTo)}`, {
        headers: { 'X-Admin-Key': key },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Connect failed (${res.status})`);
      if (data.auth_url) window.location.href = data.auth_url;
    } catch (e) {
      setLinkedinMsg(e.message);
    }
  };

  const publishToLinkedIn = async (text, articleUrl) => {
    const key = getAdminKey();
    if (!key) return;
    setLinkedinMsg('');
    setPublishingIdx(true);
    try {
      const res = await fetch(`${API}/api/linkedin/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Key': key },
        body: JSON.stringify({ commentary: text, article_url: articleUrl || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Publish failed (${res.status})`);
      setLinkedinMsg(`Published to LinkedIn (${data.published_as || 'ok'}${data.note ? ' — personal feed' : ''})`);
    } catch (e) {
      setLinkedinMsg(e.message);
    } finally {
      setPublishingIdx(null);
    }
  };

  const applyData = (data) => {
    setPosts(data.posts || []);
    setCurrentCompanyIds(data.posted_company_ids || []);
    setCurrentTrendOffset(data.trend_offset || 0);
    setDate(data.date || '');
    if (data.generated_at) {
      const d = new Date(data.generated_at);
      setGeneratedAt(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    }
    setBatchPosted(false);
    setPostedIds(new Set());
  };

  const fetchPosts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API}/api/social/daily-posts`);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      applyData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const getNewPosts = async () => {
    try {
      setRefreshing(true);
      setError(null);

      // Mark current lead posts before skipping them
      const leadIds = currentCompanyIds.filter(id => id != null);
      if (leadIds.length > 0) {
        await fetch(`${API}/api/social/daily-posts/mark-posted`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ company_ids: leadIds }),
        });
      }

      const res = await fetch(`${API}/api/social/daily-posts/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exclude_ids: leadIds,
          trend_offset: currentTrendOffset + 1,
        }),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      applyData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  const markAllPosted = async () => {
    const leadIds = currentCompanyIds.filter(id => id != null);
    if (leadIds.length > 0) {
      await fetch(`${API}/api/social/daily-posts/mark-posted`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_ids: leadIds }),
      });
    }
    setPostedIds(new Set(currentCompanyIds));
    setBatchPosted(true);
  };

  const handleMarkOnePosted = async (post) => {
    if (!post.company_id) return;
    await fetch(`${API}/api/social/daily-posts/mark-posted`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_ids: [post.company_id], post_types: [post.type] }),
    });
    setPostedIds(prev => new Set([...prev, post.company_id]));
  };

  useEffect(() => { fetchPosts(); fetchLinkedinStatus(); }, [fetchPosts, fetchLinkedinStatus]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const li = params.get('linkedin');
    if (li === 'connected') {
      setLinkedinMsg('LinkedIn company page connected.');
      fetchLinkedinStatus();
      window.history.replaceState({}, '', '/social');
    } else if (li === 'error') {
      setLinkedinMsg(params.get('detail') || 'LinkedIn connect failed');
      window.history.replaceState({}, '', '/social');
    }
  }, [fetchLinkedinStatus]);

  const postedCount = postedIds.size;
  const totalLeadPosts = (posts || []).filter(p => p.company_id != null).length;

  return (
    <>
      <Head>
        <title>Content Studio | Ready For Robots</title>
        <meta name="description" content="Daily social media content — 5 ready-to-post items from hot leads and strategic insights." />
        <meta name="robots" content="noindex" />
      </Head>

      <RrSiteLayout active="social">
        <main className="max-w-4xl mx-auto px-4 py-8 text-[var(--rr-text)]">
          <div className="mb-8">
            <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--rr-green)]">Content Studio</p>
              <div className="text-[11px] text-[var(--rr-muted)] font-mono flex flex-wrap gap-x-3">
                {date && <span>{date}</span>}
                {generatedAt && <span>Generated {generatedAt}</span>}
              </div>
            </div>
            <h1 className="text-2xl font-bold text-[var(--rr-text)] mb-2">Daily Content Queue</h1>
            <p className="text-sm text-[var(--rr-muted2)] max-w-2xl">
              Five posts from today&apos;s hot leads and strategic insights. Edit any post, then copy or share.
              Mark posts as shared to get a fresh batch with different companies.
            </p>
          </div>

          {/* LinkedIn — member feed until Marketing API approved */}
          <div className="mb-6 p-4 border border-blue-900/60 rounded-xl bg-blue-950/20">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-blue-300">LinkedIn Publishing</p>
                <p className="text-xs text-neutral-400 mt-1">
                  {linkedinStatus?.connected
                    ? linkedinStatus.member_posting
                      ? `Connected as ${linkedinStatus.member_name || 'your profile'} — posts go to your personal feed (Share on LinkedIn). Repost to the company page manually until Marketing API is approved.`
                      : `Connected · company page org ${linkedinStatus.organization_id}`
                    : linkedinStatus?.configured
                      ? 'Not connected — sign in with LinkedIn to enable one-click publish'
                      : 'Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET on the API server'}
                </p>
                {linkedinStatus?.pending_marketing_api && (
                  <p className="text-[11px] text-neutral-500 mt-1">
                    Company page API pending LinkedIn review. Using Share on LinkedIn (personal profile) for now.
                  </p>
                )}
                {linkedinMsg && <p className="text-xs text-emerald-400 mt-2 font-mono">{linkedinMsg}</p>}
              </div>
              <div className="flex gap-2 flex-wrap">
                <a
                  href={linkedinStatus?.organization_url || 'https://www.linkedin.com/company/114404417/admin/dashboard/'}
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
                    className="text-xs px-3 py-1.5 rounded border border-blue-700 text-blue-300 hover:border-blue-500"
                  >
                    Connect LinkedIn Page
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Action bar */}
          {!loading && !error && posts && posts.length > 0 && (
            <div className="mb-6 flex items-center justify-between gap-3 flex-wrap p-4 border border-neutral-800 rounded-xl bg-neutral-900/30">
              <div className="flex items-center gap-3">
                {batchPosted ? (
                  <span className="text-xs text-emerald-400 font-mono">✓ All posts marked as shared</span>
                ) : postedCount > 0 ? (
                  <span className="text-xs text-neutral-400 font-mono">
                    {postedCount} of {totalLeadPosts} lead posts marked
                  </span>
                ) : (
                  <span className="text-xs text-neutral-500">
                    Share your posts, then get a fresh batch with new companies
                  </span>
                )}
              </div>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={markAllPosted}
                  disabled={batchPosted || refreshing}
                  className="text-xs px-3 py-1.5 rounded border border-emerald-900 text-emerald-500 hover:border-emerald-700 hover:text-emerald-400 transition-colors disabled:opacity-40"
                >
                  ✓ Mark all as posted
                </button>
                <button
                  onClick={getNewPosts}
                  disabled={refreshing || loading}
                  className="text-xs px-4 py-1.5 rounded border border-violet-700 text-violet-400 hover:border-violet-500 hover:text-violet-300 transition-colors disabled:opacity-50 font-semibold"
                >
                  {refreshing ? '⟳ Generating…' : '⟳ Get New Posts'}
                </button>
              </div>
            </div>
          )}

          {/* Loading state */}
          {(loading || refreshing) && (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="border border-neutral-800 rounded-xl h-48 animate-pulse bg-neutral-900/40" />
              ))}
            </div>
          )}

          {/* Error state */}
          {error && !loading && !refreshing && (
            <div className="border border-red-900 rounded-xl p-6 text-center">
              <p className="text-red-400 text-sm mb-3">Failed to load posts: {error}</p>
              <button
                onClick={fetchPosts}
                className="text-xs border border-neutral-700 text-neutral-400 hover:border-neutral-500 px-3 py-1.5 rounded"
              >
                Try again
              </button>
            </div>
          )}

          {/* Posts */}
          {!loading && !refreshing && !error && posts && (
            <div className="space-y-6">
              {posts.length === 0 ? (
                <div className="border border-neutral-800 rounded-xl p-8 text-center">
                  <p className="text-neutral-500 text-sm mb-2">No posts generated yet.</p>
                  <p className="text-neutral-600 text-xs">Make sure the scrapers have run and there are leads in the database.</p>
                </div>
              ) : (
                posts.map((post, i) => (
                  <PostCard
                    key={`${post.company_id || post.type}-${i}`}
                    post={post}
                    index={i}
                    onMarkPosted={handleMarkOnePosted}
                    isPosted={post.company_id != null && postedIds.has(post.company_id)}
                    linkedinConnected={Boolean(linkedinStatus?.connected)}
                    onPublishLinkedIn={publishToLinkedIn}
                    publishing={publishingIdx !== null}
                  />
                ))
              )}

              {posts.length > 0 && (
                <div className="border border-neutral-800 rounded-xl p-4 text-center space-y-2">
                  <p className="text-xs text-neutral-600">
                    Posts refresh automatically every 4 hours. Click <span className="text-violet-400">Get New Posts</span> any time to skip current companies and pull fresh leads.
                    Companies are excluded from reappearing for 7 days after being marked as posted.
                  </p>
                  <div className="flex justify-center gap-4">
                    <Link href="/" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
                      View Lead Intelligence →
                    </Link>
                    <Link href="/newsletter" className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                      View Newsletter →
                    </Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </RrSiteLayout>
    </>
  );
}
