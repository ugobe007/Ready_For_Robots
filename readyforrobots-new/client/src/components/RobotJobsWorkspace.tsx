/**
 * RobotJobsWorkspace — the ReadyForRobots work terminal (front door `/`).
 *
 * The large panel is the workspace; the narrow rail is navigation/context.
 * One deliberate state at a time (submit-stability principle):
 *
 *   FIND → RESEARCH → SELECT → REVIEW PROFILE → JOBS
 *
 * SELECT supports one robot, several, or all (OEM → portfolio → distributor)
 * without changing the underlying product. Job match evidence (Why / Still
 * unknown / Blocker) lives in the large panel next to each job — the evidence
 * is the product, not the job title.
 *
 * Data: /api/robot-job-search (one transaction: profile + jobs). Matcher and
 * scoring are frozen (M2) — this component only presents their output.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { trackRobotJobsFunnel, trackSignupStart } from "@/lib/siteAnalytics";
import {
  fetchRobotJobSearch,
  type RobotJobSearchResult,
} from "@/lib/robotJobSearch";
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
type RailTab = "profile" | "jobs" | "qualified";

/** One fully-analyzed robot (single transaction result). */
type RobotAnalysis = {
  productName: string;
  companyName: string;
  tier: "A" | "B" | "C";
  profile: RobotProfileResult | null;
  capabilities: MatchCapability[];
  jobs: MatchJob[];
  jobCount: number;
};

type ProductChoice = { name: string; displayClass?: string | null };

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
  stage?: Stage;
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

