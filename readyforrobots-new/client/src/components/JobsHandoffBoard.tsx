/**
 * Activated Jobs list on /pipeline. Checked jobs from `/` sit at the top;
 * the rest of the 15 is filled from the same match. This is not SIGNAL
 * buyers and not a bounce back to FIND.
 */
import { Link } from "wouter";
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  JOBS_ACTIVATE_CAP,
  JOBS_ACTIVATE_SRC,
  JOBS_EYEBROW_CLASS,
  JOBS_JOB_TITLE_CLASS,
  JOBS_META_CLASS,
  JOBS_PLACE_CLASS,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_RAIL_LINK_CLASS,
  JOBS_ROBOT_NAME_CLASS,
  JOBS_SAVE_TO_CRM_CTA,
  JOBS_SAVE_TO_CRM_HINT,
  RAIL_STEP_HINT,
  jobExplanation,
  jobIsForLabel,
  jobsActivateHref,
  jobsFreshHomeHref,
  jobsSignupHref,
  jobsWorkspaceRestoreHref,
  onJobsFreshHomeClick,
} from "@/lib/jobsWorkflow";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";

export default function JobsHandoffBoard(_props: {
  robotUrl: string;
  cap: number;
  src?: string | null;
  signedIn: boolean;
  variant: "results" | "pipeline";
}) {
  const snap = readJobsHandoffSnapshot();
  const jobs = (snap?.jobs || []).slice(0, _props.cap || JOBS_ACTIVATE_CAP);
  const selectedCount = snap?.selectedCount ?? jobs.length;
  const product = snap?.productName || "your robot";
  const filled = Math.max(0, jobs.length - selectedCount);

  return (
    <div className="mx-auto grid w-full max-w-[1200px] flex-1 grid-cols-1 lg:grid-cols-[minmax(0,0.34fr)_minmax(0,0.66fr)]">
      <aside className="border-b border-slate-600 p-5 sm:p-6 lg:border-b-0 lg:border-r">
        <p className={JOBS_EYEBROW_CLASS}>Your robot</p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white">
          {product}
        </h2>
        <nav className="mt-6 space-y-1">
          <p className={`border-l-2 border-transparent px-3 py-2 ${JOBS_PROCESS_NAV_CLASS} text-slate-500`}>
            01 Profile
          </p>
          <p className={`border-l-2 border-transparent px-3 py-2 ${JOBS_PROCESS_NAV_CLASS} text-slate-500`}>
            02 Jobs
          </p>
          <p className={`border-l-2 border-emerald-400 bg-emerald-400/5 px-3 py-2 ${JOBS_PROCESS_NAV_CLASS} text-emerald-300`}>
            03 Live list
          </p>
        </nav>
        <p className="mt-4 text-sm leading-relaxed text-slate-300">
          {RAIL_STEP_HINT.pipeline}
        </p>
        <ol className="mt-4 space-y-2 text-sm leading-relaxed text-slate-300">
          <li>
            <span className="font-mono text-emerald-400">1.</span> The jobs you
            checked stay pinned at the top.
          </li>
          <li>
            <span className="font-mono text-emerald-400">2.</span> We filled the
            rest so you see {JOBS_ACTIVATE_CAP} live jobs, not one buyer.
          </li>
          <li>
            <span className="font-mono text-emerald-400">3.</span> Inspect jobs
            to change the list, or start a new robot.
          </li>
        </ol>
        <div className="mt-8 space-y-2">
          <Link href={jobsWorkspaceRestoreHref()} className={JOBS_RAIL_LINK_CLASS}>
            Inspect jobs
          </Link>
          <a
            href={jobsFreshHomeHref()}
            onClick={onJobsFreshHomeClick}
            className={JOBS_RAIL_LINK_CLASS}
          >
            + New robot
          </a>
        </div>
      </aside>

      <main className="min-h-0 px-4 py-8 sm:px-6">
        <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>Live job list</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Jobs for {product}
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-300">
          You checked {selectedCount}. The list shows {jobs.length} of{" "}
          {JOBS_ACTIVATE_CAP}
          {filled > 0 ? ` (${filled} more from this match)` : ""}.{" "}
          {JOBS_SAVE_TO_CRM_HINT}
        </p>
        <a
          href={
            _props.signedIn
              ? "/crm"
              : jobsSignupHref(jobsActivateHref(), JOBS_ACTIVATE_SRC)
          }
          className="mt-5 inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
        >
          {JOBS_SAVE_TO_CRM_CTA}
        </a>

        {jobs.length === 0 ? (
          <p className="mt-8 text-base text-slate-300">
            No jobs were carried over.{" "}
            <Link href={jobsWorkspaceRestoreHref()} className="text-emerald-400 hover:text-emerald-300">
              Return to Jobs
            </Link>
            .
          </p>
        ) : (
          <ol className="mt-8 space-y-3">
            {jobs.map((job, i) => (
              <JobRow
                key={job.job_key}
                index={i + 1}
                job={job}
                robotName={job.forRobot || product}
                pinned={i < selectedCount}
              />
            ))}
          </ol>
        )}
      </main>
    </div>
  );
}

function JobRow({
  index,
  job,
  robotName,
  pinned,
}: {
  index: number;
  job: MatchJob;
  robotName: string;
  pinned: boolean;
}) {
  const place = [job.company_name, job.locality].filter(Boolean).join(" · ");
  const work = jobExplanation({
    title: job.title,
    why: job.why,
    company: job.company_name,
    industry: job.industry,
  });
  return (
    <li className="border border-slate-600 bg-[#081126] px-4 py-4">
      <p className={JOBS_ROBOT_NAME_CLASS}>{robotName}</p>
      <p className={JOBS_JOB_TITLE_CLASS}>{job.title}</p>
      {place ? <p className={JOBS_PLACE_CLASS}>{place}</p> : null}
      {work && work !== job.title ? (
        <p className="mt-1.5 text-sm leading-snug text-slate-200">{work}</p>
      ) : null}
      <p className={JOBS_META_CLASS}>
        {jobIsForLabel(index, robotName)} ·{" "}
        {pinned ? "From your list" : "More from this match"}
      </p>
    </li>
  );
}
