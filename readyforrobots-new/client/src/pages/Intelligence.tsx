import { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Building2, Database, FileText, Mail, Radio, Search, Send, Target, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

type Story = {
  title?: string;
  company?: string;
  summary?: string;
  score?: number;
};

const fallbackStories: Story[] = [
  { title: "Hospitality labor pressure", summary: "Service robot demand concentrates where staffing gaps are now visible in public signals." },
  { title: "Logistics leads adoption", summary: "Warehouse and fulfillment operators show the highest signal density across expansion and hiring patterns." },
  { title: "ROI pressure rises", summary: "Buyers are framing robotics around payback, staffing resilience, and throughput guarantees." },
];

const signalStats = [
  ["158", "enterprises analyzed"],
  ["437", "buying signals detected"],
  ["62%", "strong buying intent"],
];

function IntelligenceFlow() {
  const stages = [
    { icon: Database, label: "Source", copy: "150+ feeds", color: "#03DAC5" },
    { icon: Radio, label: "Signal", copy: "labor + capex", color: "#a78bfa" },
    { icon: BarChart3, label: "Rank", copy: "intent score", color: "#FFB000" },
    { icon: Target, label: "Identify", copy: "sales + partner fit", color: "#34d399" },
  ];

  return (
    <div className="relative overflow-hidden border border-white/10 p-5 shadow-2xl shadow-black/40" style={{ background: "linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025))", borderRadius: 18 }}>
      <style>{`
        @keyframes rfr-scan-line { 0% { transform: translateY(-12%); opacity: .15; } 45% { opacity: .75; } 100% { transform: translateY(112%); opacity: .12; } }
        @keyframes rfr-pulse-node { 0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(255,176,0,0); } 50% { transform: scale(1.04); box-shadow: 0 0 28px rgba(255,176,0,.16); } }
        @keyframes rfr-flow-dot { 0% { left: 5%; opacity: 0; } 12% { opacity: 1; } 88% { opacity: 1; } 100% { left: 92%; opacity: 0; } }
      `}</style>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-20" style={{ background: "radial-gradient(circle at 50% 0%, rgba(3,218,197,0.20), transparent 62%)" }} />
      <div className="pointer-events-none absolute left-0 right-0 h-16" style={{ top: 0, background: "linear-gradient(180deg, transparent, rgba(3,218,197,0.14), transparent)", animation: "rfr-scan-line 3.2s linear infinite" }} />

      <div className="relative mb-8 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#03DAC5" }}>Live intelligence loop</p>
          <p className="mt-2 text-sm text-white/45">SCOUT turns market noise into action.</p>
        </div>
        <span className="border px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest" style={{ color: "#FFB000", borderColor: "rgba(255,176,0,0.35)", background: "rgba(255,176,0,0.06)", borderRadius: 8 }}>
          Running
        </span>
      </div>

      <div className="relative">
        <div className="absolute left-[8%] right-[8%] top-8 h-px bg-white/10" />
        <span className="absolute top-[29px] h-1.5 w-1.5 rounded-full" style={{ background: "#FFB000", animation: "rfr-flow-dot 3.4s ease-in-out infinite" }} />
        <div className="grid grid-cols-4 gap-3">
          {stages.map((stage, i) => {
            const Icon = stage.icon;
            return (
              <div key={stage.label} className="relative text-center">
                <div
                  className="mx-auto mb-3 flex h-16 w-16 items-center justify-center border"
                  style={{
                    borderColor: `${stage.color}55`,
                    background: `${stage.color}12`,
                    borderRadius: 14,
                    animation: i === 2 ? "rfr-pulse-node 2.4s ease-in-out infinite" : undefined,
                  }}
                >
                  <Icon className="h-5 w-5" style={{ color: stage.color }} />
                </div>
                <p className="text-xs font-extrabold text-white">{stage.label}</p>
                <p className="mt-1 text-[10px] text-white/35">{stage.copy}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-px overflow-hidden border border-white/8" style={{ borderRadius: 14, background: "rgba(255,255,255,0.08)" }}>
        {[
          ["sales", "capacity pain + decision timing"],
          ["partners", "integrators + channel fit"],
        ].map(([label, copy]) => (
          <div key={label} className="p-4" style={{ background: "rgba(13,5,32,0.72)" }}>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em]" style={{ color: label === "sales" ? "#FFB000" : "#03DAC5" }}>{label}</p>
            <p className="mt-2 text-xs leading-relaxed text-white/45">{copy}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Intelligence() {
  const [stories, setStories] = useState<Story[]>([]);
  const [email, setEmail] = useState("");
  const [reportForm, setReportForm] = useState({ name: "", email: "", company: "", robotCategory: "" });
  const [newsletterStatus, setNewsletterStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [reportStatus, setReportStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/newsletter/edition?limit=3`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data?.topStories) setStories(data.topStories);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function subscribe(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    setNewsletterStatus("submitting");
    try {
      const res = await fetch(`${getApiBase()}/api/newsletter/subscribe`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "intelligence_page" }),
      }));
      if (!res.ok) throw new Error("Subscribe failed");
      setNewsletterStatus("success");
      setEmail("");
    } catch {
      setNewsletterStatus("error");
    }
  }

  async function requestReport(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!reportForm.email.trim()) return;
    setReportStatus("submitting");
    try {
      const res = await fetch(`${getApiBase()}/api/leads/report-download`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reportForm),
      }));
      if (!res.ok) throw new Error("Report request failed");
      setReportStatus("success");
    } catch {
      setReportStatus("error");
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 px-6 pb-20 pt-28">
        <div className="max-w-6xl mx-auto">
          <section className="relative mb-14 grid grid-cols-1 items-center gap-10 lg:grid-cols-[1fr_440px]">
            <div className="pointer-events-none absolute -left-24 -top-24 h-64 w-64 rounded-full blur-3xl" style={{ background: "rgba(3,218,197,0.08)" }} />
            <div>
              <p className="mb-5 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#03DAC5" }}>
                ReadyForRobots Intelligence
              </p>
              <h1 className="font-extrabold leading-[0.98] tracking-tight text-white" style={{ fontSize: "clamp(2.7rem, 7vw, 5.7rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                Robot Demand Signals, Ranked
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-relaxed text-white/48">
                The same engine that powers <span style={{ color: "#FFB000", fontWeight: 800 }}>SCOUT</span> watches labor pressure, expansion plans, CapEx hints, automation hiring, and deployment news, then turns those signals into sales and partnership opportunities.
              </p>
              <div className="mt-8 grid max-w-xl grid-cols-3 gap-px overflow-hidden border border-white/8" style={{ background: "rgba(255,255,255,0.08)", borderRadius: 16 }}>
                {signalStats.map(([value, label]) => (
                  <div key={label} className="p-4" style={{ background: "rgba(255,255,255,0.035)" }}>
                    <p className="font-mono text-2xl font-bold" style={{ color: value === "62%" ? "#FFB000" : "#03DAC5", fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
                    <p className="mt-1 text-[11px] leading-snug text-white/35">{label}</p>
                  </div>
                ))}
              </div>
              <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-3 text-sm">
                <a href="#report" className="inline-flex items-center gap-2 font-bold" style={{ color: "#03DAC5" }}>
                  Download report <ArrowRight className="h-4 w-4" />
                </a>
                <Link href="/signals" className="inline-flex items-center gap-2 font-bold text-white/55 hover:text-white/80">
                  Explore robot signals <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/results?url=" className="inline-flex items-center gap-2 font-bold" style={{ color: "#FFB000" }}>
                  Activate SCOUT <Zap className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <IntelligenceFlow />
          </section>

          <section id="report" className="mb-14 grid grid-cols-1 gap-px overflow-hidden border border-white/10 lg:grid-cols-[1fr_380px]" style={{ background: "rgba(255,255,255,0.08)", borderRadius: 20 }}>
            <div className="p-6 lg:p-8" style={{ background: "rgba(255,255,255,0.035)" }}>
              <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#03DAC5" }}>Enterprise Intelligence Report</p>
              <h2 className="max-w-2xl text-3xl font-extrabold leading-tight text-white lg:text-4xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                The Automation Imperative: labor-intensive industries are flashing buy signals.
              </h2>
              <p className="mt-5 max-w-2xl text-sm leading-relaxed text-white/45">
                Built from real ReadyForRobots signal data: <span className="text-white/75">158 enterprises</span>, <span className="text-white/75">437 buying signals</span>, and sector-level ROI patterns for robotics vendors selling into labor-constrained operations.
              </p>
              <div className="mt-7 grid grid-cols-1 gap-3 md:grid-cols-3">
                {[
                  ["Logistics", "leading adoption"],
                  ["Labor shortage", "highest-intent trigger"],
                  ["ROI models", "sales narrative ready"],
                ].map(([label, copy]) => (
                  <div key={label} className="border-l px-4 py-2" style={{ borderColor: "rgba(3,218,197,0.45)" }}>
                    <p className="text-sm font-bold text-white/80">{label}</p>
                    <p className="mt-1 text-xs text-white/35">{copy}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-5" style={{ background: "rgba(13,5,32,0.82)" }}>
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center border" style={{ borderColor: "rgba(3,218,197,0.38)", background: "rgba(3,218,197,0.08)", borderRadius: 10 }}>
                  <FileText className="h-4 w-4" style={{ color: "#03DAC5" }} />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">Download the 2026 report</p>
                  <p className="text-xs text-white/35">No pillow buttons. Just the data.</p>
                </div>
              </div>
              {reportStatus === "success" ? (
                <div className="border border-teal-300/20 p-4 text-sm" style={{ color: "#99f6e4", background: "rgba(3,218,197,0.06)", borderRadius: 12 }}>
                  Report requested. We saved your request and queued the follow-up email.
                </div>
              ) : (
                <form onSubmit={requestReport} className="space-y-3">
                  {[
                    ["name", "Name", "text"],
                    ["email", "Work email", "email"],
                    ["company", "Company", "text"],
                    ["robotCategory", "Robot category", "text"],
                  ].map(([key, label, type]) => (
                    <input
                      key={key}
                      type={type}
                      required={key === "email"}
                      placeholder={label}
                      value={reportForm[key as keyof typeof reportForm]}
                      onChange={(e) => setReportForm((current) => ({ ...current, [key]: e.target.value }))}
                      className="w-full border border-white/10 px-3.5 py-2.5 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                      style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10 }}
                    />
                  ))}
                  {reportStatus === "error" && <p className="text-xs text-red-300">Could not request report. Try again.</p>}
                  <button type="submit" disabled={reportStatus === "submitting"} className="w-full border px-4 py-2.5 text-sm font-bold transition-colors hover:bg-teal-300/6 disabled:opacity-50" style={{ color: "#03DAC5", borderColor: "rgba(3,218,197,0.55)", background: "transparent", borderRadius: 10 }}>
                    {reportStatus === "submitting" ? "Requesting..." : "Download Free Report"}
                  </button>
                </form>
              )}
            </div>
          </section>

          <section className="mb-14 grid grid-cols-1 gap-4 lg:grid-cols-4">
            {[
              { icon: Search, title: "Source", copy: "Industry news, job posts, filings, earnings calls, permits, and trade signals." },
              { icon: Radio, title: "Signal", copy: "SCOUT identifies the public clues that point to automation readiness." },
              { icon: BarChart3, title: "Rank", copy: "Scores prioritize timing, pain intensity, fit, and deal motion." },
              { icon: Building2, title: "Identify", copy: "Sales leads and partnership opportunities become next actions." },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="group border border-white/8 p-5 transition-colors hover:border-teal-300/25" style={{ background: "rgba(255,255,255,0.03)", borderRadius: 16 }}>
                  <Icon className="mb-6 h-5 w-5 transition-transform group-hover:scale-110" style={{ color: item.title === "Rank" ? "#FFB000" : "#03DAC5" }} />
                  <p className="mb-2 text-sm font-bold text-white">{item.title}</p>
                  <p className="text-sm leading-relaxed text-white/40">{item.copy}</p>
                </div>
              );
            })}
          </section>

          <section id="brief" className="border border-white/10 p-6 lg:p-8" style={{ background: "rgba(255,255,255,0.035)", borderRadius: 20 }}>
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
              <div>
                <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em]" style={{ color: "#a78bfa" }}>Robot Intelligence Brief</p>
                <h2 className="max-w-2xl text-3xl font-extrabold leading-tight text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  A weekly brief that keeps the market warm between sales cycles.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-relaxed text-white/42">
                  Each issue packages new signals, deployment stories, vendor movement, and ROI language so teams know where to act before the market does.
                </p>
                <div className="mt-7 grid grid-cols-1 gap-3 md:grid-cols-3">
                  {(stories.length ? stories : fallbackStories).slice(0, 3).map((story, i) => (
                    <div key={`${story.title || story.company || i}`} className="border border-white/8 p-4" style={{ background: "rgba(13,5,32,0.45)", borderRadius: 14 }}>
                      <p className="mb-2 text-sm font-bold text-white/85">{story.title || story.company || "Signal story"}</p>
                      <p className="text-xs leading-relaxed text-white/36">{story.summary || "Fresh signal intelligence from ReadyForRobots."}</p>
                    </div>
                  ))}
                </div>
              </div>
              <form onSubmit={subscribe} className="border border-white/8 p-5" style={{ background: "rgba(13,5,32,0.55)", borderRadius: 16 }}>
                <Mail className="mb-4 h-5 w-5" style={{ color: "#03DAC5" }} />
                <p className="mb-2 text-sm font-bold text-white">Subscribe free</p>
                <p className="mb-4 text-xs leading-relaxed text-white/35">Buying signals, deployment stories, ROI benchmarks, and SCOUT activation prompts.</p>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className="w-full border border-white/10 px-3.5 py-2.5 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                  style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10 }}
                />
                {newsletterStatus === "success" && <p className="mt-3 text-xs" style={{ color: "#03DAC5" }}>Subscribed.</p>}
                {newsletterStatus === "error" && <p className="mt-3 text-xs text-red-300">Could not subscribe. Try again.</p>}
                <button type="submit" disabled={newsletterStatus === "submitting"} className="mt-3 w-full border px-4 py-2.5 text-sm font-bold transition-colors hover:bg-amber-400/6 disabled:opacity-50" style={{ color: "#FFB000", borderColor: "#FFB000", background: "transparent", borderRadius: 10 }}>
                  {newsletterStatus === "submitting" ? "Subscribing..." : "Subscribe Free"}
                </button>
              </form>
            </div>
          </section>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-5 text-sm">
            <Link href="/results?url=" className="inline-flex items-center gap-2 font-bold" style={{ color: "#FFB000" }}>
              Activate SCOUT from live intelligence <Send className="h-4 w-4" />
            </Link>
            <Link href="/signals" className="inline-flex items-center gap-2 font-bold text-white/50 hover:text-white/80">
              Browse signal types <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
