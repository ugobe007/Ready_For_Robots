/**
 * Step 03 Place desk — money moment for kept Job Cards.
 * Not SIGNAL buyers. Not robot OEM shortlists. Not a stale CRM dump.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  CRM_UNLOCKED_JOBS,
  JOBS_EYEBROW_CLASS,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_PROCESS_STEPS,
  jobsFreshHomeHref,
  jobsWorkspaceRestoreHref,
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
  placementAgentBrief,
  placementBoardStats,
  placementLaneLabel,
  placementMoneyLane,
  placementOutreachDraft,
  saveJobApplyRecord,
  type JobApplyRecord,
  type PlacementLane,
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
  void tick;
  const stats = placementBoardStats(jobs);
  const activeRec = active ? loadJobApplyRecord(active.job_key) : null;
  const activeGaps = active && activeRec ? jobCredentialGaps(active, activeRec) : [];
  const lane = active && activeRec ? placementMoneyLane(activeGaps, activeRec) : "pack";

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

      <p className={`${eyebrow} text-emerald-400`}>Step 03 · the money moment</p>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
        Place {product}.
      </h1>
      <p className="mt-3 max-w-3xl text-lg leading-relaxed text-slate-200 sm:text-xl">
        {jobs.length} employer{jobs.length === 1 ? "" : "s"} have named work.
        Quote the monthly rental you will charge. Apply. Revenue on these jobs
        is the number you type — we do not invent it. Not a SIGNAL buyer list.
        Not an OEM roster.
      </p>
      {jobs.length > 0 ? (
        <p className="mt-3 font-mono text-sm uppercase tracking-[0.08em] text-emerald-300">
          Applied {stats.applied} of {stats.total}
          {" · "}
          Quoted {stats.quoted} of {stats.total}
          {stats.quotes[0] ? ` · Live quote ${stats.quotes[0]}` : ""}
          {active ? ` · Your move: ${placementLaneLabel(lane)}` : ""}
        </p>
      ) : null}

      {jobs.length === 0 ? (
        <p className="mt-6 border border-slate-600 bg-[#081126] px-4 py-4 text-sm text-slate-300">
          No jobs to place yet. Find jobs for your robot, keep the rows checked,
          then Next.
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
  const brief = placementAgentBrief(job, record, robotName);
  const lane = placementMoneyLane(gaps, record);
  const card = robotJobCardFromMatch(job);
  const modelLine = jobModelListLine(job);

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

  const lanes: PlacementLane[] = ["pack", "quote", "apply"];

  return (
    <section
      id="jobs-apply"
      className="mt-8 border border-emerald-400/40 bg-[#0b162f] px-4 py-6 sm:px-6"
    >
      <p className={`${eyebrow} text-emerald-400`}>This job</p>
      <h2 className="mt-2 font-display text-3xl font-bold text-white">
        {card.jobTitle}
      </h2>
      <p className="mt-1 text-base text-slate-300">
        {[card.employer, card.workplace].filter(Boolean).join(" · ")}
      </p>
      {modelLine ? (
        <p className="mt-1 font-mono text-sm text-slate-400">{modelLine}</p>
      ) : null}

      <div className="mt-5 border border-emerald-400/30 bg-emerald-400/5 px-4 py-4">
        <p className={`${eyebrow} text-emerald-300`}>Your move</p>
        <p className="mt-2 text-base leading-relaxed text-slate-100">{brief}</p>
      </div>

      <ol className="mt-5 grid grid-cols-3 gap-2">
        {lanes.map((id, i) => {
          const on = lane === id || (lane === "track" && id === "apply");
          const done =
            (id === "pack" && gaps.find(g => g.id === "model_pack")?.met) ||
            (id === "quote" &&
              gaps.find(g => g.id === "poc_evidence")?.met &&
              gaps.find(g => g.id === "monthly_rental")?.met) ||
            (id === "apply" && (status === "applied" || status === "follow_up"));
          return (
            <li
              key={id}
              className={`border px-3 py-2 ${
                on
                  ? "border-emerald-400 bg-emerald-400/10 text-emerald-200"
                  : done
                    ? "border-slate-600 text-emerald-400/80"
                    : "border-slate-700 text-slate-500"
              }`}
            >
              <span className={`${eyebrow} block`}>
                0{i + 1} {id === "pack" ? "Pack" : id === "quote" ? "Quote" : "Apply"}
              </span>
            </li>
          );
        })}
      </ol>

      {lane === "pack" ? (
        <label className="mt-6 flex cursor-pointer items-start gap-3 border border-slate-600 bg-[#081126] px-4 py-4">
          <input
            type="checkbox"
            className="mt-1 h-5 w-5 accent-emerald-400"
            checked={record.packAcknowledged}
            onChange={e => patch({ packAcknowledged: e.target.checked })}
          />
          <span>
            <span className="block font-display text-lg font-bold text-white">
              Confirm the pack
            </span>
            <span className="mt-1 block text-sm leading-relaxed text-slate-300">
              {gaps.find(g => g.id === "model_pack")?.howToFix}
            </span>
          </span>
        </label>
      ) : null}

      {lane === "quote" ? (
        <div className="mt-6 space-y-4">
          <label className="block">
            <span className="block font-display text-lg font-bold text-white">
              Monthly rental you will charge
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              This is the money. Your quote — never a number we invent.
            </span>
            <input
              type="text"
              className="mt-3 w-full border border-emerald-400/50 bg-[#081126] px-4 py-3 text-lg text-slate-100"
              value={record.monthlyRental}
              onChange={e => patch({ monthlyRental: e.target.value })}
              placeholder="e.g. your RaaS / lease quote per month"
            />
          </label>
          <label className="block">
            <span className={`${eyebrow} text-slate-400`}>PoC evidence</span>
            <textarea
              className="mt-1 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
              rows={3}
              value={record.pocEvidence}
              onChange={e => patch({ pocEvidence: e.target.value })}
              placeholder="Site demo, video, or written proof of concept"
            />
          </label>
        </div>
      ) : null}

      {lane === "apply" || lane === "track" ? (
        <div className="mt-6">
          <p className={`${eyebrow} text-slate-400`}>Outreach ready to send</p>
          <pre className="mt-2 whitespace-pre-wrap border border-slate-700 bg-[#081126] px-4 py-4 text-sm leading-relaxed text-slate-300">
            {draft}
          </pre>
          <p className="mt-3 text-sm text-slate-300">{followUpNextStep(record)}</p>
        </div>
      ) : null}

      <div className="mt-6 flex flex-wrap gap-3">
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
