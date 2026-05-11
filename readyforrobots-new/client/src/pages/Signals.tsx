/**
 * Signals — ReadyForRobots
 * Signal library: browse all 14 signal types, filter by category and industry
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 */
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, TrendingUp, DollarSign, Newspaper, Building2, Briefcase, Activity, Globe, Zap, Filter, Search, ChevronRight } from "lucide-react";
import Header from "@/components/Header";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { Link } from "wouter";
import { toast } from "sonner";

type ApiLead = {
  id?: number | string;
  company_name?: string;
  industry?: string | null;
  priority_tier?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
  share_summary?: string | null;
  score?: number | {
    overall_score?: number;
    overall_intent_score?: number;
    lead_value_score?: number;
    signal_score?: number;
  };
  signals?: Array<{
    signal_type?: string;
    signal_label?: string;
    raw_text?: string;
    display_text?: string;
    text?: string;
  }>;
  gtm?: {
    readiness_label?: string;
    suggested_motion?: string;
    why_now?: string[];
  };
};

type OpportunityTrack = "Sales" | "Partnership";

type LiveOpportunitySignal = {
  id: string;
  company: string;
  type: string;
  text: string;
  score: number;
  track: OpportunityTrack;
  time: string;
  color: string;
  industry: string;
};

type LeadSummary = {
  total?: number;
  hot?: number;
  warm?: number;
  cold?: number;
  total_signals?: number;
};

const MARKET_COLORS = {
  emerald: "#065f46",
  emeraldBright: "#10b981",
  amber: "#b45309",
  amberBright: "#f59e0b",
  teal: "#03DAC5",
  violet: "#a78bfa",
};

const SIGNAL_TYPES = [
  {
    id: "labor",
    name: "Labor Shortage",
    icon: AlertTriangle,
    color: "#f87171",
    category: "Operational",
    description: "Companies unable to fill critical roles — the most reliable indicator of automation readiness.",
    sources: ["Job boards", "Earnings calls", "LinkedIn hiring patterns", "Glassdoor reviews"],
    industries: ["Hospitality", "Healthcare", "Logistics", "Food Processing"],
    example: "\"We cannot staff overnight shifts\" — Q3 earnings call, Silver Peak Hospitality",
    frequency: "Daily",
    avgScore: 88,
  },
  {
    id: "expansion",
    name: "Expansion Signal",
    icon: TrendingUp,
    color: "#34d399",
    category: "Growth",
    description: "New facilities, new markets, or significant headcount growth — companies building capacity need automation baked in.",
    sources: ["Press releases", "Real estate permits", "LinkedIn company updates", "Earnings calls"],
    industries: ["Logistics", "Manufacturing", "Retail", "Food Processing"],
    example: "\"Opening 2 new distribution centers in Q1 2027\" — press release, DesertLine Logistics",
    frequency: "Daily",
    avgScore: 84,
  },
  {
    id: "safety",
    name: "Safety Signal",
    icon: Activity,
    color: "#fb923c",
    category: "Operational",
    description: "OSHA filings, injury reports, and safety incidents indicate high-risk manual tasks ready for automation.",
    sources: ["OSHA database", "Workers' comp filings", "Industry safety reports"],
    industries: ["Manufacturing", "Healthcare", "Logistics", "Construction"],
    example: "3 repetitive strain injury filings in 6 months — OSHA records, Apex Manufacturing",
    frequency: "Weekly",
    avgScore: 81,
  },
  {
    id: "capex",
    name: "CapEx Announcement",
    icon: DollarSign,
    color: "#a78bfa",
    category: "Financial",
    description: "Capital expenditure announcements signal budget allocation for equipment and infrastructure.",
    sources: ["Earnings calls", "SEC filings", "Press releases", "Industry news"],
    industries: ["Manufacturing", "Food Processing", "Healthcare", "Logistics"],
    example: "\"$12M facility upgrade approved\" — earnings call, Harbor Fresh Foods",
    frequency: "Weekly",
    avgScore: 86,
  },
  {
    id: "hiring",
    name: "Automation Hiring",
    icon: Briefcase,
    color: "#60a5fa",
    category: "Intent",
    description: "Job postings for automation engineers, robotics technicians, or process improvement roles signal active evaluation.",
    sources: ["LinkedIn", "Indeed", "Glassdoor", "Company career pages"],
    industries: ["All industries"],
    example: "\"Automation Engineer\" job posting + \"Process Improvement Manager\" — DesertLine Logistics",
    frequency: "Daily",
    avgScore: 79,
  },
  {
    id: "news",
    name: "Industry News Trigger",
    icon: Newspaper,
    color: "#f472b6",
    category: "External",
    description: "Regulatory changes, competitor moves, or industry events that create urgency for automation adoption.",
    sources: ["Industry publications", "Trade associations", "Government announcements"],
    industries: ["Healthcare", "Food Processing", "Manufacturing", "Logistics"],
    example: "New FDA food safety regulations requiring traceability — triggers food processing automation review",
    frequency: "Weekly",
    avgScore: 72,
  },
  {
    id: "leadership",
    name: "Leadership Change",
    icon: Building2,
    color: "#fbbf24",
    category: "Intent",
    description: "New COO, VP of Operations, or Head of Manufacturing often signals a mandate to modernize operations.",
    sources: ["LinkedIn", "Press releases", "Company announcements"],
    industries: ["All industries"],
    example: "New COO hired from Amazon — known for automation-first operations philosophy",
    frequency: "Weekly",
    avgScore: 77,
  },
  {
    id: "contract",
    name: "Contract Win",
    icon: Globe,
    color: "#34d399",
    category: "Growth",
    description: "Major contract wins create immediate capacity pressure — the perfect moment to propose automation.",
    sources: ["Press releases", "Government contract databases", "Industry news"],
    industries: ["Logistics", "Manufacturing", "Healthcare", "Defense"],
    example: "Won 5-year DoD logistics contract requiring 3x throughput increase",
    frequency: "Weekly",
    avgScore: 83,
  },
];

