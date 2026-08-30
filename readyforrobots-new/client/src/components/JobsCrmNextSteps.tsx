import { useEffect, useState } from "react";
import {
  JOBS_APPLY_OFFER_CTA,
  JOBS_APPLY_SEQUENCE,
  JOBS_CONTACTS_EMPTY_NOTE,
  JOBS_DOCS_HEADING,
  JOBS_DOCS_HINT,
  JOBS_MODEL_SELECT_HINT,
  JOBS_MODEL_SELECT_LABEL,
  JOBS_PROPOSED_PRICE_HINT,
  JOBS_PROPOSED_PRICE_LABEL,
  JOBS_SEND_DRAFT_CTA,
  JOBS_SEND_DRAFT_HINT,
  JOBS_VIDEO_EMPTY_NOTE,
  applyJobOnAccount,
  applySelectedJobsOnAccount,
  canSubmitNextStepsOffer,
  companyHintFromRobotUrl,
  fetchApplyPrep,
  fetchCatalogSkus,
  fetchRobotDocuments,
  sendPreparedApplication,
  uploadRobotDocument,
  type CatalogSku,
  type JobsCrmApplication,
  type RobotDocument,
} from "@/lib/jobsCrmAccount";
import { JOBS_APPLY_CTA_BUTTON_CLASS } from "@/lib/jobsWorkflow";
import { JOBS_POC_PREFER_HINT, JOBS_POC_SKIP_CTA } from "@/lib/jobsApply";
import {
  JOBS_POC_VIDEO_HINT,
  JOBS_POC_VIDEO_LABEL,
  JOBS_POC_VIDEO_SCRIPT_HEADING,
  pocVideoScriptBeats,
  pocVideoUrlIssue,
} from "@/lib/pocVideoUrl";
import { JOBS_EYEBROW_CLASS, crmOfferBlurb } from "@/lib/jobsWorkflow";
import type { MatchJob } from "@/lib/robotJobMatch";
import { robotJobCardFromMatch } from "@/lib/robotJobCard";

