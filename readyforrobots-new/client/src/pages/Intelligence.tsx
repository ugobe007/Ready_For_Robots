/**
 * About (`/intelligence`) — Jobs chrome. Robot URL → jobs → CRM.
 * Upgraded design with modern glassmorphism, dynamic glowing cards,
 * responsive visual hierarchy, and smooth micro-animations.
 */
import { useEffect, useState } from "react";
import { ArrowRight, Building2, Check, FileText, Mail, Search, Sparkles } from "lucide-react";
import { Link } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import JobsPstackProtocol from "@/components/JobsPstackProtocol";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  CRM_UNLOCKED_JOBS,
  FIND_JOBS_CTA,
  JOBS_EXAMPLE_CAP,
  JOBS_FOR_YOUR_ROBOT_HEADING,
  JOBS_HEADER_OFFSET_CLASS,
  JOBS_PROCESS_STEPS,
  jobsCrmOpenHref,
} from "@/lib/jobsWorkflow";
import { jobsFindHref } from "@/lib/jobsLanding";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { cleanScrapedText } from "@/lib/text";

type Story = {
  title?: string;
  company?: string;
  summary?: string;
  score?: number;
};

const ABOUT_STATS = [
  ["01", JOBS_PROCESS_STEPS[0].label],
  ["02", JOBS_PROCESS_STEPS[1].label],
  ["03", JOBS_PROCESS_STEPS[2].label],
] as const;

const JOBS_LOOP = [
  {
    icon: Search,
    title: "FIND",
    copy: "Paste a robot URL. We read the SKU — not a category guess.",
  },
  {
    icon: Building2,
    title: "JOBS",
    copy: `Inspect ${JOBS_EXAMPLE_CAP} employment cards: employer, workplace, work.`,
  },
  {
    icon: FileText,
    title: "CARDS",
    copy: "Cards stay Conditional until there is evidence. Qualification is explainable, never a %.",
  },
  {
    icon: Mail,
    title: "CRM",
    copy: `Keep ${CRM_UNLOCKED_JOBS} opportunities on free. Run the next robot the same way.`,
  },
];

const EYEBROW = "font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-400";
const JOBS_SIGNUP_HREF = jobsCrmOpenHref(false);

