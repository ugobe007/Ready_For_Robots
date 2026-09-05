/**
 * FIND → Job Cards → CRM process bar for CRM / wall surfaces.
 * Step 03 stays CRM. Place is not a fourth process name.
 */
import {
  JOBS_APPLY_CTA_CLASS,
  JOBS_APPLY_HERO_CTA,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_PROCESS_STEPS,
  jobsCrmNextHref,
  jobsCrmNextLabel,
  jobsCrmOpenHref,
  jobsWorkspaceRestoreHref,
} from "@/lib/jobsWorkflow";
import { jobsFindHref } from "@/lib/jobsLanding";
import { jobsCrmOfferHref } from "@/lib/jobsCrmAccount";

export default function JobsProcessChrome({
  signedIn,
  submissionId = null,
  jobCount = 0,
  current = "activate",
}: {
  signedIn: boolean;
  submissionId?: number | null;
  jobCount?: number;
  current?: "find" | "jobs" | "activate";
}) {
  const nextHref = jobsCrmNextHref(signedIn, submissionId, jobCount);
  const nextLabel = jobsCrmNextLabel(signedIn, { submissionId, jobCount });

  return (
    <nav
      aria-label="Jobs process"
      className="rfr-jobs-process-bar flex flex-wrap items-stretch border border-slate-600"
    >
      {JOBS_PROCESS_STEPS.map(step => {
        const isCurrent = step.id === current;
        const href =
          step.id === "find"
            ? jobsFindHref()
            : step.id === "jobs"
              ? jobsWorkspaceRestoreHref()
              : jobsCrmOpenHref(signedIn, submissionId);
        const className = `flex min-w-0 flex-1 items-center px-3 py-3 ${JOBS_PROCESS_NAV_CLASS} ${
          isCurrent
            ? "border-b-2 border-emerald-400 bg-emerald-400/5 text-emerald-300"
            : "border-b-2 border-transparent text-slate-400 hover:text-slate-200"
        }`;
        return (
          <a
            key={step.id}
            href={href}
            aria-current={isCurrent ? "step" : undefined}
            className={className}
          >
            {step.n} {step.label}
          </a>
        );
      })}
      {signedIn && jobCount > 0 ? (
        <a
          href={jobsCrmOfferHref(true, submissionId)}
          className={`rfr-jobs-process-action m-2 shrink-0 ${JOBS_APPLY_CTA_CLASS}`}
        >
          {JOBS_APPLY_HERO_CTA}
        </a>
      ) : null}
      <a
        href={nextHref}
        className="rfr-bevel rfr-jobs-process-action m-2 inline-flex shrink-0 items-center justify-center bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
      >
        {nextLabel}
      </a>
    </nav>
  );
}
