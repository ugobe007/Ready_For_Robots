/**
 * Robot → jobs conversion experiment.
 * Fixture-backed. No CRM / filters / dashboards.
 * Funnel: submit → capabilities → discover → jobs → see all → signup
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import { ArrowRight, Check, ChevronRight } from "lucide-react";
import demo from "@/data/rdd_demo_jobs.json";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
import { mapUrlToEnvelope } from "@/lib/robotJobsEnvelopeMap";

type Profile = (typeof demo.profiles)[number];
type Job = (typeof demo.jobs)[keyof typeof demo.jobs][number];
type Step = "enter" | "unsupported" | "capabilities" | "discovering" | "jobs" | "gate";

const PREVIEW_FREE = 5;
const DISCOVER_MS = 1800;

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

const PERSONAS = new Set(["oem", "distributor", "integrator"]);

/** Outreach tags: /experiment?persona=oem|distributor|integrator&src=… */
function attributionFromQuery(): { persona: string | null; src: string | null } {
  if (typeof window === "undefined") return { persona: null, src: null };
  const params = new URLSearchParams(window.location.search);
  const raw = (params.get("persona") || "").toLowerCase().trim();
  const persona = PERSONAS.has(raw) ? raw : null;
  const src = (params.get("src") || "").trim() || null;
  return { persona, src };
}

function initialFromQuery(): { profileKey: string; robotName: string } | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const key = params.get("robot");
  if (!key || !profileByKey(key)) return null;
  const p = profileByKey(key)!;
  return { profileKey: key, robotName: p.display_name };
}

