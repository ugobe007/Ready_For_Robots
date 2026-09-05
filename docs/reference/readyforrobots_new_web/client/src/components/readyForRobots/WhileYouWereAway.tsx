import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { DailySummary } from "@/types/readyForRobots";

export type WhileYouWereAwayProps = {
  summary: DailySummary | null;
  isOpen: boolean;
  onClose: () => void;
};

export default function WhileYouWereAway({ summary, isOpen, onClose }: WhileYouWereAwayProps) {
  const s = summary ?? {
    signalsDetected: 0,
    companiesQualified: 0,
    outreachDraftsCreated: 0,
    followupsSent: 0,
    opportunitiesAdvanced: 0,
  };
  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-h-[85vh] max-w-[calc(100vw-2rem)] overflow-y-auto overflow-x-hidden break-words rounded-lg border-blue-200 bg-gradient-to-b from-sky-50 to-white sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-blue-950">While you were away</DialogTitle>
          <DialogDescription className="text-slate-600">
            Pipeline window (last day) from live analytics. Outreach and follow-up counts stay at zero
            until those actions are logged in the API.
          </DialogDescription>
        </DialogHeader>
        <ul className="min-w-0 space-y-2 text-sm text-slate-800 break-words">
          <li className="flex min-w-0 flex-wrap items-baseline justify-between gap-2 border-b border-blue-100 py-2 sm:flex-nowrap">
            <span className="min-w-0 shrink">Signals detected</span>
            <span className="shrink-0 font-mono font-medium text-blue-900">{s.signalsDetected}</span>
          </li>
          <li className="flex min-w-0 flex-wrap items-baseline justify-between gap-2 border-b border-blue-100 py-2 sm:flex-nowrap">
            <span className="min-w-0 shrink">Companies qualified</span>
            <span className="shrink-0 font-mono font-medium text-blue-900">{s.companiesQualified}</span>
          </li>
          <li className="flex min-w-0 flex-wrap items-baseline justify-between gap-2 border-b border-blue-100 py-2 sm:flex-nowrap">
            <span className="min-w-0 shrink">Outreach drafts created</span>
            <span className="shrink-0 font-mono font-medium text-blue-900">{s.outreachDraftsCreated}</span>
          </li>
          <li className="flex min-w-0 flex-wrap items-baseline justify-between gap-2 border-b border-blue-100 py-2 sm:flex-nowrap">
            <span className="min-w-0 shrink">Follow-ups sent</span>
            <span className="shrink-0 font-mono font-medium text-blue-900">{s.followupsSent}</span>
          </li>
          <li className="flex min-w-0 flex-wrap items-baseline justify-between gap-2 py-2 sm:flex-nowrap">
            <span className="min-w-0 shrink">Opportunities advanced</span>
            <span className="shrink-0 font-mono font-medium text-blue-900">{s.opportunitiesAdvanced}</span>
          </li>
        </ul>
      </DialogContent>
    </Dialog>
  );
}
