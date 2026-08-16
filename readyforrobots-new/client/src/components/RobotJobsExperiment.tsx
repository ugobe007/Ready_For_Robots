/**
 * /jobs — robot → jobs conversion surface.
 * Fixture-backed. No CRM / filters / dashboards.
 * Funnel: submit → capabilities → discover → jobs → see all → signup
 * Personalized: /jobs/{slug}?src= lands inside results.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import { Check } from "lucide-react";
import demo from "@/data/rdd_demo_jobs.json";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
import { mapUrlToEnvelope } from "@/lib/robotJobsEnvelopeMap";
import PixelIcon from "@/components/PixelIcon";
import {
  FACE_EMERALD,
  KARE_ARROW,
  KARE_FACE,
  KARE_INSPECT,
  KARE_PALLET,
  KARE_SCRUB,
  KARE_TRANSPORT,
  type PixelMap,
} from "@/lib/kareIcons";
import { MacWindow, macAccent, macInk, macMuted, macRule } from "@/components/jobs/MacChrome";
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
  "inline-flex items-center justify-center gap-2 rounded-md bg-emerald-500 px-4 py-2.5 text-sm font-bold text-[#04100a] transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40";
const eyebrowClass =
  "font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500";
const proofCardClass =
  "group flex items-center justify-between border border-slate-600 bg-[#0a1327] px-4 py-3 text-left transition hover:border-emerald-500/40";
const panelClass = "overflow-hidden border border-slate-600 bg-[#0b162f]";
const mutedClass = "text-sm text-slate-400";
const titleClass = "font-display font-bold tracking-tight text-slate-100";
const faceOnCta = (
  <PixelIcon map={KARE_FACE} scale={2} fill="#04100a" background="transparent" />
);

type BoardJob = {
  id: string;
  title: string;
  industry: string;
  path: string;
  classLabel: string;
  icon: PixelMap;
  status?: "OPEN" | "NEW";
};

const BOARD_JOBS: BoardJob[] = [
  {
    id: "01",
    title: "Return empty totes",
    industry: "Specialty pharma",
    path: "PACK → OPERATING AREA",
    classLabel: "TRANSPORT / AMR",
    icon: KARE_TRANSPORT,
    status: "OPEN",
  },
  {
    id: "02",
    title: "Deliver finished kits",
    industry: "Aerospace",
    path: "KITTING → PRODUCTION LINE",
    classLabel: "TRANSPORT / AMR",
    icon: KARE_TRANSPORT,
    status: "OPEN",
  },
  {
    id: "03",
    title: "Move medication carts",
    industry: "Healthcare",
    path: "PHARMACY → PATIENT UNITS",
    classLabel: "TRANSPORT / AMR",
    icon: KARE_TRANSPORT,
  },
  {
    id: "04",
    title: "Stack finished cases",
    industry: "Manufacturing",
    path: "CONVEYOR → PALLET",
    classLabel: "PALLETIZING",
    icon: KARE_PALLET,
  },
  {
    id: "05",
    title: "Scrub terminal floors",
    industry: "Airport · Overnight",
    path: "CONCOURSE · OVERNIGHT",
    classLabel: "CLEANING / SCRUB",
    icon: KARE_SCRUB,
    status: "NEW",
  },
  {
    id: "06",
    title: "Inspect equipment",
    industry: "Industrial",
    path: "ROUTE → EQUIPMENT",
    classLabel: "INSPECTION",
    icon: KARE_INSPECT,
  },
];

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

const QUALIFY_CHECKS = [
  "whether the work is still being done manually",
  "how much work exists",
  "whether autonomous robots are already being used",
  "who owns the automation decision",
  "whether there is a reason to act now",
] as const;

function whyYourRobot(job: Job, family: string): string {
  if (family === "floor_scrub") {
    return "Autonomously scrub repeatable hard-floor routes during off-peak hours.";
  }
  const iface = (job.requirements as { load_interface?: string } | undefined)?.load_interface;
  if (iface === "cart") {
    return "Move carts and orders along repeatable indoor routes.";
  }
  if (iface === "kit") {
    return "Carry kits and totes point-to-point between work areas.";
  }
  return "Move totes point-to-point between work areas.";
}

function evidenceLabel(job: Job): string {
  if (job.evidence_grade === "E1" || job.promotion_class === "DIRECT") return "Strong";
  if (job.evidence_grade === "E2") return "Moderate";
  return "Emerging";
}

function placeLine(job: Job): string {
  const loc = (job.locality || "").trim();
  if (loc) return loc;
  return job.company_name;
}

function srcFromQuery(): string | null {
  if (typeof window === "undefined") return null;
  return (new URLSearchParams(window.location.search).get("src") || "").trim() || null;
}

function ProofCards({ src }: { src: string | null }) {
  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2">
      {demoProfilesForProof().map((p) => (
        <Link key={p.profileKey} href={jobsPathForSlug(p.slug, src)} className={proofCardClass} style={{ borderColor: macRule }}>
          <span>
            <span className="block text-sm font-bold" style={{ color: macInk }}>
              {p.displayName}
            </span>
            <span className="mt-0.5 block text-xs font-bold" style={{ color: macAccent }}>
              {p.jobCount} jobs found
            </span>
          </span>
          <PixelIcon map={KARE_ARROW} scale={2} fill={macInk} background="transparent" />
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
  const [qualifyOpen, setQualifyOpen] = useState(false);
  const [qualifyRequested, setQualifyRequested] = useState(false);
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
    setQualifyOpen(false);
    setQualifyRequested(false);
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
    setQualifyOpen(false);
    setQualifyRequested(false);
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
    setQualifyOpen(false);
    setQualifyRequested(false);
    recordJobView(next);
  }

  function onOpenQualify() {
    setQualifyOpen(true);
    trackRobotJobsFunnel("qualify_opened", {
      ...funnelBase(),
      profile_key: profileKey,
      persona: personaRef.current,
      src: srcRef.current,
      robot_name: robotName,
      capability_family: profile?.capability_family ?? null,
      job_key: job?.job_key ?? null,
      company_name: job?.company_name ?? null,
      locality: job?.locality ?? null,
    });
  }

  function onRequestQualify() {
    setQualifyRequested(true);
    trackRobotJobsFunnel("qualify_requested", {
      ...funnelBase(),
      profile_key: profileKey,
      persona: personaRef.current,
      src: srcRef.current,
      robot_name: robotName,
      capability_family: profile?.capability_family ?? null,
      job_key: job?.job_key ?? null,
      company_name: job?.company_name ?? null,
      locality: job?.locality ?? null,
    });
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
        <div className="grid min-h-[min(640px,calc(100vh-68px))] grid-cols-1 overflow-hidden rounded-lg border border-slate-600 bg-[#0b162f] lg:grid-cols-[minmax(0,0.38fr)_minmax(0,0.62fr)]">
          {/* LEFT — FIND */}
          <div className="flex flex-col border-b border-slate-600 p-5 sm:p-6 lg:border-b-0 lg:border-r lg:border-slate-600">
            <h1 className={`${titleClass} text-[2.15rem] leading-[1.05] sm:text-[2.4rem]`}>
              Find jobs
              <br />
              for your robot.
            </h1>
            <p className="mt-3 text-[15px] leading-snug text-slate-300">
              Robots need jobs. We find the work.
            </p>

            <label
              className="mt-7 block font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400"
              htmlFor="robot-url"
            >
              What robot needs a job?
            </label>
            <input
              id="robot-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onContinueUrl();
              }}
              placeholder="Paste product URL"
              className="mt-1.5 w-full rounded-md border border-slate-600 bg-[#081126] px-3 py-2.5 font-mono text-[13px] text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-400"
            />
            <button
              type="button"
              onClick={onContinueUrl}
              disabled={!url.trim()}
              className={`${ctaClass} mt-2 w-full`}
            >
              {faceOnCta}
              Find Jobs →
            </button>

            <div className="mt-auto border-t border-slate-700 pt-4">
              <p className={eyebrowClass}>How it works</p>
              <ol className="mt-2 space-y-1 font-mono text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                <li>
                  <span className="text-emerald-400">[1]</span> Robot
                </li>
                <li>
                  <span className="text-emerald-400">[2]</span> Capabilities
                </li>
                <li>
                  <span className="text-emerald-400">[3]</span> Jobs
                </li>
              </ol>
            </div>
          </div>

          {/* RIGHT — JOB BOARD */}
          <div className="flex min-h-0 flex-col bg-[#081126]">
            <div className="flex items-center justify-between border-b border-slate-600 px-4 py-2">
              <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-200">
                Robot Job Board
              </p>
              <p className="font-mono text-[11px] font-semibold text-slate-500">
                {String(BOARD_JOBS.length).padStart(2, "0")}
              </p>
            </div>

            <ul className="flex-1 divide-y divide-slate-700/90 overflow-auto">
              {BOARD_JOBS.map((job) => (
                <li key={job.id} className="flex items-start gap-3 px-4 py-3">
                  <span className="mt-0.5 w-5 shrink-0 font-mono text-[11px] font-semibold text-slate-500">
                    {job.id}
                  </span>
                  <span className="mt-0.5 shrink-0">
                    <PixelIcon
                      map={job.icon}
                      scale={2}
                      fill={FACE_EMERALD}
                      background="transparent"
                    />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h2 className="font-display text-[13px] font-bold uppercase leading-tight tracking-tight text-slate-100">
                      {job.title}
                    </h2>
                    <p className="mt-0.5 text-[12px] text-slate-400">{job.industry}</p>
                    <p className="mt-1 font-mono text-[10px] font-semibold tracking-[0.1em] text-slate-300">
                      {job.path}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {step === "unsupported" && (
        <MacWindow title="No Jobs Yet" className="mx-auto w-full max-w-3xl">
          <div className="p-5 sm:p-6">
          {intro ? (
            <>
              <h1 className={`${titleClass} text-2xl sm:text-3xl`}>{intro.headline}</h1>
              <p className={`mt-3 max-w-md text-sm leading-relaxed ${mutedClass}`}>{intro.subhead}</p>
            </>
          ) : (
            <>
              <p className={mutedClass}>We analyzed {robotName}.</p>
              <h2 className={`mt-2 ${titleClass} text-2xl sm:text-3xl`}>
                We don&apos;t have jobs for this robot yet
              </h2>
              <p className={`mt-3 max-w-md text-sm leading-relaxed ${mutedClass}`}>
                {unsupportedReason || "No matching job library for this robot yet"}. Right now we can
                show real jobs for warehouse AMRs and floor-scrubbing robots.
              </p>
            </>
          )}
          <p className={`mt-8 ${eyebrowClass}`}>See what we&apos;ve already found</p>
          <ProofCards src={src} />
          <Link
            href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
            className="mt-6 inline-block text-sm font-bold underline"
            style={{ color: macAccent }}
          >
            Try another robot
          </Link>
          </div>
        </MacWindow>
      )}

      {step === "capabilities" && profile && (
        <MacWindow title={`Capabilities — ${robotName}`} className="mx-auto w-full max-w-3xl">
          <div className="p-5 sm:p-6">
          <p className={mutedClass}>We analyzed {robotName}.</p>
          <h2 className={`mt-2 ${titleClass} text-2xl sm:text-3xl`}>It appears capable of:</h2>
          <ul className={`mt-5 space-y-2 border-2 p-4`} style={{ borderColor: macRule }}>
            {profile.can_actions.map((action) => (
              <li key={action} className="flex items-start gap-2.5 text-sm" style={{ color: macInk }}>
                <Check className="mt-0.5 h-4 w-4 shrink-0" style={{ color: macAccent }} aria-hidden />
                <span>{action}</span>
              </li>
            ))}
          </ul>
          <p className={`mt-5 text-sm ${mutedClass}`}>Looks right?</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" onClick={onConfirmCapabilities} className={ctaClass} style={{ borderColor: macRule }}>
              {faceOnCta}
              Find Jobs →
            </button>
            <Link
              href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
              className="border-2 bg-[#0a1327] px-4 py-2.5 text-sm font-bold"
              style={{ borderColor: macRule, color: macInk }}
            >
              Back
            </Link>
          </div>
          </div>
        </MacWindow>
      )}

      {step === "discovering" && (
        <MacWindow title="Searching…" className="mx-auto w-full max-w-lg">
          <div className="flex flex-col items-center px-6 py-12 text-center" aria-live="polite">
          <div className="border-2 p-3" style={{ borderColor: macRule, background: macAccent }}>
            <PixelIcon map={KARE_FACE} scale={4} fill="#ffffff" background="transparent" />
          </div>
          <p className={`mt-5 text-lg ${titleClass}`}>
            Searching for work {robotName} can do…
          </p>
          <p className={`mt-2 max-w-sm text-sm leading-relaxed ${mutedClass}`}>
            Matching its capabilities to localized jobs in the open economy.
          </p>
          </div>
        </MacWindow>
      )}

      {step === "jobs" && profile && job && (
        <MacWindow
          title={`Jobs — ${robotName}`}
          trailing={
            <span className="font-mono text-[10px] font-bold" style={{ color: macMuted }}>
              {jobIndex + 1}/{previewCount}
            </span>
          }
          className="mx-auto w-full max-w-3xl"
        >
          <div className="p-5 sm:p-6">
          {intro ? (
            <>
              <h1 className={`${titleClass} text-2xl sm:text-3xl`}>{intro.headline}</h1>
              <p className={`mt-2 max-w-xl text-sm leading-relaxed ${mutedClass}`}>{intro.subhead}</p>
            </>
          ) : (
            <h1 className={`${titleClass} text-2xl sm:text-3xl`}>
              We found {totalJobs} jobs for {robotName}.
            </h1>
          )}

          <article className="mt-5 border-2 p-4 sm:p-5" style={{ borderColor: macRule }}>
            <p className={eyebrowClass}>Find</p>
            <h2 className={`mt-2 ${titleClass} text-xl uppercase sm:text-2xl`}>
              {job.robot_compatible_task}
            </h2>
            <p className={`mt-2 text-sm ${mutedClass}`}>
              {job.company_name}
              {job.locality ? ` · ${placeLine(job)}` : ""}
            </p>

            <dl className="mt-5 space-y-3 text-sm">
              <div>
                <dt className={eyebrowClass}>The work</dt>
                <dd className="mt-1 leading-relaxed" style={{ color: macInk }}>
                  {job.observed_workflow}
                </dd>
              </div>
              <div>
                <dt className={eyebrowClass}>Your robot could</dt>
                <dd className="mt-1 leading-relaxed" style={{ color: macInk }}>
                  {whyYourRobot(job, profile.capability_family)}
                </dd>
              </div>
              <div>
                <dt className={eyebrowClass}>Evidence</dt>
                <dd className="mt-1 text-sm font-bold" style={{ color: macAccent }}>
                  {evidenceLabel(job)}
                </dd>
              </div>
              {job.unknowns?.length ? (
                <div>
                  <dt className={eyebrowClass}>Still unknown</dt>
                  <dd className={`mt-1 leading-relaxed ${mutedClass}`}>{job.unknowns.join(" · ")}</dd>
                </div>
              ) : null}
            </dl>

            {!qualifyOpen ? (
              <button
                type="button"
                onClick={onOpenQualify}
                className={`${ctaClass} mt-6 w-full sm:w-auto`}
                style={{ borderColor: macRule }}
              >
                Qualify This Job →
              </button>
            ) : (
              <div className="mt-6 border-2 p-4" style={{ borderColor: macRule }}>
                <h3 className="text-sm font-bold" style={{ color: macInk }}>
                  Qualify this job
                </h3>
                <p className={`mt-2 text-sm leading-relaxed ${mutedClass}`}>
                  We&apos;ll investigate whether this job deserves your sales team&apos;s time.
                </p>
                <p className={`mt-4 ${eyebrowClass}`}>We&apos;ll look for</p>
                <ul className="mt-2 space-y-1">
                  {QUALIFY_CHECKS.map((item) => (
                    <li key={item} className="flex gap-2 text-sm" style={{ color: macInk }}>
                      <span style={{ color: macAccent }}>[·]</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
                {qualifyRequested ? (
                  <div className="mt-4 border-2 px-3 py-3" style={{ borderColor: macAccent }}>
                    <p className="text-sm font-bold" style={{ color: macAccent }}>
                      Qualification requested
                    </p>
                    <p className={`mt-1.5 text-sm leading-relaxed ${mutedClass}`}>
                      Next: a Pursuit Brief from desk research — whether to pursue, qualify further,
                      watch, or skip. Additional verification may be required before a final
                      recommendation.
                    </p>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={onRequestQualify}
                    className={`${ctaClass} mt-4 w-full sm:w-auto`}
                    style={{ borderColor: macRule }}
                  >
                    {faceOnCta}
                    Request Qualification
                  </button>
                )}
              </div>
            )}
          </article>

          <button
            type="button"
            onClick={onNextJob}
            className="mt-5 text-sm font-bold underline"
            style={{ color: macAccent }}
          >
            {jobIndex + 1 >= previewCount ? "See all jobs →" : "See next job →"}
          </button>
          </div>
        </MacWindow>
      )}

      {step === "gate" && profile && (
        <MacWindow title="See All Jobs" className="mx-auto w-full max-w-3xl">
          <div className="p-5 sm:p-6">
          <h2 className={`${titleClass} text-2xl sm:text-3xl`}>
            See all {totalJobs} jobs for {robotName}
          </h2>
          <p className={`mt-3 max-w-md text-sm leading-relaxed ${mutedClass}`}>
            You&apos;ve seen {previewCount} jobs matched to its capabilities. Create an account to unlock
            the rest.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Link
              href={signupHref}
              onClick={onSeeAll}
              className={ctaClass}
              style={{ borderColor: macRule }}
            >
              {faceOnCta}
              See all {totalJobs} jobs →
            </Link>
          </div>
          <button
            type="button"
            onClick={() => {
              setJobIndex(0);
              setQualifyOpen(false);
              setQualifyRequested(false);
              setStep("jobs");
              recordJobView(0);
            }}
            className="mt-4 text-sm font-bold underline"
            style={{ color: macAccent }}
          >
            Review jobs again
          </button>
          <Link
            href={src ? `/jobs?src=${encodeURIComponent(src)}` : "/jobs"}
            className={`mt-6 block text-xs font-bold ${mutedClass}`}
          >
            Try another robot
          </Link>
          </div>
        </MacWindow>
      )}
    </section>
  );
}
