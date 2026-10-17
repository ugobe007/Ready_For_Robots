/**
 * /jobs — browse scored robot jobs (company × workflow) without choosing a
 * robot. Example rows only, badged EXAMPLE DATA, until the scored
 * opportunities ship and Bob reviews the top 20.
 */
import { useMemo, useState } from "react";
import { SiteFooter, SiteHeader } from "@/components/editorial";
import { useAuth } from "@/contexts/AuthContext";
import { usePageMeta } from "@/lib/pageMeta";
import {
  EXAMPLE_JOBS,
  INDUSTRY_FILTERS,
  JOB_FACTORS,
  TIMING_FILTERS,
  TIMING_TAGS,
  rankJobs,
  type JobIndustryGroup,
  type JobTiming,
  type ScoredJob,
} from "@/lib/robotJobsBoard";

const SIGNUP_FROM_JOBS = "/signup?next=%2Fjobs";

function FilterRow<T extends string>({
  label,
  options,
  value,
  onPick,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onPick: (value: T) => void;
}) {
  return (
    <div className="rfr-jobs-filter" role="group" aria-label={label}>
      <span className="rfr-jobs-filter-label">{label.toUpperCase()}</span>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          className={option.value === value ? "is-on" : undefined}
          onClick={() => onPick(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function JobCard({
  job,
  open,
  onToggle,
  signedIn,
}: {
  job: ScoredJob;
  open: boolean;
  onToggle: () => void;
  signedIn: boolean;
}) {
  const tagClass = `rfr-jobs-tag is-${job.timing}`;
  return (
    <article
      className={job.locked ? "rfr-jobs-card is-locked" : "rfr-jobs-card"}
      aria-hidden={job.locked || undefined}
    >
      <div className="rfr-jobs-card-grid">
        <div className="rfr-jobs-score">
          <strong>{job.score}</strong>
          <span>SCORE</span>
        </div>
        <div className="rfr-jobs-main">
          <div className="rfr-jobs-head">
            <h2>{job.company}</h2>
            <span className={tagClass}>{TIMING_TAGS[job.timing]}</span>
          </div>
          <p className="rfr-jobs-line">
            <strong>{job.workflow}</strong> · {job.industry} · {job.place}
          </p>
          <p className="rfr-jobs-why">
            <span>WHY NOW </span>
            {job.why}
          </p>
        </div>
        <div className="rfr-jobs-factors">
          {job.factors.map((factor, index) => (
            <div className="rfr-jobs-factor" key={JOB_FACTORS[index]}>
              <span>{JOB_FACTORS[index]}</span>
              <span className="rfr-jobs-bar">
                <span
                  className={factor.estimated ? "is-est" : undefined}
                  style={{ width: `${Math.round(factor.value * 100)}%` }}
                />
              </span>
              <span className="rfr-jobs-est">
                {factor.estimated ? "est" : ""}
              </span>
            </div>
          ))}
        </div>
      </div>
      {job.locked ? null : (
        <>
          <div className="rfr-jobs-actions">
            <button
              type="button"
              className="rfr-jobs-toggle"
              aria-expanded={open}
              onClick={onToggle}
            >
              {open ? "Hide evidence" : "Why this score"}
            </button>
            <span className="rfr-jobs-robots">{job.robots}</span>
            <span className="rfr-jobs-spacer" />
            {signedIn ? (
              <button
                type="button"
                className="rfr-jobs-save"
                disabled
                title="Example job. Saving opens when real jobs are live."
              >
                Save to desk
              </button>
            ) : (
              <a className="rfr-jobs-save" href={SIGNUP_FROM_JOBS}>
                Save to desk
              </a>
            )}
          </div>
          {open ? (
            <dl className="rfr-jobs-evidence">
              {job.evidence.map((item) => (
                <div key={item.k}>
                  <dt>{item.k}</dt>
                  <dd>{item.v}</dd>
                </div>
              ))}
            </dl>
          ) : null}
        </>
      )}
    </article>
  );
}

export default function RobotJobs() {
  const { session } = useAuth();
  const [group, setGroup] = useState<JobIndustryGroup | "all">("all");
  const [timing, setTiming] = useState<JobTiming | "all">("all");
  const [openId, setOpenId] = useState("j1");

  usePageMeta({
    title: "Robot jobs — Ready For Robots",
    description:
      "Work a robot could be hired for: one company and one workflow per job, scored on seven factors.",
    path: "/jobs",
  });

  const jobs = useMemo(
    () => rankJobs(EXAMPLE_JOBS, { group, timing }),
    [group, timing]
  );
  const hidden = jobs.filter((job) => job.locked).length;

  return (
    <div className="rfr-editorial rfr-jobs">
      <SiteHeader signedIn={Boolean(session)} />
      <section className="rfr-jobs-hero">
        <div className="rfr-jobs-eyebrow">
          <span>ROBOT JOBS</span>
          <span>{jobs.length} JOBS SHOWN · EXAMPLE</span>
        </div>
        <div className="rfr-jobs-hero-row">
          <h1>
            Work a robot
            <br />
            could be hired for.
          </h1>
          <div className="rfr-jobs-hero-side">
            <p>
              Each job is one company and one workflow, scored on seven
              factors. Have a robot? Paste its page and we rank these for your
              robot.
            </p>
            <div className="rfr-jobs-hero-ctas">
              <a className="rfr-jobs-primary" href="/?visit=jobs">
                Rank for my robot
              </a>
              <a className="rfr-jobs-outline" href="/?visit=candidates">
                Post a robot job · free
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="rfr-jobs-filters">
        <FilterRow
          label="Industry"
          options={INDUSTRY_FILTERS}
          value={group}
          onPick={setGroup}
        />
        <div className="rfr-jobs-filter-row">
          <FilterRow
            label="Timing"
            options={TIMING_FILTERS}
            value={timing}
            onPick={setTiming}
          />
          <span className="rfr-jobs-sort">SORTED BY SCORE</span>
          <span className="rfr-jobs-example">EXAMPLE DATA</span>
        </div>
      </section>

      <section className="rfr-jobs-list">
        {jobs.length ? (
          jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              open={openId === job.id}
              onToggle={() => setOpenId(openId === job.id ? "" : job.id)}
              signedIn={Boolean(session)}
            />
          ))
        ) : (
          <p className="rfr-jobs-empty">No example jobs match these filters.</p>
        )}

        {hidden > 0 ? (
          <div className="rfr-jobs-gate">
            <div>
              <span>{hidden} MORE JOBS IN THIS VIEW</span>
              <strong>See every robot job, ranked for your robots.</strong>
              <p>
                Founding seller, $49/month, locked while you stay. Includes
                alerts when a new RFP fits one of your robots.
              </p>
            </div>
            <a href="/pricing">See plans</a>
          </div>
        ) : null}

        <p className="rfr-jobs-note">
          Scores average seven factors, weighted equally: workflow fit, scale,
          labor economics, peer adoption, timing, decision-maker access and
          adoption path. <span>est</span> marks a factor filled from the
          industry baseline because we have no company-specific evidence yet.
          Companies above are examples.
        </p>
      </section>
      <SiteFooter />
    </div>
  );
}
