/**
 * Signals — ReadyForRobots
 * Signal library: browse all 14 signal types, filter by category and industry
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 */
import { useState } from "react";
import { AlertTriangle, TrendingUp, DollarSign, Newspaper, Building2, Briefcase, Activity, Globe, Zap, Filter, Search, ChevronRight } from "lucide-react";
import Header from "@/components/Header";
import { toast } from "sonner";

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

const recentSignals = [
  { company: "Silver Peak Hospitality", type: "Labor Shortage", score: 94, time: "2m ago", color: "#f87171" },
  { company: "DesertLine Logistics", type: "Expansion Signal", score: 88, time: "18m ago", color: "#34d399" },
  { company: "Apex Manufacturing", type: "Safety Signal", score: 79, time: "1h ago", color: "#fb923c" },
  { company: "Harbor Fresh Foods", type: "CapEx Announcement", score: 85, time: "3h ago", color: "#a78bfa" },
  { company: "Ridgeline Hotels", type: "Labor Shortage", score: 91, time: "5h ago", color: "#f87171" },
  { company: "Cascade Fulfillment", type: "Automation Hiring", score: 76, time: "8h ago", color: "#60a5fa" },
];

export default function Signals() {
  const [category, setCategory] = useState("All");
  const [industry, setIndustry] = useState("All");
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = SIGNAL_TYPES.filter((s) => {
    const matchCat = category === "All" || s.category === category;
    const matchInd = industry === "All" || s.industries.includes(industry) || s.industries.includes("All industries");
    const matchSearch = search === "" || s.name.toLowerCase().includes(search.toLowerCase()) || s.description.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchInd && matchSearch;
  });

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-20 px-6">
        <div className="max-w-6xl mx-auto">

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
                  <Zap className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                  <span className="text-xs font-bold text-white/60 uppercase tracking-widest">Live feed</span>
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <div className="space-y-3">
                  {recentSignals.map((sig, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <span className="h-1.5 w-1.5 rounded-full shrink-0 mt-1.5" style={{ background: sig.color }} />
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-white/70">{sig.company}</p>
                        <p className="text-[10px] text-white/35">{sig.type}</p>
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
