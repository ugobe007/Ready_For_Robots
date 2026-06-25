/**
 * Social share for a single sales lead (X, LinkedIn, email, WhatsApp, copy, native share).
 */
import { useState } from "react";
import { Link2, Mail, Share2 } from "lucide-react";

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
  signal_type?: string | null;
  signals?: Array<{ signal_label?: string; signal_type?: string }>;
};

export function buildLeadSharePost(lead: LeadShareInput): { tweetText: string; shareUrl: string; fullSummary: string } {
  const name = lead.company_name || "Sales lead";
  const top = lead.signals?.[0];
  const sigLabel =
    top?.signal_label ||
    (lead.signal_type || top?.signal_type || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
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
  const tweetText = trimmed ? `${headline}\n\n${trimmed}` : headline;
  const shareUrl = `${SITE_URL}/pipeline${lead.id != null ? `?lead=${lead.id}` : ""}`;
  const fullSummary =
    lead.share_summary ||
    lead.share_blurb ||
    `${lead.company_name || "Company"} — automation signals · Ready For Robots`;

  return { tweetText, shareUrl, fullSummary };
}

type Props = {
  lead: LeadShareInput;
  compact?: boolean;
  panel?: boolean;
  className?: string;
  /** Use dark styles only on navy/dark panels; default light for marketing surfaces. */
  variant?: "light" | "dark";
};

const VARIANT_STYLES = {
  light: {
    label: "text-gray-500",
    icon: "text-gray-500 hover:bg-gray-100 hover:text-gray-900",
    iconLinkedIn: "text-gray-500 hover:bg-sky-50 hover:text-sky-700",
    iconMail: "text-gray-500 hover:bg-emerald-50 hover:text-emerald-700",
    iconWhatsApp: "text-gray-500 hover:bg-green-50 hover:text-green-700",
    copy: "text-gray-500 hover:bg-gray-100 hover:text-emerald-700",
    chip: "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:text-gray-900",
    chipLinkedIn: "border-gray-200 bg-white text-gray-700 hover:bg-sky-50 hover:text-sky-800",
    chipMail: "border-gray-200 bg-white text-gray-700 hover:bg-emerald-50 hover:text-emerald-800",
    chipWhatsApp: "border-gray-200 bg-white text-gray-700 hover:bg-green-50 hover:text-green-800",
    chipCopy: "border-gray-200 bg-white text-gray-700 hover:text-emerald-700",
    chipNative: "border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100",
  },
  dark: {
    label: "text-white/30",
    icon: "text-white/40 hover:bg-white/10 hover:text-white",
    iconLinkedIn: "text-white/40 hover:bg-white/10 hover:text-[#0a66c2]",
    iconMail: "text-white/40 hover:bg-white/10 hover:text-emerald-400",
    iconWhatsApp: "text-white/40 hover:bg-white/10 hover:text-green-400",
    copy: "text-white/40 hover:bg-white/10 hover:text-emerald-400",
    chip: "border-white/10 bg-white/5 text-white/50 hover:bg-white/10 hover:text-white",
    chipLinkedIn: "border-white/10 bg-white/5 text-white/50 hover:bg-[#0a66c2]/20 hover:text-white",
    chipMail: "border-white/10 bg-white/5 text-white/50 hover:bg-emerald-500/20 hover:text-white",
    chipWhatsApp: "border-white/10 bg-white/5 text-white/50 hover:bg-green-500/20 hover:text-white",
    chipCopy: "border-white/10 bg-white/5 text-white/50 hover:text-emerald-400",
    chipNative: "border-emerald-400/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20",
  },
} as const;

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.435 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

export default function LeadShareBar({ lead, compact = false, panel = false, className = "", variant = "light" }: Props) {
  const v = VARIANT_STYLES[variant];
  const [copied, setCopied] = useState(false);
  const { tweetText, shareUrl, fullSummary } = buildLeadSharePost(lead);
  const canNativeShare = typeof navigator !== "undefined" && typeof navigator.share === "function";

  const copyPost = (e: React.MouseEvent) => {
    e.stopPropagation();
    void navigator.clipboard?.writeText(`${tweetText}\n\n${shareUrl}`).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    });
  };

  const nativeShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    void navigator.share?.({
      title: `${lead.company_name || "Lead"} — Ready For Robots`,
      text: tweetText,
      url: shareUrl,
    });
  };

  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
  const liTitle = encodeURIComponent(
    `${lead.company_name || "Lead"} — ${lead.priority_tier || "Lead"} | Ready For Robots`,
  );
  const linkedInUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(shareUrl)}&title=${liTitle}&summary=${encodeURIComponent(fullSummary.slice(0, 700))}&source=readyforrobots.com`;
  const mailSubject = encodeURIComponent(`${lead.company_name || "Lead"} — robot-ready buyer signal`);
  const mailBody = encodeURIComponent(`${tweetText}\n\nView on Ready For Robots:\n${shareUrl}`);
  const mailtoUrl = `mailto:?subject=${mailSubject}&body=${mailBody}`;
  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(`${tweetText}\n\n${shareUrl}`)}`;

  if (compact) {
    return (
      <div
        className={`flex items-center gap-0.5 ${className}`}
        onClick={(e) => e.stopPropagation()}
        role="group"
        aria-label="Share lead with your network"
      >
        <a href={twitterUrl} target="_blank" rel="noopener noreferrer" title="Share on X" className={`rounded p-1 transition-colors ${v.icon}`}>
          <XIcon className="h-3.5 w-3.5" />
        </a>
        <a href={linkedInUrl} target="_blank" rel="noopener noreferrer" title="Share on LinkedIn" className={`rounded p-1 transition-colors ${v.iconLinkedIn}`}>
          <LinkedInIcon className="h-3.5 w-3.5" />
        </a>
        <a href={mailtoUrl} title="Email to colleague" className={`rounded p-1 transition-colors ${v.iconMail}`}>
          <Mail className="h-3.5 w-3.5" />
        </a>
        <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" title="Share on WhatsApp" className={`rounded p-1 transition-colors ${v.iconWhatsApp}`}>
          <WhatsAppIcon className="h-3.5 w-3.5" />
        </a>
        <button type="button" onClick={copyPost} title="Copy share post" className={`rounded p-1 font-mono text-[10px] transition-colors ${v.copy}`}>
          {copied ? "✓" : "⧉"}
        </button>
      </div>
    );
  }

  if (panel) {
    return (
      <div className={`pipeline-detail-share ${className}`} onClick={(e) => e.stopPropagation()}>
        <div className="mb-2 flex items-start gap-2">
          <Share2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-800">Amplify to your network</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-gray-600">
              Share this SIGNAL lead with colleagues — post to social, email your team, or copy a ready-made blurb.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <a href={twitterUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chip}`}>
            <XIcon className="h-3.5 w-3.5" />
            Post on X
          </a>
          <a href={linkedInUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chipLinkedIn}`}>
            <LinkedInIcon className="h-3.5 w-3.5" />
            LinkedIn
          </a>
          <a href={mailtoUrl} className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chipMail}`}>
            <Mail className="h-3.5 w-3.5" />
            Email colleague
          </a>
          <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chipWhatsApp}`}>
            <WhatsAppIcon className="h-3.5 w-3.5" />
            WhatsApp
          </a>
          <button type="button" onClick={copyPost} className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chipCopy}`}>
            <Link2 className="h-3.5 w-3.5" />
            {copied ? "Copied!" : "Copy post"}
          </button>
          {canNativeShare ? (
            <button type="button" onClick={nativeShare} className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${v.chipNative}`}>
              <Share2 className="h-3.5 w-3.5" />
              Share…
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`} onClick={(e) => e.stopPropagation()}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`text-[10px] font-bold uppercase tracking-widest ${v.label}`}>Share</span>
        <a href={twitterUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-medium transition-colors ${v.chip}`}>
          X
        </a>
        <a href={linkedInUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-medium transition-colors ${v.chipLinkedIn}`}>
          LinkedIn
        </a>
        <a href={mailtoUrl} className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-medium transition-colors ${v.chipMail}`}>
          Email
        </a>
        <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-medium transition-colors ${v.chipWhatsApp}`}>
          WhatsApp
        </a>
        <button type="button" onClick={copyPost} className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-[10px] font-medium transition-colors ${v.chipCopy}`}>
          <Link2 className="h-3 w-3" />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