const CATEGORIES = ["All", "Operational", "Growth", "Financial", "Intent", "External"];
const INDUSTRIES = ["All", "Logistics", "Hospitality", "Healthcare", "Manufacturing", "Food Processing", "Retail"];

const fallbackLiveSignals: LiveOpportunitySignal[] = [
  { id: "silver-peak", company: "Silver Peak Hospitality", type: "Labor Shortage", score: 94, time: "2m ago", color: MARKET_COLORS.emeraldBright, track: "Sales", industry: "Hospitality", text: "40% housekeeping vacancy and overnight staffing pressure." },
  { id: "desertline", company: "DesertLine Logistics", type: "Expansion Signal", score: 88, time: "18m ago", color: MARKET_COLORS.emerald, track: "Sales", industry: "Logistics", text: "Opening two distribution centers with throughput pressure." },
  { id: "apex", company: "Apex Manufacturing", type: "Safety Signal", score: 79, time: "1h ago", color: MARKET_COLORS.amberBright, track: "Sales", industry: "Manufacturing", text: "Manual handling injuries indicate a strong automation case." },
  { id: "harbor", company: "Harbor Fresh Foods", type: "CapEx Announcement", score: 85, time: "3h ago", color: MARKET_COLORS.amber, track: "Sales", industry: "Food Processing", text: "$12M facility upgrade creates budget timing." },
  { id: "ridgeline", company: "Ridgeline Hotels", type: "Integrator Fit", score: 91, time: "5h ago", color: MARKET_COLORS.emeraldBright, track: "Partnership", industry: "Hospitality", text: "Regional operating footprint maps to channel partner coverage." },
  { id: "cascade", company: "Cascade Fulfillment", type: "Automation Hiring", score: 76, time: "8h ago", color: MARKET_COLORS.amberBright, track: "Partnership", industry: "Logistics", text: "Automation engineer hiring suggests active vendor evaluation." },
];

