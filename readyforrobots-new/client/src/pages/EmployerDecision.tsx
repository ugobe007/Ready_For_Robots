/**
 * Employer evaluate page — Accept / Set up interview.
 * Token landing; the employer does not need a Ready For Robots account.
 */
import { useEffect, useState } from "react";
import { useRoute, useSearch } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PocVideoWatch from "@/components/PocVideoWatch";
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  JOBS_EMPLOYER_ACCEPT_CTA,
  JOBS_EMPLOYER_CONNECT_CTA,
  JOBS_EMPLOYER_HOLD_CTA,
  JOBS_EMPLOYER_INTERVIEW_CTA,
  JOBS_EMPLOYER_PROPOSE_CTA,
  applicationStatusLabel,
  suggestedHoldSlots,
} from "@/lib/jobsCrmAccount";
import {
  JOBS_EYEBROW_CLASS,
  JOBS_HEADER_OFFSET_CLASS,
} from "@/lib/jobsWorkflow";

type EmployerView = {
  employer_name: string;
  work_title: string;
  workplace?: string | null;
  robot_name: string;
  selected_models: string[];
  monthly_price: string;
  poc_evidence?: string | null;
  poc_video_url?: string | null;
  status: string;
  interview_at?: string | null;
  interview_mode?: string | null;
  slot_start?: string | null;
  slot_end?: string | null;
  slot_label?: string | null;
  hold_expires_at?: string | null;
  documents?: Array<{ id: string; filename: string; kind?: string }>;
  can_accept?: boolean;
  can_interview?: boolean;
  can_hold?: boolean;
};

type InterviewMode = "propose" | "hold";

