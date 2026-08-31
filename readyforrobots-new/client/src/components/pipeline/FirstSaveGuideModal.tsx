import { Bookmark, CheckCircle2, Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type DealLike = {
  company: string;
  outreachSubject?: string;
};

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  deal: DealLike | null;
  saving?: boolean;
  onSave: () => void;
  onDismiss: () => void;
};

const STEPS = [
  "Review the outreach draft on the right — it is ready for this buyer.",
  "Save the lead to unlock copy, CRM tracking, and HubSpot sync.",
  "Choose native pipeline or HubSpot after your first save.",
];

export default function FirstSaveGuideModal({
  open,
  onOpenChange,
  deal,
  saving,
  onSave,
  onDismiss,
}: Props) {
  if (!deal) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={next => {
        onOpenChange(next);
        if (!next) onDismiss();
      }}
    >
      <DialogContent className="border-emerald-300 bg-gradient-to-b from-emerald-50 to-white sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-300 bg-white shadow-sm">
            <Sparkles className="h-5 w-5 text-emerald-700" />
          </div>
          <DialogTitle className="text-center text-xl font-black text-slate-900">
            Save your first lead
          </DialogTitle>
          <DialogDescription className="text-center text-sm text-slate-700">
            You are signed in. One save turns this buyer into a tracked
            opportunity in your workspace.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-xl border border-emerald-200 bg-white px-4 py-3">
          <p className="text-sm font-bold text-slate-900">{deal.company}</p>
          {deal.outreachSubject && (
            <p className="mt-1 text-xs font-medium text-emerald-900">
              Draft: {deal.outreachSubject}
            </p>
          )}
        </div>

        <ol className="space-y-2.5">
          {STEPS.map((step, index) => (
            <li
              key={step}
              className="flex items-start gap-2.5 text-sm text-slate-700"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
              <span>
                <span className="font-semibold text-slate-900">
                  {index + 1}.{" "}
                </span>
                {step}
              </span>
            </li>
          ))}
        </ol>

        <DialogFooter className="gap-2 sm:justify-center">
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-lg border border-slate-300 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
          >
            Browse first
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={saving}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            <Bookmark className="h-3.5 w-3.5" />
            {saving ? "Saving…" : "Save first lead"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
