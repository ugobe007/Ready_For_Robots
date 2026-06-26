import { useLocation } from "wouter";
import { ArrowRight, FileEdit, Mail, Send, Sun, Users } from "lucide-react";

function scrollToHash(hash: string) {
  if (!hash) return;
  document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

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

type Props = {
  data: DailyBriefData | null;
  loading?: boolean;
};

export default function DailyBriefPanel({ data, loading }: Props) {
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
        scrollToHash(hash);
      }
      return;
    }

    setLocation(href);
    if (hash) {
      window.setTimeout(() => scrollToHash(hash), 400);
    }
  };

  const statCards = m
    ? [
        {
          label: "New leads today",
          value: (m.new_companies_today ?? 0) + (m.new_hot_warm_today ?? 0),
          sub: `${m.new_companies_today ?? 0} companies · ${m.new_signals_today ?? 0} signals`,
          icon: Users,
          color: "#b45309",
        },
        {
          label: "Drafts in queue",
          value: (m.unsent_drafted ?? 0) + (m.scout_drafted ?? 0),
          sub: `${m.sendable ?? 0} sendable · ${m.drafts_created_today ?? 0} drafted today`,
          icon: FileEdit,
          color: "#7c3aed",
        },
        {
          label: "Emails sent today",
          value: m.emails_sent_today ?? 0,
          sub: `${m.emails_sent_total ?? 0} total sent`,
          icon: Send,
          color: "#047857",
        },
        {
          label: "Action items",
          value: data?.next_steps?.length ?? 0,
          sub: `${m.needs_approval ?? 0} approvals · ${m.research_pending ?? 0} research`,
          icon: Mail,
          color: "#2563eb",
        },
      ]
    : [];

  return (
    <div className="mb-4 rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white px-5 py-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <Sun size={16} className="text-amber-600" />
        <div>
          <h2 className="text-sm font-bold text-gray-900">Daily brief</h2>
          <p className="text-[11px] text-gray-600">UTC {today} · intake, outreach, next steps</p>
        </div>
      </div>

      {loading ? (
        <p className="py-4 text-sm text-gray-600">Loading today&apos;s activity…</p>
      ) : (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {statCards.map((s) => (
              <div key={s.label} className="rounded-lg border border-gray-200 bg-white px-3 py-3">
                <div className="mb-1 flex items-center gap-1.5">
                  <s.icon size={12} style={{ color: s.color }} />
                  <span className="text-[10px] font-medium text-gray-600">{s.label}</span>
                </div>
                <div className="font-mono text-xl font-bold" style={{ color: s.color }}>{s.value}</div>
                <div className="mt-0.5 text-[10px] font-medium text-gray-700">{s.sub}</div>
              </div>
            ))}
          </div>

          {(data?.next_steps?.length ?? 0) > 0 ? (
            <div>
              <p className="admin-kicker mb-2">Next steps</p>
              <div className="flex flex-col gap-2">
                {data!.next_steps!.map((step) => (
                  <a
                    key={step.label}
                    href={step.href}
                    onClick={goToStep(step.href)}
                    className={`flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2.5 text-sm no-underline transition-colors hover:bg-gray-50 ${
                      step.priority === "high"
                        ? "border-amber-300 bg-amber-50 text-gray-900"
                        : "border-gray-200 bg-white text-gray-800"
                    }`}
                  >
                    <span>
                      <strong className="font-mono text-amber-700">{step.count}</strong>
                      {" "}{step.label}
                    </span>
                    <ArrowRight size={14} className="shrink-0 text-gray-600" />
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-600">No pending workflow actions — queue is clear.</p>
          )}
        </>
      )}
    </div>
  );
}
