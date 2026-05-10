import { useEffect, useState } from "react";
import { ArrowRight, BarChart3, FileText, Mail, Radio, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

type Story = {
  title?: string;
  company?: string;
  summary?: string;
  score?: number;
};

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
      <main className="flex-1 pt-28 pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          <section className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-10 items-start mb-16">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-4" style={{ color: "#03DAC5" }}>
                ReadyForRobots Intelligence
              </p>
              <h1 className="font-extrabold text-white leading-tight mb-5" style={{ fontSize: "clamp(2.4rem, 5vw, 4.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                Buying signals, deployment stories, and robotics ROI benchmarks.
              </h1>
              <p className="text-white/45 text-base leading-relaxed max-w-2xl mb-8">
                The same intelligence that powers SCOUT becomes a market brief for robotics sales leaders: where labor pressure is rising, which companies are showing intent, and how automation deals are being justified.
              </p>
              <div className="grid grid-cols-3 gap-px max-w-xl" style={{ background: "rgba(255,255,255,0.08)" }}>
                {[
                  ["158", "enterprises analyzed"],
                  ["437", "signals detected"],
                  ["62%", "strong buying intent"],
                ].map(([value, label]) => (
                  <div key={label} className="p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
                    <p className="font-mono text-2xl font-bold" style={{ color: "#03DAC5", fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
                    <p className="text-[11px] text-white/35 mt-1">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 p-6" style={{ background: "rgba(255,255,255,0.04)" }}>
              <div className="flex items-center gap-3 mb-5">
                <div className="h-10 w-10 rounded-2xl flex items-center justify-center" style={{ background: "rgba(3,218,197,0.12)" }}>
                  <FileText className="h-5 w-5" style={{ color: "#03DAC5" }} />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">Download the 2026 report</p>
                  <p className="text-xs text-white/35">Enterprise signal analysis and ROI benchmarks.</p>
                </div>
              </div>
              {reportStatus === "success" ? (
                <div className="rounded-2xl border border-teal-300/20 p-4 text-sm" style={{ color: "#99f6e4", background: "rgba(3,218,197,0.06)" }}>
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
                      className="w-full rounded-xl border border-white/10 px-4 py-3 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                      style={{ background: "rgba(255,255,255,0.04)" }}
                    />
                  ))}
                  {reportStatus === "error" && <p className="text-xs text-red-300">Could not request report. Try again.</p>}
                  <button type="submit" disabled={reportStatus === "submitting"} className="w-full rounded-xl px-4 py-3 text-sm font-bold disabled:opacity-50" style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "rgba(3,218,197,0.05)" }}>
                    {reportStatus === "submitting" ? "Requesting..." : "Download Free Report"}
                  </button>
                </form>
              )}
            </div>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-16">
            {[
              { icon: Radio, title: "Signal detection", copy: "Labor shortage, expansion, CapEx, automation hiring, leadership change, and safety signals." },
              { icon: BarChart3, title: "ROI benchmarks", copy: "Vertical-specific payback assumptions SCOUT can use in buyer messaging and proposal narratives." },
              { icon: Zap, title: "SCOUT activation", copy: "Every issue points back to live opportunities that can be added to your pipeline." },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="rounded-2xl border border-white/8 p-6" style={{ background: "rgba(255,255,255,0.03)" }}>
                  <Icon className="h-5 w-5 mb-5" style={{ color: "#a78bfa" }} />
                  <p className="text-sm font-bold text-white mb-2">{item.title}</p>
                  <p className="text-sm text-white/40 leading-relaxed">{item.copy}</p>
                </div>
              );
            })}
          </section>

          <section className="rounded-3xl border border-white/10 p-6 lg:p-8" style={{ background: "rgba(255,255,255,0.04)" }}>
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-8">
              <div className="flex-1">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>Robot Intelligence Brief</p>
                <h2 className="text-2xl font-extrabold text-white mb-3" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Weekly market intelligence for robotics sales teams.
                </h2>
                <p className="text-sm text-white/40 max-w-2xl mb-6">
                  Get the freshest buying signals, deployment stories, vendor movement, and ROI benchmarks before they become stale lead-list data.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {(stories.length ? stories : [
                    { title: "Marriott/Savioke expansion", summary: "Hospitality deployment signals continue to show labor-pressure pull." },
                    { title: "Logistics leads adoption", summary: "Warehouse and fulfillment operators show the highest signal density." },
                    { title: "ROI pressure rises", summary: "Buyers are framing robotics around payback and staffing resilience." },
                  ]).slice(0, 3).map((story, i) => (
                    <div key={`${story.title || story.company || i}`} className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
                      <p className="text-sm font-bold text-white/80 mb-2">{story.title || story.company || "Signal story"}</p>
                      <p className="text-xs text-white/35 leading-relaxed">{story.summary || "Fresh signal intelligence from ReadyForRobots."}</p>
                    </div>
                  ))}
                </div>
              </div>
              <form onSubmit={subscribe} className="w-full lg:w-[340px] rounded-2xl border border-white/8 p-5" style={{ background: "rgba(13,5,32,0.5)" }}>
                <Mail className="h-5 w-5 mb-4" style={{ color: "#03DAC5" }} />
                <p className="text-sm font-bold text-white mb-2">Subscribe free</p>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className="w-full rounded-xl border border-white/10 px-4 py-3 text-sm text-white placeholder-white/25 outline-none focus:border-teal-300/50"
                  style={{ background: "rgba(255,255,255,0.04)" }}
                />
                {newsletterStatus === "success" && <p className="mt-3 text-xs" style={{ color: "#03DAC5" }}>Subscribed.</p>}
                {newsletterStatus === "error" && <p className="mt-3 text-xs text-red-300">Could not subscribe. Try again.</p>}
                <button type="submit" disabled={newsletterStatus === "submitting"} className="mt-3 w-full rounded-xl px-4 py-3 text-sm font-bold disabled:opacity-50" style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}>
                  {newsletterStatus === "submitting" ? "Subscribing..." : "Subscribe Free"}
                </button>
              </form>
            </div>
          </section>

          <div className="mt-10 text-center">
            <Link href="/results?url=" className="inline-flex items-center gap-2 text-sm font-bold" style={{ color: "#FFB000" }}>
              Activate SCOUT from live intelligence <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
