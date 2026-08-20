/**
 * Outreach draft preview — prove value before signup (value-first principle).
 */
import { ArrowRight, Copy, CheckCheck, Mail, Eye, LockKeyhole } from "lucide-react";
import { Link } from "wouter";
import { cleanAndClampText } from "@/lib/text";
import { signupHrefForLead } from "@/lib/signupHref";
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";

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
  /** Results page uses dark panels; pipeline stays light by default. */
  tone?: "light" | "dark";
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
  tone = "light",
}: Props) {
  if (!deal.outreachBody && !deal.outreachSubject && !locked) return null;

  const dark = tone === "dark";
  const signupHref = signupNext
    ? `/signup?next=${encodeURIComponent(signupNext)}${
        deal.company ? `&co=${encodeURIComponent(deal.company)}` : ""
      }`
    : signupHrefForLead(deal.id, deal.company);

  if (locked) {
    return (
      <div
        className={
          dark
            ? variant === "compact"
              ? "rounded-lg border border-sky-400/30 bg-sky-400/10 px-3 py-3"
              : "pipeline-detail-section border-sky-400/30 bg-sky-400/10"
            : variant === "compact"
              ? "rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50/90 to-white px-3 py-3"
              : "pipeline-detail-section border-blue-200/60 bg-gradient-to-br from-blue-50/80 to-white"
        }
      >
        <div className="flex items-start gap-2">
          <LockKeyhole className={`h-4 w-4 shrink-0 mt-0.5 ${dark ? "text-sky-300" : "text-blue-800"}`} />
          <div className="min-w-0 flex-1">
            <p className={`text-[10px] font-bold uppercase tracking-widest ${dark ? "text-sky-200" : "text-blue-900"}`}>
              Cal's note ready
            </p>
            <p className={`mt-1 text-[11px] leading-relaxed ${dark ? "text-sky-100/90" : "text-blue-950"}`}>
              A short, timely note for {deal.company} — market timing, not a hard sell. Sign up free to read the full draft, copy it, and save this lead.
            </p>
            <Link
              href={signupHref}
              className={
                dark
                  ? "mt-2 inline-flex items-center justify-center gap-1.5 rounded-lg bg-sky-400 px-3 py-2 text-[11px] font-bold text-slate-950 hover:bg-sky-300"
                  : "mt-2 inline-flex items-center justify-center gap-1.5 rounded-lg bg-blue-700 px-3 py-2 text-[11px] font-bold text-white hover:bg-blue-800"
              }
            >
              <PixelIcon map={KARE_FACE} scale={2} fill={dark ? "#05271e" : "#ffffff"} background="transparent" />
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
        dark
          ? variant === "compact"
            ? "rounded-lg border border-amber-400/35 bg-amber-400/10 px-3 py-3"
            : "pipeline-detail-section border-amber-400/35 bg-amber-400/10"
          : variant === "compact"
            ? "rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50/90 to-white px-3 py-3"
            : "pipeline-detail-section border-amber-200/60 bg-gradient-to-br from-amber-50/80 to-white"
      }
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Mail className={`h-3.5 w-3.5 ${dark ? "text-emerald-300" : "text-emerald-700"}`} />
          <p
            className={
              dark
                ? "text-[10px] font-bold uppercase tracking-widest text-slate-400"
                : variant === "compact"
                  ? "text-[10px] font-bold uppercase tracking-widest text-gray-500"
                  : "text-[10px] font-bold uppercase tracking-widest text-gray-400"
            }
          >
            What Cal would send — problem first, then fit
          </p>
        </div>
        <div className="flex items-center gap-1">
          {onPreview && hasSession && (
            <button
              type="button"
              onClick={onPreview}
              className={
                dark
                  ? "flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold text-amber-200 hover:bg-amber-400/15"
                  : "flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold text-amber-800 hover:bg-amber-100"
              }
            >
              <Eye className="h-3 w-3" />
              Preview
            </button>
          )}
          {hasSession ? (
            <span className="inline-flex items-center gap-1">
              <PixelIcon map={KARE_FACE} scale={2} fill="#3ecf8e" background="transparent" />
              <button
                type="button"
                onClick={onCopy}
                className="flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold"
                style={
                  copied
                    ? { background: "rgba(52,211,153,0.12)", color: dark ? "#6ee7b7" : "#047857" }
                    : { background: "rgba(255,176,0,0.12)", color: dark ? "#fcd34d" : "#b45309" }
                }
              >
                {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </span>
          ) : null}
        </div>
      </div>

      {deal.outreachSubject && (
        <div
          className={
            dark
              ? "mb-2 rounded-lg border border-amber-400/25 bg-[#081126]/80 px-2.5 py-2"
              : "mb-2 rounded-lg border border-amber-200/80 bg-white/80 px-2.5 py-2"
          }
        >
          <p className={`text-[10px] uppercase tracking-wide ${dark ? "text-slate-500" : "text-gray-400"}`}>Subject</p>
          <p className={`text-xs font-semibold ${dark ? "text-amber-200" : "text-amber-900"}`}>{deal.outreachSubject}</p>
        </div>
      )}

      {deal.outreachBody && (
        <div
          className={
            dark
              ? "rounded-lg border border-white/10 bg-[#081126]/70 px-2.5 py-2"
              : "rounded-lg border border-gray-200 bg-white px-2.5 py-2"
          }
        >
          <pre
            className={`whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed max-h-40 overflow-y-auto ${
              dark ? "text-slate-300" : "text-gray-600"
            }`}
          >
            {cleanAndClampText(deal.outreachBody, 680)}
          </pre>
        </div>
      )}

      {!hasSession && (
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className={`text-[11px] leading-relaxed ${dark ? "text-emerald-200/90" : "text-emerald-800"}`}>
            Notice the timing — this is market insight, not a pitch. Sign up free to copy, save, and track this lead.
          </p>
          <Link
            href={signupHref}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-2 text-[11px] font-bold text-[#05271e] hover:bg-emerald-400"
          >
            <PixelIcon map={KARE_FACE} scale={2} fill="#05271e" background="transparent" />
            Sign up free — copy draft
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
