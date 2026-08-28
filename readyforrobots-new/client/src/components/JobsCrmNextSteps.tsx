import { useEffect, useState } from "react";
import {
  JOBS_APPLY_OFFER_CTA,
  JOBS_APPLY_SELECTED_CTA,
  JOBS_APPLY_SEQUENCE,
  JOBS_DOCS_HEADING,
  JOBS_DOCS_HINT,
  JOBS_MODEL_SELECT_HINT,
  JOBS_MODEL_SELECT_LABEL,
  JOBS_PROPOSED_PRICE_HINT,
  JOBS_PROPOSED_PRICE_LABEL,
  applyJobOnAccount,
  applySelectedJobsOnAccount,
  canSubmitNextStepsOffer,
  fetchCatalogSkus,
  fetchRobotDocuments,
  uploadRobotDocument,
  type CatalogSku,
  type JobsCrmApplication,
  type RobotDocument,
} from "@/lib/jobsCrmAccount";
import {
  JOBS_POC_PREFER_HINT,
  JOBS_POC_SKIP_CTA,
} from "@/lib/jobsApply";
import {
  JOBS_POC_VIDEO_HINT,
  JOBS_POC_VIDEO_LABEL,
  JOBS_POC_VIDEO_SCRIPT_HEADING,
  pocVideoScriptBeats,
  pocVideoUrlIssue,
} from "@/lib/pocVideoUrl";
import { JOBS_EYEBROW_CLASS, crmSaveJobsBlurb } from "@/lib/jobsWorkflow";
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
  const selectedJobs = (jobs && jobs.length ? jobs : [job]).filter(j => j?.job_key);
  const card = robotJobCardFromMatch(job);
  const [skus, setSkus] = useState<CatalogSku[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [monthlyPrice, setMonthlyPrice] = useState("");
  const [pocEvidence, setPocEvidence] = useState("");
  const [pocVideoUrl, setPocVideoUrl] = useState("");
  const [pocSkipped, setPocSkipped] = useState(false);
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
    return () => {
      cancelled = true;
    };
  }, [token, robotUrl, robotName]);

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
      const skipped = pocSkipped || (!pocEvidence.trim() && !pocVideoUrl.trim());
      if (selectedJobs.length > 1) {
        const result = await applySelectedJobsOnAccount(token, {
          jobs: selectedJobs,
          robotName,
          selectedModels: models,
          monthlyPrice,
          pocEvidence,
          pocVideoUrl,
          pocSkipped: skipped,
          documentIds: selectedDocs,
        });
        for (const app of result.applied) onApplied(app);
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
          job,
          documentIds: selectedDocs,
        });
        onApplied(app);
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
        Offer for {selectedJobs.length > 1 ? `${selectedJobs.length} selected jobs` : card.jobTitle}
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-300">
        {crmSaveJobsBlurb(robotName)}
      </p>

      <label className="mt-6 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>Robot name</span>
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
                  prev.includes(doc.id) ? prev : [...prev, doc.id],
                );
              })
              .catch(err => {
                setError(
                  err instanceof Error ? err.message : "Could not upload spec.",
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
                          : prev.filter(id => id !== doc.id),
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

      {error ? (
        <p className="mt-4 text-sm text-amber-200">{error}</p>
      ) : null}

      <p className="mt-6 max-w-xl text-sm leading-relaxed text-slate-300">
        {JOBS_APPLY_SEQUENCE}
      </p>
      <button
        type="button"
        onClick={() => void apply()}
        disabled={!ready || busy}
        className="mt-3 inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {busy
          ? "Applying…"
          : selectedJobs.length > 1
            ? JOBS_APPLY_SELECTED_CTA
            : JOBS_APPLY_OFFER_CTA}
      </button>
    </section>
  );
}
