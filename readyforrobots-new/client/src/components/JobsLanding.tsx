/**
 * `/` first beat: marketing landing from the Manus mockup, then two doors.
 * Not FIND yet. Headline picker A–E is not shipped.
 */
import { useState } from "react";
import { useLocation } from "wouter";
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

function Eyebrow({ children }: { children: string }) {
  return (
    <p className="rfr-landing-eyebrow" style={{ color: C.mint }}>
      {children}
    </p>
  );
}

function Corners() {
  const cls = "pointer-events-none absolute h-3 w-3 border-current opacity-60";
  return (
    <>
      <span className={`${cls} top-0 left-0 border-t-2 border-l-2`} />
      <span className={`${cls} top-0 right-0 border-t-2 border-r-2`} />
      <span className={`${cls} bottom-0 left-0 border-b-2 border-l-2`} />
      <span className={`${cls} bottom-0 right-0 border-b-2 border-r-2`} />
    </>
  );
}

function LandingCta({
  children,
  onClick,
  href,
}: {
  children: string;
  onClick?: () => void;
  href?: string;
}) {
  const className = "rfr-landing-cta";
  const style = {
    background: C.mint,
    color: C.page,
  };
  if (href) {
    return (
      <a href={href} className={className} style={style}>
        {children} <span aria-hidden="true">→</span>
      </a>
    );
  }
  return (
    <span className={className} style={style} onClick={onClick}>
      {children} <span aria-hidden="true">→</span>
    </span>
  );
}

function LandingGhostCta({ children, href }: { children: string; href: string }) {
  return (
    <a
      href={href}
      className="rfr-landing-ghost"
      style={{ borderColor: C.line, color: C.text }}
    >
      {children}{" "}
      <span aria-hidden="true" style={{ color: C.mint }}>
        →
      </span>
    </a>
  );
}

