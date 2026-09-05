/**
 * Paid product-presentation offer. Renders after Job Cards, never in front of FIND.
 */
import { useState } from "react";
import {
  JOBS_PRESENTATION_CTA,
  JOBS_PRESENTATION_HINT,
  JOBS_PRESENTATION_PAY_HINT,
  JOBS_PRESENTATION_QUEUED,
  jobsPresentationHref,
  jobsPresentationPaid,
  requestRobotPresentation,
} from "@/lib/jobsPresentation";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";

export default function JobsPresentationOffer({
  signedIn,
  plan,
  token,
  robotUrl,
  companyName,
  productName,
}: {
  signedIn: boolean;
  plan?: string | null;
  token?: string | null;
  robotUrl: string;
  companyName?: string;
  productName?: string;
}) {
  const paid = jobsPresentationPaid(plan);
  const href = jobsPresentationHref({ signedIn, paid });
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function queuePaid() {
    if (!token || !robotUrl || busy) return;
    setBusy(true);
    setNote(null);
    try {
      const result = await requestRobotPresentation(token, {
        url: robotUrl,
        companyName,
        productName,
      });
      setNote(result.hint || result.note || JOBS_PRESENTATION_QUEUED);
    } catch (err) {
      setNote(err instanceof Error ? err.message : JOBS_PRESENTATION_PAY_HINT);
    } finally {
      setBusy(false);
    }
  }

  return (
    <aside
      id="jobs-presentation"
      aria-label={JOBS_PRESENTATION_CTA}
      className="mt-8 border border-slate-600 bg-[#081126] px-4 py-5"
    >
      <p className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>After Job Cards</p>
      <h3 className="mt-2 font-display text-lg font-bold text-white">
        {JOBS_PRESENTATION_CTA}
      </h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-300">
        {JOBS_PRESENTATION_HINT}
      </p>
      {!signedIn || !paid ? (
        <a
          href={href}
          className="mt-4 inline-flex items-center justify-center border border-emerald-400/50 bg-emerald-400/10 px-4 py-3 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300"
        >
          {signedIn
            ? "Pay to order this presentation →"
            : "Sign up and pay to order →"}
        </a>
      ) : (
        <button
          type="button"
          onClick={() => void queuePaid()}
          disabled={busy || !robotUrl}
          className="mt-4 inline-flex items-center justify-center bg-emerald-400 px-4 py-3 font-mono text-xs font-bold uppercase tracking-[0.08em] text-[#04122a] disabled:opacity-40"
        >
          {busy ? "Queuing…" : "Queue presentation →"}
        </button>
      )}
      {note ? <p className="mt-3 text-sm text-slate-300">{note}</p> : null}
    </aside>
  );
}
