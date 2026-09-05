/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
import { useState, type FormEvent } from "react";
import PixelIcon from "@/components/PixelIcon";
import SiteIcon from "@/components/SiteIcon";
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
  return (
    <article className="rfr-landing-brief-job">
      <div className="rfr-landing-brief-row">
        <span className="rfr-landing-brief-id">{job.id}</span>
        <h3 className="rfr-landing-brief-employer">{job.employer}</h3>
        <span className="rfr-landing-brief-sector">{job.sector}</span>
        <span
          className={`rfr-landing-brief-status rfr-landing-brief-status--${job.status.toLowerCase()}`}
        >
          {job.status}
        </span>
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

  const handleHeroSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = heroUrl.trim();
    if (!trimmed) return;
    window.location.href = jobsFindHref(trimmed);
  };

  return (
    <div className="rfr-landing">
      <section className="rfr-landing-hero">
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
        <p className="rfr-landing-intro">{LANDING_INTRO}</p>

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
          <div className="rfr-landing-hero-samples">
            <span className="rfr-landing-samples-label">Try sample robot:</span>
            {SAMPLE_ROBOTS.map((sample) => (
              <button
                key={sample.url}
                type="button"
                className="rfr-landing-sample-chip"
                onClick={() => {
                  setHeroUrl(sample.url);
                  window.location.href = jobsFindHref(sample.url);
                }}
              >
                {sample.label}
              </button>
            ))}
          </div>
          <div className="rfr-landing-hero-actions">
            <a
              href={jobsCandidatesHref()}
              className="rfr-landing-employer-btn"
            >
              <SiteIcon
                id="handshake"
                scale={2}
                fill="#8B5CF6"
                background="transparent"
              />
              <span>Employers: Find robots for your job →</span>
            </a>
          </div>
        </form>
      </section>

      <section className="rfr-landing-brief" aria-label="Jobs brief">
        <p className="rfr-landing-brief-eyebrow">{LANDING_BRIEF_EYEBROW}</p>
        <h2 className="rfr-landing-brief-headline">{LANDING_BRIEF_HEADLINE}</h2>
        <p className="rfr-landing-brief-note">{LANDING_BRIEF_NOTE}</p>
        <div className="rfr-landing-brief-list">
          {LANDING_BRIEF_JOBS.map(job => (
            <BriefJobCard key={job.id} job={job} />
          ))}
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
