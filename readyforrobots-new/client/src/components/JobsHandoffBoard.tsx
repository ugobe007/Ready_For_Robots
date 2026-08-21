/**
 * Activated Jobs list on /pipeline. Checked jobs from `/` sit at the top;
 * the rest of the 15 is filled from the same match. This is not SIGNAL
 * buyers and not a bounce back to FIND.
 */
import { Link } from "wouter";
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  JOBS_ACTIVATE_CAP,
  RAIL_STEP_HINT,
  jobsFreshHomeHref,
  jobsWorkspaceRestoreHref,
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
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
          Your robot
        </p>
        <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-slate-100">
          {product}
        </h2>
        <nav className="mt-6 space-y-1">
          <p className="border-l-2 border-transparent px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">
            01 Profile
          </p>
          <p className="border-l-2 border-transparent px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">
            02 Jobs
          </p>
          <p className="border-l-2 border-emerald-400 bg-emerald-400/5 px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300">
            03 Live list
          </p>
        </nav>
        <p className="mt-4 text-[12px] leading-snug text-slate-400">
          {RAIL_STEP_HINT.pipeline}
        </p>
        <ol className="mt-4 space-y-2 text-[12px] leading-snug text-slate-400">
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
          <Link
            href={jobsWorkspaceRestoreHref()}
            className="block font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 hover:text-slate-300"
          >
            Inspect jobs
          </Link>
          <Link
            href={jobsFreshHomeHref()}
            className="block font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 hover:text-slate-300"
          >
            + New robot
          </Link>
        </div>
      </aside>

      <main className="min-h-0 px-4 py-8 sm:px-6">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
          Live job list
        </p>
        <h1 className="mt-1 font-display text-2xl font-bold text-slate-100 sm:text-3xl">
          Jobs for {product}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300">
          You checked {selectedCount}. The list shows {jobs.length} of{" "}
          {JOBS_ACTIVATE_CAP}
          {filled > 0 ? ` (${filled} more from this match)` : ""}.
        </p>

        {jobs.length === 0 ? (
          <p className="mt-8 text-sm text-slate-400">
            No jobs were carried over.{" "}
            <Link href={jobsWorkspaceRestoreHref()} className="text-emerald-400 hover:text-emerald-300">
              Return to Jobs
            </Link>
            .
          </p>
        ) : (
          <ol className="mt-8 space-y-2">
            {jobs.map((job, i) => (
              <JobRow
                key={job.job_key}
                index={i + 1}
                job={job}
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
  pinned,
}: {
  index: number;
  job: MatchJob;
  pinned: boolean;
}) {
  const place = [job.company_name, job.locality].filter(Boolean).join(" · ");
  return (
    <li className="border border-slate-600 bg-[#081126] px-4 py-3">
      <p className="flex flex-wrap items-center gap-2 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
        <span>Job {String(index).padStart(2, "0")}</span>
        {pinned ? (
          <span className="text-emerald-400">From your list</span>
        ) : (
          <span>More from this match</span>
        )}
      </p>
      <p className="mt-1 font-display text-base font-bold leading-snug text-slate-100">
        {job.title}
      </p>
      {place ? <p className="mt-0.5 text-xs text-slate-400">{place}</p> : null}
    </li>
  );
}
