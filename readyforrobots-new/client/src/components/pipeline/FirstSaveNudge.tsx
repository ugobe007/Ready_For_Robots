/**
 * Post-signup activation — prompt first save when workspace is empty.
 */
import { ArrowRight, Bookmark, Sparkles } from "lucide-react";

type DealLike = {
  id: number;
  company: string;
  outreachSubject?: string;
};

type Props = {
  deal: DealLike | null;
  saving?: boolean;
  onSave: () => void;
};

export default function FirstSaveNudge({ deal, saving, onSave }: Props) {
  if (!deal) return null;

  return (
    <div className="pipeline-first-save-nudge">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-emerald-300 bg-white shadow-sm">
            <Sparkles className="h-4 w-4 text-emerald-700" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-900">
              Workflow step 1 of 3 · Save lead
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-900">
              {deal.company}
            </p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-slate-700">
              Start workflow progress: save this lead, then copy draft, then
              send outreach.
            </p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[10px]">
              <span className="rounded-full border border-emerald-300 bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-800">
                1 Save lead
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 font-semibold text-slate-500">
                2 Copy draft
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 font-semibold text-slate-500">
                3 Send outreach
              </span>
            </div>
            {deal.outreachSubject && (
              <p className="mt-1 truncate text-[11px] font-medium text-emerald-900">
                Draft ready: {deal.outreachSubject}
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-60"
        >
          <Bookmark className="h-3.5 w-3.5" />
          {saving ? "Saving…" : "Complete step 1"}
          {!saving && <ArrowRight className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}
