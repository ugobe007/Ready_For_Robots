/**
 * Jobs CRM desk on /pipeline?src=jobs_activate — checked Job Cards, Apply rectify.
 * Not SIGNAL buyers. Not robot OEM shortlists.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  CRM_UNLOCKED_JOBS,
  JOBS_EYEBROW_CLASS,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  jobsFreshHomeHref,
  onJobsFreshHomeClick,
} from "@/lib/jobsWorkflow";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import { jobModelListLine, robotJobCardFromMatch } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  JOBS_APPLY_CTA,
  applyStatusFromGaps,
  canApplyToJob,
  followUpNextStep,
  jobCredentialGaps,
  loadJobApplyRecord,
  placementOutreachDraft,
  placementWorkflowStrategy,
  saveJobApplyRecord,
  type JobApplyRecord,
} from "@/lib/jobsApply";

const eyebrow = JOBS_EYEBROW_CLASS;

export default function JobsCrmDesk({
  signedIn = false,
  submissionId = null,
}: {
  signedIn?: boolean;
  submissionId?: number | null;
}) {
  const snap = readJobsHandoffSnapshot();
  const jobs = (snap?.jobs || []).slice(0, CRM_UNLOCKED_JOBS);
  const product = snap?.productName || "your robot";
  const [activeKey, setActiveKey] = useState(jobs[0]?.job_key || "");
  const [tick, setTick] = useState(0);
  const active = jobs.find(j => j.job_key === activeKey) || jobs[0] || null;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 pb-10 pt-4">
      <p className={`${eyebrow} text-emerald-400`}>Step 03 · CRM</p>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
        CRM
      </h1>
      <p className="mt-2 max-w-2xl text-lg leading-relaxed text-slate-200">
        {jobs.length} job{jobs.length === 1 ? "" : "s"} for {product} from the
        rows you kept. Select a job, then Apply to jobs — models, PoC evidence,
        and the monthly rental you will charge. No SIGNAL buyers. No OEM roster.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        {active ? (
          <a
            href="#jobs-apply"
            className="inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          >
            {JOBS_APPLY_CTA}
          </a>
        ) : null}
        <a
          href={jobsFreshHomeHref()}
          onClick={onJobsFreshHomeClick}
          className="inline-flex font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
        >
          + New robot
        </a>
      </div>

      {jobs.length === 0 ? (
        <p className="mt-6 border border-slate-600 bg-[#081126] px-4 py-4 text-sm text-slate-300">
          No jobs in CRM yet. Find jobs for your robot, keep the rows checked,
          then Next.
        </p>
      ) : (
        <ul className="mt-6 space-y-2">
          {jobs.map((job, i) => {
            const card = robotJobCardFromMatch(job);
            const modelLine = jobModelListLine(job);
            const on = job.job_key === active?.job_key;
            const rec = loadJobApplyRecord(job.job_key);
            const gaps = jobCredentialGaps(job, rec);
            const status = applyStatusFromGaps(gaps, rec);
            void tick;
            return (
              <li key={job.job_key}>
                <button
                  type="button"
                  onClick={() => setActiveKey(job.job_key)}
                  className={`flex w-full items-start gap-3 border px-4 py-3 text-left ${
                    on ? "border-emerald-400/70 bg-emerald-400/5" : "border-slate-600 bg-[#081126]"
                  }`}
                >
                  <span className="font-mono text-sm text-emerald-400">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-display text-lg font-bold text-white">
                      {card.jobTitle}
                    </span>
                    <span className="mt-0.5 block text-sm text-slate-400">
                      {[card.employer, card.workplace].filter(Boolean).join(" · ")}
                    </span>
                    {modelLine ? (
                      <span className="mt-0.5 block font-mono text-sm text-slate-400">
                        {modelLine}
                      </span>
                    ) : null}
                    <span className="mt-1 block font-mono text-xs uppercase tracking-[0.08em] text-emerald-300">
                      {status === "blocked"
                        ? "Blocked"
                        : status === "ready"
                          ? "Ready"
                          : status === "applied"
                            ? "Applied"
                            : "Follow-up"}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {active ? (
        <ApplyPanel
          key={active.job_key}
          job={active}
          robotName={product}
          signedIn={signedIn}
          onSaved={() => setTick(n => n + 1)}
        />
      ) : null}

      {submissionId ? (
        <p className="mt-6 font-mono text-xs text-slate-600">Submission {submissionId}</p>
      ) : null}
      <p className="mt-4 font-mono text-xs text-slate-500">
        {JOBS_FOR_YOUR_ROBOT_HEADING} · {signedIn ? "signed in" : "sign in to store follow-up"}
      </p>
    </div>
  );
}

function ApplyPanel({
  job,
  robotName,
  signedIn,
  onSaved,
}: {
  job: MatchJob;
  robotName: string;
  signedIn: boolean;
  onSaved: () => void;
}) {
  const [record, setRecord] = useState<JobApplyRecord>(() =>
    loadJobApplyRecord(job.job_key),
  );
  useEffect(() => {
    setRecord(loadJobApplyRecord(job.job_key));
  }, [job.job_key]);
  const gaps = useMemo(() => jobCredentialGaps(job, record), [job, record]);
  const status = applyStatusFromGaps(gaps, record);
  const ready = canApplyToJob(gaps, record);
  const draft = placementOutreachDraft(job, record, robotName);
  const strategy = placementWorkflowStrategy(gaps, record);

  function persist(saved: JobApplyRecord) {
    setRecord(saved);
    saveJobApplyRecord(saved);
    onSaved();
  }

  function patch(next: Partial<JobApplyRecord>) {
    const merged = { ...record, jobKey: job.job_key, ...next };
    const nextGaps = jobCredentialGaps(job, merged);
    const nextStatus = applyStatusFromGaps(nextGaps, merged);
    persist({ ...merged, status: nextStatus });
  }

  function apply() {
    if (!ready) return;
    persist({
      ...record,
      jobKey: job.job_key,
      status: "applied",
      appliedAt: new Date().toISOString(),
    });
  }

  function followUp() {
    persist({
      ...record,
      jobKey: job.job_key,
      status: "follow_up",
      followUpAt: new Date().toISOString(),
    });
  }

  return (
    <section
      id="jobs-apply"
      className="mt-8 border border-slate-600 bg-[#0b162f] px-4 py-5 sm:px-5"
    >
      <p className={`${eyebrow} text-emerald-400`}>Apply to this job</p>
      <h2 className="mt-2 font-display text-2xl font-bold text-white">
        {robotJobCardFromMatch(job).jobTitle}
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-300">
        Does this OEM or distributor have the credentials to apply? Close every
        gap. We do not invent a monthly rate.
      </p>
      <p className="mt-2 font-mono text-sm uppercase tracking-[0.08em] text-emerald-300">
        {status === "blocked"
          ? "Blocked — missing credentials"
          : status === "ready"
            ? "Ready to apply"
            : status === "applied"
              ? "Applied — track follow-up"
              : "Follow-up open"}
      </p>

      <div className="mt-4 border border-slate-700 bg-[#081126] px-3 py-3">
        <p className={`${eyebrow} text-slate-400`}>Workflow strategy</p>
        <p className="mt-1 text-sm leading-relaxed text-slate-200">{strategy}</p>
      </div>

      <ol className="mt-4 space-y-3">
        {gaps.map((gap, i) => (
          <li key={gap.id} className="text-sm leading-snug text-slate-200">
            <span className="font-mono text-emerald-400">{i + 1}.</span>{" "}
            <span className={gap.met ? "text-emerald-300" : "text-amber-200"}>
              {gap.met ? "Met" : "Missing"}
            </span>
            {" · "}
            <span className="text-slate-100">{gap.label}.</span> {gap.howToFix}
          </li>
        ))}
      </ol>

      <label className="mt-5 flex cursor-pointer items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 accent-emerald-400"
          checked={record.packAcknowledged}
          onChange={e => patch({ packAcknowledged: e.target.checked })}
        />
        <span className="text-sm text-slate-200">
          We can license or already carry the task-library pack for this work
          (OEM or distributor). We will not train a foundation VLA.
        </span>
      </label>

      <label className="mt-4 block">
        <span className={`${eyebrow} text-slate-400`}>PoC evidence</span>
        <textarea
          className="mt-1 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
          rows={3}
          value={record.pocEvidence}
          onChange={e => patch({ pocEvidence: e.target.value })}
          placeholder="Site demo, video, or written proof of concept"
        />
      </label>

      <label className="mt-4 block">
        <span className={`${eyebrow} text-slate-400`}>
          Monthly rental you will charge the employer
        </span>
        <input
          type="text"
          className="mt-1 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
          value={record.monthlyRental}
          onChange={e => patch({ monthlyRental: e.target.value })}
          placeholder="Your quote — not a number we invent"
        />
      </label>

      <div className="mt-5">
        <p className={`${eyebrow} text-slate-400`}>Outreach</p>
        <pre className="mt-1 whitespace-pre-wrap border border-slate-700 bg-[#081126] px-3 py-3 text-sm leading-relaxed text-slate-300">
          {draft}
        </pre>
      </div>

      <p className="mt-4 text-sm text-slate-300">{followUpNextStep(record)}</p>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={apply}
          disabled={!ready}
          className="inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Apply to this job
        </button>
        {record.status === "applied" || record.status === "follow_up" ? (
          <button
            type="button"
            onClick={followUp}
            className="inline-flex items-center justify-center border border-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-emerald-200 transition hover:bg-emerald-400/10"
          >
            Track follow-up
          </button>
        ) : null}
        {!signedIn ? (
          <Link
            href="/signup?src=jobs_activate&next=/pipeline?src=jobs_activate"
            className="inline-flex items-center font-mono text-sm font-semibold uppercase tracking-[0.08em] text-slate-400 hover:text-slate-200"
          >
            Sign in to keep this desk
          </Link>
        ) : null}
      </div>
    </section>
  );
}

/** Used when a leftover import still names a full-page desk. */
export function JobsCrmDeskPage(props: {
  signedIn?: boolean;
  submissionId?: number | null;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-[#081126] pt-14">
      <JobsCrmDesk {...props} />
    </div>
  );
}
