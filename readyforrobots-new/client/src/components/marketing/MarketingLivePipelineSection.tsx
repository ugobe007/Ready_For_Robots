/**
 * Full-width live pipeline table — emerald redesign, live /api/leads data.
 */
import { useEffect, useState } from "react";
import { ArrowRight, Building2, Factory, Heart, Hotel, Truck, Utensils, Zap } from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { dedupeHomepageLeads } from "@/lib/homepageLeads";
import { cleanAndClampText, leadPreviewSentences } from "@/lib/text";
import { HeatBadge, LiveDot } from "@/components/marketing/primitives";
import { formatStat } from "@/hooks/usePipelineStats";

type LeadRow = {
  id: number;
  company_name?: string;
  industry?: string;
  priority_tier?: string;
  core_need?: string | null;
  share_summary?: string | null;
  signals?: { display_text?: string }[];
  score?: { overall_score?: number };
};

const FALLBACK: LeadRow[] = [
  { id: -1, company_name: "Silver Peak Hospitality", industry: "Hospitality", priority_tier: "HOT", score: { overall_score: 94 }, core_need: "Housekeeping vacancy rate hit 43%" },
  { id: -2, company_name: "DesertLine Logistics", industry: "Logistics", priority_tier: "HOT", score: { overall_score: 88 }, core_need: "Announced 2 new distribution centers" },
  { id: -3, company_name: "Apex Food Processing", industry: "Food Processing", priority_tier: "WARM", score: { overall_score: 76 }, core_need: "OSHA citation on line 4" },
  { id: -4, company_name: "NovaCare Health Systems", industry: "Healthcare", priority_tier: "WARM", score: { overall_score: 71 }, core_need: "Hiring 12 pharmacy techs" },
  { id: -5, company_name: "Summit Manufacturing", industry: "Manufacturing", priority_tier: "WARM", score: { overall_score: 65 }, core_need: "CapEx budget increased 28% YoY" },
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

function signalLine(lead: LeadRow): string {
  const summary = leadPreviewSentences(lead.share_summary, 1, 140);
  if (summary) return summary;
  const need = cleanAndClampText(lead.core_need, 100);
  if (need) return need;
  return cleanAndClampText(lead.signals?.[0]?.display_text, 100) || lead.industry || "";
}

type Props = {
  hotCount: number | null;
  totalCount: number | null;
};

export default function MarketingLivePipelineSection({ hotCount, totalCount }: Props) {
  const [rows, setRows] = useState<LeadRow[]>(FALLBACK);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${getApiBase()}/api/leads?limit=50&sort=score&exclude_junk=true`,
          liveFetchInit(),
        );
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as { leads?: LeadRow[] };
        const raw = Array.isArray(data.leads) ? data.leads : [];
        const mapped = raw
          .filter((r) => r.company_name && r.id)
          .slice(0, 5) as LeadRow[];
        if (mapped.length && !cancelled) {
          setRows(dedupeHomepageLeads(mapped).slice(0, 5) as LeadRow[]);
        }
      } catch {
        /* fallback */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const hotLabel = formatStat(hotCount, "319");
  const totalLabel = formatStat(totalCount, "3,957");

  return (
    <section className="py-20 bg-slate-900">
      <div className="container">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-10 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <LiveDot />
              <span className="text-emerald-400 text-xs font-mono-data font-semibold uppercase tracking-widest">
                Live Pipeline
              </span>
            </div>
            <h2 className="font-display text-4xl font-bold text-white tracking-tight">
              Your pipeline is already moving.
            </h2>
          </div>
          <div className="text-slate-400 text-sm font-mono-data">
            Live pipeline · <span className="text-emerald-400 font-bold">{hotLabel} hot leads</span>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-2xl border border-white/10 overflow-hidden">
          <div className="grid grid-cols-12 px-6 py-3 border-b border-white/10 text-slate-500 text-xs font-mono-data uppercase tracking-widest">
            <div className="col-span-4">Company</div>
            <div className="col-span-4 hidden md:block">Signal</div>
            <div className="col-span-2 text-center">Score</div>
            <div className="col-span-2 text-right">Status</div>
          </div>

          {rows.map((lead) => {
            const Icon = iconForIndustry(lead.industry);
            const tier = (lead.priority_tier || "WARM").toUpperCase();
            const score = lead.score?.overall_score != null ? Math.round(Number(lead.score.overall_score)) : "—";
            return (
              <div
                key={lead.id}
                className="grid grid-cols-12 px-6 py-4 border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors duration-150 items-center"
              >
                <div className="col-span-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                    <Icon size={16} className="text-slate-300" />
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm font-display">{lead.company_name}</div>
                    <div className="text-slate-500 text-xs font-mono-data uppercase">{lead.industry}</div>
                  </div>
                </div>
                <div className="col-span-4 hidden md:block">
                  <p className="text-slate-400 text-sm truncate pr-4">{signalLine(lead)}</p>
                </div>
                <div className="col-span-2 text-center">
                  <span className="score-number text-2xl text-emerald-400">{score}</span>
                </div>
                <div className="col-span-2 flex items-center justify-end">
                  <HeatBadge heat={tier} />
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between mt-6 gap-4">
          <p className="text-slate-500 text-sm font-mono-data">
            Showing {rows.length} of <span className="text-white font-bold">{totalLabel}</span> active opportunities
          </p>
          <Link
            href="/results?url="
            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-all duration-150 active:scale-[0.97] text-sm"
          >
            <Zap size={16} />
            Activate SIGNAL
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </section>
  );
}
