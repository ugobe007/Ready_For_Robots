/**
 * Operator top-25 Robot Jobs — same list emailed daily.
 * Named employers and work. Not SIGNAL buyers.
 */
import { Mail } from "lucide-react";

export type DailyJobsReportJob = {
  rank?: number;
  job_key?: string;
  employer?: string;
  title?: string;
  locality?: string;
  action?: string;
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
      className="mb-4 scroll-mt-28 rounded-xl border-2 border-emerald-300 bg-white px-5 py-5 shadow-sm"
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Mail size={16} className="text-emerald-700" />
          <div>
            <h2 className="text-sm font-bold text-gray-900">
              Top 25 robot jobs
            </h2>
            <p className="text-[11px] text-gray-600">
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
          className="inline-flex items-center justify-center bg-emerald-700 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] text-white hover:bg-emerald-600 disabled:opacity-50"
        >
          {sending ? "Sending…" : "Email now"}
        </button>
      </div>
      {sendError ? (
        <p className="mb-3 text-sm text-red-800">{sendError}</p>
      ) : null}
      {loading ? (
        <p className="py-2 text-sm text-gray-600">Loading jobs…</p>
      ) : jobs.length === 0 ? (
        <p className="text-sm text-gray-600">
          No named-employer jobs in the live table yet.
        </p>
      ) : (
        <ol className="space-y-2">
          {jobs.map(job => (
            <li
              key={job.job_key || `${job.rank}-${job.employer}`}
              className="border border-gray-200 bg-gray-50 px-3 py-2"
            >
              <p className="text-[11px] font-mono text-gray-500">
                {String(job.rank || 0).padStart(2, "0")}
              </p>
              <p className="font-display text-base font-bold text-emerald-700">
                {job.employer}
              </p>
              <p className="text-sm text-gray-900">{job.title}</p>
              {job.locality ? (
                <p className="text-[12px] text-gray-600">{job.locality}</p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
      <p className="mt-3 text-[11px] text-gray-500">
        Named employers and the work. Daily email at 14:00 UTC. FIND stays{" "}
        <code>/?visit=jobs</code>.
      </p>
    </section>
  );
}
