/**
 * /jobs — robot → jobs conversion surface.
 * Fixture-backed. No CRM / filters / dashboards.
 * Funnel: submit → capabilities → discover → jobs → see all → signup
 * Personalized: /jobs/{slug}?src= lands inside results.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, Check, ChevronRight } from "lucide-react";
import demo from "@/data/rdd_demo_jobs.json";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
import { mapUrlToEnvelope } from "@/lib/robotJobsEnvelopeMap";
import PixelIcon from "@/components/PixelIcon";
import { FACE_WHITE, KARE_FACE } from "@/lib/kareIcons";
import {
  demoProfilesForProof,
  jobsPathForProfile,
  jobsPathForSlug,
  PROFILE_KEY_TO_SLUG,
  resolveJobsSlug,
  type JobsSlugConfig,
} from "@/lib/jobsSlugs";

type Profile = (typeof demo.profiles)[number];
type Job = (typeof demo.jobs)[keyof typeof demo.jobs][number];
type Step = "enter" | "unsupported" | "capabilities" | "discovering" | "jobs" | "gate";

const PREVIEW_FREE = 5;
const DISCOVER_MS = 1800;

const ctaClass =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40";
const eyebrowClass =
  "text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400";
const proofCardClass =
  "group flex items-center justify-between rounded-xl border border-slate-600 bg-[#0b162f] px-4 py-3.5 text-left transition hover:border-emerald-400/60 hover:bg-[#0d1c38]";
const panelClass =
  "overflow-hidden rounded-xl border border-slate-700/80 bg-[#0b162f]";
const mutedClass = "text-sm text-slate-400";
const titleClass = "font-display font-bold tracking-tight text-slate-100";
const faceOnCta = (
  <PixelIcon map={KARE_FACE} scale={2} fill={FACE_WHITE} background="transparent" />
);

function profileByKey(key: string): Profile | undefined {
  return demo.profiles.find((p) => p.profile_key === key);
}

function jobsFor(key: string): Job[] {
  const map = demo.jobs as Record<string, Job[]>;
  return map[key] ?? [];
}

function titleCaseToken(s: string): string {
  return s
    .replace(/[-_]+/g, " ")
    .replace(/\.(html?|php|aspx?)$/i, "")
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Best-effort product name from a URL for personalization copy. */
export function robotNameFromUrl(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  try {
    const withProto = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    const u = new URL(withProto);
    const parts = u.pathname.split("/").filter(Boolean);
    const skip = new Set(["products", "product", "robots", "robot", "solutions", "en", "us"]);
    for (let i = parts.length - 1; i >= 0; i--) {
      const p = parts[i];
      if (!skip.has(p.toLowerCase()) && p.length > 1) return titleCaseToken(decodeURIComponent(p));
    }
    const host = u.hostname.replace(/^www\./, "").split(".")[0];
    if (host && host.length > 1) return titleCaseToken(host);
  } catch {
    return titleCaseToken(trimmed.slice(0, 48));
  }
  return null;
}

const DISCOVERED_WORK = [
  {
    title: "Return empty totes",
    context: "Specialty pharma · Newark, DE",
    path: "Pack → operating area",
  },
  {
    title: "Deliver finished kits",
    context: "Aerospace manufacturing · Foley, AL",
    path: "Kitting → production line",
  },
  {
    title: "Move medication carts",
    context: "Hospital operations · Newark, DE",
    path: "Pharmacy → patient units",
  },
  {
    title: "Stack finished cases",
    context: "Manufacturing · Kinston, NC",
    path: "Packaging line → pallet",
  },
] as const;

function whyYourRobot(job: Job, family: string): string {
  if (family === "floor_scrub") {
    return "Hard-floor scrubbing on a repeatable route matches its autonomous scrub capabilities.";
  }
  const iface = (job.requirements as { load_interface?: string } | undefined)?.load_interface;
  if (iface === "cart") {
    return "Cart / order movement matches its mobility and load-handling capabilities.";
  }
  if (iface === "kit") {
    return "Kit and tote replenishment matches its point-to-point transport capabilities.";
  }
  return "Point-to-point tote transport matches its mobility and load-handling capabilities.";
}

function worthLabel(job: Job): string {
  if (job.fit === "H" || job.investigate_status === "yes") return "HIGH";
  if (job.fit === "M" || job.investigate_status === "weak") return "MEDIUM";
  return "LOW";
}

