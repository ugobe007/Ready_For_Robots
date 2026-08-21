/**
 * RobotJobsWorkspace — the ReadyForRobots work terminal (front door `/`).
 *
 * Left = robot / context / navigation. Right = work. One deliberate state at
 * a time (submit-stability principle):
 *
 *   FIND → RESEARCH → SELECT → PORTFOLIO (several SKUs; research one at a time)
 *                      SELECT → REVIEW PROFILE → JOBS → activate list (one robot)

 *
 * Three separated objects:
 *   ROBOT  — what did we understand?      (REVIEW PROFILE, pre-match)
 *   MATCH  — what work looks compatible?  (JOBS, produced only when asked)
 *   JOB    — inspect this one             (why / unknowns / blockers)
 *
 * Product-integrity contract (every displayed number must be true):
 *   - The profile screen is a pre-match checkpoint: no job count until the
 *     robot has actually been matched.
 *   - SELECT supports one robot, several, or all. A portfolio only shows a
 *     per-robot count when counts are genuinely differentiated; otherwise it
 *     shows the capability summary + "View matches →" (no suspicious number).
 *
 * Matcher / Understanding are frozen (M2) — this only presents their output.
 */
import { useEffect, useRef, useState } from "react";
import { useLocation } from "wouter";
import { trackRobotJobsFunnel } from "@/lib/siteAnalytics";
import {
  fetchRobotJobSearch,
  type RobotJobSearchResult,
} from "@/lib/robotJobSearch";
import { fetchRobotProfile } from "@/lib/robotProfile";
import { fetchRobotJobMatch } from "@/lib/robotJobMatch";
import {
  formatFactLine,
  profileConfidenceCopy,
  sourceTypeLabel,
  type RobotProfileResult,
} from "@/lib/robotProfile";
import type { ClassOption, MatchCapability, MatchJob } from "@/lib/robotJobMatch";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import { MARKET_TAPE_JOBS } from "@/lib/jobsTapeCorpus";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  JOBS_EXAMPLE_CAP,
  FIND_JOBS_CTA,
  JOBS_NEXT_CTA,
  JOBS_NEXT_HINT,
  JOBS_PIPELINE_CAP,
  JOBS_ACTIVATE_CAP,
  JOBS_RESTORE_ONCE_KEY,
  RAIL_STEP_HINT,
  capExampleJobs,
  consumeJobsWorkspaceRestoreOnce,
  defaultCheckedJobKeys,
  isJobsFreshQuery,
  jobsActivateHref,
  jobsForActivatedPipeline,
  jobsHeading,
  readNavigationType,
  shouldRestoreJobsWorkspace,
} from "@/lib/jobsWorkflow";
import { saveJobsHandoffSnapshot } from "@/lib/jobsHandoffSnapshot";

/* ------------------------------------------------------------------ */
/* Types + constants                                                   */
/* ------------------------------------------------------------------ */

type Stage = "find" | "research" | "select" | "portfolio" | "review" | "jobs";
type RailTab = "profile" | "jobs";

/** One robot in the workspace. `matched` gates every count we display. */
type RobotAnalysis = {
  productName: string;
  companyName: string;
  tier: "A" | "B" | "C";
  profile: RobotProfileResult | null;
  matched: boolean;
  capabilities: MatchCapability[];
  jobs: MatchJob[];
  jobCount: number;
  zeroReason?: string | null;
  needsClassChoice?: boolean;
  classOptions?: ClassOption[];
  previewImageUrl?: string | null;
};

type ZeroReason =
  | "insufficient_profile_evidence"
  | "no_compatible_jobs"
  | "corpus_gap";

type ProductChoice = { name: string; displayClass?: string | null };
type RestoreView = "review" | "jobs" | "portfolio";

const MARKET_FOUND_BASE = 140;
const WORKSPACE_SESSION_KEY = "rfr_jobs_workspace";

const DEFAULT_CLASS_OPTIONS: ClassOption[] = [
  {
    id: "humanoid",
    label: "Humanoid",
    hint: "Two legs, arms and hands — NEO, Unitree G1, Walker",
  },
  {
    id: "amr",
    label: "AMR / mobile robot",
    hint: "Rolls on a base and moves materials or itself",
  },
  {
    id: "mobile_manipulator",
    label: "Mobile manipulator",
    hint: "Rolling base with an arm that picks or places",
  },
  {
    id: "cobot",
    label: "Collaborative arm",
    hint: "Stationary or cart-mounted arm beside a person",
  },
  {
    id: "quadruped",
    label: "Quadruped",
    hint: "Four legs — inspection, patrol, unstructured ground",
  },
  {
    id: "autonomous_scrubber",
    label: "Floor scrubber",
    hint: "Cleans floors on its own",
  },
];

const eyebrow =
  "font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500";
const ctaClass =
  "inline-flex items-center justify-center gap-2 bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-45";

function FaceCue({
  scale = 2,
  onEmerald = false,
  className = "",
}: {
  scale?: number;
  onEmerald?: boolean;
  className?: string;
}) {
  return (
    <PixelIcon
      map={KARE_FACE}
      scale={scale}
      fill={onEmerald ? "#04122a" : FACE_EMERALD}
      background="transparent"
      className={`shrink-0 ${className}`.trim()}
    />
  );
}

/* ------------------------------------------------------------------ */
/* Session persistence (signup continuity)                             */
/* ------------------------------------------------------------------ */

type WorkspaceSession = {
  url: string;
  products: string[];
  view: RestoreView;
  activeIdx?: number;
  selectedJobKey?: string;
  checkedJobKeys?: string[];
};

function saveWorkspaceSession(data: WorkspaceSession) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(WORKSPACE_SESSION_KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

function readWorkspaceSession(): WorkspaceSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(WORKSPACE_SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as {
      url?: string;
      products?: string[];
      view?: string;
      activeIdx?: number;
      selectedJobKey?: string;
      checkedJobKeys?: unknown;
    };
    if (!parsed?.url) return null;
    const view: RestoreView =
      parsed.view === "place" || parsed.view === "qualify"
        ? "jobs"
        : parsed.view === "portfolio"
          ? "portfolio"
          : parsed.view === "review"
            ? "review"
            : "jobs";
    const checkedJobKeys = Array.isArray(parsed.checkedJobKeys)
      ? parsed.checkedJobKeys.filter((k): k is string => typeof k === "string")
      : [];
    return {
      url: parsed.url,
      products: Array.isArray(parsed.products) ? parsed.products : [],
      view,
      activeIdx: parsed.activeIdx,
      selectedJobKey: parsed.selectedJobKey,
      checkedJobKeys,
    };
  } catch {
    return null;
  }
}

