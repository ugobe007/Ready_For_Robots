import type { LucideIcon } from "lucide-react";
import { BarChart3, Mail, Search } from "lucide-react";

type Accent = "emerald" | "amber" | "blue";

const ACCENT: Record<
  Accent,
  { border: string; iconBg: string; icon: string; stat: string }
> = {
  emerald: {
    border: "border-l-emerald-500",
    iconBg: "bg-emerald-500/10 border border-emerald-500/30",
    icon: "text-emerald-400",
    stat: "text-emerald-300",
  },
  amber: {
    border: "border-l-amber-500",
    iconBg: "bg-amber-500/10 border border-amber-500/30",
    icon: "text-amber-400",
    stat: "text-amber-300",
  },
  blue: {
    border: "border-l-blue-500",
    iconBg: "bg-blue-500/10 border border-blue-500/30",
    icon: "text-blue-400",
    stat: "text-blue-300",
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
  // Signup funnel (conversion board #20)
  signupStart?: number;
  signupComplete?: number;
  firstSave?: number;
  startToCompleteRate?: number;
  completeToSaveRate?: number;
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

function MetricCard({
  icon: Icon,
  accent,
  title,
  value,
  statLabel,
  description,
}: CardSpec) {
  const tone = ACCENT[accent];
  return (
    <div
      className={`rounded-xl border border-slate-700/60 bg-[#0a1226] p-6 shadow-xl border-l-4 ${tone.border} transition-all duration-200 hover:-translate-y-0.5 hover:shadow-2xl`}
    >
      <div className="mb-5 flex items-start justify-between gap-3">
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl ${tone.iconBg}`}
        >
          <Icon size={22} className={tone.icon} />
        </div>
        <div className="text-right">
          <p
            className={`font-mono text-2xl font-black tabular-nums ${tone.stat}`}
          >
            {value}
          </p>
          <p className="text-xs font-medium text-slate-400">{statLabel}</p>
        </div>
      </div>
      <h3 className="mb-2 font-display text-xl font-bold text-white">
        {title}
      </h3>
      <p className="text-sm leading-relaxed text-slate-300">{description}</p>
    </div>
  );
}

type Props = {
  data: SiteMetricsPanelData;
  timeRangeLabel: string;
  loading?: boolean;
};

export default function SiteMetricsPanel({
  data,
  timeRangeLabel,
  loading,
}: Props) {
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
      description:
        "Email capture rate vs funnel activity — waitlist, newsletter, and buyer intake.",
    },
  ];

  return (
    <section className="mb-8">
      <div className="mb-6 text-center md:text-left">
        <p className="mb-2 font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Site funnel · {timeRangeLabel}
        </p>
        <h2 className="font-display text-xl font-bold text-white sm:text-2xl">
          Discover traffic, develop intent, deploy capture.
        </h2>
        {loading ? (
          <p className="mt-2 text-xs font-medium text-slate-400">
            Refreshing metrics…
          </p>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map(card => (
          <MetricCard key={card.title} {...card} />
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-slate-700/60 bg-[#0a1226] px-4 py-3 text-sm">
        <span className="font-semibold text-white">
          Pipeline backing data
        </span>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-300">
          {formatCount(data.hotCount)} hot
        </span>
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-bold text-amber-300">
          {formatCount(data.warmCount)} warm
        </span>
        <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-bold text-blue-300">
          {hotShare}% hot share
        </span>
        <span className="text-xs text-slate-400">
          {formatCount(data.totalSignals)} total signals in database
        </span>
      </div>

      <SignupFunnelStrip data={data} timeRangeLabel={timeRangeLabel} />
    </section>
  );
}

function formatRate(value?: number) {
  if (value == null) return "—";
  return `${value}%`;
}

function SignupFunnelStrip({
  data,
  timeRangeLabel,
}: {
  data: SiteMetricsPanelData;
  timeRangeLabel: string;
}) {
  const start = data.signupStart ?? 0;
  const complete = data.signupComplete ?? 0;
  const save = data.firstSave ?? 0;
  const hasData = start + complete + save > 0;

  const steps = [
    { label: "Signup start", sub: "reached /signup", value: start },
    {
      label: "Signup complete",
      sub: "account created",
      value: complete,
      rate: data.startToCompleteRate,
    },
    {
      label: "First save",
      sub: "activated",
      value: save,
      rate: data.completeToSaveRate,
    },
  ];

  // Flag the weaker conversion step so the operator knows where to focus.
  const s2c = data.startToCompleteRate ?? 0;
  const c2s = data.completeToSaveRate ?? 0;
  let hint = "";
  if (hasData && complete > 0) {
    hint =
      c2s <= s2c
        ? "Activation is the weaker step — improve the first-save guide and pipeline onboarding."
        : "Signup friction is the weaker step — simplify the /signup flow.";
  }

  return (
    <div className="mt-4 rounded-xl border border-slate-700/60 bg-[#0a1226] p-4 shadow-xl">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-400">
          Signup funnel · {timeRangeLabel}
        </p>
        {!hasData ? (
          <span className="text-[11px] font-medium text-slate-400">
            Collecting funnel events…
          </span>
        ) : null}
      </div>
      <div className="flex items-stretch gap-2">
        {steps.map((step, i) => (
          <div key={step.label} className="flex flex-1 items-center gap-2">
            <div className="flex-1 rounded-lg border border-slate-700/60 bg-[#060c1c] px-3 py-2.5 text-center">
              <p className="font-mono text-xl font-bold tabular-nums text-white">
                {formatCount(step.value)}
              </p>
              <p className="mt-0.5 text-xs font-semibold text-slate-200">
                {step.label}
              </p>
              <p className="text-[10px] text-slate-400">{step.sub}</p>
            </div>
            {i < steps.length - 1 ? (
              <div className="flex shrink-0 flex-col items-center text-slate-400">
                <span className="text-lg leading-none">→</span>
                <span className="text-[10px] font-bold text-emerald-400">
                  {formatRate(steps[i + 1].rate)}
                </span>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {hint ? <p className="mt-3 text-xs text-slate-400">{hint}</p> : null}
    </div>
  );
}
