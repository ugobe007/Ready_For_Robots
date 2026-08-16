/**
 * /jobs — robot → jobs conversion surface.
 * Fixture-backed. No CRM / filters / dashboards.
 * Funnel: submit → capabilities → discover → jobs → see all → signup
 * Personalized: /jobs/{slug}?src= lands inside results.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import demo from "@/data/rdd_demo_jobs.json";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
import { mapUrlToEnvelope } from "@/lib/robotJobsEnvelopeMap";
import { useAuth } from "@/contexts/AuthContext";
import PixelIcon from "@/components/PixelIcon";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import {
  FACE_EMERALD,
  FACE_WHITE,
  KARE_ARROW,
  KARE_FACE,
  KARE_JOB_CARD,
  KARE_QUALIFY,
  KARE_SEARCH,
} from "@/lib/kareIcons";
import { MacWindow, macAccent, macInk, macRule } from "@/components/jobs/MacChrome";
import {
  demoJobsToTape,
  MARKET_TAPE_JOBS,
  type TapeJob,
} from "@/lib/jobsTapeCorpus";
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
type Step = "enter" | "unsupported" | "gate";
type BoardMode = "market" | "status" | "personal";
/** Left funnel process trace under the URL input. */
type TracePhase = "idle" | "url" | "caps" | "search" | "done";

const PREVIEW_FREE = 5;
/** Independent discovery counter seed — not tied to visible row count. */
const MARKET_FOUND_BASE = 140;
/** Persist discovery across signup so auth return restores personal jobs. */
const JOBS_SESSION_KEY = "rfr_jobs_discovery";

type JobsDiscoverySession = {
  profileKey: string;
  robotName: string;
  slug: string | null;
};

function saveJobsDiscoverySession(data: JobsDiscoverySession) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(JOBS_SESSION_KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

function readJobsDiscoverySession(): JobsDiscoverySession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(JOBS_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as JobsDiscoverySession;
    if (!parsed?.profileKey) return null;
    return parsed;
  } catch {
    return null;
  }
}

function FunnelTrace({ phase, jobCount }: { phase: TracePhase; jobCount: number | null }) {
  const countLabel =
    jobCount != null ? `${String(jobCount).padStart(2, "0")} JOBS FOUND` : "JOBS";
  let label = "URL → CAPABILITIES → JOBS";
  if (phase === "url") label = "URL ✓ → CAPABILITIES... → JOBS";
  else if (phase === "caps") label = "URL ✓ → CAPABILITIES ✓ → JOBS...";
  else if (phase === "search") label = "URL ✓ → CAPABILITIES ✓ → SEARCHING...";
  else if (phase === "done") label = `URL ✓ → CAPABILITIES ✓ → ${countLabel}`;

  return (
    <p
      className="mt-2 font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-slate-600"
      aria-live="polite"
    >
      {phase === "done" || phase === "caps" || phase === "search" || phase === "url" ? (
        <span className="text-emerald-500/90">{label}</span>
      ) : (
        label
      )}
    </p>
  );
}

const ctaClass =
  "inline-flex items-center justify-center gap-2 bg-emerald-400 px-4 py-2.5 text-sm font-bold uppercase tracking-[0.06em] text-white transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-45";
const eyebrowClass =
  "font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500";
const proofCardClass =
  "group flex items-center justify-between border border-slate-600 bg-[#0a1327] px-4 py-3 text-left transition hover:border-emerald-500/40";
const mutedClass = "text-sm text-slate-400";
const titleClass = "font-display font-bold tracking-tight text-slate-100";
const faceOnCta = (
  <PixelIcon map={KARE_FACE} scale={3} fill={FACE_WHITE} background="transparent" />
);

