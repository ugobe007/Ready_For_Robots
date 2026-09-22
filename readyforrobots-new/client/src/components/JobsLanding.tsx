/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
import { useState, type FormEvent } from "react";
import { Sparkles, UserPlus, ShieldCheck } from "lucide-react";
import PixelIcon from "@/components/PixelIcon";
import SiteIcon from "@/components/SiteIcon";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import CustomerQuoteBanner from "@/components/CustomerQuoteBanner";
import QuickSignupModal from "@/components/QuickSignupModal";
import { MARKET_TAPE_JOBS } from "@/lib/jobsTapeCorpus";
import { KARE_FACE } from "@/lib/kareIcons";
import {
  LANDING_BRIEF_EYEBROW,
  LANDING_BRIEF_HEADLINE,
  LANDING_BRIEF_JOB_FIELD,
  LANDING_BRIEF_JOBS,
  LANDING_BRIEF_NOTE,
  LANDING_COLORS as C,
  LANDING_CANDIDATES_DOOR_LINE,
  LANDING_CTA_ROBOT_WORD,
  LANDING_DOOR_ICON_FILL,
  LANDING_DOOR_ICON_SCALE,
  LANDING_DOORS_CUE,
  LANDING_EYEBROW,
  LANDING_JOBS_DOOR_LINE,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE_AFTER,
  LANDING_HEADLINE_BEFORE,
  LANDING_HEADLINE_END,
  LANDING_HEADLINE_ROBOT,
  LANDING_INTRO,
  LANDING_KICKER_JOBS,
  LANDING_STATS,
  LANDING_SUBHEAD,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  jobsCandidatesHref,
  jobsFindHref,
  splitAccentWord,
  type LandingAccentPart,
  type LandingBriefJob,
} from "@/lib/jobsLanding";

function LandingFace({ scale }: { scale: number }) {
  return (
    <PixelIcon
      map={KARE_FACE}
      scale={scale}
      fill={C.emerald}
      background="transparent"
    />
  );
}

function LandingDoor({
  href,
  option,
  icon,
  title,
  line,
}: {
  href: string;
  option: "jobs" | "candidates";
  icon: "truck" | "handshake";
  title: string;
  line: string;
}) {
  return (
    <a
      href={href}
      data-landing-option={option}
      className={`rfr-landing-door rfr-landing-door--${option}`}
    >
      <span className="rfr-landing-door-mark" aria-hidden="true">
        <SiteIcon
          id={icon}
          scale={LANDING_DOOR_ICON_SCALE}
          fill={LANDING_DOOR_ICON_FILL}
          background="transparent"
        />
      </span>
      <span className="rfr-landing-door-copy-stack">
        <span className="rfr-landing-door-title">
          <span className="rfr-landing-door-copy">
            <AccentLabel
              parts={splitAccentWord(title, LANDING_CTA_ROBOT_WORD)}
            />
          </span>
        </span>
        <span className="rfr-landing-door-line">{line}</span>
      </span>
    </a>
  );
}

function AccentLabel({ parts }: { parts: LandingAccentPart[] }) {
  return (
    <span>
      {parts.map((part, index) =>
        part.accent ? (
          <span key={`${part.text}-${index}`} className="rfr-landing-accent">
            {part.text}
          </span>
        ) : (
          <span key={`${part.text}-${index}`}>{part.text}</span>
        )
      )}
    </span>
  );
}

function BriefJobCard({ job }: { job: LandingBriefJob }) {
  const isConditional = job.status === "CONDITIONAL";

  return (
    <article className="rfr-landing-brief-job">
      <div className="rfr-landing-brief-row">
        <span className="rfr-landing-brief-id">{job.id}</span>
        <h3 className="rfr-landing-brief-employer">{job.employer}</h3>
        <span className="rfr-landing-brief-sector">{job.workplace || job.sector}</span>
        {!isConditional && (
          <span
            className={`rfr-landing-brief-status rfr-landing-brief-status--${job.status.toLowerCase()}`}
          >
            {job.status}
          </span>
        )}
      </div>
      <p className="rfr-landing-brief-field-label">{LANDING_BRIEF_JOB_FIELD}</p>
      <p className="rfr-landing-brief-jobs">{job.work}</p>
    </article>
  );
}

const SAMPLE_ROBOTS = [
  { label: "Humanoid", url: "https://www.dexmate.ai" },
  { label: "Logistics robot", url: "https://www.locusrobotics.com" },
  { label: "Agriculture robot", url: "https://greenfieldrobotics.com" },
];

