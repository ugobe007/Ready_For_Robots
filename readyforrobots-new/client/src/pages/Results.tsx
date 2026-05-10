/**
 * Results — ReadyForRobots
 * Scanning animation → matched prospect cards with signals, scores, draft outreach
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 */
import { useState, useEffect } from "react";
import { ArrowRight, Zap, TrendingUp, MapPin, Users, AlertTriangle, CheckCircle2, FileText, ChevronDown, ChevronUp } from "lucide-react";
import { Link, useSearch } from "wouter";
import Header from "@/components/Header";
import { toast } from "sonner";

const SCAN_STEPS = [
  "Analyzing company profile…",
  "Scanning 150+ signal sources…",
  "Matching automation readiness patterns…",
  "Scoring qualification factors…",
  "Generating outreach drafts…",
  "Pipeline ready.",
];

const mockProspects = [
  {
    id: 1,
    company: "Silver Peak Hospitality Group",
    location: "Phoenix, AZ",
    industry: "Hospitality",
    employees: "2,400",
    score: 94,
    signal: "Earnings call: \"40% housekeeping vacancy, cannot staff overnight shifts\" — Q3 2026",
    signalType: "Labor shortage",
    signalIcon: AlertTriangle,
    signalColor: "#f87171",
    timing: "Decision window: Now",
    action: "Reach out with overnight automation case study",
    draft: `Subject: Solving Silver Peak's overnight staffing gap\n\nHi [Name],\n\nI came across your Q3 earnings call where you mentioned a 40% housekeeping vacancy and difficulty staffing overnight shifts. We work with hospitality groups facing exactly this challenge.\n\nReadyForRobots has helped similar properties automate overnight cleaning and turnover workflows — reducing labor dependency by 60% while improving consistency.\n\nWould a 15-minute call this week make sense? I can share how Marriott properties in Phoenix handled the same problem.\n\nBest,\n[Your name]`,
    stage: "New Signal",
  },
  {
    id: 2,
    company: "DesertLine Logistics",
    location: "Las Vegas, NV",
    industry: "Logistics",
    employees: "1,800",
    score: 88,
    signal: "Job posting: \"Automation Engineer\" + press release: \"Opening 2 new distribution centers in Q1 2027\"",
    signalType: "Expansion signal",
    signalIcon: TrendingUp,
    signalColor: "#34d399",
    timing: "Decision window: 3–6 months",
    action: "Contact during facility design phase",
    draft: `Subject: Automation planning for your new DCs\n\nHi [Name],\n\nCongratulations on the two new distribution centers — that's a significant expansion. I noticed you're also hiring an Automation Engineer, which suggests you're thinking about how to build automation into the new facilities from the start.\n\nWe specialize in helping logistics companies design automation into new DCs before construction locks in the layout. Getting this right at the design stage typically saves 30–40% vs. retrofitting.\n\nWould it be worth a quick call to share what we've seen work well at similar scale?\n\nBest,\n[Your name]`,
    stage: "Draft Ready",
  },
  {
    id: 3,
    company: "Apex Manufacturing Co.",
    location: "Tucson, AZ",
    industry: "Manufacturing",
    employees: "950",
    score: 79,
    signal: "OSHA filing: 3 repetitive strain injuries in 6 months + LinkedIn: hiring \"process improvement manager\"",
    signalType: "Safety signal",
    signalIcon: AlertTriangle,
    signalColor: "#fb923c",
    timing: "Decision window: 1–3 months",
    action: "Lead with safety ROI and ergonomics case",
    draft: `Subject: Reducing repetitive strain incidents at Apex\n\nHi [Name],\n\nI noticed Apex has had three repetitive strain injury filings in the past six months — a pattern we see frequently before companies invest in automation for high-repetition tasks.\n\nWe've helped manufacturers in similar situations reduce RSI incidents by 80%+ while improving throughput. The ROI case is usually straightforward when you factor in workers' comp, productivity loss, and turnover.\n\nYour new process improvement hire will likely be evaluating options soon. Would it make sense to connect before that process kicks off?\n\nBest,\n[Your name]`,
    stage: "New Signal",
  },
];

