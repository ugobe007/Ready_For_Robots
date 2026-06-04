/**
 * Social share for a single sales lead (X, LinkedIn, copy).
 */
import { useState } from "react";
import { Link2 } from "lucide-react";

const SITE_URL =
  typeof import.meta !== "undefined" && import.meta.env?.VITE_SITE_URL
    ? String(import.meta.env.VITE_SITE_URL)
    : "https://readyforrobots.com";

export type LeadShareInput = {
  id?: number | string;
  company_name?: string;
  priority_tier?: string | null;
  share_summary?: string | null;
  share_blurb?: string | null;
  signals?: Array<{ signal_label?: string; signal_type?: string }>;
};

function buildTweetText(lead: LeadShareInput): string {
  const name = lead.company_name || "Sales lead";
  const top = lead.signals?.[0];
  const sigLabel =
    top?.signal_label ||
    (top?.signal_type || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const tier = (lead.priority_tier || "Lead").toUpperCase();
  const emoji = tier === "HOT" ? "🔥" : tier === "WARM" ? "⚡" : "✦";
  const headline = `${name}${sigLabel ? ` — ${sigLabel}` : ""} | ${emoji} ${tier}`;
  const summary = lead.share_summary || lead.share_blurb || "";
  const first = summary.split(". ").filter(Boolean)[0];
  const body = first ? (first.endsWith(".") ? first : `${first}.`) : "";
  const maxBody = 240 - headline.length - 2;
  const trimmed =
    body && body.length <= maxBody
      ? body
      : body.slice(0, Math.max(30, maxBody - 1)).trim() + "…";
  return trimmed ? `${headline}\n\n${trimmed}` : headline;
}

type Props = {
  lead: LeadShareInput;
  compact?: boolean;
  className?: string;
};

export default function LeadShareBar({ lead, compact = false, className = "" }: Props) {
  const [copied, setCopied] = useState(false);
  const shareUrl = `${SITE_URL}/pipeline${lead.id != null ? `?lead=${lead.id}` : ""}`;
  const tweetText = buildTweetText(lead);
  const fullSummary =
    lead.share_summary ||
    lead.share_blurb ||
    `${lead.company_name || "Company"} — automation signals · Ready For Robots`;

  const copyPost = (e: React.MouseEvent) => {
    e.stopPropagation();
    void navigator.clipboard?.writeText(`${tweetText}\n\n${shareUrl}`).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    });
  };

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
  const liTitle = encodeURIComponent(
    `${lead.company_name || "Lead"} — ${lead.priority_tier || "Lead"} | Ready For Robots`,
  );
  const linkedInUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${liTitle}&summary=${encodeURIComponent(fullSummary.slice(0, 700))}&source=readyforrobots.com`;

  if (compact) {
    return (
      <div
        className={`flex items-center gap-1 ${className}`}
        onClick={(e) => e.stopPropagation()}
        role="group"
        aria-label="Share lead"
      >
        <a
          href={twitterUrl}
          target="_blank"
          rel="noopener noreferrer"
          title="Share on X"
          className="rounded p-1 text-white/40 transition-colors hover:bg-white/10 hover:text-white"
        >
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
        </a>
        <a
          href={linkedInUrl}
          target="_blank"
          rel="noopener noreferrer"
          title="Share on LinkedIn"
          className="rounded p-1 text-white/40 transition-colors hover:bg-white/10 hover:text-[#0a66c2]"
        >
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
          </svg>
        </a>
        <button
          type="button"
          onClick={copyPost}
          title="Copy post"
          className="rounded p-1 font-mono text-[10px] text-white/40 transition-colors hover:bg-white/10 hover:text-emerald-400"
        >
          {copied ? "✓" : "⧉"}
        </button>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`} onClick={(e) => e.stopPropagation()}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">Share</span>
        <a
          href={twitterUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded border border-white/10 bg-white/5 px-2 py-1 text-[10px] font-medium text-white/50 transition-colors hover:bg-white/10 hover:text-white"
        >
          X
        </a>
        <a
          href={linkedInUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded border border-white/10 bg-white/5 px-2 py-1 text-[10px] font-medium text-white/50 transition-colors hover:bg-[#0a66c2]/20 hover:text-white"
        >
          LinkedIn
        </a>
        <button
          type="button"
          onClick={copyPost}
          className="inline-flex items-center gap-1 rounded border border-white/10 bg-white/5 px-2 py-1 text-[10px] font-medium text-white/50 transition-colors hover:text-emerald-400"
        >
          <Link2 className="h-3 w-3" />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
