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
  unsentDrafted?: number;
  sendable?: number;
  noEmail?: number;
  onDraftAll?: () => void;
  onRedraft?: () => void;
  onFixEmails?: () => void;
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

    setLocation(path || current);
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
  const calUnsent = calActions?.unsentDrafted ?? m?.unsent_drafted ?? 0;
  const calNoEmail = calActions?.noEmail ?? 0;

  const openQueue = calActions?.onOpenQueue ?? (() => scrollToAdminSection("cal-outreach"));

  // Order the "Do now" links by where they sit in the outreach lifecycle so the
  // brief reads as a chronological timeline (discover → research → draft →
  // review → send → replies) instead of an arbitrary link soup.
  const stageRank = (label: string): number => {
    const l = label.toLowerCase();
    if (l.includes("new") || l.includes("compan") || l.includes("hot")) return 1;
    if (l.includes("research")) return 2;
    if (l.includes("draft") && !l.includes("signal") && !l.includes("awaiting")) return 3;
    if (l.includes("review") || l.includes("signal") || l.includes("awaiting") || l.includes("approv")) return 4;
    if (l.includes("send") || l.includes("email")) return 5;
    if (l.includes("repl") || l.includes("follow") || l.includes("inbox")) return 6;
    return 5;
  };

  return (
    <div className="mb-4 rounded-xl border-2 border-gray-300 bg-white px-5 py-5 shadow-sm">
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
            <p className="admin-kicker mb-1.5">Do now · in workflow order</p>
            <div className="text-sm leading-relaxed text-gray-800">
              {(() => {
                const items: Array<{ rank: number; key: string; node: React.ReactNode }> = [];
                if ((calNoEmail ?? 0) > 0 && calActions?.onFixEmails) {
                  items.push({
                    rank: 1,
                    key: "cal-fix",
                    node: (
                      <SupabaseInlineLink tone="amber" onClick={calActions.onFixEmails}>
                        Fix {calNoEmail} Cal contact emails
                      </SupabaseInlineLink>
                    ),
                  });
                }
                if ((calPending ?? 0) > 0 && calActions?.onDraftAll) {
                  items.push({
                    rank: 2,
                    key: "cal-draft",
                    node: (
                      <SupabaseInlineLink onClick={calActions.onDraftAll} busy={calActions.draftBusy}>
                        Draft {calPending} Cal leads
                      </SupabaseInlineLink>
                    ),
                  });
                }
                if ((calUnsent ?? 0) > 0 && calActions?.onRedraft) {
                  items.push({
                    rank: 3,
                    key: "cal-redraft",
                    node: (
                      <SupabaseInlineLink tone="amber" onClick={calActions.onRedraft} busy={calActions.draftBusy}>
                        Redraft {calUnsent} unsent
                      </SupabaseInlineLink>
                    ),
                  });
                }
                if (calTotal > 0) {
                  items.push({
                    rank: 4,
                    key: "cal-open",
                    node: (
                      <SupabaseInlineLink tone="blue" onClick={openQueue}>
                        Review Cal queue
                      </SupabaseInlineLink>
                    ),
                  });
                }
                if ((calSendable ?? 0) > 0 && calActions?.onSendAll) {
                  items.push({
                    rank: 5,
                    key: "cal-send",
                    node: (
                      <SupabaseInlineLink onClick={calActions.onSendAll} busy={calActions.sendBusy} tone="amber">
                        Send {calSendable} Cal emails
                      </SupabaseInlineLink>
                    ),
                  });
                }
                nonCalSteps.forEach((step) => {
                  items.push({
                    rank: stageRank(step.label),
                    key: `step-${step.label}`,
                    node: (
                      <SupabaseInlineLink href={step.href} onNavigate={goToStep(step.href)}>
                        {step.count} {step.label}
                      </SupabaseInlineLink>
                    ),
                  });
                });
                items.sort((a, b) => a.rank - b.rank);
                if (items.length === 0) {
                  return <span className="text-gray-600">No pending actions.</span>;
                }
                return items.map((item, i) => (
                  <span key={item.key}>
                    {i > 0 ? <span className="text-gray-400"> · </span> : null}
                    {item.node}
                  </span>
                ));
              })()}
            </div>
          </div>

          <div className="text-sm text-gray-700">
            <span className="font-semibold text-gray-950">Cal queue:</span>{" "}
            {calTotal} leads · {calPending} need draft · {calUnsent} unsent · {calSendable} sendable
            {(m?.scout_drafted ?? 0) > 0 ? (
              <span className="text-gray-600"> · SIGNAL drafts separate ({m?.scout_drafted})</span>
            ) : null}
            {calTotal > 0 ? (
              <>
                <span className="text-gray-400"> · </span>
                <SupabaseInlineLink tone="gray" onClick={openQueue}>
                  jump to workflow
                </SupabaseInlineLink>
              </>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