export default function JobsLanding() {
  const [heroUrl, setHeroUrl] = useState("");
  const [isSignupOpen, setIsSignupOpen] = useState(false);

  const handleHeroSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = heroUrl.trim();
    if (!trimmed) return;
    window.location.href = jobsFindHref(trimmed);
  };

  return (
    <div className="rfr-landing">
      <QuickSignupModal
        isOpen={isSignupOpen}
        onClose={() => setIsSignupOpen(false)}
        title="Unlock Engineering Feasibility & Commercial Proposals"
        subtitle="Create your free ReadyForRobots workspace in 10 seconds to save matches, view buyer signals, and generate turnkey commercial quotes."
        source="jobs_landing_hero"
      />

      <section className="rfr-landing-hero">
        <div className="rfr-landing-hero-bg" aria-hidden="true">
          <img
            src="/ready_for_robots_hero.jpg"
            alt=""
            className="rfr-landing-hero-bg-img"
          />
          <div className="rfr-landing-hero-bg-overlay" />
        </div>
        <p className="rfr-landing-kicker">
          {LANDING_EYEBROW}
          {" · "}
          <span className="rfr-landing-kicker-jobs">{LANDING_KICKER_JOBS}</span>
        </p>
        <div className="rfr-landing-hero-row">
          <h1 className="rfr-landing-headline">
            {LANDING_HEADLINE_BEFORE}
            <span className="rfr-landing-accent">{LANDING_HEADLINE_ROBOT}</span>
            {LANDING_HEADLINE_AFTER}
            <br />
            {LANDING_HEADLINE_END}
          </h1>
          <div className="rfr-landing-hero-mark" aria-hidden="true">
            <LandingFace scale={7} />
          </div>
        </div>
        <p className="rfr-landing-subhead">{LANDING_SUBHEAD}</p>

        <div className="rfr-landing-stats-bar">
          {LANDING_STATS.map((stat, idx) => (
            <span key={stat.label} className="rfr-landing-stat-group">
              {idx > 0 && <div className="rfr-landing-stat-divider" />}
              <div className="rfr-landing-stat-item">
                {stat.pulse && <span className="rfr-landing-stat-pulse" />}
                <span className="rfr-landing-stat-value">{stat.value}</span>
                <span className="rfr-landing-stat-label">{stat.label}</span>
              </div>
            </span>
          ))}
        </div>

        <form onSubmit={handleHeroSubmit} className="rfr-landing-hero-form">
          <div className="rfr-landing-hero-input-wrap">
            <input
              type="text"
              placeholder="Paste a robot product URL (e.g. https://www.dexmate.ai)..."
              value={heroUrl}
              onChange={(e) => setHeroUrl(e.target.value)}
              className="rfr-landing-hero-input"
              aria-label="Robot product URL"
            />
            <button type="submit" className="rfr-landing-hero-submit">
              Find jobs →
            </button>
          </div>
        </form>

        {/* Featured Daily Customer Intent Quotes */}
        <div className="rfr-landing-quotes mt-8 mb-5 w-full pt-1" aria-label="Customer Quotes">
          <CustomerQuoteBanner />
        </div>

        {/* High-Converting Account Registration Banner (Positioned directly below Customer Quotes) */}
        <div className="rfr-landing-signup-cta my-4 py-3 px-5 sm:py-3.5 sm:px-6 rounded-2xl bg-gradient-to-r from-emerald-950/90 via-slate-900 to-cyan-950/90 border border-emerald-500/40 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="space-y-0.5 text-left">
            <div className="flex items-center gap-2 text-emerald-400 font-mono text-[11px] uppercase tracking-wider font-bold">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> Free Enterprise Workspace
            </div>
            <h3 className="text-sm sm:text-base font-extrabold text-white">
              Unlock Engineering Feasibility & Commercial Proposals
            </h3>
            <p className="text-xs text-slate-300 max-w-xl">
              Join 1,200+ robotics leaders. Access verified buyer signals, 3D cell simulations, and turnkey RaaS commercial quotes.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsSignupOpen(true)}
            className="w-full sm:w-auto px-5 py-2.5 sm:py-3 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-extrabold text-xs tracking-wide uppercase transition-all shadow-lg shadow-emerald-400/20 whitespace-nowrap text-center flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            <UserPlus className="w-4 h-4" />
            Create Free Account in 10s →
          </button>
        </div>

        {/* Action Links pulled to left margin with normalized text-sm font */}
        <div className="rfr-landing-hero-actions flex flex-wrap items-center justify-start gap-5 my-3">
          <a
            href={jobsCandidatesHref()}
            className="rfr-landing-employer-link inline-flex items-center gap-1 text-sm font-semibold font-mono text-[#d6b15d] hover:text-[#f0cb75] underline underline-offset-4 transition-all"
          >
            Employers: Find robots for your job →
          </a>
          <a
            href="/newsletter"
            className="inline-flex items-center gap-1 text-sm font-semibold font-mono text-emerald-400 hover:text-emerald-300 underline underline-offset-4 transition-all"
          >
            <span>📰 Daily Newsletter →</span>
          </a>
        </div>
      </section>

      <section className="rfr-landing-brief" aria-label="Live job feed">
        <h2 className="rfr-landing-brief-headline">Jobs for <span className="text-emerald-400">robots.</span></h2>
        <p className="rfr-landing-brief-note">{LANDING_BRIEF_NOTE}</p>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-800 bg-[#081126] shadow-2xl">
          <LiveJobTape
            title="Verified Physical Work Feed"
            subtitle="Classified job opportunities highlighting as they reach the top of the feed"
            corpus={MARKET_TAPE_JOBS}
            baseCount={MARKET_TAPE_JOBS.length}
            running={true}
          />
        </div>
      </section>

      <footer className="rfr-landing-footer">
        <div className="rfr-landing-footer-row">
          <p className="rfr-landing-footer-mark">{LANDING_FOOTER_MARK}</p>
          <div className="rfr-landing-footer-links">
            {LANDING_FOOTER_LINKS.map(link => (
              <a
                key={link.label}
                href={link.href}
                className="rfr-landing-footer-link"
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