export default function EmployerDecision() {
  const [, params] = useRoute("/employer/:token");
  const search = useSearch();
  const token = params?.token || "";
  const action = new URLSearchParams(search).get("action") || "";
  const api = getPublicReadApiBase();
  const [data, setData] = useState<EmployerView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [proposedAt, setProposedAt] = useState("");
  const [slotStart, setSlotStart] = useState("");
  const [slotEnd, setSlotEnd] = useState("");
  const [note, setNote] = useState("");
  const [showInterview, setShowInterview] = useState(action === "interview");
  const [mode, setMode] = useState<InterviewMode>(
    action === "hold" ? "hold" : "propose",
  );
  const offered = suggestedHoldSlots();

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setError("This application link is not valid.");
      return;
    }
    fetch(`${api}/api/jobs-crm/employer/${token}`, liveFetchInit())
      .then(async res => {
        if (!res.ok) throw new Error("This application link is not valid.");
        return (await res.json()) as EmployerView;
      })
      .then(row => {
        if (!cancelled) setData(row);
      })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "This application link is not valid.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [api, token]);

  async function post(path: string, body?: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${api}/api/jobs-crm/employer/${token}${path}`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: body ? JSON.stringify(body) : "{}",
        }),
      );
      if (!res.ok) {
        let detail = "Could not update this application.";
        try {
          const payload = (await res.json()) as { detail?: unknown };
          if (typeof payload.detail === "string") detail = payload.detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      setData((await res.json()) as EmployerView);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update this application.");
    } finally {
      setBusy(false);
    }
  }

  const heldWindow = data?.slot_label
    || (data?.slot_start
      ? `${new Date(data.slot_start).toLocaleString()}${
          data.slot_end ? ` – ${new Date(data.slot_end).toLocaleString()}` : ""
        }`
      : null);

  return (
    <div className={`flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>Employer evaluate</p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          {data?.work_title || "Application"}
        </h1>
        {data ? (
          <>
            <p className="mt-2 font-display text-xl font-bold text-emerald-400">
              {data.employer_name}
            </p>
            <p className="mt-2 text-slate-300">
              {data.robot_name}
              {data.selected_models?.length
                ? ` · ${data.selected_models.join(", ")}`
                : ""}
              {data.workplace ? ` · ${data.workplace}` : ""}
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Proposed monthly price (their offer, not a site rate): {data.monthly_price}
            </p>
            {data.poc_evidence ? (
              <p className="mt-2 text-sm text-slate-300">{data.poc_evidence}</p>
            ) : null}
            <PocVideoWatch url={data.poc_video_url} />
            <p className="mt-2 font-mono text-xs uppercase tracking-[0.08em] text-emerald-300">
              {applicationStatusLabel(data.status)}
            </p>
            {data.status === "interview_held" && heldWindow ? (
              <p className="mt-2 text-sm text-slate-200">
                Held slot: {heldWindow}
                {data.hold_expires_at
                  ? ` · hold until ${new Date(data.hold_expires_at).toLocaleString()}`
                  : ""}
              </p>
            ) : data.interview_at ? (
              <p className="mt-2 text-sm text-slate-200">
                Interview: {new Date(data.interview_at).toLocaleString()}
              </p>
            ) : null}
            {data.documents?.length ? (
              <ul className="mt-4 space-y-1 text-sm text-slate-300">
                {data.documents.map(doc => (
                  <li key={doc.id}>
                    <a
                      href={`${api}/api/jobs-crm/employer/${token}/documents/${doc.id}/file`}
                      className="text-emerald-300 underline decoration-emerald-400/50 underline-offset-2"
                    >
                      {doc.filename}
                    </a>
                  </li>
                ))}
              </ul>
            ) : null}
            <div className="mt-8 flex flex-wrap gap-3">
              {data.can_accept ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void post("/accept")}
                  className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] disabled:opacity-40"
                >
                  {JOBS_EMPLOYER_ACCEPT_CTA}
                </button>
              ) : null}
              {data.can_interview ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => setShowInterview(true)}
                  className="inline-flex items-center justify-center border border-emerald-400/50 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-emerald-300 disabled:opacity-40"
                >
                  {JOBS_EMPLOYER_INTERVIEW_CTA}
                </button>
              ) : null}
            </div>
            {showInterview && data.can_interview ? (
              <form
                className="mt-6 space-y-4 border border-emerald-400/40 bg-[#0b162f] px-4 py-5"
                onSubmit={event => {
                  event.preventDefault();
                  if (mode === "hold") {
                    if (!slotStart) {
                      setError("Pick a start time to hold this slot.");
                      return;
                    }
                    void post("/hold", {
                      slot_start: slotStart,
                      slot_end: slotEnd || null,
                      note: note || null,
                    });
                    return;
                  }
                  void post("/interview", {
                    proposed_at: proposedAt || null,
                    note: note || null,
                    connect_you: !proposedAt,
                  });
                }}
              >
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setMode("propose")}
                    className={
                      mode === "propose"
                        ? "border border-emerald-400 bg-emerald-400/15 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300"
                        : "border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300"
                    }
                  >
                    Propose time
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode("hold")}
                    className={
                      mode === "hold"
                        ? "border border-emerald-400 bg-emerald-400/15 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-emerald-300"
                        : "border border-slate-600 px-3 py-2 font-mono text-xs font-bold uppercase tracking-[0.08em] text-slate-300"
                    }
                  >
                    {JOBS_EMPLOYER_HOLD_CTA}
                  </button>
                </div>
                {mode === "propose" ? (
                  <label className="block">
                    <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
                      Proposed interview time
                    </span>
                    <input
                      type="datetime-local"
                      value={proposedAt}
                      onChange={e => setProposedAt(e.target.value)}
                      className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-slate-100"
                    />
                  </label>
                ) : (
                  <>
                    <div>
                      <p className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
                        Offered slots
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {offered.map(slot => (
                          <button
                            key={slot.start}
                            type="button"
                            onClick={() => {
                              setSlotStart(slot.start);
                              setSlotEnd(slot.end);
                            }}
                            className={
                              slotStart === slot.start
                                ? "border border-emerald-400 bg-emerald-400/15 px-3 py-2 text-sm text-emerald-200"
                                : "border border-slate-600 px-3 py-2 text-sm text-slate-200"
                            }
                          >
                            {slot.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <label className="block">
                      <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
                        Slot start
                      </span>
                      <input
                        type="datetime-local"
                        value={slotStart}
                        onChange={e => setSlotStart(e.target.value)}
                        className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-slate-100"
                      />
                    </label>
                    <label className="block">
                      <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>
                        Slot end
                      </span>
                      <input
                        type="datetime-local"
                        value={slotEnd}
                        onChange={e => setSlotEnd(e.target.value)}
                        className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 text-slate-100"
                      />
                    </label>
                  </>
                )}
                <label className="block">
                  <span className={`${JOBS_EYEBROW_CLASS} text-slate-400`}>Note</span>
                  <textarea
                    value={note}
                    onChange={e => setNote(e.target.value)}
                    rows={3}
                    className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100"
                    placeholder="Optional — site window, attendees, constraints"
                  />
                </label>
                <p className="text-sm text-slate-400">
                  {mode === "hold"
                    ? "We hold this window on the application and email both sides. The robot company can confirm or release. This is not Cal sales autonomy."
                    : "Leave the time blank to ask Ready For Robots to connect you with the robot company. We email both sides. This is not Cal sales autonomy."}
                </p>
                <button
                  type="submit"
                  disabled={busy}
                  className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] disabled:opacity-40"
                >
                  {mode === "hold"
                    ? JOBS_EMPLOYER_HOLD_CTA
                    : proposedAt
                      ? JOBS_EMPLOYER_PROPOSE_CTA
                      : JOBS_EMPLOYER_CONNECT_CTA}
                </button>
              </form>
            ) : null}
          </>
        ) : (
          <p className="mt-4 text-slate-300">
            {error || "Loading this application…"}
          </p>
        )}
        {error && data ? (
          <p className="mt-4 text-sm text-amber-200">{error}</p>
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
