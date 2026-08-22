/**
 * CRM page chrome — Kare face, emerald headline, how-to, jobs-watch opt-in.
 */
import { type ReactNode } from "react";
import { Link } from "wouter";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  CRM_HEADLINE_CLASS,
  CRM_HOW_TO_STEPS,
  CRM_PAGE_HEADLINE,
  CRM_PAGE_NEXT,
  CRM_WATCH_FREE_HINT,
  CRM_WATCH_OPT_IN_LABEL,
  CRM_WATCH_SIGNED_OUT,
  JOBS_EYEBROW_CLASS,
  jobsFreshHomeHref,
  onJobsFreshHomeClick,
} from "@/lib/jobsWorkflow";

export type JobsWatchStatus = {
  opted_in: boolean;
  plan?: string;
  robot_url?: string | null;
  product_name?: string | null;
  last_checked_at?: string | null;
  robots_used?: number;
  robots_limit?: number | null;
  alerts_sent?: number;
  alerts_limit?: number | null;
  events?: Array<{
    id?: number;
    kind?: string;
    title?: string;
    company_name?: string | null;
    locked?: boolean;
  }>;
  upgrade_url?: string;
  free_taste?: boolean;
};

type Props = {
  signedIn?: boolean;
  watch?: JobsWatchStatus | null;
  watchBusy?: boolean;
  watchError?: string | null;
  onOptIn?: (optedIn: boolean) => void;
  actions?: ReactNode;
  footer?: ReactNode;
};

export default function CrmHero({
  signedIn = false,
  watch,
  watchBusy,
  watchError,
  onOptIn,
  actions,
  footer,
}: Props) {
  const optedIn = Boolean(watch?.opted_in);
  const events = watch?.events || [];
  return (
    <div className="mb-5 border border-slate-600 bg-[#0b162f] px-5 py-5 sm:px-6">
      <div className="flex items-start gap-4">
        <PixelIcon
          map={KARE_FACE}
          scale={3}
          fill={FACE_EMERALD}
          background="transparent"
          className="mt-1 shrink-0"
        />
        <div className="min-w-0 flex-1">
          <p className={`${JOBS_EYEBROW_CLASS} text-emerald-400`}>ReadyForRobots</p>
          <h1 className={`mt-2 ${CRM_HEADLINE_CLASS}`}>{CRM_PAGE_HEADLINE}</h1>
          <p className="mt-2 max-w-2xl text-base leading-relaxed text-slate-300">
            {CRM_PAGE_NEXT}
          </p>
        </div>
      </div>

      <ol className="mt-5 max-w-2xl space-y-2">
        {CRM_HOW_TO_STEPS.map((step, i) => (
          <li key={step} className="flex gap-3 text-base leading-relaxed text-slate-200">
            <span className="font-mono text-emerald-400">{i + 1}.</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>

      <div className="mt-5 border border-emerald-500/30 bg-emerald-400/5 px-4 py-4">
        <label className="flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-5 w-5 accent-emerald-400"
            checked={optedIn}
            disabled={!signedIn || watchBusy}
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
        {optedIn && watch?.robot_url ? (
          <p className="mt-3 font-mono text-sm text-emerald-300">
            Watching {watch.product_name || watch.robot_url}
            {watch.last_checked_at ? " · last check recorded" : " · first check runs on the daily cron"}
          </p>
        ) : null}
        {events.length > 0 ? (
          <ul className="mt-3 space-y-1.5">
            {events.slice(0, 5).map((event, i) => (
              <li
                key={event.id ?? i}
                className={`text-sm ${event.locked ? "text-slate-500" : "text-slate-200"}`}
              >
                {event.locked
                  ? "Pro sees this new job — upgrade to keep the feed."
                  : `• ${event.title}${event.company_name ? ` · ${event.company_name}` : ""}`}
              </li>
            ))}
          </ul>
        ) : null}
        {watch?.free_taste && optedIn ? (
          <Link
            href={watch.upgrade_url || "/pricing"}
            className="mt-3 inline-block font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
          >
            Keep watching with Pro →
          </Link>
        ) : null}
      </div>

      {actions ? <div className="mt-4 flex flex-wrap gap-3">{actions}</div> : null}
      {footer ? <div className="mt-4 text-base text-slate-400">{footer}</div> : null}
      <a
        href={jobsFreshHomeHref()}
        onClick={onJobsFreshHomeClick}
        className="mt-4 inline-flex font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
      >
        + New robot
      </a>
    </div>
  );
}
