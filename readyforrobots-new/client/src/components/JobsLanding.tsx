/**
 * `/` first beat: Kare Macintosh landing from docs/rfr-70s-ui-source,
 * then two doors. Not FIND yet. Headline picker A–E is not shipped.
 */
import { useState, type ReactNode } from "react";
import { useLocation } from "wouter";
import {
  PixelBriefcase,
  PixelDoc,
  PixelHand,
  PixelRobot,
} from "@/components/LandingPixels";
import {
  LANDING_BRIEFING_CTA,
  LANDING_BRIEFING_HREF,
  LANDING_BRIEF_EYEBROW,
  LANDING_BRIEF_HEADLINE,
  LANDING_BRIEF_JOBS,
  LANDING_BRIEF_NOTE,
  LANDING_CANDIDATES_HINT,
  LANDING_CANDIDATES_LABEL,
  LANDING_CLOSE_HEADLINE,
  LANDING_CLOSE_SUBHEAD,
  LANDING_COLORS as C,
  LANDING_EYEBROW,
  LANDING_FOOTER_LINKS,
  LANDING_FOOTER_MARK,
  LANDING_HEADLINE,
  LANDING_HOW_EYEBROW,
  LANDING_HOW_HEADLINE,
  LANDING_HOW_STEPS,
  LANDING_JOBS_HINT,
  LANDING_JOBS_LABEL,
  LANDING_SIGNUP_HREF,
  LANDING_START_FREE_CTA,
  LANDING_SUBHEAD,
  LANDING_VOCAB,
  LANDING_VOCAB_EYEBROW,
  LANDING_VOCAB_HEADLINE,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  jobsCandidatesHref,
  jobsFindHref,
  landingHeadlineParts,
  type LandingBriefJob,
} from "@/lib/jobsLanding";

function Chip({ children }: { children: string }) {
  return (
    <p className="rfr-landing-eyebrow" style={{ color: C.mint }}>
      {children}
    </p>
  );
}

function WindowBar({ title, right }: { title: string; right?: ReactNode }) {
  return (
    <div className="rfr-landing-windowbar">
      <div className="flex items-center gap-2">
        <span
          className="h-3 w-3 border-2"
          style={{ borderColor: C.muted }}
          aria-hidden="true"
        />
        <span className="rfr-landing-windowbar-title">{title}</span>
      </div>
      {right}
    </div>
  );
}

function LandingCta({
  children,
  onClick,
  href,
  primary = false,
}: {
  children: string;
  onClick?: () => void;
  href?: string;
  primary?: boolean;
}) {
  const className = primary ? "rfr-landing-cta" : "rfr-landing-ghost";
  if (href) {
    return (
      <a href={href} className={className}>
        {children} <span aria-hidden="true">→</span>
      </a>
    );
  }
  return (
    <span className={className} onClick={onClick}>
      {children} <span aria-hidden="true">→</span>
    </span>
  );
}

function DoorCard({
  label,
  title,
  body,
  featured,
  option,
  icon,
  onOpen,
}: {
  label: string;
  title: string;
  body: string;
  featured?: boolean;
  option: "jobs" | "candidates";
  icon: ReactNode;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      data-landing-option={option}
      aria-label={title}
      onClick={onOpen}
      className="rfr-landing-door flex flex-col text-left"
      data-featured={featured ? "true" : "false"}
    >
      <WindowBar
        title={label}
        right={
          <span
            className="h-3 w-3 border-2"
            style={{
              background: featured ? C.mint : "transparent",
              borderColor: featured ? C.mint : C.muted,
            }}
            aria-hidden="true"
          />
        }
      />
      <div className="p-6 md:p-8">
        <div className="flex items-start justify-between gap-4">
          <h3
            className="text-2xl font-semibold md:text-3xl"
            style={{
              color: C.text,
              fontFamily: "var(--font-landing-display)",
            }}
          >
            {title}
          </h3>
          <span className="mt-1 shrink-0">{icon}</span>
        </div>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: C.muted }}>
          {body}
        </p>
        <span className="mt-7 inline-block">
          <LandingCta primary={featured}>{title}</LandingCta>
        </span>
      </div>
    </button>
  );
}

