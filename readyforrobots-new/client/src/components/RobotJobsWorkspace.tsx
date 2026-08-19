/**
 * RobotJobsWorkspace — the ReadyForRobots work terminal (front door `/`).
 *
 * Left = robot / context / navigation. Right = work. One deliberate state at
 * a time (submit-stability principle):
 *
 *   FIND → RESEARCH → SELECT → REVIEW PROFILE → JOBS
 *
 * Three separated objects:
 *   ROBOT  — what did we understand?      (REVIEW PROFILE, pre-match)
 *   MATCH  — what work looks compatible?  (JOBS, produced only when asked)
 *   JOB    — should we pursue this one?   (QUALIFY)
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
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
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
import type { MatchCapability, MatchJob } from "@/lib/robotJobMatch";
import LiveJobTape from "@/components/jobs/LiveJobTape";
import { MARKET_TAPE_JOBS } from "@/lib/jobsTapeCorpus";

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
};

type ZeroReason =
  | "insufficient_profile_evidence"
  | "no_compatible_jobs"
  | "corpus_gap";

type ProductChoice = { name: string; displayClass?: string | null };
type RestoreView = "review" | "jobs" | "portfolio";

const PREVIEW_FREE = 5;
const TOP_SHOWN = 12;
const MARKET_FOUND_BASE = 140;
const WORKSPACE_SESSION_KEY = "rfr_jobs_workspace";

const eyebrow =
  "font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500";
const ctaClass =
  "inline-flex items-center justify-center gap-2 bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-45";

/* ------------------------------------------------------------------ */
/* Session persistence (signup continuity)                             */
/* ------------------------------------------------------------------ */

