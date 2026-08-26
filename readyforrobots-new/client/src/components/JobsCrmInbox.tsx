import { useEffect, useState } from "react";
import {
  JOBS_INBOX_HEADING,
  JOBS_INBOX_PASTE_HINT,
  fetchApplicationThread,
  pasteInboundReply,
  replyOnApplication,
  threadStateLabel,
  type JobsCrmApplication,
} from "@/lib/jobsCrmAccount";
import { JOBS_EYEBROW_CLASS } from "@/lib/jobsWorkflow";

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
        {threadStateLabel(app.thread_state)}
        {app.send_status ? ` · ${app.send_status.replace(/_/g, " ")}` : ""}
      </p>
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
      {error ? <p className="mt-3 text-sm text-amber-200">{error}</p> : null}
    </section>
  );
}
