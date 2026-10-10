/**
 * OEM hold confirm / release — token landing from the recruiter email.
 * The robot company does not need to hunt the CRM inbox first.
 */
import { useEffect, useState } from "react";
import { useRoute } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import { getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";
import {
  JOBS_OEM_CONFIRM_HOLD_CTA,
  JOBS_OEM_RELEASE_HOLD_CTA,
  applicationStatusLabel,
} from "@/lib/jobsCrmAccount";
import {
  JOBS_EYEBROW_CLASS,
  JOBS_HEADER_OFFSET_CLASS,
} from "@/lib/jobsWorkflow";

type HoldView = {
  employer_name: string;
  work_title: string;
  workplace?: string | null;
  robot_name: string;
  status: string;
  interview_note?: string | null;
  slot_start?: string | null;
  slot_end?: string | null;
  slot_label?: string | null;
  hold_expires_at?: string | null;
  can_confirm_hold?: boolean;
  can_release_hold?: boolean;
};

export default function OemHold() {
  const [, params] = useRoute("/oem-hold/:token");
  const token = params?.token || "";
  const api = getPublicReadApiBase();
  const [data, setData] = useState<HoldView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setError("This hold link is not valid.");
      return;
    }
    fetch(`${api}/api/jobs-crm/oem-hold/${token}`, liveFetchInit())
      .then(async res => {
        if (!res.ok) throw new Error("This hold link is not valid.");
        return (await res.json()) as HoldView;
      })
      .then(row => {
        if (!cancelled) setData(row);
      })
      .catch(err => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "This hold link is not valid."
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [api, token]);

  async function post(path: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${api}/api/jobs-crm/oem-hold/${token}${path}`,
        liveFetchInit({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: "{}",
        })
      );
      if (!res.ok) {
        let detail = "Could not update this hold.";
        try {
          const payload = (await res.json()) as { detail?: unknown };
          if (typeof payload.detail === "string") detail = payload.detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      setData((await res.json()) as HoldView);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not update this hold."
      );
    } finally {
      setBusy(false);
    }
  }

  const windowLabel =
    data?.slot_label ||
    (data?.slot_start
      ? `${new Date(data.slot_start).toLocaleString()}${
          data.slot_end ? ` – ${new Date(data.slot_end).toLocaleString()}` : ""
        }`
      : null);

  return (
    <div
      className={`flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>
          Robot company — held slot
        </p>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          {data?.work_title || "Held interview"}
        </h1>
        {data ? (
          <>
            <p className="mt-2 font-display text-xl font-bold text-emerald-400">
              {data.employer_name}
            </p>
            <p className="mt-2 text-slate-300">
              {data.robot_name}
              {data.workplace ? ` · ${data.workplace}` : ""}
            </p>
            <p className="mt-2 font-mono text-xs uppercase tracking-[0.08em] text-emerald-300">
              {applicationStatusLabel(data.status)}
            </p>
            {windowLabel ? (
              <p className="mt-3 text-sm text-slate-200">
                Held slot: {windowLabel}
                {data.hold_expires_at
                  ? ` · hold until ${new Date(data.hold_expires_at).toLocaleString()}`
                  : ""}
              </p>
            ) : null}
            {data.interview_note ? (
              <p className="mt-2 text-sm text-slate-400">
                {data.interview_note}
              </p>
            ) : null}
            <p className="mt-4 text-sm text-slate-400">
              Confirm books this window. Release frees it so the employer can
              propose or hold another time. This is not Cal sales autonomy.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {data.can_confirm_hold ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void post("/confirm")}
                  className="inline-flex items-center justify-center bg-emerald-400 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-[#04122a] disabled:opacity-40"
                >
                  {JOBS_OEM_CONFIRM_HOLD_CTA}
                </button>
              ) : null}
              {data.can_release_hold ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void post("/release")}
                  className="inline-flex items-center justify-center border border-emerald-400/50 px-6 py-4 text-base font-bold uppercase tracking-[0.06em] text-emerald-300 disabled:opacity-40"
                >
                  {JOBS_OEM_RELEASE_HOLD_CTA}
                </button>
              ) : null}
            </div>
          </>
        ) : (
          <p className="mt-4 text-slate-300">
            {error || "Loading this held slot…"}
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