type WorkspaceSession = {
  url: string;
  products: string[];
  view: RestoreView;
  activeIdx?: number;
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
    const parsed = JSON.parse(raw) as WorkspaceSession;
    if (!parsed?.url) return null;
    return parsed;
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

/** Profile-only analysis — matching has not happened yet. */
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

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function RobotJobsWorkspace() {
  const { session } = useAuth();
  const unlocked = Boolean(session);

  // On reload / auth return, start in the research state when a workspace session
  // exists — restore() (mount effect) rebuilds it. Avoids a flash of the FIND +
  // live-tape screen before the researched robot is restored.
  const [stage, setStage] = useState<Stage>(() =>
    readWorkspaceSession()?.url ? "research" : "find"
  );
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

  /* Restore the researched robot on reload OR auth return (signup continuity).
     Runs once on mount for everyone — not just logged-in users — so a page
     reload no longer drops the user back to an empty FIND screen. */
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    const saved = readWorkspaceSession();
    if (saved?.url) {
      void restore(saved);
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
    } catch {
      setError("Research failed. Check the URL and try again.");
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

    // Portfolio — each robot independently requirement-matched before we show it.
    setStage("research");
    try {
      const results = await Promise.all(
        names.map(name =>
          fetchRobotJobSearch({ url: submitUrl, product: name }).catch(
            () => null
          )
        )
      );
      const validResults = results.filter(
        (r): r is RobotJobSearchResult => Boolean(r)
      );
      submissionIdRef.current =
        validResults.find(r => r.robot_submission_id)?.robot_submission_id ??
        submissionIdRef.current;
      const analyses = validResults.map(searchToAnalysis);
      if (analyses.length === 0) {
        setError("We could not research those robots.");
        setStage("select");
        return;
      }
      if (analyses.length === 1) {
        enterReviewMatched(analyses[0], submitUrl);
        return;
      }
      setPortfolio(analyses);
      setActiveIdx(0);
      saveWorkspaceSession({
        url: submitUrl,
        products: analyses.map(a => a.productName),
        view: "portfolio",
        activeIdx: 0,
      });
      trackRobotJobsFunnel("capabilities_viewed", {
        ...funnelBase(),
        robots_analyzed: analyses.length,
        company_name: analyses[0]?.companyName,
      });
      setStage("portfolio");
    } catch {
      setError("Portfolio research failed.");
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
    setPortfolio([analysis]);
    setActiveIdx(0);
    setRailTab("profile");
    setExpandedJob(null);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    saveWorkspaceSession({
      url: submitUrl,
      products: productNames.filter(Boolean),
      view: "review",
      activeIdx: 0,
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

  function revealJobs(a: RobotAnalysis) {
    setRailTab("jobs");
    setExpandedJob(a.jobs[0]?.job_key ?? null);
    setStage("jobs");
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a.productName,
      job_count: a.jobCount,
    });
  }

  function goToJobs(idx: number) {
    setActiveIdx(idx);
    const a = portfolio[idx];
    setRailTab("jobs");
    setExpandedJob(a?.jobs[0]?.job_key ?? null);
    setStage("jobs");
    saveWorkspaceSession({
      url: submittedUrlRef.current,
      products: portfolio.map(p => p.productName),
      view: "jobs",
      activeIdx: idx,
    });
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: a?.productName,
      job_count: a?.jobCount,
    });
  }

  async function restore(saved: WorkspaceSession) {
    submittedUrlRef.current = saved.url;
    const savedIdx = typeof saved.activeIdx === "number" ? saved.activeIdx : 0;
    try {
      // Multi-robot portfolio — rebuild every robot and return to the exact one
      // the user was on before signup (not always robot 0).
      if (saved.products.length > 1) {
        const results = await Promise.all(
          saved.products.map(name =>
            fetchRobotJobSearch({ url: saved.url, product: name }).catch(
              () => null
            )
          )
        );
        const validResults = results.filter(
          (r): r is RobotJobSearchResult => Boolean(r)
        );
        submissionIdRef.current =
          validResults.find(r => r.robot_submission_id)?.robot_submission_id ??
          submissionIdRef.current;
        const analyses = validResults.map(searchToAnalysis);
        if (analyses.length > 1) {
          const idx =
            savedIdx >= 0 && savedIdx < analyses.length ? savedIdx : 0;
          setPortfolio(analyses);
          setCompanyName(analyses[0].companyName);
          setActiveIdx(idx);
          if (saved.view === "jobs") {
            setRailTab("jobs");
            setExpandedJob(analyses[idx].jobs[0]?.job_key ?? null);
            setStage("jobs");
          } else if (saved.view === "review") {
            setRailTab("profile");
            setStage("review");
          } else {
            setStage("portfolio");
          }
          return;
        }
      }
      const product = saved.products[0] || undefined;
      if (saved.view === "jobs") {
        const res = await fetchRobotJobSearch({ url: saved.url, product });
        submissionIdRef.current = res.robot_submission_id ?? submissionIdRef.current;
        const a = searchToAnalysis(res);
        setPortfolio([a]);
        setActiveIdx(0);
        setRailTab("jobs");
        setExpandedJob(a.jobs[0]?.job_key ?? null);
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

  function openReviewFor(idx: number) {
    setActiveIdx(idx);
    setRailTab("profile");
    setStage("review");
    saveWorkspaceSession({
      url: submittedUrlRef.current,
      products: portfolio.map(p => p.productName),
      view: "review",
      activeIdx: idx,
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

  function toggleExpand(job: MatchJob) {
    setExpandedJob(prev => (prev === job.job_key ? null : job.job_key));
    recordJobView(job);
  }

  /** Pursue this work → bridge to the real matched-buyer pipeline (fires funnel
   *  intent then the Link navigates to /pipeline?url=<robot>). */
  function onPursue(job: MatchJob) {
    if (!active) return;
    trackRobotJobsFunnel("qualify_opened", {
      ...funnelBase(),
      job_key: job.job_key,
    });
    trackRobotJobsFunnel("qualify_requested", {
      ...funnelBase(),
      job_key: job.job_key,
      robot_name: active.productName,
      next: "pipeline_buyers",
    });
  }

  /** /pipeline scoped to real buyers matched to the researched robot. When an
   *  industry is passed (from a specific job's work type), it biases matching
   *  toward buyers in that vertical — the backend falls back to an open match if
   *  the filter is too narrow, so this never empties the pipeline. */
  function buyersHref(industry?: string): string {
    const robotUrl = submittedUrlRef.current || url;
    const params = new URLSearchParams();
    if (robotUrl) params.set("url", robotUrl);
    const ind = (industry || "").trim();
    if (ind) params.set("industries", ind);
    // Carry the durable robot id so saved buyer leads are grouped under this
    // robot in the CRM hub ("this robot → its collected buyers").
    if (submissionIdRef.current) {
      params.set("submission", String(submissionIdRef.current));
    }
    params.set("src", "robot_jobs_qualify");
    return `/pipeline?${params.toString()}`;
  }

  function newRobot() {
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
    viewedRef.current = new Set();
    fired3Plus.current = false;
    restoredRef.current = true;
    submittedUrlRef.current = "";
    submissionIdRef.current = null;
    clearWorkspaceSession();
  }

  const signupHref = useMemo(() => {
    const params = new URLSearchParams();
    const next = srcRef.current
      ? `/?src=${encodeURIComponent(srcRef.current)}`
      : "/";
    params.set("next", next);
    params.set("src", "robot_jobs");
    return `/signup?${params.toString()}`;
  }, []);

  function onSeeAll() {
    trackRobotJobsFunnel("see_all_clicked", {
      ...funnelBase(),
      robot_name: active?.productName,
      job_count_total: active?.jobCount,
    });
    trackSignupStart({
      source: "robot_jobs",
      robot_name: active?.productName,
      ...funnelBase(),
    });
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
            jobCount={active?.jobCount || 0}
            portfolioCount={portfolio.length}
            railTab={railTab}
            onTab={t => {
              setRailTab(t);
              const nextStage = t === "profile" ? "review" : "jobs";
              setStage(nextStage);
              saveWorkspaceSession({
                url: submittedUrlRef.current,
                products: portfolio.map(p => p.productName),
                view: nextStage === "review" ? "review" : "jobs",
                activeIdx,
              });
            }}
            onBackToPortfolio={
              portfolio.length > 1 ? () => setStage("portfolio") : undefined
            }
            onNewRobot={newRobot}
            signedIn={unlocked}
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
            onView={goToJobs}
            onReview={openReviewFor}
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
            unlocked={unlocked}
            showCount={showActiveCount}
            expandedJob={expandedJob}
            onToggle={toggleExpand}
            onPursue={onPursue}
            buyersHref={buyersHref}
            signupHref={signupHref}
            onSeeAll={onSeeAll}
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
          Robots need jobs. We find the work.
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
          {busy ? "Researching…" : "Find Jobs →"}
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
            <span className="font-mono text-emerald-400">02</span> We show what
            we understood — you confirm it.
          </li>
          <li>
            <span className="font-mono text-emerald-400">03</span> Then we find
            the work — jobs matched to confirmed capabilities.
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
        {count} robots analyzed
      </p>
      <p className="mt-3 text-[12px] leading-snug text-slate-400">
        Pick a robot to review its profile and matched work. Each robot keeps
        its own confirmed capabilities.
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
  portfolioCount,
  railTab,
  onTab,
  onBackToPortfolio,
  onNewRobot,
  signedIn,
}: {
  company: string;
  identityVerified: boolean;
  product: string;
  tier: "A" | "B" | "C";
  matched: boolean;
  showCount: boolean;
  jobCount: number;
  portfolioCount: number;
  railTab: RailTab;
  onTab: (t: RailTab) => void;
  onBackToPortfolio?: () => void;
  onNewRobot: () => void;
  signedIn: boolean;
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
            {jobCount} JOBS
          </span>
        ) : null}
      </div>

      {/* Profile / Jobs nav only exists after matching (the profile is a pre-match checkpoint).
          Pursuing an opportunity hands off to the pipeline (real buyers + CRM stages). */}
      {matched && (
        <nav className="mt-6 space-y-1">
          {navItem("profile", "Profile")}
          {navItem("jobs", "Jobs", showCount ? `${jobCount}` : undefined)}
        </nav>
      )}

      <div className="mt-auto space-y-2 pt-6">
        {onBackToPortfolio && (
          <button
            type="button"
            onClick={onBackToPortfolio}
            className="w-full border border-slate-600 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 transition hover:border-slate-400"
          >
            ← All {portfolioCount} robots
          </button>
        )}
        <button
          type="button"
          onClick={onNewRobot}
          className="w-full border border-emerald-500/50 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300 transition hover:border-emerald-400"
        >
          + New robot
        </button>
        {signedIn ? (
          <Link
            href="/my-robots"
            className="block w-full border border-slate-600 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 transition hover:border-slate-400"
          >
            Your robots &amp; leads →
          </Link>
        ) : null}
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
        Which robots should we find jobs for? Choose one, several, or all —{" "}
        {company || "this maker"} has {products.length}.
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

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={selected.length === 0}
          onClick={() => onConfirm(selected)}
          className={ctaClass}
        >
          {selected.length <= 1
            ? `Find jobs for ${selected[0] || "selected"} →`
            : `Find jobs for ${selected.length} robots →`}
        </button>
        <button
          type="button"
          onClick={() => onConfirm("all")}
          className="inline-flex items-center justify-center border border-slate-500 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-slate-200 transition hover:border-emerald-400 hover:text-emerald-300"
        >
          All {products.length} robots
        </button>
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
        {robots.length} robots analyzed
      </h2>
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
                View matches →
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

function JobsPanel({
  analysis,
  unlocked,
  showCount,
  expandedJob,
  onToggle,
  onPursue,
  buyersHref,
  signupHref,
  onSeeAll,
}: {
  analysis: RobotAnalysis;
  unlocked: boolean;
  showCount: boolean;
  expandedJob: string | null;
  onToggle: (job: MatchJob) => void;
  onPursue: (job: MatchJob) => void;
  buyersHref: (industry?: string) => string;
  signupHref: string;
  onSeeAll: () => void;
}) {
  const baseJobs = analysis.jobs;
  const visible = unlocked ? baseJobs : baseJobs.slice(0, PREVIEW_FREE);
  const hiddenCount = Math.max(0, analysis.jobCount - visible.length);
  const shownOfTop = Math.min(TOP_SHOWN, baseJobs.length);

  return (
    <div className="p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl font-bold text-slate-100">
          Jobs for {analysis.productName}
        </h2>
        <span className="font-mono text-sm font-bold text-emerald-300">
          {baseJobs.length === 0
            ? ""
            : showCount
              ? `${analysis.jobCount} JOBS FOR ${analysis.productName.toUpperCase()}`
              : `MATCHES FOR ${analysis.productName.toUpperCase()}`}
        </span>
      </div>
      {/* These are example roles that prove fit — the next step is real buyers. */}
      {baseJobs.length > 0 && (
        <p className="mt-1 text-[12px] text-slate-400">
          Example work {analysis.productName} can do, matched to its confirmed
          capabilities
          {showCount && analysis.jobCount > visible.length
            ? ` · showing the ${visible.length} strongest of ${analysis.jobCount}`
            : ` · ${visible.length} shown`}
          . Pick one to find real companies hiring for it.
        </p>
      )}

      {baseJobs.length === 0 ? (
        <ZeroState
          robotName={analysis.productName}
          reason={analysis.zeroReason}
        />
      ) : (
        <ol className="mt-6 space-y-3">
          {visible.map((job, i) => (
            <JobCard
              key={job.job_key}
              index={i + 1}
              job={job}
              robotName={analysis.productName}
              expanded={expandedJob === job.job_key}
              buyersHref={buyersHref}
              onToggle={() => onToggle(job)}
              onPursue={() => onPursue(job)}
            />
          ))}
        </ol>
      )}

      {!unlocked && hiddenCount > 0 && (
        <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5 text-center">
          <p className="font-display text-lg font-bold text-slate-100">
            More matches for {analysis.productName}
          </p>
          <p className="mt-1 text-[12px] text-slate-400">
            Create a free account to see every match and its evidence, then take
            the ones worth pursuing to real buyers.
          </p>
          <Link
            href={signupHref}
            onClick={onSeeAll}
            className={`${ctaClass} mt-4`}
          >
            {showCount
              ? `See all ${analysis.jobCount} matches →`
              : "See all matches →"}
          </Link>
        </div>
      )}

      {/* List-level next step — real buyers for this robot in the pipeline. */}
      {unlocked && baseJobs.length > 0 && (
        <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5 text-center">
          <p className="font-display text-lg font-bold text-slate-100">
            Ready to pursue this work?
          </p>
          <p className="mt-1 text-[12px] text-slate-400">
            We'll show real companies hiring for {analysis.productName}'s work —
            save the ones worth pursuing and draft outreach in your pipeline.
          </p>
          <Link href={buyersHref()} className={`${ctaClass} mt-4`}>
            Find buyers hiring for {analysis.productName}'s work →
          </Link>
        </div>
      )}
    </div>
  );
}

/**
 * Truthful zero-state. "Zero" must be explainable: did we fail to understand the
 * robot, understand it but find no compatible work, or simply lack corpus
 * coverage for its domain? These are radically different states.
 */
function ZeroState({
  robotName,
  reason,
}: {
  robotName: string;
  reason?: string | null;
}) {
  const r = (reason || "") as ZeroReason | "";
  if (r === "insufficient_profile_evidence") {
    return (
      <div className="mt-6 border border-amber-500/30 bg-amber-500/5 p-5">
        <p className="font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-amber-300">
          Insufficient robot evidence
        </p>
        <h3 className="mt-2 font-display text-lg font-bold text-slate-100">
          We found {robotName}, but couldn't establish enough capability
          evidence to match it confidently.
        </h3>
        <p className="mt-2 text-[13px] leading-snug text-slate-300">
          We confirmed some product facts, but key information about mobility,
          manipulation, autonomy, and operating capabilities is still missing —
          so we won't claim matches we can't ground.
        </p>
        <p className="mt-4 font-mono text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
          What happens next
        </p>
        <ul className="mt-1 space-y-1 text-[13px] text-slate-300">
          <li>· Review the robot profile (Profile tab)</li>
          <li>· Add a product or specification URL if available</li>
          <li>· Or try another product page for this robot</li>
        </ul>
      </div>
    );
  }
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

/**
 * Work-type → buyer vertical (substring-matched against Company.industry by the
 * backend, so tokens must be substrings of real industry names — e.g. "logistics"
 * not "warehouse", "healthcare" not "eldercare"). Specific tape families map
 * directly; generic families (transport/cart/gripper/scrub/inspect) fall back to
 * keywords found in the job's free-text industry (so e.g. an airport transport job
 * still biases toward airport buyers). Returns "" when unknown — the pipeline then
 * shows the full robot-matched set, and the backend soft-falls-back regardless.
 */
const FAMILY_VERTICAL: Record<string, string> = {
  clinical_delivery: "healthcare",
  disinfection: "healthcare",
  resident_services: "healthcare",
  serve: "hospitality",
  food_prep: "hospitality",
  beverage: "hospitality",
  restroom: "hospitality",
  shelf_scan: "retail",
  asrs: "logistics",
  pick_pack: "logistics",
  sortation: "logistics",
  trailer_unload: "logistics",
  pallet_move: "logistics",
  pallet: "logistics",
  agriculture: "agriculture",
  construction: "construction",
  mining: "mining",
};

const INDUSTRY_KEYWORD_VERTICAL: [string, string][] = [
  ["hospital", "healthcare"], ["surgery", "healthcare"], ["clinic", "healthcare"],
  ["pharmac", "healthcare"], ["senior", "healthcare"], ["assisted", "healthcare"],
  ["nursing", "healthcare"], ["memory care", "healthcare"], ["med device", "healthcare"],
  ["airport", "airport"],
  ["hotel", "hospitality"], ["restaurant", "hospitality"], ["cafe", "hospitality"], ["bar", "hospitality"],
  ["grocery", "retail"], ["retail", "retail"], ["mall", "retail"], ["home improvement", "retail"],
  ["warehouse", "logistics"], ["fulfillment", "logistics"], ["distribution", "logistics"],
  ["3pl", "logistics"], ["parcel", "logistics"], ["returns", "logistics"], ["port", "logistics"],
  ["manufacturing", "manufacturing"], ["machine shop", "manufacturing"], ["aerospace", "manufacturing"],
  ["packaging", "manufacturing"], ["process plant", "manufacturing"], ["industrial", "manufacturing"],
  ["university", "education"], ["education", "education"],
  ["utilities", "utilities"],
  ["agriculture", "agriculture"], ["construction", "construction"], ["mining", "mining"],
];

function verticalForJob(job: MatchJob): string {
  const fam = (job.tape_family || "").toLowerCase().trim();
  if (FAMILY_VERTICAL[fam]) return FAMILY_VERTICAL[fam];
  const ind = (job.industry || "").toLowerCase();
  for (const [kw, vert] of INDUSTRY_KEYWORD_VERTICAL) {
    if (ind.includes(kw)) return vert;
  }
  return "";
}

function JobCard({
  index,
  job,
  robotName,
  expanded,
  buyersHref,
  onToggle,
  onPursue,
}: {
  index: number;
  job: MatchJob;
  robotName: string;
  expanded: boolean;
  buyersHref: (industry?: string) => string;
  onToggle: () => void;
  onPursue: () => void;
}) {
  const possible = job.verdict !== "NOT_A_MATCH";
  const place = [job.company_name, job.locality].filter(Boolean).join(" · ");
  return (
    <li className="border border-slate-600 bg-[#081126]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start gap-3 p-4 text-left"
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
          {expanded ? "−" : "+"}
        </span>
      </button>

      {expanded && (
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

          {possible ? (
            <div className="mt-4">
              <Link
                href={buyersHref(verticalForJob(job))}
                onClick={onPursue}
                className={`${ctaClass} w-full`}
              >
                Find buyers hiring for this →
              </Link>
              <p className="mt-2 text-[12px] text-slate-500">
                Real companies hiring for this kind of work that fit {robotName}{" "}
                — save the ones worth pursuing and draft outreach.
              </p>
            </div>
          ) : null}
        </div>
      )}
    </li>
  );
}