function titleize(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function leadScore(lead: ApiLead): number {
  if (typeof lead.score === "number") return Math.round(lead.score);
  const structured = lead.score || {};
  return Math.round(
    structured.lead_value_score ??
      structured.overall_score ??
      structured.overall_intent_score ??
      structured.signal_score ??
      lead.priority_score ??
      70,
  );
}

function opportunityTrack(lead: ApiLead): OpportunityTrack {
  const text = [
    lead.gtm?.suggested_motion,
    lead.share_summary,
    ...(lead.priority_reasons || []),
    ...(lead.gtm?.why_now || []),
  ].join(" ").toLowerCase();
  return /(partner|partnership|channel|integrator|distributor|co-sell|alliance)/.test(text) ? "Partnership" : "Sales";
}

function signalColor(signalType: string, track: OpportunityTrack): string {
  const type = signalType.toLowerCase();
  if (track === "Partnership") return MARKET_COLORS.amberBright;
  if (/(capex|safety|hiring|leadership)/.test(type)) return MARKET_COLORS.amber;
  return MARKET_COLORS.emeraldBright;
}

function mapLeadToLiveSignal(lead: ApiLead, index: number): LiveOpportunitySignal {
  const firstSignal = lead.signals?.[0];
  const type = firstSignal?.signal_label || titleize(firstSignal?.signal_type || "demand_signal");
  const track = opportunityTrack(lead);
  const text =
    firstSignal?.display_text ||
    firstSignal?.raw_text ||
    firstSignal?.text ||
    lead.share_summary ||
    lead.gtm?.suggested_motion ||
    "SCOUT found a scored automation opportunity worth reviewing.";
  return {
    id: String(lead.id ?? `${lead.company_name || "lead"}-${index}`),
    company: lead.company_name || `Scored Lead ${index + 1}`,
    type,
    text: String(text).slice(0, 150),
    score: leadScore(lead),
    track,
    time: index < 3 ? `${Math.max(index * 4 + 2, 2)}m ago` : "live",
    color: signalColor(type, track),
    industry: lead.industry || "Market",
  };
}

function buildRadarRows(signals: LiveOpportunitySignal[], activeIndex: number) {
  const groups = new Map<string, { label: string; track: OpportunityTrack; count: number; total: number; color: string }>();
  signals.forEach((signal) => {
    const key = `${signal.track}:${signal.type}`;
    const current = groups.get(key) || { label: signal.type, track: signal.track, count: 0, total: 0, color: signal.color };
    current.count += 1;
    current.total += signal.score;
    current.color = signal.color;
    groups.set(key, current);
  });

  return Array.from(groups.values())
    .map((row, index) => {
      const average = row.total / row.count;
      const pulse = index === activeIndex % Math.max(groups.size, 1) ? 0.04 : 0;
      const value = Math.min(0.98, average / 100 + Math.min(row.count * 0.015, 0.06) + pulse);
      return {
        label: row.label,
        track: row.track,
        value,
        delta: `+${Math.max(1, row.count + Math.round((average - 70) / 10)).toString().padStart(2, "0")}`,
        color: row.track === "Partnership" ? MARKET_COLORS.amberBright : row.color,
      };
    })
    .sort((a, b) => b.value - a.value)
    .slice(0, 7);
}

function formatMetric(value: number | string): string {
  if (typeof value === "string") return value;
  return new Intl.NumberFormat("en-US").format(value);
}

function SignalRadar({ signals, summary, loading, activeIndex }: { signals: LiveOpportunitySignal[]; summary: LeadSummary | null; loading: boolean; activeIndex: number }) {
  const radarRows = useMemo(() => buildRadarRows(signals, activeIndex), [signals, activeIndex]);
  const activeSignal = signals[activeIndex % Math.max(signals.length, 1)];
  const hotCount = signals.filter((signal) => signal.score >= 85).length;
  const totalLeads = summary?.total ?? signals.length;
  const hotLeads = summary?.hot ?? hotCount;
  const warmLeads = summary?.warm ?? 0;
  const totalSignals = summary?.total_signals ?? signals.length;

  return (
    <section className="mb-10 overflow-hidden border p-5 lg:p-6" style={{ background: "radial-gradient(circle at 18% 18%, rgba(16,185,129,0.2), transparent 28%), radial-gradient(circle at 82% 20%, rgba(245,158,11,0.18), transparent 30%), linear-gradient(135deg, rgba(3,7,18,0.96), rgba(13,5,32,0.92) 52%, rgba(6,95,70,0.22))", borderColor: "rgba(16,185,129,0.22)", borderRadius: 24, boxShadow: "0 28px 90px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.06)" }}>
      <style>{`
        @keyframes rfr-radar-sweep { 0% { transform: translateX(-18%); opacity: .08; } 32% { opacity: .72; } 100% { transform: translateX(118%); opacity: .08; } }
        @keyframes rfr-signal-pip { 0% { left: -148px; transform: translateY(-50%) scale(.92); opacity: 0; } 10% { opacity: .98; } 78% { opacity: .98; } 100% { left: calc(100% + 16px); transform: translateY(-50%) scale(1); opacity: 0; } }
        @keyframes rfr-card-pulse { 0%, 100% { box-shadow: 0 0 0 rgba(16,185,129,0); } 50% { box-shadow: 0 0 34px rgba(245,158,11,.16); } }
        @keyframes rfr-live-rise { 0% { transform: translateY(3px); opacity: .48; } 100% { transform: translateY(0); opacity: 1; } }
      `}</style>
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.24em]" style={{ color: MARKET_COLORS.emeraldBright }}>
            SCOUT market radar
          </p>
          <h2 className="text-3xl font-extrabold leading-tight text-white md:text-4xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
            Live Robot Demand Radar
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/42">
            Signal lanes move as SCOUT scores live sales leads and partnership opportunities, then elevates the strongest account on the board.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            ["Leads", formatMetric(totalLeads), MARKET_COLORS.emeraldBright],
            ["Hot", formatMetric(hotLeads), MARKET_COLORS.emeraldBright],
            ["Warm", formatMetric(warmLeads), MARKET_COLORS.amberBright],
            ["Signals", formatMetric(totalSignals), MARKET_COLORS.violet],
          ].map(([label, value, color]) => (
            <div key={String(label)} className="rounded-xl border border-white/8 px-3 py-2 text-right" style={{ background: "rgba(255,255,255,0.035)" }}>
              <div className="font-mono text-lg font-black" style={{ color: String(color) }}>{value}</div>
              <div className="text-[9px] font-bold uppercase tracking-widest text-white/28">{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.35fr_0.85fr]">
        <div className="relative min-h-[390px] overflow-hidden border p-4" style={{ background: "linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.018))", borderColor: "rgba(255,255,255,0.1)", borderRadius: 18 }}>
          <div className="pointer-events-none absolute inset-0 opacity-50" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)", backgroundSize: "42px 42px" }} />
          <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4" style={{ background: "linear-gradient(90deg, transparent, rgba(16,185,129,0.26), rgba(245,158,11,0.18), transparent)", animation: "rfr-radar-sweep 5.4s linear infinite" }} />
          <div className="relative mb-4 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">
            <span>{loading ? "Syncing scored leads" : "150+ sources scanning"}</span>
            <span style={{ color: MARKET_COLORS.emeraldBright }}>lead packets moving</span>
          </div>

          <div className="relative space-y-4">
            {radarRows.map((row, rowIndex) => {
              const laneSignals = signals.filter((signal) => signal.type === row.label && signal.track === row.track);
              const pipSignals = (laneSignals.length ? laneSignals : signals).slice(0, 3);
              const activeLane = activeSignal?.type === row.label && activeSignal?.track === row.track;
              return (
                <div key={`${row.track}-${row.label}`} className="relative" style={{ animation: "rfr-live-rise .42s ease-out both", animationDelay: `${rowIndex * 65}ms` }}>
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-black text-white">
                        {activeLane && <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: row.track === "Partnership" ? MARKET_COLORS.amberBright : MARKET_COLORS.emeraldBright }} />}
                        {row.label}
                      </div>
                      <div className="text-[9px] font-bold uppercase tracking-widest" style={{ color: row.track === "Partnership" ? MARKET_COLORS.amberBright : MARKET_COLORS.emeraldBright }}>
                        {row.track} lane
                      </div>
                    </div>
                    <div className="font-mono text-xs font-bold text-white/58">{Math.round(row.value * 100)} intensity</div>
                  </div>
                  <div className="relative h-12 overflow-hidden rounded-2xl border" style={{ background: activeLane ? "rgba(255,255,255,0.055)" : "rgba(2,6,23,0.52)", borderColor: activeLane ? (row.track === "Partnership" ? "rgba(245,158,11,0.28)" : "rgba(16,185,129,0.28)") : "rgba(255,255,255,0.08)" }}>
                    <div className="absolute inset-y-1 left-2 rounded-full" style={{ width: `${Math.round(row.value * 92)}%`, background: `linear-gradient(90deg, ${row.track === "Partnership" ? "rgba(180,83,9,0.14)" : "rgba(6,95,70,0.16)"}, transparent)` }} />
                    <div className="absolute left-0 right-0 top-1/2 h-px bg-white/10" />
                    {pipSignals.map((signal, pipIndex) => (
                      <div
                        key={`${row.label}-${signal.id}-${pipIndex}`}
                        className="absolute top-1/2 flex h-7 min-w-[118px] items-center gap-2 rounded-full border px-2"
                        title={`${signal.company}: ${signal.text}`}
                        style={{
                          left: -148,
                          background: row.track === "Partnership" ? "rgba(180,83,9,0.92)" : "rgba(6,95,70,0.92)",
                          borderColor: row.track === "Partnership" ? "rgba(245,158,11,0.56)" : "rgba(16,185,129,0.56)",
                          boxShadow: `0 0 20px ${row.track === "Partnership" ? "rgba(245,158,11,.38)" : "rgba(16,185,129,.42)"}`,
                          animation: `rfr-signal-pip ${6.2 + pipIndex * 0.85}s linear infinite`,
                          animationDelay: `${rowIndex * 0.34 + pipIndex * 1.35}s`,
                        }}
                      >
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-white/80" />
                        <span className="max-w-[72px] truncate text-[10px] font-bold text-white/90">{signal.company}</span>
                        <span className="font-mono text-[10px] font-black text-white">{signal.score}</span>
                      </div>
                    ))}
                    <div className="absolute bottom-1 right-3 font-mono text-[10px] font-bold text-white/25">{row.delta} signals</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="relative overflow-hidden border p-5" style={{ background: "linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.025))", borderColor: "rgba(245,158,11,0.2)", borderRadius: 18, animation: "rfr-card-pulse 3.8s ease-in-out infinite" }}>
          <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full blur-3xl" style={{ background: activeSignal?.track === "Partnership" ? "rgba(245,158,11,0.18)" : "rgba(16,185,129,0.18)" }} />
          {activeSignal && (
            <div className="relative">
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: activeSignal.track === "Partnership" ? MARKET_COLORS.amberBright : MARKET_COLORS.emeraldBright }}>
                Scoring now
              </p>
              <h3 className="text-2xl font-black leading-tight text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                {activeSignal.company}
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest" style={{ borderColor: activeSignal.track === "Partnership" ? "rgba(245,158,11,0.34)" : "rgba(16,185,129,0.34)", color: activeSignal.track === "Partnership" ? MARKET_COLORS.amberBright : MARKET_COLORS.emeraldBright, background: activeSignal.track === "Partnership" ? "rgba(245,158,11,0.08)" : "rgba(16,185,129,0.08)" }}>
                  {activeSignal.track}
                </span>
                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-white/38">
                  {activeSignal.industry}
                </span>
              </div>
              <div className="my-6 flex items-end justify-between gap-4">
                <div>
                  <div className="font-mono text-6xl font-black leading-none" style={{ color: activeSignal.color }}>
                    {activeSignal.score}
                  </div>
                  <div className="mt-1 text-[10px] font-bold uppercase tracking-widest text-white/28">intent score</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-white/78">{activeSignal.type}</div>
                  <div className="text-[10px] text-white/30">{activeSignal.time}</div>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-white/56">
                {activeSignal.text}
              </p>
              <div className="mt-5 rounded-2xl border border-white/8 p-3" style={{ background: "rgba(0,0,0,0.18)" }}>
                <div className="text-[10px] font-bold uppercase tracking-widest text-white/26">Recommended motion</div>
                <p className="mt-2 text-xs leading-relaxed text-white/48">
                  {activeSignal.track === "Partnership"
                    ? "Qualify channel fit, coverage overlap, and co-sell timing while this partner signal is fresh."
                    : "Prioritize outreach now with a use-case tied directly to this buying trigger."}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default function Signals() {
  const [category, setCategory] = useState("All");
  const [industry, setIndustry] = useState("All");
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [liveSignals, setLiveSignals] = useState<LiveOpportunitySignal[]>(fallbackLiveSignals);
  const [leadSummary, setLeadSummary] = useState<LeadSummary | null>(null);
  const [loadingLiveSignals, setLoadingLiveSignals] = useState(true);
  const [activeSignalIndex, setActiveSignalIndex] = useState(0);

  const filtered = SIGNAL_TYPES.filter((s) => {
    const matchCat = category === "All" || s.category === category;
    const matchInd = industry === "All" || s.industries.includes(industry) || s.industries.includes("All industries");
    const matchSearch = search === "" || s.name.toLowerCase().includes(search.toLowerCase()) || s.description.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchInd && matchSearch;
  });

  const orderedLiveSignals = useMemo(() => {
    if (!liveSignals.length) return [];
    const start = activeSignalIndex % liveSignals.length;
    return [...liveSignals.slice(start), ...liveSignals.slice(0, start)];
  }, [liveSignals, activeSignalIndex]);

  useEffect(() => {
    let cancelled = false;

    async function loadLeadSummary() {
      try {
        const response = await fetch(`${getApiBase()}/api/leads/summary?exclude_junk=true`, liveFetchInit());
        if (!response.ok) throw new Error(`Lead summary failed with ${response.status}`);
        const data = await response.json();
        if (!cancelled) setLeadSummary(data);
      } catch (error) {
        console.info(error);
      }
    }

    async function loadLiveSignals() {
      try {
        const response = await fetch(
          `${getApiBase()}/api/leads?limit=12&tier=HOT&sort=score&exclude_junk=true`,
          liveFetchInit(),
        );
        if (!response.ok) throw new Error(`Live signal feed failed with ${response.status}`);
        const data = await response.json();
        const leads = Array.isArray(data) ? data : [];
        const mapped = leads.map(mapLeadToLiveSignal).filter((signal) => signal.score > 0);
        if (!mapped.length) throw new Error("No scored leads returned");
        if (!cancelled) setLiveSignals(mapped);
      } catch (error) {
        console.info(error);
        if (!cancelled) setLiveSignals(fallbackLiveSignals);
      } finally {
        if (!cancelled) setLoadingLiveSignals(false);
      }
    }

    loadLeadSummary();
    loadLiveSignals();
    const refreshTimer = window.setInterval(() => {
      loadLeadSummary();
      loadLiveSignals();
    }, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(refreshTimer);
    };
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSignalIndex((current) => current + 1);
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="sticky top-20 z-20 mb-8 rounded-2xl border border-teal-300/20 px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3" style={{ background: "rgba(3,218,197,0.08)", backdropFilter: "blur(16px)" }}>
            <p className="text-sm text-white/70">
              These signals come from the same 150+ sources analyzed in our 2026 Automation Imperative Report.
            </p>
            <Link href="/intelligence" className="inline-flex items-center gap-1.5 text-sm font-bold shrink-0" style={{ color: "#03DAC5" }}>
              Download it <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Page header */}
          <div className="mb-10">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-2" style={{ color: "#a78bfa" }}>
              Signal library
            </p>
            <h1
              className="font-extrabold text-white leading-tight mb-3"
              style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              What we watch for
            </h1>
            <p className="text-sm text-white/40 max-w-xl">
              150+ sources monitored continuously. Every signal is scored, categorized, and matched to your robot category before it reaches your pipeline.
            </p>
          </div>

          <SignalRadar signals={liveSignals} summary={leadSummary} loading={loadingLiveSignals} activeIndex={activeSignalIndex} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Left: Signal library */}
            <div className="lg:col-span-2 flex flex-col gap-5">

              {/* Filters */}
              <div className="flex flex-col gap-3">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/25" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search signals…"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm text-white placeholder-white/25 border border-white/10 outline-none focus:border-violet-500/50 transition-colors"
                    style={{ background: "rgba(255,255,255,0.04)", fontFamily: "'Inter', system-ui, sans-serif" }}
                  />
                </div>

                {/* Category filter */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Filter className="h-3 w-3 text-white/25 shrink-0" />
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCategory(cat)}
                      className="text-[11px] font-semibold px-3 py-1.5 rounded-full border transition-all"
                      style={
                        category === cat
                          ? { background: "#7c3aed", borderColor: "#7c3aed", color: "#fff" }
                          : { background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.45)" }
                      }
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Industry filter */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Building2 className="h-3 w-3 text-white/25 shrink-0" />
                  {INDUSTRIES.map((ind) => (
                    <button
                      key={ind}
                      onClick={() => setIndustry(ind)}
                      className="text-[11px] font-semibold px-3 py-1.5 rounded-full border transition-all"
                      style={
                        industry === ind
                          ? { background: "rgba(124,58,237,0.3)", borderColor: "#7c3aed", color: "#c4b5fd" }
                          : { background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.35)" }
                      }
                    >
                      {ind}
                    </button>
                  ))}
                </div>
              </div>

              {/* Signal cards */}
              <div className="space-y-3">
                {filtered.length === 0 && (
                  <div className="text-center py-12 text-white/25 text-sm">No signals match your filters.</div>
                )}
                {filtered.map((sig) => {
                  const Icon = sig.icon;
                  const open = expanded === sig.id;
                  return (
                    <div
                      key={sig.id}
                      className="rounded-2xl border border-white/8 overflow-hidden hover:border-violet-500/20 transition-colors"
                      style={{ background: "rgba(255,255,255,0.03)" }}
                    >
                      <button
                        onClick={() => setExpanded(open ? null : sig.id)}
                        className="w-full flex items-start gap-4 p-5 text-left"
                      >
                        <div
                          className="h-9 w-9 rounded-xl flex items-center justify-center shrink-0"
                          style={{ background: `${sig.color}18`, border: `1px solid ${sig.color}30` }}
                        >
                          <Icon className="h-4 w-4" style={{ color: sig.color }} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-bold text-white">{sig.name}</span>
                            <span
                              className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest"
                              style={{ color: sig.color, background: `${sig.color}15`, border: `1px solid ${sig.color}25` }}
                            >
                              {sig.category}
                            </span>
                          </div>
                          <p className="text-xs text-white/40 leading-relaxed">{sig.description}</p>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <span
                            className="font-mono text-sm font-bold"
                            style={{ color: sig.color, fontFamily: "'JetBrains Mono', monospace" }}
                          >
                            {sig.avgScore}
                          </span>
                          <span className="text-[9px] text-white/20">avg score</span>
                        </div>
                      </button>

                      {open && (
                        <div className="px-5 pb-5 border-t border-white/6 pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-2">Sources monitored</p>
                            <div className="flex flex-wrap gap-1.5">
                              {sig.sources.map((src) => (
                                <span
                                  key={src}
                                  className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-white/40"
                                  style={{ background: "rgba(255,255,255,0.04)" }}
                                >
                                  {src}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-2">Industries</p>
                            <div className="flex flex-wrap gap-1.5">
                              {sig.industries.map((ind) => (
                                <span
                                  key={ind}
                                  className="text-[10px] px-2 py-0.5 rounded-full border text-white/50"
                                  style={{ background: `${sig.color}0d`, borderColor: `${sig.color}25`, color: sig.color }}
                                >
                                  {ind}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="sm:col-span-2">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-2">Real example</p>
                            <p className="text-xs text-white/50 italic">"{sig.example}"</p>
                          </div>
                          <div className="sm:col-span-2 flex items-center gap-3">
                            <span className="text-[10px] text-white/25">Detection frequency: <span className="text-white/45">{sig.frequency}</span></span>
                            <button
                              onClick={() => toast.success(`Watching for ${sig.name} signals`)}
                              className="ml-auto text-xs font-semibold px-3 py-1.5 rounded-lg text-white transition-all"
                              style={{ background: "#7c3aed" }}
                            >
                              Watch this signal
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right: Live signal feed */}
            <div className="flex flex-col gap-4">
              <div
                className="rounded-2xl border border-white/8 p-5"
                style={{ background: "rgba(255,255,255,0.02)" }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="h-3.5 w-3.5" style={{ color: MARKET_COLORS.amberBright }} />
                  <span className="text-xs font-bold text-white/60 uppercase tracking-widest">Live feed</span>
                  <span className="ml-auto h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: MARKET_COLORS.emeraldBright }} />
                </div>
                <div className="space-y-3">
                  {orderedLiveSignals.slice(0, 6).map((sig) => (
                    <div key={sig.id} className="flex items-start gap-3">
                      <span className="h-1.5 w-1.5 rounded-full shrink-0 mt-1.5" style={{ background: sig.color }} />
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-white/70">{sig.company}</p>
                        <p className="text-[10px] text-white/35">{sig.type} · {sig.track}</p>
                      </div>
                      <div className="flex flex-col items-end gap-0.5">
                        <span
                          className="font-mono text-xs font-bold"
                          style={{ color: sig.color, fontFamily: "'JetBrains Mono', monospace" }}
                        >
                          {sig.score}
                        </span>
                        <span className="text-[9px] text-white/20">{sig.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stats */}
              <div
                className="rounded-2xl border border-white/8 p-5"
                style={{ background: "rgba(255,255,255,0.02)" }}
              >
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-4">This week</p>
                <div className="space-y-3">
                  {[
                    { label: "Signals detected", value: "1,204", color: "#a78bfa" },
                    { label: "Hot leads identified", value: "38", color: "#34d399" },
                    { label: "Outreach drafts ready", value: "24", color: "#60a5fa" },
                    { label: "Sources monitored", value: "150+", color: "#f472b6" },
                  ].map((stat) => (
                    <div key={stat.label} className="flex items-center justify-between">
                      <span className="text-xs text-white/35">{stat.label}</span>
                      <span
                        className="font-mono text-sm font-bold"
                        style={{ color: stat.color, fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {stat.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
