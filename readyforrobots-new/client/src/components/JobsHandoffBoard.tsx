/**
 * Step 3 on /pipeline — confirm and save. Step 2 already showed the jobs.
 * This is not a second card list.
 */
import { Link } from "wouter";
import {
  JOBS_ACTIVATE_CAP,
  JOBS_ACTIVATE_SRC,
  JOBS_EYEBROW_CLASS,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_RAIL_LINK_CLASS,
  JOBS_SAVE_TO_CRM_CTA,
  JOBS_SAVE_TO_CRM_HINT,
  RAIL_STEP_HINT,
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
            03 Activate
          </p>
        </nav>
        <p className="mt-4 text-sm leading-relaxed text-slate-300">
          {RAIL_STEP_HINT.pipeline}
        </p>
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
        <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>Save this list</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Activate jobs for {product}
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-300">
          {jobs.length === 0
            ? "No jobs were carried over. Inspect jobs to rebuild the list."
            : `${selectedCount} checked · ${jobs.length} in this list. ${JOBS_SAVE_TO_CRM_HINT}`}
        </p>
        <a
          href={
            _props.signedIn
              ? "/crm"
              : jobsSignupHref(jobsActivateHref(), JOBS_ACTIVATE_SRC)
          }
          className="mt-6 inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
        >
          {JOBS_SAVE_TO_CRM_CTA}
        </a>
        {jobs.length === 0 ? (
          <p className="mt-8 text-base text-slate-300">
            <Link href={jobsWorkspaceRestoreHref()} className="text-emerald-400 hover:text-emerald-300">
              Return to Jobs
            </Link>
          </p>
        ) : (
          <p className="mt-6 font-mono text-sm uppercase tracking-[0.08em] text-slate-500">
            {jobs.length} jobs ready — open Inspect jobs if you need the cards again.
          </p>
        )}
      </main>
    </div>
  );
}
