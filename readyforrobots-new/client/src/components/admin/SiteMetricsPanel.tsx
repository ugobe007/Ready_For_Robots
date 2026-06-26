import type { LucideIcon } from "lucide-react";
import { BarChart3, Mail, Search } from "lucide-react";

type Accent = "emerald" | "amber" | "blue";

const ACCENT: Record<
  Accent,
  { border: string; iconBg: string; icon: string; stat: string }
> = {
  emerald: {
    border: "border-l-emerald-500",
    iconBg: "bg-emerald-50",
    icon: "text-emerald-600",
    stat: "text-emerald-700",
  },
  amber: {
    border: "border-l-amber-500",
    iconBg: "bg-amber-50",
    icon: "text-amber-700",
    stat: "text-amber-800",
  },
  blue: {
    border: "border-l-blue-500",
    iconBg: "bg-blue-50",
    icon: "text-blue-700",
    stat: "text-blue-800",
  },
};

export type SiteMetricsPanelData = {
  siteVisits?: number;
  funnelRuns?: number;
  buyerIntake?: number;
  emailCaptures?: number;
  conversionRate?: number;
  hotCount?: number;
  warmCount?: number;
  totalSignals?: number;
};

type CardSpec = {
  icon: LucideIcon;
  accent: Accent;
  title: string;
  value: string;
  statLabel: string;
  description: string;
};

function formatCount(value?: number) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

function MetricCard({ icon: Icon, accent, title, value, statLabel, description }: CardSpec) {
  const tone = ACCENT[accent];
  return (
    <div
      className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm border-l-4 ${tone.border} transition-shadow hover:shadow-md`}
    >
      <div className="mb-5 flex items-start justify-between gap-3">
        <div className={`flex h-11 w-11 items-center justify-center rounded-lg ${tone.iconBg}`}>
          <Icon size={22} className={tone.icon} />
        </div>
        <div className="text-right">
          <p className={`font-mono text-2xl font-bold tabular-nums ${tone.stat}`}>{value}</p>
          <p className="text-xs font-medium text-gray-600">{statLabel}</p>
        </div>
      </div>
      <h3 className="mb-2 font-display text-xl font-bold text-gray-900">{title}</h3>
      <p className="text-sm leading-relaxed text-gray-700">{description}</p>
    </div>
  );
}

type Props = {
  data: SiteMetricsPanelData;
  timeRangeLabel: string;
  loading?: boolean;
};

export default function SiteMetricsPanel({ data, timeRangeLabel, loading }: Props) {
  const funnelRuns = (data.funnelRuns ?? 0) + (data.buyerIntake ?? 0);
  const pipelineLeads = (data.hotCount ?? 0) + (data.warmCount ?? 0);
  const hotShare = pipelineLeads
    ? Math.round(((data.hotCount ?? 0) / pipelineLeads) * 100)
    : 0;

  const cards: CardSpec[] = [
    {
      icon: Search,
      accent: "emerald",
      title: "Discover",
      value: formatCount(data.siteVisits),
      statLabel: "site visits",
      description: `Traffic reaching readyforrobots.com in the last ${timeRangeLabel}. Page views plus SCOUT sessions.`,
    },
    {
      icon: BarChart3,
      accent: "amber",
      title: "Develop",
      value: formatCount(funnelRuns || data.totalSignals),
      statLabel: funnelRuns ? "funnel runs" : "pipeline signals",
      description: funnelRuns
        ? "URL scans, ROI runs, and Find Robots intake — people evaluating the product."
        : "Live scored signals in pipeline when front-end funnel events are still sparse.",
    },
    {
      icon: Mail,
      accent: "blue",
      title: "Deploy",
      value: `${data.conversionRate ?? 0}%`,
      statLabel: `${formatCount(data.emailCaptures)} emails captured`,
      description: "Email capture rate vs funnel activity — waitlist, newsletter, and buyer intake.",
    },
  ];

  return (
    <section className="mb-8">
      <div className="mb-6 text-center md:text-left">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-800">
          Site funnel · {timeRangeLabel}
        </p>
        <h2 className="font-display text-xl font-bold text-gray-900 sm:text-2xl">
          Discover traffic, develop intent, deploy capture.
        </h2>
        {loading ? (
          <p className="mt-2 text-xs font-medium text-gray-600">Refreshing metrics…</p>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <MetricCard key={card.title} {...card} />
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-sm">
        <span className="font-semibold text-gray-900">Pipeline backing data</span>
        <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
          {formatCount(data.hotCount)} hot
        </span>
        <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900">
          {formatCount(data.warmCount)} warm
        </span>
        <span className="rounded-full border border-blue-300 bg-blue-50 px-3 py-1 text-xs font-bold text-blue-900">
          {hotShare}% hot share
        </span>
        <span className="text-xs text-gray-700">
          {formatCount(data.totalSignals)} total signals in database
        </span>
      </div>
    </section>
  );
}
