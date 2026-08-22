import { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Building2, FileText, Mail, Radio, Search, Send, Zap } from "lucide-react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import { JOBS_HEADER_OFFSET_CLASS } from "@/lib/jobsWorkflow";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanScrapedText } from "@/lib/text";

type Story = {
  title?: string;
  company?: string;
  summary?: string;
  score?: number;
};

const signalStats = [
  ["158", "enterprises analyzed"],
  ["437", "buying signals detected"],
  ["62%", "strong buying intent"],
];

const scoringModel = [
  {
    label: "Intent score",
    value: "40%",
    color: "#FFB000",
    copy: "Weights urgent public signals: labor gaps, expansion, CapEx, funding, executive hires, and robotics pilots.",
  },
  {
    label: "Robot fit",
    value: "30%",
    color: "#059669",
    copy: "Maps the buyer’s operating pain to robot categories like AMRs, service robots, cleaning, healthcare logistics, or food automation.",
  },
  {
    label: "Timing window",
    value: "20%",
    color: "#10b981",
    copy: "Prioritizes signals that imply a current buying window: new facility design, budget planning, staffing urgency, or active vendor review.",
  },
  {
    label: "Sales motion",
    value: "10%",
    color: "#34d399",
    copy: "Turns the signal into an action: who to contact, what proof point to lead with, and why now.",
  },
];