function BriefJobCard({
  job,
  open,
  onToggle,
}: {
  job: LandingBriefJob;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <article
      className="overflow-hidden border-2"
      style={{
        borderColor: open ? C.mint : C.line,
        background: open ? C.panel : C.navy2,
      }}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-4 py-4 text-left md:gap-5 md:px-5"
      >
        <span
          className="w-16 shrink-0 text-[10px] font-bold"
          style={{
            color: C.mint,
            fontFamily: "var(--font-landing-ui)",
          }}
        >
          {job.id}
        </span>
        <div className="min-w-0 flex-1">
          <p
            className="truncate text-lg font-semibold"
            style={{
              color: C.text,
              fontFamily: "var(--font-landing-display)",
            }}
          >
            {job.employer}
          </p>
          <p
            className="truncate text-[11px] uppercase"
            style={{
              color: C.muted,
              fontFamily: "var(--font-landing-ui)",
              letterSpacing: "0.08em",
            }}
          >
            {job.sector}
          </p>
        </div>
        <span
          className="hidden shrink-0 px-2 py-1 text-[9px] font-bold uppercase sm:inline-block"
          style={{
            fontFamily: "var(--font-landing-ui)",
            letterSpacing: "0.1em",
            color: job.status === "OPEN" ? C.page : C.muted,
            background: job.status === "OPEN" ? C.mint : "transparent",
            border: `2px solid ${job.status === "OPEN" ? C.mint : C.line}`,
          }}
        >
          {job.status}
        </span>
        <span
          aria-hidden="true"
          style={{ color: C.mint, fontFamily: "var(--font-landing-ui)" }}
        >
          {open ? "▲" : "▼"}
        </span>
      </button>
      {open ? (
        <div
          className="rfr-landing-dither grid gap-x-10 gap-y-4 border-t-2 px-4 pb-6 pt-4 md:grid-cols-2 md:px-5"
          style={{ borderColor: C.line, backgroundColor: C.panel }}
        >
          {[
            ["Employer", `${job.employer} — ${job.sector}`],
            ["Workplace", job.workplace],
            ["Work", job.work],
            ["What's driving it", job.drivers.join(" · ")],
            ["Outreach window", job.window],
            ["Good fit for", job.fit.join(" · ")],
          ].map(([label, value]) => (
            <div key={label}>
              <p
                className="text-[9px] font-bold uppercase"
                style={{
                  color: C.muted,
                  fontFamily: "var(--font-landing-ui)",
                  letterSpacing: "0.1em",
                }}
              >
                {label}
              </p>
              <p
                className="mt-1 text-sm leading-relaxed"
                style={{ color: C.text }}
              >
                {value}
              </p>
            </div>
          ))}
          <p
            className="text-xs md:col-span-2"
            style={{ color: C.muted, fontFamily: "var(--font-landing-ui)" }}
          >
            Qualification is explainable — never a %. Cards stay Conditional
            until there is evidence.
          </p>
        </div>
      ) : null}
    </article>
  );
}

