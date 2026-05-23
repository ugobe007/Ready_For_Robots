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
          color: "#FFB000",
        },
        {
          label: "Drafts in queue",
          value: (m.unsent_drafted ?? 0) + (m.scout_drafted ?? 0),
          sub: `${m.sendable ?? 0} sendable · ${m.drafts_created_today ?? 0} drafted today`,
          icon: FileEdit,
          color: "#c4b5fd",
        },
        {
          label: "Emails sent today",
          value: m.emails_sent_today ?? 0,
          sub: `${m.emails_sent_total ?? 0} total sent`,
          icon: Send,
          color: "#6ee7b7",
        },
        {
          label: "Action items",
          value: data?.next_steps?.length ?? 0,
          sub: `${m.needs_approval ?? 0} approvals · ${m.research_pending ?? 0} research`,
          icon: Mail,
          color: "#60a5fa",
        },
      ]
    : [];

  return (
    <div
      className="mb-4 rounded-2xl border px-5 py-5"
      style={{ background: "rgba(0,255,135,0.04)", borderColor: "rgba(0,255,135,0.18)" }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Sun size={16} style={{ color: "#FFB000" }} />
        <div>
          <h2 className="text-sm font-bold text-white">Daily brief</h2>
          <p className="text-[11px] text-white/35">UTC {today} · intake, outreach, next steps</p>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-white/40 py-4">Loading today&apos;s activity…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            {statCards.map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-white/8 px-3 py-3"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <s.icon size={12} style={{ color: s.color }} />
                  <span className="text-[10px] text-white/45">{s.label}</span>
                </div>
                <div className="text-xl font-bold font-mono" style={{ color: s.color }}>{s.value}</div>
                <div className="text-[10px] text-white/30 mt-0.5">{s.sub}</div>
              </div>
            ))}
          </div>

          {(data?.next_steps?.length ?? 0) > 0 ? (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-2">Next steps</p>
              <div className="flex flex-col gap-2">
                {data!.next_steps!.map((step) => (
                  <a
                    key={step.label}
                    href={step.href}
                    onClick={goToStep(step.href)}
                    className="flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm text-white/85 hover:bg-white/[0.04] transition-colors cursor-pointer no-underline"
                    style={{
                      borderColor: step.priority === "high" ? "rgba(255,176,0,0.35)" : "rgba(255,255,255,0.08)",
                      background: step.priority === "high" ? "rgba(255,176,0,0.06)" : "rgba(255,255,255,0.02)",
                    }}
                  >
                    <span>
                      <strong className="font-mono" style={{ color: "#FFB000" }}>{step.count}</strong>
                      {" "}{step.label}
                    </span>
                    <ArrowRight size={14} className="text-white/30 shrink-0" />
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-white/35">No pending workflow actions — queue is clear.</p>
          )}
        </>
      )}
    </div>
  );
}