const EYEBROW = "text-[10px] font-semibold uppercase tracking-[0.15em]";

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

  const inputClass =
    "w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-emerald-400";

  return (
    <div className={`intelligence-page flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}>
      <ExperimentHeader />
      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow="ReadyForRobots"
        title={
          <span className="inline-flex items-center gap-4">
            <PixelIcon map={KARE_FACE} scale={3} fill={FACE_EMERALD} background="transparent" />
            <span className="font-display text-emerald-400">About</span>
          </span>
        }
        description={
          <>
            Labor pressure, expansion, CapEx, and deployment news — ranked as work robots can do, not as a generic sales dump.
          </>
        }
        innerClassName="pb-8"
      >
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {signalStats.map(([value, label]) => (
              <div key={label} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
                <div className={`font-mono text-xl font-black ${value === "62%" ? "text-amber-400" : "text-emerald-400"}`}>
                  {value}
                </div>
                <div className="mt-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">{label}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2.5 text-[13px]">
            <a href="#report" className="group inline-flex items-center gap-1.5 font-semibold text-emerald-400 transition-colors hover:text-emerald-300">
              Download report <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </a>
            <Link href="/signals" className="group inline-flex items-center gap-1.5 font-semibold text-slate-400 transition-colors hover:text-white">
              Explore robot signals <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link href="/signup" className="group inline-flex items-center gap-1.5 font-semibold text-amber-400 transition-colors hover:text-amber-300">
              Activate SIGNAL <Zap className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </PageHeroDark>
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 px-6 pb-20">
        <div className="max-w-6xl mx-auto">

          <section className="mb-12 overflow-hidden rounded-lg border border-slate-600 bg-[#0b162f]">
            <div className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="border-b border-gray-100 p-6 lg:border-b-0 lg:border-r">
                <p className={`mb-3 ${EYEBROW}`} style={{ color: "#FFB000" }}>Lead scoring model</p>
                <h2 className="max-w-xl font-display text-xl font-bold leading-tight text-white lg:text-2xl">
                  We score the work first, then match it to a robot that can do the job.
                </h2>
                <p className="mt-4 max-w-xl text-[13px] leading-relaxed text-gray-500">
                  SIGNAL does not treat every lead as equal. It ranks the company’s buying intent, the operational problem, and the timing window, then compares that profile against the robot category or vendor URL you submit.
                </p>
                <div className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-md border border-slate-600 bg-[#081126]">
                  {[
                    ["HOT", "Act now"],
                    ["WARM", "Sequence"],
                    ["EMERGING", "Watch"],
                    ["PARTNER", "Channel fit"],
                  ].map(([tier, action]) => (
                    <div key={tier} className="p-3 bg-[#0b162f]">
                      <p className="font-mono text-[13px] font-bold" style={{ color: tier === "HOT" ? "#FFB000" : "#059669", fontFamily: "'JetBrains Mono', monospace" }}>{tier}</p>
                      <p className="mt-0.5 text-[11px] text-gray-600">{action}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6">
                <div className="space-y-3.5">
                  {scoringModel.map((item) => (
                    <div key={item.label}>
                      <div className="mb-1.5 flex items-start justify-between gap-4">
                        <div>
                          <p className="text-[13px] font-semibold text-slate-100">{item.label}</p>
                          <p className="mt-0.5 text-xs leading-relaxed text-gray-500">{item.copy}</p>
                        </div>
                        <span className="shrink-0 font-mono text-[13px] font-bold" style={{ color: item.color, fontFamily: "'JetBrains Mono', monospace" }}>{item.value}</span>
                      </div>
                      <div className="h-1 overflow-hidden rounded-full bg-gray-100">
                        <div className="h-full rounded-full" style={{ width: item.value, background: item.color }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-r border-l-2 bg-amber-400/[0.04] px-3.5 py-2.5" style={{ borderColor: "#FFB000" }}>
                  <p className="text-[13px] leading-relaxed" style={{ color: "#FFB000" }}>
                    Example: a warehouse expansion plus automation hiring scores differently for an AMR vendor than it does for a surgical robotics company. The lead stays the same; the opportunity ranking changes based on robot fit.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section id="report" className="mb-12 grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-slate-600 lg:grid-cols-[1fr_360px] bg-[#081126]">
            <div className="p-6 bg-[#0b162f]">
              <p className={`mb-3 ${EYEBROW}`} style={{ color: "#34d399" }}>Enterprise Intelligence Report</p>
              <h2 className="max-w-2xl font-display text-2xl font-bold leading-tight text-white lg:text-3xl">
                The Automation Imperative: labor-intensive industries are flashing buy signals.
              </h2>
              <p className="mt-4 max-w-2xl text-[13px] leading-relaxed text-slate-400">
                Built from real ReadyForRobots signal data: <span className="text-slate-200">158 enterprises</span>, <span className="text-slate-200">437 buying signals</span>, and sector-level ROI patterns for robotics vendors selling into labor-constrained operations.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
                {[
                  ["Logistics", "leading adoption"],
                  ["Labor shortage", "highest-intent trigger"],
                  ["ROI models", "sales narrative ready"],
                ].map(([label, copy]) => (
                  <div key={label} className="border-l px-3 py-1.5" style={{ borderColor: "rgba(3,218,197,0.45)" }}>
                    <p className="text-[13px] font-semibold text-slate-100">{label}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{copy}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-5 bg-[#081126]">
              <div className="mb-4 flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-md border" style={{ borderColor: "rgba(52,211,153,0.35)", background: "rgba(52,211,153,0.07)" }}>
                  <FileText className="h-4 w-4" style={{ color: "#34d399" }} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-white">Download the 2026 report</p>
                  <p className="text-[11px] text-slate-400">No padded buttons. Just the data.</p>
                </div>
              </div>
              {reportStatus === "success" ? (
                <div className="rounded-md border border-teal-300/20 px-3.5 py-3 text-[13px]" style={{ color: "#99f6e4", background: "rgba(3,218,197,0.06)" }}>
                  Report requested. We saved your request and queued the follow-up email.
                </div>
              ) : (
                <form onSubmit={requestReport} className="space-y-2.5">
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
                      className={inputClass}
                    />
                  ))}
                  {reportStatus === "error" && <p className="text-xs text-red-300">Could not request report. Try again.</p>}
                  <button
                    type="submit"
                    disabled={reportStatus === "submitting"}
                    className="group inline-flex items-center gap-1.5 pt-1 text-[13px] font-semibold transition-colors hover:text-teal-200 disabled:opacity-50"
                    style={{ color: "#059669" }}
                  >
                    {reportStatus === "submitting" ? "Requesting…" : "Download free report"}
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </button>
                </form>
              )}
            </div>
          </section>

          <section className="mb-12 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: Search, title: "Source", copy: "Industry news, job posts, filings, earnings calls, permits, and trade signals." },
              { icon: Radio, title: "Signal", copy: "SIGNAL identifies the public clues that point to automation readiness." },
              { icon: BarChart3, title: "Rank", copy: "Scores prioritize timing, pain intensity, fit, and deal motion." },
              { icon: Building2, title: "Identify", copy: "Sales leads and partnership opportunities become next actions." },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="rounded-lg border border-slate-600 bg-[#0b162f] p-4 transition-colors hover:border-emerald-400/40">
                  <Icon className="mb-4 h-[18px] w-[18px]" style={{ color: item.title === "Rank" ? "#FFB000" : "#34d399" }} />
                  <p className="mb-1 text-[13px] font-semibold text-white">{item.title}</p>
                  <p className="text-[13px] leading-relaxed text-slate-400">{item.copy}</p>
                </div>
              );
            })}
          </section>

          <section id="brief" className="rounded-lg border border-slate-600 bg-[#0b162f] p-6">
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_300px]">
              <div>
                <p className={`mb-2.5 ${EYEBROW}`} style={{ color: "#34d399" }}>Robot Intelligence Brief</p>
                <h2 className="max-w-2xl font-display text-2xl font-bold leading-tight text-white">
                  A weekly brief that keeps the market warm between sales cycles.
                </h2>
                <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-gray-500">
                  Each issue packages new signals, deployment stories, vendor movement, and ROI language so teams know where to act before the market does.
                </p>
                {stories.length > 0 && (
                  <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
                    {stories.slice(0, 3).map((story, i) => (
                      <div key={`${story.title || story.company || i}`} className="rounded-md border border-slate-600 bg-[#081126] p-3.5">
                        <p className="break-words mb-1.5 text-[13px] font-semibold text-slate-100">{cleanScrapedText(story.title || story.company) || "Signal story"}</p>
                        <p className="break-words text-xs leading-relaxed text-gray-500">{cleanScrapedText(story.summary) || "Fresh signal intelligence from ReadyForRobots."}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <form onSubmit={subscribe} className="rounded-md border border-slate-600 bg-[#081126] p-4">
                <Mail className="mb-3 h-[18px] w-[18px]" style={{ color: "#34d399" }} />
                <p className="mb-1.5 text-[13px] font-semibold text-white">Subscribe free</p>
                <p className="mb-3.5 text-xs leading-relaxed text-gray-500">Buying signals, deployment stories, ROI benchmarks, and SIGNAL activation prompts.</p>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className={inputClass}
                />
                {newsletterStatus === "success" && <p className="mt-2.5 text-xs" style={{ color: "#059669" }}>Subscribed.</p>}
                {newsletterStatus === "error" && <p className="mt-2.5 text-xs text-red-300">Could not subscribe. Try again.</p>}
                <button
                  type="submit"
                  disabled={newsletterStatus === "submitting"}
                  className="group mt-3 inline-flex items-center gap-1.5 text-[13px] font-semibold transition-colors hover:text-amber-300 disabled:opacity-50"
                  style={{ color: "#FFB000" }}
                >
                  {newsletterStatus === "submitting" ? "Subscribing…" : "Subscribe free"}
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                </button>
              </form>
            </div>
          </section>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-5 text-[13px]">
            <Link href="/signup" className="group inline-flex items-center gap-1.5 font-semibold transition-colors" style={{ color: "#FFB000" }}>
              Activate SIGNAL from live intelligence <Send className="h-3.5 w-3.5" />
            </Link>
            <Link href="/signals" className="group inline-flex items-center gap-1.5 font-semibold text-slate-400 transition-colors hover:text-white">
              Browse signal types <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
