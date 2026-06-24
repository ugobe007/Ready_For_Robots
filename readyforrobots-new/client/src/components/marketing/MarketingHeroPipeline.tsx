/**
 * Hero live pipeline widget — emerald redesign skin, /api/leads/homepage data.
 */
import { useEffect, useRef, useState } from "react";
import { ArrowRight, Building2, Factory, Heart, Hotel, Truck, Utensils } from "lucide-react";
import { Link } from "wouter";
import { fetchHomepageLeadPool } from "@/lib/homepageLeads";
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
  { id: -1, company_name: "Lineage Logistics", industry: "Logistics", priority_tier: "HOT", score: { overall_score: 84 }, core_need: "Labor shortage + 2 new DCs" },
  { id: -2, company_name: "Hyatt Hotels Corp.", industry: "Hospitality", priority_tier: "HOT", score: { overall_score: 79 }, core_need: "Staffing crisis + expansion" },
  { id: -3, company_name: "FedEx Supply Chain", industry: "Logistics", priority_tier: "HOT", score: { overall_score: 88 }, core_need: "New distribution centers announced" },
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
  const summary = leadPreviewSentences(lead.share_summary, 1, 120);
  if (summary) return summary;
  const need = cleanAndClampText(lead.core_need, 90);
  if (need) return need;
  return cleanAndClampText(lead.signals?.[0]?.display_text, 90) || lead.industry || "Automation-ready signal";
}

function scoreOf(lead: LeadRow): number | string {
  const v = lead.score?.overall_score;
  return v != null ? Math.round(Number(v)) : "—";
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
    }, 2800);
    return () => window.clearInterval(timer);
  }, [pool]);

  const hotLabel = formatStat(hotCount, "319");
  const totalLabel = formatStat(totalCount, "3,957");
  const rows = visible.slice(0, 3);

  return (
    <div className="hero-widget-glow bg-slate-900 rounded-2xl overflow-hidden border border-white/10">
      <div className="flex items-center justify-between px-4 sm:px-5 py-3 sm:py-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <LiveDot />
          <span className="text-white font-semibold text-sm font-display">LIVE PIPELINE</span>
        </div>
        <span className="font-mono-data text-xs text-emerald-400 font-semibold">{hotLabel} HOT</span>
      </div>

      <div>
        {rows.map((lead, rowIndex) => {
          const Icon = iconForIndustry(lead.industry);
          const tier = (lead.priority_tier || "WARM").toUpperCase();
          return (
            <div
              key={`${lead.id}-${rowIndex}`}
              className={`flex items-center gap-3 sm:gap-4 px-4 sm:px-5 py-3 sm:py-4 border-b border-white/10 last:border-0 hover:bg-white/5 transition-all duration-500 ${
                rowIndex === 2 ? "hidden sm:flex" : ""
              }`}
            >
              <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                <Icon size={16} className="text-slate-300" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-white font-semibold text-sm truncate font-display">
                    {lead.company_name}
                  </span>
                  <HeatBadge heat={tier} />
                </div>
                <p className="text-slate-400 text-xs truncate">{signalLine(lead)}</p>
              </div>
              <div className="flex-shrink-0 text-right">
                <div className="score-number text-2xl leading-none text-emerald-400">{scoreOf(lead)}</div>
                <div className="text-slate-500 text-xs mt-0.5 font-mono-data">{live ? "live" : "demo"}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="px-4 sm:px-5 py-2.5 sm:py-3 border-t border-white/10 flex items-center justify-between">
        <span className="text-slate-400 text-[10px] sm:text-xs font-mono-data">
          Showing {rows.length} of {totalLabel} active opportunities
          {!live && <span className="text-slate-500"> · preview</span>}
        </span>
        <Link href="/pipeline" className="text-emerald-400 text-xs font-semibold hover:text-emerald-300 flex items-center gap-1">
          View all <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
}
