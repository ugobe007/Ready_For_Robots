/**
 * Content Studio — Daily Social Media Post Generator
 * Pulls 5 ready-to-post items from /api/social/daily-posts.
 * Each post has Twitter (X) and LinkedIn variants with editable text + copy/share.
 */
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { getApiBase } from '../lib/apiBase';

const API = getApiBase();

const POST_TYPE_META = {
  hot_lead:           { label: '🔥 Hot Lead Spotlight',   border: 'border-red-800',    text: 'text-red-400',     bg: 'bg-red-950/30' },
  signal_alert:       { label: '📊 Signal Alert',         border: 'border-amber-800',  text: 'text-amber-400',   bg: 'bg-amber-950/30' },
  industry_insight:   { label: '🧠 Industry Intelligence', border: 'border-cyan-800',   text: 'text-cyan-400',    bg: 'bg-cyan-950/20' },
  market_trend:       { label: '📈 Market Trend',         border: 'border-violet-800', text: 'text-violet-400',  bg: 'bg-violet-950/20' },
  thought_leadership: { label: '🤖 Thought Leadership',   border: 'border-emerald-800',text: 'text-emerald-400', bg: 'bg-emerald-950/20' },
};

const TWITTER_SOFT_LIMIT = 257; // URL counts ~23 chars on platform side

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

function LinkedInShareButton({ url }) {
  const encoded = encodeURIComponent(url);
  return (
    <a
      href={`https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-xs px-3 py-1.5 rounded border border-blue-800 text-blue-400 hover:border-blue-600 hover:text-blue-300 transition-colors font-mono"
    >
      Post on LinkedIn ↗
    </a>
  );
}

function PostCard({ post, index }) {
  const meta = POST_TYPE_META[post.type] || POST_TYPE_META.thought_leadership;
  const [activeTab, setActiveTab] = useState('twitter');
  const [twitterText, setTwitterText] = useState(post.twitter || '');
  const [linkedinText, setLinkedinText] = useState(post.linkedin || '');

  const twitterLen = twitterText.length;
  const shareUrl = post.share_url || 'https://readyforrobots.com';

  return (
    <div className={`border ${meta.border} rounded-xl overflow-hidden`}>
      {/* Card header */}
      <div className={`${meta.bg} border-b ${meta.border} px-4 py-3 flex items-center justify-between gap-3 flex-wrap`}>
        <div className="flex items-center gap-3">
          <span className="text-neutral-500 font-mono text-xs tabular-nums">#{index + 1}</span>
          <span className={`text-sm font-semibold ${meta.text}`}>{meta.label}</span>
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
          {post.signal_count != null && (
            <span className="text-[10px] border border-neutral-700 text-neutral-500 px-2 py-0.5 rounded font-mono">
              {post.signal_count} signals
            </span>
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
                <LinkedInShareButton url={shareUrl} />
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [date, setDate] = useState('');
  const [generatedAt, setGeneratedAt] = useState('');

  const fetchPosts = async (force = false) => {
    try {
      if (force) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const url = `${API}/api/social/daily-posts${force ? '?refresh=true' : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      setPosts(data.posts || []);
      setDate(data.date || '');
      if (data.generated_at) {
        const d = new Date(data.generated_at);
        setGeneratedAt(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchPosts(); }, []);

  return (
    <>
      <Head>
        <title>Content Studio | Ready For Robots</title>
        <meta name="description" content="Daily social media content — 5 ready-to-post items from hot leads and strategic insights." />
        <meta name="robots" content="noindex" />
      </Head>

      <div className="min-h-screen bg-neutral-950 text-neutral-100">
        {/* Top nav */}
        <header className="border-b border-neutral-800 px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors font-mono">
              ← Home
            </Link>
            <span className="text-neutral-600">|</span>
            <h1 className="text-sm font-semibold text-neutral-200">Content Studio</h1>
            {date && (
              <span className="text-xs text-neutral-500 font-mono">{date}</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {generatedAt && (
              <span className="text-[10px] text-neutral-600 font-mono">Generated {generatedAt}</span>
            )}
            <Link href="/dashboard" className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors">
              Dashboard
            </Link>
            <Link href="/newsletter" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              Newsletter
            </Link>
            <button
              onClick={() => fetchPosts(false)}
              disabled={loading || refreshing}
              className="text-xs border border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-300 px-3 py-1.5 rounded transition-colors disabled:opacity-50"
            >
              {loading || refreshing ? '…' : '↺ Refresh'}
            </button>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          {/* Page header */}
          <div className="mb-8">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h2 className="text-2xl font-bold text-neutral-100 mb-1">Daily Content Queue</h2>
                <p className="text-sm text-neutral-500">
                  5 posts generated from today's hot leads, market trends, and strategic insights.
                  Edit any post before copying or publishing.
                </p>
              </div>
              <div className="flex gap-2 items-center flex-wrap">
                <div className="flex gap-1.5">
                  {Object.entries(POST_TYPE_META).map(([key, m]) => (
                    <span key={key} className={`text-[10px] font-mono border ${m.border} ${m.text} px-2 py-0.5 rounded`}>
                      {m.label.split(' ').slice(0, 2).join(' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="border border-neutral-800 rounded-xl h-48 animate-pulse bg-neutral-900/40" />
              ))}
            </div>
          )}

          {/* Error state */}
          {error && !loading && (
            <div className="border border-red-900 rounded-xl p-6 text-center">
              <p className="text-red-400 text-sm mb-3">Failed to load posts: {error}</p>
              <button
                onClick={() => fetchPosts()}
                className="text-xs border border-neutral-700 text-neutral-400 hover:border-neutral-500 px-3 py-1.5 rounded"
              >
                Try again
              </button>
            </div>
          )}

          {/* Posts */}
          {!loading && !error && posts && (
            <div className="space-y-6">
              {posts.length === 0 ? (
                <div className="border border-neutral-800 rounded-xl p-8 text-center">
                  <p className="text-neutral-500 text-sm mb-2">No posts generated yet.</p>
                  <p className="text-neutral-600 text-xs">Make sure the scrapers have run and there are HOT leads in the database.</p>
                </div>
              ) : (
                posts.map((post, i) => (
                  <PostCard key={i} post={post} index={i} />
                ))
              )}

              {/* Footer tip */}
              {posts.length > 0 && (
                <div className="border border-neutral-800 rounded-xl p-4 text-center">
                  <p className="text-xs text-neutral-600">
                    Posts refresh automatically every 4 hours as new signals come in.
                    Edit any post above before publishing — the text is fully customizable.
                  </p>
                  <div className="mt-3 flex justify-center gap-4">
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
      </div>
    </>
  );
}
