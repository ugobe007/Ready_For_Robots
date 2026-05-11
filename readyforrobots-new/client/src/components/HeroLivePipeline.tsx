/**
 * Hero right column — live spotlight leads (same API as readyforrobots_new_web),
 * staggered reveal animation, expandable rows. Dark theme to match Home.
 */
import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Link } from "wouter";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanAndClampText } from "@/lib/text";
export type HomepageLeadRow = {
  id: number;
  company_name?: string;
  industry?: string;
  priority_tier?: string;
  core_need?: string | null;
  signals?: { display_text?: string }[];
  score?: { overall_score?: number };
};

const STATIC_FALLBACK: HomepageLeadRow[] = [
  {
    id: -1,
    company_name: "Lineage Logistics",
    industry: "Logistics",
    priority_tier: "HOT",
    score: { overall_score: 84 },
    core_need: "Labor shortage + 2 new DCs — automation window opening",
    signals: [],
  },
  {
    id: -2,
    company_name: "Hyatt Hotels Corp.",
    industry: "Hospitality",
    priority_tier: "HOT",
    score: { overall_score: 79 },
    core_need: "Staffing crisis + expansion — overnight robotics fit",
    signals: [],
  },
  {
    id: -3,
    company_name: "Pepsi Beverage Co.",
    industry: "Food Processing",
    priority_tier: "HOT",
    score: { overall_score: 71 },
    core_need: "OSHA citation + CapEx signal on packaging lines",
    signals: [],
  },
];

function heroSubline(lead: HomepageLeadRow): string {
  const need = cleanAndClampText(lead.core_need, 72);
  if (need) return need;
  const t = cleanAndClampText(lead.signals?.[0]?.display_text, 72);
  if (t) return t;
  return lead.industry || "";
}

function scoreDisplay(lead: HomepageLeadRow): string | number {
  const v = lead.score && typeof lead.score === "object" ? lead.score.overall_score : undefined;
  return v != null ? Math.round(Number(v)) : "—";
}

const tierStyle: Record<string, { color: string; bg: string; border: string }> = {
  HOT: { color: "#f87171", bg: "rgba(248,113,113,0.12)", border: "rgba(248,113,113,0.28)" },
  WARM: { color: "#a78bfa", bg: "rgba(167,139,250,0.10)", border: "rgba(167,139,250,0.25)" },
};

export default function HeroLivePipeline() {
  const [visibleRows, setVisibleRows] = useState(0);
  const [apiLeads, setApiLeads] = useState<HomepageLeadRow[] | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const rows = useMemo(() => (apiLeads && apiLeads.length ? apiLeads : STATIC_FALLBACK), [apiLeads]);

  useEffect(() => {
    setVisibleRows(0);
  }, [rows]);

  useEffect(() => {
    const t = window.setInterval(() => {
      setVisibleRows((v) => (v < rows.length ? v + 1 : v));
    }, 420);
    return () => window.clearInterval(t);
  }, [rows.length]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const base = getApiBase();
        const r = await fetch(`${base}/api/leads/homepage?cb=${Date.now()}`, liveFetchInit());
        if (!r.ok || cancelled) return;
        const raw = await r.text();
        if (raw.trimStart().startsWith("<") || cancelled) return;
        const data = JSON.parse(raw) as { hotLeads?: HomepageLeadRow[] };
        const hl = data.hotLeads;
        if (Array.isArray(hl) && hl.length && !cancelled) {
          setApiLeads(hl.slice(0, 3));
        }
      } catch {
        /* keep fallback */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="relative w-full">
      <div
        className="rounded-2xl border border-white/10 overflow-hidden shadow-2xl shadow-black/50"
        style={{
          background: "linear-gradient(165deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)",
          boxShadow: "0 24px 64px -12px rgba(124,58,237,0.15), 0 0 0 1px rgba(255,255,255,0.06) inset",
        }}
      >
        <div
          className="px-5 py-4 flex items-center justify-between border-b border-white/8"
          style={{ background: "rgba(124,58,237,0.12)" }}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <img src="/logo-r.png" alt="" className="h-8 w-8 shrink-0 object-contain opacity-95" width={32} height={32} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white truncate" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                Live pipeline
              </p>
              <p className="rfr-scout-wordmark text-[9px] text-violet-200/80 truncate">SCOUT spotlight</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span
              className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-full border border-emerald-500/30"
              style={{ color: "#6ee7b7", background: "rgba(52,211,153,0.1)" }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </span>
            <span className="text-[10px] font-mono text-white/30" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {apiLeads ? "API" : "Demo"}
            </span>
          </div>
        </div>

        <div className="divide-y divide-white/8">
          {rows.map((lead, i) => {
            const open = expandedId === lead.id;
            const tier = (lead.priority_tier || "HOT").toUpperCase();
            const st = tierStyle[tier] || tierStyle.HOT;
            const visible = i < visibleRows;

            return (
              <div
                key={lead.id}
                className="transition-all duration-500 ease-out"
                style={{
                  opacity: visible ? 1 : 0,
                  transform: visible ? "translateY(0)" : "translateY(10px)",
                }}
              >
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left hover:bg-white/4 transition-colors"
                  onClick={() => setExpandedId(open ? null : lead.id)}
                  aria-expanded={open}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold text-white shrink-0"
                      style={{
                        background:
                          i === 0 ? "#7c3aed" : i === 1 ? "rgba(139,92,246,0.85)" : "rgba(255,176,0,0.85)",
                      }}
                    >
                      {(lead.company_name || "?").charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">{lead.company_name}</p>
                      <p className="text-xs text-white/40 truncate">{heroSubline(lead)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className="hidden sm:inline text-[9px] font-bold px-2 py-0.5 rounded-full border"
                      style={{ color: st.color, background: st.bg, borderColor: st.border }}
                    >
                      {tier}
                    </span>
                    <span
                      className="font-mono text-base font-bold tabular-nums"
                      style={{ color: "#c4b5fd", fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {scoreDisplay(lead)}
                    </span>
                    {open ? (
                      <ChevronDown className="h-4 w-4 text-white/30 shrink-0" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-white/30 shrink-0" />
                    )}
                  </div>
                </button>
                {open && (
                  <div className="px-4 pb-4 border-t border-white/6 bg-violet-950/40">
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-1.5 rfr-scout-wordmark text-violet-300/90 pt-3">
                      Why SCOUT surfaced this
                    </p>
                    <p className="text-sm text-white/60 leading-relaxed">{heroSubline(lead)}</p>
                    {lead.id > 0 && (
                      <Link
                        href="/pipeline"
                        className="inline-flex items-center gap-1 mt-3 text-xs font-semibold text-violet-300 hover:text-violet-200"
                      >
                        Open in pipeline →
                      </Link>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div
          className="px-4 py-3 border-t border-white/8 flex items-center gap-3"
          style={{ background: "linear-gradient(90deg, rgba(124,58,237,0.08), rgba(52,211,153,0.06))" }}
        >
          <div className="h-8 w-8 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center shrink-0 text-sm" aria-hidden>
            📈
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-semibold text-white/90 leading-tight">New signal detected</p>
            <p className="text-[11px] text-white/40 truncate">&quot;Opening 2 new DCs next Q&quot; — logistics</p>
          </div>
        </div>

        <div className="px-4 py-3 border-t border-white/6" style={{ background: "rgba(124,58,237,0.08)" }}>
          <Link href="/pipeline" className="text-xs font-semibold flex items-center gap-1 text-violet-200 hover:text-white transition-colors">
            View full pipeline
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