export default function RobotJobsExperiment() {
  const [step, setStep] = useState<Step>("enter");
  const [url, setUrl] = useState("");
  const [profileKey, setProfileKey] = useState<string | null>(null);
  const [robotName, setRobotName] = useState("your robot");
  const [unsupportedReason, setUnsupportedReason] = useState<string | null>(null);
  const [jobIndex, setJobIndex] = useState(0);
  const [jobsViewed, setJobsViewed] = useState(0);
  const sessionId = useRef(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `rdd_${Date.now()}`,
  );
  const attribution = useRef(attributionFromQuery());
  const fired3Plus = useRef(false);
  const discoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const funnelBase = () => ({
    session_id: sessionId.current,
    ...(attribution.current.persona ? { persona: attribution.current.persona } : {}),
    ...(attribution.current.src ? { src: attribution.current.src } : {}),
  });

  useEffect(() => {
    trackRobotJobsFunnel("experiment_view", funnelBase());
    const boot = initialFromQuery();
    if (!boot) return;
    setProfileKey(boot.profileKey);
    setRobotName(boot.robotName);
    setJobIndex(0);
    setStep("capabilities");
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      profile_key: boot.profileKey,
      robot_name: boot.robotName,
      source: "query",
    });
    return () => {
      if (discoverTimer.current) clearTimeout(discoverTimer.current);
    };
  }, []);

  const profile = profileKey ? profileByKey(profileKey) : undefined;
  const jobs = useMemo(() => (profileKey ? jobsFor(profileKey) : []), [profileKey]);
  const job = jobs[jobIndex];
  const totalJobs = profile?.job_count_total ?? jobs.length;
  const previewCount = Math.min(PREVIEW_FREE, jobs.length);

  function beginWithMappedRobot(opts: {
    key: string;
    name: string;
    source: "url" | "demo" | "query";
    submittedUrl?: string;
  }) {
    setUnsupportedReason(null);
    setProfileKey(opts.key);
    setRobotName(opts.name);
    setJobIndex(0);
    setJobsViewed(0);
    fired3Plus.current = false;
    setStep("capabilities");
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

  function onPickDemo(key: string) {
    const p = profileByKey(key);
    if (!p) return;
    beginWithMappedRobot({ key, name: p.display_name, source: "demo" });
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
      source: "robot_jobs_experiment",
      profile_key: profileKey,
      robot_name: robotName,
      ...funnelBase(),
    });
  }

  const signupHref = (() => {
    const nextParams = new URLSearchParams();
    nextParams.set("robot", profileKey || "locus_origin");
    if (attribution.current.persona) nextParams.set("persona", attribution.current.persona);
    if (attribution.current.src) nextParams.set("src", attribution.current.src);
    const signupParams = new URLSearchParams();
    signupParams.set("next", `/experiment?${nextParams.toString()}`);
    signupParams.set("src", "robot_jobs");
    if (attribution.current.persona) signupParams.set("persona", attribution.current.persona);
    return `/signup?${signupParams.toString()}`;
  })();

  return (
    <section
      className="flex min-h-[520px] flex-col rounded-2xl border border-gray-200 bg-white px-5 py-6 sm:px-7 sm:py-8"
      aria-label="Find jobs for your robot"
    >
      {step === "enter" && (
        <div className="flex flex-1 flex-col">
          <h2 className="text-xl font-semibold tracking-tight text-gray-900 sm:text-2xl">
            Find jobs for your robot
          </h2>
          <p className="mt-2 max-w-md text-sm text-gray-500">
            Give us your robot. We&apos;ll find work it can do.
          </p>

          <label className="mt-8 block text-xs font-medium text-gray-600" htmlFor="robot-url">
            Robot product URL
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              id="robot-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") onContinueUrl();
              }}
              placeholder="https://robotcompany.com/product"
              className="min-w-0 flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-900 outline-none ring-emerald-600/30 placeholder:text-gray-400 focus:ring-2"
            />
            <button
              type="button"
              onClick={onContinueUrl}
              disabled={!url.trim()}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Continue
              <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <p className="mt-10 text-xs font-medium uppercase tracking-wide text-gray-400">
            Or try a known robot
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {demo.profiles.map((p) => (
              <button
                key={p.profile_key}
                type="button"
                onClick={() => onPickDemo(p.profile_key)}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-left text-sm text-gray-800 hover:border-emerald-300 hover:bg-emerald-50/60"
              >
                <span className="font-medium">{p.display_name}</span>
                <span className="mt-0.5 block text-xs text-gray-500">{p.manufacturer}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === "unsupported" && (
        <div className="flex flex-1 flex-col">
          <p className="text-sm text-gray-500">We analyzed {robotName}.</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-gray-900 sm:text-2xl">
            We don&apos;t have jobs for this robot yet
          </h2>
          <p className="mt-3 max-w-md text-sm text-gray-500">
            {unsupportedReason || "No matching job library for this robot yet"}. Right now we can show
            real jobs for warehouse AMRs and floor-scrubbing robots.
          </p>
          <p className="mt-8 text-xs font-medium uppercase tracking-wide text-gray-400">
            Try one we support
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {demo.profiles.map((p) => (
              <button
                key={p.profile_key}
                type="button"
                onClick={() => onPickDemo(p.profile_key)}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-left text-sm text-gray-800 hover:border-emerald-300 hover:bg-emerald-50/60"
              >
                <span className="font-medium">{p.display_name}</span>
                <span className="mt-0.5 block text-xs text-gray-500">{p.manufacturer}</span>
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              setStep("enter");
              setUnsupportedReason(null);
            }}
            className="mt-8 text-sm text-gray-500 underline-offset-2 hover:underline"
          >
            Try another URL
          </button>
        </div>
      )}

      {step === "capabilities" && profile && (
        <div className="flex flex-1 flex-col">
          <p className="text-sm text-gray-500">We analyzed {robotName}.</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-gray-900 sm:text-2xl">
            It appears capable of:
          </h2>
          <ul className="mt-5 space-y-2.5">
            {profile.can_actions.map((action) => (
              <li key={action} className="flex items-start gap-2.5 text-sm text-gray-800">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden />
                <span>{action}</span>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm text-gray-500">Looks right?</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onConfirmCapabilities}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-800"
            >
              Find jobs for {robotName}
              <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => {
                setStep("enter");
                setProfileKey(null);
              }}
              className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
            >
              Back
            </button>
          </div>
        </div>
      )}

      {step === "discovering" && (
        <div className="flex flex-1 flex-col items-center justify-center py-16 text-center" aria-live="polite">
          <div
            className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-700"
            aria-hidden
          />
          <p className="mt-6 text-lg font-medium text-gray-900">
            Searching for work {robotName} can do…
          </p>
          <p className="mt-2 max-w-sm text-sm text-gray-500">
            Matching its capabilities to localized jobs in the open economy.
          </p>
        </div>
      )}

      {step === "jobs" && profile && job && (
        <div className="flex flex-1 flex-col">
          <p className="text-sm text-gray-500">
            We found{" "}
            <span className="font-semibold text-gray-900">{totalJobs}</span> jobs matching{" "}
            {robotName}&apos;s capabilities.
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Job {jobIndex + 1} of {previewCount}
          </p>

          <article className="mt-6 flex-1">
            <h2 className="text-lg font-semibold tracking-tight text-gray-900 sm:text-xl">
              {job.robot_compatible_task}
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              {job.company_name}
              {job.locality ? ` · ${job.locality}` : ""}
            </p>

            <dl className="mt-6 space-y-4 text-sm">
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                  Why we believe it exists
                </dt>
                <dd className="mt-1 text-gray-800">{job.why_job}</dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                  Why {robotName} could do it
                </dt>
                <dd className="mt-1 text-gray-800">
                  {whyYourRobot(job, profile.capability_family)}
                </dd>
              </div>
              {job.unknowns?.length ? (
                <div>
                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                    What we don&apos;t know
                  </dt>
                  <dd className="mt-1 text-gray-800">{job.unknowns.join(" · ")}</dd>
                </div>
              ) : null}
              <div>
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                  Worth investigating
                </dt>
                <dd className="mt-1 font-semibold tracking-wide text-emerald-800">
                  {worthLabel(job)}
                </dd>
              </div>
            </dl>
          </article>

          <button
            type="button"
            onClick={onNextJob}
            className="mt-8 inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-700 px-4 py-3 text-sm font-medium text-white hover:bg-emerald-800 sm:w-auto"
          >
            {jobIndex + 1 >= previewCount ? "Continue" : "See next job"}
            <ChevronRight className="h-4 w-4" aria-hidden />
          </button>
        </div>
      )}

      {step === "gate" && profile && (
        <div className="flex flex-1 flex-col items-start justify-center">
          <h2 className="text-xl font-semibold tracking-tight text-gray-900 sm:text-2xl">
            See all {totalJobs} jobs for {robotName}
          </h2>
          <p className="mt-3 max-w-md text-sm text-gray-500">
            You&apos;ve seen {previewCount} jobs matched to its capabilities. Create an account to unlock
            the rest.
          </p>
          <Link
            href={signupHref}
            onClick={onSeeAll}
            className="mt-6 inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-medium text-white hover:bg-emerald-800"
          >
            See all {totalJobs} jobs
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <button
            type="button"
            onClick={() => {
              setJobIndex(0);
              setStep("jobs");
              recordJobView(0);
            }}
            className="mt-4 text-sm text-gray-500 underline-offset-2 hover:underline"
          >
            Review jobs again
          </button>
          <button
            type="button"
            onClick={() => {
              setStep("enter");
              setProfileKey(null);
              setJobIndex(0);
              setUrl("");
            }}
            className="mt-8 text-xs text-gray-400 hover:text-gray-600"
          >
            Try another robot
          </button>
        </div>
      )}
    </section>
  );
}
