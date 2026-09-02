/**
 * `/` first beat: sparse System 1 fork, then two doors. Not FIND yet.
 * Headline picker A–E is not shipped.
 */
import PixelIcon from "@/components/PixelIcon";
import { KARE_FACE } from "@/lib/kareIcons";
import {
  LANDING_COLORS as C,
  LANDING_EYEBROW,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE_END,
  LANDING_HEADLINE_LEAD,
  LANDING_KICKER_JOBS,
  LANDING_SUBHEAD,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  jobsCandidatesHref,
  jobsFindHref,
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
            {LANDING_HEADLINE_LEAD}
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
            {LOOK_FOR_ROBOT_JOBS_CTA}
          </a>
          <a
            href={jobsCandidatesHref()}
            data-landing-option="candidates"
            className="rfr-landing-door-title"
          >
            {LOOK_FOR_ROBOT_CANDIDATES_CTA}
          </a>
        </nav>
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
