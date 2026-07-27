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
  MarketingVsGenericAI,
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
        className="relative overflow-hidden pt-24 pb-14 sm:pt-28 sm:pb-20 home-hero-bg"
      >
        <div className="pointer-events-none absolute -top-28 right-[-10%] h-80 w-80 rounded-full bg-emerald-300/35 blur-3xl home-hero-orb" aria-hidden />
        <div className="pointer-events-none absolute bottom-[-7rem] left-[-8%] h-72 w-72 rounded-full bg-sky-200/45 blur-3xl home-hero-orb home-hero-orb-delay" aria-hidden />
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-white/75 to-transparent" aria-hidden />

        <div className="container relative">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-16 items-center">
            <div className="animate-fade-in-up order-1">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-[11px] font-semibold text-emerald-900 sm:mb-6">
                <LiveDot />
                <span className="font-mono-data">
                  {hotLabel} HOT · {signalsLabel} live signals · updated daily
                </span>
              </div>

              <h1 className="home-hero-title mb-5 font-bold sm:mb-6">
                Find Robot-Ready Buyers
                <span className="text-emerald-700"> in Minutes, Not Weeks.</span>
              </h1>

              <p className="home-hero-lead mb-6 max-w-lg text-base leading-relaxed sm:mb-8 sm:text-lg">
                <span className="font-semibold text-slate-900">SIGNAL</span> helps robot OEM and integration teams
                prioritize accounts with active buying signals, generate outreach-ready context, and move deals forward
                in CRM without manual list building.
              </p>

              <ul className="home-hero-list mb-6 max-w-xl space-y-1.5 text-xs sm:text-sm">
                <li>• {hotLabel} HOT accounts showing near-term automation intent</li>
                <li>• {signalsLabel} cited signals mapped to why-now buying pressure</li>
                <li>• {totalLabel} scored opportunities ready for outreach triage</li>
              </ul>

              <HeroUrlScan onDark />

              <Link
                href="/pipeline"
                className="home-hero-cta mb-4"
                onClick={() => trackMarketingEvent("home_cta_pipeline_click", { location: "hero" })}
              >
                Browse the pipeline free
                <ChevronRight size={16} className="btn-arrow" />
              </Link>

              <p className="mb-1 text-xs font-medium text-slate-500">
                No signup required · Free to start · Results in seconds
              </p>
              <Link
                href="#live-pipeline"
                className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
                onClick={() => trackMarketingEvent("home_cta_live_pipeline_anchor_click", { location: "hero" })}
              >
                View live pipeline <ArrowRight size={12} />
              </Link>
            </div>

            <div className="animate-fade-in-up order-2 lg:order-2" style={{ animationDelay: "120ms" }}>
              <div className="relative max-md:mt-2">
                <div
                  className="pointer-events-none absolute -inset-3 rounded-3xl bg-emerald-200/70 blur-2xl sm:-inset-5 sm:blur-3xl"
                  aria-hidden
                />
                <div className="relative home-hero-pipeline-shell">
                  <MarketingHeroPipeline hotCount={hot} totalCount={total} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="home-hero-fade" aria-hidden />

      <div id="about">
        <MarketingWhatSignalDoes hotCount={hot} totalCount={total} />
      </div>
      <MarketingHowItWorks />
      <MarketingLivePipelineSection hotCount={hot} totalCount={total} />
      <MarketingBeforeAfter />
      <MarketingVsGenericAI />
      <MarketingCaseStudies />

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
