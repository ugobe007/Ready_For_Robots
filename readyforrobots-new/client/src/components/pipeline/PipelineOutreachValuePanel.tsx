/**
 * Outreach draft preview — prove value before signup (value-first principle).
 */
import { ArrowRight, Copy, CheckCheck, Mail, Eye, LockKeyhole } from "lucide-react";
import { Link } from "wouter";
import { cleanAndClampText } from "@/lib/text";
import { signupHrefForLead } from "@/lib/signupHref";

type DealLike = {
  id: number;
  company: string;
  outreachSubject?: string;
  outreachBody?: string;
};

type Props = {
  deal: DealLike;
  hasSession: boolean;
  copied: boolean;
  onCopy: () => void;
  onPreview?: () => void;
  variant?: "inline" | "compact";
  /** Override signup return path (e.g. URL scan results). */
  signupNext?: string;
  /** Hide draft body and show unlock CTA (anonymous results gate). */
  locked?: boolean;
};

export default function PipelineOutreachValuePanel({
  deal,
  hasSession,
  copied,
  onCopy,
  onPreview,
  variant = "inline",
  signupNext,
  locked = false,
}: Props) {
  if (!deal.outreachBody && !deal.outreachSubject && !locked) return null;

  const signupHref = signupNext
    ? `/signup?next=${encodeURIComponent(signupNext)}${
        deal.company ? `&co=${encodeURIComponent(deal.company)}` : ""
      }`
    : signupHrefForLead(deal.id, deal.company);

  if (locked) {
    return (
      <div
        className={
          variant === "compact"
            ? "rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50/90 to-white px-3 py-3"
            : "pipeline-detail-section border-blue-200/60 bg-gradient-to-br from-blue-50/80 to-white"
        }
      >
        <div className="flex items-start gap-2">
          <LockKeyhole className="h-4 w-4 shrink-0 text-blue-800 mt-0.5" />
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-900">
              Outreach draft ready
            </p>
            <p className="mt-1 text-[11px] leading-relaxed text-blue-950">
              SIGNAL wrote a rep-voice email for {deal.company}. Sign up free to read the full draft, copy it, and save this lead.
            </p>
            <Link
              href={signupHref}
              className="mt-2 inline-flex items-center justify-center gap-1.5 rounded-lg bg-blue-700 px-3 py-2 text-[11px] font-bold text-white hover:bg-blue-800"
            >
              Unlock draft
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={
        variant === "compact"
          ? "rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50/90 to-white px-3 py-3"
          : "pipeline-detail-section border-amber-200/60 bg-gradient-to-br from-amber-50/80 to-white"
      }
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Mail className="h-3.5 w-3.5 text-emerald-700" />
          <p className={variant === "compact" ? "text-[10px] font-bold uppercase tracking-widest text-gray-500" : "text-[10px] font-bold uppercase tracking-widest text-gray-400"}>
            Your outreach draft — ready to send
          </p>
        </div>
        <div className="flex items-center gap-1">
          {onPreview && hasSession && (
            <button
              type="button"
              onClick={onPreview}
              className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold text-amber-800 hover:bg-amber-100"
            >
              <Eye className="h-3 w-3" />
              Preview
            </button>
          )}
          {hasSession ? (
            <button
              type="button"
              onClick={onCopy}
              className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold"
              style={
                copied
                  ? { background: "rgba(52,211,153,0.12)", color: "#047857" }
                  : { background: "rgba(255,176,0,0.12)", color: "#b45309" }
              }
            >
              {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
          ) : null}
        </div>
      </div>

      {deal.outreachSubject && (
        <div className="mb-2 rounded-lg border border-amber-200/80 bg-white/80 px-2.5 py-2">
          <p className="text-[10px] uppercase tracking-wide text-gray-400">Subject</p>
          <p className="text-xs font-semibold text-amber-900">{deal.outreachSubject}</p>
        </div>
      )}

      {deal.outreachBody && (
        <div className="rounded-lg border border-gray-200 bg-white px-2.5 py-2">
          <pre className="whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed text-gray-600 max-h-40 overflow-y-auto">
            {cleanAndClampText(deal.outreachBody, 680)}
          </pre>
        </div>
      )}

      {!hasSession && (
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[11px] leading-relaxed text-emerald-800">
            This draft is written in your voice for this buyer. Sign up free to copy, save, and track this lead.
          </p>
          <Link
            href={signupHref}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-[11px] font-bold text-white hover:bg-emerald-700"
          >
            Sign up free — copy draft
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