const HOW_IT_WORKS = [
  {
    n: "01",
    title: "Show us your robot",
    body: "We identify what it can actually do.",
    icon: KARE_FACE,
    scale: 1.5,
  },
  {
    n: "02",
    title: "We find the work",
    body: "We search for matching physical work.",
    icon: KARE_SEARCH,
    scale: 2,
  },
  {
    n: "03",
    title: "You review the jobs",
    body: "See evidence, fit and unknowns.",
    icon: KARE_JOB_CARD,
    scale: 2,
  },
] as const;

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
  const { session } = useAuth();
  const unlocked = Boolean(session);
  const slugConfig = useMemo(() => resolveJobsSlug(slug), [slug]);
  const [step, setStep] = useState<Step>("enter");
  const [boardMode, setBoardMode] = useState<BoardMode>("market");
  const [statusLines, setStatusLines] = useState<string[]>([]);
  const [tracePhase, setTracePhase] = useState<TracePhase>("idle");
  const [traceJobCount, setTraceJobCount] = useState<number | null>(null);
  const [personalCorpus, setPersonalCorpus] = useState<TapeJob[]>([]);
  const [tapeRunning, setTapeRunning] = useState(true);
  const [selectedTapeKey, setSelectedTapeKey] = useState<string | null>(null);
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
  const boardTimers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const bootedSlug = useRef<string | null>(null);

  const funnelBase = () => ({
    session_id: sessionId.current,
    ...(personaRef.current ? { persona: personaRef.current } : {}),
    ...(srcRef.current ? { src: srcRef.current } : {}),
    ...(slugRef.current ? { slug: slugRef.current } : {}),
  });

  function clearBoardTimers() {
    boardTimers.current.forEach(clearTimeout);
    boardTimers.current = [];
  }

  function boardLater(fn: () => void, ms: number) {
    const id = setTimeout(fn, ms);
    boardTimers.current.push(id);
  }

  function enterPersonalBoard(key: string, name: string) {
    const p = profileByKey(key);
    const list = jobsFor(key);
    const tape = demoJobsToTape(list, p?.capability_family ?? "transport_amr");
    const total = p?.job_count_total ?? list.length;
    const ownerSlug = PROFILE_KEY_TO_SLUG[key] ?? slugRef.current;
    slugRef.current = ownerSlug;
    setProfileKey(key);
    setRobotName(name);
    setPersonalCorpus(tape.length ? tape : MARKET_TAPE_JOBS.slice(0, 8));
    setJobCountOverride(total);
    setBoardMode("personal");
    setStatusLines([]);
    setTracePhase("done");
    setTraceJobCount(total);
    setTapeRunning(true);
    setStep("enter");
    setJobIndex(0);
    setJobsViewed(1);
    setSelectedTapeKey(tape[0]?.key ?? null);
    setQualifyOpen(false);
    setQualifyRequested(false);
    saveJobsDiscoverySession({
      profileKey: key,
      robotName: name,
      slug: ownerSlug,
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      profile_key: key,
      robot_name: name,
      job_count: total,
    });
    trackRobotJobsFunnel("first_job_viewed", {
      ...funnelBase(),
      profile_key: key,
      robot_name: name,
    });
    const first = list[0];
    trackRobotJobsFunnel("job_viewed", {
      ...funnelBase(),
      profile_key: key,
      job_index: 0,
      job_key: first?.job_key ?? null,
      company_name: first?.company_name ?? null,
      locality: first?.locality ?? null,
    });
  }

  function runBoardDiscovery(key: string, name: string) {
    clearBoardTimers();
    const p = profileByKey(key);
    const capCount = String(p?.can_actions?.length ?? 5).padStart(2, "0");
    setStep("enter");
    setBoardMode("status");
    setTapeRunning(false);
    setTracePhase("url");
    setTraceJobCount(null);
    setStatusLines(["Analyzing your robot…"]);
    setSelectedTapeKey(null);
    setQualifyOpen(false);
    setQualifyRequested(false);

    trackRobotJobsFunnel("discovery_started", {
      ...funnelBase(),
      profile_key: key,
      robot_name: name,
    });

    boardLater(() => {
      setTracePhase("caps");
      setStatusLines(["Product found ✓", `Capabilities ${capCount}`]);
    }, 700);
    boardLater(() => {
      setTracePhase("search");
      setStatusLines(["Product found ✓", `Capabilities ${capCount}`, "Searching work…"]);
    }, 1400);
    boardLater(() => {
      setStatusLines([
        "Product found ✓",
        `Capabilities ${capCount}`,
        "Searching work…",
        "> Job found",
        "> Job found",
        "> Job found",
      ]);
    }, 2200);
    boardLater(() => {
      enterPersonalBoard(key, name);
    }, 3200);
  }

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
      setBoardMode("market");
      setTracePhase("idle");
      setTraceJobCount(null);
      return;
    }

    setProfileKey(config.profileKey);
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      profile_key: config.profileKey,
      robot_name: config.displayName,
      source: "slug",
    });
    enterPersonalBoard(config.profileKey, config.displayName);
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
      clearBoardTimers();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- boot once per slug
  }, [slugConfig?.slug]);

  const profile = profileKey ? profileByKey(profileKey) : undefined;
  const jobs = useMemo(() => (profileKey ? jobsFor(profileKey) : []), [profileKey]);
  const job = useMemo(() => {
    if (selectedTapeKey) {
      return jobs.find((j) => j.job_key === selectedTapeKey) ?? jobs[jobIndex];
    }
    return jobs[jobIndex];
  }, [jobs, selectedTapeKey, jobIndex]);
  const totalJobs = jobCountOverride ?? profile?.job_count_total ?? jobs.length;
  const freePreviewCount = Math.min(PREVIEW_FREE, jobs.length);
  const previewCount = unlocked ? jobs.length : freePreviewCount;
  const src = srcRef.current;

  const tapeCorpus = boardMode === "personal" ? personalCorpus : MARKET_TAPE_JOBS;
  const tapeTitle = boardMode === "personal" ? "Jobs For Your Robot" : "Jobs We Found";
  const tapeBase = boardMode === "personal" ? totalJobs : MARKET_FOUND_BASE;
  const tapeStatus = boardMode === "status" ? statusLines : undefined;

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
    runBoardDiscovery(opts.key, opts.name);
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
      setBoardMode("market");
      setTracePhase("idle");
      setTraceJobCount(null);
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

  function onSelectTapeJob(tapeJob: TapeJob) {
    if (boardMode !== "personal") return;
    setSelectedTapeKey(tapeJob.key);
    const idx = jobs.findIndex((j) => j.job_key === tapeJob.key);
    if (idx >= 0) {
      setJobIndex(idx);
      recordJobView(idx);
    }
    setQualifyOpen(false);
    setQualifyRequested(false);
  }

  function recordJobView(nextIndex: number) {
    const viewed = Math.max(jobsViewed, nextIndex + 1);
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
    if (!unlocked && jobIndex + 1 >= freePreviewCount) {
      setStep("gate");
      trackRobotJobsFunnel("preview_complete", {
        ...funnelBase(),
        profile_key: profileKey,
        jobs_viewed: jobsViewed,
      });
      return;
    }
    if (unlocked && jobIndex + 1 >= jobs.length) {
      setJobIndex(0);
      setSelectedTapeKey(jobs[0]?.job_key ?? null);
      setQualifyOpen(false);
      setQualifyRequested(false);
      recordJobView(0);
      return;
    }
    const next = jobIndex + 1;
    if (next >= jobs.length) return;
    setJobIndex(next);
    setSelectedTapeKey(jobs[next]?.job_key ?? null);
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
            ? `/?src=${encodeURIComponent(srcRef.current)}`
            : "/";
    const signupParams = new URLSearchParams();
    signupParams.set("next", next);
    signupParams.set("src", "robot_jobs");
    if (personaRef.current) signupParams.set("persona", personaRef.current);
    return `/signup?${signupParams.toString()}`;
  })();

  // Auth unlock: skip gate; restore discovery if session returns without slug.
  useEffect(() => {
    if (!session) return;
    if (step === "gate" && profileKey) {
      setStep("enter");
      setBoardMode("personal");
      return;
    }
    if (slugConfig) return;
    if (boardMode === "personal" && profileKey) return;
    const saved = readJobsDiscoverySession();
    if (saved?.profileKey) {
      enterPersonalBoard(saved.profileKey, saved.robotName);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- unlock on session only
  }, [session]);

  return (
    <section className="flex min-h-0 flex-1 flex-col" aria-label="Find jobs for your robot">
      {step === "enter" && (
        <div className="grid h-[calc(100vh-76px)] min-h-[520px] grid-cols-1 overflow-hidden border border-slate-600 bg-[#0b162f] lg:grid-cols-[minmax(0,0.35fr)_minmax(0,0.65fr)]">
          {/* LEFT — FIND (still) */}
          <div className="flex flex-col border-b border-slate-600 p-5 sm:p-6 lg:border-b-0 lg:border-r lg:border-slate-600">
            <h1 className={`${titleClass} text-[2.15rem] leading-[1.05] sm:text-[2.4rem]`}>
              Find <span className="text-emerald-400">jobs</span>
              <br />
              for your robot.
            </h1>
            <p className="mt-3 text-[15px] leading-snug text-slate-300">
              {boardMode === "personal"
                ? `Work matched to ${robotName}.`
                : "Robots need jobs. We find the work."}
            </p>

            <label
              className="mt-7 block font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400"
              htmlFor="robot-url"
            >
              What robot needs a job?
            </label>
            <div className="mt-1.5 overflow-hidden border border-slate-500">
              <input
                id="robot-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") onContinueUrl();
                }}
                placeholder="Paste robot product URL"
                disabled={boardMode === "status"}
                className="w-full border-0 border-b border-slate-500 bg-[#081126] px-3 py-2 font-mono text-[13px] text-slate-100 outline-none placeholder:text-slate-600 focus:bg-[#0a152c] disabled:opacity-60"
              />
              <button
                type="button"
                onClick={onContinueUrl}
                disabled={!url.trim() || boardMode === "status"}
                className="flex w-full items-center justify-between gap-3 bg-emerald-400 px-3 py-2 text-left font-mono text-[13px] font-bold uppercase tracking-[0.12em] text-white transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:bg-emerald-400/40 disabled:text-white/70"
              >
                <span className="inline-flex items-center gap-2.5">
                  {faceOnCta}
                  Find Jobs
                </span>
                <PixelIcon map={KARE_ARROW} scale={2} fill={FACE_WHITE} background="transparent" />
              </button>
            </div>
            <FunnelTrace phase={tracePhase} jobCount={traceJobCount} />

            {boardMode === "personal" && job ? (
              <div className="mt-auto border-t border-slate-700 pt-4">
                <p className={eyebrowClass}>Selected job</p>
                <p className="mt-1 font-display text-sm font-bold uppercase text-slate-100">
                  {job.robot_compatible_task}
                </p>
                <p className={`mt-1 text-xs ${mutedClass}`}>
                  {job.company_name}
                  {job.locality ? ` · ${placeLine(job)}` : ""}
                </p>
                {!qualifyOpen ? (
                  <button
                    type="button"
                    onClick={onOpenQualify}
                    className={`${ctaClass} mt-3 w-full`}
                  >
                    Qualify This Job →
                  </button>
                ) : (
                  <div className="mt-3 border border-slate-600 p-3">
                    <p className="text-xs leading-relaxed text-slate-400">
                      We&apos;ll investigate whether this job deserves your sales team&apos;s time.
                    </p>
                    {qualifyRequested ? (
                      <p className="mt-2 text-xs font-bold text-emerald-400">Qualification requested</p>
                    ) : (
                      <button
                        type="button"
                        onClick={onRequestQualify}
                        className={`${ctaClass} mt-3 w-full text-xs`}
                      >
                        {faceOnCta}
                        Request Qualification
                      </button>
                    )}
                  </div>
                )}
                <button
                  type="button"
                  onClick={onNextJob}
                  className="mt-3 text-xs font-bold text-emerald-400 underline"
                >
                  {unlocked
                    ? jobIndex + 1 >= jobs.length
                      ? "Back to first job →"
                      : "Next job →"
                    : jobIndex + 1 >= freePreviewCount
                      ? "See all jobs →"
                      : "Next job →"}
                </button>
              </div>
            ) : boardMode === "status" ? (
              <div className="mt-auto border-t border-slate-700 pt-4">
                <div className="flex items-center gap-3">
                  <PixelIcon map={KARE_FACE} scale={2} fill={FACE_EMERALD} background="transparent" />
                  <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
                    Analyzing your robot
                  </p>
                </div>
                <ul className="mt-4 space-y-2 font-mono text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                  {statusLines.map((line) => (
                    <li
                      key={line}
                      className={
                        line.startsWith(">") || line.includes("✓")
                          ? "text-emerald-400"
                          : undefined
                      }
                    >
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="mt-auto space-y-3.5 border-t border-slate-700 pt-4">
                <div>
                  <p className={eyebrowClass}>How it works</p>
                  <ul className="mt-3 space-y-3">
                    {HOW_IT_WORKS.map((step) => (
                      <li key={step.n} className="flex items-start gap-3">
                        <span className="mt-0.5 flex w-6 shrink-0 justify-center">
                          <PixelIcon
                            map={step.icon}
                            scale={step.scale}
                            fill={FACE_EMERALD}
                            background="transparent"
                          />
                        </span>
                        <span className="min-w-0">
                          <span className="block font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-200">
                            <span className="text-emerald-400">{step.n}</span> {step.title}
                          </span>
                          <span className="mt-0.5 block text-[12px] leading-4 text-slate-500">
                            {step.body}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="border-t border-slate-700 pt-3">
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-200">
                    Found one worth pursuing?
                  </p>
                  <div className="mt-2 flex items-center gap-2.5">
                    <PixelIcon map={KARE_QUALIFY} scale={2} fill={FACE_EMERALD} background="transparent" />
                    <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-emerald-400">
                      Qualify the job
                    </p>
                  </div>
                  <p className="mt-1 text-[12px] leading-4 text-slate-500">
                    We&apos;ll research the commercial unknowns.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT — LIVE TAPE */}
          <div className="min-h-0 flex-1">
            <LiveJobTape
              title={tapeTitle}
              corpus={tapeCorpus}
              baseCount={tapeBase}
              running={tapeRunning && boardMode !== "status"}
              statusLines={tapeStatus}
              onSelect={onSelectTapeJob}
              selectedKey={selectedTapeKey}
            />
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
            href={src ? `/?src=${encodeURIComponent(src)}` : "/"}
            className="mt-6 inline-block text-sm font-bold underline"
            style={{ color: macAccent }}
          >
            Try another robot
          </Link>
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
            You&apos;ve seen {freePreviewCount} jobs matched to its capabilities. Create an account to unlock
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
              setSelectedTapeKey(jobs[0]?.job_key ?? null);
              setQualifyOpen(false);
              setQualifyRequested(false);
              setBoardMode("personal");
              setStep("enter");
              recordJobView(0);
            }}
            className="mt-4 text-sm font-bold underline"
            style={{ color: macAccent }}
          >
            Review jobs again
          </button>
          <Link
            href={src ? `/?src=${encodeURIComponent(src)}` : "/"}
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
