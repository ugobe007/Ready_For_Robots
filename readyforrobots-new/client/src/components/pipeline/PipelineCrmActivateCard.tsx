/**
 * Signed-in, CRM-off: one obvious next step — save this buyer to start the native CRM.
 */
import { ArrowRight, Bookmark, LayoutDashboard } from "lucide-react";
import { Link } from "wouter";

type DealLike = {
  id: number;
  company: string;
  outreachSubject?: string;
};

type Props = {
  deal: DealLike | null;
  saving?: boolean;
  onActivate: () => void;
  compact?: boolean;
};

export default function PipelineCrmActivateCard({ deal, saving, onActivate, compact = false }: Props) {
  if (!deal) return null;
  const company = deal.company.trim() || "this buyer";

  return (
    <div className={`pipeline-crm-activate ${compact ? "pipeline-crm-activate-compact" : ""}`}>
      <div className="flex min-w-0 items-start gap-3">
        <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-emerald-400/40 bg-emerald-400/10">
          <LayoutDashboard className="h-5 w-5 text-emerald-300" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.18em] text-emerald-300">
            Next step · Activate CRM
          </p>
          <p className="pipeline-company-name mt-1 text-lg leading-snug sm:text-xl">{company}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-300">
            Saving this buyer turns the ranked list into your working pipeline — draft, send, and track from here
            or HubSpot.
          </p>
          {deal.outreachSubject ? (
            <p className="mt-1 truncate text-xs font-medium text-emerald-200/90">
              Draft ready: {deal.outreachSubject}
            </p>
          ) : null}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onActivate}
          disabled={saving}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-extrabold text-slate-950 transition hover:bg-amber-300 disabled:opacity-60"
        >
          <Bookmark className="h-4 w-4" />
          {saving ? "Saving…" : `Save ${company} to CRM`}
          {!saving && <ArrowRight className="h-4 w-4" />}
        </button>
        <Link
          href="/integrations/hubspot"
          className="inline-flex min-h-11 items-center justify-center rounded-lg border border-white/20 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-white/5"
        >
          Or connect HubSpot
        </Link>
      </div>
    </div>
  );
}
