/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
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
  LANDING_JOBS_LABEL,
  LANDING_CANDIDATES_LABEL,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE_AFTER,
  LANDING_HEADLINE_BEFORE,
  LANDING_HEADLINE_END,
  LANDING_HEADLINE_ROBOT,
  LANDING_INTRO,
  LANDING_KICKER_JOBS,
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
  who,
  title,
  line,
}: {
  href: string;
  option: "jobs" | "candidates";
  icon: "truck" | "handshake";
  who: string;
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
        <span className="rfr-landing-door-who">{who}</span>
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

export default function JobsLanding() {
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
            <LandingFace scale={9} />
          </div>
        </div>
        <p className="rfr-landing-subhead">{LANDING_SUBHEAD}</p>
        <p className="rfr-landing-intro">{LANDING_INTRO}</p>
        <nav className="rfr-landing-doors" aria-label="Choose a visit">
          <p className="rfr-landing-doors-cue">{LANDING_DOORS_CUE}</p>
          <div className="rfr-landing-doors-choices">
            <LandingDoor
              href={jobsFindHref()}
              option="jobs"
              icon="truck"
              who={LANDING_JOBS_LABEL}
              title={LOOK_FOR_ROBOT_JOBS_CTA}
              line={LANDING_JOBS_DOOR_LINE}
            />
            <LandingDoor
              href={jobsCandidatesHref()}
              option="candidates"
              icon="handshake"
              who={LANDING_CANDIDATES_LABEL}
              title={LOOK_FOR_ROBOT_CANDIDATES_CTA}
              line={LANDING_CANDIDATES_DOOR_LINE}
            />
          </div>
        </nav>
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