function srcFromQuery(): string | null {
  if (typeof window === "undefined") return null;
  return (new URLSearchParams(window.location.search).get("src") || "").trim() || null;
}

function ProofCards({ src }: { src: string | null }) {
  return (
    <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
      {demoProfilesForProof().map((p) => (
        <Link
          key={p.profileKey}
          href={jobsPathForSlug(p.slug, src)}
          className={proofCardClass}
        >
          <span>
            <span className="block text-sm font-semibold text-slate-100">{p.displayName}</span>
            <span className="mt-0.5 block text-xs font-semibold text-emerald-300">
              {p.jobCount} jobs found
            </span>
          </span>
          <ArrowRight
            className="h-4 w-4 shrink-0 text-slate-500 transition group-hover:text-emerald-300"
            aria-hidden
          />
        </Link>
      ))}
    </div>
  );
}

type Props = {
  /** /jobs/:slug — capability owner personalization */
  slug?: string;
};

export default function RobotJobsExperiment({ slug }: Props) {
  const slugConfig = useMemo(() => resolveJobsSlug(slug), [slug]);
  const [step, setStep] = useState<Step>("enter");
  const [url, setUrl] = useState("");
  const [profileKey, setProfileKey] = useState<string | null>(null);
  const [robotName, setRobotName] = useState("your robot");
  const [intro, setIntro] = useState<{ headline: string; subhead: string } | null>(null);
  const [jobCountOverride, setJobCountOverride] = useState<number | null>(null);
  const [unsupportedReason, setUnsupportedReason] = useState<string | null>(null);
  const [jobIndex, setJobIndex] = useState(0);
  const [jobsViewed, setJobsViewed] = useState(0);
  const sessionId = useRef(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `rdd_${Date.now()}`,
  );
  const srcRef = useRef(srcFromQuery());
  const personaRef = useRef<string | null>(slugConfig?.persona ?? null);
  const slugRef = useRef<string | null>(slugConfig?.slug ?? null);
  const fired3Plus = useRef(false);
  const discoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bootedSlug = useRef<string | null>(null);

  const funnelBase = () => ({
    session_id: sessionId.current,
    ...(personaRef.current ? { persona: personaRef.current } : {}),
    ...(srcRef.current ? { src: srcRef.current } : {}),
    ...(slugRef.current ? { slug: slugRef.current } : {}),
  });

  function applySlugConfig(config: JobsSlugConfig) {
    personaRef.current = config.persona;
    slugRef.current = config.slug;
    setRobotName(config.displayName);
    setIntro({ headline: config.headline, subhead: config.subhead });
    setJobCountOverride(config.jobCount > 0 ? config.jobCount : null);
    setUnsupportedReason(null);
    setJobIndex(0);
    setJobsViewed(0);
    fired3Plus.current = false;

    if (!config.profileKey) {
      setProfileKey(null);
      setStep("unsupported");
      setUnsupportedReason(config.subhead);
      return;
    }

    setProfileKey(config.profileKey);
    setStep("jobs");
    setJobsViewed(1);
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      profile_key: config.profileKey,
      robot_name: config.displayName,
      source: "slug",
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      profile_key: config.profileKey,
      robot_name: config.displayName,
      job_count: config.jobCount,
      source: "slug",
    });
    trackRobotJobsFunnel("first_job_viewed", {
      ...funnelBase(),
      profile_key: config.profileKey,
      robot_name: config.displayName,
      source: "slug",
    });
    const first = jobsFor(config.profileKey)[0];
    trackRobotJobsFunnel("job_viewed", {
      ...funnelBase(),
      profile_key: config.profileKey,
      job_index: 0,
      job_key: first?.job_key ?? null,
      company_name: first?.company_name ?? null,
      locality: first?.locality ?? null,
      source: "slug",
    });
  }

  useEffect(() => {
    srcRef.current = srcFromQuery();
    if (slugConfig) {
      personaRef.current = slugConfig.persona;
      slugRef.current = slugConfig.slug;
    } else {
      personaRef.current = null;
      slugRef.current = null;
    }
    trackRobotJobsFunnel("experiment_view", {
      ...funnelBase(),
      path: typeof window !== "undefined" ? window.location.pathname : "/jobs",
    });

    if (slugConfig) {
      if (bootedSlug.current !== slugConfig.slug) {
        bootedSlug.current = slugConfig.slug;
        applySlugConfig(slugConfig);
      }
    } else {
      bootedSlug.current = null;
    }

    return () => {
      if (discoverTimer.current) clearTimeout(discoverTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- boot once per slug
  }, [slugConfig?.slug]);

  const profile = profileKey ? profileByKey(profileKey) : undefined;
  const jobs = useMemo(() => (profileKey ? jobsFor(profileKey) : []), [profileKey]);
  const job = jobs[jobIndex];
  const totalJobs = jobCountOverride ?? profile?.job_count_total ?? jobs.length;
  const previewCount = Math.min(PREVIEW_FREE, jobs.length);
  const src = srcRef.current;

  function beginWithMappedRobot(opts: {
    key: string;
    name: string;
    source: "url" | "demo" | "query";
    submittedUrl?: string;
  }) {
    setUnsupportedReason(null);
    setIntro(null);
    setJobCountOverride(null);
    setProfileKey(opts.key);
    setRobotName(opts.name);
    setJobIndex(0);
    setJobsViewed(0);
    fired3Plus.current = false;
    setStep("capabilities");
    slugRef.current = PROFILE_KEY_TO_SLUG[opts.key] ?? null;
    trackRobotJobsFunnel("robot_submitted", {
      ...funnelBase(),
      profile_key: opts.key,
      robot_name: opts.name,
      source: opts.source,
      url: opts.submittedUrl || null,
    });
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      profile_key: opts.key,
      robot_name: opts.name,
      source: opts.source,
    });
  }

  function onContinueUrl() {
    const name = robotNameFromUrl(url) || "your robot";
    const match = mapUrlToEnvelope(url);
    if (match.status === "unsupported") {
      setRobotName(name);
      setProfileKey(null);
      setIntro(null);
      setUnsupportedReason(match.reason);
      setStep("unsupported");
      trackRobotJobsFunnel("robot_submitted", {
        ...funnelBase(),
        robot_name: name,
        source: "url",
        url: url.trim(),
        matched: false,
      });
      trackRobotJobsFunnel("unsupported_robot", {
        ...funnelBase(),
        robot_name: name,
        url: url.trim(),
        reason: match.reason,
        guessed_family: match.guessedFamily,
      });
      return;
    }
    beginWithMappedRobot({
      key: match.profileKey,
      name,
      source: "url",
      submittedUrl: url.trim(),
    });
  }

  function onConfirmCapabilities() {
    if (!profileKey) return;
    setStep("discovering");
    trackRobotJobsFunnel("discovery_started", {
      ...funnelBase(),
      profile_key: profileKey,
      robot_name: robotName,
    });
    if (discoverTimer.current) clearTimeout(discoverTimer.current);
    discoverTimer.current = setTimeout(() => {
      setStep("jobs");
      setJobIndex(0);
      setJobsViewed(1);
      trackRobotJobsFunnel("discovery_complete", {
        ...funnelBase(),
        profile_key: profileKey,
        robot_name: robotName,
        job_count: profileByKey(profileKey)?.job_count_total ?? 0,
      });
      trackRobotJobsFunnel("first_job_viewed", {
        ...funnelBase(),
        profile_key: profileKey,
        robot_name: robotName,
      });
      trackRobotJobsFunnel("job_viewed", {
        ...funnelBase(),
        profile_key: profileKey,
        job_index: 0,
        job_key: jobsFor(profileKey)[0]?.job_key ?? null,
        company_name: jobsFor(profileKey)[0]?.company_name ?? null,
        locality: jobsFor(profileKey)[0]?.locality ?? null,
      });
    }, DISCOVER_MS);
  }

  function recordJobView(nextIndex: number) {
    const viewed = nextIndex + 1;
    const j = jobs[nextIndex];
    setJobsViewed(viewed);
    trackRobotJobsFunnel("job_viewed", {
      ...funnelBase(),
      profile_key: profileKey,
      job_index: nextIndex,
      jobs_viewed: viewed,
      job_key: j?.job_key ?? null,
      company_name: j?.company_name ?? null,
      locality: j?.locality ?? null,
    });
    if (viewed >= 3 && !fired3Plus.current) {
      fired3Plus.current = true;
      trackRobotJobsFunnel("jobs_3plus_viewed", {
        ...funnelBase(),
        profile_key: profileKey,
        jobs_viewed: viewed,
      });
    }
  }

  function onNextJob() {
    if (jobIndex + 1 >= previewCount) {
      setStep("gate");
      trackRobotJobsFunnel("preview_complete", {
        ...funnelBase(),
        profile_key: profileKey,
        jobs_viewed: jobsViewed,
      });
      return;
    }
    const next = jobIndex + 1;
    setJobIndex(next);
    recordJobView(next);
  }

  function onSeeAll() {
    trackRobotJobsFunnel("see_all_clicked", {
      ...funnelBase(),
      profile_key: profileKey,
      robot_name: robotName,
      jobs_viewed: jobsViewed,
      job_count_total: totalJobs,
    });
    trackSignupStart({
      source: "robot_jobs",
      profile_key: profileKey,
      robot_name: robotName,
      ...funnelBase(),
    });
  }

  const signupHref = (() => {
    const next =
      slugRef.current != null
        ? jobsPathForSlug(slugRef.current, srcRef.current)
        : profileKey
          ? jobsPathForProfile(profileKey, srcRef.current)
          : srcRef.current
            ? `/jobs?src=${encodeURIComponent(srcRef.current)}`
            : "/jobs";
    const signupParams = new URLSearchParams();
    signupParams.set("next", next);
    signupParams.set("src", "robot_jobs");
    if (personaRef.current) signupParams.set("persona", personaRef.current);
    return `/signup?${signupParams.toString()}`;
  })();

  return (
    <section className="flex min-h-[70vh] flex-col" aria-label="Find jobs for your robot">
      {step === "enter" && (
        <div className="flex flex-1 flex-col">
          <h1 className={`${titleClass} text-3xl sm:text-4xl`}>Find jobs for your robot.</h1>
          <p className="mt-3 max-w-xl text-base leading-relaxed text-slate-300 sm:text-lg">
            Give us your robot. We&apos;ll search for real work that matches what it can do.
          </p>

          <label className="mt-10 block text-xs font-semibold text-slate-300" htmlFor="robot-url">
            Paste robot product URL
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-stretch">
            <input
              id="robot-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onContinueUrl();
              }}
              placeholder="https://yourrobot.com/product"
              className="min-w-0 flex-1 rounded-lg border border-slate-600 bg-[#0a1327] px-3.5 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
            />
            <button
              type="button"
              onClick={onContinueUrl}
              disabled={!url.trim()}
              className={ctaClass}
            >
              {faceOnCta}
              Find Jobs
              <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <p className={`mt-12 ${eyebrowClass}`}>See what we&apos;ve already found</p>
          <ProofCards src={src} />

          <p className={`mt-14 ${eyebrowClass}`}>Real work we&apos;ve discovered</p>
          <ul className={`mt-4 ${panelClass}`}>
            {DISCOVERED_WORK.map((w, i) => (
              <li
                key={w.title}
                className={`px-4 py-4 sm:px-5 ${i > 0 ? "border-t border-slate-700/80" : ""}`}
              >
                <div className="flex gap-3">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" aria-hidden />
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{w.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{w.context}</p>
                    <p className="mt-0.5 font-mono text-[11px] text-slate-500">{w.path}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <p className="mt-10 text-sm leading-relaxed text-slate-500">
            We find the work first. Then determine whether your robot fits.
          </p>
        </div>
      )}

      {step === "unsupported" && (
        <div className="flex flex-1 flex-col">
          {intro ? (
            <>
              <h1 className={`${titleClass} text-2xl sm:text-3xl`}>{intro.headline}</h1>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">{intro.subhead}</p>
            </>
          ) : (
            <>
              <p className={mutedClass}>We analyzed {robotName}.</p>
              <h2 className={`mt-2 ${titleClass} text-2xl sm:text-3xl`}>
                We don&apos;t have jobs for this robot yet
              </h2>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">
                {unsupportedReason || "No matching job library for this robot yet"}. Right now we can
                show real jobs for warehouse AMRs and floor-scrubbing robots.
              </p>
            </>
          )}
          <p className={`mt-10 ${eyebrowClass}`}>See what we&apos;ve already found</p>
          <ProofCards src={src} />
          <Link
            href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
            className="mt-8 text-sm font-medium text-emerald-300 underline-offset-2 hover:underline"
          >
            Try another robot
          </Link>
        </div>
      )}

      {step === "capabilities" && profile && (
        <div className="flex flex-1 flex-col">
          <p className={mutedClass}>We analyzed {robotName}.</p>
          <h2 className={`mt-2 ${titleClass} text-2xl sm:text-3xl`}>It appears capable of:</h2>
          <ul className={`mt-6 space-y-3 ${panelClass} p-4 sm:p-5`}>
            {profile.can_actions.map((action) => (
              <li key={action} className="flex items-start gap-2.5 text-sm text-slate-200">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" aria-hidden />
                <span>{action}</span>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm text-slate-400">Looks right?</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={onConfirmCapabilities} className={ctaClass}>
              {faceOnCta}
              Find Jobs
              <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
            <Link
              href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
              className="rounded-lg border border-slate-600 bg-transparent px-4 py-3 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800/50"
            >
              Back
            </Link>
          </div>
        </div>
      )}

      {step === "discovering" && (
        <div className="flex flex-1 flex-col items-center justify-center py-16 text-center" aria-live="polite">
          <div className="rounded-2xl bg-emerald-600 p-4">
            <PixelIcon map={KARE_FACE} scale={4} fill={FACE_WHITE} background="transparent" />
          </div>
          <p className="mt-6 text-lg font-semibold text-slate-100">
            Searching for work {robotName} can do…
          </p>
          <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
            Matching its capabilities to localized jobs in the open economy.
          </p>
        </div>
      )}

      {step === "jobs" && profile && job && (
        <div className="flex flex-1 flex-col">
          {intro ? (
            <>
              <h1 className={`${titleClass} text-2xl sm:text-3xl`}>{intro.headline}</h1>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-300 sm:text-base">
                {intro.subhead}
              </p>
            </>
          ) : (
            <p className={mutedClass}>
              We found <span className="font-semibold text-slate-100">{totalJobs}</span> jobs matching{" "}
              {robotName}&apos;s capabilities.
            </p>
          )}
          <p className="mt-4 text-xs font-medium text-slate-500">
            Job {jobIndex + 1} of {previewCount}
          </p>

          <article className={`mt-4 flex-1 ${panelClass} p-5 sm:p-6`}>
            <h2 className={`${titleClass} text-xl sm:text-2xl`}>{job.robot_compatible_task}</h2>
            <p className="mt-2 text-sm font-medium text-slate-400">
              {job.company_name}
              {job.locality ? ` · ${job.locality}` : ""}
            </p>

            <dl className="mt-6 space-y-4 text-sm">
              <div>
                <dt className={eyebrowClass}>Why we believe it exists</dt>
                <dd className="mt-1.5 leading-relaxed text-slate-200">{job.why_job}</dd>
              </div>
              <div>
                <dt className={eyebrowClass}>Why {robotName} could do it</dt>
                <dd className="mt-1.5 leading-relaxed text-slate-200">
                  {whyYourRobot(job, profile.capability_family)}
                </dd>
              </div>
              {job.unknowns?.length ? (
                <div>
                  <dt className={eyebrowClass}>What we don&apos;t know</dt>
                  <dd className="mt-1.5 leading-relaxed text-slate-200">{job.unknowns.join(" · ")}</dd>
                </div>
              ) : null}
              <div>
                <dt className={eyebrowClass}>Worth investigating</dt>
                <dd className="mt-1.5 text-sm font-bold tracking-wide text-emerald-300">
                  {worthLabel(job)}
                </dd>
              </div>
            </dl>
          </article>

          <button type="button" onClick={onNextJob} className={`${ctaClass} mt-8 w-full sm:w-auto`}>
            {jobIndex + 1 >= previewCount ? "See all jobs" : "See next job"}
            <ChevronRight className="h-4 w-4" aria-hidden />
          </button>
        </div>
      )}

      {step === "gate" && profile && (
        <div className="flex flex-1 flex-col items-start justify-center">
          <h2 className={`${titleClass} text-2xl sm:text-3xl`}>
            See all {totalJobs} jobs for {robotName}
          </h2>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">
            You&apos;ve seen {previewCount} jobs matched to its capabilities. Create an account to unlock
            the rest.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-emerald-600">
              <PixelIcon map={KARE_FACE} scale={2} fill={FACE_WHITE} background="transparent" />
            </span>
            <Link href={signupHref} onClick={onSeeAll} className={ctaClass}>
              See all {totalJobs} jobs
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </div>
          <button
            type="button"
            onClick={() => {
              setJobIndex(0);
              setStep("jobs");
              recordJobView(0);
            }}
            className="mt-4 text-sm font-medium text-emerald-300 underline-offset-2 hover:underline"
          >
            Review jobs again
          </button>
          <Link
            href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
            className="mt-8 text-xs font-medium text-slate-500 transition hover:text-slate-300"
          >
            Try another robot
          </Link>
        </div>
      )}
    </section>
  );
}
