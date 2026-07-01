/**
 * Signals — ReadyForRobots
 * Signal library: browse all 14 signal types, filter by category and industry
 * Violet palette: #111827 bg · #059669 accent · cream text
 */
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, TrendingUp, DollarSign, Newspaper, Building2, Briefcase, Activity, Globe, Zap, Filter, Search, ChevronRight } from "lucide-react";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { getApiBase, getPublicReadApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanAndClampText, cleanScrapedText, leadPreviewSentences } from "@/lib/text";
import { Link } from "wouter";
import { toast } from "sonner";
import LeadShareBar from "@/components/LeadShareBar";

type ApiLead = {
  id?: number | string;
  company_name?: string;
  industry?: string | null;
  priority_tier?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
  share_summary?: string | null;
  share_blurb?: string | null;
  robot_types_needed?: string[];
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
  leadId?: number;
  company: string;
  type: string;
  text: string;
  score: number;
  track: OpportunityTrack;
  time: string;
  color: string;
  industry: string;
  priorityTier?: string;
  shareSummary?: string;
  shareBlurb?: string;
  robotTypes?: string[];
  signals?: ApiLead["signals"];
};

type LeadSummary = {
  total?: number;
  hot?: number;
  warm?: number;
  cold?: number;
  total_signals?: number;
};

const MARKET_COLORS = {
  emerald: "#00D27A",
  emeraldBright: "#34F5A5",
  amber: "#FFB000",
  amberBright: "#FFB000",
  teal: "#059669",
  violet: "#C084FC",
};

