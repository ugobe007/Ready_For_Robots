/**
 * `/` first beat: who is this visit. Two options. Not FIND yet.
 */
import { useLocation } from "wouter";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  LANDING_CANDIDATES_HINT,
  LANDING_HEADLINE,
  LANDING_JOBS_HINT,
  LANDING_SUBHEAD,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  jobsCandidatesHref,
  jobsFindHref,
} from "@/lib/jobsLanding";
import {
  FIND_JOBS_HEADLINE_ACCENT_CLASS,
  FIND_JOBS_HEADLINE_CLASS,
  FIND_JOBS_SUBHEAD_CLASS,
  JOBS_FIND_CTA_CLASS,
} from "@/lib/jobsWorkflow";

export default function JobsLanding() {
  const [, setLocation] = useLocation();
  return (
    <div className="rfr-jobs-page-shell border border-slate-600 bg-[#0b162f]">
      <div className="px-6 py-10 sm:px-10 sm:py-14">
        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-300">
          ReadyForRobots
        </p>
        <h1 className={FIND_JOBS_HEADLINE_CLASS}>
          {LANDING_HEADLINE.split(/(visit)/).map((part, i) =>
            part === "visit" ? (
              <span key={i} className={FIND_JOBS_HEADLINE_ACCENT_CLASS}>
                {part}
              </span>
            ) : (
              part
            )
          )}
        </h1>
        <p className={FIND_JOBS_SUBHEAD_CLASS}>{LANDING_SUBHEAD}</p>
        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          <button
            type="button"
            data-landing-option="jobs"
            aria-label={LOOK_FOR_ROBOT_JOBS_CTA}
            onClick={() => setLocation(jobsFindHref())}
            className="border border-slate-600 bg-[#081126] px-5 py-6 text-left transition hover:border-emerald-400/70 hover:bg-emerald-400/5"
          >
            <PixelIcon
              map={KARE_FACE}
              scale={3}
              fill={FACE_EMERALD}
              background="transparent"
              className="mb-4"
            />
            <span className="block font-display text-xl font-bold text-slate-100">
              {LOOK_FOR_ROBOT_JOBS_CTA}
            </span>
            <span className="mt-2 block text-sm leading-snug text-slate-400">
              {LANDING_JOBS_HINT}
            </span>
            <span className={`${JOBS_FIND_CTA_CLASS} mt-6 inline-flex`}>
              {LOOK_FOR_ROBOT_JOBS_CTA} →
            </span>
          </button>
          <button
            type="button"
            data-landing-option="candidates"
            aria-label={LOOK_FOR_ROBOT_CANDIDATES_CTA}
            onClick={() => setLocation(jobsCandidatesHref())}
            className="border border-slate-600 bg-[#081126] px-5 py-6 text-left transition hover:border-emerald-400/70 hover:bg-emerald-400/5"
          >
            <span className="mb-4 block font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-300">
              Employer
            </span>
            <span className="block font-display text-xl font-bold text-slate-100">
              {LOOK_FOR_ROBOT_CANDIDATES_CTA}
            </span>
            <span className="mt-2 block text-sm leading-snug text-slate-400">
              {LANDING_CANDIDATES_HINT}
            </span>
            <span className={`${JOBS_FIND_CTA_CLASS} mt-6 inline-flex`}>
              {LOOK_FOR_ROBOT_CANDIDATES_CTA} →
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
