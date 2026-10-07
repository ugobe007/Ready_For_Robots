/**
 * Customer jobs pipeline report on CRM — named employer + work for one robot.
 * Not SIGNAL buyers. Not invented match %.
 */
import { Link } from "wouter";
import {
  CRM_EMPLOYER_NAME_CLASS,
  CRM_WATCH_FREE_HINT,
  CRM_WATCH_LOCKED_HINT,
  CRM_WATCH_OPT_IN_LABEL,
  CRM_WATCH_REPORT_EYEBROW,
  CRM_WATCH_SIGNED_OUT,
  CRM_WATCH_UPGRADE_CTA,
  FIND_JOBS_CTA,
  JOBS_EYEBROW_CLASS,
} from "@/lib/jobsWorkflow";
import { jobsFindHref } from "@/lib/jobsLanding";
import {
  jobsWatchCheckedLabel,
  type JobsWatchStatus,
} from "@/lib/jobsCrmAccount";

export type { JobsWatchStatus };

type Props = {
  signedIn?: boolean;
  watch?: JobsWatchStatus | null;
  watchReady?: boolean;
  watchBusy?: boolean;
  watchError?: string | null;
  onOptIn?: (optedIn: boolean) => void;
};

export default function JobsWatchReport({
  signedIn = false,
  watch,
  watchReady = true,
  watchBusy,
  watchError,
  onOptIn,
}: Props) {
  const optedIn = Boolean(watch?.opted_in);
  const events = watch?.events || [];
  const product = watch?.product_name || watch?.robot_url;
  return (
    <section
      className="mt-5 border border-emerald-500/30 bg-emerald-400/5 px-4 py-4"
      aria-label={CRM_WATCH_REPORT_EYEBROW}
    >
      <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>
        {CRM_WATCH_REPORT_EYEBROW}
      </p>
      <label className="mt-3 flex cursor-pointer items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 h-5 w-5 accent-emerald-400"
          checked={optedIn}
          disabled={!signedIn || !watchReady || watchBusy}
          onChange={e => onOptIn?.(e.target.checked)}
        />
        <span>
          <span className="block text-base font-semibold text-white">
            {CRM_WATCH_OPT_IN_LABEL}
          </span>
          <span className="mt-1 block text-sm leading-relaxed text-slate-300">
            {signedIn ? CRM_WATCH_FREE_HINT : CRM_WATCH_SIGNED_OUT}
          </span>
        </span>
      </label>
      {watchError ? (
        <p className="mt-3 text-sm text-amber-200">{watchError}</p>
      ) : null}
      {optedIn && product ? (
        <p className="mt-3 font-mono text-sm text-emerald-300">
          Watching {product}
          {" · "}
          {jobsWatchCheckedLabel(watch?.last_checked_at)}
        </p>
      ) : null}
      {events.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {events.slice(0, 5).map((event, i) => (
            <li
              key={event.id ?? i}
              className={`text-sm ${event.locked ? "text-slate-500" : "text-slate-200"}`}
            >
              {event.locked ? (
                CRM_WATCH_LOCKED_HINT
              ) : (
                <>
                  {event.company_name ? (
                    <span className={`block ${CRM_EMPLOYER_NAME_CLASS}`}>
                      {event.company_name}
                    </span>
                  ) : null}
                  <span>{event.title}</span>
                </>
              )}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        <a
          href={jobsFindHref()}
          className="font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
        >
          {FIND_JOBS_CTA}
        </a>
        {watch?.free_taste && optedIn ? (
          <Link
            href={watch.upgrade_url || "/pricing"}
            className="font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
          >
            {CRM_WATCH_UPGRADE_CTA}
          </Link>
        ) : null}
      </div>
    </section>
  );
}