const RADAR_SIGNAL_ROWS = [
  { label: "Labor Shortage", track: "Sales" as OpportunityTrack, baseline: 0.82 },
  { label: "Expansion Signal", track: "Sales" as OpportunityTrack, baseline: 0.76 },
  { label: "CapEx Announcement", track: "Sales" as OpportunityTrack, baseline: 0.72 },
  { label: "Safety Signal", track: "Sales" as OpportunityTrack, baseline: 0.66 },
  { label: "Automation Hiring", track: "Sales" as OpportunityTrack, baseline: 0.62 },
  { label: "Leadership Change", track: "Sales" as OpportunityTrack, baseline: 0.58 },
  { label: "Contract Win", track: "Partnership" as OpportunityTrack, baseline: 0.54 },
  { label: "Integrator Fit", track: "Partnership" as OpportunityTrack, baseline: 0.5 },
  { label: "Industry News Trigger", track: "Partnership" as OpportunityTrack, baseline: 0.46 },
];

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
    color: MARKET_COLORS.emeraldBright,
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
    color: "#FFB000",
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
    color: MARKET_COLORS.violet,
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
    color: MARKET_COLORS.teal,
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
    color: MARKET_COLORS.amber,
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
    color: MARKET_COLORS.amberBright,
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
    color: MARKET_COLORS.emeraldBright,
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
    cleanScrapedText(lead.share_summary),
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
    "SIGNAL found a scored automation opportunity worth reviewing.";
  return {
    id: String(lead.id ?? `${lead.company_name || "lead"}-${index}`),
    leadId: typeof lead.id === "number" ? lead.id : undefined,
    company: lead.company_name || `Scored Lead ${index + 1}`,
    type,
    text:
      leadPreviewSentences(lead.share_summary || String(text), 3, 480) ||
      "SIGNAL found a scored automation opportunity worth reviewing.",
    score: leadScore(lead),
    track,
    time: index < 3 ? `${Math.max(index * 4 + 2, 2)}m ago` : "live",
    color: signalColor(type, track),
    industry: lead.industry || "Market",
    priorityTier: lead.priority_tier || undefined,
    shareSummary: lead.share_summary || undefined,
    shareBlurb: lead.share_blurb || undefined,
    robotTypes: lead.robot_types_needed,
    signals: lead.signals,
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

  return RADAR_SIGNAL_ROWS.map((seed, index) => {
    const salesMatch = groups.get(`Sales:${seed.label}`);
    const partnerMatch = groups.get(`Partnership:${seed.label}`);
    const matched = salesMatch || partnerMatch;
    const average = matched ? matched.total / matched.count : seed.baseline * 100;
    const pulse = index === activeIndex % RADAR_SIGNAL_ROWS.length ? 0.035 : 0;
    const value = Math.min(0.98, Math.max(0.22, average / 100 + (matched ? Math.min(matched.count * 0.02, 0.08) : 0) + pulse));
    return {
      label: seed.label,
      track: matched?.track || seed.track,
      value,
      delta: `+${Math.max(1, (matched?.count || 0) + Math.round((average - 58) / 12)).toString().padStart(2, "0")}`,
      color: (matched?.track || seed.track) === "Partnership" ? MARKET_COLORS.amberBright : MARKET_COLORS.emeraldBright,
    };
  })
    .sort((a, b) => b.value - a.value);
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
    <section className="signal-radar-dark mb-10">
      <style>{`
        @keyframes rfr-radar-sweep { 0% { transform: translateX(-22%); opacity: .08; } 38% { opacity: .35; } 100% { transform: translateX(122%); opacity: .08; } }
        @keyframes rfr-bar-sheen { 0% { transform: translateX(-120%); opacity: 0; } 30% { opacity: .45; } 100% { transform: translateX(120%); opacity: 0; } }
        @keyframes rfr-live-rise { 0% { transform: translateY(3px); opacity: .7; } 100% { transform: translateY(0); opacity: 1; } }
      `}</style>
      <div className="signal-radar-head p-5 lg:p-6">
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="section-eyebrow mb-2">Live buyer intelligence</p>
            <h2 className="section-headline font-bold">
              Find robot buyers before they shop elsewhere
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed">
              ReadyForRobots helps robot companies find buyers for their robots. We monitor 150+ market signals to identify
              who is ready to purchase — and when the buying window opens.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[
              ["Leads", formatMetric(totalLeads), "text-emerald-400"],
              ["Hot", formatMetric(hotLeads), "text-emerald-400"],
              ["Warm", formatMetric(warmLeads), "text-amber-400"],
              ["Signals", formatMetric(totalSignals), "text-white"],
            ].map(([label, value, colorClass]) => (
              <div key={String(label)} className="signal-radar-stat">
                <div className={`font-mono text-lg font-black ${colorClass}`}>{value}</div>
                <div className="signal-radar-stat-label">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 p-5 lg:grid-cols-[1.35fr_0.85fr] lg:p-6">
        <div className="signal-radar-chart">
          <div
            className="pointer-events-none absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "linear-gradient(rgba(16,185,129,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.06) 1px, transparent 1px)",
              backgroundSize: "42px 42px",
            }}
          />
          <div
            className="pointer-events-none absolute inset-y-0 left-0 w-1/4"
            style={{
              background: "linear-gradient(90deg, transparent, rgba(16,185,129,0.12), rgba(255,176,0,0.08), transparent)",
              animation: "rfr-radar-sweep 10s linear infinite",
            }}
          />
          <div className="relative mb-4 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
            <span>{loading ? "Syncing scored leads" : "150+ sources scanning"}</span>
            <span className="text-emerald-400">Live signal strength</span>
          </div>
          <div className="signal-radar-chart-caption">
            Each bar is a signal type. Length shows buyer readiness from live sales leads — updated as we score the next opportunity.
          </div>

          <div className="relative space-y-4">
            {radarRows.map((row, rowIndex) => {
              const activeLane = activeSignal?.type === row.label && activeSignal?.track === row.track;
              const sameMotion = activeSignal?.track === row.track;
              const adjustedValue = Math.min(
                0.98,
                Math.max(0.16, row.value + (activeLane ? 0.16 : sameMotion ? 0.05 : -0.03)),
              );
              const isPartner = row.track === "Partnership";
              return (
                <div
                  key={`${row.track}-${row.label}`}
                  className={`relative rounded-2xl border p-3 transition-colors ${
                    activeLane
                      ? isPartner
                        ? "border-amber-500/40 bg-amber-500/10"
                        : "border-emerald-500/40 bg-emerald-500/10"
                      : "border-white/10 bg-white/[0.04]"
                  }`}
                  style={{
                    animation: "rfr-live-rise .42s ease-out both",
                    animationDelay: `${rowIndex * 65}ms`,
                  }}
                >
                  <div className="grid gap-3 md:grid-cols-[180px_1fr_74px] md:items-center">
                    <div>
                      <div
                        className={`flex items-center gap-2 text-base font-black ${
                          isPartner ? "text-amber-300" : "text-emerald-300"
                        }`}
                      >
                        {activeLane && (
                          <span
                            className={`h-2 w-2 rounded-full animate-pulse ${isPartner ? "bg-amber-500" : "bg-emerald-500"}`}
                          />
                        )}
                        <span>{row.label}</span>
                      </div>
                      <div className="mt-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                        {row.track} motion
                      </div>
                    </div>

                    <div>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <span className="truncate text-xs font-semibold text-slate-200">
                          {activeLane ? `Matched to ${activeSignal?.company}` : `${row.delta} scored signals`}
                        </span>
                        <span className="font-mono text-xs font-bold text-white">{Math.round(adjustedValue * 100)}%</span>
                      </div>
                      <div className="relative h-3 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="absolute inset-y-0 left-0 overflow-hidden rounded-full transition-all duration-700 ease-out"
                          style={{
                            width: `${Math.round(adjustedValue * 100)}%`,
                            background: isPartner
                              ? "linear-gradient(90deg, #d97706, #f59e0b)"
                              : "linear-gradient(90deg, #059669, #10b981)",
                            boxShadow: activeLane
                              ? isPartner
                                ? "0 0 16px rgba(245,158,11,.25)"
                                : "0 0 16px rgba(16,185,129,.25)"
                              : "none",
                          }}
                        >
                          <div
                            className="absolute inset-y-0 w-1/2"
                            style={{
                              background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)",
                              animation: activeLane ? "rfr-bar-sheen 2.2s ease-in-out infinite" : undefined,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <div
                      className={`font-mono text-left text-sm font-black md:text-right ${
                        isPartner ? "text-amber-300" : "text-emerald-300"
                      }`}
                    >
                      {Math.round(adjustedValue * 100)}
                      <span className="ml-1 text-[10px] font-bold text-slate-500">strength</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="signal-radar-live">
          {activeSignal && (
            <div className="relative">
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-400">
                Scoring now
              </p>
              <h3 className="text-2xl font-black leading-tight text-white">
                {activeSignal.company}
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                <span
                  className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest ${
                    activeSignal.track === "Partnership"
                      ? "border-amber-500/40 bg-amber-500/15 text-amber-200"
                      : "border-emerald-500/40 bg-emerald-500/15 text-emerald-200"
                  }`}
                >
                  {activeSignal.track}
                </span>
                <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-300">
                  {activeSignal.industry}
                </span>
              </div>
              <div className="my-6 flex items-end justify-between gap-4">
                <div>
                  <div
                    className={`font-mono text-6xl font-black leading-none ${
                      activeSignal.track === "Partnership" ? "text-amber-400" : "text-emerald-400"
                    }`}
                  >
                    {activeSignal.score}
                  </div>
                  <div className="mt-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">buyer readiness</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-white">{activeSignal.type}</div>
                  <div className="text-[10px] text-slate-500">{activeSignal.time}</div>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-slate-300">{activeSignal.text}</p>
              {activeSignal.robotTypes && activeSignal.robotTypes.length > 0 && (
                <p className="mt-3 text-xs text-slate-300">
                  <span className="font-semibold text-emerald-300">Robots needed: </span>
                  {activeSignal.robotTypes.slice(0, 4).join(" · ")}
                </p>
              )}
              {activeSignal.leadId != null && (
                <div className="mt-4">
                  <LeadShareBar
                    variant="light"
                    lead={{
                      id: activeSignal.leadId,
                      company_name: activeSignal.company,
                      priority_tier: activeSignal.priorityTier,
                      share_summary: activeSignal.shareSummary,
                      share_blurb: activeSignal.shareBlurb,
                      signals: activeSignal.signals,
                    }}
                  />
                </div>
              )}
              <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Recommended motion</div>
                <p className="mt-2 text-xs leading-relaxed text-slate-300">
                  {activeSignal.track === "Partnership"
                    ? "Qualify channel fit, coverage overlap, and co-sell timing while this partner signal is fresh."
                    : "Reach out now with outreach tied to this buying trigger — before competitors find the same signal."}
                </p>
              </div>
              <Link
                href="/signup?next=/pipeline"
                className="mt-5 inline-flex w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 hover:-translate-y-0.5"
              >
                Start finding buyers free
              </Link>
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
        const response = await fetch(`${getPublicReadApiBase()}/api/leads/summary?exclude_junk=true`, liveFetchInit());
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
          `${getPublicReadApiBase()}/api/leads?limit=24&tier=HOT&sort=score&exclude_junk=true`,
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
    }, 4000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <PageHeroDark
        maxWidthClass="max-w-6xl"
        badge={
          <div className="page-hero-badge">
            <span className="relative inline-flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            {formatMetric(leadSummary?.total_signals ?? 0) || "8,058"} live signals · 150+ sources monitored
          </div>
        }
        eyebrow="Signal library"
        title="What we watch for"
        description="150+ sources monitored continuously. Every signal is scored, categorized, and matched to your robot category before it reaches your pipeline."
        stats={[
          { label: "Signals this week", value: formatMetric(1204), tone: "white" },
          { label: "Hot leads", value: formatMetric(leadSummary?.hot ?? 38), tone: "amber" },
          { label: "Drafts ready", value: formatMetric(24), tone: "emerald" },
          { label: "Sources", value: "150+", tone: "white" },
        ]}
        innerClassName="pb-4"
      />

      <section className="bg-white pb-12 pt-4">
        <div className="container max-w-6xl pb-8">
          <div className="mb-8 flex flex-col gap-3 rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-gray-800">
              These signals come from the same 150+ sources analyzed in our 2026 Automation Imperative Report.
            </p>
            <Link href="/intelligence" className="inline-flex shrink-0 items-center gap-1.5 text-sm font-bold text-emerald-800 hover:text-emerald-900">
              Download it <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          <SignalRadar signals={liveSignals} summary={leadSummary} loading={loadingLiveSignals} activeIndex={activeSignalIndex} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">

            {/* Left: Signal library */}
            <div className="lg:col-span-2 flex flex-col gap-5">

              {/* Filters */}
              <div className="flex flex-col gap-3">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search signals…"
                    className="sb-input py-2.5 pl-9"
                  />
                </div>

                {/* Category filter */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Filter className="h-3 w-3 text-gray-500 shrink-0" />
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCategory(cat)}
                      className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-all ${
                        category === cat
                          ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                          : "border-gray-200 bg-white text-gray-600 hover:border-emerald-300 hover:text-emerald-700"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Industry filter */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Building2 className="h-3 w-3 text-gray-500 shrink-0" />
                  {INDUSTRIES.map((ind) => (
                    <button
                      key={ind}
                      onClick={() => setIndustry(ind)}
                      className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-all ${
                        industry === ind
                          ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                          : "border-gray-200 bg-white text-gray-600 hover:border-emerald-300 hover:text-emerald-700"
                      }`}
                    >
                      {ind}
                    </button>
                  ))}
                </div>
              </div>

              {/* Signal cards */}
              <div className="space-y-3">
                {filtered.length === 0 && (
                  <div className="text-center py-12 text-gray-500 text-sm">No signals match your filters.</div>
                )}
                {filtered.map((sig) => {
                  const Icon = sig.icon;
                  const open = expanded === sig.id;
                  return (
                    <div
                      key={sig.id}
                      className="surface-card overflow-hidden"
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
                            <span className="text-sm font-bold text-gray-900">{sig.name}</span>
                            <span
                              className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest border"
                              style={{ color: sig.color, background: `${sig.color}12`, borderColor: `${sig.color}35` }}
                            >
                              {sig.category}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 leading-relaxed">{sig.description}</p>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <span className="font-mono-data text-sm font-bold" style={{ color: sig.color }}>
                            {sig.avgScore}
                          </span>
                          <span className="text-[9px] text-gray-500">avg score</span>
                        </div>
                      </button>

                      {open && (
                        <div className="px-5 pb-5 border-t border-gray-100 pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Sources monitored</p>
                            <div className="flex flex-wrap gap-1.5">
                              {sig.sources.map((src) => (
                                <span
                                  key={src}
                                  className="text-[10px] px-2 py-0.5 rounded-full border border-gray-200 bg-gray-50 text-gray-600"
                                >
                                  {src}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Industries</p>
                            <div className="flex flex-wrap gap-1.5">
                              {sig.industries.map((ind) => (
                                <span
                                  key={ind}
                                  className="text-[10px] px-2 py-0.5 rounded-full border text-gray-500"
                                  style={{ background: `${sig.color}0d`, borderColor: `${sig.color}25`, color: sig.color }}
                                >
                                  {ind}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="sm:col-span-2">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">Real example</p>
                            <p className="text-xs text-gray-500 italic">"{sig.example}"</p>
                          </div>
                          <div className="sm:col-span-2 flex items-center gap-3">
                            <span className="text-[10px] text-gray-400">Detection frequency: <span className="text-gray-500">{sig.frequency}</span></span>
                            <button
                              onClick={() => toast.success(`Watching for ${sig.name} signals`)}
                              className="ml-auto text-xs font-semibold px-3 py-1.5 rounded-lg text-white transition-all"
                              style={{ background: "#059669" }}
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
              <div className="surface-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="h-3.5 w-3.5 text-amber-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-gray-700">Live feed</span>
                  <span className="ml-auto h-1.5 w-1.5 rounded-full animate-pulse bg-emerald-500" />
                </div>
                <div className="space-y-3">
                  {orderedLiveSignals.slice(0, 6).map((sig) => (
                    <div key={sig.id} className="flex items-start gap-3">
                      <span className="h-1.5 w-1.5 rounded-full shrink-0 mt-1.5" style={{ background: sig.color }} />
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-gray-900">{sig.company}</p>
                        <p className="text-[10px] text-gray-500">{sig.type} · {sig.track}</p>
                      </div>
                      <div className="flex flex-col items-end gap-0.5">
                        <span className="font-mono-data text-xs font-bold" style={{ color: sig.color }}>
                          {sig.score}
                        </span>
                        <span className="text-[9px] text-gray-500">{sig.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="surface-card p-5">
                <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4">This week</p>
                <div className="space-y-3">
                  {[
                    { label: "Signals detected", value: "1,204", color: "#059669" },
                    { label: "Hot leads identified", value: "38", color: "#d97706" },
                    { label: "Outreach drafts ready", value: "24", color: "#2563eb" },
                    { label: "Sources monitored", value: "150+", color: "#059669" },
                  ].map((stat) => (
                    <div key={stat.label} className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">{stat.label}</span>
                      <span className="font-mono-data text-sm font-bold" style={{ color: stat.color }}>
                        {stat.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
