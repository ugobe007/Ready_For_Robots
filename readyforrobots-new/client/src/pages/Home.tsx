/**
 * Home — Precision Intelligence redesign (emerald light SaaS)
 * Wired to live pipeline stats, homepage leads, newsletter, and report APIs.
 */
import { useEffect, useState } from "react";
import { ArrowRight, ChevronRight, X, Zap } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import HumanoidDailyRecap from "@/components/HumanoidDailyRecap";
import HumanoidBenchmarkMarquee from "@/components/HumanoidBenchmarkMarquee";
import MarketingHeroPipeline from "@/components/marketing/MarketingHeroPipeline";
import MarketingLivePipelineSection from "@/components/marketing/MarketingLivePipelineSection";
import MarketingDailyBrief from "@/components/marketing/MarketingDailyBrief";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import {
  MarketingBeforeAfter,
  MarketingBenchmark,
  MarketingCaseStudies,
  MarketingFinalCTA,
  MarketingHowItWorks,
  MarketingReportSection,
  MarketingTestimonials,
  MarketingWhatSignalDoes,
} from "@/components/marketing/MarketingSections";
import { LiveDot } from "@/components/marketing/primitives";
import { usePipelineStats, formatStat } from "@/hooks/usePipelineStats";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

const HERO_BG =
  "https://d2xsxph8kpxj0f.cloudfront.net/310519663452998285/bZbY4XZf5ZnDvj8w6Dq8Cf/rfr-hero-bg-4bNqTqw4cnY6Gmaq7G9bQp.webp";

type NewsletterEdition = {
  latestEdition?: { headline?: string; subheadline?: string };
  topStories?: { category?: string; company?: string; headline?: string; snippet?: string; summary?: string }[];
};

type HumanoidBenchReport = {
  title?: string;
  total_robots?: number;
  overall_leader?: { name?: string; vendor?: string; score?: number };
};