function clearWorkspaceSession() {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(WORKSPACE_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

function srcFromQuery(): string | null {
  if (typeof window === "undefined") return null;
  return (
    (new URLSearchParams(window.location.search).get("src") || "").trim() ||
    null
  );
}

/* ------------------------------------------------------------------ */
/* Pure helpers                                                        */
/* ------------------------------------------------------------------ */

/** Identity-only row — matching has not happened yet. */
function identityAnalysis(productName: string, companyName: string): RobotAnalysis {
  return {
    productName,
    companyName,
    tier: "C",
    profile: null,
    matched: false,
    capabilities: [],
    jobs: [],
    jobCount: 0,
  };
}
function profileToAnalysis(profile: RobotProfileResult): RobotAnalysis {
  return {
    productName:
      profile.selected_product?.name || profile.company?.name || "Your robot",
    companyName: profile.company?.name || "",
    tier: (profile.profile_confidence as "A" | "B" | "C") || "C",
    profile,
    matched: false,
    capabilities: [],
    jobs: [],
    jobCount: 0,
  };
}

/** Full analysis from a matched robot-job-search transaction. */
function searchToAnalysis(res: RobotJobSearchResult): RobotAnalysis {
  const profile = (res.profile as RobotProfileResult | null) ?? null;
  return {
    productName:
      profile?.selected_product?.name ||
      res.robot_name ||
      res.company_name ||
      "Your robot",
    companyName:
      profile?.company?.name || res.company_name || res.robot_name || "",
    tier: (profile?.profile_confidence as "A" | "B" | "C") || "C",
    profile,
    matched: true,
    capabilities: res.capabilities || [],
    jobs: res.jobs || [],
    jobCount: res.job_count || (res.jobs || []).length,
    zeroReason: res.zero_reason ?? null,
    needsClassChoice: Boolean(res.needs_class_choice),
    classOptions: res.class_options || [],
    previewImageUrl: res.preview_image_url ?? null,
  };
}

/** Weak identity: low-confidence profile whose company name may be tagline-derived. */
function weakIdentity(profile: RobotProfileResult | null): boolean {
  return Boolean(
    profile &&
      profile.profile_confidence === "C" &&
      profile.coverage_level === "low"
  );
}

/** Honest company line: prefer the verified name; fall back to the domain when weak. */
function companyIdentity(a: RobotAnalysis): {
  label: string;
  verified: boolean;
} {
  const domain = a.profile?.company?.primary_domain || "";
  if (weakIdentity(a.profile) && domain)
    return { label: domain, verified: false };
  return { label: a.companyName || domain || "", verified: true };
}

function confirmedFacts(profile: RobotProfileResult | null) {
  if (!profile) return [];
  const confirmed = profile.facts.filter(
    f => f.epistemic === "explicit" || f.epistemic === "strongly_inferred"
  );
  const byPred = new Map<string, (typeof confirmed)[number]>();
  for (const f of confirmed) {
    const prev = byPred.get(f.predicate);
    if (!prev || f.confidence > prev.confidence) byPred.set(f.predicate, f);
  }
  return [...byPred.values()]
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 10);
}

function unknownFacts(profile: RobotProfileResult | null) {
  if (!profile) return [];
  return profile.facts.filter(f => f.epistemic === "unknown").slice(0, 8);
}

function conflictFacts(profile: RobotProfileResult | null) {
  if (!profile) return [];
  return profile.facts.filter(f => f.epistemic === "contradicted").slice(0, 4);
}

function capabilitySummary(a: RobotAnalysis): string {
  if (!a.matched) return "Not researched yet — open this SKU for its own jobs.";
  const labels = a.capabilities.filter(c => c.label).map(c => c.label);
  if (labels.length) return labels.slice(0, 3).join(" · ");
  const fams = [
    ...new Set(a.jobs.map(j => j.tape_family).filter(Boolean)),
  ] as string[];
  return (
    fams.slice(0, 3).join(" · ") || "Work matched to confirmed capabilities"
  );
}

function tierColor(tier: "A" | "B" | "C"): string {
  if (tier === "A") return "text-emerald-400";
  if (tier === "B") return "text-amber-300";
  return "text-slate-400";
}

/**
 * Whether a robot's job count is trustworthy enough to display.
 * A single robot's own matched count is fine. Across a portfolio we only
 * assert a count when the robots actually differ — never three identical
 * numbers that would undermine the promise.
 */
function differentiatedCounts(portfolio: RobotAnalysis[]): boolean {
  const matched = portfolio.filter(a => a.matched);
  if (matched.length <= 1) return true;
  return new Set(matched.map(a => a.jobCount)).size > 1;
}

function pickSelectedJobKey(
  jobs: MatchJob[],
  preferred?: string | null,
): string | null {
  if (preferred && jobs.some(j => j.job_key === preferred)) return preferred;
  return jobs[0]?.job_key ?? null;
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function RobotJobsWorkspace() {
  const [location, setLocation] = useLocation();
  const [stage, setStage] = useState<Stage>(() => {
    if (typeof window === "undefined") return "find";
    if (isJobsFreshQuery(window.location.search)) return "find";
    const saved = readWorkspaceSession();
    if (!saved?.url) return "find";
    let restoreOnce = false;
    try {
      restoreOnce = window.sessionStorage.getItem(JOBS_RESTORE_ONCE_KEY) === "1";
    } catch {
      restoreOnce = false;
    }
    const restoreQuery = new URLSearchParams(window.location.search).get("restore") === "1";
    return shouldRestoreJobsWorkspace({
      navigationType: readNavigationType(),
      restoreOnce,
      restoreQuery,
    })
      ? "research"
      : "find";
  });
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  // SELECT
  const [companyName, setCompanyName] = useState("");
  const [products, setProducts] = useState<ProductChoice[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  // Results
  const [portfolio, setPortfolio] = useState<RobotAnalysis[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [railTab, setRailTab] = useState<RailTab>("jobs");
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [checkedJobKeys, setCheckedJobKeys] = useState<string[]>([]);
  const [showAllJobs, setShowAllJobs] = useState(false);

  const sessionId = useRef(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `rdd_${Date.now()}`
  );
  const srcRef = useRef(srcFromQuery());
  const submittedUrlRef = useRef("");
  const submissionIdRef = useRef<number | null>(null);
  const viewedRef = useRef<Set<string>>(new Set());
  const fired3Plus = useRef(false);
  const restoredRef = useRef(false);
  const matchAbortRef = useRef<(() => void) | null>(null);

  const funnelBase = () => ({
    session_id: sessionId.current,
    ...(srcRef.current ? { src: srcRef.current } : {}),
    // Durable submitter id → submitter → funnel outcome is a single join.
    ...(submissionIdRef.current
      ? { robot_submission_id: submissionIdRef.current }
      : {}),
  });

  const active = portfolio[activeIdx] || null;
  const countsTrusted = differentiatedCounts(portfolio);
  const showActiveCount = Boolean(
    active?.matched &&
      active.jobCount > 0 &&
      (portfolio.length === 1 || countsTrusted)
  );

  useEffect(() => {
    trackRobotJobsFunnel("experiment_view", {
      ...funnelBase(),
      surface: "workspace",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function resetToFind(replaceHome = false) {
    if (matchAbortRef.current) {
      matchAbortRef.current();
      matchAbortRef.current = null;
    }
    setStage("find");
    setUrl("");
    setError(null);
    setMatchError(null);
    setMatching(false);
    setPortfolio([]);
    setProducts([]);
    setSelected([]);
    setCompanyName("");
    setActiveIdx(0);
    setExpandedJob(null);
    setCheckedJobKeys([]);
    setShowAllJobs(false);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    restoredRef.current = true;
    submittedUrlRef.current = "";
    submissionIdRef.current = null;
    clearWorkspaceSession();
    if (replaceHome && isJobsFreshQuery(window.location.search)) {
      setLocation("/", { replace: true });
    }
  }

  /* Wordmark / Jobs nav: `/?new=1` must dump in-progress work and show FIND. */
  useEffect(() => {
    if (!isJobsFreshQuery(typeof window === "undefined" ? location : window.location.search)) {
      return;
    }
    resetToFind(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location]);

  /* Restore only on refresh, back/forward, or an auth one-shot.
     A normal revisit of `/` must show FIND — not replay the last robot URL. */
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    if (isJobsFreshQuery(window.location.search)) {
      resetToFind(true);
      return;
    }
    const saved = readWorkspaceSession();
    const restoreOnce = consumeJobsWorkspaceRestoreOnce();
    const restoreQuery =
      new URLSearchParams(window.location.search).get("restore") === "1";
    const allowRestore = shouldRestoreJobsWorkspace({
      navigationType: readNavigationType(),
      restoreOnce,
      restoreQuery,
    });
    if (allowRestore && saved?.url) {
      if (restoreQuery) {
        window.history.replaceState({}, "", "/");
      }
      void restore(saved);
    } else {
      clearWorkspaceSession();
      setUrl("");
      setStage("find");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* -------------------------------------------------------------- */
  /* Data flow                                                       */
  /* -------------------------------------------------------------- */

  /** FIND submit — research identity first (no jobs yet). */
  async function submitFind(submitUrl: string) {
    setError(null);
    submittedUrlRef.current = submitUrl;
    setStage("research");
    trackRobotJobsFunnel("robot_submitted", {
      ...funnelBase(),
      url: submitUrl,
      source: "url",
    });
    trackRobotJobsFunnel("discovery_started", {
      ...funnelBase(),
      url: submitUrl,
    });
    try {
      const profile = await fetchRobotProfile({ url: submitUrl });
      submissionIdRef.current = profile.robot_submission_id ?? submissionIdRef.current;
      setCompanyName(profile.company?.name || "");
      if (profile.needs_product_choice && (profile.products || []).length > 1) {
        setProducts(
          (profile.products || []).map(p => ({
            name: p.name,
            displayClass: p.display_class,
          }))
        );
        setSelected([]);
        setStage("select");
        return;
      }
      enterReview(profileToAnalysis(profile), submitUrl, [
        profile.selected_product?.name || "",
      ]);
    } catch (err) {
      const detail = err instanceof Error ? err.message.trim() : "";
      setError(
        detail && !/^robot-profile\s+\d+$/i.test(detail)
          ? `Research failed. ${detail}`
          : "Research failed. Check the URL and try again.",
      );
      setStage("find");
    }
  }

  /** SELECT — one robot goes to a profile checkpoint; several/all matches up front. */
  async function confirmSelection(which: string[] | "all") {
    const names = (which === "all" ? products.map(p => p.name) : which).filter(
      Boolean
    );
    if (names.length === 0) return;
    const submitUrl = submittedUrlRef.current || url;

    if (names.length === 1) {
      setStage("research");
      try {
        const profile = await fetchRobotProfile({
          url: submitUrl,
          product: names[0],
        });
        submissionIdRef.current = profile.robot_submission_id ?? submissionIdRef.current;
        enterReview(profileToAnalysis(profile), submitUrl, names);
      } catch {
        setError("Research failed for that robot.");
        setStage("select");
      }
      return;
    }

    // Several / all — a portfolio of distinct SKUs. Do NOT research the first
    // robot and stamp those jobs onto every name (any multi-product OEM).
    const analyses = names.map(name => identityAnalysis(name, companyName));
    setPortfolio(analyses);
    setActiveIdx(0);
    setRailTab("profile");
    saveWorkspaceSession({
      url: submitUrl,
      products: names,
      view: "portfolio",
      activeIdx: 0,
    });
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      robots_analyzed: analyses.length,
      company_name: companyName,
    });
    setStage("portfolio");
  }

  /** Enter the profile checkpoint (matching deferred).
   *
   * `track` defaults to true (a genuine new research view). Restoring the same
   * state on reload / auth-return passes `track: false` so a page reload never
   * re-fires `capabilities_viewed` and inflates the funnel — the same
   * once-per-journey discipline the signup funnel events use. */
  function enterReview(
    analysis: RobotAnalysis,
    submitUrl: string,
    productNames: string[],
    opts: { track?: boolean } = {}
  ) {
    const { track = true } = opts;
    const keepPortfolio = productNames.filter(Boolean).length > 1;
    if (keepPortfolio) {
      const idx = activeIdx;
      setPortfolio(prev => {
        if (prev.length === productNames.length) {
          return prev.map((p, i) => (i === idx ? analysis : p));
        }
        return productNames.map((name, i) =>
          i === idx ? analysis : identityAnalysis(name, analysis.companyName),
        );
      });
    } else {
      setPortfolio([analysis]);
      setActiveIdx(0);
    }
    setRailTab("profile");
    setExpandedJob(null);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    saveWorkspaceSession({
      url: submitUrl,
      products: productNames.filter(Boolean),
      view: "review",
      activeIdx: keepPortfolio ? activeIdx : 0,
    });
    if (track) {
      trackRobotJobsFunnel("capabilities_viewed", {
        ...funnelBase(),
        robot_name: analysis.productName,
        company_name: analysis.companyName,
        profile_tier: analysis.tier,
      });
    }
    setStage("review");
  }

  /** Enter review for an already-matched robot (e.g. portfolio of one). */
  function enterReviewMatched(analysis: RobotAnalysis, submitUrl: string) {
    setPortfolio([analysis]);
    setActiveIdx(0);
    setRailTab("profile");
    saveWorkspaceSession({
      url: submitUrl,
      products: [analysis.productName],
      view: "review",
      activeIdx: 0,
    });
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      robot_name: analysis.productName,
      profile_tier: analysis.tier,
    });
    setStage("review");
  }

  /** REVIEW → run matching for the active robot, then reveal jobs. */
  async function findJobsForActive() {
    const a = portfolio[activeIdx];
    if (!a) return;
    if (a.matched) {
      goToJobs(activeIdx);
      return;
    }
    setMatching(true);
    setMatchError(null);
    let aborted = false;
    matchAbortRef.current = () => {
      aborted = true;
    };
    try {
      const res = await fetchRobotJobMatch({
        url: submittedUrlRef.current,
        productName: a.productName,
        profile: a.profile,
      });
      if (aborted) return;
      const merged: RobotAnalysis = {
        ...a,
        matched: true,
        capabilities: res.capabilities || [],
        jobs: res.jobs || [],
        jobCount: res.job_count || (res.jobs || []).length,
        zeroReason: res.zero_reason ?? null,
        needsClassChoice: Boolean(res.needs_class_choice),
        classOptions: res.class_options || [],
        previewImageUrl: res.preview_image_url ?? a.previewImageUrl ?? null,
      };
      setPortfolio(prev => prev.map((p, i) => (i === activeIdx ? merged : p)));
      saveWorkspaceSession({
        url: submittedUrlRef.current,
        products:
          portfolio.length > 1
            ? portfolio.map(p => p.productName)
            : [a.productName],
        view: "jobs",
        activeIdx,
      });
      revealJobs(merged);
    } catch {
      if (!aborted) {
        setMatchError("Matching failed. Try again.");
      }
    } finally {
      matchAbortRef.current = null;
      if (!aborted) {
        setMatching(false);
      }
    }
  }

  /** Operator names the morphology so Jobs can rematch from that class. */
  async function qualifyActive(classId: string) {
    const a = portfolio[activeIdx];
    if (!a) return;
    setMatching(true);
    setMatchError(null);
    try {
      const url = submittedUrlRef.current;
      let merged: RobotAnalysis;
      if (a.profile) {
        const res = await fetchRobotJobMatch({
          url,
          productName: a.productName,
          profile: a.profile,
          assertedClass: classId,
        });
        merged = {
          ...a,
          matched: true,
          capabilities: res.capabilities || [],
          jobs: res.jobs || [],
          jobCount: res.job_count || (res.jobs || []).length,
          zeroReason: res.zero_reason ?? null,
          needsClassChoice: Boolean(res.needs_class_choice),
          classOptions: res.class_options || [],
          previewImageUrl: res.preview_image_url ?? a.previewImageUrl ?? null,
        };
      } else {
        const res = await fetchRobotJobSearch({
          url,
          product: a.productName,
          assertedClass: classId,
        });
        merged = { ...searchToAnalysis(res), productName: a.productName };
      }
      setPortfolio(prev => prev.map((p, i) => (i === activeIdx ? merged : p)));
      revealJobs(merged);
    } catch {
      setMatchError("Could not apply that robot class. Try again.");
    } finally {
      setMatching(false);
    }
  }

  function revealJobs(a: RobotAnalysis) {
    const checks = defaultCheckedJobKeys(a.jobs);
    setRailTab("jobs");
    setExpandedJob(pickSelectedJobKey(a.jobs, expandedJob));
    setCheckedJobKeys(checks);
    setStage("jobs");
    saveWorkspaceSession({
      url: submittedUrlRef.current,
      products:
        portfolio.length > 1
          ? portfolio.map(p => p.productName)
          : [a.productName],
      view: "jobs",
      activeIdx,
      selectedJobKey: pickSelectedJobKey(a.jobs, expandedJob) || undefined,
      checkedJobKeys: checks,
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a.productName,
      job_count: a.jobCount,
    });
  }

  function goToJobs(idx: number) {
    setActiveIdx(idx);
    const a = portfolio[idx];
    const selectedKey = pickSelectedJobKey(a?.jobs || [], expandedJob);
    const checks =
      checkedJobKeys.length > 0
        ? checkedJobKeys.filter(k => (a?.jobs || []).some(j => j.job_key === k))
        : defaultCheckedJobKeys(a?.jobs || []);
    const nextChecks = checks.length ? checks : defaultCheckedJobKeys(a?.jobs || []);
    setRailTab("jobs");
    setExpandedJob(selectedKey);
    setCheckedJobKeys(nextChecks);
    setStage("jobs");
    saveWorkspaceSession({
      url: submittedUrlRef.current,
      products: portfolio.map(p => p.productName),
      view: "jobs",
      activeIdx: idx,
      selectedJobKey: selectedKey || undefined,
      checkedJobKeys: nextChecks,
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a?.productName,
      job_count: a?.jobCount,
    });
  }

  function goToActivate() {
    const pool = active?.jobs || [];
    const selected = pool.filter(job => checkedJobKeys.includes(job.job_key));
    if (selected.length === 0) return;
    const jobs = jobsForActivatedPipeline(selected, pool, JOBS_ACTIVATE_CAP);
    saveJobsHandoffSnapshot({
      url: submittedUrlRef.current,
      productName: active?.productName || "",
      jobs,
      selectedCount: selected.length,
    });
    trackRobotJobsFunnel("jobs_list_activated", {
      ...funnelBase(),
      robot_name: active?.productName,
      selected_count: selected.length,
      list_count: jobs.length,
    });
    window.location.href = jobsActivateHref(submissionIdRef.current);
  }

  function applyCheckedKeys(jobs: MatchJob[], saved?: string[]) {
    const fromSaved = (saved || []).filter(k => jobs.some(j => j.job_key === k));
    const next = fromSaved.length ? fromSaved : defaultCheckedJobKeys(jobs);
    setCheckedJobKeys(next);
    return next;
  }

  async function researchPortfolioRobot(idx: number, dest: "review" | "jobs") {
    const a = portfolio[idx];
    if (!a) return;
    const submitUrl = submittedUrlRef.current;
    const names = portfolio.map(p => p.productName);
    setActiveIdx(idx);
    if (dest === "jobs" && a.matched && (a.jobs || []).length > 0) {
      goToJobs(idx);
      return;
    }
    if (dest === "review" && a.profile && !a.matched) {
      setRailTab("profile");
      setStage("review");
      return;
    }
    setStage("research");
    setError(null);
    try {
      if (dest === "jobs") {
        const search = await fetchRobotJobSearch({
          url: submitUrl,
          product: a.productName,
        });
        submissionIdRef.current =
          search.robot_submission_id ?? submissionIdRef.current;
        const merged = {
          ...searchToAnalysis(search),
          productName: a.productName,
        };
        setPortfolio(prev => prev.map((p, i) => (i === idx ? merged : p)));
        setCompanyName(merged.companyName);
        setRailTab("jobs");
        setExpandedJob(pickSelectedJobKey(merged.jobs, null));
        setCheckedJobKeys(defaultCheckedJobKeys(merged.jobs));
        saveWorkspaceSession({
          url: submitUrl,
          products: names,
          view: "jobs",
          activeIdx: idx,
          selectedJobKey: merged.jobs[0]?.job_key,
          checkedJobKeys: defaultCheckedJobKeys(merged.jobs),
        });
        trackRobotJobsFunnel("discovery_complete", {
          ...funnelBase(),
          robot_name: merged.productName,
          job_count: merged.jobCount,
        });
        setStage("jobs");
        return;
      }
      const profile = await fetchRobotProfile({
        url: submitUrl,
        product: a.productName,
      });
      submissionIdRef.current =
        profile.robot_submission_id ?? submissionIdRef.current;
      const merged = profileToAnalysis(profile);
      setPortfolio(prev =>
        prev.map((p, i) =>
          i === idx ? merged : { ...p, companyName: merged.companyName || p.companyName },
        ),
      );
      setCompanyName(merged.companyName);
      setRailTab("profile");
      saveWorkspaceSession({
        url: submitUrl,
        products: names,
        view: "review",
        activeIdx: idx,
      });
      setStage("review");
    } catch {
      setError("Research failed for that robot.");
      setStage("portfolio");
    }
  }

  async function restore(saved: WorkspaceSession) {
    submittedUrlRef.current = saved.url;
    const savedIdx = typeof saved.activeIdx === "number" ? saved.activeIdx : 0;
    try {
      if (saved.products.length > 1) {
        const idx =
          savedIdx >= 0 && savedIdx < saved.products.length ? savedIdx : 0;
        const stubs = saved.products.map(name => identityAnalysis(name, ""));
        if (saved.view === "portfolio") {
          setPortfolio(stubs);
          setActiveIdx(idx);
          setStage("portfolio");
          return;
        }
        const product = saved.products[idx];
        if (saved.view === "jobs") {
          const res = await fetchRobotJobSearch({ url: saved.url, product });
          submissionIdRef.current =
            res.robot_submission_id ?? submissionIdRef.current;
          const a = { ...searchToAnalysis(res), productName: product };
          const analyses = stubs.map((row, i) =>
            i === idx ? a : { ...row, companyName: a.companyName },
          );
          setPortfolio(analyses);
          setCompanyName(a.companyName);
          setActiveIdx(idx);
          setExpandedJob(pickSelectedJobKey(a.jobs, saved.selectedJobKey));
          applyCheckedKeys(a.jobs, saved.checkedJobKeys);
          setRailTab("jobs");
          setStage("jobs");
          return;
        }
        const profile = await fetchRobotProfile({ url: saved.url, product });
        submissionIdRef.current =
          profile.robot_submission_id ?? submissionIdRef.current;
        const a = profileToAnalysis(profile);
        const analyses = stubs.map((row, i) =>
          i === idx ? a : { ...row, companyName: a.companyName },
        );
        setPortfolio(analyses);
        setCompanyName(a.companyName);
        setActiveIdx(idx);
        setRailTab("profile");
        setStage("review");
        return;
      }
      const product = saved.products[0] || undefined;
      if (saved.view === "jobs") {
        const res = await fetchRobotJobSearch({ url: saved.url, product });
        submissionIdRef.current = res.robot_submission_id ?? submissionIdRef.current;
        const a = searchToAnalysis(res);
        setPortfolio([a]);
        setActiveIdx(0);
        setExpandedJob(pickSelectedJobKey(a.jobs, saved.selectedJobKey));
        applyCheckedKeys(a.jobs, saved.checkedJobKeys);
        setRailTab("jobs");
        setStage("jobs");
        return;
      }
      const profile = await fetchRobotProfile({ url: saved.url, product });
      submissionIdRef.current = profile.robot_submission_id ?? submissionIdRef.current;
      // Silent: restoring on reload / auth-return must not re-fire the funnel.
      enterReview(profileToAnalysis(profile), saved.url, saved.products, {
        track: false,
      });
    } catch {
      setStage("find");
    }
  }

  /* -------------------------------------------------------------- */
  /* Handlers                                                        */
  /* -------------------------------------------------------------- */

  function onSubmitFind(e: React.FormEvent) {
    e.preventDefault();
    const u = url.trim();
    if (!u) return;
    void submitFind(u);
  }

  function toggleProduct(name: string) {
    setSelected(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]
    );
  }

  function recordJobView(job: MatchJob) {
    if (viewedRef.current.has(job.job_key)) return;
    viewedRef.current.add(job.job_key);
    trackRobotJobsFunnel("job_viewed", {
      ...funnelBase(),
      job_key: job.job_key,
      company_name: job.company_name,
      robot_name: active?.productName,
    });
    if (!fired3Plus.current && viewedRef.current.size >= 3) {
      fired3Plus.current = true;
      trackRobotJobsFunnel("jobs_3plus_viewed", {
        ...funnelBase(),
        robot_name: active?.productName,
      });
    }
  }

  function selectJob(job: MatchJob) {
    setExpandedJob(job.job_key);
    recordJobView(job);
    saveWorkspaceSession({
      url: submittedUrlRef.current,
      products: portfolio.map(p => p.productName),
      view: "jobs",
      activeIdx,
      selectedJobKey: job.job_key,
      checkedJobKeys,
    });
  }

  function toggleCheckedJob(job: MatchJob) {
    setCheckedJobKeys(prev => {
      const next = prev.includes(job.job_key)
        ? prev.filter(k => k !== job.job_key)
        : [...prev, job.job_key];
      saveWorkspaceSession({
        url: submittedUrlRef.current,
        products: portfolio.map(p => p.productName),
        view: "jobs",
        activeIdx,
        selectedJobKey: expandedJob || job.job_key,
        checkedJobKeys: next,
      });
      return next;
    });
  }

  function seeAllJobs() {
    setShowAllJobs(true);
    trackRobotJobsFunnel("see_all_clicked", {
      ...funnelBase(),
      robot_name: active?.productName,
      job_count: active?.jobCount,
    });
  }

  function newRobot() {
    resetToFind(false);
  }

  /* -------------------------------------------------------------- */
  /* Render                                                          */
  /* -------------------------------------------------------------- */

  return (
    <div className="grid h-[calc(100vh-76px)] min-h-[560px] grid-cols-1 overflow-hidden border border-slate-600 bg-[#0b162f] lg:grid-cols-[minmax(0,0.34fr)_minmax(0,0.66fr)]">
      {/* ---------------- LEFT RAIL (navigation / context) ---------------- */}
      <aside className="flex min-h-0 flex-col border-b border-slate-600 p-5 sm:p-6 lg:border-b-0 lg:border-r">
        {stage === "find" || stage === "research" || stage === "select" ? (
          <FindRail
            stage={stage}
            url={url}
            setUrl={setUrl}
            onSubmit={onSubmitFind}
            companyName={companyName}
            error={error}
            onCancel={stage === "select" ? newRobot : undefined}
          />
        ) : stage === "portfolio" ? (
          <PortfolioRail
            company={
              portfolio[0] ? companyIdentity(portfolio[0]).label : companyName
            }
            identityVerified={
              portfolio[0] ? companyIdentity(portfolio[0]).verified : true
            }
            count={portfolio.length}
            onNewRobot={newRobot}
          />
        ) : (
          <ContextRail
            company={active ? companyIdentity(active).label : companyName}
            identityVerified={active ? companyIdentity(active).verified : true}
            product={active?.productName || ""}
            tier={active?.tier || "C"}
            matched={Boolean(active?.matched)}
            showCount={showActiveCount}
            jobCount={Math.min(JOBS_EXAMPLE_CAP, active?.jobs?.length || 0)}
            hint={railTab === "profile" ? RAIL_STEP_HINT.profile : RAIL_STEP_HINT.jobs}
            portfolioCount={portfolio.length}
            railTab={railTab}
            onTab={t => {
              if (t === "profile") {
                setRailTab("profile");
                setStage("review");
                saveWorkspaceSession({
                  url: submittedUrlRef.current,
                  products: portfolio.map(p => p.productName),
                  view: "review",
                  activeIdx,
                  selectedJobKey: expandedJob || undefined,
                  checkedJobKeys,
                });
                return;
              }
              goToJobs(activeIdx);
            }}
            onBackToPortfolio={
              portfolio.length > 1 ? () => setStage("portfolio") : undefined
            }
            onNewRobot={newRobot}
          />
        )}
      </aside>

      {/* ---------------- LARGE WORKSPACE ---------------- */}
      <section className="min-h-0 overflow-y-auto">
        {stage === "find" && (
          <LiveJobTape
            title="Live Robot Jobs"
            subtitle={null}
            corpus={MARKET_TAPE_JOBS}
            baseCount={MARKET_FOUND_BASE}
            running
            statusLines={[]}
            revealTarget={null}
            onRevealComplete={() => undefined}
            onSelect={() => undefined}
            selectedKey={null}
          />
        )}

        {stage === "research" && <ResearchPanel company={companyName} />}

        {stage === "select" && (
          <SelectPanel
            company={companyName}
            products={products}
            selected={selected}
            onToggle={toggleProduct}
            onConfirm={confirmSelection}
          />
        )}

        {stage === "portfolio" && (
          <PortfolioPanel
            company={companyName || portfolio[0]?.companyName || ""}
            robots={portfolio}
            showCounts={countsTrusted}
            onView={idx => void researchPortfolioRobot(idx, "jobs")}
            onReview={idx => void researchPortfolioRobot(idx, "review")}
          />
        )}

        {stage === "review" && active && (
          <ReviewPanel
            analysis={active}
            matching={matching}
            matchError={matchError}
            onFindJobs={() => void findJobsForActive()}
          />
        )}

        {stage === "jobs" && active && (
          <JobsPanel
            analysis={active}
            expandedJob={expandedJob}
            checkedJobKeys={checkedJobKeys}
            showAll={showAllJobs}
            onSelectJob={selectJob}
            onToggleJob={toggleCheckedJob}
            onActivate={goToActivate}
            onSeeAll={seeAllJobs}
            robotCount={portfolio.length}
            companyName={companyName || active.companyName}
            qualifying={matching}
            onSelectClass={id => void qualifyActive(id)}
          />
        )}
      </section>
    </div>
  );
}

/* ================================================================== */
/* Left rail — FIND / RESEARCH / SELECT                                */
/* ================================================================== */

function FindRail({
  stage,
  url,
  setUrl,
  onSubmit,
  companyName,
  error,
  onCancel,
}: {
  stage: Stage;
  url: string;
  setUrl: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  companyName: string;
  error: string | null;
  onCancel?: () => void;
}) {
  const busy = stage === "research" || stage === "select";
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className={eyebrow}>{busy ? "Your robot" : "Find jobs"}</p>
      <h1 className="mt-1 font-display text-3xl font-bold leading-tight tracking-tight text-slate-100">
        {busy ? (
          companyName || "Researching…"
        ) : (
          <>
            Find <span className="text-emerald-400">jobs</span> for your robot.
          </>
        )}
      </h1>
      {!busy && (
        <p className="mt-3 text-sm text-slate-400">
          {RAIL_STEP_HINT.find}
        </p>
      )}

      <form onSubmit={onSubmit} className="mt-6">
        <label className={eyebrow} htmlFor="robot-url">
          Robot product URL
        </label>
        <input
          id="robot-url"
          type="text"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste robot product URL"
          disabled={busy}
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 font-mono text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={busy || !url.trim()}
          className={`${ctaClass} mt-3 w-full`}
        >
          {busy ? "Researching…" : FIND_JOBS_CTA}
        </button>
      </form>

      {error && (
        <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
          {error}
        </p>
      )}

      {stage === "select" && onCancel && (
        <button
          type="button"
          onClick={onCancel}
          className="mt-4 w-full border border-slate-600 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 transition hover:border-slate-400"
        >
          ← Start over
        </button>
      )}

      <div className="mt-auto pt-6">
        <ol className="space-y-3 text-xs text-slate-400">
          <li>
            <span className="font-mono text-emerald-400">01</span> Show us your
            robot — we research the company and product.
          </li>
          <li>
            <span className="font-mono text-emerald-400">02</span> Here are its
            jobs — expand a card for why, unknowns, and blockers.
          </li>
          <li>
            <span className="font-mono text-emerald-400">03</span> Activate the
            job list — checked jobs sit at the top of 15 live jobs.
          </li>
        </ol>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Left rail — PORTFOLIO overview                                      */
/* ================================================================== */

function PortfolioRail({
  company,
  identityVerified,
  count,
  onNewRobot,
}: {
  company: string;
  identityVerified: boolean;
  count: number;
  onNewRobot: () => void;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className={eyebrow}>Portfolio</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-slate-100">
        {company}
      </h2>
      {!identityVerified ? (
        <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-amber-300/80">
          Company identity not fully verified
        </p>
      ) : null}
      <p className="mt-0.5 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300">
        {count} robots
      </p>
      <p className="mt-3 text-[12px] leading-snug text-slate-400">
        Pick one robot. Each SKU is researched on its own — we do not copy one
        robot's jobs onto the rest of the lineup.
      </p>
      <div className="mt-auto pt-6">
        <button
          type="button"
          onClick={onNewRobot}
          className="w-full border border-emerald-500/50 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300 transition hover:border-emerald-400"
        >
          + New robot
        </button>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Left rail — CONTEXT (identity + nav + new robot)                    */
/* ================================================================== */

function ContextRail({
  company,
  identityVerified,
  product,
  tier,
  matched,
  showCount,
  jobCount,
  hint,
  portfolioCount,
  railTab,
  onTab,
  onBackToPortfolio,
  onNewRobot,
}: {
  company: string;
  identityVerified: boolean;
  product: string;
  tier: "A" | "B" | "C";
  matched: boolean;
  showCount: boolean;
  jobCount: number;
  hint: string;
  portfolioCount: number;
  railTab: RailTab;
  onTab: (t: RailTab) => void;
  onBackToPortfolio?: () => void;
  onNewRobot: () => void;
}) {
  const navItem = (t: RailTab, label: string, badge?: string) => (
    <button
      type="button"
      onClick={() => onTab(t)}
      className={`flex w-full items-center justify-between border-l-2 px-3 py-2 text-left font-mono text-[11px] font-bold uppercase tracking-[0.12em] transition ${
        railTab === t
          ? "border-emerald-400 bg-emerald-400/5 text-emerald-300"
          : "border-transparent text-slate-400 hover:text-slate-200"
      }`}
    >
      <span>{label}</span>
      {badge ? <span className="text-slate-500">{badge}</span> : null}
    </button>
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className={eyebrow}>Your robot</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-slate-100">
        {product}
      </h2>
      {company && company !== product ? (
        <p className="mt-0.5 text-sm text-slate-400">{company}</p>
      ) : null}
      {!identityVerified ? (
        <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-amber-300/80">
          Company identity not fully verified
        </p>
      ) : null}
      <div className="mt-3 flex items-center gap-2">
        <span className={eyebrow}>Profile</span>
        <span className={`font-mono text-base font-bold ${tierColor(tier)}`}>
          {tier}
        </span>
        {/* Count only appears once the robot is actually matched AND trustworthy. */}
        {matched && showCount ? (
          <span className="ml-2 font-mono text-[11px] font-bold text-emerald-300">
            {jobCount} EXAMPLE JOBS
          </span>
        ) : null}
      </div>

      {/* Profile is the pre-match checkpoint. Jobs unlock after matching.
          Live list is the activate destination — not a Place buyer dump. */}
      <nav className="mt-6 space-y-1">
        {navItem("profile", "01 Profile")}
        {matched
          ? navItem("jobs", "02 Jobs", showCount ? `${jobCount}` : undefined)
          : (
            <p className="border-l-2 border-transparent px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-600">
              02 Jobs
            </p>
          )}
        <p className="border-l-2 border-transparent px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-600">
          03 Live list
        </p>
      </nav>

      <p className="mt-4 text-[12px] leading-snug text-slate-400">{hint}</p>

      <div className="mt-auto space-y-1 pt-6">
        {onBackToPortfolio ? (
          <button
            type="button"
            onClick={onBackToPortfolio}
            className="block text-left font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500 transition hover:text-slate-300"
          >
            ← All {portfolioCount} robots
          </button>
        ) : null}
        <button
          type="button"
          onClick={onNewRobot}
          className="block text-left font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500 transition hover:text-slate-300"
        >
          + New robot
        </button>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — RESEARCH                                                */
/* ================================================================== */

function ResearchPanel({ company }: { company: string }) {
  const steps = [
    { n: "01", label: "Identify company", done: true },
    { n: "02", label: "Find robots", done: true },
    { n: "03", label: "Read sources & confirm facts", done: false },
  ];
  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Researching your robot</p>
      <h2 className="mt-1 font-display text-2xl font-bold text-slate-100">
        {company || "Understanding your robot…"}
      </h2>
      <ul className="mt-8 space-y-4">
        {steps.map(s => (
          <li key={s.n} className="flex items-center gap-3">
            <span className="font-mono text-sm text-slate-500">{s.n}</span>
            <span className="flex-1 font-mono text-sm uppercase tracking-[0.08em] text-slate-200">
              {s.label}
            </span>
            <span
              className={`font-mono text-sm ${s.done ? "text-emerald-400" : "text-amber-300"}`}
            >
              {s.done ? "✓" : "→"}
            </span>
          </li>
        ))}
      </ul>
      <div className="mt-8 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
        <span className="inline-flex h-2 w-2 animate-ping rounded-full bg-emerald-400" />
        Reading manufacturer sources…
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — SELECT                                                  */
/* ================================================================== */

function SelectPanel({
  company,
  products,
  selected,
  onToggle,
  onConfirm,
}: {
  company: string;
  products: ProductChoice[];
  selected: string[];
  onToggle: (name: string) => void;
  onConfirm: (which: string[] | "all") => void;
}) {
  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Select robot</p>
      <h2 className="mt-1 font-display text-2xl font-bold text-slate-100">
        We found {products.length} robots
      </h2>
      <p className="mt-2 text-sm text-slate-400">
        Which robot should we research? Pick one SKU, or list all of them and
        open each separately — {company || "this maker"} has {products.length}.
        We do not copy one robot's jobs onto the others.
      </p>

      <div className="mt-6 grid gap-2 sm:grid-cols-2">
        {products.map(p => {
          const on = selected.includes(p.name);
          return (
            <button
              key={p.name}
              type="button"
              onClick={() => onToggle(p.name)}
              className={`flex items-center justify-between border px-4 py-3 text-left transition ${
                on
                  ? "border-emerald-400 bg-emerald-400/10"
                  : "border-slate-600 bg-[#081126] hover:border-emerald-500/40"
              }`}
            >
              <span>
                <span className="block text-sm font-bold text-slate-100">
                  {p.name}
                </span>
                {p.displayClass ? (
                  <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-[0.1em] text-slate-500">
                    {p.displayClass.replace(/_/g, " ")}
                  </span>
                ) : null}
              </span>
              <span
                className={`font-mono text-sm ${on ? "text-emerald-400" : "text-slate-600"}`}
              >
                {on ? "✓" : "+"}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={() => onConfirm(selected.length > 0 ? selected : "all")}
          className={ctaClass}
        >
          <FaceCue scale={2} onEmerald />
          {selected.length === 0
            ? `List all ${products.length} robots →`
            : selected.length === 1
              ? `Find jobs for ${selected[0]} →`
              : `List ${selected.length} robots →`}
        </button>
        {selected.length > 0 && selected.length < products.length ? (
          <button
            type="button"
            onClick={() => onConfirm("all")}
            className="mt-3 block font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 transition hover:text-slate-300"
          >
            or all {products.length} robots
          </button>
        ) : null}
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — PORTFOLIO                                               */
/* ================================================================== */

function PortfolioPanel({
  company,
  robots,
  showCounts,
  onView,
  onReview,
}: {
  company: string;
  robots: RobotAnalysis[];
  showCounts: boolean;
  onView: (idx: number) => void;
  onReview: (idx: number) => void;
}) {
  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>{company}</p>
      <h2 className="mt-1 font-display text-2xl font-bold text-slate-100">
        {robots.length} robots
      </h2>
      <p className="mt-2 max-w-xl text-sm text-slate-400">
        Pick a robot to research. Each SKU gets its own jobs — we do not reuse
        one robot's matches for the whole lineup.
      </p>
      <div className="mt-6 space-y-3">
        {robots.map((a, idx) => (
          <div
            key={a.productName}
            className="border border-slate-600 bg-[#081126] p-4"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <h3 className="font-display text-lg font-bold text-slate-100">
                  {a.productName}
                </h3>
                <p className="mt-0.5 text-xs text-slate-400">
                  {capabilitySummary(a)}
                </p>
              </div>
              {/* Only assert a count when the portfolio's counts are genuinely differentiated. */}
              {showCounts ? (
                <span className="font-mono text-sm font-bold text-emerald-300">
                  {a.jobCount} matching jobs
                </span>
              ) : null}
            </div>
            <div className="mt-3 flex gap-3">
              <button
                type="button"
                onClick={() => onView(idx)}
                className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300 hover:text-emerald-200"
              >
                {a.matched ? "View matches →" : "Find jobs for this robot →"}
              </button>
              <button
                type="button"
                onClick={() => onReview(idx)}
                className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400 hover:text-slate-200"
              >
                Review profile
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — REVIEW PROFILE (understanding checkpoint, pre-match)    */
/* ================================================================== */

function ReviewPanel({
  analysis,
  matching,
  matchError,
  onFindJobs,
}: {
  analysis: RobotAnalysis;
  matching: boolean;
  matchError: string | null;
  onFindJobs: () => void;
}) {
  const [showSources, setShowSources] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const profile = analysis.profile;
  const confirmed = confirmedFacts(profile);
  const unknowns = unknownFacts(profile);
  const conflicts = conflictFacts(profile);
  const sources = profile?.sources || [];

  const groundingPct = Math.round((profile?.source_grounding_rate ?? 0) * 100);
  const coveragePct = Math.round((profile?.coverage_rate ?? 0) * 100);
  const qualityPct = Math.round((profile?.source_quality_rate ?? 0) * 100);

  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Here's what we understood</p>
      <div className="mt-1 flex flex-wrap items-baseline gap-x-3">
        <h2 className="font-display text-3xl font-bold tracking-tight text-slate-100">
          {analysis.productName}
        </h2>
        {companyIdentity(analysis).label &&
        companyIdentity(analysis).label !== analysis.productName ? (
          <span className="text-lg text-slate-400">
            {companyIdentity(analysis).label}
          </span>
        ) : null}
      </div>
      {!companyIdentity(analysis).verified ? (
        <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-amber-300/80">
          Company identity not fully verified — showing domain
        </p>
      ) : null}
      <div className="mt-3 flex items-center gap-2">
        <span className={eyebrow}>Profile</span>
        <span
          className={`font-mono text-lg font-bold ${tierColor(analysis.tier)}`}
        >
          {analysis.tier}
        </span>
      </div>
      <p className="mt-1 max-w-2xl text-[13px] leading-snug text-slate-400">
        {profileConfidenceCopy(analysis.tier)}
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <p className={eyebrow}>Confirmed</p>
          {confirmed.length ? (
            <ul className="mt-2 space-y-1.5">
              {confirmed.map(f => (
                <li
                  key={f.id}
                  className="text-[13px] leading-snug text-slate-200"
                >
                  <span className="text-emerald-400">✓</span>{" "}
                  {formatFactLine(f)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-[13px] text-slate-500">
              Identity resolved; no hard constraints extracted yet.
            </p>
          )}
        </div>
        <div>
          <p className={eyebrow}>Still unknown</p>
          {conflicts.length || unknowns.length ? (
            <ul className="mt-2 space-y-1.5">
              {conflicts.map(f => (
                <li
                  key={f.id}
                  className="text-[13px] leading-snug text-amber-200/90"
                >
                  CONFLICTED — {formatFactLine(f)}
                </li>
              ))}
              {unknowns.map(f => (
                <li
                  key={f.id}
                  className="text-[13px] leading-snug text-amber-200/80"
                >
                  ? {formatFactLine(f)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-[13px] leading-snug text-amber-200/80">
              Some constraints may still be unknown even when not listed —
              verify before relying on this profile.
            </p>
          )}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-slate-700 pt-4">
        <span className={eyebrow}>Sources</span>
        <span className="text-[12px] text-slate-400">
          {sources.length.toString().padStart(2, "0")} reviewed
        </span>
        {sources.length ? (
          <button
            type="button"
            onClick={() => setShowSources(v => !v)}
            className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-400"
          >
            {showSources ? "Hide ←" : `View ${sources.length} →`}
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => setShowDetails(v => !v)}
          className="font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500 hover:text-slate-300"
        >
          {showDetails ? "Hide profile details" : "Profile details"}
        </button>
      </div>

      {showDetails && (
        <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-slate-500">
          Grounding {groundingPct}% · Coverage {profile?.coverage_level || "—"}{" "}
          ({coveragePct}%) · Sources {profile?.source_quality_level || "—"} (
          {qualityPct}%)
        </p>
      )}

      {showSources && (
        <ul className="mt-2 max-h-48 space-y-2 overflow-y-auto border border-slate-700 p-2">
          {sources.map(s => (
            <li key={s.id} className="text-[11px] leading-snug">
              <span className="font-mono uppercase tracking-[0.08em] text-slate-500">
                {sourceTypeLabel(s.source_type)}
              </span>
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-0.5 block text-slate-300 underline decoration-slate-600 hover:text-emerald-400"
              >
                {s.title || s.url}
              </a>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-8">
        <button
          type="button"
          onClick={onFindJobs}
          disabled={matching}
          className={ctaClass}
        >
          {matching ? "Matching…" : `Find jobs for ${analysis.productName} →`}
        </button>
        <p className="mt-2 text-[11px] text-slate-500">
          Confirm we understood {analysis.productName} — then we match jobs
          against these capabilities.
        </p>
        {matchError && (
          <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
            {matchError}
          </p>
        )}
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — JOBS (matching output)                                  */
/* ================================================================== */

function shouldQualify(analysis: RobotAnalysis): boolean {
  if (analysis.needsClassChoice) return true;
  if (analysis.zeroReason === "insufficient_profile_evidence") return true;
  if (
    analysis.matched &&
    (analysis.jobs || []).length === 0 &&
    (analysis.capabilities || []).length === 0
  ) {
    return true;
  }
  return false;
}

function JobsPanel({
  analysis,
  expandedJob,
  checkedJobKeys,
  showAll,
  onSelectJob,
  onToggleJob,
  onActivate,
  onSeeAll,
  robotCount = 1,
  companyName = "",
  qualifying = false,
  onSelectClass,
}: {
  analysis: RobotAnalysis;
  expandedJob: string | null;
  checkedJobKeys: string[];
  showAll: boolean;
  onSelectJob: (job: MatchJob) => void;
  onToggleJob: (job: MatchJob) => void;
  onActivate: () => void;
  onSeeAll: () => void;
  robotCount?: number;
  companyName?: string;
  qualifying?: boolean;
  onSelectClass?: (classId: string) => void;
}) {
  const baseJobs = analysis.jobs;
  const visible = showAll
    ? baseJobs.slice(0, JOBS_PIPELINE_CAP)
    : capExampleJobs(baseJobs);
  const hiddenCount = Math.max(0, Math.min(baseJobs.length, JOBS_PIPELINE_CAP) - visible.length);
  const heading = jobsHeading({
    productName: analysis.productName,
    companyName: companyName || analysis.companyName,
    robotCount,
  });
  const checkedCount = checkedJobKeys.filter(k =>
    visible.some(job => job.job_key === k),
  ).length;

  return (
    <div className="p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl font-bold text-slate-100">
          {heading}
        </h2>
        <span className="font-mono text-sm font-bold text-emerald-300">
          {visible.length === 0
            ? ""
            : `${visible.length} JOBS FOR ${analysis.productName.toUpperCase()}`}
        </span>
      </div>
      {baseJobs.length > 0 && (
        <p className="mt-1 text-[12px] text-slate-400">
          Example work {analysis.productName} can do, matched to confirmed
          capabilities. Expand a card to inspect. Check every job you want —
          then activate the list at the bottom.
        </p>
      )}

      {baseJobs.length === 0 ? (
        shouldQualify(analysis) ? (
          <ClassPicker
            robotName={analysis.productName}
            options={analysis.classOptions}
            previewUrl={analysis.previewImageUrl}
            busy={qualifying}
            onSelect={onSelectClass}
          />
        ) : (
          <ZeroState
            robotName={analysis.productName}
            reason={analysis.zeroReason}
          />
        )
      ) : (
        <>
          <ol className="mt-6 space-y-3">
            {visible.map((job, i) => (
              <JobCard
                key={job.job_key}
                index={i + 1}
                job={job}
                robotName={analysis.productName}
                selected={expandedJob === job.job_key}
                checked={checkedJobKeys.includes(job.job_key)}
                onSelect={() => onSelectJob(job)}
                onToggle={() => onToggleJob(job)}
              />
            ))}
          </ol>
          <div className="mt-6">
            <button
              type="button"
              onClick={onActivate}
              disabled={checkedCount === 0}
              className={`${ctaClass} w-full sm:w-auto`}
            >
              <FaceCue scale={2} onEmerald />
              {JOBS_NEXT_CTA}
            </button>
            <p className="mt-2 text-[12px] text-slate-400">
              {checkedCount} selected. {JOBS_NEXT_HINT}.
            </p>
          </div>
          {hiddenCount > 0 ? (
            <button
              type="button"
              onClick={onSeeAll}
              className="mt-4 font-mono text-[12px] font-semibold uppercase tracking-[0.12em] text-emerald-400 hover:text-emerald-300"
            >
              See all {Math.min(baseJobs.length, JOBS_PIPELINE_CAP)} jobs
            </button>
          ) : null}
        </>
      )}
    </div>
  );
}

function ClassPicker({
  robotName,
  options,
  previewUrl,
  busy,
  onSelect,
}: {
  robotName: string;
  options?: ClassOption[];
  previewUrl?: string | null;
  busy?: boolean;
  onSelect?: (classId: string) => void;
}) {
  const choices = options && options.length > 0 ? options : DEFAULT_CLASS_OPTIONS;
  return (
    <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5">
      <p className="font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-300">
        Name the robot class
      </p>
      <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
        What kind of robot is {robotName}?
      </h3>
      <p className="mt-2 text-[13px] leading-snug text-slate-300">
        Photos and the product page were not enough to name the class. Pick the
        closest match so we can find jobs — humanoids like NEO, Unitree, and
        UBTech share the same work primitives.
      </p>
      {previewUrl ? (
        <img
          src={previewUrl}
          alt={`${robotName} product photo`}
          className="mt-4 max-h-40 border border-slate-700 object-contain"
        />
      ) : null}
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {choices.map(opt => (
          <button
            key={opt.id}
            type="button"
            disabled={busy}
            onClick={() => onSelect?.(opt.id)}
            className="border border-slate-600 bg-[#081126] px-3 py-3 text-left transition hover:border-emerald-400/60 hover:bg-emerald-400/5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="block font-display text-sm font-bold text-slate-100">
              {opt.label}
            </span>
            <span className="mt-1 block text-[12px] leading-snug text-slate-400">
              {opt.hint}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * Truthful zero-state after the robot is understood. Class confusion is a
 * picker, not a dead-end. This block is only corpus gap / no compatible jobs.
 */
function ZeroState({
  robotName,
  reason,
}: {
  robotName: string;
  reason?: string | null;
}) {
  const r = (reason || "") as ZeroReason | "";
  if (r === "corpus_gap") {
    return (
      <div className="mt-6 border border-slate-600 bg-[#081126] p-5">
        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
          Corpus gap
        </p>
        <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
          We understand {robotName}, but we don't have work represented for its
          capabilities yet.
        </h3>
        <p className="mt-2 text-[13px] leading-snug text-slate-300">
          The current job corpus is thin for this robot's capability domain.
          This is a coverage gap on our side, not a limitation of the robot.
        </p>
      </div>
    );
  }
  if (r === "no_compatible_jobs") {
    return (
      <div className="mt-6 border border-slate-600 bg-[#081126] p-5">
        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
          No compatible jobs
        </p>
        <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
          We understand {robotName}, but the current jobs don't meet its
          requirements.
        </h3>
        <p className="mt-2 text-[13px] leading-snug text-slate-300">
          Each candidate job has an unmet hard requirement for this robot.
          Unknowns were kept unknown — nothing was promoted into a false match.
        </p>
      </div>
    );
  }
  return (
    <p className="mt-8 text-sm text-slate-400">
      No matched jobs for {robotName} yet.
    </p>
  );
}


function JobCard({
  index,
  job,
  robotName,
  selected,
  checked,
  onSelect,
  onToggle,
}: {
  index: number;
  job: MatchJob;
  robotName: string;
  selected: boolean;
  checked: boolean;
  onSelect: () => void;
  onToggle: () => void;
}) {
  const possible = job.verdict !== "NOT_A_MATCH";
  const place = [job.company_name, job.locality].filter(Boolean).join(" · ");
  return (
    <li
      className={`border bg-[#081126] ${
        selected ? "border-emerald-400/60" : "border-slate-600"
      }`}
    >
      <div className="flex items-start">
        <label
          className="flex shrink-0 cursor-pointer items-start px-3 pt-4"
          onClick={e => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={checked}
            onChange={onToggle}
            aria-label={`Include ${job.title} in the job list`}
            className="mt-0.5 h-4 w-4 accent-emerald-400"
          />
        </label>
        <button
          type="button"
          onClick={onSelect}
          className="flex min-w-0 flex-1 items-start gap-3 py-4 pr-4 text-left"
        >
          <span className="flex-1">
            <span className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                Job {String(index).padStart(2, "0")}
              </span>
              <span
                className={`font-mono text-[10px] font-bold uppercase tracking-[0.12em] ${
                  possible ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {possible ? "Possible match" : "Not a match"}
              </span>
            </span>
            <span className="mt-1 block font-display text-base font-bold leading-snug text-slate-100">
              {job.title}
            </span>
            {place ? (
              <span className="mt-0.5 block text-xs text-slate-400">{place}</span>
            ) : null}
          </span>
          <span className="font-mono text-xs text-slate-500">
            {selected ? "−" : "+"}
          </span>
        </button>
      </div>

      {selected && (
        <div className="border-t border-slate-700 px-4 pb-4 pt-3">
          {job.why?.length ? (
            <div>
              <p className={eyebrow}>Why {robotName}</p>
              <ul className="mt-1 space-y-0.5">
                {job.why.map(w => (
                  <li
                    key={w}
                    className="text-[13px] leading-snug text-slate-200"
                  >
                    <span className="text-emerald-400">✓</span> {w}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {job.still_unknown?.length ? (
            <div className="mt-3">
              <p className={eyebrow}>Still unknown</p>
              <ul className="mt-1 space-y-0.5">
                {job.still_unknown.map(w => (
                  <li
                    key={w}
                    className="text-[13px] leading-snug text-amber-200/80"
                  >
                    ? {w}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {job.blockers?.length ? (
            <div className="mt-3">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-rose-400/80">
                Blocker
              </p>
              <ul className="mt-1 space-y-0.5">
                {job.blockers.map(w => (
                  <li
                    key={w}
                    className="text-[13px] leading-snug text-slate-300"
                  >
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          ) : possible ? (
            <p className="mt-3 text-[12px] text-slate-500">
              No confirmed blocker
            </p>
          ) : null}
        </div>
      )}
    </li>
  );
}

