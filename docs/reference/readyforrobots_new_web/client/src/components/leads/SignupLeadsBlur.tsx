/**
 * Blurred teaser of locked leads + centered signup CTA (preview wall).
 */

import type { LeadRow } from "@/lib/leadTypes";
import { scoreNum } from "@/lib/leadTypes";
import { Link } from "wouter";

type Props = {
  leads: LeadRow[];
  /** Number of rows shown fully above this block (default 5). */
  previewLimit: number;
  signupHref?: string;
};

export default function SignupLeadsBlur({ leads, previewLimit, signupHref = "/login" }: Props) {
  const locked = leads.slice(previewLimit);
  if (!locked.length) return null;

  const more = locked.length > 18 ? locked.length - 18 : 0;

  return (
    <div className="relative border-t border-gray-100">
      <div className="max-h-52 overflow-hidden blur-[3px] opacity-[0.42] pointer-events-none select-none px-4 py-1">
        {locked.slice(0, 18).map((lead) => (
          <div
            key={lead.id}
            className="flex items-center justify-between gap-3 border-b border-gray-100/90 py-2.5 text-sm"
          >
            <span className="truncate font-medium text-gray-800">{lead.company_name || "—"}</span>
            <span className="shrink-0 font-mono text-xs tabular-nums text-gray-600">
              {Math.round(scoreNum(lead, "overall_score"))}
            </span>
          </div>
        ))}
        {more > 0 ? (
          <p className="py-3 text-center text-xs text-gray-400">+{more} more leads</p>
        ) : null}
      </div>

      <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-white/20 via-emerald-50/25 to-white/40 px-4 py-8 backdrop-blur-[2px]">
        <div className="max-w-sm rounded-2xl border border-white/70 bg-white/35 px-5 py-4 text-center shadow-[0_8px_32px_-8px_rgba(5,80,60,0.25)] backdrop-blur-xl backdrop-saturate-150 ring-1 ring-white/40">
          <Link
            href={signupHref}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-white shadow-md transition-opacity hover:opacity-90"
            style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}
          >
            Sign up to unlock full list →
          </Link>
          <p className="mt-2.5 text-[11px] text-gray-600/90">No credit card required · Same data as logged-in preview</p>
        </div>
      </div>
    </div>
  );
}