export default function JobsCrmNextSteps({
  job,
  jobs,
  robotName,
  robotUrl,
  token,
  onApplied,
}: {
  job: MatchJob;
  jobs?: MatchJob[];
  robotName: string;
  robotUrl?: string;
  token: string;
  onApplied: (app: JobsCrmApplication) => void;
}) {
  const selectedJobs = (jobs && jobs.length ? jobs : [job]).filter(
    j => j?.job_key
  );
  const oemCompany = companyHintFromRobotUrl(robotUrl) || robotName;
  const card = robotJobCardFromMatch(job);
  const [skus, setSkus] = useState<CatalogSku[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [monthlyPrice, setMonthlyPrice] = useState("");
  const [pocEvidence, setPocEvidence] = useState("");
  const [pocVideoUrl, setPocVideoUrl] = useState("");
  const [pocSkipped, setPocSkipped] = useState(false);
  const [why, setWhy] = useState("");
  const [videoNote, setVideoNote] = useState("");
  const [videoSearchUrl, setVideoSearchUrl] = useState("");
  const [drafts, setDrafts] = useState<JobsCrmApplication[]>([]);
  const [docs, setDocs] = useState<RobotDocument[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoIssue = pocVideoUrlIssue(pocVideoUrl);
  const scriptBeats = pocVideoScriptBeats({
    robotName,
    selectedModels: models,
    employer: card.employer,
    jobTitle: card.jobTitle,
    work: card.work,
    requirements: card.requirements,
  });
  const ready =
    canSubmitNextStepsOffer({
      monthlyPrice,
      selectedModels: models,
    }) && !videoIssue;

  useEffect(() => {
    let cancelled = false;
    fetchCatalogSkus(token, {
      url: robotUrl,
      company: robotName,
    })
      .then(rows => {
        if (!cancelled) setSkus(rows);
      })
      .catch(() => {
        if (!cancelled) setSkus([]);
      });
    fetchRobotDocuments(token)
      .then(rows => {
        if (!cancelled) setDocs(rows);
      })
      .catch(() => {
        if (!cancelled) setDocs([]);
      });
    fetchApplyPrep(token, {
      robot: robotName,
      company: oemCompany,
      sku: robotName,
    })
      .then(prep => {
        if (cancelled) return;
        setVideoNote(prep.video_note || "");
        setVideoSearchUrl(prep.video_search_url || "");
      })
      .catch(() => {
        if (!cancelled) setVideoNote(JOBS_VIDEO_EMPTY_NOTE);
      });
    return () => {
      cancelled = true;
    };
  }, [token, robotUrl, robotName, oemCompany]);

  useEffect(() => {
    const sku = models[0];
    if (!sku) return;
    let cancelled = false;
    fetchApplyPrep(token, {
      robot: robotName,
      company: oemCompany,
      sku,
    })
      .then(prep => {
        if (cancelled) return;
        setVideoNote(prep.video_note || "");
        setVideoSearchUrl(prep.video_search_url || "");
        if (prep.video_url) {
          setPocVideoUrl(prep.video_url);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [token, robotName, oemCompany, models]);

  function toggleModel(name: string, on: boolean) {
    setModels(prev => {
      const set = new Set(prev);
      if (on) set.add(name);
      else set.delete(name);
      return [...set];
    });
  }

  async function apply() {
    if (!ready || busy) return;
    setBusy(true);
    setError(null);
    try {
      const skipped =
        pocSkipped || (!pocEvidence.trim() && !pocVideoUrl.trim());
      if (selectedJobs.length > 1) {
        const result = await applySelectedJobsOnAccount(token, {
          jobs: selectedJobs,
          robotName,
          selectedModels: models,
          monthlyPrice,
          pocEvidence,
          pocVideoUrl,
          pocSkipped: skipped,
          why,
          companyName: oemCompany,
          documentIds: selectedDocs,
        });
        for (const app of result.applied) onApplied(app);
        setDrafts(result.applied);
        if (!result.applied.length && result.errors[0]) {
          setError(result.errors[0].error);
        }
      } else {
        const app = await applyJobOnAccount(token, {
          jobKey: job.job_key,
          robotName,
          selectedModels: models,
          monthlyPrice,
          pocEvidence,
          pocVideoUrl,
          pocSkipped: skipped,
          why,
          companyName: oemCompany,
          job,
          documentIds: selectedDocs,
        });
        onApplied(app);
        setDrafts([app]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not apply.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      id="jobs-next-steps"
      aria-label="Next steps"
      className="mt-6 border border-emerald-400/40 bg-[#0b162f] px-4 py-6 sm:px-6"
    >
      <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>Next steps</p>
      <h2 className="mt-2 font-display text-2xl font-bold text-white sm:text-3xl">
        Offer for{" "}
        {selectedJobs.length > 1
          ? `${selectedJobs.length} selected jobs`
          : card.jobTitle}
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-300">
        {crmOfferBlurb(robotName)}
      </p>

      <label className="mt-6 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          Robot name
        </span>
        <input
          type="text"
          readOnly
          value={robotName}
          aria-label="Robot name"
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-slate-100"
        />
      </label>

      <fieldset className="mt-6">
        <legend className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          {JOBS_MODEL_SELECT_LABEL}
        </legend>
        <p className="mt-1 text-sm text-slate-400">{JOBS_MODEL_SELECT_HINT}</p>
        {skus.length === 0 ? (
          <p className="mt-3 text-sm text-amber-200/90">
            No catalogued SKUs for this OEM. We will not invent a model. Apply
            stays gated until a listed SKU is available.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {skus.map(sku => (
              <li key={sku.slug || sku.name}>
                <label className="flex items-center gap-2 text-sm text-slate-200">
                  <input
                    type="checkbox"
                    checked={models.includes(sku.name)}
                    onChange={e => toggleModel(sku.name, e.target.checked)}
                    className="h-4 w-4 accent-emerald-400"
                  />
                  {sku.name}
                </label>
              </li>
            ))}
          </ul>
        )}
      </fieldset>

      <div className="mt-6" data-poc-video-script="1">
        <p className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          {JOBS_POC_VIDEO_SCRIPT_HEADING}
        </p>
        <ol className="mt-3 space-y-3">
          {scriptBeats.map(beat => (
            <li key={beat.n} className="text-sm leading-relaxed text-slate-300">
              <span className="font-mono text-xs uppercase tracking-[0.08em] text-emerald-300">
                {String(beat.n).padStart(2, "0")} · {beat.title}
              </span>
              <span className="mt-1 block">{beat.body}</span>
            </li>
          ))}
        </ol>
      </div>

      <label className="mt-6 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          PoC proof if available
        </span>
        <span className="mt-1 block text-sm text-slate-400">
          {JOBS_POC_PREFER_HINT}
        </span>
        <textarea
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
          rows={3}
          value={pocEvidence}
          onChange={e => {
            setPocEvidence(e.target.value);
            setPocSkipped(false);
          }}
          placeholder="Written proof of concept — optional. Do not paste a video URL here."
        />
      </label>
      <label className="mt-4 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          {JOBS_POC_VIDEO_LABEL}
        </span>
        <span className="mt-1 block text-sm text-slate-400">
          {JOBS_POC_VIDEO_HINT}
        </span>
        <input
          type="url"
          aria-label={JOBS_POC_VIDEO_LABEL}
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
          value={pocVideoUrl}
          onChange={e => {
            setPocVideoUrl(e.target.value);
            setPocSkipped(false);
          }}
          placeholder="https://www.loom.com/share/… or YouTube / Vimeo"
        />
        {videoIssue ? (
          <p className="mt-2 text-sm text-amber-200">{videoIssue}</p>
        ) : null}
        {videoNote ? (
          <p className="mt-2 text-sm text-slate-400">{videoNote}</p>
        ) : null}
        {videoSearchUrl && !pocVideoUrl.trim() ? (
          <p className="mt-2 text-sm text-slate-400">
            YouTube search:{" "}
            <a
              href={videoSearchUrl}
              className="underline decoration-violet-400/50 underline-offset-2 text-violet-200"
              target="_blank"
              rel="noreferrer"
            >
              open results
            </a>
            . We did not pick a video.
          </p>
        ) : null}
      </label>
      {!pocSkipped && !pocEvidence.trim() && !pocVideoUrl.trim() ? (
        <button
          type="button"
          onClick={() => setPocSkipped(true)}
          className="mt-2 border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300"
        >
          {JOBS_POC_SKIP_CTA}
        </button>
      ) : pocSkipped ? (
        <p className="mt-2 font-mono text-xs uppercase tracking-[0.08em] text-slate-500">
          PoC skipped. Employers still prefer proof.
        </p>
      ) : null}

      <fieldset className="mt-6">
        <legend className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          {JOBS_DOCS_HEADING}
        </legend>
        <p className="mt-1 text-sm text-slate-400">{JOBS_DOCS_HINT}</p>
        <input
          type="file"
          accept="application/pdf,image/jpeg,image/png,image/webp,image/gif"
          aria-label="Upload brochure or product spec"
          className="mt-3 block w-full text-sm text-slate-300"
          onChange={event => {
            const file = event.target.files?.[0];
            if (!file || busy) return;
            setBusy(true);
            setError(null);
            void uploadRobotDocument(token, file, "spec")
              .then(doc => {
                setDocs(prev => [doc, ...prev]);
                setSelectedDocs(prev =>
                  prev.includes(doc.id) ? prev : [...prev, doc.id]
                );
              })
              .catch(err => {
                setError(
                  err instanceof Error ? err.message : "Could not upload spec."
                );
              })
              .finally(() => setBusy(false));
            event.target.value = "";
          }}
        />
        {docs.length ? (
          <ul className="mt-3 space-y-2">
            {docs.map(doc => (
              <li key={doc.id}>
                <label className="flex items-center gap-2 text-sm text-slate-200">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={e =>
                      setSelectedDocs(prev =>
                        e.target.checked
                          ? [...prev, doc.id]
                          : prev.filter(id => id !== doc.id)
                      )
                    }
                    className="h-4 w-4 accent-emerald-400"
                  />
                  {doc.filename}
                  {doc.kind ? (
                    <span className="font-mono text-xs uppercase text-slate-500">
                      {doc.kind}
                    </span>
                  ) : null}
                </label>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            No specs on this account yet.
          </p>
        )}
      </fieldset>

      <label className="mt-6 block">
        <span className="block font-display text-xl font-bold text-white">
          {JOBS_PROPOSED_PRICE_LABEL}
        </span>
        <span className="mt-1 block text-sm text-slate-400">
          {JOBS_PROPOSED_PRICE_HINT}
        </span>
        <input
          type="text"
          aria-label={JOBS_PROPOSED_PRICE_LABEL}
          className="mt-3 w-full border border-emerald-400/50 bg-[#081126] px-4 py-3 text-lg text-slate-100"
          value={monthlyPrice}
          onChange={e => setMonthlyPrice(e.target.value)}
          placeholder="e.g. your RaaS / lease quote per month"
        />
      </label>

      {error ? <p className="mt-4 text-sm text-amber-200">{error}</p> : null}

      <label className="mt-6 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          Why you are applying
        </span>
        <span className="mt-1 block text-sm text-slate-400">
          Short recruiter note. We draft one if you leave this blank. You can
          edit it.
        </span>
        <textarea
          aria-label="Why you are applying"
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
          rows={3}
          value={why}
          onChange={e => setWhy(e.target.value)}
          placeholder={`We're putting ${robotName || "this robot"} forward for this job.`}
        />
      </label>

      <p className="mt-6 max-w-xl text-sm leading-relaxed text-slate-300">
        {JOBS_APPLY_SEQUENCE}
      </p>
      <p className="mt-2 text-sm text-slate-400">{JOBS_SEND_DRAFT_HINT}</p>
      <button
        type="button"
        onClick={() => void apply()}
        disabled={!ready || busy}
        className={`mt-3 ${JOBS_APPLY_CTA_BUTTON_CLASS}`}
      >
        {busy ? "Preparing…" : JOBS_APPLY_OFFER_CTA}
      </button>

      {drafts.length ? (
        <div
          className="mt-6 border border-violet-500/40 bg-[#12082a] px-4 py-4"
          data-apply-draft="1"
        >
          <p className={`${JOBS_EYEBROW_CLASS} text-violet-300`}>
            Application draft
          </p>
          <p className="mt-2 text-sm text-slate-300">{JOBS_SEND_DRAFT_HINT}</p>
          {drafts.map(app => {
            const draft = app.draft;
            const contacts = app.contacts || draft?.contacts || [];
            return (
              <article
                key={app.id}
                className="mt-4 border border-slate-700 px-3 py-3"
              >
                <p className="font-mono text-xs uppercase tracking-[0.08em] text-violet-200">
                  {app.work_title} · {app.employer_name}
                </p>
                {draft?.subject ? (
                  <p className="mt-2 text-sm text-slate-200">
                    Subject: {draft.subject}
                  </p>
                ) : null}
                {draft?.why ? (
                  <p className="mt-2 text-sm text-slate-300">{draft.why}</p>
                ) : null}
                {draft?.clip_description ? (
                  <p className="mt-2 text-sm text-slate-400">
                    {draft.clip_description}
                  </p>
                ) : null}
                {app.poc_video_url || draft?.video_url ? (
                  <p className="mt-2 text-sm text-violet-200">
                    Video: {app.poc_video_url || draft?.video_url}
                  </p>
                ) : (
                  <p className="mt-2 text-sm text-amber-200/90">
                    {draft?.video_note || JOBS_VIDEO_EMPTY_NOTE}
                  </p>
                )}
                {contacts.length ? (
                  <p className="mt-2 text-sm text-slate-200">
                    Contact: {contacts.map(c => c.email).join(", ")}
                  </p>
                ) : (
                  <p className="mt-2 text-sm text-amber-200/90">
                    {JOBS_CONTACTS_EMPTY_NOTE}
                  </p>
                )}
                {draft?.body ? (
                  <pre className="mt-3 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-300">
                    {draft.body}
                  </pre>
                ) : null}
                {app.can_operator_send ? (
                  <button
                    type="button"
                    className={`mt-3 ${JOBS_APPLY_CTA_BUTTON_CLASS} px-4 py-2 text-sm`}
                    disabled={busy}
                    onClick={() => {
                      setBusy(true);
                      setError(null);
                      sendPreparedApplication(token, app.id)
                        .then(row => {
                          onApplied(row);
                          setDrafts(prev =>
                            prev.map(item => (item.id === row.id ? row : item))
                          );
                        })
                        .catch(err =>
                          setError(
                            err instanceof Error
                              ? err.message
                              : "Could not send."
                          )
                        )
                        .finally(() => setBusy(false));
                    }}
                  >
                    {JOBS_SEND_DRAFT_CTA}
                  </button>
                ) : (
                  <p className="mt-3 text-sm text-amber-200/90">
                    {app.no_email_reason || JOBS_CONTACTS_EMPTY_NOTE}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
