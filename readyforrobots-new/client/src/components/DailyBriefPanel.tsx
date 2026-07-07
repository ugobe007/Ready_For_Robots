import { useLocation } from "wouter";
import { Sun } from "lucide-react";
import SupabaseInlineLink from "@/components/admin/SupabaseInlineLink";
import { scrollToAdminSection, scrollToAdminSectionFromHref } from "@/lib/adminNavigation";

function normalizePath(path: string) {
  return (path.replace(/^\/readyforrobots/, "") || "/").replace(/\/$/, "") || "/";
}

export type DailyBriefData = {
  date?: string;
  metrics?: {
    new_companies_today?: number;
    new_signals_today?: number;
    new_hot_warm_today?: number;
    drafts_created_today?: number;
    unsent_drafted?: number;
    sendable?: number;
    cal_queue_total?: number | null;
    cal_queue_pending?: number | null;
    cal_queue_scope?: string | null;
    emails_sent_today?: number;
    emails_sent_total?: number;
    scout_drafted?: number;
    needs_approval?: number;
    research_pending?: number;
  };
  next_steps?: Array<{
    label: string;
    count: number;
    href: string;
    priority: "high" | "medium" | "low";
  }>;
};

type CalActions = {
  pendingDraft?: number;
  sendable?: number;
  onDraftAll?: () => void;
  onSendAll?: () => void;
  onOpenQueue?: () => void;
  draftBusy?: boolean;
  sendBusy?: boolean;
};

type Props = {
  data: DailyBriefData | null;
  loading?: boolean;
  calActions?: CalActions;
};

export default function DailyBriefPanel({ data, loading, calActions }: Props) {
  const [, setLocation] = useLocation();
  const m = data?.metrics;
  const today = data?.date ?? new Date().toISOString().slice(0, 10);

  const goToStep = (href: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const hashIndex = href.indexOf("#");
    const path = hashIndex === -1 ? href : href.slice(0, hashIndex);
    const hash = hashIndex === -1 ? "" : href.slice(hashIndex + 1);
    const current = normalizePath(window.location.pathname);
    const target = normalizePath(path || current);

    if (target === current) {
      if (hash) {
        window.history.replaceState(null, "", `${window.location.pathname}#${hash}`);
        scrollToAdminSection(hash);
      }
      return;
    }

    setLocation(href);
    if (hash) {
      window.setTimeout(() => scrollToAdminSection(hash), 400);
    }
  };

  const nonCalSteps = (data?.next_steps ?? []).filter(
    (s) => !s.label.toLowerCase().includes("cal autopilot")
      && !s.label.toLowerCase().includes("cal leads need drafting")
      && !s.label.toLowerCase().includes("cal drafts need approval")
      && !s.label.toLowerCase().includes("hot leads not yet"),
  );

  const calTotal = m?.cal_queue_total ?? 0;
  const calPending = calActions?.pendingDraft ?? m?.cal_queue_pending ?? 0;
  const calSendable = calActions?.sendable ?? m?.sendable ?? 0;
  const calUnsent = m?.unsent_drafted ?? 0;

  const openQueue = calActions?.onOpenQueue ?? (() => scrollToAdminSection("cal-outreach"));

  return (
    <div className="mb-4 rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white px-5 py-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <Sun size={16} className="text-amber-600" />
        <div>
          <h2 className="text-sm font-bold text-gray-900">Daily brief</h2>
          <p className="text-[11px] text-gray-600">UTC {today}</p>
        </div>
      </div>

      {loading ? (
        <p className="py-2 text-sm text-gray-600">Loading…</p>
      ) : (
        <>
          <div className="mb-4">
            <p className="admin-kicker mb-1.5">Do now</p>
            <div className="text-sm leading-relaxed text-gray-800">
              {(calPending ?? 0) > 0 && calActions?.onDraftAll ? (
                <>
                  <SupabaseInlineLink onClick={calActions.onDraftAll} busy={calActions.draftBusy}>
                    Draft {calPending} Cal leads
                  </SupabaseInlineLink>
                  <span className="text-gray-400"> · </span>
                </>
              ) : null}
              {(calSendable ?? 0) > 0 && calActions?.onSendAll ? (
                <>
                  <SupabaseInlineLink onClick={calActions.onSendAll} busy={calActions.sendBusy} tone="amber">
                    Send {calSendable} Cal emails
                  </SupabaseInlineLink>
                  <span className="text-gray-400"> · </span>
                </>
              ) : null}
              {calTotal > 0 ? (
                <>
                  <SupabaseInlineLink tone="blue" onClick={openQueue}>
                    Open Cal queue
                  </SupabaseInlineLink>
                  {nonCalSteps.length > 0 ? <span className="text-gray-400"> · </span> : null}
                </>
              ) : null}
              {nonCalSteps.map((step, i) => (
                <span key={step.label}>
                  {i > 0 ? <span className="text-gray-400"> · </span> : null}
                  <SupabaseInlineLink href={step.href} onNavigate={goToStep(step.href)}>
                    {step.count} {step.label}
                  </SupabaseInlineLink>
                </span>
              ))}
              {!calPending && !calSendable && calTotal === 0 && nonCalSteps.length === 0 ? (
                <span className="text-gray-600">No pending actions.</span>
              ) : null}
            </div>
          </div>

          <div className="text-sm text-gray-700">
            <span className="font-medium text-gray-900">Cal outreach (HOT/WARM):</span>{" "}
            {calTotal} in queue · {calPending} need drafting · {calUnsent} drafted unsent · {calSendable} ready to send
            {(m?.scout_drafted ?? 0) > 0 ? (
              <span className="text-gray-600"> · SIGNAL: {m?.scout_drafted} drafts (separate)</span>
            ) : null}
            {calTotal > 0 ? (
              <>
                <span className="text-gray-400"> · </span>
                <SupabaseInlineLink tone="gray" onClick={openQueue}>
                  jump to queue
                </SupabaseInlineLink>
              </>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