export default function JobsLanding() {
  const [, setLocation] = useLocation();
  const [openJob, setOpenJob] = useState(LANDING_BRIEF_JOBS[0]?.id ?? "");
  const headline = landingHeadlineParts(LANDING_HEADLINE);

  return (
    <div
      className="rfr-landing min-h-screen pt-14"
      style={{ background: C.page, color: C.text }}
    >
      <section className="relative border-b-2" style={{ borderColor: C.line }}>
        <div className="rfr-landing-hero-dither" aria-hidden="true" />
        <div className="relative mx-auto max-w-6xl px-4 pb-14 pt-16 md:pt-24">
          <Chip>{LANDING_EYEBROW}</Chip>
          <div className="mt-6 flex items-start gap-6 md:gap-10">
            <div className="min-w-0 flex-1">
              <h1 className="rfr-landing-headline max-w-3xl">
                {headline.map((part, index) => (
                  <span
                    key={part.text}
                    style={{ color: part.accent ? C.mint : C.text }}
                  >
                    {part.text}
                    {index < headline.length - 1 ? " " : ""}
                  </span>
                ))}
              </h1>
              <p
                className="mt-6 max-w-xl text-base leading-relaxed md:text-lg"
                style={{ color: C.muted }}
              >
                {LANDING_SUBHEAD}
              </p>
            </div>
            <div
              className="rfr-landing-hero-mark hidden shrink-0 items-center justify-center md:flex"
              aria-hidden="true"
            >
              <PixelRobot size={88} color={C.mint} />
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid gap-6 md:grid-cols-2">
          <DoorCard
            label={LANDING_JOBS_LABEL}
            title={LOOK_FOR_ROBOT_JOBS_CTA}
            body={LANDING_JOBS_HINT}
            featured
            option="jobs"
            icon={<PixelRobot size={40} color={C.mint} />}
            onOpen={() => setLocation(jobsFindHref())}
          />
          <DoorCard
            label={LANDING_CANDIDATES_LABEL}
            title={LOOK_FOR_ROBOT_CANDIDATES_CTA}
            body={LANDING_CANDIDATES_HINT}
            option="candidates"
            icon={<PixelBriefcase size={40} color={C.muted} />}
            onOpen={() => setLocation(jobsCandidatesHref())}
          />
        </div>
      </section>

      <section
        className="border-y-2"
        style={{ borderColor: C.line, background: C.navy2 }}
      >
        <div className="mx-auto max-w-6xl px-4 py-16">
          <Chip>{LANDING_HOW_EYEBROW}</Chip>
          <h2 className="rfr-landing-section-title mt-4">
            {LANDING_HOW_HEADLINE}
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {LANDING_HOW_STEPS.map(step => (
              <div key={step.n} className="rfr-landing-step">
                <WindowBar
                  title={`step ${step.n}`}
                  right={
                    <span
                      className="text-[10px] font-bold"
                      style={{
                        color: C.mint,
                        fontFamily: "var(--font-landing-ui)",
                      }}
                    >
                      {step.n}
                    </span>
                  }
                />
                <div className="p-6">
                  <h3
                    className="text-xl font-semibold"
                    style={{ fontFamily: "var(--font-landing-display)" }}
                  >
                    {step.title}
                  </h3>
                  <p
                    className="mt-2 text-sm leading-relaxed"
                    style={{ color: C.muted }}
                  >
                    {step.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Chip>{LANDING_BRIEF_EYEBROW}</Chip>
            <h2 className="rfr-landing-section-title mt-4">
              {LANDING_BRIEF_HEADLINE}
            </h2>
          </div>
          <p
            className="max-w-xs text-[10px] uppercase"
            style={{
              color: C.muted,
              fontFamily: "var(--font-landing-ui)",
              letterSpacing: "0.1em",
            }}
          >
            {LANDING_BRIEF_NOTE}
          </p>
        </div>
        <div className="mt-8 space-y-4">
          {LANDING_BRIEF_JOBS.map(job => (
            <BriefJobCard
              key={job.id}
              job={job}
              open={openJob === job.id}
              onToggle={() =>
                setOpenJob(current => (current === job.id ? "" : job.id))
              }
            />
          ))}
        </div>
      </section>

      <section
        className="border-y-2"
        style={{ borderColor: C.line, background: C.navy2 }}
      >
        <div className="mx-auto max-w-6xl px-4 py-16">
          <Chip>{LANDING_VOCAB_EYEBROW}</Chip>
          <h2 className="rfr-landing-section-title mt-4">
            {LANDING_VOCAB_HEADLINE}
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            {LANDING_VOCAB.map(item => (
              <div
                key={item.term}
                className="border-2 p-5"
                style={{ borderColor: C.line, background: C.panel }}
              >
                <div className="flex items-center gap-3">
                  <PixelDoc size={22} color={C.mint} />
                  <h3
                    className="text-xl font-semibold"
                    style={{ fontFamily: "var(--font-landing-display)" }}
                  >
                    {item.term}
                  </h3>
                </div>
                <p
                  className="mt-2 text-sm leading-relaxed"
                  style={{ color: C.muted }}
                >
                  {item.def}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="rfr-landing-close">
          <WindowBar
            title="readyforrobots start"
            right={<PixelHand size={20} color={C.mint} />}
          />
          <div className="flex flex-wrap items-center justify-between gap-8 p-8 md:p-10">
            <div>
              <h2
                className="text-3xl font-medium md:text-4xl"
                style={{ fontFamily: "var(--font-landing-display)" }}
              >
                {LANDING_CLOSE_HEADLINE}
              </h2>
              <p className="mt-2 text-sm" style={{ color: C.muted }}>
                {LANDING_CLOSE_SUBHEAD}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <LandingCta primary href={LANDING_SIGNUP_HREF}>
                {LANDING_START_FREE_CTA}
              </LandingCta>
              <LandingCta href={LANDING_BRIEFING_HREF}>
                {LANDING_BRIEFING_CTA}
              </LandingCta>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t-2" style={{ borderColor: C.line }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-10 gap-y-4 px-4 py-8">
          <div className="flex items-center gap-3">
            <PixelRobot size={22} color={C.mint} />
            <p
              className="text-[10px] uppercase"
              style={{
                color: C.muted,
                fontFamily: "var(--font-landing-ui)",
                letterSpacing: "0.1em",
              }}
            >
              {LANDING_FOOTER_MARK}
            </p>
          </div>
          <div className="flex flex-wrap gap-5">
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