export default function Intelligence() {
  const [stories, setStories] = useState<Story[]>([]);
  const [email, setEmail] = useState("");
  const [reportForm, setReportForm] = useState({
    name: "",
    email: "",
    company: "",
    robotCategory: "",
    website: "",
  });
  const [newsletterStatus, setNewsletterStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");
  const [reportStatus, setReportStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");

  useEffect(() => {
    let cancelled = false;
    fetch(`${getApiBase()}/api/newsletter/edition?limit=3`, liveFetchInit())
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
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
      const res = await fetch(
        `${getApiBase()}/api/newsletter/subscribe`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, source: "intelligence_page" }),
        })
      );
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
      const res = await fetch(
        `${getApiBase()}/api/leads/report-download`,
        liveFetchInit({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(reportForm),
        })
      );
      if (!res.ok) throw new Error("Report request failed");
      setReportStatus("success");
    } catch {
      setReportStatus("error");
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700/70 bg-[#070e20] px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all duration-150 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20";

  return (
    <div
      className={`intelligence-page flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />

      {/* Hero Beat */}
      <div className="relative overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-950/30 via-[#060b18] to-[#060b18]">
        <PageHeroDark
          maxWidthClass="max-w-6xl"
          eyebrow={
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300 backdrop-blur-md shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
              ReadyForRobots · Intelligence
            </span>
          }
          title={
            <span className="inline-flex flex-wrap items-center gap-4">
              <PixelIcon
                map={KARE_FACE}
                scale={3}
                fill={FACE_EMERALD}
                background="transparent"
              />
              <span className="font-display bg-gradient-to-r from-white via-slate-100 to-emerald-300 bg-clip-text text-transparent">
                Robots Need Jobs. We Find the Work.
              </span>
            </span>
          }
          description={
            <p className="text-base sm:text-lg leading-relaxed text-slate-300">
              We discover the physical work your machine is qualified to do — employer, workplace, and exact task — then turn matches directly into actionable CRM opportunities.
            </p>
          }
          innerClassName="pb-10 pt-4"
        >
          <div className="mt-8 space-y-6">
            {/* Real Stats Bar: 1,000+ Verified Jobs */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 backdrop-blur-md shadow-[0_0_20px_rgba(16,185,129,0.1)]">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
                  </span>
                  <div>
                    <span className="font-mono text-2xl font-black text-white sm:text-3xl">1,000+</span>
                    <span className="ml-2 font-display text-sm font-bold uppercase tracking-wider text-emerald-400">
                      Verified Jobs Available
                    </span>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-xs text-slate-300 font-medium">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-white">100+</span>
                    <span className="text-slate-400">Indexed SKUs</span>
                  </div>
                  <span className="text-slate-600">•</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-white">100%</span>
                    <span className="text-slate-400">Evidence-Backed</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Workflow Steps 01 -> 02 -> 03 with arrow connectors */}
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              {ABOUT_STATS.map(([value, label], idx) => (
                <div key={label} className="flex flex-1 items-center gap-2">
                  <div className="group relative flex-1 overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md transition-all duration-200 hover:border-emerald-400/40 hover:bg-white/[0.05] hover:shadow-lg hover:shadow-emerald-950/30">
                    <div className="flex items-center justify-between">
                      <div className="font-mono text-2xl font-black text-emerald-400">
                        {value}
                      </div>
                      <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                        Step {idx + 1}
                      </span>
                    </div>
                    <div className="mt-1 text-xs font-bold uppercase tracking-wider text-slate-300 group-hover:text-white transition-colors">
                      {label}
                    </div>
                  </div>
                  {idx < ABOUT_STATS.length - 1 ? (
                    <div className="hidden sm:flex shrink-0 items-center justify-center px-1 text-emerald-400/60" aria-hidden="true">
                      <ArrowRight className="h-5 w-5 animate-pulse text-emerald-400" />
                    </div>
                  ) : null}
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href={jobsFindHref()}
                className="group inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-400 hover:shadow-emerald-400/30"
              >
                {FIND_JOBS_CTA}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href={JOBS_SIGNUP_HREF}
                className="group inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-[#0b162f] px-4 py-2.5 text-sm font-semibold text-slate-200 transition-all hover:border-violet-400/50 hover:bg-[#111f42] hover:text-white"
              >
                Keep jobs in CRM
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <a
                href="#report"
                className="group inline-flex items-center gap-2 rounded-xl border border-slate-700/60 px-4 py-2.5 text-sm font-medium text-slate-400 transition-all hover:border-slate-500 hover:text-slate-200"
              >
                Download report
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </a>
            </div>
          </div>
        </PageHeroDark>
      </div>

      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 px-4 sm:px-6 pb-20">
        <div className="max-w-6xl mx-auto space-y-12">

          {/* How Jobs Works & Vocabulary */}
          <section className="overflow-hidden rounded-2xl border border-slate-700/60 bg-[#0a1226]/90 shadow-2xl backdrop-blur-md">
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr]">
              <div className="border-b border-slate-700/60 p-6 sm:p-8 lg:border-b-0 lg:border-r">
                <p className={`mb-3 ${EYEBROW}`}>
                  Process Architecture
                </p>
                <h2 className="font-display text-2xl font-bold leading-tight text-white lg:text-3xl">
                  {JOBS_FOR_YOUR_ROBOT_HEADING}
                </h2>
                <p className="mt-3.5 text-sm leading-relaxed text-slate-300">
                  Companies have physical work. Robots need qualified jobs. Paste a product URL,
                  inspect matched opportunities, and manage your pipeline in your native CRM.
                </p>

                <div className="mt-6 flex flex-col gap-2 rounded-xl border border-slate-700/60 bg-[#060c1c] p-2.5 sm:flex-row sm:items-center sm:justify-between">
                  {JOBS_PROCESS_STEPS.map((step, idx) => (
                    <div key={step.id} className="flex flex-1 items-center gap-2">
                      <div className="flex-1 rounded-lg bg-[#0b162f] p-3 transition-colors hover:bg-[#101e3d]">
                        <p className="font-mono text-sm font-bold text-emerald-400">
                          {step.n}
                        </p>
                        <p className="mt-1 text-xs font-medium text-slate-300">
                          {step.label}
                        </p>
                      </div>
                      {idx < JOBS_PROCESS_STEPS.length - 1 ? (
                        <div className="hidden sm:flex shrink-0 px-0.5 text-emerald-400/70" aria-hidden="true">
                          <ArrowRight className="h-4 w-4 text-emerald-400" />
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6 sm:p-8 bg-[#091022]/80">
                <p className={`mb-4 ${EYEBROW}`}>
                  Core Definitions
                </p>
                <div className="space-y-3">
                  {[
                    [
                      "Employer",
                      "The organization with physical work — not a prospect or lead.",
                    ],
                    ["Workplace", "The facility where the work happens."],
                    [
                      "Work",
                      "Observable activity, robot-neutral. We do not invent a use-case to fit a SKU.",
                    ],
                    [
                      "Robot Job",
                      "Work defined well enough to recruit against. Cards stay Conditional until evidence.",
                    ],
                  ].map(([label, copy]) => (
                    <div
                      key={label}
                      className="group rounded-xl border-l-2 border-emerald-400 bg-emerald-950/20 p-3.5 transition-all duration-200 hover:bg-emerald-950/30 hover:border-emerald-300"
                    >
                      <p className="text-sm font-bold text-slate-100 group-hover:text-emerald-300 transition-colors">
                        {label}
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-slate-400">
                        {copy}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Protocol Architecture Component */}
          <section className="rounded-2xl border border-violet-500/30 bg-[#0a1226] shadow-xl overflow-hidden">
            <JobsPstackProtocol aboutLink={false} />
          </section>

          {/* 2026 Work Briefing Download Section */}
          <section
            id="report"
            className="overflow-hidden rounded-2xl border border-slate-700/60 bg-[#0a1226] shadow-2xl"
          >
            <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_380px]">
              <div className="p-6 sm:p-8 bg-[#0a1226]">
                <p className={`mb-3 ${EYEBROW}`}>
                  Work Briefing · 2026
                </p>
                <h2 className="font-display text-2xl font-bold leading-tight text-white lg:text-3xl">
                  Labor-intensive workplaces still have jobs robots can do.
                </h2>
                <p className="mt-3.5 text-sm leading-relaxed text-slate-300">
                  A short briefing on where physical work is piling up — so robot
                  companies show up with jobs, not a generic sales dump.
                </p>

                <div className="mt-8 grid grid-cols-1 gap-3.5 sm:grid-cols-3">
                  {[
                    ["Logistics", "Warehouses with work to fill"],
                    ["Labor Shortage", "Shifts robots can cover"],
                    ["Site Work", "Employer · workplace · task"],
                  ].map(([label, copy]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3.5 transition-all hover:border-emerald-400/40"
                    >
                      <p className="text-sm font-bold text-emerald-300">
                        {label}
                      </p>
                      <p className="mt-1 text-xs text-slate-400 leading-normal">{copy}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6 sm:p-8 bg-[#060c1c] border-t border-slate-700/60 lg:border-t-0 lg:border-l">
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/30 bg-emerald-500/10 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Download the 2026 Briefing
                    </h3>
                    <p className="text-xs text-slate-400">
                      Work, not a buyer dump.
                    </p>
                  </div>
                </div>

                {reportStatus === "success" ? (
                  <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-300 flex items-start gap-2.5">
                    <Check className="h-4 w-4 shrink-0 mt-0.5 text-emerald-400" />
                    <span>Briefing requested. We saved your request and queued the follow-up email.</span>
                  </div>
                ) : (
                  <form onSubmit={requestReport} className="relative space-y-3">
                    <label
                      className="absolute -left-[10000px] h-px w-px overflow-hidden"
                      aria-hidden="true"
                    >
                      Website
                      <input
                        type="text"
                        name="website"
                        tabIndex={-1}
                        autoComplete="off"
                        value={reportForm.website}
                        onChange={e =>
                          setReportForm(current => ({
                            ...current,
                            website: e.target.value,
                          }))
                        }
                      />
                    </label>
                    {[
                      ["name", "Name", "text"],
                      ["email", "Work email", "email"],
                      ["company", "Company", "text"],
                      ["robotCategory", "Robot you place", "text"],
                    ].map(([key, label, type]) => (
                      <input
                        key={key}
                        type={type}
                        required={key === "email"}
                        placeholder={label}
                        value={reportForm[key as keyof typeof reportForm]}
                        onChange={e =>
                          setReportForm(current => ({
                            ...current,
                            [key]: e.target.value,
                          }))
                        }
                        className={inputClass}
                      />
                    ))}
                    {reportStatus === "error" && (
                      <p className="text-xs text-rose-400">
                        Could not request briefing. Try again.
                      </p>
                    )}
                    <button
                      type="submit"
                      disabled={reportStatus === "submitting"}
                      className="group w-full mt-2 inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-md transition-all hover:bg-emerald-400 disabled:opacity-50"
                    >
                      {reportStatus === "submitting"
                        ? "Requesting…"
                        : "Download Free Briefing"}
                      <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
                    </button>
                  </form>
                )}
              </div>
            </div>
          </section>

          {/* 4-Card Feature Grid */}
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {JOBS_LOOP.map(item => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="group rounded-2xl border border-slate-700/60 bg-[#0a1226] p-5 backdrop-blur-md transition-all duration-200 hover:-translate-y-1 hover:border-emerald-400/50 hover:shadow-[0_8px_25px_rgba(16,185,129,0.12)]"
                >
                  <div className="mb-4 inline-flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 transition-colors group-hover:bg-emerald-500/20 group-hover:text-emerald-300">
                    <Icon className="h-4 w-4" />
                  </div>
                  <h3 className="mb-1.5 text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-400">
                    {item.copy}
                  </p>
                </div>
              );
            })}
          </section>

          {/* Weekly Briefing & Email Subscription */}
          <section
            id="brief"
            className="rounded-2xl border border-slate-700/60 bg-[#0a1226] p-6 sm:p-8 shadow-xl"
          >
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_340px]">
              <div>
                <p className={`mb-2.5 ${EYEBROW}`}>
                  Weekly Intelligence
                </p>
                <h2 className="font-display text-2xl font-bold leading-tight text-white">
                  A weekly look at work robots can take.
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-slate-300">
                  Deployments, open work, and SKUs getting hired — so you run
                  FIND on the next robot instead of waiting on a sales cycle.
                </p>
                {stories.length > 0 && (
                  <div className="mt-6 grid grid-cols-1 gap-3.5 md:grid-cols-3">
                    {stories.slice(0, 3).map((story, i) => (
                      <div
                        key={`${story.title || story.company || i}`}
                        className="rounded-xl border border-slate-700/60 bg-[#060c1c] p-4 transition-all hover:border-emerald-400/40"
                      >
                        <p className="break-words mb-1.5 text-xs font-bold text-slate-100">
                          {cleanScrapedText(story.title || story.company) ||
                            "Work Story"}
                        </p>
                        <p className="break-words text-xs leading-relaxed text-slate-400">
                          {cleanScrapedText(story.summary) ||
                            "Fresh work from ReadyForRobots."}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <form
                onSubmit={subscribe}
                className="rounded-xl border border-slate-700/60 bg-[#060c1c] p-5 shadow-lg flex flex-col justify-between"
              >
                <div>
                  <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-400/30 bg-emerald-500/10 text-emerald-400">
                    <Mail className="h-4 w-4" />
                  </div>
                  <h3 className="mb-1 text-sm font-bold text-white">
                    Subscribe Free
                  </h3>
                  <p className="mb-4 text-xs leading-relaxed text-slate-400">
                    Jobs, workplaces, and which robots are getting the work.
                  </p>
                  <input
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    type="email"
                    placeholder="Work email address"
                    className={inputClass}
                  />
                  {newsletterStatus === "success" && (
                    <p className="mt-2 text-xs text-emerald-400 flex items-center gap-1">
                      <Check className="h-3.5 w-3.5" /> Subscribed!
                    </p>
                  )}
                  {newsletterStatus === "error" && (
                    <p className="mt-2 text-xs text-rose-400">
                      Could not subscribe. Try again.
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={newsletterStatus === "submitting"}
                  className="group mt-4 w-full inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-md transition-all hover:bg-emerald-400 disabled:opacity-50"
                >
                  {newsletterStatus === "submitting"
                    ? "Subscribing…"
                    : "Subscribe Free"}
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
                </button>
              </form>
            </div>
          </section>

          {/* Footer CTA Beat */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-4 text-sm">
            <Link
              href={jobsFindHref()}
              className="group inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-2.5 font-bold text-slate-950 shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-400"
            >
              {FIND_JOBS_CTA}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href={JOBS_SIGNUP_HREF}
              className="group inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-[#0b162f] px-4 py-2.5 font-semibold text-slate-200 transition-all hover:border-violet-400/50 hover:bg-[#111f42] hover:text-white"
            >
              Keep jobs in CRM
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
