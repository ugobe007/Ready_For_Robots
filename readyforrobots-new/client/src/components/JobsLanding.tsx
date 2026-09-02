/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";
import {
  LANDING_BRIEF_EYEBROW,
  LANDING_BRIEF_HEADLINE,
  LANDING_BRIEF_JOB_FIELD,
  LANDING_BRIEF_JOBS,
  LANDING_BRIEF_NOTE,
  LANDING_COLORS as C,
  LANDING_CTA_ROBOT_WORD,
  LANDING_EYEBROW,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE_AFTER,
  LANDING_HEADLINE_BEFORE,
  LANDING_HEADLINE_END,
  LANDING_HEADLINE_ROBOT,
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
      fill={C.page}
      background="transparent"
    />
  );
}

function AccentLabel({
  parts,
}: {
  parts: LandingAccentPart[];
}) {
  return (
    <>
      {parts.map((part, index) =>
        part.accent ? (
          <span key={`${part.text}-${index}`} className="rfr-landing-accent">
            {part.text}
          </span>
        ) : (
          <span key={`${part.text}-${index}`}>{part.text}</span>
        )
      )}
    </>
  );
}

function BriefJobCard({ job }: { job: LandingBriefJob }) {
  return (
    <article className="rfr-landing-brief-job">
      <div className="rfr-landing-brief-row">
        <span className="rfr-landing-brief-id">{job.id}</span>
        <h3 className="rfr-landing-brief-employer">{job.employer}</h3>
        <span className="rfr-landing-brief-sector">{job.sector}</span>
        <span className="rfr-landing-brief-status">{job.status}</span>
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
            <LandingFace scale={6} />
          </div>
        </div>
        <p className="rfr-landing-subhead">{LANDING_SUBHEAD}</p>
        <nav className="rfr-landing-doors" aria-label="Choose a visit">
          <a
            href={jobsFindHref()}
            data-landing-option="jobs"
            className="rfr-landing-door-title"
          >
            <AccentLabel
              parts={splitAccentWord(
                LOOK_FOR_ROBOT_JOBS_CTA,
                LANDING_CTA_ROBOT_WORD
              )}
            />
          </a>
          <a
            href={jobsCandidatesHref()}
            data-landing-option="candidates"
            className="rfr-landing-door-title"
          >
            <AccentLabel
              parts={splitAccentWord(
                LOOK_FOR_ROBOT_CANDIDATES_CTA,
                LANDING_CTA_ROBOT_WORD
              )}
            />
          </a>
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
