/**
 * Cal on the Jobs CRM desk after Open CRM.
 * Asks missing apply facts. Prepares the draft. You send.
 * Not FIND. Not a buyer chatbot.
 */
import { useEffect, useMemo, useState } from "react";
import {
  JOBS_CONTACTS_EMPTY_NOTE,
  JOBS_PREPARE_CTA,
  JOBS_PROPOSED_PRICE_HINT,
  JOBS_PROPOSED_PRICE_LABEL,
  JOBS_SEND_DRAFT_HINT,
  WORK_TASK_MODEL_QUESTION,
  WORK_TASK_MODEL_SELF_OPTION,
  WORK_TASK_MODEL_SOURCE_HINT,
  WORK_TASK_MODEL_SOURCE_OPTION,
  WORK_TASK_MODEL_SOURCE_PLACEHOLDER,
  WORK_TASK_MODEL_SOURCE_REQUIRED,
  fetchCalDesk,
  runCalDeskTool,
  type CalDeskBrief,
  type CalDeskJob,
  type JobsCrmApplication,
  type KeptJobRow,
} from "@/lib/jobsCrmAccount";
import {
  OEM_CAL_DESK_EYEBROW,
  OEM_CAL_DESK_LEAD,
  OEM_CAL_OPERATOR_SENDS,
} from "@/lib/oemCalCopy";
import { JOBS_POC_PREFER_HINT, JOBS_POC_SKIP_CTA } from "@/lib/jobsApply";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";

type ThreadLine = { who: "cal" | "you"; text: string };

type PendingFacts = {
  selectedModels: string[];
  monthlyPrice: string;
  pocEvidence: string;
  pocSkipped: boolean;
};

const EMPTY_FACTS: PendingFacts = {
  selectedModels: [],
  monthlyPrice: "",
  pocEvidence: "",
  pocSkipped: false,
};

function nextFact(
  job: CalDeskJob | null,
  pending: PendingFacts
): string | null {
  if (!job) return null;
  const status = (job.application_status || "").toLowerCase();
  if (
    status === "prepared" ||
    status === "sent" ||
    status === "not_sent_no_email"
  ) {
    return null;
  }
  if (job.missing.includes("task_model")) return "task_model";
  const models = pending.selectedModels.length
    ? pending.selectedModels
    : job.selected_models;
  if (job.missing.includes("selected_models") && !models.length) {
    return "selected_models";
  }
  const price = pending.monthlyPrice || job.monthly_price || "";
  if (job.missing.includes("monthly_price") && !price.trim()) {
    return "monthly_price";
  }
  const pocDone =
    pending.pocSkipped ||
    pending.pocEvidence.trim().length > 0 ||
    Boolean(job.poc?.skipped) ||
    Boolean(job.poc?.evidence) ||
    Boolean(job.poc?.video);
  if (job.missing.includes("poc") && !pocDone) return "poc";
  return "prepare_apply";
}

function promptFor(
  fact: string | null,
  job: CalDeskJob | null,
  greeting: string
): string {
  if (!fact) return greeting;
  const shop = job?.employer_name || "this employer";
  if (fact === "task_model")
    return `${WORK_TASK_MODEL_QUESTION} This one is ${shop}.`;
  if (fact === "selected_models") {
    return "Which catalogued SKU goes on this apply? I will not invent one.";
  }
  if (fact === "monthly_price") {
    return `What monthly price will you charge this employer? Employer: ${shop}.`;
  }
  if (fact === "poc") {
    return "Any proof of concept? Employers prefer it. Skip is fine.";
  }
  return "I have enough to prepare the draft. Review it. You send.";
}

