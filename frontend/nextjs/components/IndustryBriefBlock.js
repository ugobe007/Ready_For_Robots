/**
 * Renders industry_strategic brief from /api/daily-report or newsletter `industryBrief`.
 */
import { useState } from 'react';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://readyforrobots.com';

function formatBriefTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

function buildShareText(brief) {
  const lines = [];
  const exec = (brief.executive_take || '').trim();
  if (exec) lines.push(exec);

  const trends = (brief.macro_trends || []).slice(0, 2);
  if (trends.length) {
    lines.push('');
    lines.push('Top trends:');
    trends.forEach(t => {
      const title = typeof t === 'object' ? t.title : '';
      const detail = typeof t === 'object' ? t.detail : t;
      lines.push(`• ${title ? title + ': ' : ''}${detail}`);
    });
  }

  lines.push('');
  lines.push(`🤖 Full brief: ${SITE_URL}/newsletter/`);
  return lines.join('\n');
}

export default function IndustryBriefBlock({ brief, className = '' }) {
  const [copied, setCopied] = useState(false);

  if (!brief || !(brief.executive_take || '').trim()) return null;

  const sourceLabel =
    brief.source === 'openai'
      ? 'AI synthesis (live signals)'
      : 'Signal-based summary';

  const shareUrl = `${SITE_URL}/newsletter/`;
  const execTake = (brief.executive_take || '').trim();

  // X post: headline first, then first sentence of executive_take — fresh & relevant
  const briefHeadline = 'Strategic Industry Brief: Today\'s Automation Intelligence';
  const firstSentence = execTake.split('. ')[0] + '.';
  const maxBody = 240 - briefHeadline.length - 2;
  const tweetBody = firstSentence.length <= maxBody ? firstSentence : firstSentence.slice(0, maxBody - 1) + '…';
  const tweetText = `${briefHeadline}\n\n${tweetBody}`;

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
  const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
  const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;

  const copyBrief = () => {
    navigator.clipboard?.writeText(buildShareText(brief)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <section
      className={`border border-violet-800/50 rounded-lg p-6 bg-gradient-to-br from-violet-950/30 to-neutral-950/40 ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-violet-300">
          Strategic industry brief
        </h2>
        <div className="flex flex-wrap items-center gap-2 text-[10px] text-neutral-500">
          {brief.period_days != null && (
            <span className="px-2 py-0.5 rounded border border-neutral-700">
              Last {brief.period_days}d window
            </span>
          )}
          <span className="px-2 py-0.5 rounded border border-violet-800/60 text-violet-400/90">
            {sourceLabel}
          </span>
          {formatBriefTime(brief.generated_at) && (
            <span>{formatBriefTime(brief.generated_at)}</span>
          )}
        </div>
      </div>

      <p className="text-sm text-neutral-200 leading-relaxed mb-4">{brief.executive_take}</p>

      {/* Share row — sits right under the summary so it's immediately visible */}
      <div className="flex flex-wrap items-center gap-2 pb-5 mb-5 border-b border-violet-900/40">
        <span className="text-[10px] text-violet-400/70 uppercase tracking-wider font-semibold">Share brief:</span>
        <a
          href={linkedInUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Share on LinkedIn"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800/80 hover:bg-[#0a66c2] text-neutral-300 hover:text-white text-xs font-medium transition-colors border border-neutral-700/50"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          LinkedIn
        </a>
        <a
          href={twitterUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Share on X"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800/80 hover:bg-black text-neutral-300 hover:text-white text-xs font-medium transition-colors border border-neutral-700/50"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          X
        </a>
        <a
          href={facebookUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Share on Facebook"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800/80 hover:bg-[#1877f2] text-neutral-300 hover:text-white text-xs font-medium transition-colors border border-neutral-700/50"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
          Facebook
        </a>
        <button
          type="button"
          onClick={copyBrief}
          aria-label="Copy brief for social post"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-violet-900/40 hover:bg-violet-700 text-violet-300 hover:text-white text-xs font-medium transition-colors border border-violet-800/50"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
          {copied ? 'Copied!' : 'Copy post'}
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-xs font-semibold text-violet-400/90 uppercase tracking-wider mb-3">
            Macro trends
          </h3>
          <ul className="space-y-3 text-sm text-neutral-300">
            {(brief.macro_trends || []).map((t, i) => (
              <li key={i}>
                <span className="text-neutral-100 font-medium">
                  {typeof t === 'object' ? t.title : 'Trend'}:{' '}
                </span>
                <span className="text-neutral-400">
                  {typeof t === 'object' ? t.detail : t}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-violet-400/90 uppercase tracking-wider mb-3">
            Strategic implications
          </h3>
          <ul className="space-y-3 text-sm text-neutral-300">
            {(brief.strategic_implications || []).map((s, i) => (
              <li key={i}>
                <span className="text-cyan-400/90 font-medium">
                  {typeof s === 'object' ? s.audience || s.for_who || 'Stakeholders' : 'Stakeholders'}
                  :{' '}
                </span>
                <span className="text-neutral-400">
                  {typeof s === 'object' ? s.insight || s.detail : s}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-neutral-800">
        <div>
          <h3 className="text-xs font-semibold text-amber-500/90 uppercase tracking-wider mb-2">
            Risks & unknowns
          </h3>
          <ul className="list-disc list-inside text-xs text-neutral-500 space-y-1">
            {(brief.risks_and_unknowns || []).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-emerald-500/90 uppercase tracking-wider mb-2">
            What to watch
          </h3>
          <ul className="list-disc list-inside text-xs text-neutral-500 space-y-1">
            {(brief.watch_next || []).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
