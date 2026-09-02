/**
 * RobotJobsWorkspace — Jobs process on `/`.
 *
 * Architecture (locked): this is a three-step process on a normal page.
 * Site header + process bar are page chrome. The document scrolls.
 * Two columns are a layout of that page — not a 100vh box that clips Chrome.
 *
 *   FIND → SELECT (several SKUs) → one robot: jobs for that product
 *                              → several/all: type-first match (faster) → jobs
 *   Process: 01 robot → 02 jobs → 03 CRM (top and bottom of the page).


 *
 * Three separated objects:
 *   ROBOT  — what did we understand?      (REVIEW PROFILE, pre-match)
 *   MATCH  — what work looks compatible?  (JOBS, produced only when asked)
 *   JOB    — inspect this one             (employer / work / qualification)
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
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useLocation, useSearch } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import JobsKeepStatusBar from "@/components/JobsKeepStatusBar";
import JobsPresentationOffer from "@/components/JobsPresentationOffer";
import { keepJobsOnAccount } from "@/lib/jobsCrmAccount";
import { trackRobotJobsFunnel } from "@/lib/siteAnalytics";
import {
  fetchRobotJobSearch,
  type RobotJobSearchResult,
} from "@/lib/robotJobSearch";
import { fetchOemListing, fetchRobotProfile } from "@/lib/robotProfile";
import { lookupKnownOem } from "@/lib/knownOemLineups";
import { type CatalogSku } from "@/lib/knownOemCatalog";
import {
  I_KNOW_THE_ROBOT_HINT,
  I_KNOW_THE_ROBOT_LABEL,
  jobsFindHref,
} from "@/lib/jobsLanding";
import {
  formatFactLine,
  profileConfidenceCopy,
  sourceTypeLabel,
  type RobotProfileResult,
} from "@/lib/robotProfile";
import type {
  ClassOption,
  MatchCapability,
  MatchJob,
} from "@/lib/robotJobMatch";
import { classOptionsOrDefault } from "@/lib/robotClassOptions";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import { MARKET_TAPE_JOBS, uniqueTapeJobCount } from "@/lib/jobsTapeCorpus";
import PixelIcon from "@/components/PixelIcon";
import { FACE_EMERALD, KARE_FACE } from "@/lib/kareIcons";
import {
  JOBS_EXAMPLE_CAP,
  FIND_JOBS_CTA,
  FIND_JOBS_HEADLINE_ACCENT_CLASS,
  FIND_JOBS_HEADLINE_CLASS,
  FIND_JOBS_HOME_HEADLINE,
  FIND_JOBS_HOME_SUBHEAD,
  FIND_JOBS_SUBHEAD_CLASS,
  JOBS_NEXT_CTA,
  JOBS_NEXT_HINT,
  JOBS_KEEP_LABEL,
  JOBS_SKIP_LABEL,
  JOBS_PIPELINE_CAP,
  CRM_UNLOCKED_JOBS,
  JOBS_PROCESS_STEPS,
  JOBS_RESTORE_ONCE_KEY,
  JOBS_RUN_ONE_ROBOT_CTA,
  JOBS_SEE_JOBS_CTA,
  RAIL_STEP_HINT,
  JOBS_FRESH_HOME_EVENT,
  canStartFindSubmit,
  canStartClassFindSubmit,
  robotClassTitle,
  consumeJobsWorkspaceRestoreOnce,
  defaultCheckedJobKeys,
  defaultCheckedKeysForLineup,
  exampleJobsForLineup,
  isJobsFreshQuery,
  stripJobsFreshQuery,
  jobIndexLabel,
  JOBS_EYEBROW_CLASS,
  JOBS_META_CLASS,
  JOBS_PLACE_CLASS,
  JOBS_PROCESS_NAV_CLASS,
  JOBS_RAIL_LINK_CLASS,
  JOBS_ROBOT_NAME_CLASS,
  jobsCrmOpenHref,
  jobsCountEyebrow,
  jobsDumpedToCrm,
  jobsForCrmDesk,
  recordPipelineActivity,
  jobsHeading,
  jobsListHint,
  jobsProcessActionClass,
  jobsProcessActionLabel,
  jobsProcessStepFromStage,
  jobsProductLimitForPlan,
  lineupJobLookups,
  lineupSegments,
  usesLineupSegments,
  searchNamesForSegment,
  skuLookupGrain,
  configurationClassForLookup,
  portfolioShowsJobCounts,
  productClassesFromLineup,
  qualifySearchLookupGrain,
  shouldShowClassPicker,
  classJobsEmptyCopy,
  CLASS_PICKER_PROMPT,
  readNavigationType,
  shouldRestoreJobsWorkspace,
  filterJobsLineupProducts,
  pageJobsLineup,
  JOBS_PRODUCT_CAP_FREE,
  JOBS_PRODUCT_CAP_PAID,
  JOBS_LINEUP_DISPLAY_CAP,
  OEM_LISTING_TIMEOUT_MS,
  ROBOT_PROFILE_TIMEOUT_MS,
  ROBOT_JOB_SEARCH_TIMEOUT_MS,
  FIND_IDENTITY_TIMEOUT_MS,
} from "@/lib/jobsWorkflow";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import {
  beginJobsHandoffForUrl,
  clearJobsHandoffSnapshot,
  saveJobsHandoffSnapshot,
} from "@/lib/jobsHandoffSnapshot";
import {
  isAbortError,
  isCurrentRobotSubmit,
  sameRobotUrl,
} from "@/lib/robotUrlIdentity";
import {
  beginFindResearch,
  FIND_RESEARCH_INTERRUPTED_MESSAGE,
  ensureFindStayVisit,
  findResearchFailureMessage,
  isLiveFindResearch,
  shouldContinueAfterListingError,
  shouldIgnoreStaleFindError,
  type FindResearchHandle,
} from "@/lib/findResearch";
import { isNamedRobotJob, robotJobCardFromMatch } from "@/lib/robotJobCard";
import JobsPstackProtocol from "@/components/JobsPstackProtocol";

/* ------------------------------------------------------------------ */
/* Types + constants                                                   */
/* ------------------------------------------------------------------ */

type Stage = "find" | "research" | "select" | "portfolio" | "review" | "jobs";
type RailTab = "profile" | "jobs";
type ResearchPhase = "identity" | "jobs";

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
  lookupGrain?: "robot_type" | "product";
  robotClass?: string | null;
};

type ZeroReason =
  | "insufficient_profile_evidence"
  | "no_compatible_jobs"
  | "corpus_gap";

type ProductChoice = {
  name: string;
  displayClass?: string | null;
  description?: string | null;
};
type RestoreView = "review" | "jobs" | "portfolio";

const MARKET_FOUND_BASE = uniqueTapeJobCount();
const WORKSPACE_SESSION_KEY = "rfr_jobs_workspace";

const eyebrow = JOBS_EYEBROW_CLASS;
const ctaClass =
  "rfr-bevel inline-flex items-center justify-center gap-2 bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-45";

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