export default function Results() {
  const search = useSearch();
  const params = new URLSearchParams(search);
  const inputUrl = params.get("url") || "yourcompany.com";

  const [scanStep, setScanStep] = useState(0);
  const [scanning, setScanning] = useState(true);
  const [expandedDraft, setExpandedDraft] = useState<number | null>(null);

  useEffect(() => {
    if (scanStep < SCAN_STEPS.length - 1) {
      const t = setTimeout(() => setScanStep((s) => s + 1), 600);
      return () => clearTimeout(t);
    } else {
      const t = setTimeout(() => setScanning(false), 500);
      return () => clearTimeout(t);
    }
  }, [scanStep]);

  const scoreColor = (s: number) =>
    s >= 90 ? "#34d399" : s >= 75 ? "#a78bfa" : "#fb923c";

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-20 px-6">
        <div className="max-w-4xl mx-auto">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-white/30 mb-8">
            <Link href="/" className="hover:text-white/60 transition-colors">Home</Link>
            <span>/</span>
            <span className="text-white/50">Results for {inputUrl}</span>
          </div>

          {/* Scanning state */}
          {scanning ? (
            <div className="flex flex-col items-center justify-center py-24 gap-8">
              {/* Animated ring */}
              <div className="relative h-20 w-20">
                <div
                  className="absolute inset-0 rounded-full border-2 border-violet-500/20 animate-ping"
                  style={{ animationDuration: "1.5s" }}
                />
                <div className="absolute inset-2 rounded-full border-2 border-violet-500/40 animate-spin" style={{ animationDuration: "2s" }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="h-6 w-6" style={{ color: "#7c3aed" }} />
                </div>
              </div>

              {/* Step log */}
              <div className="w-full max-w-sm space-y-2">
                {SCAN_STEPS.slice(0, scanStep + 1).map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 text-sm"
                    style={{ opacity: i === scanStep ? 1 : 0.35 }}
                  >
                    {i < scanStep ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-violet-500/60 shrink-0 animate-pulse" />
                    )}
                    <span
                      className="font-mono text-xs"
                      style={{ color: i === scanStep ? "#c4b5fd" : "#ffffff55", fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <>
              {/* Results header */}
              <div className="mb-10">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-2" style={{ color: "#a78bfa" }}>
                  Scan complete · {mockProspects.length} opportunities found
                </p>
                <h1
                  className="font-extrabold text-white leading-tight"
                  style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
                >
                  Your matched pipeline
                </h1>
                <p className="text-sm text-white/40 mt-2">
                  Based on your profile at <span className="text-white/60 font-medium">{inputUrl}</span> — sorted by signal strength
                </p>
              </div>

              {/* Prospect cards */}
              <div className="space-y-4">
                {mockProspects.map((p) => {
                  const SignalIcon = p.signalIcon;
                  const draftOpen = expandedDraft === p.id;
                  return (
                    <div
                      key={p.id}
                      className="rounded-2xl border border-white/8 overflow-hidden hover:border-violet-500/25 transition-colors"
                      style={{ background: "rgba(255,255,255,0.03)" }}
                    >
                      {/* Card header */}
                      <div className="px-6 pt-6 pb-4 flex flex-col sm:flex-row sm:items-start gap-4">
                        {/* Score ring */}
                        <div className="shrink-0 flex flex-col items-center gap-1">
                          <div
                            className="h-14 w-14 rounded-full border-2 flex items-center justify-center"
                            style={{ borderColor: scoreColor(p.score), background: `${scoreColor(p.score)}12` }}
                          >
                            <span
                              className="font-mono text-lg font-bold"
                              style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {p.score}
                            </span>
                          </div>
                          <span className="text-[9px] text-white/25 uppercase tracking-widest">score</span>
                        </div>

                        {/* Company info */}
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-white">{p.company}</h2>
                            <span
                              className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                              style={{ color: "#a78bfa", background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
                            >
                              {p.stage}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-white/35 mb-3">
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />{p.location}
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />{p.employees} employees
                            </span>
                            <span>{p.industry}</span>
                          </div>

                          {/* Signal */}
                          <div
                            className="flex items-start gap-2.5 p-3 rounded-xl"
                            style={{ background: `${p.signalColor}0d`, border: `1px solid ${p.signalColor}25` }}
                          >
                            <SignalIcon className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: p.signalColor }} />
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-widest mr-2" style={{ color: p.signalColor }}>
                                {p.signalType}
                              </span>
                              <span className="text-xs text-white/50">{p.signal}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Recommended action */}
                      <div className="px-6 pb-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                        <div className="flex items-center gap-2 flex-1">
                          <ArrowRight className="h-3.5 w-3.5 shrink-0" style={{ color: "#7c3aed" }} />
                          <span className="text-sm text-white/60">{p.action}</span>
                        </div>
                        <span
                          className="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0"
                          style={{ color: "#34d399", background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.25)" }}
                        >
                          {p.timing}
                        </span>
                      </div>

                      {/* Draft outreach toggle */}
                      <div className="border-t border-white/6">
                        <button
                          onClick={() => setExpandedDraft(draftOpen ? null : p.id)}
                          className="w-full flex items-center justify-between px-6 py-3.5 text-left hover:bg-white/2 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                            <span className="text-xs font-semibold" style={{ color: "#a78bfa" }}>View drafted outreach</span>
                          </div>
                          {draftOpen
                            ? <ChevronUp className="h-3.5 w-3.5 text-white/25" />
                            : <ChevronDown className="h-3.5 w-3.5 text-white/25" />
                          }
                        </button>
                        {draftOpen && (
                          <div className="px-6 pb-5 border-t border-white/6">
                            <pre
                              className="text-xs text-white/50 leading-relaxed whitespace-pre-wrap pt-4"
                              style={{ fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {p.draft}
                            </pre>
                            <div className="flex gap-2 mt-4">
                              <button
                                onClick={() => toast.success("Outreach approved and queued")}
                                className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg text-white transition-all hover:-translate-y-0.5"
                                style={{ background: "#7c3aed", boxShadow: "0 4px 16px rgba(124,58,237,0.35)" }}
                              >
                                <CheckCircle2 className="h-3.5 w-3.5" /> Approve & send
                              </button>
                              <button
                                onClick={() => toast.info("Opening editor…")}
                                className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg text-white/60 border border-white/10 hover:border-white/20 transition-colors"
                                style={{ background: "rgba(255,255,255,0.04)" }}
                              >
                                Edit draft
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bottom CTA */}
              <div
                className="mt-10 rounded-2xl border border-violet-500/20 p-8 text-center"
                style={{ background: "rgba(124,58,237,0.06)" }}
              >
                <p className="text-sm text-white/50 mb-2">Want your full pipeline — not just a preview?</p>
                <h3 className="font-bold text-white text-lg mb-5" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Sign up to unlock all matched opportunities
                </h3>
                <button
                  onClick={() => toast.success("Account creation coming soon!")}
                  className="inline-flex items-center gap-2 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5"
                  style={{ background: "#7c3aed", boxShadow: "0 8px 24px rgba(124,58,237,0.35)" }}
                >
                  Create free account <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
