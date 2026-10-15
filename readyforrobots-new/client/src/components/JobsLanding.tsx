/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
import { useState, useEffect, useRef, type FormEvent } from "react";
import PixelIcon from "@/components/PixelIcon";
import SiteIcon from "@/components/SiteIcon";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import LiveJobDetailModal from "@/components/jobs/LiveJobDetailModal";
import CustomerQuoteBanner from "@/components/CustomerQuoteBanner";
import { MARKET_TAPE_JOBS } from "@/lib/jobsTapeCorpus";
import { JOB_TAPE_EXAMPLE_SUBTITLE } from "@/lib/robotJobCard";
import { useTapeJobCard } from "@/lib/tapeJobCard";
import { KARE_FACE } from "@/lib/kareIcons";
import {
  LANDING_BRIEF_JOB_FIELD,
  LANDING_BRIEF_NOTE,
  LANDING_COLORS as C,
  LANDING_CTA_ROBOT_WORD,
  LANDING_DOOR_ICON_FILL,
  LANDING_DOOR_ICON_SCALE,
  LANDING_EXAMPLES_HEADING,
  LANDING_EYEBROW,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE_AFTER,
  LANDING_HEADLINE_BEFORE,
  LANDING_HEADLINE_LEAD,
  LANDING_HEADLINE_ROBOT,
  LANDING_INPUT_PLACEHOLDER,
  LANDING_PRODUCT_LINE_HINT,
  LANDING_PROOF_POINTS,
  LANDING_SUBHEAD,
  LANDING_SUBMIT_CTA,
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
        <span className="rfr-landing-brief-sector">
          {job.workplace || job.sector}
        </span>
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
  const heroInputRef = useRef<HTMLInputElement>(null);
  const { selectedTapeJob, handleSelectJob, handleCloseModal } =
    useTapeJobCard();

  useEffect(() => {
    try {
      const visit = new URLSearchParams(window.location.search).get("visit");
      if (visit === "jobs" || visit === "jobslanding") {
        const tapeEl = document.querySelector(".rfr-landing-brief");
        if (tapeEl) {
          setTimeout(() => {
            tapeEl.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 200);
        }
      }
    } catch {
      // Ignore URL parsing errors
    }
  }, []);

  const handleHeroSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = heroUrl.trim();
    if (!trimmed) return;
    window.location.href = jobsFindHref(trimmed);
  };

  const focusHeroInput = () => {
    heroInputRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
    heroInputRef.current?.focus({ preventScroll: true });
  };

  return (
    <div className="rfr-landing">
      <section className="rfr-landing-hero">
        <div className="rfr-landing-hero-bg" aria-hidden="true">
          <img
            src="/ready_for_robots_hero.jpg"
            alt=""
            className="rfr-landing-hero-bg-img"
          />
          <div className="rfr-landing-hero-bg-overlay" />
        </div>
        <p className="rfr-landing-kicker">{LANDING_EYEBROW}</p>
        <div className="rfr-landing-hero-row">
          <h1 className="rfr-landing-headline">
            {LANDING_HEADLINE_LEAD}
            <br />
            {LANDING_HEADLINE_BEFORE}
            <span className="rfr-landing-accent">{LANDING_HEADLINE_ROBOT}</span>
            {LANDING_HEADLINE_AFTER}
          </h1>
          <div className="rfr-landing-hero-mark" aria-hidden="true">
            <LandingFace scale={7} />
          </div>
        </div>
        <p className="rfr-landing-subhead">{LANDING_SUBHEAD}</p>

        <form onSubmit={handleHeroSubmit} className="rfr-landing-hero-form">
          <div className="rfr-landing-hero-input-wrap">
            <input
              ref={heroInputRef}
              type="text"
              placeholder={LANDING_INPUT_PLACEHOLDER}
              value={heroUrl}
              onChange={e => setHeroUrl(e.target.value)}
              className="rfr-landing-hero-input"
              aria-label="Robot product URL"
            />
            <button type="submit" className="rfr-landing-hero-submit">
              {LANDING_SUBMIT_CTA}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            {LANDING_PRODUCT_LINE_HINT}
          </p>
        </form>

        <ul
          className="mt-8 grid w-full gap-4 sm:grid-cols-3"
          aria-label="Why Ready For Robots"
        >
          {LANDING_PROOF_POINTS.map(point => (
            <li
              key={point.title}
              className="rounded-xl border border-slate-700/70 bg-[#0b162f]/80 p-4"
            >
              <p className="text-sm font-bold text-slate-100">{point.title}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-300">
                {point.body}
              </p>
            </li>
          ))}
        </ul>

        <div
          className="rfr-landing-quotes mt-8 mb-5 w-full pt-1"
          aria-label="Employer quotes"
        >
          <CustomerQuoteBanner />
        </div>
      </section>

      <section className="rfr-landing-brief" aria-label="Example robot jobs">
        <h2 className="rfr-landing-brief-headline">
          {LANDING_EXAMPLES_HEADING}
        </h2>
        <p className="rfr-landing-brief-note">{LANDING_BRIEF_NOTE}</p>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-800 bg-[#081126] shadow-2xl">
          <LiveJobTape
            title="Example jobs"
            subtitle={JOB_TAPE_EXAMPLE_SUBTITLE}
            corpus={MARKET_TAPE_JOBS}
            baseCount={MARKET_TAPE_JOBS.length}
            running={true}
            onSelect={handleSelectJob}
            selectedKey={selectedTapeJob?.key ?? null}
          />
        </div>
      </section>

      <LiveJobDetailModal
        job={selectedTapeJob}
        isOpen={Boolean(selectedTapeJob)}
        onClose={handleCloseModal}
        onFindBuyers={focusHeroInput}
      />

      <footer className="rfr-landing-footer">
        <div className="rfr-landing-footer-row">
          <p className="rfr-landing-footer-mark">{LANDING_FOOTER_MARK}</p>
          <nav className="rfr-landing-footer-links" aria-label="Footer">
            {LANDING_FOOTER_LINKS.map(link => (
              <a
                key={link.label}
                href={link.href}
                className="rfr-landing-footer-link"
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  );
}
