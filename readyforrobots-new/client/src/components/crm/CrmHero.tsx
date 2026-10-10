/**
 * CRM page chrome — Kare face, emerald headline, how-to, jobs-watch opt-in.
 */
import { type ReactNode } from "react";
import { Link } from "wouter";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import JobsWatchReport from "@/components/crm/JobsWatchReport";
import {
  CRM_HEADLINE_CLASS,
  CRM_HOW_TO_STEPS,
  CRM_PAGE_HEADLINE,
  CRM_PAGE_NEXT,
  CRM_SUBHEAD_CLASS,
  CRM_UNLOCKED_JOBS,
  JOBS_ACTIVATE_JOBS_CTA,
  JOBS_EYEBROW_CLASS,
  jobsFreshHomeHref,
  onJobsFreshHomeClick,
} from "@/lib/jobsWorkflow";
import { jobModelListLine } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";
import type { JobsWatchStatus } from "@/lib/jobsCrmAccount";

export type { JobsWatchStatus };

export type CrmTasteJob = Pick<
  MatchJob,
  "title" | "company_name" | "forRobot"
> & {
  required_task_models?: MatchJob["required_task_models"];
};

type Props = {
  signedIn?: boolean;
  watch?: JobsWatchStatus | null;
  watchBusy?: boolean;
  watchError?: string | null;
  onOptIn?: (optedIn: boolean) => void;
  tasteJobs?: CrmTasteJob[];
  tasteProduct?: string | null;
  activateHref?: string;
  actions?: ReactNode;
  footer?: ReactNode;
};

export default function CrmHero({
  signedIn = false,
  watch,
  watchBusy,
  watchError,
  onOptIn,
  tasteJobs = [],
  tasteProduct,
  activateHref,
  actions,
  footer,
}: Props) {
  const activateCta = activateHref ? (
    <Link
      href={activateHref}
      className="inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
    >
      {JOBS_ACTIVATE_JOBS_CTA}
    </Link>
  ) : null;
  const unlocked = tasteJobs.slice(0, CRM_UNLOCKED_JOBS);
  return (
    <div className="mb-5 border border-slate-600 bg-[#0b162f] px-5 py-5 sm:px-6">
      <div className="flex items-start gap-4">
        <PixelIcon
          map={KARE_FACE}
          scale={3}
          fill={FACE_EMERALD}
          background="transparent"
          className="mt-1 shrink-0"
        />
        <div className="min-w-0 flex-1">
          <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>
            ReadyForRobots
          </p>
          <h1 className={`mt-2 ${CRM_HEADLINE_CLASS}`}>{CRM_PAGE_HEADLINE}</h1>
          <p className={CRM_SUBHEAD_CLASS}>{CRM_PAGE_NEXT}</p>
          {activateCta ? <div className="mt-4">{activateCta}</div> : null}
        </div>
      </div>

      <ol className="mt-5 max-w-2xl space-y-2">
        {CRM_HOW_TO_STEPS.map((step, i) => (
          <li
            key={step}
            className="flex gap-3 text-base leading-relaxed text-slate-200"
          >
            <span className="font-mono text-emerald-400">{i + 1}.</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>

      {unlocked.length > 0 ? (
        <div className="mt-5 border border-slate-600 bg-[#081126] px-4 py-4">
          <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>
            {unlocked.length} of {CRM_UNLOCKED_JOBS} job opportunities unlocked
          </p>
          {tasteProduct ? (
            <p className="mt-1 text-sm text-slate-400">{tasteProduct}</p>
          ) : null}
          <ul className="mt-3 space-y-1.5">
            {unlocked.map((job, i) => {
              const modelLine = jobModelListLine(job);
              return (
                <li
                  key={`${job.title || "job"}-${i}`}
                  className="text-sm text-slate-200"
                >
                  • {job.title}
                  {job.company_name ? ` · ${job.company_name}` : ""}
                  {modelLine ? (
                    <span className="block text-slate-400">{modelLine}</span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <JobsWatchReport
        signedIn={signedIn}
        watch={watch}
        watchBusy={watchBusy}
        watchError={watchError}
        onOptIn={onOptIn}
      />

      {actions ? (
        <div className="mt-4 flex flex-wrap gap-3">{actions}</div>
      ) : null}
      {activateCta ? <div className="mt-4">{activateCta}</div> : null}
      {footer ? (
        <div className="mt-4 text-base text-slate-400">{footer}</div>
      ) : null}
      <a
        href={jobsFreshHomeHref()}
        onClick={onJobsFreshHomeClick}
        className="mt-4 inline-flex font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
      >
        + New robot
      </a>
    </div>
  );
}
