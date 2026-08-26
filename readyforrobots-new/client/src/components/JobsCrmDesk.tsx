/**
 * Step 03 CRM desk — kept Job Cards from step 02, Place as the money action.
 * Not SIGNAL buyers. Not robot OEM shortlists.
 */
import { useEffect, useMemo, useState } from "react";
import { useLocation } from "wouter";
import {
  CRM_UNLOCKED_JOBS,
  JOBS_EYEBROW_CLASS,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_PROCESS_STEPS,
  jobsCrmOpenHref,
  jobsFreshHomeHref,
  jobsWorkspaceRestoreHref,
  onJobsFreshHomeClick,
  pipelineActivityForJob,
  recordPipelineActivity,
  type PipelineActivityEvent,
} from "@/lib/jobsWorkflow";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import { jobModelListLine, robotJobCardFromMatch } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  JOBS_APPLY_CTA,
  applyStatusFromGaps,
  canApplyToJob,
  canLockQuote,
  followUpNextStep,
  jobCredentialGaps,
  loadJobApplyRecord,
  placementAgentBrief,
  placementBoardStats,
  placementLaneLabel,
  placementMoneyLane,
  placementNextActionLabel,
  placementOutreachDraft,
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
  const [, setLocation] = useLocation();
  useEffect(() => {
    if (signedIn) return;
    setLocation(jobsCrmOpenHref(false, submissionId));
  }, [signedIn, submissionId, setLocation]);

  const snap = readJobsHandoffSnapshot();
  const jobs = (snap?.jobs || []).slice(0, CRM_UNLOCKED_JOBS);
  const product = snap?.productName || "your robot";
  const [activeKey, setActiveKey] = useState(jobs[0]?.job_key || "");
  const [tick, setTick] = useState(0);
  const active = jobs.find(j => j.job_key === activeKey) || jobs[0] || null;
  void tick;
  const stats = placementBoardStats(jobs);
  const activeRec = active ? loadJobApplyRecord(active.job_key) : null;

  if (!signedIn) {
    return (
      <p className="px-6 py-16 text-center font-mono text-sm uppercase tracking-[0.08em] text-slate-400">
        Opening CRM…
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-12 pt-4">
      <nav
        aria-label="Jobs process"
        className="rfr-jobs-process-bar mb-6 flex flex-wrap items-stretch border border-slate-600"
      >
        {JOBS_PROCESS_STEPS.map(step => {
          const current = step.id === "activate";
          const href =
            step.id === "find"
              ? jobsFreshHomeHref()
              : step.id === "jobs"
                ? jobsWorkspaceRestoreHref()
                : undefined;
          const className = `flex min-w-0 flex-1 items-center px-3 py-3 ${JOBS_PROCESS_NAV_CLASS} ${
            current
              ? "border-b-2 border-emerald-400 bg-emerald-400/5 text-emerald-300"
              : "border-b-2 border-transparent text-slate-400 hover:text-slate-200"
          }`;
          if (href) {
            return (
              <a
                key={step.id}
                href={href}
                onClick={step.id === "find" ? onJobsFreshHomeClick : undefined}
                className={className}
              >
                {step.n} {step.label}
              </a>
            );
          }
          return (
            <span key={step.id} aria-current="step" className={className}>
              {step.n} {step.label}
            </span>
          );
        })}
      </nav>

      <p className={`${eyebrow} text-emerald-400`}>Step 03 · CRM</p>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
        CRM
      </h1>
      <p className="mt-3 max-w-3xl text-lg leading-relaxed text-slate-200 sm:text-xl">
        Place {product}. {jobs.length} job{jobs.length === 1 ? "" : "s"} from
        the rows you kept. Quote the monthly rental you will charge, then Place
        this job. Revenue is the number you type — we do not invent it.
        Not a SIGNAL buyer list. Not an OEM roster.
      </p>
      {jobs.length > 0 ? (
        <p className="mt-3 font-mono text-sm uppercase tracking-[0.08em] text-emerald-300">
          Applied {stats.applied} of {stats.total}
          {" · "}
          Quoted {stats.quoted} of {stats.total}
          {stats.quotes[0] ? ` · Live quote ${stats.quotes[0]}` : ""}
          {active && activeRec
            ? ` · Your move: ${placementNextActionLabel(active, activeRec)}`
            : ""}
        </p>
      ) : null}

      {jobs.length === 0 ? (
        <p className="mt-6 border border-slate-600 bg-[#081126] px-4 py-4 text-sm text-slate-300">
          No jobs in CRM yet. Find jobs for your robot, keep the rows checked,
          then Open CRM.
        </p>
      ) : (
        <ul className="mt-6 flex gap-2 overflow-x-auto pb-1">
          {jobs.map((job, i) => {
            const card = robotJobCardFromMatch(job);
            const rec = loadJobApplyRecord(job.job_key);
            const gaps = jobCredentialGaps(job, rec);
            const chipLane = placementMoneyLane(gaps, rec);
            const on = job.job_key === active?.job_key;
            return (
              <li key={job.job_key} className="min-w-[10.5rem] flex-1">
                <button
                  type="button"
                  onClick={() => setActiveKey(job.job_key)}
                  className={`flex h-full w-full flex-col items-start border px-3 py-3 text-left ${
                    on
                      ? "border-emerald-400 bg-emerald-400/10"
                      : "border-slate-600 bg-[#081126]"
                  }`}
                >
                  <span className="font-mono text-xs text-emerald-400">
                    {String(i + 1).padStart(2, "0")} · {placementLaneLabel(chipLane)}
                  </span>
                  <span className="mt-1 font-display text-base font-bold leading-snug text-white">
                    {card.employer || card.jobTitle}
                  </span>
                  <span className="mt-0.5 line-clamp-2 text-sm text-slate-400">
                    {card.jobTitle}
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
    </div>
  );
}

function ApplyPanel({
  job,
  robotName,
  signedIn: _signedIn,
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
  const ready = canApplyToJob(gaps, record);
  const draft = placementOutreachDraft(job, record, robotName);
  const brief = placementAgentBrief(job, record, robotName);
  const lane = placementMoneyLane(gaps, record);
  const card = robotJobCardFromMatch(job);
  const modelLine = jobModelListLine(job);

  function note(kind: PipelineActivityEvent["kind"], label: string) {
    recordPipelineActivity({
      kind,
      label,
      jobKey: job.job_key,
      company: robotJobCardFromMatch(job).employer || undefined,
    });
  }

  function persist(saved: JobApplyRecord) {
    setRecord(saved);
    saveJobApplyRecord(saved);
    onSaved();
  }

  function patch(next: Partial<JobApplyRecord>) {
    const merged = { ...record, jobKey: job.job_key, ...next };
    const nextGaps = jobCredentialGaps(job, merged);
    const nextStatus = applyStatusFromGaps(nextGaps, merged);
    if (next.packAcknowledged && !record.packAcknowledged) {
      note("place", "Confirmed pack");
    }
    if (next.quoteCommitted && !record.quoteCommitted) {
      note("place", "Locked quote");
    }
    persist({ ...merged, status: nextStatus });
  }

  function apply() {
    if (!ready) return;
    note("apply", "Applied");
    persist({
      ...record,
      jobKey: job.job_key,
      status: "applied",
      appliedAt: new Date().toISOString(),
    });
  }

  function followUp() {
    note("follow_up", "Followed up");
    persist({
      ...record,
      jobKey: job.job_key,
      status: "follow_up",
      followUpAt: new Date().toISOString(),
    });
  }

  const nextLabel = placementNextActionLabel(job, record);
  const quoteReady = canLockQuote(gaps, record);

  return (
    <section
      id="jobs-apply"
      className="mt-8 border border-emerald-400/40 bg-[#0b162f] px-4 py-6 sm:px-6"
    >
      <p className={`${eyebrow} text-emerald-400`}>
        {card.employer || "This employer"} · {card.workplace || "site TBD"}
      </p>
      <h2 className="mt-2 font-display text-3xl font-bold text-white sm:text-4xl">
        Your move: {nextLabel.replace(/ →$/, "")}
      </h2>
      <p className="mt-2 text-lg leading-relaxed text-slate-200">{brief}</p>
      {modelLine ? (
        <p className="mt-2 font-mono text-sm text-slate-400">{modelLine}</p>
      ) : null}

      {lane === "pack" ? (
        <p className="mt-6 max-w-2xl text-sm leading-relaxed text-slate-400">
          {gaps.find(g => g.id === "model_pack")?.howToFix}
        </p>
      ) : null}

      {lane === "quote" ? (
        <div className="mt-6 max-w-2xl space-y-5">
          <label className="block">
            <span className="block font-display text-2xl font-bold text-white">
              Monthly rental you will charge
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              This is the money. Your quote — never a number we invent.
            </span>
            <input
              type="text"
              className="mt-4 w-full border border-emerald-400/50 bg-[#081126] px-4 py-4 text-xl text-slate-100"
              value={record.monthlyRental}
              onChange={e => patch({ monthlyRental: e.target.value, quoteCommitted: false })}
              placeholder="e.g. your RaaS / lease quote per month"
            />
          </label>
          <label className="block">
            <span className={`${eyebrow} text-slate-400`}>PoC evidence</span>
            <textarea
              className="mt-1 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
              rows={3}
              value={record.pocEvidence}
              onChange={e => patch({ pocEvidence: e.target.value, quoteCommitted: false })}
              placeholder="Site demo, video, or written proof of concept"
            />
          </label>
        </div>
      ) : null}

      {lane === "apply" || lane === "track" ? (
        <div className="mt-6 max-w-3xl">
          <p className={`${eyebrow} text-slate-400`}>Outreach ready to send</p>
          <pre className="mt-2 whitespace-pre-wrap border border-slate-700 bg-[#081126] px-4 py-4 text-sm leading-relaxed text-slate-300">
            {draft}
          </pre>
          {lane === "track" ? (
            <p className="mt-3 text-sm text-slate-300">{followUpNextStep(record)}</p>
          ) : null}
        </div>
      ) : null}

      <div className="mt-8 flex flex-wrap items-center gap-3">
        {lane === "pack" ? (
          <button
            type="button"
            onClick={() => patch({ packAcknowledged: true })}
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          >
            {nextLabel}
          </button>
        ) : null}
        {lane === "quote" ? (
          <button
            type="button"
            onClick={() => patch({ quoteCommitted: true })}
            disabled={!quoteReady}
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {nextLabel}
          </button>
        ) : null}
        {lane === "apply" ? (
          <button
            type="button"
            onClick={apply}
            disabled={!ready}
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {JOBS_APPLY_CTA}
          </button>
        ) : null}
        {lane === "track" ? (
          <button
            type="button"
            onClick={followUp}
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          >
            {nextLabel}
          </button>
        ) : null}
      </div>

      <PipelineActivity jobKey={job.job_key} tick={record.status} />
    </section>
  );
}

function PipelineActivity({
  jobKey,
  tick,
}: {
  jobKey: string;
  tick: string;
}) {
  void tick;
  const events = pipelineActivityForJob(jobKey).slice(0, 8);
  if (events.length === 0) return null;
  return (
    <div className="mt-8 border-t border-slate-700 pt-5">
      <p className={`${eyebrow} text-slate-400`}>Pipeline activity</p>
      <ul className="mt-2 space-y-1.5">
        {events.map((event, i) => (
          <li
            key={`${event.at}-${event.kind}-${i}`}
            className="font-mono text-sm text-slate-400"
          >
            {event.label}
            {event.company ? ` · ${event.company}` : ""}
            <span className="text-slate-600">
              {" · "}
              {formatActivityWhen(event.at)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function formatActivityWhen(iso: string): string {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return iso;
  return new Date(t).toLocaleString();
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
