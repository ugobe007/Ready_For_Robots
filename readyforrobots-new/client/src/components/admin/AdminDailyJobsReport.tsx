/**
 * Operator top-25 hot job opportunities — same inline text emailed daily.
 * Named employers, stored decision maker and contact. CSV download, no job cards.
 */
import { useState } from "react";
import { Copy, Mail } from "lucide-react";
import {
  composeEmployerNeedIntro,
  composeRobotCompanyIntro,
} from "@/lib/oemJobIntro";

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
  decision_maker_name?: string | null;
  timing?: string;
  contact?: string;
  employer_email?: string | null;
  contact_url?: string | null;
  apply_url?: string | null;
  contact_source?: string | null;
  target_titles?: string[];
  match_why?: string | null;
  intro?: string | null;
  employer_intro?: string | null;
};

export type DailyJobsReportHunter = {
  ok?: boolean;
  looked_up?: number;
  filled?: number;
  skipped?: number;
  missed?: number;
  reason?: string | null;
  enabled?: boolean;
};

export type DailyJobsReportData = {
  date?: string;
  count?: number;
  limit?: number;
  jobs?: DailyJobsReportJob[];
  recipients?: string[];
  last_sent_date?: string | null;
  find_href?: string;
  hunter?: DailyJobsReportHunter;
};

type Props = {
  data: DailyJobsReportData | null;
  loading?: boolean;
  sending?: boolean;
  enriching?: boolean;
  sendError?: string | null;
  onSend?: () => void;
  onEnrich?: () => void;
  onDownloadCsv?: () => void;
  downloading?: boolean;
};

function jobNameLine(job: DailyJobsReportJob): string {
  const title = job.title || job.job_type || "Work";
  const description = job.description || "";
  if (description && description !== title) return `${title} — ${description}`;
  return title;
}

function decisionMakerLine(job: DailyJobsReportJob): string {
  const parts = [job.decision_maker || "Not named on the posting"];
  if (!job.decision_maker_name && job.target_titles?.length) {
    parts.push(`Looked for: ${job.target_titles.slice(0, 3).join(", ")}`);
  }
  if (job.match_why) parts.push(job.match_why);
  return parts.join(" · ");
}

function IntroField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  if (!value) return null;
  return (
    <div className="sm:col-span-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-400">
          {label}
        </p>
        <button
          type="button"
          onClick={() => {
            void navigator.clipboard.writeText(value).then(() => {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1500);
            });
          }}
          className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-[0.08em] text-emerald-300 hover:text-emerald-200"
        >
          <Copy size={12} />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p className="mt-0.5 whitespace-pre-wrap text-sm text-slate-100">
        {value}
      </p>
    </div>
  );
}

export default function AdminDailyJobsReport({
  data,
  loading,
  sending,
  enriching,
  sendError,
  onSend,
  onEnrich,
  onDownloadCsv,
  downloading,
}: Props) {
  const jobs = data?.jobs || [];
  const today = data?.date ?? new Date().toISOString().slice(0, 10);
  const hunter = data?.hunter;
  return (
    <section
      id="daily-jobs-report"
      className="mb-6 scroll-mt-28 border border-emerald-500/40 bg-[#0c192e] px-3 py-2"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Mail size={16} className="text-emerald-400" />
          <div>
            <h2 className="text-sm font-bold text-white">
              Top 25 hot job opportunities
            </h2>
            <p className="text-[11px] text-slate-400">
              UTC {today}
              {data?.last_sent_date
                ? ` · last emailed ${data.last_sent_date}`
                : " · not emailed yet today"}
              {data?.recipients?.[0] ? ` · ${data.recipients[0]}` : ""}
              {" · Hunter.io company lookup"}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onEnrich}
            disabled={sending || enriching || loading}
            className="inline-flex items-center justify-center border border-emerald-500/60 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-50"
          >
            {enriching
              ? "Looking up companies…"
              : "Look up companies on Hunter.io"}
          </button>
          <button
            type="button"
            onClick={onDownloadCsv}
            disabled={sending || enriching || loading || downloading}
            className="inline-flex items-center justify-center border border-emerald-500/60 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-50"
          >
            {downloading ? "Preparing CSV…" : "Download CSV"}
          </button>
          <button
            type="button"
            onClick={onSend}
            disabled={sending || enriching || loading}
            className="inline-flex items-center justify-center bg-emerald-500 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] text-[#090d16] hover:bg-emerald-400 disabled:opacity-50"
          >
            {sending ? "Sending…" : "Email the 25 jobs now"}
          </button>
        </div>
      </div>
      {sendError ? (
        <p className="mt-2 text-sm text-red-300">{sendError}</p>
      ) : null}
      {loading ? (
        <p className="mt-2 text-sm text-slate-400">Loading jobs…</p>
      ) : jobs.length === 0 ? (
        <p className="mt-2 text-sm text-slate-400">
          No named-employer jobs in the live table yet.
        </p>
      ) : (
        <ol className="mt-3">
          {jobs.map(job => {
            const place = [job.employer, job.locality]
              .filter(Boolean)
              .join(" · ");
            const robotIntro =
              job.intro ||
              composeRobotCompanyIntro({
                title: job.title || job.job_type,
                employer: job.employer,
                locality: job.locality,
                requirements: job.description || job.title,
                decisionMakerName: job.decision_maker,
              });
            const employerIntro =
              job.employer_intro ||
              composeEmployerNeedIntro({
                contactName: job.decision_maker,
                announcedNeed: job.title || job.job_type,
                automationTasks: job.description,
              });
            return (
              <li
                key={job.job_key || `${job.rank}-${job.employer}`}
                className="mt-2 text-sm leading-snug text-slate-200 first:mt-0"
              >
                <span className="font-mono text-slate-500">
                  {String(job.rank || 0).padStart(2, "0")}
                </span>{" "}
                <span className="font-bold text-emerald-400">{place}</span>
                <br />
                {jobNameLine(job)}
                <br />
                Decision maker: {decisionMakerLine(job)}
                <br />
                Contact:{" "}
                {job.contact ||
                  "No page email or apply URL. We will not invent one."}
                {robotIntro ? (
                  <>
                    <br />
                    <IntroField
                      label="[5] Intro to the robot company"
                      value={robotIntro}
                    />
                  </>
                ) : null}
                {employerIntro ? (
                  <>
                    <br />
                    <IntroField
                      label="[6] Intro to the employer"
                      value={employerIntro}
                    />
                  </>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
      {hunter ? (
        <p className="mt-3 text-[11px] text-slate-400">
          Hunter.io
          {typeof hunter.filled === "number" ? ` filled ${hunter.filled}` : ""}
          {typeof hunter.missed === "number"
            ? ` · missed ${hunter.missed}`
            : ""}
          {typeof hunter.skipped === "number"
            ? ` · already had ${hunter.skipped}`
            : ""}
          {hunter.reason ? ` · ${hunter.reason}` : ""}
        </p>
      ) : null}
      <p className="mt-2 text-[11px] text-slate-500">
        Look up companies reads the employer leadership page, then asks
        Hunter.io for that person&apos;s email (name, company, and site domain).
        We do not invent people. Daily email at 14:00 UTC to ugobe07@gmail.com
        is this text, with the CSV attached. Download CSV saves the same file.
      </p>
    </section>
  );
}
