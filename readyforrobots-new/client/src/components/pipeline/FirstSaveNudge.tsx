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
    <div className="rounded-xl border border-violet-200 bg-gradient-to-r from-violet-50 via-white to-emerald-50 px-4 py-3 sm:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-violet-200 bg-white">
            <Sparkles className="h-4 w-4 text-violet-700" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-violet-800">
              Your first save unlocks the workspace
            </p>
            <p className="mt-1 text-sm font-semibold text-gray-900">{deal.company}</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-gray-600">
              Save this lead to copy your outreach draft, track it in CRM, and choose native pipeline or HubSpot sync.
            </p>
            {deal.outreachSubject && (
              <p className="mt-1 truncate text-[11px] text-amber-800">
                Draft ready: {deal.outreachSubject}
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white transition-colors hover:bg-emerald-700 disabled:opacity-60"
        >
          <Bookmark className="h-3.5 w-3.5" />
          {saving ? "Saving…" : "Save first lead"}
          {!saving && <ArrowRight className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}