function DoorCard({
  label,
  title,
  body,
  featured,
  option,
  onOpen,
}: {
  label: string;
  title: string;
  body: string;
  featured?: boolean;
  option: "jobs" | "candidates";
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      data-landing-option={option}
      aria-label={title}
      onClick={onOpen}
      className="rfr-landing-door group relative flex flex-col p-8 text-left md:p-10"
      style={{
        background: featured
          ? `linear-gradient(160deg, ${C.card} 0%, ${C.panel} 100%)`
          : C.panel,
        border: `1px solid ${featured ? C.mintDim : C.line}`,
        color: C.mint,
      }}
    >
      <Corners />
      <p
        className="text-[10px] font-bold uppercase tracking-[0.35em]"
        style={{
          color: featured ? C.mint : C.muted,
          fontFamily: "var(--font-landing-mono)",
        }}
      >
        {label}
      </p>
      <h3
        className="mt-4 text-2xl font-bold md:text-3xl"
        style={{ color: C.text, fontFamily: "var(--font-landing-display)" }}
      >
        {title}
      </h3>
      <p
        className="mt-3 flex-1 text-sm leading-relaxed"
        style={{ color: C.muted }}
      >
        {body}
      </p>
      <span className="mt-8">
        <LandingCta>{title}</LandingCta>
      </span>
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
      className="overflow-hidden"
      style={{ border: `1px solid ${C.line}`, background: C.panel }}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-4 py-3 text-left sm:px-5"
      >
        <span
          className="shrink-0 font-mono text-[11px] font-bold tracking-wider"
          style={{ color: C.mint, fontFamily: "var(--font-landing-mono)" }}
        >
          {job.id}
        </span>
        <span
          className="min-w-0 flex-1 truncate font-bold"
          style={{ color: C.text, fontFamily: "var(--font-landing-display)" }}
        >
          {job.employer}
        </span>
        <span
          className="hidden truncate text-sm sm:block"
          style={{ color: C.muted }}
        >
          {job.sector}
        </span>
        <span
          className="shrink-0 text-[10px] font-bold uppercase tracking-[0.18em]"
          style={{
            color: job.status === "OPEN" ? C.page : C.mint,
            background: job.status === "OPEN" ? C.mint : "transparent",
            border: `1px solid ${C.mintDim}`,
            padding: "4px 8px",
            fontFamily: "var(--font-landing-mono)",
          }}
        >
          {job.status}
          <span aria-hidden="true">{open ? " ▾" : " ▸"}</span>
        </span>
      </button>
      {open ? (
        <div
          className="grid gap-5 border-t px-4 py-5 sm:grid-cols-2 sm:px-5"
          style={{ borderColor: C.line }}
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
                className="text-[10px] font-bold uppercase tracking-[0.22em]"
                style={{
                  color: C.muted,
                  fontFamily: "var(--font-landing-mono)",
                }}
              >
                {label}
              </p>
              <p className="mt-1 text-sm leading-relaxed" style={{ color: C.text }}>
                {value}
              </p>
            </div>
          ))}
          <p
            className="sm:col-span-2 text-xs"
            style={{ color: C.muted, fontFamily: "var(--font-landing-mono)" }}
          >
            Qualification is explainable — never a %. Cards stay Conditional until
            there is evidence.
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
      <section className="relative overflow-hidden">
        <div className="rfr-landing-hero-grid" aria-hidden="true" />
        <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-16 md:pt-24">
          <Eyebrow>{LANDING_EYEBROW}</Eyebrow>
          <h1 className="rfr-landing-headline mt-5 max-w-4xl">
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
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="grid gap-5 md:grid-cols-2">
          <DoorCard
            label={LANDING_JOBS_LABEL}
            title={LOOK_FOR_ROBOT_JOBS_CTA}
            body={LANDING_JOBS_HINT}
            featured
            option="jobs"
            onOpen={() => setLocation(jobsFindHref())}
          />
          <DoorCard
            label={LANDING_CANDIDATES_LABEL}
            title={LOOK_FOR_ROBOT_CANDIDATES_CTA}
            body={LANDING_CANDIDATES_HINT}
            option="candidates"
            onOpen={() => setLocation(jobsCandidatesHref())}
          />
        </div>
      </section>

      <section className="border-t" style={{ borderColor: C.line, background: C.panel }}>
        <div className="mx-auto max-w-6xl px-4 py-20">
          <Eyebrow>{LANDING_HOW_EYEBROW}</Eyebrow>
          <h2 className="rfr-landing-section-title mt-4">{LANDING_HOW_HEADLINE}</h2>
          <div className="relative mt-12 grid gap-8 md:grid-cols-3">
            <div
              className="absolute top-5 right-0 left-0 hidden h-px md:block"
              style={{ background: C.line }}
              aria-hidden="true"
            />
            {LANDING_HOW_STEPS.map(step => (
              <div key={step.n} className="relative">
                <div
                  className="inline-flex h-10 w-10 items-center justify-center text-xs font-bold"
                  style={{
                    border: `1px solid ${C.mintDim}`,
                    color: C.mint,
                    background: C.page,
                    fontFamily: "var(--font-landing-mono)",
                  }}
                >
                  {step.n}
                </div>
                <h3
                  className="mt-4 text-lg font-bold"
                  style={{ fontFamily: "var(--font-landing-display)" }}
                >
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: C.muted }}>
                  {step.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Eyebrow>{LANDING_BRIEF_EYEBROW}</Eyebrow>
            <h2 className="rfr-landing-section-title mt-4">
              {LANDING_BRIEF_HEADLINE}
            </h2>
          </div>
          <p
            className="max-w-xs text-xs"
            style={{ color: C.muted, fontFamily: "var(--font-landing-mono)" }}
          >
            {LANDING_BRIEF_NOTE}
          </p>
        </div>
        <div className="mt-8 space-y-3">
          {LANDING_BRIEF_JOBS.map(job => (
            <BriefJobCard
              key={job.id}
              job={job}
              open={openJob === job.id}
              onToggle={() => setOpenJob(current => (current === job.id ? "" : job.id))}
            />
          ))}
        </div>
      </section>

      <section className="border-t" style={{ borderColor: C.line, background: C.panel }}>
        <div className="mx-auto max-w-6xl px-4 py-20">
          <Eyebrow>{LANDING_VOCAB_EYEBROW}</Eyebrow>
          <h2 className="rfr-landing-section-title mt-4">{LANDING_VOCAB_HEADLINE}</h2>
          <div className="mt-10 grid gap-x-12 md:grid-cols-2">
            {LANDING_VOCAB.map(item => (
              <div
                key={item.term}
                className="border-b py-5"
                style={{ borderColor: C.line }}
              >
                <div className="flex items-baseline gap-3">
                  <span
                    className="h-1.5 w-1.5 shrink-0 translate-y-[-2px]"
                    style={{ background: C.mint }}
                  />
                  <h3
                    className="font-bold"
                    style={{ fontFamily: "var(--font-landing-display)" }}
                  >
                    {item.term}
                  </h3>
                </div>
                <p
                  className="mt-1.5 pl-[18px] text-sm leading-relaxed"
                  style={{ color: C.muted }}
                >
                  {item.def}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20">
        <div
          className="relative flex flex-wrap items-center justify-between gap-8 p-8 md:p-12"
          style={{
            border: `1px solid ${C.mintDim}`,
            background: `linear-gradient(120deg, ${C.card}, ${C.panel})`,
            color: C.mint,
          }}
        >
          <Corners />
          <div>
            <h2
              className="text-2xl font-bold md:text-3xl"
              style={{ color: C.text, fontFamily: "var(--font-landing-display)" }}
            >
              {LANDING_CLOSE_HEADLINE}
            </h2>
            <p className="mt-2 text-sm" style={{ color: C.muted }}>
              {LANDING_CLOSE_SUBHEAD}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <LandingCta href={LANDING_SIGNUP_HREF}>{LANDING_START_FREE_CTA}</LandingCta>
            <LandingGhostCta href={LANDING_BRIEFING_HREF}>
              {LANDING_BRIEFING_CTA}
            </LandingGhostCta>
          </div>
        </div>
      </section>

      <footer className="border-t" style={{ borderColor: C.line }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-10 gap-y-4 px-4 py-10 text-xs" style={{ color: C.muted }}>
          <p style={{ fontFamily: "var(--font-landing-mono)" }}>
            {LANDING_FOOTER_MARK}
          </p>
          <div
            className="flex flex-wrap gap-6 font-bold uppercase tracking-[0.2em]"
            style={{ fontFamily: "var(--font-landing-mono)" }}
          >
            {LANDING_FOOTER_LINKS.map(link => (
              <a
                key={link.label}
                href={link.href}
                className="transition-colors hover:text-white"
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