function toAnalysis(res: RobotJobSearchResult): RobotAnalysis {
  const profile = (res.profile as RobotProfileResult | null) ?? null;
  const productName =
    profile?.selected_product?.name ||
    res.robot_name ||
    res.company_name ||
    "Your robot";
  const companyName =
    profile?.company?.name || res.company_name || res.robot_name || "";
  const tier = (profile?.profile_confidence as "A" | "B" | "C") || "C";
  return {
    productName,
    companyName,
    tier,
    profile,
    capabilities: res.capabilities || [],
    jobs: res.jobs || [],
    jobCount: res.job_count || (res.jobs || []).length,
  };
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

/** Short capability summary line for a portfolio card. */
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

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function RobotJobsWorkspace() {
  const { session } = useAuth();
  const unlocked = Boolean(session);

  const [stage, setStage] = useState<Stage>("find");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  // SELECT
  const [companyName, setCompanyName] = useState("");
  const [products, setProducts] = useState<ProductChoice[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  // Results
  const [portfolio, setPortfolio] = useState<RobotAnalysis[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [railTab, setRailTab] = useState<RailTab>("jobs");
  const [qualified, setQualified] = useState<Record<string, string[]>>({}); // productName -> job_keys
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  const sessionId = useRef(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `rdd_${Date.now()}`
  );
  const srcRef = useRef(srcFromQuery());
  const viewedRef = useRef<Set<string>>(new Set());
  const fired3Plus = useRef(false);
  const restoredRef = useRef(false);

  const funnelBase = () => ({
    session_id: sessionId.current,
    ...(srcRef.current ? { src: srcRef.current } : {}),
  });

  const active = portfolio[activeIdx] || null;

  useEffect(() => {
    trackRobotJobsFunnel("experiment_view", {
      ...funnelBase(),
      surface: "workspace",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* Restore discovery after auth return (signup continuity). */
  useEffect(() => {
    if (!session || restoredRef.current) return;
    if (stage !== "find") return;
    const saved = readWorkspaceSession();
    if (saved?.url) {
      restoredRef.current = true;
      void runSearch(saved.url, saved.products, saved.stage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  /* -------------------------------------------------------------- */
  /* Core: research one or more robots                               */
  /* -------------------------------------------------------------- */

  async function runSearch(
    submitUrl: string,
    productNames: string[],
    restoredStage?: Stage
  ) {
    setError(null);
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
    saveWorkspaceSession({ url: submitUrl, products: productNames });

    try {
      if (productNames.length === 0) {
        // First pass — may need product selection.
        const res = await fetchRobotJobSearch({ url: submitUrl });
        setCompanyName(res.company_name || res.robot_name || "");
        if (res.state === "select_product" && (res.products || []).length > 1) {
          setProducts(
            (res.products || []).map(p => ({
              name: p.name,
              displayClass: p.display_class,
            }))
          );
          setSelected([]);
          setStage("select");
          return;
        }
        finalizePortfolio([toAnalysis(res)], submitUrl, restoredStage);
        return;
      }

      // Specific product(s) chosen — one transaction each.
      const results = await Promise.all(
        productNames.map(name =>
          fetchRobotJobSearch({ url: submitUrl, product: name }).catch(
            () => null
          )
        )
      );
      const analyses = results
        .filter((r): r is RobotJobSearchResult => Boolean(r))
        .map(toAnalysis);
      if (analyses.length === 0) {
        setError("We could not research those robots. Try another URL.");
        setStage("find");
        return;
      }
      finalizePortfolio(analyses, submitUrl, restoredStage);
    } catch {
      setError("Research failed. Check the URL and try again.");
      setStage("find");
    }
  }

  function finalizePortfolio(
    analyses: RobotAnalysis[],
    submitUrl: string,
    restoredStage?: Stage
  ) {
    setPortfolio(analyses);

    const saved = readWorkspaceSession();
    const restoredIdx =
      saved?.activeIdx !== undefined && saved.activeIdx < analyses.length
        ? saved.activeIdx
        : 0;
    const useRestoredIdx =
      restoredStage === "jobs" &&
      analyses.length > 1 &&
      saved?.activeIdx !== undefined;
    const finalIdx = useRestoredIdx ? restoredIdx : 0;

    setActiveIdx(finalIdx);
    setExpandedJob(null);
    viewedRef.current = new Set();
    fired3Plus.current = false;

    let targetStage: Stage;
    if (restoredStage === "jobs") {
      targetStage = "jobs";
      setRailTab("jobs");
    } else if (analyses.length > 1) {
      targetStage = "portfolio";
    } else {
      targetStage = "review";
      setRailTab("profile");
    }

    saveWorkspaceSession({
      url: submitUrl,
      products: analyses.map(a => a.productName),
      stage: targetStage,
      activeIdx: finalIdx,
    });
    trackRobotJobsFunnel("capabilities_viewed", {
      ...funnelBase(),
      robot_name: analyses[finalIdx]?.productName,
      company_name: analyses[finalIdx]?.companyName,
      profile_tier: analyses[finalIdx]?.tier,
      robots_analyzed: analyses.length,
    });
    setStage(targetStage);
  }

  /* -------------------------------------------------------------- */
  /* Handlers                                                        */
  /* -------------------------------------------------------------- */

  function onSubmitFind(e: React.FormEvent) {
    e.preventDefault();
    const u = url.trim();
    if (!u) return;
    void runSearch(u, []);
  }

  function toggleProduct(name: string) {
    setSelected(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]
    );
  }

  function confirmSelection(which: string[] | "all") {
    const names = which === "all" ? products.map(p => p.name) : which;
    if (names.length === 0) return;
    const saved = readWorkspaceSession();
    void runSearch(saved?.url || url, names);
  }

  function openReviewFor(idx: number) {
    setActiveIdx(idx);
    setRailTab("profile");
    setStage("review");
    const saved = readWorkspaceSession();
    if (saved?.url) {
      saveWorkspaceSession({ ...saved, activeIdx: idx });
    }
  }

  function findJobsForActive() {
    setRailTab("jobs");
    setStage("jobs");
    const saved = readWorkspaceSession();
    if (saved?.url) {
      saveWorkspaceSession({ ...saved, stage: "jobs", activeIdx });
    }
    trackRobotJobsFunnel("discovery_complete", {
      ...funnelBase(),
      robot_name: active?.productName,
      job_count: active?.jobCount,
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

  function onQualify(job: MatchJob) {
    if (!active) return;
    trackRobotJobsFunnel("qualify_opened", {
      ...funnelBase(),
      job_key: job.job_key,
    });
    trackRobotJobsFunnel("qualify_requested", {
      ...funnelBase(),
      job_key: job.job_key,
      robot_name: active.productName,
    });
    setQualified(prev => {
      const cur = prev[active.productName] || [];
      if (cur.includes(job.job_key)) return prev;
      return { ...prev, [active.productName]: [...cur, job.job_key] };
    });
  }

  function newRobot() {
    setStage("find");
    setUrl("");
    setError(null);
    setPortfolio([]);
    setProducts([]);
    setSelected([]);
    setCompanyName("");
    setActiveIdx(0);
    setExpandedJob(null);
    viewedRef.current = new Set();
    fired3Plus.current = false;
    restoredRef.current = true; // do not auto-restore over an explicit reset
    try {
      window.sessionStorage.removeItem(WORKSPACE_SESSION_KEY);
    } catch {
      /* ignore */
    }
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

  const showLeftJobsNav = stage === "review" || stage === "jobs";

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
            company={companyName || portfolio[0]?.companyName || ""}
            count={portfolio.length}
            onNewRobot={newRobot}
          />
        ) : (
          <ContextRail
            company={active?.companyName || companyName}
            product={active?.productName || ""}
            tier={active?.tier || "C"}
            jobCount={active?.jobCount || 0}
            portfolioCount={portfolio.length}
            railTab={railTab}
            showNav={showLeftJobsNav}
            qualifiedCount={
              active ? qualified[active.productName]?.length || 0 : 0
            }
            onTab={t => {
              setRailTab(t);
              setStage(t === "profile" ? "review" : "jobs");
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
          <div className="h-full">
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
            onView={idx => {
              setActiveIdx(idx);
              setRailTab("jobs");
              setStage("jobs");
              const saved = readWorkspaceSession();
              if (saved?.url) {
                saveWorkspaceSession({
                  ...saved,
                  stage: "jobs",
                  activeIdx: idx,
                });
              }
              trackRobotJobsFunnel("discovery_complete", {
                ...funnelBase(),
                robot_name: portfolio[idx]?.productName,
                job_count: portfolio[idx]?.jobCount,
              });
            }}
            onReview={openReviewFor}
          />
        )}

        {stage === "review" && active && (
          <ReviewPanel analysis={active} onFindJobs={findJobsForActive} />
        )}

        {stage === "jobs" && active && (
          <JobsPanel
            analysis={active}
            unlocked={unlocked}
            railTab={railTab}
            qualifiedKeys={qualified[active.productName] || []}
            expandedJob={expandedJob}
            onToggle={toggleExpand}
            onQualify={onQualify}
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
  const busy = stage === "research";
  const selecting = stage === "select";
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className={eyebrow}>
        {busy || selecting ? "Your robot" : "Find jobs"}
      </p>
      <h1 className="mt-1 font-display text-3xl font-bold leading-tight tracking-tight text-slate-100">
        {busy || selecting ? (
          companyName || "Researching…"
        ) : (
          <>
            Find <span className="text-emerald-400">jobs</span> for your robot.
          </>
        )}
      </h1>
      {!busy && !selecting && (
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
          disabled={busy || selecting}
          className="mt-2 w-full border border-slate-600 bg-[#081126] px-3 py-3 font-mono text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-emerald-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={busy || selecting || !url.trim()}
          className={`${ctaClass} mt-3 w-full`}
        >
          {busy ? "Researching…" : selecting ? "Select robot →" : "Find Jobs →"}
        </button>
      </form>

      {error && (
        <p className="mt-3 border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-300">
          {error}
        </p>
      )}

      {selecting && onCancel && (
        <div className="mt-4">
          <button
            type="button"
            onClick={onCancel}
            className="w-full border border-slate-600 px-3 py-2 text-center font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-slate-300 transition hover:border-slate-400"
          >
            ← Start over
          </button>
        </div>
      )}

      <div className="mt-auto pt-6">
        <ol className="space-y-3 text-xs text-slate-400">
          <li>
            <span className="font-mono text-emerald-400">01</span> Show us your
            robot — we research the company and product.
          </li>
          <li>
            <span className="font-mono text-emerald-400">02</span> We build a
            robot profile — grounded facts from sources.
          </li>
          <li>
            <span className="font-mono text-emerald-400">03</span> Then we find
            the work — jobs matched to what we confirmed.
          </li>
        </ol>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Left rail — PORTFOLIO overview context                              */
/* ================================================================== */

function PortfolioRail({
  company,
  count,
  onNewRobot,
}: {
  company: string;
  count: number;
  onNewRobot: () => void;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <p className={eyebrow}>Portfolio</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-slate-100">
        {company}
      </h2>
      <p className="mt-0.5 font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300">
        {count} robots analyzed
      </p>
      <p className="mt-3 text-[12px] leading-snug text-slate-400">
        Pick a robot to review its profile and jobs. Each robot keeps its own
        confirmed capabilities and matched work.
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
  product,
  tier,
  jobCount,
  portfolioCount,
  railTab,
  showNav,
  qualifiedCount,
  onTab,
  onBackToPortfolio,
  onNewRobot,
}: {
  company: string;
  product: string;
  tier: "A" | "B" | "C";
  jobCount: number;
  portfolioCount: number;
  railTab: RailTab;
  showNav: boolean;
  qualifiedCount: number;
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
      <p className="mt-0.5 text-sm text-slate-400">{company}</p>
      <div className="mt-3 flex items-center gap-2">
        <span className={eyebrow}>Profile</span>
        <span className={`font-mono text-base font-bold ${tierColor(tier)}`}>
          {tier}
        </span>
        <span className="ml-2 font-mono text-[11px] font-bold text-emerald-300">
          {jobCount} JOBS
        </span>
      </div>

      {showNav && (
        <nav className="mt-6 space-y-1">
          {navItem("profile", "Profile")}
          {navItem("jobs", "Jobs", `${jobCount}`)}
          {navItem("qualified", "Qualified", `${qualifiedCount}`)}
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
/* Workspace — SELECT (one / several / all)                            */
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
/* Workspace — PORTFOLIO (multiple robots)                             */
/* ================================================================== */

function PortfolioPanel({
  company,
  robots,
  onView,
  onReview,
}: {
  company: string;
  robots: RobotAnalysis[];
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
              <span className="font-mono text-sm font-bold text-emerald-300">
                {a.jobCount} jobs
              </span>
            </div>
            <div className="mt-3 flex gap-3">
              <button
                type="button"
                onClick={() => onView(idx)}
                className="font-mono text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-300 hover:text-emerald-200"
              >
                View jobs →
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
/* Workspace — REVIEW PROFILE (checkpoint)                             */
/* ================================================================== */

function ReviewPanel({
  analysis,
  onFindJobs,
}: {
  analysis: RobotAnalysis;
  onFindJobs: () => void;
}) {
  const [showSources, setShowSources] = useState(false);
  const profile = analysis.profile;
  const confirmed = confirmedFacts(profile);
  const unknowns = unknownFacts(profile);
  const conflicts = conflictFacts(profile);
  const sources = profile?.sources || [];

  return (
    <div className="p-6 sm:p-8">
      <p className={eyebrow}>Here's what we understood</p>
      <div className="mt-1 flex flex-wrap items-baseline gap-x-3">
        <h2 className="font-display text-3xl font-bold tracking-tight text-slate-100">
          {analysis.productName}
        </h2>
        <span className="text-lg text-slate-400">{analysis.companyName}</span>
      </div>
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
          <p className={eyebrow}>We confirmed</p>
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
      </div>
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
        <button type="button" onClick={onFindJobs} className={ctaClass}>
          Find jobs for {analysis.productName} →
        </button>
        <p className="mt-2 text-[11px] text-slate-500">
          Confirm we understood your robot — then we match {analysis.jobCount}{" "}
          jobs against these capabilities.
        </p>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Workspace — JOBS (evidence is the product)                          */
/* ================================================================== */

function JobsPanel({
  analysis,
  unlocked,
  railTab,
  qualifiedKeys,
  expandedJob,
  onToggle,
  onQualify,
  signupHref,
  onSeeAll,
}: {
  analysis: RobotAnalysis;
  unlocked: boolean;
  railTab: RailTab;
  qualifiedKeys: string[];
  expandedJob: string | null;
  onToggle: (job: MatchJob) => void;
  onQualify: (job: MatchJob) => void;
  signupHref: string;
  onSeeAll: () => void;
}) {
  const showQualifiedOnly = railTab === "qualified";
  const allJobs = analysis.jobs;
  const baseJobs = showQualifiedOnly
    ? allJobs.filter(j => qualifiedKeys.includes(j.job_key))
    : allJobs;
  const visible = unlocked ? baseJobs : baseJobs.slice(0, PREVIEW_FREE);
  const hiddenCount = Math.max(0, analysis.jobCount - visible.length);
  const shownOfTop = Math.min(TOP_SHOWN, allJobs.length);

  return (
    <div className="p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl font-bold text-slate-100">
          {showQualifiedOnly
            ? "Qualified jobs"
            : `Jobs for ${analysis.productName}`}
        </h2>
        <span className="font-mono text-sm font-bold text-emerald-300">
          {showQualifiedOnly
            ? `${baseJobs.length} qualified`
            : `${analysis.jobCount} JOBS FOR ${analysis.productName.toUpperCase()}`}
        </span>
      </div>
      {!showQualifiedOnly && (
        <p className="mt-1 text-[12px] text-slate-400">
          We matched these jobs against {analysis.productName}'s confirmed
          capabilities · {shownOfTop} strongest matches shown
        </p>
      )}

      {baseJobs.length === 0 ? (
        <p className="mt-8 text-sm text-slate-400">
          {showQualifiedOnly
            ? "No qualified jobs yet — open a job and Qualify it."
            : "No strong matches in the current corpus for this robot yet."}
        </p>
      ) : (
        <ol className="mt-6 space-y-3">
          {visible.map((job, i) => (
            <JobCard
              key={job.job_key}
              index={i + 1}
              job={job}
              robotName={analysis.productName}
              expanded={expandedJob === job.job_key}
              qualified={qualifiedKeys.includes(job.job_key)}
              onToggle={() => onToggle(job)}
              onQualify={() => onQualify(job)}
            />
          ))}
        </ol>
      )}

      {!unlocked && !showQualifiedOnly && hiddenCount > 0 && (
        <div className="mt-6 border border-emerald-500/30 bg-emerald-400/5 p-5 text-center">
          <p className="font-display text-lg font-bold text-slate-100">
            {hiddenCount} more jobs for {analysis.productName}
          </p>
          <p className="mt-1 text-[12px] text-slate-400">
            Create a free account to see every match, its evidence, and qualify
            the ones worth pursuing.
          </p>
          <Link
            href={signupHref}
            onClick={onSeeAll}
            className={`${ctaClass} mt-4`}
          >
            See all {analysis.jobCount} jobs →
          </Link>
        </div>
      )}
    </div>
  );
}

function JobCard({
  index,
  job,
  robotName,
  expanded,
  qualified,
  onToggle,
  onQualify,
}: {
  index: number;
  job: MatchJob;
  robotName: string;
  expanded: boolean;
  qualified: boolean;
  onToggle: () => void;
  onQualify: () => void;
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
        <span className="mt-0.5 font-mono text-xs text-slate-500">
          {String(index).padStart(2, "0")}
        </span>
        <span className="flex-1">
          <span
            className={`font-mono text-[10px] font-bold uppercase tracking-[0.12em] ${
              possible ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {possible ? "Possible match" : "Not a match"}
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

          <button
            type="button"
            onClick={onQualify}
            disabled={qualified}
            className={`${ctaClass} mt-4`}
          >
            {qualified ? "Qualification requested ✓" : "Qualify this job →"}
          </button>
        </div>
      )}
    </li>
  );
}
