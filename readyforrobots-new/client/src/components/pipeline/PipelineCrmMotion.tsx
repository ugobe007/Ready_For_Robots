/**
 * CRM motion on /pipeline — one obvious next step, not a second setup checklist.
 *
 * Before the first save: activate CRM by saving the selected buyer.
 * After the first save: show the working accounts and a single Open CRM action.
 */
import { Link } from "wouter";
import { ArrowRight, Bookmark, LayoutDashboard, Plug } from "lucide-react";

export type CrmMotionDeal = {
  id: number;
  company: string;
  stage: string;
  industry?: string;
};

type Props = {
  hasSession: boolean;
  savedCount: number;
  selectedCompany?: string | null;
  selectedSaved?: boolean;
  saving?: boolean;
  onActivateCrm?: () => void;
  hubspotConnected?: boolean;
  savedDeals?: CrmMotionDeal[];
  selectedId?: number | null;
  onSelectDeal?: (id: number) => void;
  jobsAutomate?: boolean;
};

export default function PipelineCrmMotion({
  hasSession,
  savedCount,
  selectedCompany,
  selectedSaved = false,
  saving = false,
  onActivateCrm,
  hubspotConnected = false,
  savedDeals = [],
  selectedId = null,
  onSelectDeal,
  jobsAutomate = false,
}: Props) {
  if (!hasSession) return null;

  const company = (selectedCompany || (jobsAutomate ? "this job" : "this buyer")).trim()
    || (jobsAutomate ? "this job" : "this buyer");
  const crmLive = savedCount > 0;

  if (!crmLive) {
    return (
      <section className="pipeline-crm-motion pipeline-crm-motion-activate">
        <p className="pipeline-crm-motion-kicker">
          {jobsAutomate ? "CRM · automate jobs" : "CRM · next action"}
        </p>
        <h2 className="pipeline-crm-motion-title">
          {jobsAutomate ? "Automate jobs" : "Activate CRM on this page"}
        </h2>
        <p className="pipeline-crm-motion-body">
          {jobsAutomate
            ? `We apply to the jobs you unlocked and help land the robot. Automate jobs for ${company} starts CRM automation for that employer.`
            : `Saving ${company} starts your working pipeline. Native CRM is the default path; HubSpot can sync after the first save.`}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onActivateCrm}
            disabled={saving || !onActivateCrm || selectedSaved}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-400 px-4 py-2.5 text-sm font-extrabold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Bookmark className="h-4 w-4" />
            {saving
              ? "Saving…"
              : jobsAutomate
                ? `Automate jobs — apply ${company}`
                : `Activate CRM — save ${company}`}
            {!saving && <ArrowRight className="h-4 w-4" />}
          </button>
          <Link
            href="/integrations/hubspot"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-500 bg-[#0b162f] px-4 py-2.5 text-sm font-semibold text-slate-100 hover:border-slate-400"
          >
            <Plug className="h-4 w-4" />
            Prefer HubSpot?
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="pipeline-crm-motion pipeline-crm-motion-live">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="pipeline-crm-motion-kicker">Your CRM pipeline</p>
          <h2 className="pipeline-crm-motion-title">
            {savedCount} active account{savedCount === 1 ? "" : "s"}
          </h2>
          <p className="pipeline-crm-motion-body">
            {jobsAutomate
              ? "CRM automation is applying to these jobs. Open a row to keep landing the robot, or open CRM for the full list."
              : "Work saved buyers here, then open the full CRM to advance stages and track replies."}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href="/crm"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-extrabold text-slate-950 hover:bg-emerald-400"
          >
            <LayoutDashboard className="h-4 w-4" />
            Open CRM
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/integrations/hubspot"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-500 bg-[#0b162f] px-4 py-2.5 text-sm font-semibold text-slate-100 hover:border-slate-400"
          >
            <Plug className="h-4 w-4" />
            {hubspotConnected ? "HubSpot connected" : "Connect HubSpot"}
          </Link>
        </div>
      </div>
      {savedDeals.length > 0 ? (
        <ul className="mt-4 space-y-1.5">
          {savedDeals.slice(0, 5).map((deal) => {
            const active = deal.id === selectedId;
            return (
              <li key={deal.id}>
                <button
                  type="button"
                  onClick={() => onSelectDeal?.(deal.id)}
                  className={`flex w-full items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-left transition ${
                    active
                      ? "border-emerald-400/70 bg-emerald-400/10"
                      : "border-slate-600 bg-[#0b162f] hover:border-slate-400"
                  }`}
                >
                  <span className="pipeline-company-name truncate">{deal.company}</span>
                  <span className="shrink-0 text-xs font-bold uppercase tracking-wide text-emerald-300">
                    {deal.stage}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
