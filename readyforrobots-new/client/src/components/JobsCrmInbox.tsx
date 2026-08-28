import { useEffect, useState } from "react";
import {
  JOBS_INBOX_HEADING,
  JOBS_INBOX_PASTE_HINT,
  applicationStatusLabel,
  declineReasonLabel,
  confirmHoldOnAccount,
  confirmInterviewOnAccount,
  fetchApplicationThread,
  JOBS_OEM_CONFIRM_HOLD_CTA,
  JOBS_OEM_RELEASE_HOLD_CTA,
  markApplicationOutcome,
  releaseHoldOnAccount,
  pasteInboundReply,
  replyOnApplication,
  threadStateLabel,
  type JobsCrmApplication,
} from "@/lib/jobsCrmAccount";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";
import PocVideoWatch from "@/components/PocVideoWatch";

export default function JobsCrmInbox({
  applicationId,
  token,
  initial,
}: {
  applicationId: string;
  token: string;
  initial?: JobsCrmApplication | null;
}) {
  const [app, setApp] = useState<JobsCrmApplication | null>(initial || null);
  const [reply, setReply] = useState("");
  const [paste, setPaste] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchApplicationThread(token, applicationId)
      .then(row => {
        if (!cancelled) setApp(row);
      })
      .catch(() => {
        /* keep initial */
      });
    return () => {
      cancelled = true;
    };
  }, [token, applicationId]);

  async function sendReply() {
    if (!reply.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      setApp(await replyOnApplication(token, applicationId, reply.trim()));
      setReply("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send reply.");
    } finally {
      setBusy(false);
    }
  }

  async function storePaste() {
    if (!paste.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      setApp(await pasteInboundReply(token, applicationId, paste.trim()));
      setPaste("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not store reply.");
    } finally {
      setBusy(false);
    }
  }

  if (!app) return null;
  const messages = app.messages || [];

  return (
    <section
      aria-label={JOBS_INBOX_HEADING}
      className="mt-6 border border-slate-600 bg-[#081126] px-4 py-5"
    >
      <p className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>{JOBS_INBOX_HEADING}</p>
      <p className="mt-1 font-mono text-xs uppercase tracking-[0.08em] text-emerald-300">
        {applicationStatusLabel(app.status)}
        {" · "}
        {threadStateLabel(app.thread_state)}
        {app.send_status ? ` · ${app.send_status.replace(/_/g, " ")}` : ""}
      </p>
      {app.status === "declined" ? (
        <p className="mt-2 text-sm text-slate-200">
          Employer declined
          {app.decline_reason_code
            ? `: ${app.decline_reason_label || declineReasonLabel(app.decline_reason_code)}`
            : ""}
          {app.decline_note ? ` — ${app.decline_note}` : ""}
        </p>
      ) : app.status === "interview_held" && (app.slot_label || app.slot_start) ? (
        <p className="mt-2 text-sm text-slate-200">
          Held slot: {app.slot_label || new Date(app.slot_start || "").toLocaleString()}
          {app.hold_expires_at
            ? ` · hold until ${new Date(app.hold_expires_at).toLocaleString()}`
            : ""}
        </p>
      ) : app.interview_at ? (
        <p className="mt-2 text-sm text-slate-200">
          Interview: {new Date(app.interview_at).toLocaleString()}
          {app.interview_mode ? ` · ${app.interview_mode.replace(/_/g, " ")}` : ""}
        </p>
      ) : app.interview_mode === "connect_you" ? (
        <p className="mt-2 text-sm text-slate-200">
          Employer asked us to connect you. Confirm or arrange a time.
        </p>
      ) : null}
      {app.interview_note ? (
        <p className="mt-1 text-sm text-slate-400">{app.interview_note}</p>
      ) : null}
      {app.documents && app.documents.length ? (
        <p className="mt-2 text-sm text-slate-400">
          Specs attached: {app.documents.map(doc => doc.filename).join(", ")}
        </p>
      ) : null}
      {app.poc_evidence ? (
        <p className="mt-2 text-sm text-slate-300">{app.poc_evidence}</p>
      ) : null}
      <PocVideoWatch url={app.poc_video_url} />
      {!app.can_send ? (
        <p className="mt-2 text-sm text-amber-200/90">
          {app.no_email_reason ||
            "No employer email on this Job Card. Outreach cannot send. The offer is stored."}
        </p>
      ) : null}
      {app.send_error && app.send_status !== "not_sent_no_email" ? (
        <p className="mt-2 text-sm text-amber-200">{app.send_error}</p>
      ) : null}

      <ul className="mt-4 space-y-3" aria-label="Application thread">
        {messages.length === 0 ? (
          <li className="text-sm text-slate-400">
            No thread yet. Apply stores the offer here. Employer replies land
            here when inbound mail is wired, or when you paste them.
          </li>
        ) : (
          messages.map(msg => (
            <li
              key={msg.id}
              className="border border-slate-700 px-3 py-3 text-sm text-slate-200"
            >
              <p className="font-mono text-xs uppercase tracking-[0.08em] text-slate-500">
                {msg.direction === "inbound" ? "Employer" : "You"}
                {msg.from_email ? ` · ${msg.from_email}` : ""}
              </p>
              <pre className="mt-2 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200">
                {msg.body}
              </pre>
            </li>
          ))
        )}
      </ul>

      {app.can_send ? (
        <label className="mt-4 block">
          <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>Reply</span>
          <textarea
            className="mt-2 w-full border border-slate-600 bg-[#0b162f] px-3 py-2 text-sm text-slate-100"
            rows={4}
            value={reply}
            onChange={e => setReply(e.target.value)}
            placeholder="Reply to the employer"
          />
          <button
            type="button"
            onClick={() => void sendReply()}
            disabled={!reply.trim() || busy}
            className="mt-2 border border-emerald-400/50 bg-emerald-400/10 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300 disabled:opacity-40"
          >
            Send reply
          </button>
        </label>
      ) : null}

      <label className="mt-4 block">
        <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
          Paste employer reply
        </span>
        <p className="mt-1 text-sm text-slate-400">{JOBS_INBOX_PASTE_HINT}</p>
        <textarea
          className="mt-2 w-full border border-slate-600 bg-[#0b162f] px-3 py-2 text-sm text-slate-100"
          rows={4}
          value={paste}
          onChange={e => setPaste(e.target.value)}
          placeholder="Paste the employer email body"
        />
        <button
          type="button"
          onClick={() => void storePaste()}
          disabled={!paste.trim() || busy}
          className="mt-2 border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300 disabled:opacity-40"
        >
          Store reply
        </button>
      </label>
      <div className="mt-4 flex flex-wrap gap-2">
        {app.can_confirm_hold || app.status === "interview_held" ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              setError(null);
              void confirmHoldOnAccount(token, applicationId)
                .then(setApp)
                .catch(err =>
                  setError(
                    err instanceof Error ? err.message : "Could not confirm this hold.",
                  ),
                )
                .finally(() => setBusy(false));
            }}
            className="border border-emerald-400/50 bg-emerald-400/10 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300 disabled:opacity-40"
          >
            {JOBS_OEM_CONFIRM_HOLD_CTA}
          </button>
        ) : null}
        {app.can_release_hold || app.status === "interview_held" ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              setError(null);
              void releaseHoldOnAccount(token, applicationId)
                .then(setApp)
                .catch(err =>
                  setError(
                    err instanceof Error ? err.message : "Could not release this hold.",
                  ),
                )
                .finally(() => setBusy(false));
            }}
            className="border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300 disabled:opacity-40"
          >
            {JOBS_OEM_RELEASE_HOLD_CTA}
          </button>
        ) : null}
        {app.status === "interview_scheduled" || app.status === "interview_requested" ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              setError(null);
              void confirmInterviewOnAccount(token, applicationId)
                .then(setApp)
                .catch(err =>
                  setError(
                    err instanceof Error ? err.message : "Could not confirm interview.",
                  ),
                )
                .finally(() => setBusy(false));
            }}
            className="border border-emerald-400/50 bg-emerald-400/10 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300 disabled:opacity-40"
          >
            Confirm interview
          </button>
        ) : null}
        {app.status &&
        !["success", "failed", "declined"].includes(app.status) ? (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                setError(null);
                void markApplicationOutcome(token, applicationId, "success")
                  .then(setApp)
                  .catch(err =>
                    setError(
                      err instanceof Error ? err.message : "Could not record outcome.",
                    ),
                  )
                  .finally(() => setBusy(false));
              }}
              className="border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300 disabled:opacity-40"
            >
              Mark success
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                setError(null);
                void markApplicationOutcome(token, applicationId, "failed")
                  .then(setApp)
                  .catch(err =>
                    setError(
                      err instanceof Error ? err.message : "Could not record outcome.",
                    ),
                  )
                  .finally(() => setBusy(false));
              }}
              className="border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300 disabled:opacity-40"
            >
              Mark unsuccessful
            </button>
          </>
        ) : null}
      </div>
      {error ? <p className="mt-3 text-sm text-amber-200">{error}</p> : null}
    </section>
  );
}
