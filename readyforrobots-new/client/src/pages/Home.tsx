/**
 * Home — Precision Intelligence redesign (emerald light SaaS)
 * Wired to live pipeline stats, homepage leads, newsletter, and report APIs.
 */
import { useEffect, useState } from "react";
import { ArrowRight, X } from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import HumanoidDailyRecap from "@/components/HumanoidDailyRecap";
import HumanoidBenchmarkMarquee from "@/components/HumanoidBenchmarkMarquee";
import MarketingHeroPipeline from "@/components/marketing/MarketingHeroPipeline";
import MarketingLivePipelineSection from "@/components/marketing/MarketingLivePipelineSection";
import MarketingDailyBrief from "@/components/marketing/MarketingDailyBrief";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import {
  MarketingBenchmark,
  MarketingCaseStudies,
  MarketingFinalCTA,
  MarketingHowItWorks,
  MarketingNewsletterBand,
  MarketingPricing,
  MarketingReportSection,
  MarketingWhatSignalDoes,
} from "@/components/marketing/MarketingSections";
import HeroUrlScan from "@/components/marketing/HeroUrlScan";
import { LiveDot } from "@/components/marketing/primitives";
import { usePipelineStats, formatStat } from "@/hooks/usePipelineStats";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { trackMarketingEvent } from "@/lib/siteAnalytics";

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
  const totalLabel = formatStat(total, "3,957");

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
    trackMarketingEvent("home_report_submit_start", {
      has_name: Boolean(reportForm.name.trim()),
      has_company: Boolean(reportForm.company.trim()),
      has_robot_category: Boolean(reportForm.robotCategory.trim()),
    });
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
      trackMarketingEvent("home_report_submit_success");
    } catch {
      setReportStatus("error");
      trackMarketingEvent("home_report_submit_error");
    }
  }

  async function submitNewsletter(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    trackMarketingEvent("home_newsletter_submit_start", { source: "homepage_newsletter_band" });
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
      trackMarketingEvent("home_newsletter_submit_success", { source: "homepage_newsletter_band" });
      setNewsletterEmail("");
    } catch {
      setNewsletterStatus("error");
      trackMarketingEvent("home_newsletter_submit_error", { source: "homepage_newsletter_band" });
    }
  }

  function openReportModal() {
    trackMarketingEvent("home_report_modal_open", { source: "homepage_report_section" });
    setReportOpen(true);
  }

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <section
        id="hero-cta"
        className="relative overflow-hidden pt-14 pb-10 sm:pt-16 sm:pb-12 home-hero-bg"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-slate-950/55 to-transparent" aria-hidden />
        <div className="home-hero-grid" aria-hidden />
        <div className="home-hero-glow-orb -top-24 right-[8%] h-72 w-72 bg-emerald-500/[0.14]" aria-hidden />
        <div className="home-hero-glow-orb home-hero-orb-delay bottom-[-6rem] left-[-4rem] h-80 w-80 bg-sky-500/[0.1]" aria-hidden />

        <div className="container home-hero-container relative">
          <div className="grid items-center gap-6 lg:grid-cols-12 lg:gap-5 xl:gap-6">
            <div className="animate-fade-in-up order-1 lg:col-span-7">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-300/25 bg-emerald-400/[0.08] px-3.5 py-1.5 text-[11px] font-semibold text-emerald-100 shadow-[0_0_24px_-8px_rgba(16,185,129,0.45)] backdrop-blur-sm sm:mb-5">
                <LiveDot />
                <span className="font-mono-data">
                  {hotLabel} HOT · {signalsLabel} live signals · updated daily
                </span>
              </div>

              <h1 className="home-hero-title mb-4 max-w-[13.2ch] font-bold sm:mb-5">
                Deployment Intelligence
                <span className="home-hero-title-accent"> for Robotics.</span>
              </h1>

              <p className="home-hero-lead mb-3 max-w-2xl text-lg leading-relaxed text-slate-100 sm:mb-4 sm:text-[1.34rem] sm:leading-[1.45]">
                <span className="font-semibold text-slate-50">ReadyForRobots</span> helps robot companies identify organizations entering the automation buying cycle.
              </p>

              <p className="mb-4 max-w-2xl text-sm leading-relaxed text-slate-300 sm:mb-5 sm:text-base">
                By analyzing operational, workforce, investment, and market signals, we reveal where robots are most likely to deliver value and when buyers are most likely to act.
              </p>

              <HeroUrlScan onDark />

              <p className="mb-4 max-w-lg text-xs leading-relaxed text-slate-400 sm:mb-6 sm:text-sm">
                Enter your company website to generate your first deployment pipeline.
              </p>
            </div>

            <div className="animate-fade-in-up order-2 lg:col-span-5 lg:order-2" style={{ animationDelay: "120ms" }}>
              <div className="relative max-md:mt-2">
                <div className="relative home-hero-pipeline-shell lg:-ml-4 lg:max-w-[36rem] lg:origin-right lg:scale-[0.98] xl:-ml-6 xl:max-w-[37rem] xl:scale-100">
                  <MarketingHeroPipeline hotCount={hot} totalCount={total} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="home-hero-fade" aria-hidden />
      <div className="home-hero-divider" aria-hidden />

      <div id="about">
        <MarketingWhatSignalDoes hotCount={hot} totalCount={total} />
      </div>
      <MarketingHowItWorks />
      <MarketingCaseStudies />
      <MarketingLivePipelineSection hotCount={hot} totalCount={total} />

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
      <MarketingReportSection onOpenReport={openReportModal} />
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
                      className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-900 outline-none focus:border-sky-500"
                    />
                  </label>
                ))}
                {reportStatus === "error" && (
                  <p className="text-xs text-red-600">Could not request the report. Please try again.</p>
                )}
                <button
                  type="submit"
                  disabled={reportStatus === "submitting"}
                  className="w-full rounded-xl bg-amber-500 px-4 py-3 text-sm font-bold text-slate-950 transition-all hover:bg-amber-400 disabled:opacity-50"
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
