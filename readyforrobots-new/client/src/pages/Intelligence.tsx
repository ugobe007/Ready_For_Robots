/**
 * About (`/intelligence`) — Jobs chrome. Robot URL → jobs → CRM.
 */
import { useEffect, useState } from "react";
import { ArrowRight, Building2, FileText, Mail, Search } from "lucide-react";
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

const EYEBROW = "text-[10px] font-semibold uppercase tracking-[0.15em]";
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
    "w-full border border-slate-600 bg-[#081126] px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-emerald-400";

  return (
    <div
      className={`intelligence-page flex min-h-screen flex-col bg-[#081126] text-slate-100 ${JOBS_HEADER_OFFSET_CLASS}`}
    >
      <ExperimentHeader />
      <PageHeroDark
        maxWidthClass="max-w-6xl"
        eyebrow="ReadyForRobots"
        title={
          <span className="inline-flex items-center gap-4">
            <PixelIcon
              map={KARE_FACE}
              scale={3}
              fill={FACE_EMERALD}
              background="transparent"
            />
            <span className="font-display text-emerald-400">About</span>
          </span>
        }
        description={
          <>
            Robots need jobs. We find the work your machine is qualified to do —
            employer, workplace, work — then keep it in CRM.
          </>
        }
        innerClassName="pb-8"
      >
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {ABOUT_STATS.map(([value, label]) => (
              <div
                key={label}
                className="border border-white/10 bg-white/5 px-3 py-2.5"
              >
                <div className="font-mono text-xl font-black text-emerald-400">
                  {value}
                </div>
                <div className="mt-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {label}
                </div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2.5 text-[13px]">
            <Link
              href={jobsFindHref()}
              className="group inline-flex items-center gap-1.5 font-semibold text-emerald-400 transition-colors hover:text-emerald-300"
            >
              {FIND_JOBS_CTA}
            </Link>
            <Link
              href={JOBS_SIGNUP_HREF}
              className="group inline-flex items-center gap-1.5 font-semibold text-slate-400 transition-colors hover:text-white"
            >
              Keep jobs in CRM{" "}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#report"
              className="group inline-flex items-center gap-1.5 font-semibold text-slate-400 transition-colors hover:text-white"
            >
              Download report{" "}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </a>
          </div>
        </div>
      </PageHeroDark>
      <div className="page-hero-fade" aria-hidden />

      <main className="flex-1 px-6 pb-20">
        <div className="max-w-6xl mx-auto">
          <section className="mb-12 overflow-hidden border border-slate-600 bg-[#0b162f]">
            <div className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="border-b border-slate-600 p-6 lg:border-b-0 lg:border-r">
                <p className={`mb-3 ${EYEBROW}`} style={{ color: "#34d399" }}>
                  How Jobs works
                </p>
                <h2 className="max-w-xl font-display text-xl font-bold leading-tight text-white lg:text-2xl">
                  {JOBS_FOR_YOUR_ROBOT_HEADING}
                </h2>
                <p className="mt-4 max-w-xl text-[13px] leading-relaxed text-slate-400">
                  Companies have work. Robots need jobs. Paste a product URL,
                  inspect the cards, check the jobs to take forward. Next is
                  Place — quote the rental, apply. {CRM_UNLOCKED_JOBS} jobs on
                  free. Not a buyer pipeline.
                </p>
                <div className="mt-5 grid grid-cols-3 gap-px overflow-hidden border border-slate-600 bg-[#081126]">
                  {JOBS_PROCESS_STEPS.map(step => (
                    <div key={step.id} className="bg-[#0b162f] p-3">
                      <p className="font-mono text-[13px] font-bold text-emerald-400">
                        {step.n}
                      </p>
                      <p className="mt-0.5 text-[11px] text-slate-400">
                        {step.label}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6">
                <div className="space-y-3.5">
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
                      className="border-l-2 border-emerald-400/50 bg-emerald-400/[0.04] px-3.5 py-2.5"
                    >
                      <p className="text-[13px] font-semibold text-slate-100">
                        {label}
                      </p>
                      <p className="mt-0.5 text-xs leading-relaxed text-slate-400">
                        {copy}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="mb-12">
            <JobsPstackProtocol aboutLink={false} />
          </section>

          <section
            id="report"
            className="mb-12 grid grid-cols-1 gap-px overflow-hidden border border-slate-600 lg:grid-cols-[1fr_360px] bg-[#081126]"
          >
            <div className="p-6 bg-[#0b162f]">
              <p className={`mb-3 ${EYEBROW}`} style={{ color: "#34d399" }}>
                Work briefing
              </p>
              <h2 className="max-w-2xl font-display text-2xl font-bold leading-tight text-white lg:text-3xl">
                Labor-intensive workplaces still have jobs robots can do.
              </h2>
              <p className="mt-4 max-w-2xl text-[13px] leading-relaxed text-slate-400">
                A short briefing on where physical work is piling up — so robot
                companies show up with jobs, not a generic sales dump.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
                {[
                  ["Logistics", "warehouses with work to fill"],
                  ["Labor shortage", "shifts robots can cover"],
                  ["Site work", "employer · workplace · task"],
                ].map(([label, copy]) => (
                  <div
                    key={label}
                    className="border-l px-3 py-1.5"
                    style={{ borderColor: "rgba(3,218,197,0.45)" }}
                  >
                    <p className="text-[13px] font-semibold text-slate-100">
                      {label}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-400">{copy}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-5 bg-[#081126]">
              <div className="mb-4 flex items-center gap-2.5">
                <div
                  className="flex h-8 w-8 items-center justify-center border"
                  style={{
                    borderColor: "rgba(52,211,153,0.35)",
                    background: "rgba(52,211,153,0.07)",
                  }}
                >
                  <FileText className="h-4 w-4" style={{ color: "#34d399" }} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-white">
                    Download the 2026 briefing
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Work, not a buyer dump.
                  </p>
                </div>
              </div>
              {reportStatus === "success" ? (
                <div
                  className="border border-teal-300/20 px-3.5 py-3 text-[13px]"
                  style={{
                    color: "#99f6e4",
                    background: "rgba(3,218,197,0.06)",
                  }}
                >
                  Briefing requested. We saved your request and queued the
                  follow-up email.
                </div>
              ) : (
                <form onSubmit={requestReport} className="relative space-y-2.5">
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
                    <p className="text-xs text-red-300">
                      Could not request briefing. Try again.
                    </p>
                  )}
                  <button
                    type="submit"
                    disabled={reportStatus === "submitting"}
                    className="group inline-flex items-center gap-1.5 pt-1 text-[13px] font-semibold transition-colors hover:text-teal-200 disabled:opacity-50"
                    style={{ color: "#059669" }}
                  >
                    {reportStatus === "submitting"
                      ? "Requesting…"
                      : "Download free briefing"}
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </button>
                </form>
              )}
            </div>
          </section>

          <section className="mb-12 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {JOBS_LOOP.map(item => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="border border-slate-600 bg-[#0b162f] p-4 transition-colors hover:border-emerald-400/40"
                >
                  <Icon className="mb-4 h-[18px] w-[18px] text-emerald-400" />
                  <p className="mb-1 text-[13px] font-semibold text-white">
                    {item.title}
                  </p>
                  <p className="text-[13px] leading-relaxed text-slate-400">
                    {item.copy}
                  </p>
                </div>
              );
            })}
          </section>

          <section
            id="brief"
            className="border border-slate-600 bg-[#0b162f] p-6"
          >
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_300px]">
              <div>
                <p className={`mb-2.5 ${EYEBROW}`} style={{ color: "#34d399" }}>
                  Jobs brief
                </p>
                <h2 className="max-w-2xl font-display text-2xl font-bold leading-tight text-white">
                  A weekly look at work robots can take.
                </h2>
                <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-slate-400">
                  Deployments, open work, and SKUs getting hired — so you run
                  FIND on the next robot instead of waiting on a sales cycle.
                </p>
                {stories.length > 0 && (
                  <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
                    {stories.slice(0, 3).map((story, i) => (
                      <div
                        key={`${story.title || story.company || i}`}
                        className="border border-slate-600 bg-[#081126] p-3.5"
                      >
                        <p className="break-words mb-1.5 text-[13px] font-semibold text-slate-100">
                          {cleanScrapedText(story.title || story.company) ||
                            "Work story"}
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
                className="border border-slate-600 bg-[#081126] p-4"
              >
                <Mail className="mb-3 h-[18px] w-[18px] text-emerald-400" />
                <p className="mb-1.5 text-[13px] font-semibold text-white">
                  Subscribe free
                </p>
                <p className="mb-3.5 text-xs leading-relaxed text-slate-400">
                  Jobs, workplaces, and which robots are getting the work.
                </p>
                <input
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  type="email"
                  placeholder="work email"
                  className={inputClass}
                />
                {newsletterStatus === "success" && (
                  <p className="mt-2.5 text-xs" style={{ color: "#059669" }}>
                    Subscribed.
                  </p>
                )}
                {newsletterStatus === "error" && (
                  <p className="mt-2.5 text-xs text-red-300">
                    Could not subscribe. Try again.
                  </p>
                )}
                <button
                  type="submit"
                  disabled={newsletterStatus === "submitting"}
                  className="group mt-3 inline-flex items-center gap-1.5 text-[13px] font-semibold text-emerald-400 transition-colors hover:text-emerald-300 disabled:opacity-50"
                >
                  {newsletterStatus === "submitting"
                    ? "Subscribing…"
                    : "Subscribe free"}
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                </button>
              </form>
            </div>
          </section>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-5 text-[13px]">
            <Link
              href={jobsFindHref()}
              className="group inline-flex items-center gap-1.5 font-semibold text-emerald-400 transition-colors hover:text-emerald-300"
            >
              {FIND_JOBS_CTA}
            </Link>
            <Link
              href={JOBS_SIGNUP_HREF}
              className="group inline-flex items-center gap-1.5 font-semibold text-slate-400 transition-colors hover:text-white"
            >
              Keep jobs in CRM{" "}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
