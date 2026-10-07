import { useEffect, useState } from "react";
import {
  JOBS_DOC_KINDS,
  JOBS_DOCS_EMPTY,
  JOBS_DOCS_HEADING,
  JOBS_DOCS_HINT,
  JOBS_DOCS_INCLUDE_LABEL,
  deleteRobotDocument,
  fetchRobotDocuments,
  robotDocumentKindLabel,
  updateRobotDocument,
  uploadRobotDocument,
  type RobotDocument,
} from "@/lib/jobsCrmAccount";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";

export default function RobotSalesMaterial({
  token,
  robotUrl,
  robotName,
  onIncludedIds,
  onReady,
}: {
  token: string;
  robotUrl?: string;
  robotName?: string;
  onIncludedIds?: (ids: string[]) => void;
  onReady?: () => void;
}) {
  const [docs, setDocs] = useState<RobotDocument[]>([]);
  const [kind, setKind] = useState<(typeof JOBS_DOC_KINDS)[number]["id"]>(
    "spec"
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!robotUrl) {
      setDocs([]);
      onIncludedIds?.([]);
      onReady?.();
      return;
    }
    let cancelled = false;
    fetchRobotDocuments(token, robotUrl)
      .then(rows => {
        if (cancelled) return;
        setDocs(rows);
        onIncludedIds?.(
          rows.filter(row => row.include_with_submissions).map(row => row.id)
        );
        onReady?.();
      })
      .catch(() => {
        if (cancelled) return;
        setDocs([]);
        onIncludedIds?.([]);
        onReady?.();
      });
    return () => {
      cancelled = true;
    };
  }, [token, robotUrl]);

  function publish(rows: RobotDocument[]) {
    setDocs(rows);
    onIncludedIds?.(
      rows.filter(row => row.include_with_submissions).map(row => row.id)
    );
  }

  return (
    <fieldset className="mt-6 border border-slate-700 bg-[#081126] px-4 py-4">
      <legend className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
        {JOBS_DOCS_HEADING}
        {robotName ? ` · ${robotName}` : ""}
      </legend>
      <p className="mt-1 text-sm text-slate-400">{JOBS_DOCS_HINT}</p>
      {robotUrl ? (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="text-sm text-slate-300">
            <span className="mr-2 font-mono text-xs uppercase tracking-[0.08em] text-slate-500">
              File type
            </span>
            <select
              aria-label="File type"
              value={kind}
              onChange={event =>
                setKind(
                  event.target.value as (typeof JOBS_DOC_KINDS)[number]["id"]
                )
              }
              className="border border-slate-600 bg-[#0b162f] px-2 py-2 text-slate-100"
            >
              {JOBS_DOC_KINDS.map(row => (
                <option key={row.id} value={row.id}>
                  {row.label}
                </option>
              ))}
            </select>
          </label>
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp,image/gif"
            aria-label="Upload spec sheet, brochure, or certificate"
            disabled={busy}
            className="block text-sm text-slate-300"
            onChange={event => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (!file || busy || !robotUrl) return;
              setBusy(true);
              setError(null);
              void uploadRobotDocument(token, file, kind, {
                robotUrl,
                robotName,
                includeWithSubmissions: true,
              })
                .then(doc => publish([doc, ...docs]))
                .catch(err => {
                  setError(
                    err instanceof Error ? err.message : "Could not upload."
                  );
                })
                .finally(() => setBusy(false));
            }}
          />
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          Submit a robot URL before uploading sales material. Each file belongs
          to one robot.
        </p>
      )}
      {error ? <p className="mt-3 text-sm text-amber-200">{error}</p> : null}
      {docs.length ? (
        <ul className="mt-4 space-y-3">
          {docs.map(doc => (
            <li key={doc.id} className="text-sm text-slate-200">
              <p>
                {doc.filename}{" "}
                <span className="font-mono text-xs uppercase text-slate-500">
                  {robotDocumentKindLabel(doc.kind)}
                </span>
              </p>
              <label className="mt-1 flex items-center gap-2 text-slate-300">
                <input
                  type="checkbox"
                  checked={Boolean(doc.include_with_submissions)}
                  aria-label={`${JOBS_DOCS_INCLUDE_LABEL} ${doc.filename}`}
                  className="h-4 w-4 accent-emerald-400"
                  onChange={event => {
                    const include = event.target.checked;
                    setBusy(true);
                    setError(null);
                    void updateRobotDocument(token, doc.id, {
                      includeWithSubmissions: include,
                    })
                      .then(updated =>
                        publish(
                          docs.map(row => (row.id === updated.id ? updated : row))
                        )
                      )
                      .catch(err => {
                        setError(
                          err instanceof Error
                            ? err.message
                            : "Could not update this file."
                        );
                      })
                      .finally(() => setBusy(false));
                  }}
                />
                {JOBS_DOCS_INCLUDE_LABEL}
              </label>
              <button
                type="button"
                className="mt-1 font-mono text-xs uppercase tracking-[0.08em] text-slate-500 underline decoration-slate-600 underline-offset-2"
                onClick={() => {
                  setBusy(true);
                  setError(null);
                  void deleteRobotDocument(token, doc.id)
                    .then(() => publish(docs.filter(row => row.id !== doc.id)))
                    .catch(err => {
                      setError(
                        err instanceof Error
                          ? err.message
                          : "Could not remove this file."
                      );
                    })
                    .finally(() => setBusy(false));
                }}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      ) : robotUrl ? (
        <p className="mt-3 text-sm text-slate-500">{JOBS_DOCS_EMPTY}</p>
      ) : null}
    </fieldset>
  );
}
