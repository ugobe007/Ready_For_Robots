/**
 * Operator top-25 Robot Job sales cards — same cards emailed daily.
 * Named employers and work. Not SIGNAL buyers. No invented people.
 */
import { Mail } from "lucide-react";

export type DailyJobsReportJob = {
  rank?: number;
  job_key?: string;
  employer?: string;
  title?: string;
  locality?: string;
  action?: string;
  job_type?: string;
  description?: string;
  decision_maker?: string;
  timing?: string;
  contact?: string;
  employer_email?: string | null;
  contact_url?: string | null;
  apply_url?: string | null;
};

export type DailyJobsReportData = {
  date?: string;
  count?: number;
  limit?: number;
  jobs?: DailyJobsReportJob[];
  recipients?: string[];
  last_sent_date?: string | null;
  find_href?: string;
};

type Props = {
  data: DailyJobsReportData | null;
  loading?: boolean;
  sending?: boolean;
  sendError?: string | null;
  onSend?: () => void;
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-400">
        {label}
      </p>
      <p className="mt-0.5 whitespace-pre-wrap text-sm text-slate-100">{value}</p>
    </div>
  );
}

export default function AdminDailyJobsReport({
  data,
  loading,
  sending,
  sendError,
  onSend,
}: Props) {
  const jobs = data?.jobs || [];
  const today = data?.date ?? new Date().toISOString().slice(0, 10);
  return (
    <section
      id="daily-jobs-report"
      className="mb-6 scroll-mt-28 rounded-2xl border border-emerald-500/40 bg-[#0c192e] px-5 py-5 shadow-xl"
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Mail size={16} className="text-emerald-400" />
          <div>
            <h2 className="text-sm font-bold text-white">
              Top 25 robot job sales cards
            </h2>
            <p className="text-[11px] text-slate-400">
              UTC {today}
              {data?.last_sent_date
                ? ` · last emailed ${data.last_sent_date}`
                : " · not emailed yet today"}
              {data?.recipients?.[0] ? ` · ${data.recipients[0]}` : ""}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onSend}
          disabled={sending || loading}
          className="inline-flex items-center justify-center bg-emerald-500 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] text-[#090d16] hover:bg-emerald-400 disabled:opacity-50"
        >
          {sending ? "Sending…" : "Email the 25 cards now"}
        </button>
      </div>
      {sendError ? (
        <p className="mb-3 text-sm text-red-300">{sendError}</p>
      ) : null}
      {loading ? (
        <p className="py-2 text-sm text-slate-400">Loading jobs…</p>
      ) : jobs.length === 0 ? (
        <p className="text-sm text-slate-400">
          No named-employer jobs in the live table yet.
        </p>
      ) : (
        <ol className="space-y-3">
          {jobs.map(job => {
            const jobType = job.job_type || job.title || "Work";
            const description = job.description || job.title || "";
            const typeBlock =
              description && description !== jobType
                ? `${jobType}\n${description}`
                : jobType;
            return (
              <li
                key={job.job_key || `${job.rank}-${job.employer}`}
                className="border border-slate-700/60 bg-[#060c1c] px-3 py-3"
              >
                <p className="text-[11px] font-mono text-slate-500">
                  {String(job.rank || 0).padStart(2, "0")}
                </p>
                <p className="font-display text-base font-bold text-emerald-400">
                  {job.employer}
                </p>
                {job.locality ? (
                  <p className="text-[12px] text-slate-400">{job.locality}</p>
                ) : null}
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <Field label="[1] Job type and description" value={typeBlock} />
                  <Field
                    label="[2] Decision maker"
                    value={job.decision_maker || "Not named on the posting"}
                  />
                  <Field
                    label="[3] Timing"
                    value={job.timing || "Timing not on the posting"}
                  />
                  <Field
                    label="[4] Contact information"
                    value={
                      job.contact ||
                      "No page email or apply URL. We will not invent one."
                    }
                  />
                </div>
              </li>
            );
          })}
        </ol>
      )}
      <p className="mt-3 text-[11px] text-slate-500">
        Page-sourced contacts only. Daily email at 14:00 UTC to
        ugobe07@gmail.com. FIND stays <code>/?visit=jobs</code>.
      </p>
    </section>
  );
}
