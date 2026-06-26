/**
 * Home — Precision Intelligence redesign (emerald light SaaS)
 * Wired to live pipeline stats, homepage leads, newsletter, and report APIs.
 */
import { useEffect, useState } from "react";
import { ArrowRight, ChevronRight, X } from "lucide-react";
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
  MarketingNewsletterBand,
  MarketingPricing,
  MarketingReportSection,
  MarketingTestimonials,
  MarketingWhatSignalDoes,
} from "@/components/marketing/MarketingSections";
import HeroUrlScan from "@/components/marketing/HeroUrlScan";
import { LiveDot } from "@/components/marketing/primitives";
import { usePipelineStats, formatStat } from "@/hooks/usePipelineStats";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";

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
  const { hot, total, totalSignals } = usePipelineStats();
  const [reportOpen, setReportOpen] = useState(false);
  const [reportForm, setReportForm] = useState({ name: "", email: "", company: "", robotCategory: "" });
  const [reportStatus, setReportStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [newsletterStatus, setNewsletterStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [dailyBrief, setDailyBrief] = useState<NewsletterEdition | null>(null);
  const [benchReport, setBenchReport] = useState<HumanoidBenchReport | null>(null);

  const hotLabel = formatStat(hot, "319");
  const signalsLabel = formatStat(totalSignals, "2,000+");

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
          body: JSON.stringify({ email: newsletterEmail, source: "homepage_newsletter_band" }),
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
        className="relative pt-24 pb-14 sm:pt-28 sm:pb-20 overflow-hidden hero-mesh-bg"
      >
        <div className="absolute inset-0 hero-grid-texture pointer-events-none" aria-hidden />
        <div
          className="absolute inset-0 opacity-[0.35] pointer-events-none mix-blend-soft-light"
          aria-hidden
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, rgba(16,185,129,0.15) 0%, transparent 40%), radial-gradient(circle at 80% 70%, rgba(5,150,105,0.1) 0%, transparent 35%)",
          }}
        />

        <div className="container relative">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-16 items-center">
            <div className="animate-fade-in-up order-1">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-50/90 border border-emerald-200 rounded-full text-xs font-medium text-emerald-700 mb-5 sm:mb-6">
                <LiveDot />
                <span className="font-mono-data">
                  {hotLabel} HOT · {signalsLabel} live signals · updated daily
                </span>
              </div>

              <h1 className="hero-display font-bold text-gray-900 mb-5 sm:mb-6">
                Automate Your{" "}
                <span className="text-emerald-600">Sales Pipeline.</span>
              </h1>

              <p className="text-base sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8 max-w-lg">
                <span className="font-semibold text-gray-800">SIGNAL</span> monitors 150+ live sources to surface
                automation-ready buyers — scored, briefed, and ready to contact. You approve. You show up. That&apos;s
                it.
              </p>

              <HeroUrlScan />

              <Link href="/pipeline" className="btn-secondary-hero mb-4">
                Browse the pipeline free
                <ChevronRight size={16} className="btn-arrow" />
              </Link>

              <p className="text-xs text-gray-500 font-medium mb-1">
                No signup required · Free to start · Results in seconds
              </p>
              <Link href="#live-pipeline" className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 inline-flex items-center gap-1">
                View live pipeline <ArrowRight size={12} />
              </Link>
            </div>

            <div className="animate-fade-in-up order-2 lg:order-2" style={{ animationDelay: "120ms" }}>
              <div className="relative max-md:mt-2">
                <div
                  className="absolute -inset-3 sm:-inset-5 rounded-3xl bg-emerald-300/35 blur-2xl sm:blur-3xl pointer-events-none"
                  aria-hidden
                />
                <div className="relative">
                  <MarketingHeroPipeline hotCount={hot} totalCount={total} />
                </div>
              </div>
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
      <MarketingPricing />
      <MarketingFinalCTA hotCount={hot} totalCount={total} />
      <MarketingNewsletterBand
        newsletterEmail={newsletterEmail}
        newsletterStatus={newsletterStatus}
        onEmailChange={setNewsletterEmail}
        onSubmit={submitNewsletter}
      />
      <MarketingFooter />

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
