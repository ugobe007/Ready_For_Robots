/**
 * Hero live pipeline widget — emerald redesign skin, /api/leads/homepage data.
 */
import { useEffect, useRef, useState } from "react";
import { ArrowRight, Building2, Factory, Heart, Hotel, Truck, Utensils } from "lucide-react";
import { Link } from "wouter";
import { fetchHomepageLeadPool } from "@/lib/homepageLeads";
import PipelineLeadActionMeta from "@/components/pipeline/PipelineLeadActionMeta";
import { HeatBadge, LiveDot } from "@/components/marketing/primitives";
import { formatStat } from "@/hooks/usePipelineStats";

type LeadRow = {
  id: number;
  company_name?: string;
  industry?: string;
  priority_tier?: string;
  core_need?: string | null;
  share_summary?: string | null;
  pipeline_action?: string | null;
  robot_types_needed?: string[];
  signals?: { display_text?: string }[];
  score?: { overall_score?: number };
};

const FALLBACK: LeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 84 },
    pipeline_action: "Priority: Pitch AMR fleet for new distribution centers",
    robot_types_needed: ["mobile robots (AMRs)", "warehouse automation"],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Hospitality",
    priority_tier: "HOT",
    score: { overall_score: 79 },
    pipeline_action: "Priority: Lead with overnight cleaning robots — confirm facilities owner",
    robot_types_needed: ["service robots", "cleaning robots"],
  },
  {
    id: -3,
    company_name: "FedEx Supply Chain",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 88 },
    pipeline_action: "Priority: Sortation + AMR pilot for new DC rollout",
    robot_types_needed: ["sortation robots", "mobile robots (AMRs)"],
  },
];

const industryIcon: Record<string, React.ElementType> = {
  hospitality: Hotel,
  logistics: Truck,
  healthcare: Heart,
  manufacturing: Factory,
  food: Utensils,
};

function iconForIndustry(industry?: string) {
  const key = (industry || "").toLowerCase();
  for (const [k, Icon] of Object.entries(industryIcon)) {
    if (key.includes(k)) return Icon;
  }
  return Building2;
}

function scoreOf(lead: LeadRow): number | string {
  const v = lead.score?.overall_score;
  return v != null ? Math.round(Number(v)) : "—";
}

/**
 * Deep link a real, live lead into its value proof (pitch + outreach draft) on
 * /pipeline. Fallback/demo rows (negative ids or preview mode) stay non-clickable
 * so we never route a visitor to a lead the pipeline can't load. This is the
 * value-first browse → proof step: the strongest evidence on home becomes the
 * fastest path to the intent peak that gates signup.
 */
function leadHref(lead: LeadRow, live: boolean): string | null {
  if (!live || !Number.isFinite(lead.id) || lead.id <= 0) return null;
  return `/pipeline?lead=${lead.id}`;
}

type Props = {
  hotCount: number | null;
  totalCount: number | null;
};

export default function MarketingHeroPipeline({ hotCount, totalCount }: Props) {
  const [pool, setPool] = useState<LeadRow[]>(FALLBACK);
  const [visible, setVisible] = useState<LeadRow[]>(FALLBACK.slice(0, 3));
  const [live, setLive] = useState(false);
  const poolCursor = useRef(3);
  const rotateSlot = useRef(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const { leads, live: isLive } = await fetchHomepageLeadPool(FALLBACK);
      if (cancelled) return;
      setPool(leads);
      setVisible(leads.slice(0, 3));
      poolCursor.current = Math.min(3, leads.length);
      setLive(isLive);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (pool.length <= 3) return;
    const timer = window.setInterval(() => {
      setVisible((current) => {
        const next = [...current];
        const pick = pool[poolCursor.current % pool.length];
        poolCursor.current = (poolCursor.current + 1) % pool.length;
        const slot = rotateSlot.current % 3;
        rotateSlot.current += 1;
        next[slot] = pick;
        return next;
      });
    }, 5600);
    return () => window.clearInterval(timer);
  }, [pool]);

  const hotLabel = formatStat(hotCount, "319");
  const totalLabel = formatStat(totalCount, "3,957");
  const rows = visible.slice(0, 3);

  return (
    <div className="hero-widget-glow home-hero-panel">
      <div className="home-hero-panel-header flex items-center justify-between px-4 py-3 sm:px-5 sm:py-4">
        <div className="flex items-center gap-2">
          <LiveDot />
          <span className="font-display text-sm font-semibold text-slate-100">Live pipeline</span>
        </div>
        <span className="rounded-full border border-amber-300/60 bg-amber-400/18 px-2.5 py-0.5 font-mono-data text-xs font-bold text-amber-200">
          {hotLabel} HOT
        </span>
      </div>

      <div>
        {rows.map((lead, rowIndex) => {
          const Icon = iconForIndustry(lead.industry);
          const tier = (lead.priority_tier || "WARM").toUpperCase();
          const href = leadHref(lead, live);
          const rowClass = `home-hero-panel-row flex items-start gap-3 px-4 py-3 sm:gap-4 sm:px-5 sm:py-4 ${
            rowIndex === 2 ? "hidden sm:flex" : ""
          }`;
          const body = (
            <>
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-slate-800/70 shadow-sm">
                <Icon size={16} className="text-sky-300" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="truncate font-display text-sm font-semibold text-slate-100">
                    {lead.company_name}
                  </span>
                  <HeatBadge heat={tier} onDark />
                </div>
                <PipelineLeadActionMeta lead={lead} variant="hero" />
                {href && (
                  <span className="mt-1 inline-flex items-center gap-1 text-[11px] font-semibold text-sky-300 opacity-0 transition-opacity group-hover:opacity-100">
                    See the pitch + outreach draft <ArrowRight size={11} />
                  </span>
                )}
              </div>
              <div className="shrink-0 text-right">
                <div className="score-number text-2xl leading-none text-emerald-400">{scoreOf(lead)}</div>
                <div className="mt-0.5 font-mono-data text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {live ? "live" : "demo"}
                </div>
              </div>
            </>
          );
          if (!href) {
            return (
              <div key={`${lead.id}-${rowIndex}`} className={rowClass}>
                {body}
              </div>
            );
          }
          return (
            <Link
              key={`${lead.id}-${rowIndex}`}
              href={href}
              aria-label={`Open ${lead.company_name || "this lead"} — pitch action and outreach draft`}
              className={`group cursor-pointer transition-colors hover:bg-sky-500/10 ${rowClass}`}
            >
              {body}
            </Link>
          );
        })}
      </div>

      <div className="home-hero-panel-footer flex items-center justify-between px-4 py-2.5 sm:px-5 sm:py-3">
        <span className="font-mono-data text-[10px] text-slate-400 sm:text-xs">
          Showing {rows.length} of {totalLabel} active opportunities
          {!live && <span className="text-slate-400"> · preview</span>}
        </span>
        <Link
          href="/pipeline"
          className="flex items-center gap-1 rounded-lg bg-sky-400/10 px-2 py-1 text-xs font-semibold text-sky-200 hover:bg-sky-400/20"
        >
          View all <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
}
