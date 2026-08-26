/**
 * Step 03 CRM desk — collected Job Cards from step 02.
 * Hunt on FIND, collect here, enjoy Place this job when ready.
 * Not SIGNAL buyers. Not robot OEM shortlists.
 */
import { useEffect, useMemo, useState } from "react";
import { useLocation } from "wouter";
import {
  CRM_EMPLOYER_NAME_CLASS,
  CRM_INSPECT_HINT,
  CRM_LISTING_EYEBROW,
  CRM_PLACE_EGG_HINT,
  CRM_UNLOCKED_JOBS,
  JOBS_EYEBROW_CLASS,
  JOBS_KEEP_LABEL,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_PROCESS_STEPS,
  crmCollectedCountLabel,
  crmDeskJobKeys,
  crmSelectAllKeys,
  crmSelectAllLabel,
  crmSyncSelectedKeys,
  crmToggleSelectedKey,
  jobsCrmOpenHref,
  jobsFreshHomeHref,
  jobsWorkspaceRestoreHref,
  onJobsFreshHomeClick,
  pipelineActivityForJob,
  recordPipelineActivity,
  type PipelineActivityEvent,
} from "@/lib/jobsWorkflow";
import JobsPstackProtocol from "@/components/JobsPstackProtocol";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import { jobModelListLine, robotJobCardFromMatch } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";
import {
  JOBS_APPLY_CTA,
  JOBS_POC_PREFER_HINT,
  JOBS_POC_SKIP_CTA,
  applyStatusFromGaps,
  canApplyToJob,
  canLockQuote,
  lockQuoteUpdate,
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
  const allKeys = crmDeskJobKeys(jobs);
  const allKeySig = allKeys.join("\0");
  const [selectedKeys, setSelectedKeys] = useState<string[]>(() =>
    crmSelectAllKeys(allKeys),
  );
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  void tick;
  useEffect(() => {
    const pool = allKeySig ? allKeySig.split("\0") : [];
    setSelectedKeys(prev => crmSyncSelectedKeys(prev, pool));
  }, [allKeySig]);
  const stats = placementBoardStats(jobs);
  const selected = selectedKeys.filter(key => allKeys.includes(key));
  const expanded = jobs.find(j => j.job_key === expandedKey) || null;

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
        Collect jobs for {product}. Inspect an egg, then Place this job when you
        are ready. Quote the monthly rental you will charge. We do not invent
        it. Employers prefer proof of concept; you can skip it. Not a SIGNAL buyer list. Not an OEM roster.
      </p>
      {jobs.length > 0 ? (
        <p className="mt-3 font-mono text-sm uppercase tracking-[0.08em] text-emerald-300">
          {crmCollectedCountLabel(selected.length)}
          {" · "}
          Applied {stats.applied} of {stats.total}
          {" · "}
          Quoted {stats.quoted} of {stats.total}
          {stats.quotes[0] ? ` · Live quote ${stats.quotes[0]}` : ""}
        </p>
      ) : null}
      <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
        {CRM_INSPECT_HINT}
      </p>
      <div className="mt-4">
        <JobsPstackProtocol compact />
      </div>

      {jobs.length === 0 ? (
        <p className="mt-6 border border-slate-600 bg-[#081126] px-4 py-4 text-sm text-slate-300">
          No jobs in CRM yet. Find jobs for your robot, keep the rows checked,
          then Open CRM.
        </p>
      ) : (
        <div className="mt-6">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <p className={`${eyebrow} text-emerald-400`}>{CRM_LISTING_EYEBROW}</p>
            <button
              type="button"
              onClick={() => setSelectedKeys(crmSelectAllKeys(allKeys))}
              aria-label="Keep all collected jobs"
              className="border border-emerald-400/50 bg-emerald-400/10 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300 transition hover:border-emerald-400 hover:text-emerald-200"
            >
              {crmSelectAllLabel(jobs.length)}
            </button>
          </div>
          <ul className="space-y-3" aria-label="Collected jobs">
            {jobs.map((job, i) => {
              const card = robotJobCardFromMatch(job);
              const rec = loadJobApplyRecord(job.job_key);
              const gaps = jobCredentialGaps(job, rec);
              const chipLane = placementMoneyLane(gaps, rec);
              const on = selected.includes(job.job_key);
              const open = expanded?.job_key === job.job_key;
              return (
                <li
                  key={job.job_key}
                  className={`border bg-[#081126] ${
                    on ? "border-emerald-400" : "border-slate-600"
                  } ${open ? "bg-emerald-400/5" : ""}`}
                >
                  <div className="flex items-start">
                    <label
                      className="flex shrink-0 cursor-pointer flex-col items-center gap-1 self-stretch border-r border-slate-700 px-3 py-4"
                      onClick={e => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={on}
                        onChange={e =>
                          setSelectedKeys(keys =>
                            crmToggleSelectedKey(
                              keys,
                              job.job_key,
                              e.target.checked,
                            ),
                          )
                        }
                        aria-label={`${JOBS_KEEP_LABEL} ${card.jobTitle} in the basket`}
                        className="h-5 w-5 accent-emerald-400"
                      />
                      <span
                        className={`font-mono text-xs font-bold uppercase tracking-[0.08em] ${
                          on ? "text-emerald-300" : "text-slate-500"
                        }`}
                      >
                        {on ? JOBS_KEEP_LABEL : "Out"}
                      </span>
                    </label>
                    <button
                      type="button"
                      aria-expanded={open}
                      aria-label={`${open ? "Collapse" : "Inspect"} ${card.jobTitle}`}
                      onClick={() =>
                        setExpandedKey(open ? null : job.job_key)
                      }
                      data-crm-select="inspect-only"
                      className="flex min-w-0 flex-1 items-start gap-3 py-4 pr-4 text-left"
                    >
                      <span className="flex-1">
                        <span className="font-mono text-xs text-slate-500">
                          {String(i + 1).padStart(2, "0")} ·{" "}
                          {placementLaneLabel(chipLane)}
                        </span>
                        <span className="mt-1 block font-display text-lg font-bold leading-snug tracking-tight text-white sm:text-xl">
                          {card.jobTitle}
                        </span>
                        {card.employer ? (
                          <span className={`mt-0.5 block ${CRM_EMPLOYER_NAME_CLASS}`}>
                            {card.employer}
                          </span>
                        ) : null}
                        <span className="mt-1 block text-sm text-slate-400">
                          {[card.workplace, card.qualificationLabel]
                            .filter(Boolean)
                            .join(" · ")}
                        </span>
                        {jobModelListLine(job) ? (
                          <span className="mt-1 block font-mono text-sm text-slate-500">
                            {jobModelListLine(job)}
                          </span>
                        ) : null}
                      </span>
                      <span className="font-mono text-xs text-slate-500">
                        {open ? "−" : "+"}
                      </span>
                    </button>
                  </div>
                  {open ? (
                    <div className="border-t border-slate-700 px-4 pb-5 pt-4">
                      <CollectedJobInspect job={job} />
                      <ApplyPanel
                        key={job.job_key}
                        job={job}
                        robotName={product}
                        signedIn={signedIn}
                        onSaved={() => setTick(n => n + 1)}
                      />
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {submissionId ? (
        <p className="mt-6 font-mono text-xs text-slate-600">Submission {submissionId}</p>
      ) : null}
    </div>
  );
}

function CollectedJobInspect({ job }: { job: MatchJob }) {
  const card = robotJobCardFromMatch(job);
  return (
    <div>
      <p className={`${eyebrow} text-slate-400`}>Inspecting this egg</p>
      <dl className="mt-3 grid gap-2 text-[13px] leading-snug text-slate-200">
        <div>
          <dt className={eyebrow}>Employer</dt>
          <dd className={`mt-0.5 ${CRM_EMPLOYER_NAME_CLASS}`}>
            {card.employer || "Unnamed employer"}
          </dd>
        </div>
        <div>
          <dt className={eyebrow}>Workplace</dt>
          <dd className="mt-0.5">{card.workplace || "Site TBD"}</dd>
        </div>
        <div>
          <dt className={eyebrow}>Work being performed</dt>
          <dd className="mt-0.5">{card.work}</dd>
        </div>
        <div>
          <dt className={eyebrow}>{card.qualificationLabel}</dt>
          <dd className="mt-0.5 text-slate-300">{card.qualificationHint}</dd>
        </div>
      </dl>

      {card.taskModels.length || card.modelLinks.length ? (
        <div className="mt-3">
          <p className={eyebrow}>Task models</p>
          {card.taskModels.length ? (
            <ul className="mt-1 space-y-0.5">
              {card.taskModels.map(model => (
                <li
                  key={model.id}
                  className="text-[13px] leading-snug text-slate-200"
                >
                  {model.label}
                  <span className="text-slate-400">
                    {" "}
                    ·{" "}
                    {model.presence === "unknown"
                      ? "Not yet confirmed"
                      : model.presence === "present"
                        ? "Present"
                        : "Absent"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
          {card.modelContract ? (
            <div className="mt-2 space-y-0.5 text-[13px] leading-snug text-slate-300">
              <p className="text-slate-200">{card.modelContract.headline}</p>
              {card.modelContract.steps.length ? (
                <ol className="mt-1 space-y-1">
                  {card.modelContract.steps.map(step => (
                    <li key={`${step.n}-${step.label}`}>
                      <span className="font-mono text-emerald-400">{step.n}.</span>{" "}
                      <span className="text-slate-200">{step.label}.</span> {step.body}
                    </li>
                  ))}
                </ol>
              ) : (
                <>
                  {card.modelContract.layer ? <p>{card.modelContract.layer}</p> : null}
                  {card.modelContract.whoTrains ? (
                    <p>{card.modelContract.whoTrains}</p>
                  ) : null}
                  {card.modelContract.time ? <p>{card.modelContract.time}</p> : null}
                  {card.modelContract.youProvide ? (
                    <p>{card.modelContract.youProvide}</p>
                  ) : null}
                  {card.modelContract.fieldFeedback ? (
                    <p className="text-slate-400">{card.modelContract.fieldFeedback}</p>
                  ) : null}
                </>
              )}
            </div>
          ) : null}
        </div>
      ) : null}

      {card.openQuestions.length ? (
        <div className="mt-3">
          <p className={eyebrow}>Open questions</p>
          <ul className="mt-1 space-y-0.5">
            {card.openQuestions.map(w => (
              <li key={w} className="text-[13px] leading-snug text-amber-200/80">
                ? {w}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {card.requirements.length ? (
        <div className="mt-3">
          <p className={eyebrow}>Why this is listed</p>
          <ul className="mt-1 space-y-0.5">
            {card.requirements.map(w => (
              <li key={w} className="text-[13px] leading-snug text-slate-200">
                <span className="text-emerald-400">✓</span> {w}
              </li>
            ))}
          </ul>
        </div>
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
    if (next.pocSkipped && !record.pocSkipped) {
      note("place", "Skipped PoC");
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
      className="mt-6 border border-emerald-400/40 bg-[#0b162f] px-4 py-6 sm:px-6"
    >
      <p className={`${eyebrow} text-slate-400`}>Place this collected egg</p>
      <p className={`mt-2 ${CRM_EMPLOYER_NAME_CLASS}`}>
        {card.employer || "This employer"}
      </p>
      <p className="mt-1 text-sm text-slate-400">
        {card.workplace || "site TBD"}
      </p>
      <h2 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl">
        Your move: {nextLabel.replace(/ →$/, "")}
      </h2>
      <p className="mt-2 text-lg leading-relaxed text-slate-200">{brief}</p>
      {modelLine ? (
        <p className="mt-2 font-mono text-sm text-slate-400">{modelLine}</p>
      ) : null}
      <p className="mt-2 text-sm text-slate-500">{CRM_PLACE_EGG_HINT}</p>

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
              This is the money. Your quote, never a number we invent.
            </span>
            <input
              type="text"
              className="mt-4 w-full border border-emerald-400/50 bg-[#081126] px-4 py-4 text-xl text-slate-100"
              value={record.monthlyRental}
              onChange={e =>
                patch({ monthlyRental: e.target.value, quoteCommitted: false })
              }
              placeholder="e.g. your RaaS / lease quote per month"
            />
          </label>
          <label className="block">
            <span className={`${eyebrow} text-slate-400`}>
              PoC evidence (optional)
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              {JOBS_POC_PREFER_HINT}
            </span>
            <textarea
              className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
              rows={3}
              value={record.pocEvidence}
              onChange={e =>
                patch({
                  pocEvidence: e.target.value,
                  pocSkipped: false,
                  quoteCommitted: false,
                })
              }
              placeholder="Site demo, video, or written proof of concept — optional"
            />
          </label>
          {!record.pocSkipped && !(record.pocEvidence || "").trim() ? (
            <button
              type="button"
              onClick={() => patch({ pocSkipped: true })}
              className="border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300 transition hover:border-slate-400"
            >
              {JOBS_POC_SKIP_CTA}
            </button>
          ) : record.pocSkipped ? (
            <p className="font-mono text-xs uppercase tracking-[0.08em] text-slate-500">
              PoC skipped. Employers still prefer proof.
            </p>
          ) : null}
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
            onClick={() => patch(lockQuoteUpdate(record))}
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
            {event.company ? (
              <span className="text-emerald-400"> · {event.company}</span>
            ) : (
              ""
            )}
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