function JobsProcessNav({
  current,
  onFind,
  onJobs,
  onActivate,
  layout = "rail",
  actionLabel,
  onAction,
  actionClassName,
}: {
  current: "find" | "jobs" | "activate";
  onFind?: () => void;
  onJobs?: () => void;
  onActivate?: () => void;
  layout?: "rail" | "page";
  actionLabel?: string;
  onAction?: () => void;
  actionClassName?: string;
}) {
  const page = layout === "page";
  return (
    <nav
      aria-label="Jobs process"
      className={
        page ? "rfr-jobs-process-bar flex flex-wrap items-stretch" : "space-y-1"
      }
    >
      {JOBS_PROCESS_STEPS.map(step => {
        const isCurrent = current === step.id;
        const onClick =
          step.id === "find"
            ? onFind
            : step.id === "jobs"
              ? onJobs
              : onActivate;
        const className = page
          ? `flex min-w-0 flex-1 cursor-pointer items-center justify-between gap-2 px-3 py-3 text-left ${JOBS_PROCESS_NAV_CLASS} transition disabled:cursor-not-allowed ${
              isCurrent
                ? "border-b-2 border-emerald-400 bg-emerald-400/5 text-emerald-300"
                : onClick
                  ? "border-b-2 border-transparent text-slate-400 hover:text-slate-200"
                  : "border-b-2 border-transparent text-slate-600"
            }`
          : `flex w-full cursor-pointer items-center justify-between border-l-2 px-3 py-2 text-left ${JOBS_PROCESS_NAV_CLASS} transition disabled:cursor-not-allowed ${
              isCurrent
                ? "border-emerald-400 bg-emerald-400/5 text-emerald-300"
                : onClick
                  ? "border-transparent text-slate-400 hover:text-slate-200"
                  : "border-transparent text-slate-600"
            }`;
        const label = `${step.n} ${step.label}`;
        return (
          <button
            key={step.id}
            type="button"
            onClick={onClick}
            disabled={!onClick}
            aria-current={isCurrent ? "step" : undefined}
            className={className}
          >
            <span>{label}</span>
            {!page ? (
              <span
                className={isCurrent ? "text-emerald-400/80" : "text-slate-500"}
              >
                {step.linkLabel}
              </span>
            ) : null}
          </button>
        );
      })}
      {page && onAction && actionLabel ? (
        <button
          type="button"
          onClick={onAction}
          className={`rfr-jobs-process-action m-2 shrink-0 ${
            actionClassName ||
            "rfr-bevel inline-flex items-center justify-center bg-emerald-400 px-4 py-2 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300"
          }`}
        >
          {actionLabel}
        </button>
      ) : null}
    </nav>
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
  productClasses?: Record<string, string>;
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
      productClasses?: unknown;
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
    const productClasses: Record<string, string> = {};
    if (parsed.productClasses && typeof parsed.productClasses === "object") {
      for (const [name, cls] of Object.entries(
        parsed.productClasses as Record<string, unknown>
      )) {
        if (typeof cls === "string" && cls.trim()) productClasses[name] = cls;
      }
    }
    return {
      url: parsed.url,
      products: Array.isArray(parsed.products) ? parsed.products : [],
      view,
      activeIdx: parsed.activeIdx,
      selectedJobKey: parsed.selectedJobKey,
      checkedJobKeys,
      productClasses,
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
  clearJobsHandoffSnapshot();
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
function identityAnalysis(
  productName: string,
  companyName: string
): RobotAnalysis {
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
    jobs: (res.jobs || []).filter(isNamedRobotJob),
    jobCount: (res.jobs || []).filter(isNamedRobotJob).length,
    zeroReason: res.zero_reason ?? null,
    needsClassChoice: Boolean(res.needs_class_choice),
    classOptions: res.class_options || [],
    previewImageUrl: res.preview_image_url ?? null,
    lookupGrain: "product",
    robotClass:
      configurationClassForLookup(res.robot_class) ||
      configurationClassForLookup(profile?.selected_product?.display_class),
  };
}

function typeMatchToAnalysis(
  res: RobotJobSearchResult,
  productName: string,
  robotClass: string
): RobotAnalysis {
  return {
    ...searchToAnalysis(res),
    productName,
    lookupGrain: "robot_type",
    robotClass,
  };
}

/** One named SKU: MATCH the configuration work-kind, not the FIND tile. */
function analysisForSelectedSku(
  res: RobotJobSearchResult,
  name: string,
  displayClass?: string | null
): RobotAnalysis {
  void displayClass;
  return {
    ...searchToAnalysis(res),
    productName: name,
    lookupGrain: "product",
  };
}

function sessionProductClasses(
  names: string[],
  products: ProductChoice[],
  extra?: Record<string, string>
): Record<string, string> {
  const fromPicker = productClassesFromLineup(
    names.map(name => ({
      name,
      displayClass: products.find(p => p.name === name)?.displayClass,
    }))
  );
  return { ...fromPicker, ...(extra || {}) };
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
 * numbers that would undermine the promise. Unresearched shells stay quiet.
 */
function differentiatedCounts(portfolio: RobotAnalysis[]): boolean {
  return portfolioShowsJobCounts(portfolio);
}

function lookupFailedMessage(err: unknown, fallback: string): string {
  return findResearchFailureMessage(err, fallback);
}

function pickSelectedJobKey(
  jobs: MatchJob[],
  preferred?: string | null
): string | null {
  if (preferred && jobs.some(j => j.job_key === preferred)) return preferred;
  return jobs[0]?.job_key ?? null;
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function RobotJobsWorkspace() {
  const { session } = useAuth();
  const [, setLocation] = useLocation();
  const search = useSearch();
  const [stage, setStage] = useState<Stage>(() => {
    if (typeof window === "undefined") return "find";
    if (isJobsFreshQuery(window.location.search)) {
      try {
        window.sessionStorage.removeItem(WORKSPACE_SESSION_KEY);
        window.sessionStorage.removeItem(JOBS_RESTORE_ONCE_KEY);
      } catch {
        /* ignore */
      }
      clearJobsHandoffSnapshot();
      return "find";
    }
    const saved = readWorkspaceSession();
    if (!saved?.url) return "find";
    let restoreOnce = false;
    try {
      restoreOnce =
        window.sessionStorage.getItem(JOBS_RESTORE_ONCE_KEY) === "1";
    } catch {
      restoreOnce = false;
    }
    const restoreQuery =
      new URLSearchParams(window.location.search).get("restore") === "1";
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
  const [productCap, setProductCap] = useState(JOBS_PRODUCT_CAP_FREE);
  const [plan, setPlan] = useState<string>("anonymous");
  const [researchPhase, setResearchPhase] = useState<ResearchPhase>("identity");

  // Results
  const [portfolio, setPortfolio] = useState<RobotAnalysis[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [railTab, setRailTab] = useState<RailTab>("jobs");
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [checkedJobKeys, setCheckedJobKeys] = useState<string[]>([]);
  const [keepSavedCount, setKeepSavedCount] = useState(0);
  const [showAllJobs, setShowAllJobs] = useState(false);
  const [lineupPreview, setLineupPreview] = useState(false);

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
  const researchAbortRef = useRef<AbortController | null>(null);
  const researchHandleRef = useRef<FindResearchHandle | null>(null);
  const matchAbortRef = useRef<(() => void) | null>(null);
  const findInFlightRef = useRef(false);

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

  useEffect(() => {
    const token = session?.access_token;
    if (!token) {
      setProductCap(JOBS_PRODUCT_CAP_FREE);
      setPlan("anonymous");
      return;
    }
    let cancelled = false;
    void fetch(
      `${getApiBase()}/api/user/me`,
      liveFetchInit({ headers: authHeader(token) })
    )
      .then(res => (res.ok ? res.json() : null))
      .then(
        (
          data: {
            entitlements?: { plan?: string; jobs_product_limit?: number };
          } | null
        ) => {
          if (cancelled) return;
          setPlan(data?.entitlements?.plan || "free");
          const fromApi = data?.entitlements?.jobs_product_limit;
          if (typeof fromApi === "number" && fromApi > 0) {
            setProductCap(fromApi);
            return;
          }
          setProductCap(jobsProductLimitForPlan(data?.entitlements?.plan));
        }
      )
      .catch(() => {
        if (!cancelled) setProductCap(JOBS_PRODUCT_CAP_FREE);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  function resetToFind(replaceHome = false) {
    researchHandleRef.current?.controller.abort();
    researchHandleRef.current = null;
    if (researchAbortRef.current) {
      researchAbortRef.current.abort();
      researchAbortRef.current = null;
    }
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
    setKeepSavedCount(0);
    setShowAllJobs(false);
    setLineupPreview(false);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    restoredRef.current = true;
    submittedUrlRef.current = "";
    submissionIdRef.current = null;
    findInFlightRef.current = false;
    clearWorkspaceSession();
    if (replaceHome) {
      stripJobsFreshQuery();
    }
  }

  /** New FIND URL: abort *previous* in-flight work and bind CRM (honest empty). */
  function bindSubmittedRobot(submitUrl: string): FindResearchHandle {
    submittedUrlRef.current = submitUrl;
    submissionIdRef.current = null;
    const handle = beginFindResearch(researchHandleRef.current, submitUrl);
    researchHandleRef.current = handle;
    researchAbortRef.current = handle.controller;
    if (matchAbortRef.current) {
      matchAbortRef.current();
      matchAbortRef.current = null;
    }
    setPortfolio([]);
    setProducts([]);
    setSelected([]);
    setCompanyName("");
    setActiveIdx(0);
    setExpandedJob(null);
    setCheckedJobKeys([]);
    setKeepSavedCount(0);
    setShowAllJobs(false);
    setLineupPreview(false);
    setMatchError(null);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    beginJobsHandoffForUrl(submitUrl);
    saveWorkspaceSession({
      url: submitUrl,
      products: [],
      view: "jobs",
    });
    return handle;
  }

  function stillThisSubmit(
    submitUrl: string,
    handle?: FindResearchHandle | null
  ): boolean {
    const live = handle || researchHandleRef.current;
    if (!live) return false;
    return (
      isLiveFindResearch(researchHandleRef.current, live) &&
      isCurrentRobotSubmit(submittedUrlRef.current, submitUrl)
    );
  }

  /* Strip `/?new=1` after paint. Never replaceState during render — wouter
     patches history and that remounts FIND. Never resetToFind here: a typed
     URL or in-flight research must not be aborted by the fresh-query flag. */
  useLayoutEffect(() => {
    stripJobsFreshQuery();
  }, []);

  useEffect(() => {
    if (
      !isJobsFreshQuery(search) &&
      !isJobsFreshQuery(window.location.search)
    ) {
      return;
    }
    stripJobsFreshQuery();
  }, [search]);

  useEffect(() => {
    const onFresh = () => resetToFind(true);
    window.addEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
    return () => window.removeEventListener(JOBS_FRESH_HOME_EVENT, onFresh);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* Restore only on refresh, back/forward, or an auth one-shot.
     A normal revisit of `/` must show FIND — not replay the last robot URL. */
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    if (isJobsFreshQuery(window.location.search)) {
      stripJobsFreshQuery();
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
        window.history.replaceState({}, "", jobsFindHref());
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

  function openJobsFromAnalyses(
    analyses: RobotAnalysis[],
    submitUrl: string,
    names: string[],
    handle?: FindResearchHandle | null
  ) {
    if (!stillThisSubmit(submitUrl, handle)) return;
    const first = analyses[0];
    if (!first) return;
    const company = first.companyName || companyName;
    const withCompany = analyses.map(row => ({
      ...row,
      companyName: row.companyName || company,
    }));
    const tagged = exampleJobsForLineup(withCompany);
    const checks = defaultCheckedKeysForLineup(withCompany);
    const selectedKey =
      tagged[0]?.job_key || pickSelectedJobKey(first.jobs, null);
    setPortfolio(withCompany);
    setActiveIdx(0);
    setCompanyName(company);
    setRailTab("jobs");
    setExpandedJob(selectedKey);
    setCheckedJobKeys(checks);
    setLineupPreview(names.length > 1);
    saveWorkspaceSession({
      url: submitUrl,
      products: names,
      view: "jobs",
      activeIdx: 0,
      selectedJobKey: selectedKey || undefined,
      checkedJobKeys: checks,
      productClasses: sessionProductClasses(names, products),
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: first.productName,
      job_count: first.jobCount,
      robots_analyzed: names.length,
      lookup_grain: first.lookupGrain || "product",
    });
    writeCrmHandoff(
      checks,
      tagged.map(job => ({
        ...job,
        forRobot: first.productName || "",
      })),
      first.productName,
      jobsDumpedToCrm(tagged, checks, CRM_UNLOCKED_JOBS)
    );
    setStage("jobs");
  }

  /** FIND submit — research identity first (no jobs yet). */
  async function submitFind(submitUrl: string) {
    setError(null);
    const research = bindSubmittedRobot(submitUrl);
    const ac = research.controller;
    setResearchPhase("identity");
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
    const live = () => stillThisSubmit(submitUrl, research);
    try {
      const known = lookupKnownOem(submitUrl);
      if (known && known.robots.length > 0) {
        if (!live()) return;
        setCompanyName(known.vendor_name || "");
        const lineup = filterJobsLineupProducts(
          known.robots.map(p => ({
            name: p.name,
            displayClass: p.display_class,
            description: p.description,
          }))
        );
        if (lineup.length > 1) {
          setProducts(lineup);
          setSelected([]);
          setStage("select");
          return;
        }
        if (lineup.length === 1) {
          const name = lineup[0].name;
          const displayClass = lineup[0].displayClass;
          const cls = configurationClassForLookup(displayClass);
          setResearchPhase("jobs");
          const res = await fetchRobotJobSearch({
            url: submitUrl,
            product: name || undefined,
            assertedClass: cls || undefined,
            lookupGrain: "product",
            signal: ac.signal,
            timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
          });
          if (!live()) return;
          submissionIdRef.current =
            res.robot_submission_id ?? submissionIdRef.current;
          const analysis = analysisForSelectedSku(res, name, displayClass);
          openJobsFromAnalyses(
            [analysis],
            submitUrl,
            name ? [name] : [],
            research
          );
          return;
        }
      }
      try {
        const listing = await fetchOemListing({
          url: submitUrl,
          signal: ac.signal,
          timeoutMs: OEM_LISTING_TIMEOUT_MS,
        });
        if (!live()) return;
        if (listing.matched && listing.robots.length > 0) {
          setCompanyName(listing.vendor_name || "");
          const lineup = filterJobsLineupProducts(
            listing.robots.map(p => ({
              name: p.name,
              displayClass: p.display_class,
              description: p.description,
            }))
          );
          if (lineup.length > 1) {
            setProducts(lineup);
            setSelected([]);
            setStage("select");
            return;
          }
          const name = lineup[0]?.name || listing.robots[0]?.name || "";
          const displayClass =
            lineup[0]?.displayClass || listing.robots[0]?.display_class;
          const cls = configurationClassForLookup(displayClass);
          setResearchPhase("jobs");
          const res = await fetchRobotJobSearch({
            url: submitUrl,
            product: name || undefined,
            assertedClass: cls || undefined,
            lookupGrain: "product",
            signal: ac.signal,
            timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
          });
          if (!live()) return;
          submissionIdRef.current =
            res.robot_submission_id ?? submissionIdRef.current;
          const analysis = analysisForSelectedSku(res, name, displayClass);
          openJobsFromAnalyses(
            [analysis],
            submitUrl,
            name ? [name] : [],
            research
          );
          return;
        }
      } catch (listingErr) {
        if (
          shouldIgnoreStaleFindError({
            current: researchHandleRef.current,
            handle: research,
          }) ||
          !shouldContinueAfterListingError({
            current: researchHandleRef.current,
            handle: research,
            err: listingErr,
          })
        ) {
          return;
        }
        /* listing miss or timeout — one composed search, not profile then search */
      }
      if (!live()) return;
      setResearchPhase("jobs");
      const res = await fetchRobotJobSearch({
        url: submitUrl,
        lookupGrain: "product",
        signal: ac.signal,
        timeoutMs: FIND_IDENTITY_TIMEOUT_MS,
      });
      if (!live()) return;
      submissionIdRef.current =
        res.robot_submission_id ?? submissionIdRef.current;
      setCompanyName(res.company_name || res.profile?.company?.name || "");
      const searchProducts =
        (res.products && res.products.length
          ? res.products
          : res.profile?.products) || [];
      const lineup = filterJobsLineupProducts(
        searchProducts.map(p => ({
          name: p.name,
          displayClass:
            ("display_class" in p ? p.display_class : null) ||
            ("robot_class" in p ? p.robot_class : null) ||
            null,
          description:
            "description" in p && typeof p.description === "string"
              ? p.description
              : undefined,
        }))
      );
      if (lineup.length === 0) {
        setCompanyName(res.company_name || res.profile?.company?.name || "");
        setProducts([]);
        const analysis = {
          ...searchToAnalysis(res),
          productName: "",
          jobs: [],
          jobCount: 0,
          needsClassChoice: true,
          matched: true,
        };
        openJobsFromAnalyses([analysis], submitUrl, [], research);
        return;
      }
      if (
        (res.needs_product_choice || lineup.length > 1) &&
        lineup.length > 1
      ) {
        setProducts(lineup);
        setSelected([]);
        setStage("select");
        return;
      }
      const name =
        lineup[0]?.name ||
        res.profile?.selected_product?.name ||
        res.robot_name ||
        res.company_name ||
        "";
      const displayClass =
        lineup[0]?.displayClass ||
        res.profile?.selected_product?.display_class ||
        res.robot_class;
      const analysis = analysisForSelectedSku(res, name, displayClass);
      openJobsFromAnalyses([analysis], submitUrl, name ? [name] : [], research);
    } catch (err) {
      if (
        shouldIgnoreStaleFindError({
          current: researchHandleRef.current,
          handle: research,
        })
      ) {
        return;
      }
      ensureFindStayVisit();
      if (research.controller.signal.aborted || isAbortError(err, ac.signal)) {
        setError(FIND_RESEARCH_INTERRUPTED_MESSAGE);
        setStage("find");
        return;
      }
      setError(
        lookupFailedMessage(
          err,
          "Research failed. Check the URL and try again."
        )
      );
      setStage("find");
    } finally {
      if (live()) findInFlightRef.current = false;
    }
  }

  /** SELECT — picker already chose; go to jobs. One SKU = that product. Several = type-first. */
  async function confirmSelection(which: string[] | "all") {
    const names = (which === "all" ? products.map(p => p.name) : which)
      .filter(Boolean)
      .slice(0, productCap);
    if (names.length === 0) return;
    const submitUrl = submittedUrlRef.current || url;

    const research = beginFindResearch(researchHandleRef.current, submitUrl);
    researchHandleRef.current = research;
    researchAbortRef.current = research.controller;
    const ac = research.controller;
    setResearchPhase("jobs");
    if (names.length === 1) {
      setStage("research");
      try {
        const displayClass = products.find(
          p => p.name === names[0]
        )?.displayClass;
        const cls = configurationClassForLookup(displayClass);
        const res = await fetchRobotJobSearch({
          url: submitUrl,
          product: names[0],
          assertedClass: cls || undefined,
          lookupGrain: "product",
          signal: ac.signal,
          timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
        });
        submissionIdRef.current =
          res.robot_submission_id ?? submissionIdRef.current;
        if (!stillThisSubmit(submitUrl, research)) return;
        openJobsFromAnalyses(
          [analysisForSelectedSku(res, names[0], displayClass)],
          submitUrl,
          names,
          research
        );
      } catch (err) {
        if (
          shouldIgnoreStaleFindError({
            current: researchHandleRef.current,
            handle: research,
          })
        )
          return;
        ensureFindStayVisit();
        if (
          research.controller.signal.aborted ||
          isAbortError(err, ac.signal)
        ) {
          setError(FIND_RESEARCH_INTERRUPTED_MESSAGE);
          setStage("select");
          return;
        }
        setError(lookupFailedMessage(err, "Research failed for that robot."));
        setStage("select");
      }
      return;
    }

    // Several / all — one job search per robot type (the group), not per SKU.
    setStage("research");
    try {
      const selectedProducts = names.map(name => ({
        name,
        displayClass: products.find(p => p.name === name)?.displayClass || null,
      }));
      const lookups = lineupJobLookups(selectedProducts);
      const classResults = new Map<string, RobotJobSearchResult>();
      const skuResults = new Map<string, RobotJobSearchResult>();
      await Promise.all(
        lookups.map(async lookup => {
          if (lookup.grain === "robot_type" && lookup.robotClass) {
            const res = await fetchRobotJobSearch({
              url: submitUrl,
              assertedClass: lookup.robotClass,
              lookupGrain: "robot_type",
              signal: ac.signal,
              timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
            });
            classResults.set(lookup.robotClass, res);
            return;
          }
          const product = lookup.productNames[0];
          if (!product) return;
          const res = await fetchRobotJobSearch({
            url: submitUrl,
            product,
            signal: ac.signal,
            timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
          });
          skuResults.set(product, res);
        })
      );

      if (!stillThisSubmit(submitUrl, research)) return;
      const analyses: RobotAnalysis[] = selectedProducts.map(row => {
        const cls = configurationClassForLookup(row.displayClass);
        if (cls && classResults.has(cls)) {
          return typeMatchToAnalysis(classResults.get(cls)!, row.name, cls);
        }
        const sku = skuResults.get(row.name);
        if (sku) {
          return { ...searchToAnalysis(sku), productName: row.name };
        }
        return identityAnalysis(row.name, companyName);
      });
      const first = analyses[0];
      if (!first) {
        setError("Research failed for those robots.");
        setStage("select");
        return;
      }
      const company = first.companyName || companyName;
      const withCompany = analyses.map(row => ({
        ...row,
        companyName: row.companyName || company,
      }));
      for (const res of [...classResults.values(), ...skuResults.values()]) {
        if (res.robot_submission_id) {
          submissionIdRef.current = res.robot_submission_id;
          break;
        }
      }
      openJobsFromAnalyses(withCompany, submitUrl, names, research);
    } catch (err) {
      if (
        shouldIgnoreStaleFindError({
          current: researchHandleRef.current,
          handle: research,
        })
      )
        return;
      ensureFindStayVisit();
      if (research.controller.signal.aborted || isAbortError(err, ac.signal)) {
        setError(FIND_RESEARCH_INTERRUPTED_MESSAGE);
        setStage("select");
        return;
      }
      setError(lookupFailedMessage(err, "Research failed for those robots."));
      setStage("select");
    }
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
          i === idx ? analysis : identityAnalysis(name, analysis.companyName)
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
      const res = await fetchRobotJobSearch({
        url: submittedUrlRef.current,
        product: a.productName,
        assertedClass: a.robotClass || undefined,
        lookupGrain: "product",
      });
      if (aborted) return;
      const merged: RobotAnalysis = {
        ...searchToAnalysis(res),
        productName: a.productName,
        profile: a.profile || searchToAnalysis(res).profile,
        lookupGrain: "product",
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

  /** Operator names the class so Jobs can search. Never a silent no-op. */
  async function qualifyActive(classId: string) {
    const chosen = String(classId || "").trim();
    if (!chosen) {
      setMatchError("Pick a robot type to search for jobs.");
      return;
    }
    const url = submittedUrlRef.current;
    if (!url) {
      setMatchError("Paste a robot URL, then pick a type.");
      return;
    }
    const prior = portfolio[activeIdx];
    const productName = String(prior?.productName || "").trim();
    const grain = qualifySearchLookupGrain(productName);
    setMatching(true);
    setMatchError(null);
    setStage("jobs");
    let aborted = false;
    if (matchAbortRef.current) {
      matchAbortRef.current();
    }
    matchAbortRef.current = () => {
      aborted = true;
    };
    try {
      const res = await fetchRobotJobSearch({
        url,
        product: grain === "product" ? productName : undefined,
        assertedClass: chosen,
        lookupGrain: grain,
      });
      if (aborted) return;
      const next = searchToAnalysis(res);
      const merged: RobotAnalysis = {
        ...next,
        productName:
          (grain === "product" && productName
            ? productName
            : prior?.productName || next.productName || companyName) ||
          next.productName,
        companyName: prior?.companyName || next.companyName || companyName,
        profile: prior?.profile || next.profile,
        lookupGrain: grain,
        robotClass: chosen,
        needsClassChoice: false,
      };
      setPortfolio(prev =>
        prev.length
          ? prev.map((p, i) => (i === activeIdx ? merged : p))
          : [merged]
      );
      revealJobs(merged);
    } catch {
      if (!aborted) {
        setMatchError("Could not find jobs for that robot type. Try again.");
      }
    } finally {
      matchAbortRef.current = null;
      if (!aborted) {
        setMatching(false);
      }
    }
  }

  function revealJobs(a: RobotAnalysis) {
    const checks = defaultCheckedJobKeys(a.jobs);
    setLineupPreview(false);
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
    writeCrmHandoff(
      checks,
      a.jobs.map(job => ({
        ...job,
        forRobot: a.productName || "",
      })),
      a.productName
    );
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a.productName,
      job_count: a.jobCount,
    });
  }

  function goToJobs(idx: number) {
    setActiveIdx(idx);
    setLineupPreview(false);
    const a = portfolio[idx];
    const selectedKey = pickSelectedJobKey(a?.jobs || [], expandedJob);
    const checks =
      checkedJobKeys.length > 0
        ? checkedJobKeys.filter(k => (a?.jobs || []).some(j => j.job_key === k))
        : defaultCheckedJobKeys(a?.jobs || []);
    const nextChecks = checks.length
      ? checks
      : defaultCheckedJobKeys(a?.jobs || []);
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
    writeCrmHandoff(
      nextChecks,
      (a?.jobs || []).map(job => ({
        ...job,
        forRobot: a?.productName || "",
      })),
      a?.productName
    );
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a?.productName,
      job_count: a?.jobCount,
    });
  }

  function crmPool(): MatchJob[] {
    return lineupPreview
      ? exampleJobsForLineup(portfolio)
      : (active?.jobs || []).map(job => ({
          ...job,
          forRobot: active?.productName || "",
        }));
  }

  function writeCrmHandoff(
    checks: string[],
    pool = crmPool(),
    productName?: string,
    jobsOverride?: MatchJob[]
  ) {
    const url = submittedUrlRef.current;
    if (!url) return;
    const jobs =
      jobsOverride ?? jobsDumpedToCrm(pool, checks, CRM_UNLOCKED_JOBS);
    saveJobsHandoffSnapshot({
      url,
      productName:
        productName ||
        (lineupPreview
          ? companyName || active?.companyName || ""
          : active?.productName || ""),
      jobs,
      selectedCount: jobs.length,
    });
  }

  function goToActivate() {
    if (!handoffCheckedJobs()) return;
    setLocation(jobsCrmOpenHref(Boolean(session), submissionIdRef.current));
  }

  function handoffCheckedJobs(): boolean {
    if (active && shouldShowClassPicker(active)) {
      document
        .getElementById("jobs-list")
        ?.scrollIntoView({ behavior: "smooth" });
      return false;
    }
    const pool = crmPool();
    const jobs = jobsForCrmDesk(pool, checkedJobKeys, CRM_UNLOCKED_JOBS);
    writeCrmHandoff(checkedJobKeys, pool, undefined, jobs);
    for (const job of jobs) {
      recordPipelineActivity({
        kind: "dump",
        label: "Kept from FIND",
        jobKey: job.job_key,
        company: job.company || undefined,
        robotUrl: submittedUrlRef.current,
      });
    }
    recordPipelineActivity({
      kind: "open_crm",
      label: "Opened CRM",
      robotUrl: submittedUrlRef.current,
    });
    trackRobotJobsFunnel("jobs_list_activated", {
      ...funnelBase(),
      robot_name: active?.productName,
      selected_count: jobs.length,
      list_count: jobs.length,
    });
    void persistKeptJobs(jobs);
    return true;
  }

  async function persistKeptJobs(jobs: MatchJob[]) {
    const pool = jobs.filter(job => job?.job_key);
    if (!pool.length) return;
    setKeepSavedCount(pool.length);
    const token = session?.access_token;
    if (!token) return;
    try {
      const result = await keepJobsOnAccount(token, {
        jobs: pool,
        robotName: active?.productName || companyName,
        robotUrl: submittedUrlRef.current,
        submissionId: submissionIdRef.current,
      });
      setKeepSavedCount(result.saved_count);
    } catch {
      /* handoff still holds the rows */
    }
  }

  function applyCheckedKeys(jobs: MatchJob[], saved?: string[]) {
    const fromSaved = (saved || []).filter(k =>
      jobs.some(j => j.job_key === k)
    );
    const next = fromSaved.length ? fromSaved : defaultCheckedJobKeys(jobs);
    setCheckedJobKeys(next);
    writeCrmHandoff(
      next,
      jobs.map(job => ({
        ...job,
        forRobot: active?.productName || "",
      }))
    );
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
        const cls =
          a.robotClass ||
          configurationClassForLookup(
            products.find(p => p.name === a.productName)?.displayClass
          );
        const search = await fetchRobotJobSearch({
          url: submitUrl,
          product: a.productName,
          assertedClass: cls || undefined,
          lookupGrain: "product",
        });
        submissionIdRef.current =
          search.robot_submission_id ?? submissionIdRef.current;
        const merged = {
          ...searchToAnalysis(search),
          productName: a.productName,
          lookupGrain: "product" as const,
        };
        setPortfolio(prev => prev.map((p, i) => (i === idx ? merged : p)));
        setCompanyName(merged.companyName);
        setLineupPreview(false);
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
          productClasses: sessionProductClasses(names, products),
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
        timeoutMs: ROBOT_PROFILE_TIMEOUT_MS,
      });
      submissionIdRef.current =
        profile.robot_submission_id ?? submissionIdRef.current;
      const merged = profileToAnalysis(profile);
      setPortfolio(prev =>
        prev.map((p, i) =>
          i === idx
            ? merged
            : { ...p, companyName: merged.companyName || p.companyName }
        )
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
          const lineup = saved.products.map(name => ({
            name,
            displayClass: saved.productClasses?.[name] || null,
          }));
          setProducts(
            lineup.map(row => ({
              name: row.name,
              displayClass: row.displayClass,
            }))
          );
          const lookups = lineupJobLookups(lineup);
          const classResults = new Map<string, RobotJobSearchResult>();
          const skuResults = new Map<string, RobotJobSearchResult>();
          await Promise.all(
            lookups.map(async lookup => {
              if (lookup.grain === "robot_type" && lookup.robotClass) {
                const res = await fetchRobotJobSearch({
                  url: saved.url,
                  assertedClass: lookup.robotClass,
                  lookupGrain: "robot_type",
                });
                classResults.set(lookup.robotClass, res);
                return;
              }
              const skuName = lookup.productNames[0];
              if (!skuName) return;
              const res = await fetchRobotJobSearch({
                url: saved.url,
                product: skuName,
              });
              skuResults.set(skuName, res);
            })
          );
          const analyses = lineup.map(row => {
            const cls = configurationClassForLookup(row.displayClass);
            if (cls && classResults.has(cls)) {
              return typeMatchToAnalysis(classResults.get(cls)!, row.name, cls);
            }
            const sku = skuResults.get(row.name);
            if (sku) return { ...searchToAnalysis(sku), productName: row.name };
            return identityAnalysis(row.name, "");
          });
          const firstMatched =
            analyses.find(row => row.matched) || analyses[idx];
          const company = firstMatched?.companyName || "";
          const withCompany = analyses.map(row => ({
            ...row,
            companyName: row.companyName || company,
          }));
          for (const res of [
            ...classResults.values(),
            ...skuResults.values(),
          ]) {
            if (res.robot_submission_id) {
              submissionIdRef.current = res.robot_submission_id;
              break;
            }
          }
          const activeRow = withCompany[idx] || withCompany[0];
          setPortfolio(withCompany);
          setCompanyName(company);
          setActiveIdx(idx);
          setExpandedJob(
            pickSelectedJobKey(activeRow?.jobs || [], saved.selectedJobKey)
          );
          applyCheckedKeys(activeRow?.jobs || [], saved.checkedJobKeys);
          setRailTab("jobs");
          setStage("jobs");
          return;
        }
        const profile = await fetchRobotProfile({
          url: saved.url,
          product,
          timeoutMs: ROBOT_PROFILE_TIMEOUT_MS,
        });
        submissionIdRef.current =
          profile.robot_submission_id ?? submissionIdRef.current;
        const a = profileToAnalysis(profile);
        const analyses = stubs.map((row, i) =>
          i === idx ? a : { ...row, companyName: a.companyName }
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
        submissionIdRef.current =
          res.robot_submission_id ?? submissionIdRef.current;
        const a = searchToAnalysis(res);
        setPortfolio([a]);
        setActiveIdx(0);
        setExpandedJob(pickSelectedJobKey(a.jobs, saved.selectedJobKey));
        applyCheckedKeys(a.jobs, saved.checkedJobKeys);
        setRailTab("jobs");
        setStage("jobs");
        return;
      }
      const profile = await fetchRobotProfile({
        url: saved.url,
        product,
        timeoutMs: ROBOT_PROFILE_TIMEOUT_MS,
      });
      submissionIdRef.current =
        profile.robot_submission_id ?? submissionIdRef.current;
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
    e.stopPropagation();
    startJobs();
  }

  function startJobs() {
    const field = document.getElementById(
      "robot-url"
    ) as HTMLInputElement | null;
    field?.scrollIntoView({ behavior: "smooth", block: "center" });
    field?.focus();
    const u = (field?.value || url).trim();
    if (
      !canStartFindSubmit({
        url: u,
        inFlight: findInFlightRef.current,
        stage,
        currentUrl: submittedUrlRef.current,
      })
    ) {
      return;
    }
    setUrl(u);
    findInFlightRef.current = true;
    void submitFind(u);
  }

  async function submitKnownSku(sku: CatalogSku) {
    const submitUrl = sku.findUrl;
    if (
      !canStartFindSubmit({
        url: submitUrl,
        inFlight: findInFlightRef.current,
        stage,
        currentUrl: submittedUrlRef.current,
      })
    ) {
      return;
    }
    setUrl(submitUrl);
    findInFlightRef.current = true;
    setError(null);
    const research = bindSubmittedRobot(submitUrl);
    const ac = research.controller;
    setResearchPhase("jobs");
    setStage("research");
    setCompanyName(sku.vendorName);
    const live = () => stillThisSubmit(submitUrl, research);
    const cls = configurationClassForLookup(sku.displayClass);
    try {
      const res = await fetchRobotJobSearch({
        url: submitUrl,
        product: sku.name,
        assertedClass: cls || undefined,
        lookupGrain: skuLookupGrain(sku.displayClass),
        signal: ac.signal,
        timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
      });
      if (!live()) return;
      submissionIdRef.current =
        res.robot_submission_id ?? submissionIdRef.current;
      const analysis = analysisForSelectedSku(res, sku.name, sku.displayClass);
      openJobsFromAnalyses([analysis], submitUrl, [sku.name], research);
    } catch (err) {
      if (!live()) return;
      ensureFindStayVisit();
      setError(
        findResearchFailureMessage(err, "Research failed for that robot.")
      );
      setStage("find");
    } finally {
      if (live()) findInFlightRef.current = false;
    }
  }

  async function submitClassFind(classId: string) {
    const chosen = classId.trim();
    if (
      !canStartClassFindSubmit({
        assertedClass: chosen,
        inFlight: findInFlightRef.current,
      })
    ) {
      return;
    }
    findInFlightRef.current = true;
    setError(null);
    setMatchError(null);
    setResearchPhase("jobs");
    setStage("research");
    setCompanyName(robotClassTitle(chosen));
    try {
      const res = await fetchRobotJobSearch({
        assertedClass: chosen,
        lookupGrain: "robot_type",
        timeoutMs: ROBOT_JOB_SEARCH_TIMEOUT_MS,
      });
      const analysis = typeMatchToAnalysis(
        res,
        robotClassTitle(chosen),
        chosen
      );
      const checks = defaultCheckedJobKeys(analysis.jobs);
      setPortfolio([analysis]);
      setActiveIdx(0);
      setLineupPreview(false);
      setRailTab("jobs");
      setExpandedJob(pickSelectedJobKey(analysis.jobs, null));
      setCheckedJobKeys(checks);
      setStage("jobs");
    } catch {
      if (!findInFlightRef.current) return;
      ensureFindStayVisit();
      setError("Could not find jobs for that robot type. Try again.");
      setStage("find");
    } finally {
      findInFlightRef.current = false;
    }
  }

  function toggleProduct(name: string) {
    setSelected(prev => {
      if (prev.includes(name)) return prev.filter(n => n !== name);
      if (prev.length >= productCap) return prev;
      return [...prev, name];
    });
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
      writeCrmHandoff(next);
      const pool = crmPool().filter(job => next.includes(job.job_key));
      void persistKeptJobs(pool);
      return next;
    });
  }

  function runOneRobot() {
    setLineupPreview(false);
    if (products.length > 1) {
      setStage("select");
      return;
    }
    if (portfolio.length > 1) {
      setStage("portfolio");
    }
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

  function openProfileStep() {
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
  }

  function openJobsStep() {
    if (stage === "select") {
      if (selected.length > 0) {
        void confirmSelection(selected);
        return;
      }
      const segs = lineupSegments(products);
      if (usesLineupSegments(products, productCap) && segs[0]) {
        void confirmSelection(searchNamesForSegment(segs[0], productCap));
        return;
      }
      void confirmSelection("all");
      return;
    }
    if (stage === "portfolio") {
      const idx = portfolio.findIndex(
        row => row.matched && (row.jobs || []).length > 0
      );
      void researchPortfolioRobot(idx >= 0 ? idx : 0, "jobs");
      return;
    }
    if (active?.matched) {
      goToJobs(activeIdx);
      return;
    }
    void findJobsForActive();
  }

  const processCurrent = jobsProcessStepFromStage(stage);
  const processOnFind =
    stage === "select"
      ? newRobot
      : stage === "find" || stage === "research"
        ? () => window.scrollTo({ top: 0, behavior: "smooth" })
        : openProfileStep;
  const processOnJobs =
    stage === "jobs" || stage === "portfolio"
      ? () =>
          document
            .getElementById("jobs-list")
            ?.scrollIntoView({ behavior: "smooth" })
      : stage === "research"
        ? undefined
        : stage === "find"
          ? startJobs
          : openJobsStep;
  const processOnActivate = goToActivate;
  const processActionLabel = jobsProcessActionLabel(processCurrent);
  const processActionClass = jobsProcessActionClass(processCurrent);
  const processOnAction =
    processCurrent === "jobs"
      ? goToActivate
      : stage === "research"
        ? undefined
        : stage === "find"
          ? startJobs
          : openJobsStep;

  /* -------------------------------------------------------------- */
  /* Render                                                          */
  /* -------------------------------------------------------------- */

  return (
    <div className="rfr-jobs-page-shell border border-slate-600 bg-[#0b162f]">
      <div className="sticky top-14 z-[60] border-b border-slate-600 bg-[#0b162f]">
        <JobsProcessNav
          layout="page"
          current={processCurrent}
          onFind={processOnFind}
          onJobs={processOnJobs}
          onActivate={processOnActivate}
          actionLabel={processActionLabel}
          actionClassName={processActionClass}
          onAction={processOnAction}
        />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.34fr)_minmax(0,0.66fr)]">
        {/* ---------------- LEFT RAIL (context) ---------------- */}
        <aside className="rfr-find-pane min-w-0 overflow-x-clip border-b border-slate-600 p-5 sm:p-6 lg:border-b-0 lg:border-r">
          {stage === "find" || stage === "research" || stage === "select" ? (
            <FindRail
              stage={stage}
              url={url}
              setUrl={setUrl}
              onSubmit={onSubmitFind}
              companyName={companyName}
              error={error}
              currentSubmitUrl={submittedUrlRef.current}
              onCancel={stage === "select" ? newRobot : undefined}
              onPickClass={id => void submitClassFind(id)}
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
              identityVerified={
                active ? companyIdentity(active).verified : true
              }
              product={
                portfolio.length > 1
                  ? `${portfolio.length} robots`
                  : active?.productName || ""
              }
              tier={active?.tier || "C"}
              matched={Boolean(active?.matched)}
              showCount={showActiveCount}
              jobCount={Math.min(JOBS_EXAMPLE_CAP, active?.jobs?.length || 0)}
              hint={
                railTab === "profile"
                  ? RAIL_STEP_HINT.profile
                  : RAIL_STEP_HINT.jobs
              }
              portfolioCount={portfolio.length}
              onBackToPortfolio={
                portfolio.length > 1 ? () => setStage("portfolio") : undefined
              }
              onNewRobot={newRobot}
            />
          )}
        </aside>

        {/* ---------------- LARGE WORKSPACE ---------------- */}
        <section className="rfr-find-pane min-w-0">
          {stage === "find" && (
            <div>
              <div className="rfr-jobs-start-bar border-b border-slate-600 px-6 py-4">
                <button
                  type="button"
                  onClick={startJobs}
                  className={`${ctaClass} w-full sm:w-auto`}
                >
                  <FaceCue scale={2} onEmerald />
                  {FIND_JOBS_CTA}
                </button>
                <p className="mt-2 text-[12px] text-slate-400">
                  Paste a robot URL on the left, then find jobs.
                </p>
              </div>
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
            </div>
          )}

          {stage === "research" && (
            <ResearchPanel company={companyName} phase={researchPhase} />
          )}

          {stage === "select" && (
            <SelectPanel
              company={companyName}
              products={products}
              selected={selected}
              productCap={productCap}
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
              onSeeJobs={() => {
                const idx = portfolio.findIndex(
                  row => row.matched && (row.jobs || []).length > 0
                );
                void researchPortfolioRobot(idx >= 0 ? idx : 0, "jobs");
              }}
              onActivate={goToActivate}
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
              lineup={portfolio}
              lineupPreview={lineupPreview}
              expandedJob={expandedJob}
              checkedJobKeys={checkedJobKeys}
              showAll={showAllJobs}
              onSelectJob={selectJob}
              onToggleJob={toggleCheckedJob}
              onActivate={goToActivate}
              keepSavedCount={keepSavedCount}
              signedIn={Boolean(session)}
              plan={plan}
              accessToken={session?.access_token || null}
              robotUrl={submittedUrlRef.current}
              submissionId={submissionIdRef.current}
              onSeeAll={seeAllJobs}
              onRunOneRobot={runOneRobot}
              robotCount={lineupPreview ? portfolio.length : 1}
              companyName={companyName || active.companyName}
              qualifying={matching}
              matchError={matchError}
              onSelectClass={id => void qualifyActive(id)}
            />
          )}
        </section>
      </div>
      <div className="relative z-[60] mt-6">
        <JobsPstackProtocol />
      </div>
      <div className="rfr-jobs-page-footer relative z-[60] pointer-events-auto border-t border-slate-600 bg-[#0b162f]">
        <JobsProcessNav
          layout="page"
          current={processCurrent}
          onFind={processOnFind}
          onJobs={processOnJobs}
          onActivate={processOnActivate}
          actionLabel={processActionLabel}
          actionClassName={processActionClass}
          onAction={processOnAction}
        />
      </div>
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
  currentSubmitUrl,
  onCancel,
  onPickClass,
}: {
  stage: Stage;
  url: string;
  setUrl: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  companyName: string;
  error: string | null;
  currentSubmitUrl?: string;
  onCancel?: () => void;
  onPickClass?: (classId: string) => void;
}) {
  const researching = stage === "research";
  const sameSubmit =
    researching &&
    Boolean(url.trim()) &&
    sameRobotUrl(url, currentSubmitUrl || "");
  const [catalogClass, setCatalogClass] = useState("");
  const classChoices = classOptionsOrDefault();
  return (
    <div>
      <p className={eyebrow}>
        {researching || stage === "select" ? "Your robot" : "Find jobs"}
      </p>
      <h1 className={FIND_JOBS_HEADLINE_CLASS}>
        {stage === "select"
          ? companyName || "Select a robot"
          : researching
            ? companyName || "Researching…"
            : FIND_JOBS_HOME_HEADLINE.split(/(Jobs)/).map((part, i) =>
                part === "Jobs" ? (
                  <span key={i} className={FIND_JOBS_HEADLINE_ACCENT_CLASS}>
                    {part}
                  </span>
                ) : (
                  part
                )
              )}
      </h1>
      {stage === "find" && (
        <p className={FIND_JOBS_SUBHEAD_CLASS}>{FIND_JOBS_HOME_SUBHEAD}</p>
      )}

      <form
        aria-label="Find jobs for your robot"
        onSubmit={onSubmit}
        className="mt-6"
      >
        <label className={eyebrow} htmlFor="robot-url">
          Robot product URL
        </label>
        <input
          id="robot-url"
          type="text"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste robot product URL"
          disabled={stage === "select"}
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 font-mono text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={stage === "select" || !url.trim() || sameSubmit}
          className={`${ctaClass} mt-3 w-full`}
        >
          {researching ? "Researching…" : FIND_JOBS_CTA}
        </button>
      </form>

      {stage === "find" && onPickClass ? (
        <div className="mt-8 border-2 border-emerald-400 bg-emerald-400/20 p-4 shadow-[0_0_28px_rgba(46,230,168,0.35)]">
          <label
            htmlFor="robot-type"
            className="font-display text-xl font-bold tracking-tight text-emerald-200 sm:text-2xl"
          >
            {I_KNOW_THE_ROBOT_LABEL}
          </label>
          <p className="mt-2 text-[13px] leading-snug text-emerald-100/80">
            {I_KNOW_THE_ROBOT_HINT}
          </p>
          <select
            id="robot-type"
            aria-label={I_KNOW_THE_ROBOT_LABEL}
            value={catalogClass}
            onChange={e => setCatalogClass(e.target.value)}
            className="mt-3 w-full border border-emerald-500/40 bg-[#081126] px-3 py-3 text-[13px] text-slate-100 outline-none focus:border-emerald-300"
          >
            <option value="">Select a type</option>
            {classChoices.map(opt => (
              <option key={opt.id} value={opt.id} data-jobs-class={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={!catalogClass}
            onClick={() => onPickClass(catalogClass)}
            className={`${ctaClass} mt-3 w-full`}
          >
            {FIND_JOBS_CTA}
          </button>
        </div>
      ) : null}

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
    <div>
      <p className={eyebrow}>Portfolio</p>
      <h2 className={FIND_JOBS_HEADLINE_CLASS}>{company}</h2>
      {!identityVerified ? (
        <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-amber-300/80">
          Company identity not fully verified
        </p>
      ) : null}
      <p className="mt-0.5 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300">
        {count} robots
      </p>
      <p className="mt-3 text-[12px] leading-snug text-slate-400">
        Pick one robot for that product, or continue to jobs for the lineup.
      </p>
      <div className="mt-6">
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
  onBackToPortfolio?: () => void;
  onNewRobot: () => void;
}) {
  return (
    <div>
      <p className={eyebrow}>Your robot</p>
      <h2 className={FIND_JOBS_HEADLINE_CLASS}>{product}</h2>
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
        {matched && showCount ? (
          <span className="ml-2 font-mono text-[11px] font-bold text-emerald-300">
            {jobCount} EXAMPLE JOBS
          </span>
        ) : null}
      </div>

      <p className="mt-4 text-[12px] leading-snug text-slate-400">{hint}</p>

      <div className="mt-6 space-y-1">
        {onBackToPortfolio ? (
          <button
            type="button"
            onClick={onBackToPortfolio}
            className={JOBS_RAIL_LINK_CLASS}
          >
            ← All {portfolioCount} robots
          </button>
        ) : null}
        <button
          type="button"
          onClick={onNewRobot}
          className={JOBS_RAIL_LINK_CLASS}
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

function ResearchPanel({
  company,
  phase,
}: {
  company: string;
  phase: ResearchPhase;
}) {
  const steps = [
    {
      n: "01",
      label: "Identify company",
      state: phase === "identity" ? "active" : "done",
    },
    {
      n: "02",
      label: "Find robots",
      state: phase === "identity" ? "pending" : "done",
    },
    {
      n: "03",
      label: "Find matching jobs",
      state: phase === "jobs" ? "active" : "pending",
    },
  ] as const;
  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Researching your robot</p>
      <h2 className={FIND_JOBS_HEADLINE_CLASS}>
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
              className={`font-mono text-sm ${
                s.state === "done"
                  ? "text-emerald-400"
                  : s.state === "active"
                    ? "text-amber-300"
                    : "text-slate-600"
              }`}
            >
              {s.state === "done" ? "✓" : s.state === "active" ? "→" : "·"}
            </span>
          </li>
        ))}
      </ul>
      <div className="mt-8 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-slate-500">
        <span className="rfr-led animate-pulse" />
        {phase === "identity"
          ? "Reading the product page…"
          : "Matching jobs to this robot…"}
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
  productCap,
  onToggle,
  onConfirm,
}: {
  company: string;
  products: ProductChoice[];
  selected: string[];
  productCap: number;
  onToggle: (name: string) => void;
  onConfirm: (which: string[] | "all") => void;
}) {
  const [lineupPage, setLineupPage] = useState(0);
  const segments = lineupSegments(products);
  const grouped = usesLineupSegments(products, productCap);
  const pageSize = JOBS_LINEUP_DISPLAY_CAP;
  const pageCount = Math.max(1, Math.ceil(products.length / pageSize));
  const safePage = Math.min(lineupPage, pageCount - 1);
  const visible = pageJobsLineup(products, safePage, pageSize);
  const defaultNames = products.slice(0, productCap).map(p => p.name);
  const startNames =
    selected.length > 0 ? selected.slice(0, productCap) : defaultNames;
  const paidHint =
    productCap <= JOBS_PRODUCT_CAP_FREE
      ? `Each pass searches up to ${productCap} robots. Pro searches ${JOBS_PRODUCT_CAP_PAID}.`
      : `Each pass searches up to ${productCap} robots.`;
  const from = safePage * pageSize + 1;
  const to = Math.min(products.length, (safePage + 1) * pageSize);

  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Select robot</p>
      <h2 className={FIND_JOBS_HEADLINE_CLASS}>
        {grouped
          ? `${products.length} robots in ${segments.length} groups`
          : `We found ${products.length} robots`}
      </h2>
      <p className="mt-2 text-sm text-slate-400">
        {grouped
          ? `Run one family — one job search for that class, not a crawl of every SKU. ${company || "This maker"} has ${products.length}. ${paidHint}`
          : `Pick up to ${productCap} robots this pass. ${company || "This maker"} has ${products.length} named robot${products.length === 1 ? "" : "s"} — names first, then a short description if we have one.`}
      </p>

      {grouped ? (
        <div className="mt-6 space-y-3">
          {segments.map(seg => {
            const names = searchNamesForSegment(seg, productCap);
            const extra = seg.products.length - names.length;
            return (
              <div
                key={seg.id}
                className="border border-slate-600 bg-[#081126] p-4"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <h3 className="font-display text-lg font-bold text-slate-100">
                      {seg.title}
                    </h3>
                    <p className="mt-0.5 text-sm text-slate-400">
                      {seg.subtitle}
                    </p>
                    {extra > 0 ? (
                      <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.08em] text-slate-500">
                        Searching {names.length} of {seg.products.length} this
                        pass
                      </p>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    onClick={() => onConfirm(names)}
                    className="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-300 transition hover:text-emerald-200"
                  >
                    Find jobs for {seg.title} →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {grouped ? (
        <p className="mt-8 font-mono text-[11px] uppercase tracking-[0.12em] text-slate-500">
          Or pick up to {productCap} SKUs
        </p>
      ) : null}

      <div className={`${grouped ? "mt-3" : "mt-6"} grid gap-2 sm:grid-cols-2`}>
        {visible.map(p => {
          const on = selected.includes(p.name);
          const blocked = !on && selected.length >= productCap;
          return (
            <button
              key={p.name}
              type="button"
              onClick={() => onToggle(p.name)}
              disabled={blocked}
              className={`flex items-center justify-between border px-4 py-3 text-left transition ${
                on
                  ? "border-emerald-400 bg-emerald-400/10"
                  : blocked
                    ? "cursor-not-allowed border-slate-800 bg-[#081126] opacity-50"
                    : "border-slate-600 bg-[#081126] hover:border-emerald-500/40"
              }`}
            >
              <span>
                <span className="block text-sm font-bold text-slate-100">
                  {p.name}
                </span>
                {p.displayClass ? (
                  <span className="mt-0.5 block font-mono text-sm uppercase tracking-[0.08em] text-slate-400">
                    {p.displayClass.replace(/_/g, " ")}
                  </span>
                ) : null}
                {p.description ? (
                  <span className="mt-1 block text-xs leading-snug text-slate-500">
                    {p.description}
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
      {pageCount > 1 ? (
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-slate-500">
            Showing {from}–{to} of {products.length}
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              disabled={safePage <= 0}
              onClick={() => setLineupPage(p => Math.max(0, p - 1))}
              className="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 transition hover:text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Previous 3
            </button>
            <button
              type="button"
              disabled={safePage >= pageCount - 1}
              onClick={() => setLineupPage(p => Math.min(pageCount - 1, p + 1))}
              className="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-300 transition hover:text-emerald-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next 3 →
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-6">
        <button
          type="button"
          onClick={() =>
            onConfirm(
              grouped && selected.length === 0
                ? searchNamesForSegment(segments[0], productCap)
                : startNames
            )
          }
          className={ctaClass}
        >
          <FaceCue scale={2} onEmerald />
          {selected.length === 1
            ? `Find jobs for ${selected[0]} →`
            : grouped && selected.length === 0 && segments[0]
              ? `Find jobs for ${segments[0].title} →`
              : startNames.length === 1
                ? `Find jobs for ${startNames[0]} →`
                : products.length <= productCap && selected.length === 0
                  ? `Find jobs for all ${products.length} robots →`
                  : `Find jobs for ${startNames.length} robots →`}
        </button>
        {!grouped &&
        selected.length > 0 &&
        selected.length < Math.min(products.length, productCap) ? (
          <button
            type="button"
            onClick={() => onConfirm("all")}
            className="mt-3 block font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 transition hover:text-slate-300"
          >
            or first {Math.min(products.length, productCap)} robots
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
  onSeeJobs,
  onActivate,
}: {
  company: string;
  robots: RobotAnalysis[];
  showCounts: boolean;
  onView: (idx: number) => void;
  onReview: (idx: number) => void;
  onSeeJobs: () => void;
  onActivate: () => void;
}) {
  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>{company}</p>
      <h2 className={FIND_JOBS_HEADLINE_CLASS}>{robots.length} robots</h2>
      <p className="mt-2 max-w-xl text-sm text-slate-400">
        Pick one robot for jobs for that product, or continue to jobs for the
        lineup.
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
      <div className="mt-6 flex flex-wrap gap-3">
        <button type="button" onClick={onSeeJobs} className={ctaClass}>
          <FaceCue scale={2} onEmerald />
          {JOBS_SEE_JOBS_CTA}
        </button>
        <button
          type="button"
          onClick={onActivate}
          className="inline-flex items-center justify-center gap-2 border border-emerald-500/50 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-emerald-300 transition hover:border-emerald-400"
        >
          {JOBS_NEXT_CTA}
        </button>
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
        <h2 className={FIND_JOBS_HEADLINE_CLASS}>{analysis.productName}</h2>
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
        {profileConfidenceCopy(analysis.tier, {
          emptyResearch: sources.length === 0 && confirmed.length === 0,
        })}
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
  return shouldShowClassPicker(analysis);
}

function JobsActivateBar({
  onActivate,
  checkedCount,
  className = "",
}: {
  onActivate: () => void;
  checkedCount: number;
  className?: string;
}) {
  return (
    <div className={`rfr-jobs-activate-bar ${className}`.trim()}>
      <button
        type="button"
        onClick={onActivate}
        className={`${ctaClass} w-full sm:w-auto`}
      >
        <FaceCue scale={2} onEmerald />
        {JOBS_NEXT_CTA}
      </button>
      <p className="mt-2 text-sm leading-snug text-slate-300">
        {checkedCount} selected. {JOBS_NEXT_HINT}.
      </p>
    </div>
  );
}

function JobsPanel({
  analysis,
  lineup,
  lineupPreview,
  expandedJob,
  checkedJobKeys,
  showAll,
  onSelectJob,
  onToggleJob,
  onActivate,
  keepSavedCount = 0,
  signedIn = false,
  plan = "anonymous",
  accessToken = null,
  robotUrl = "",
  submissionId = null,
  onSeeAll,
  onRunOneRobot,
  robotCount = 1,
  companyName = "",
  qualifying = false,
  matchError = null,
  onSelectClass,
}: {
  analysis: RobotAnalysis;
  lineup: RobotAnalysis[];
  lineupPreview: boolean;
  expandedJob: string | null;
  checkedJobKeys: string[];
  showAll: boolean;
  onSelectJob: (job: MatchJob) => void;
  onToggleJob: (job: MatchJob) => void;
  onActivate: () => void;
  keepSavedCount?: number;
  signedIn?: boolean;
  plan?: string;
  accessToken?: string | null;
  robotUrl?: string;
  submissionId?: number | null;
  onSeeAll: () => void;
  onRunOneRobot: () => void;
  robotCount?: number;
  companyName?: string;
  qualifying?: boolean;
  matchError?: string | null;
  onSelectClass: (classId: string) => void;
}) {
  const sources = lineupPreview && lineup.length > 1 ? lineup : [analysis];
  const tagged = exampleJobsForLineup(sources);
  const baseJobs = analysis.jobs;
  const visible =
    !lineupPreview && showAll
      ? baseJobs.slice(0, JOBS_PIPELINE_CAP).map(job => ({
          ...job,
          forRobot: analysis.productName,
        }))
      : tagged;
  const hiddenCount = lineupPreview
    ? 0
    : Math.max(0, Math.min(baseJobs.length, JOBS_PIPELINE_CAP) - tagged.length);
  const heading = jobsHeading({
    productName: analysis.productName,
    companyName: companyName || analysis.companyName,
    robotCount,
    lookupGrain: analysis.lookupGrain,
    robotClass: analysis.robotClass,
  });
  const checkedCount = checkedJobKeys.filter(k =>
    visible.some(job => job.job_key === k)
  ).length;
  const showPicker = shouldQualify(analysis);
  const showCrmCtas = !showPicker && !qualifying;

  return (
    <div id="jobs-list" className="p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className={`${FIND_JOBS_HEADLINE_CLASS} text-white`}>{heading}</h2>
        <span className="font-mono text-base font-bold text-emerald-300">
          {jobsCountEyebrow({
            visibleCount: visible.length,
            productName: analysis.productName,
            companyName: companyName || analysis.companyName,
            robotCount,
            lookupGrain: analysis.lookupGrain,
            robotClass: analysis.robotClass,
          })}
        </span>
      </div>
      {visible.length > 0 && (
        <p className="mt-2 text-base leading-relaxed text-slate-300">
          {jobsListHint({
            robotCount,
            productName: analysis.productName,
          })}{" "}
          <span className="font-semibold text-emerald-200">
            {JOBS_KEEP_LABEL} is on. Uncheck a row to skip it.
          </span>
        </p>
      )}
      {matchError ? (
        <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
          {matchError}
        </p>
      ) : null}
      <div className="mt-4 space-y-3">
        {keepSavedCount > 0 ? (
          <JobsKeepStatusBar
            savedCount={keepSavedCount}
            onCrmDesk={false}
            signedIn={signedIn}
            submissionId={submissionId}
          />
        ) : null}
      </div>
      {showCrmCtas ? (
        <JobsActivateBar
          onActivate={onActivate}
          checkedCount={checkedCount}
          className="mt-4"
        />
      ) : null}
      {lineupPreview ? (
        <button
          type="button"
          onClick={onRunOneRobot}
          className="mt-3 font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
        >
          {JOBS_RUN_ONE_ROBOT_CTA}
        </button>
      ) : null}

      {baseJobs.length === 0 && visible.length === 0 ? (
        showPicker ? (
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
            robotClass={analysis.robotClass}
          />
        )
      ) : (
        <ol className="mt-6 space-y-3">
          {visible.map((job, i) => (
            <JobCard
              key={`${job.forRobot}:${job.job_key}`}
              index={i + 1}
              job={job}
              selected={expandedJob === job.job_key}
              checked={checkedJobKeys.includes(job.job_key)}
              onSelect={() => onSelectJob(job)}
              onToggle={() => onToggleJob(job)}
            />
          ))}
        </ol>
      )}
      {hiddenCount > 0 ? (
        <button
          type="button"
          onClick={onSeeAll}
          className="mt-4 font-mono text-sm font-semibold uppercase tracking-[0.08em] text-emerald-400 hover:text-emerald-300"
        >
          See all {Math.min(baseJobs.length, JOBS_PIPELINE_CAP)} jobs
        </button>
      ) : null}
      {showCrmCtas ? (
        <JobsActivateBar
          onActivate={onActivate}
          checkedCount={checkedCount}
          className="mt-8 border-t border-slate-600 pt-6"
        />
      ) : null}
      {visible.length > 0 ? (
        <JobsPresentationOffer
          signedIn={signedIn}
          plan={plan}
          token={accessToken}
          robotUrl={robotUrl || ""}
          companyName={companyName || analysis.companyName}
          productName={analysis.productName}
        />
      ) : null}
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
  onSelect: (classId: string) => void;
}) {
  const choices = classOptionsOrDefault(options);
  return (
    <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5">
      <p className={`${JOBS_EYEBROW_CLASS} text-emerald-300`}>
        Name the robot class
      </p>
      <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
        {CLASS_PICKER_PROMPT}
      </h3>
      <p className="mt-2 text-[13px] leading-snug text-slate-300">
        Photos and the product page were not enough to name the class
        {robotName ? ` for ${robotName}` : ""}. Pick the closest match so we can
        find jobs — then we show Job Cards on Available jobs, or tell you we do
        not have jobs for that type yet.
      </p>
      {previewUrl ? (
        <img
          src={previewUrl}
          alt={`${robotName} product photo`}
          className="mt-4 max-h-40 border border-slate-700 object-contain"
        />
      ) : null}
      {busy ? (
        <p className="mt-3 font-mono text-sm font-semibold uppercase tracking-[0.08em] text-amber-300">
          Finding jobs for that robot type…
        </p>
      ) : null}
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {choices.map(opt => (
          <button
            key={opt.id}
            type="button"
            disabled={busy}
            data-jobs-class={opt.id}
            onClick={() => onSelect(opt.id)}
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
  robotClass,
}: {
  robotName: string;
  reason?: string | null;
  robotClass?: string | null;
}) {
  if (robotClass) {
    return (
      <div className="mt-6 border border-slate-600 bg-[#081126] p-5">
        <p className={JOBS_EYEBROW_CLASS}>No jobs yet</p>
        <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
          {classJobsEmptyCopy(robotClass, robotName)}
        </h3>
        <p className="mt-2 text-[13px] leading-snug text-slate-300">
          We do not have work represented for this robot type yet. This is a
          coverage gap on our side, not a limitation of the robot. CRM stays
          empty until there are jobs to keep.
        </p>
      </div>
    );
  }
  const r = (reason || "") as ZeroReason | "";
  if (r === "corpus_gap") {
    return (
      <div className="mt-6 border border-slate-600 bg-[#081126] p-5">
        <p className={JOBS_EYEBROW_CLASS}>Corpus gap</p>
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
        <p className={JOBS_EYEBROW_CLASS}>No compatible jobs</p>
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
  selected,
  checked,
  onSelect,
  onToggle,
}: {
  index: number;
  job: MatchJob;
  selected: boolean;
  checked: boolean;
  onSelect: () => void;
  onToggle: () => void;
}) {
  const card = robotJobCardFromMatch(job);
  if (!card.employer || !card.workplace) return null;
  const place = [card.employer, card.workplace].filter(Boolean).join(" · ");
  return (
    <li
      className={`border bg-[#081126] ${
        checked || selected ? "border-emerald-400/70" : "border-slate-600"
      }`}
    >
      <div className="flex items-start">
        <label
          className="flex shrink-0 cursor-pointer flex-col items-center gap-1 px-3 pt-4"
          onClick={e => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={checked}
            onChange={onToggle}
            aria-label={`${checked ? JOBS_KEEP_LABEL : JOBS_SKIP_LABEL} ${card.jobTitle} on the CRM desk`}
            className="h-5 w-5 accent-emerald-400"
          />
          <span
            className={`font-mono text-xs font-bold uppercase tracking-[0.08em] ${
              checked ? "text-emerald-300" : "text-slate-500"
            }`}
          >
            {checked ? JOBS_KEEP_LABEL : JOBS_SKIP_LABEL}
          </span>
        </label>
        <button
          type="button"
          onClick={onSelect}
          className="flex min-w-0 flex-1 items-start gap-3 py-4 pr-4 text-left"
        >
          <span className="flex-1">
            <span className={JOBS_ROBOT_NAME_CLASS}>{card.jobTitle}</span>
            {place ? <span className={JOBS_PLACE_CLASS}>{place}</span> : null}
            <span className={JOBS_META_CLASS}>
              {jobIndexLabel(index)} · {card.qualificationLabel}
            </span>
            {card.modelContract?.listLine ? (
              <span className={JOBS_PLACE_CLASS}>
                {card.modelContract.listLine}
              </span>
            ) : null}
          </span>
          <span className="font-mono text-xs text-slate-500">
            {selected ? "−" : "+"}
          </span>
        </button>
      </div>

      {selected && (
        <div className="border-t border-slate-700 px-4 pb-4 pt-3">
          <dl className="grid gap-2 text-[13px] leading-snug text-slate-200">
            <div>
              <dt className={eyebrow}>Employer</dt>
              <dd className="mt-0.5">{card.employer}</dd>
            </div>
            <div>
              <dt className={eyebrow}>Workplace</dt>
              <dd className="mt-0.5">{card.workplace}</dd>
            </div>
            <div>
              <dt className={eyebrow}>Work being performed</dt>
              <dd className="mt-0.5">{card.work}</dd>
            </div>
            {card.description ? (
              <div>
                <dt className={eyebrow}>Job description</dt>
                <dd className="mt-0.5 text-slate-300">{card.description}</dd>
              </div>
            ) : null}
            <div>
              <dt className={eyebrow}>{card.payEstimate.heading}</dt>
              <dd className="mt-0.5">
                <span className="text-emerald-300">
                  {card.payEstimate.monthlyLabel}
                </span>
                {" · "}
                <span className="text-emerald-300">
                  {card.payEstimate.annualLabel}
                </span>
                <span className="mt-0.5 block text-slate-400">
                  {card.payEstimate.disclaimer}
                </span>
              </dd>
            </div>
            <div>
              <dt className={eyebrow}>{card.qualificationLabel}</dt>
              <dd className="mt-0.5 text-slate-300">
                {card.qualificationHint}
              </dd>
            </div>
          </dl>

          {card.taskModels.length || card.modelLinks.length ? (
            <div className="mt-3">
              <p className={eyebrow}>Task models</p>
              {card.taskModels.length ? (
                <ul className="mt-1 space-y-0.5">
                  {card.taskModels.map(model => (
                    <li
                      key={model.id}
                      className="text-[13px] leading-snug text-slate-200"
                    >
                      {model.label}
                      <span className="text-slate-400">
                        {" "}
                        ·{" "}
                        {model.presence === "unknown"
                          ? "Not yet confirmed"
                          : model.presence === "present"
                            ? "Present"
                            : "Absent"}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
              {card.modelContract ? (
                <div className="mt-2 space-y-0.5 text-[13px] leading-snug text-slate-300">
                  <p className="text-slate-200">
                    {card.modelContract.headline}
                  </p>
                  {card.modelContract.steps.length ? (
                    <ol className="mt-1 space-y-1">
                      {card.modelContract.steps.map(step => (
                        <li key={`${step.n}-${step.label}`}>
                          <span className="font-mono text-emerald-400">
                            {step.n}.
                          </span>{" "}
                          <span className="text-slate-200">{step.label}.</span>{" "}
                          {step.body}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <>
                      {card.modelContract.layer ? (
                        <p>{card.modelContract.layer}</p>
                      ) : null}
                      {card.modelContract.whoTrains ? (
                        <p>{card.modelContract.whoTrains}</p>
                      ) : null}
                      {card.modelContract.time ? (
                        <p>{card.modelContract.time}</p>
                      ) : null}
                      {card.modelContract.youProvide ? (
                        <p>{card.modelContract.youProvide}</p>
                      ) : null}
                      {card.modelContract.fieldFeedback ? (
                        <p className="text-slate-400">
                          {card.modelContract.fieldFeedback}
                        </p>
                      ) : null}
                    </>
                  )}
                </div>
              ) : null}
              {card.modelLinks.length ? (
                <ul className="mt-1 space-y-0.5">
                  {card.modelLinks.map(dest => (
                    <li key={dest.url || dest.name}>
                      {dest.url ? (
                        <a
                          href={dest.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[13px] leading-snug text-slate-300 underline decoration-slate-600 underline-offset-2"
                        >
                          {dest.name}
                        </a>
                      ) : (
                        dest.name
                      )}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}

          {card.requirements.length ? (
            <div className="mt-3">
              <p className={eyebrow}>Why this is listed</p>
              <ul className="mt-1 space-y-0.5">
                {card.requirements.map(w => (
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

          {job.blockers?.length ? (
            <div className="mt-3">
              <p className="mt-3 font-mono text-sm font-semibold uppercase tracking-[0.08em] text-rose-400/80">
                Not qualified
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
          ) : null}

          <p className="mt-3 text-sm text-slate-400">
            Next step: {card.nextStep}
          </p>
        </div>
      )}
    </li>
  );
}