export default function Home() {
  const { hot, total } = usePipelineStats();
  const [reportOpen, setReportOpen] = useState(false);
  const [reportForm, setReportForm] = useState({ name: "", email: "", company: "", robotCategory: "" });
  const [reportStatus, setReportStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [newsletterStatus, setNewsletterStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [dailyBrief, setDailyBrief] = useState<NewsletterEdition | null>(null);
  const [benchReport, setBenchReport] = useState<HumanoidBenchReport | null>(null);

  const hotLabel = formatStat(hot, "319");

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/newsletter/edition?limit=3`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data?.topStories) setDailyBrief(data);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/humanoid/report`, liveFetchInit())
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data?.report) setBenchReport(data.report);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function submitReportDownload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!reportForm.email.trim()) return;
    setReportStatus("submitting");
    try {
      const res = await fetch(
        `${getApiBase()}/api/leads/report-download`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(reportForm),
        }),
      );
      if (!res.ok) throw new Error("Report request failed");
      setReportStatus("success");
    } catch {
      setReportStatus("error");
    }
  }

  async function submitNewsletter(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    setNewsletterStatus("submitting");
    try {
      const res = await fetch(
        `${getApiBase()}/api/newsletter/subscribe`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: newsletterEmail, source: "homepage_footer" }),
        }),
      );
      if (!res.ok) throw new Error("Newsletter signup failed");
      setNewsletterStatus("success");
      setNewsletterEmail("");
    } catch {
      setNewsletterStatus("error");
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <section
        id="hero-cta"
        className="relative pt-28 pb-20 overflow-hidden"
        style={{
          backgroundImage: `url(${HERO_BG})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full text-xs font-medium text-emerald-700 mb-6">
                <LiveDot />
                <span className="font-mono-data">{hotLabel} hot leads active now</span>
              </div>

              <h1 className="font-display text-5xl lg:text-6xl font-bold text-gray-900 leading-[1.08] tracking-tight mb-6">
                Close Robot Deals{" "}
                <span className="text-emerald-600">Before the RFP Drops</span>
              </h1>

              <p className="text-lg text-gray-600 leading-relaxed mb-8 max-w-lg">
                SIGNAL scans 150+ live sources to surface automation-ready buyers — scored, briefed, and ready to
                contact. You approve. You show up. That&apos;s it.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 mb-6">
                <Link
                  href="/results?url="
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-all duration-150 active:scale-[0.97] shadow-md hover:shadow-lg text-base"
                >
                  <Zap size={18} />
                  Activate SIGNAL
                  <ArrowRight size={16} />
                </Link>
                <Link
                  href="/signup?next=/pipeline"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-white hover:bg-gray-50 text-gray-800 font-semibold rounded-xl border border-gray-200 transition-all duration-150 active:scale-[0.97] text-base"
                >
                  Start free workspace
                  <ChevronRight size={16} />
                </Link>
              </div>

              <p className="text-xs text-gray-400 font-medium">
                No signup required · Free to start · Results in seconds
              </p>
            </div>

            <div className="animate-fade-in-up" style={{ animationDelay: "120ms" }}>
              <MarketingHeroPipeline hotCount={hot} totalCount={total} />
            </div>
          </div>
        </div>
      </section>

      <div id="about">
        <MarketingWhatSignalDoes hotCount={hot} totalCount={total} />
      </div>
      <MarketingHowItWorks />
      <MarketingLivePipelineSection hotCount={hot} totalCount={total} />
      <MarketingBeforeAfter />
      <MarketingCaseStudies />
      <MarketingTestimonials />

      <HumanoidDailyRecap className="py-8 border-y border-gray-100 bg-slate-50" />
      <HumanoidBenchmarkMarquee compact />

      <MarketingBenchmark benchReport={benchReport} />
      <MarketingDailyBrief
        dailyBrief={dailyBrief}
        newsletterEmail={newsletterEmail}
        newsletterStatus={newsletterStatus}
        onEmailChange={setNewsletterEmail}
        onSubmit={submitNewsletter}
      />
      <MarketingReportSection onOpenReport={() => setReportOpen(true)} />
      <MarketingFinalCTA hotCount={hot} totalCount={total} />
      <MarketingFooter
        newsletterEmail={newsletterEmail}
        newsletterStatus={newsletterStatus}
        onEmailChange={setNewsletterEmail}
        onSubmit={submitNewsletter}
      />

      {reportOpen && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center px-4 bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-3xl border border-gray-200 bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4 mb-5">
              <div>
                <p className="section-eyebrow mb-2">Free Report</p>
                <h3 className="text-2xl font-display font-bold text-gray-900">Download the Automation Imperative</h3>
                <p className="mt-2 text-sm text-gray-600">
                  Get the enterprise intelligence report and join the Robot Intelligence Brief.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setReportOpen(false)}
                className="rounded-xl p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-100"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {reportStatus === "success" ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <p className="font-bold text-emerald-700">Report requested.</p>
                <p className="mt-2 text-sm text-gray-600">
                  We saved your request and will send the report using the configured ReadyForRobots email sender.
                </p>
              </div>
            ) : (
              <form onSubmit={submitReportDownload} className="space-y-3">
                {(
                  [
                    ["name", "Name", "text"],
                    ["email", "Work email", "email"],
                    ["company", "Company", "text"],
                    ["robotCategory", "Robot category", "text"],
                  ] as const
                ).map(([key, label, type]) => (
                  <label key={key} className="block">
                    <span className="mb-1.5 block text-xs font-semibold text-gray-500">{label}</span>
                    <input
                      type={type}
                      required={key === "email"}
                      value={reportForm[key]}
                      onChange={(e) => setReportForm((current) => ({ ...current, [key]: e.target.value }))}
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-900 outline-none focus:border-emerald-500"
                    />
                  </label>
                ))}
                {reportStatus === "error" && (
                  <p className="text-xs text-red-600">Could not request the report. Please try again.</p>
                )}
                <button
                  type="submit"
                  disabled={reportStatus === "submitting"}
                  className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white transition-all hover:bg-emerald-700 disabled:opacity-50"
                >
                  {reportStatus === "submitting" ? "Requesting..." : "Download Free Report"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
