import { keepJobsStatusBar } from "@/lib/jobsCrmAccount";
import { JOBS_APPLY_CTA_CLASS } from "@/lib/jobsWorkflow";

export default function JobsKeepStatusBar({
  savedCount,
  onCrmDesk,
  signedIn,
  submissionId = null,
  onApplyClick,
}: {
  savedCount: number;
  onCrmDesk: boolean;
  signedIn: boolean;
  submissionId?: number | null;
  onApplyClick?: (event: { preventDefault: () => void }) => void;
}) {
  if (savedCount <= 0) return null;
  const bar = keepJobsStatusBar({
    savedCount,
    onCrmDesk,
    signedIn,
    submissionId,
  });
  return (
    <div
      role="status"
      aria-live="polite"
      data-jobs-keep-status="1"
      className="flex flex-wrap items-center gap-3 border border-emerald-400/40 bg-emerald-400/10 px-4 py-3"
    >
      <p className="font-mono text-sm font-bold uppercase tracking-[0.08em] text-emerald-300">
        {bar.text}
      </p>
      {bar.href ? (
        <a
          href={bar.href}
          onClick={onCrmDesk ? onApplyClick : undefined}
          className={
            onCrmDesk
              ? `${JOBS_APPLY_CTA_CLASS} px-3 py-2 font-mono text-xs`
              : "font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-200 underline decoration-emerald-400/50 underline-offset-2 hover:text-white"
          }
        >
          {bar.hrefLabel}
        </a>
      ) : null}
    </div>
  );
}
