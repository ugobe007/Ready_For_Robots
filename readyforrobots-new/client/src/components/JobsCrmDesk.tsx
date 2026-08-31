/**
 * Jobs CRM desk. Jobs the OEM kept, then apply from here.
 * Not SIGNAL buyers. Not robot OEM shortlists.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "wouter";
import {
  CRM_EMPLOYER_NAME_CLASS,
  CRM_LEAVE_HINT,
  CRM_LISTING_EYEBROW,
  CRM_SIGNUP_NEXT_CTA,
  CRM_UNLOCKED_JOBS,
  CRM_WALL_LEAD,
  JOBS_EYEBROW_CLASS,
  JOBS_KEEP_LABEL,
  crmCollectedCountLabel,
  crmEmptyDeskHint,
  crmSaveJobsBlurb,
  crmDeskJobKeys,
  crmSelectAllKeys,
  crmSyncSelectedKeys,
  crmToggleSelectedKey,
  jobsCrmLeaveHref,
  jobsCrmLeaveLabel,
  jobsCrmNextHref,
  jobsCrmOpenHref,
  onJobsFreshHomeClick,
  pipelineActivityForJob,
  recordPipelineActivity,
  type PipelineActivityEvent,
} from "@/lib/jobsWorkflow";
import ExperimentHeader from "@/components/ExperimentHeader";
import JobsProcessChrome from "@/components/JobsProcessChrome";
import { readJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";
import { jobModelListLine, robotJobCardFromMatch } from "@/lib/robotJobCard";
import type { MatchJob } from "@/lib/robotJobMatch";
import JobsKeepStatusBar from "@/components/JobsKeepStatusBar";
import JobsCrmNextSteps from "@/components/JobsCrmNextSteps";
import JobsCrmInbox from "@/components/JobsCrmInbox";
import {
  JOBS_APPLY_SELECTED_CTA,
  JOBS_APPLY_SEQUENCE,
  JOBS_APPLY_CTA_CLASS,
  WORK_TASK_MODEL_QUESTION,
  WORK_TASK_MODEL_SELF_OPTION,
  WORK_TASK_MODEL_SOURCE_HINT,
  WORK_TASK_MODEL_SOURCE_OPTION,
  WORK_TASK_MODEL_SOURCE_PLACEHOLDER,
  WORK_TASK_MODEL_SOURCE_REQUIRED,
  WORK_TASK_MODEL_UNKNOWN_HINT,
  fetchKeptJobs,
  isJobsCrmOfferQuery,
  jobsCrmOfferHref,
  keepJobsOnAccount,
  openJobsCrmNextStepsForm,
  parseWorkTaskModel,
  saveWorkTaskModelOnAccount,
  workTaskModelListLine,
  crmDeskForCurrentRobot,
  postJobsCrmActivity,
  type JobsCrmApplication,
  type KeptJobRow,
  type WorkTaskModelAnswer,
  type WorkTaskModelKind,
} from "@/lib/jobsCrmAccount";
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
  authReady = true,
  accessToken = null,
  submissionId = null,
}: {
  signedIn?: boolean;
  authReady?: boolean;
  accessToken?: string | null;
  submissionId?: number | null;
}) {
  const [, setLocation] = useLocation();
  useEffect(() => {
    if (!authReady || signedIn) return;
    const dest = jobsCrmOpenHref(false, submissionId);
    setLocation(dest);
    if (typeof window !== "undefined") {
      window.location.assign(dest);
    }
  }, [authReady, signedIn, submissionId, setLocation]);

  const snap = readJobsHandoffSnapshot();
  const [accountRows, setAccountRows] = useState<KeptJobRow[]>([]);
  const [justSavedCount, setJustSavedCount] = useState(0);
  const [showNextSteps, setShowNextSteps] = useState(() =>
    typeof window !== "undefined"
      ? isJobsCrmOfferQuery(window.location.search)
      : false,
  );
  const [applications, setApplications] = useState<
    Record<string, JobsCrmApplication>
  >({});
  useEffect(() => {
    if (!showNextSteps) return;
    const timer = window.setTimeout(() => openJobsCrmNextStepsForm(), 40);
    return () => window.clearTimeout(timer);
  }, [showNextSteps]);
  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    fetchKeptJobs(accessToken)
      .then(rows => {
        if (cancelled) return;
        setAccountRows(rows);
        const apps: Record<string, JobsCrmApplication> = {};
        for (const row of rows) {
          if (row.application) apps[row.job_key] = row.application;
        }
        setApplications(apps);
      })
      .catch(() => {
        /* handoff still paints */
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);
  const desk = crmDeskForCurrentRobot({ snap, accountRows });
  const jobs = desk.jobs.slice(0, CRM_UNLOCKED_JOBS);
  const product = desk.product;
  const robotUrl = desk.robotUrl;
  const savedCount = Math.max(justSavedCount, desk.savedCount);
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
  const jobCount = jobs.length;
  const offerJob = expanded || jobs.find(j => selected.includes(j.job_key)) || jobs[0] || null;
  const rowByKey = useMemo(() => {
    const map = new Map<string, KeptJobRow>();
    for (const row of desk.rows) map.set(row.job_key, row);
    return map;
  }, [desk.rows]);

  function mergeKeptRow(row: KeptJobRow) {
    setAccountRows(prev => {
      const idx = prev.findIndex(item => item.job_key === row.job_key);
      if (idx < 0) return [row, ...prev];
      const next = [...prev];
      next[idx] = { ...prev[idx], ...row };
      return next;
    });
  }

  async function persistKeptJobs(
    keys: string[] = selected,
    opts: { openOffer?: boolean } = {},
  ) {
    const picked = jobs.filter(j => keys.includes(j.job_key));
    const pool = picked.length ? picked : jobs;
    if (!pool.length) return;
    const openOffer = opts.openOffer === true;
    for (const job of pool) {
      recordPipelineActivity({
        kind: "dump",
        label: "Kept from FIND",
        jobKey: job.job_key,
        company: robotJobCardFromMatch(job).employer || undefined,
        robotUrl,
      });
    }
    if (!accessToken) {
      setJustSavedCount(pool.length);
      if (openOffer) {
        setShowNextSteps(true);
        queueMicrotask(() => openJobsCrmNextStepsForm());
      }
      return;
    }
    try {
      const result = await keepJobsOnAccount(accessToken, {
        jobs: pool,
        robotName: product,
        robotUrl,
        submissionId,
      });
      setAccountRows(result.jobs);
      setJustSavedCount(
        crmDeskForCurrentRobot({ snap, accountRows: result.jobs }).savedCount,
      );
      if (openOffer) {
        setShowNextSteps(true);
        queueMicrotask(() => openJobsCrmNextStepsForm());
      }
    } catch {
      setJustSavedCount(pool.length);
      if (openOffer) {
        setShowNextSteps(true);
        queueMicrotask(() => openJobsCrmNextStepsForm());
      }
    }
  }

  const didPersistRef = useRef(false);
  useEffect(() => {
    if (!accessToken || jobs.length === 0 || didPersistRef.current) return;
    didPersistRef.current = true;
    void persistKeptJobs(selected, { openOffer: false });
  }, [accessToken, jobs.length]);

  function openOfferForm(event?: { preventDefault: () => void }) {
    event?.preventDefault();
    setShowNextSteps(true);
    if (typeof window !== "undefined") {
      const href = jobsCrmOfferHref(true, submissionId);
      window.history.replaceState(null, "", href);
    }
    queueMicrotask(() => openJobsCrmNextStepsForm());
  }
  const leaveHref = jobsCrmLeaveHref({ submissionId, jobCount });
  const leaveLabel = jobsCrmLeaveLabel({ submissionId, jobCount });
  const wallHref = jobsCrmNextHref(false, submissionId, jobCount);
  const process = (
    <JobsProcessChrome
      signedIn={signedIn}
      submissionId={submissionId}
      jobCount={jobCount}
    />
  );

  if (!signedIn) {
    return (
      <div className="mx-auto w-full max-w-5xl px-4 pb-12 pt-4">
        <div className="mb-6">{process}</div>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
          CRM
        </h1>
        <p className="mt-3 max-w-3xl text-lg leading-relaxed text-slate-200 sm:text-xl">
          {authReady ? CRM_WALL_LEAD : "Opening CRM…"}
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <a
            href={wallHref}
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          >
            {CRM_SIGNUP_NEXT_CTA}
          </a>
          <a
            href={leaveHref}
            onClick={
              leaveHref.startsWith("/?new=") ? onJobsFreshHomeClick : undefined
            }
            className="inline-flex items-center justify-center border border-slate-500 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-slate-200 transition hover:border-slate-300 hover:text-white"
          >
            {leaveLabel}
          </a>
        </div>
        <div className="mt-10">{process}</div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-12 pt-4">
      <div className="mb-6">{process}</div>

      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
        CRM
      </h1>
      <p className="mt-3 max-w-3xl text-lg leading-relaxed text-slate-200 sm:text-xl">
        {jobs.length === 0 ? crmEmptyDeskHint(product) : crmSaveJobsBlurb(product)}
      </p>
      {jobs.length > 0 ? (
        <p className="mt-3 font-mono text-sm uppercase tracking-[0.08em] text-emerald-300">
          {crmCollectedCountLabel(selected.length, jobCount || CRM_UNLOCKED_JOBS)}
          {" · "}
          Applied {stats.applied} of {stats.total}
          {" · "}
          Quoted {stats.quoted} of {stats.total}
          {stats.quotes[0] ? ` · Live quote ${stats.quotes[0]}` : ""}
        </p>
      ) : null}
      <div className="mt-4">
        <JobsKeepStatusBar
          savedCount={savedCount}
          onCrmDesk
          signedIn={signedIn}
          submissionId={submissionId}
          onApplyClick={openOfferForm}
        />
      </div>

      {jobs.length === 0 ? (
        <p className="mt-6 border border-slate-600 bg-[#081126] px-4 py-4 text-sm text-slate-300">
          <a
            href={leaveHref}
            onClick={
              leaveHref.startsWith("/?new=") ? onJobsFreshHomeClick : undefined
            }
            className="font-bold text-emerald-300 underline decoration-emerald-400/50 underline-offset-2 hover:text-emerald-200"
          >
            {leaveLabel}
          </a>
        </p>
      ) : (
        <div className="mt-6">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <p className={`${eyebrow} text-emerald-400`}>{CRM_LISTING_EYEBROW}</p>
            <div className="flex flex-wrap items-center gap-2">
              <a
                href={jobsCrmOfferHref(signedIn, submissionId)}
                onClick={openOfferForm}
                aria-label={JOBS_APPLY_SELECTED_CTA}
                className={`${JOBS_APPLY_CTA_CLASS} px-3 py-2 font-mono text-xs`}
              >
                {JOBS_APPLY_SELECTED_CTA}
              </a>
              <p className="basis-full text-sm leading-relaxed text-slate-400">
                {JOBS_APPLY_SEQUENCE}
              </p>
            </div>
          </div>
          {showNextSteps && offerJob && accessToken ? (
            <JobsCrmNextSteps
              job={offerJob}
              jobs={jobs.filter(j => selected.includes(j.job_key))}
              robotName={product}
              robotUrl={robotUrl}
              token={accessToken}
              onApplied={app => {
                setApplications(prev => ({ ...prev, [app.job_key]: app }));
                setExpandedKey(app.job_key);
              }}
            />
          ) : showNextSteps && offerJob ? (
            <p className="mb-4 border border-emerald-400/40 bg-[#0b162f] px-4 py-4 text-sm text-slate-200">
              Sign in to store this offer on your account, then apply.
            </p>
          ) : null}
          <ul className="space-y-3" aria-label={CRM_LISTING_EYEBROW}>
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
                        aria-label={`${JOBS_KEEP_LABEL} ${card.jobTitle}`}
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
                        <span className="mt-1 block font-mono text-sm text-slate-500">
                          {workTaskModelListLine(
                            parseWorkTaskModel(rowByKey.get(job.job_key)),
                          )}
                        </span>
                      </span>
                      <span className="font-mono text-xs text-slate-500">
                        {open ? "−" : "+"}
                      </span>
                    </button>
                  </div>
                  {open ? (
                    <div className="border-t border-slate-700 px-4 pb-5 pt-4">
                      <CollectedJobInspect job={job} />
                      <WorkTaskModelQuestion
                        jobKey={job.job_key}
                        row={rowByKey.get(job.job_key)}
                        token={accessToken}
                        onSaved={mergeKeptRow}
                      />
                      <ApplyPanel
                        key={job.job_key}
                        job={job}
                        robotName={product}
                        robotUrl={robotUrl}
                        signedIn={signedIn}
                        accessToken={accessToken}
                        onSaved={() => setTick(n => n + 1)}
                      />
                      {applications[job.job_key] && accessToken ? (
                        <JobsCrmInbox
                          applicationId={applications[job.job_key].id}
                          token={accessToken}
                          initial={applications[job.job_key]}
                        />
                      ) : null}
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <nav
        aria-label="CRM next"
        className="mt-8 border border-emerald-400/40 bg-[#0b162f] px-4 py-5 sm:px-6"
      >
        <p className="mt-2 max-w-3xl text-base leading-relaxed text-slate-200">
          {CRM_LEAVE_HINT}
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <a
            href={leaveHref}
            onClick={
              leaveHref.startsWith("/?new=") ? onJobsFreshHomeClick : undefined
            }
            className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          >
            {leaveLabel}
          </a>
        </div>
      </nav>

      {submissionId ? (
        <p className="mt-6 font-mono text-xs text-slate-600">Submission {submissionId}</p>
      ) : null}
      <div className="mt-10">{process}</div>
    </div>
  );
}

function WorkTaskModelQuestion({
  jobKey,
  row,
  token,
  onSaved,
}: {
  jobKey: string;
  row?: KeptJobRow;
  token?: string | null;
  onSaved: (row: KeptJobRow) => void;
}) {
  const saved = parseWorkTaskModel(row);
  const [choice, setChoice] = useState<WorkTaskModelKind>(saved.kind);
  const [sourceDraft, setSourceDraft] = useState(
    saved.kind === "source" ? saved.source : "",
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const next = parseWorkTaskModel(row);
    setChoice(next.kind);
    setSourceDraft(next.kind === "source" ? next.source : "");
    setError("");
  }, [jobKey, row?.work_task_model_kind, row?.work_task_model_source]);

  async function persist(next: WorkTaskModelAnswer) {
    if (!token) {
      setError("Sign in to save this on the desk.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const savedRow = await saveWorkTaskModelOnAccount(token, {
        jobKey,
        kind: next.kind,
        source: next.kind === "source" ? next.source : "",
      });
      onSaved(savedRow);
      setChoice(parseWorkTaskModel(savedRow).kind);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : WORK_TASK_MODEL_SOURCE_REQUIRED;
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  function pickSelfTrain() {
    setChoice("self_train");
    setSourceDraft("");
    void persist({ kind: "self_train" });
  }

  function pickSource() {
    setChoice("source");
    setError("");
  }

  function commitSource() {
    const named = sourceDraft.replace(/\s+/g, " ").trim();
    if (!named) {
      setError(WORK_TASK_MODEL_SOURCE_REQUIRED);
      return;
    }
    void persist({ kind: "source", source: named });
  }

  const group = `work-task-model-${jobKey}`;

  return (
    <section
      className="mt-6 border border-emerald-400/40 bg-[#0b162f] px-4 py-5 sm:px-6"
      aria-label={WORK_TASK_MODEL_QUESTION}
    >
      <p className={`${eyebrow} text-slate-400`}>For this job</p>
      <h3 className="mt-2 font-display text-2xl font-bold text-white">
        {WORK_TASK_MODEL_QUESTION}
      </h3>
      {choice === "unknown" ? (
        <p className="mt-2 text-sm leading-relaxed text-slate-400">
          {WORK_TASK_MODEL_UNKNOWN_HINT}
        </p>
      ) : null}
      <div className="mt-4 space-y-3">
        <label className="flex cursor-pointer items-start gap-3 text-sm text-slate-200">
          <input
            type="radio"
            name={group}
            checked={choice === "source"}
            onChange={pickSource}
            disabled={busy}
            className="mt-1 h-4 w-4 accent-emerald-400"
          />
          <span>
            <span className="block font-semibold">{WORK_TASK_MODEL_SOURCE_OPTION}</span>
            <span className="mt-1 block text-slate-400">{WORK_TASK_MODEL_SOURCE_HINT}</span>
          </span>
        </label>
        {choice === "source" ? (
          <input
            type="text"
            value={sourceDraft}
            onChange={e => {
              setSourceDraft(e.target.value);
              setError("");
            }}
            onBlur={commitSource}
            disabled={busy}
            placeholder={WORK_TASK_MODEL_SOURCE_PLACEHOLDER}
            aria-label={WORK_TASK_MODEL_SOURCE_OPTION}
            className="w-full border border-emerald-400/50 bg-[#081126] px-3 py-3 text-base text-slate-100"
          />
        ) : null}
        <label className="flex cursor-pointer items-start gap-3 text-sm text-slate-200">
          <input
            type="radio"
            name={group}
            checked={choice === "self_train"}
            onChange={pickSelfTrain}
            disabled={busy}
            className="mt-1 h-4 w-4 accent-emerald-400"
          />
          <span className="font-semibold">{WORK_TASK_MODEL_SELF_OPTION}</span>
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-sm text-rose-300">{error}</p>
      ) : null}
    </section>
  );
}

function CollectedJobInspect({ job }: { job: MatchJob }) {
  const card = robotJobCardFromMatch(job);
  return (
    <div>
      <p className={`${eyebrow} text-slate-400`}>This job</p>
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
        {card.description ? (
          <div>
            <dt className={eyebrow}>Job description</dt>
            <dd className="mt-0.5 text-slate-300">{card.description}</dd>
          </div>
        ) : null}
        <div>
          <dt className={eyebrow}>{card.payEstimate.heading}</dt>
          <dd className="mt-0.5">
            <span className="text-emerald-300">{card.payEstimate.monthlyLabel}</span>
            {" · "}
            <span className="text-emerald-300">{card.payEstimate.annualLabel}</span>
            <span className="mt-0.5 block text-slate-400">
              {card.payEstimate.disclaimer}
            </span>
          </dd>
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
  robotUrl,
  signedIn: _signedIn,
  accessToken = null,
  onSaved,
}: {
  job: MatchJob;
  robotName: string;
  robotUrl?: string;
  signedIn: boolean;
  accessToken?: string | null;
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
    const company = robotJobCardFromMatch(job).employer || undefined;
    recordPipelineActivity({
      kind,
      label,
      jobKey: job.job_key,
      company,
      robotUrl,
    });
    if (accessToken) {
      void postJobsCrmActivity(accessToken, {
        kind,
        label,
        jobKey: job.job_key,
        company,
      });
    }
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
      <p className={`${eyebrow} text-slate-400`}>Place this job</p>
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
          <div className="space-y-2">
            <p className="max-w-xl text-sm leading-relaxed text-slate-300">
              {JOBS_APPLY_SEQUENCE}
            </p>
            <button
              type="button"
              onClick={apply}
              disabled={!ready}
              className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {JOBS_APPLY_CTA}
            </button>
          </div>
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

      <PipelineActivity
        jobKey={job.job_key}
        robotUrl={robotUrl}
        tick={record.status}
      />
    </section>
  );
}

function PipelineActivity({
  jobKey,
  robotUrl,
  tick,
}: {
  jobKey: string;
  robotUrl?: string;
  tick: string;
}) {
  void tick;
  const events = pipelineActivityForJob(jobKey, robotUrl).slice(0, 8);
  if (events.length === 0) return null;
  return (
    <div className="mt-8 border-t border-slate-700 pt-5">
      <p className={`${eyebrow} text-slate-400`}>What we did</p>
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
  authReady?: boolean;
  submissionId?: number | null;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-[#081126] pt-14">
      <ExperimentHeader />
      <JobsCrmDesk {...props} />
    </div>
  );
}