export default function CalJobsDesk({
  token,
  onKeptRow,
  onPrepared,
}: {
  token: string;
  onKeptRow: (row: KeptJobRow) => void;
  onPrepared: (app: JobsCrmApplication) => void;
}) {
  const [desk, setDesk] = useState<CalDeskBrief | null>(null);
  const [pendingByJob, setPendingByJob] = useState<
    Record<string, PendingFacts>
  >({});
  const [thread, setThread] = useState<ThreadLine[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sourceDraft, setSourceDraft] = useState("");
  const [priceDraft, setPriceDraft] = useState("");
  const [pocDraft, setPocDraft] = useState("");

  const focus = useMemo(() => {
    const jobs = desk?.jobs || [];
    return (
      jobs.find(job =>
        nextFact(job, pendingByJob[job.job_key] || EMPTY_FACTS)
      ) ||
      jobs[0] ||
      null
    );
  }, [desk, pendingByJob]);

  const pending = focus
    ? pendingByJob[focus.job_key] || EMPTY_FACTS
    : EMPTY_FACTS;
  const fact = nextFact(focus, pending);

  useEffect(() => {
    let cancelled = false;
    fetchCalDesk(token)
      .then(brief => {
        if (cancelled) return;
        setDesk(brief);
        const first =
          brief.jobs.find(job => nextFact(job, EMPTY_FACTS)) ||
          brief.jobs[0] ||
          null;
        const opening = promptFor(
          nextFact(first, EMPTY_FACTS),
          first,
          brief.greeting
        );
        setThread([{ who: "cal", text: opening }]);
      })
      .catch(() => {
        if (!cancelled) setError("Sign in to work this desk with Cal.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  function remember(jobKey: string, patch: Partial<PendingFacts>) {
    setPendingByJob(prev => ({
      ...prev,
      [jobKey]: { ...(prev[jobKey] || EMPTY_FACTS), ...patch },
    }));
  }

  function say(who: "cal" | "you", text: string) {
    setThread(prev => [...prev, { who, text }]);
  }

  function afterLocal(
    job: CalDeskJob,
    nextPending: PendingFacts,
    youSaid: string
  ) {
    say("you", youSaid);
    const nxt = nextFact(job, nextPending);
    say("cal", promptFor(nxt, job, desk?.greeting || OEM_CAL_DESK_LEAD));
  }

  async function saveTaskModel(kind: "source" | "self_train", source = "") {
    if (!focus) return;
    if (kind === "source" && !source.trim()) {
      setError(WORK_TASK_MODEL_SOURCE_REQUIRED);
      return;
    }
    setBusy(true);
    setError("");
    say(
      "you",
      kind === "source"
        ? `Model source: ${source.trim()}`
        : WORK_TASK_MODEL_SELF_OPTION
    );
    try {
      const turn = await runCalDeskTool(token, {
        tool: "save_task_model",
        jobKey: focus.job_key,
        kind,
        source: kind === "source" ? source.trim() : "",
      });
      setDesk(turn.desk);
      if (turn.result && "job_key" in turn.result) {
        onKeptRow(turn.result as KeptJobRow);
      }
      const job =
        turn.desk.jobs.find(row => row.job_key === focus.job_key) || focus;
      const nxt = nextFact(job, pending);
      say("cal", promptFor(nxt, job, turn.desk.greeting));
      setSourceDraft("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save that.");
    } finally {
      setBusy(false);
    }
  }

  async function prepareDraft() {
    if (!focus) return;
    const models = pending.selectedModels.length
      ? pending.selectedModels
      : focus.selected_models.length
        ? focus.selected_models
        : focus.catalog_skus.length
          ? []
          : focus.robot_name
            ? [focus.robot_name]
            : [];
    const price = pending.monthlyPrice || focus.monthly_price || "";
    if (!models.length) {
      setError("Pick a catalogued SKU. I will not invent one.");
      return;
    }
    if (!price.trim()) {
      setError(
        "Enter the monthly price you will charge. I will not invent it."
      );
      return;
    }
    setBusy(true);
    setError("");
    say("you", JOBS_PREPARE_CTA);
    try {
      const turn = await runCalDeskTool(token, {
        tool: "prepare_apply",
        jobKey: focus.job_key,
        robotName: focus.robot_name || undefined,
        selectedModels: models,
        monthlyPrice: price,
        pocEvidence: pending.pocEvidence || focus.poc?.evidence || "",
        pocVideoUrl: focus.poc?.video || "",
        pocSkipped: pending.pocSkipped || Boolean(focus.poc?.skipped),
      });
      if (turn.refused && turn.detail) {
        setError(turn.detail);
      }
      setDesk(turn.desk);
      const app = turn.result as JobsCrmApplication | undefined;
      if (app?.id) onPrepared(app);
      const job =
        turn.desk.jobs.find(row => row.job_key === focus.job_key) || focus;
      say("cal", promptFor(nextFact(job, pending), job, turn.desk.greeting));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not prepare that.");
    } finally {
      setBusy(false);
    }
  }

  const catalog = focus?.catalog_skus || [];
  const draft = focus?.application?.draft;

  return (
    <section
      className="mt-6 border border-emerald-400/40 bg-[#0b162f] px-4 py-5 sm:px-6"
      data-cal-jobs-desk="1"
      aria-label={OEM_CAL_DESK_EYEBROW}
    >
      <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>
        {OEM_CAL_DESK_EYEBROW}
      </p>
      <h2 className="mt-2 font-display text-2xl font-bold text-white">Cal</h2>
      <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-300">
        {OEM_CAL_DESK_LEAD}
      </p>

      {desk?.jobs.length ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-200">
          {desk.jobs.map(job => (
            <li key={job.job_key}>
              <span className="text-emerald-400">
                {job.employer_name || "Unnamed employer"}
              </span>
              {" · "}
              {job.work_title || "this job"}
              {" · "}
              <span className="text-slate-400">
                {jobStatusLine(job, pendingByJob[job.job_key])}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-slate-400">{desk?.greeting}</p>
      )}

      <ol className="mt-4 space-y-2" aria-live="polite">
        {thread.slice(-8).map((line, i) => (
          <li
            key={`${line.who}-${i}-${line.text.slice(0, 20)}`}
            className={
              line.who === "cal"
                ? "text-sm leading-relaxed text-slate-100"
                : "text-sm leading-relaxed text-emerald-200"
            }
          >
            <span className={`${JOBS_EYEBROW_CLASS} text-slate-500`}>
              {line.who === "cal" ? "Cal" : "You"}
            </span>
            <span className="mt-0.5 block">{line.text}</span>
          </li>
        ))}
      </ol>

      {focus?.contacts_note ? (
        <p className="mt-3 text-sm text-slate-400">
          {JOBS_CONTACTS_EMPTY_NOTE}
        </p>
      ) : null}

      {fact === "task_model" && focus ? (
        <div className="mt-4 space-y-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => setSourceDraft(sourceDraft ? sourceDraft : " ")}
            className="block w-full border border-emerald-400/50 bg-[#081126] px-3 py-3 text-left text-sm text-slate-100"
          >
            {WORK_TASK_MODEL_SOURCE_OPTION}
            <span className="mt-1 block text-slate-400">
              {WORK_TASK_MODEL_SOURCE_HINT}
            </span>
          </button>
          {sourceDraft !== "" ? (
            <form
              onSubmit={e => {
                e.preventDefault();
                void saveTaskModel("source", sourceDraft);
              }}
            >
              <input
                type="text"
                value={sourceDraft === " " ? "" : sourceDraft}
                onChange={e => setSourceDraft(e.target.value)}
                placeholder={WORK_TASK_MODEL_SOURCE_PLACEHOLDER}
                aria-label={WORK_TASK_MODEL_SOURCE_OPTION}
                className="w-full border border-emerald-400/50 bg-[#081126] px-3 py-3 text-base text-slate-100"
              />
              <button
                type="submit"
                disabled={busy}
                className="mt-2 bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a]"
              >
                Save model source
              </button>
            </form>
          ) : null}
          <button
            type="button"
            disabled={busy}
            onClick={() => void saveTaskModel("self_train")}
            className="block w-full border border-slate-500 px-3 py-3 text-left text-sm font-semibold text-slate-100"
          >
            {WORK_TASK_MODEL_SELF_OPTION}
          </button>
        </div>
      ) : null}

      {fact === "selected_models" && focus ? (
        <div className="mt-4 space-y-2">
          {catalog.length ? (
            catalog.map(sku => (
              <button
                key={sku.name}
                type="button"
                disabled={busy}
                onClick={() => {
                  const next = { ...pending, selectedModels: [sku.name] };
                  remember(focus.job_key, { selectedModels: [sku.name] });
                  afterLocal(focus, next, sku.name);
                }}
                className="block w-full border border-slate-500 px-3 py-3 text-left text-sm text-slate-200"
              >
                {sku.name}
              </button>
            ))
          ) : (
            <p className="text-sm text-slate-300">
              No catalogued SKU on file. I'll use{" "}
              {focus.robot_name || "this robot"}. I will not invent a name.
            </p>
          )}
          {!catalog.length ? (
            <button
              type="button"
              disabled={busy || !focus.robot_name}
              onClick={() => {
                const name = focus.robot_name || "";
                const next = { ...pending, selectedModels: [name] };
                remember(focus.job_key, { selectedModels: [name] });
                afterLocal(focus, next, `SKU: ${name}`);
              }}
              className="bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a]"
            >
              Use {focus.robot_name || "this robot"}
            </button>
          ) : null}
        </div>
      ) : null}

      {fact === "monthly_price" && focus ? (
        <form
          className="mt-4"
          onSubmit={e => {
            e.preventDefault();
            const price = priceDraft.replace(/\s+/g, " ").trim();
            if (!price) {
              setError(
                "Enter the monthly price you will charge. I will not invent it."
              );
              return;
            }
            const next = { ...pending, monthlyPrice: price };
            remember(focus.job_key, { monthlyPrice: price });
            afterLocal(focus, next, `Monthly price: ${price}`);
            setPriceDraft("");
          }}
        >
          <label className="block text-sm font-semibold text-white">
            {JOBS_PROPOSED_PRICE_LABEL}
            <span className="mt-1 block font-normal text-slate-400">
              {JOBS_PROPOSED_PRICE_HINT}
            </span>
          </label>
          <input
            type="text"
            value={priceDraft}
            onChange={e => setPriceDraft(e.target.value)}
            className="mt-2 w-full border border-emerald-400/50 bg-[#081126] px-3 py-3 text-base text-slate-100"
          />
          <button
            type="submit"
            disabled={busy}
            className="mt-2 bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a]"
          >
            Save price
          </button>
        </form>
      ) : null}

      {fact === "poc" && focus ? (
        <div className="mt-4 space-y-3">
          <p className="text-sm text-slate-300">{JOBS_POC_PREFER_HINT}</p>
          <textarea
            value={pocDraft}
            onChange={e => setPocDraft(e.target.value)}
            rows={3}
            className="w-full border border-emerald-400/50 bg-[#081126] px-3 py-3 text-sm text-slate-100"
            aria-label="Proof of concept"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy || !pocDraft.trim()}
              onClick={() => {
                const next = { ...pending, pocEvidence: pocDraft.trim() };
                remember(focus.job_key, { pocEvidence: pocDraft.trim() });
                afterLocal(focus, next, "PoC noted");
                setPocDraft("");
              }}
              className="bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a]"
            >
              Save PoC
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                const next = { ...pending, pocSkipped: true };
                remember(focus.job_key, { pocSkipped: true });
                afterLocal(focus, next, JOBS_POC_SKIP_CTA);
              }}
              className="border border-slate-500 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-slate-200"
            >
              {JOBS_POC_SKIP_CTA}
            </button>
          </div>
        </div>
      ) : null}

      {fact === "prepare_apply" && focus ? (
        <div className="mt-4">
          <p className="text-sm text-slate-300">{OEM_CAL_OPERATOR_SENDS}</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void prepareDraft()}
            className="mt-2 bg-violet-500 px-4 py-3 text-sm font-bold uppercase tracking-[0.06em] text-white"
          >
            {JOBS_PREPARE_CTA}
          </button>
        </div>
      ) : null}

      {draft ? (
        <div
          className="mt-4 border border-violet-500/40 bg-[#12082a] px-4 py-4"
          data-apply-draft="1"
        >
          <p className={`${JOBS_EYEBROW_CLASS} text-violet-300`}>Apply draft</p>
          <p className="mt-2 text-sm font-semibold text-white">
            {draft.subject}
          </p>
          <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-200">
            {draft.body}
          </pre>
          <p className="mt-3 text-sm text-slate-400">{JOBS_SEND_DRAFT_HINT}</p>
        </div>
      ) : null}

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}

function jobStatusLine(job: CalDeskJob, pending?: PendingFacts): string {
  const fact = nextFact(job, pending || EMPTY_FACTS);
  if (!fact) return "Draft ready. You send.";
  if (fact === "task_model") return "Model not named yet";
  if (fact === "selected_models") return "Needs a catalogued SKU";
  if (fact === "monthly_price") return "Needs a monthly price";
  if (fact === "poc") return "PoC still open";
  if (fact === "prepare_apply") return "Ready to prepare";
  return fact;
}
