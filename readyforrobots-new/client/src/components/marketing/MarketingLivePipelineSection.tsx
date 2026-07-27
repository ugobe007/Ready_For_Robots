/**
 * Full-width live pipeline table — emerald redesign, /api/leads/homepage data.
 */
import { useEffect, useRef, useState } from "react";
import { ArrowRight, Building2, Factory, Heart, Hotel, Truck, Utensils, Zap } from "lucide-react";
import { Link } from "wouter";
import { fetchHomepageLeadPool } from "@/lib/homepageLeads";
import PipelineLeadActionMeta from "@/components/pipeline/PipelineLeadActionMeta";
import { HeatBadge, LiveDot } from "@/components/marketing/primitives";
import LeadShareBar from "@/components/LeadShareBar";
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
    company_name: "Silver Peak Hospitality",
    industry: "Hospitality",
    priority_tier: "HOT",
    score: { overall_score: 94 },
    pipeline_action: "Priority: Pitch overnight cleaning robots — 43% housekeeping vacancy",
    robot_types_needed: ["cleaning robots", "service robots"],
  },
  {
    id: -2,
    company_name: "DesertLine Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 88 },
    pipeline_action: "Priority: AMR fleet for 2 new distribution centers",
    robot_types_needed: ["mobile robots (AMRs)", "warehouse automation"],
  },
  {
    id: -3,
    company_name: "Apex Food Processing",
    industry: "Food Processing",
    priority_tier: "WARM",
    score: { overall_score: 76 },
    pipeline_action: "Priority: Line 4 packaging automation after OSHA citation",
    robot_types_needed: ["pick-and-place robots", "packaging automation"],
  },
  {
    id: -4,
    company_name: "NovaCare Health Systems",
    industry: "Healthcare",
    priority_tier: "WARM",
    score: { overall_score: 71 },
    pipeline_action: "Priority: AMR delivery for pharmacy expansion",
    robot_types_needed: ["mobile robots (AMRs)", "service robots"],
  },
  {
    id: -5,
    company_name: "Summit Manufacturing",
    industry: "Manufacturing",
    priority_tier: "WARM",
    score: { overall_score: 65 },
    pipeline_action: "Priority: CapEx window — pitch palletizing for new line",
    robot_types_needed: ["palletizing robots", "industrial arms"],
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

type Props = {
  hotCount: number | null;
  totalCount: number | null;
};

export default function MarketingLivePipelineSection({ hotCount, totalCount }: Props) {
  const [pool, setPool] = useState<LeadRow[]>(FALLBACK);
  const [rows, setRows] = useState<LeadRow[]>(FALLBACK.slice(0, 5));
  const [live, setLive] = useState(false);
  const [resolvedTotal, setResolvedTotal] = useState<number | null>(null);
  const [resolvedHot, setResolvedHot] = useState<number | null>(null);
  const poolCursor = useRef(5);
  const rotateSlot = useRef(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const { leads, live: isLive, summary } = await fetchHomepageLeadPool(FALLBACK);
      if (cancelled) return;
      setPool(leads);
      setRows(leads.slice(0, 5));
      poolCursor.current = Math.min(5, leads.length);
      setLive(isLive);
      if (summary) {
        if (typeof summary.total === "number") setResolvedTotal(summary.total);
        if (typeof summary.hot === "number") setResolvedHot(summary.hot);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (pool.length <= 5) return;
    const timer = window.setInterval(() => {
      setRows((current) => {
        const next = [...current];
        const pick = pool[poolCursor.current % pool.length];
        poolCursor.current = (poolCursor.current + 1) % pool.length;
        const slot = rotateSlot.current % 5;
        rotateSlot.current += 1;
        next[slot] = pick;
        return next;
      });
    }, 3200);
    return () => window.clearInterval(timer);
  }, [pool]);

  const hotLabel = formatStat(resolvedHot ?? hotCount, "319");
  const totalLabel = formatStat(resolvedTotal ?? totalCount, "3,957");

  return (
    <section id="live-pipeline" className="py-20 bg-slate-900 scroll-mt-24">
      <div className="container">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-10 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <LiveDot />
              <span className="text-sky-300 text-xs font-mono-data font-semibold uppercase tracking-widest">
                Live Pipeline
              </span>
              {live && (
                <span className="rounded-full border border-amber-400/35 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
                  Live data
                </span>
              )}
            </div>
            <h2 className="font-display text-4xl font-bold text-white tracking-tight">
              Every lead shows what to pitch — not just who to call.
            </h2>
            <p className="mt-2 max-w-xl text-sm text-slate-300">
              Pipeline actions and robot categories on every row. No company search — a running sales funnel for robot OEMs.
            </p>
          </div>
          <div className="text-slate-400 text-sm font-mono-data">
            Live pipeline · <span className="text-amber-300 font-bold">{hotLabel} hot leads</span>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-2xl border border-white/10 overflow-hidden">
          <div className="grid grid-cols-12 px-6 py-3 border-b border-white/10 text-slate-400 text-xs font-mono-data uppercase tracking-widest">
            <div className="col-span-3">Company</div>
            <div className="col-span-5 hidden md:block">Next action · Robot types</div>
            <div className="col-span-2 text-center">Score</div>
            <div className="col-span-2 text-right">Status</div>
          </div>

          {rows.map((lead) => {
            const Icon = iconForIndustry(lead.industry);
            const tier = (lead.priority_tier || "WARM").toUpperCase();
            const score = lead.score?.overall_score != null ? Math.round(Number(lead.score.overall_score)) : "—";
            const href = lead.id > 0 ? `/pipeline?lead=${lead.id}` : "/pipeline";
            return (
              <Link
                key={`${lead.id}-${lead.company_name}`}
                href={href}
                className="grid grid-cols-12 px-6 py-4 border-b border-white/5 last:border-0 hover:bg-white/5 transition-all duration-500 items-center group"
              >
                <div className="col-span-3 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                    <Icon size={16} className="text-slate-300" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-white font-semibold text-sm font-display group-hover:text-emerald-300 transition-colors truncate">
                      {lead.company_name}
                    </div>
                    <div className="text-slate-400 text-xs font-mono-data uppercase truncate">{lead.industry}</div>
                  </div>
                </div>
                <div className="col-span-5 hidden md:block pr-4">
                  <PipelineLeadActionMeta lead={lead} variant="dark" />
                </div>
                <div className="col-span-2 text-center">
                  <span className="score-number text-2xl">{score}</span>
                </div>
                <div className="col-span-2 flex items-center justify-end gap-2">
                  <LeadShareBar
                    compact
                    variant="dark"
                    lead={{
                      id: lead.id,
                      company_name: lead.company_name,
                      priority_tier: tier,
                      share_summary: lead.share_summary,
                      share_blurb: lead.core_need,
                      pipeline_action: lead.pipeline_action,
                      robot_types_needed: lead.robot_types_needed,
                    }}
                  />
                  <HeatBadge heat={tier} />
                </div>
              </Link>
            );
          })}
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between mt-6 gap-4">
          <p className="text-slate-400 text-sm font-mono-data">
            Showing {rows.length} of <span className="text-white font-bold">{totalLabel}</span> active opportunities
            {!live && <span className="text-slate-500"> · sample preview</span>}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/pipeline"
              className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl transition-all duration-150 active:scale-[0.97] text-sm"
            >
              Open full pipeline
              <ArrowRight size={14} />
            </Link>
            <Link
              href="/compare"
              className="inline-flex items-center gap-2 px-5 py-3 text-slate-200 hover:text-white font-semibold rounded-xl border border-sky-300/30 hover:border-sky-300/60 transition-all text-sm"
            >
              vs data tools
            </Link>
            <Link
              href="/results?url="
              className="inline-flex items-center gap-2 px-5 py-3 text-sky-300 hover:text-white font-semibold rounded-xl border border-sky-300/30 hover:border-sky-300/60 transition-all text-sm"
            >
              <Zap size={16} />
              URL scan
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
