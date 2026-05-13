/**
 * Pipeline — ReadyForRobots
 * Two-panel layout: left = inline deal rows grouped by stage, right = selected deal detail + outreach draft
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 * Design: Linear/Raycast-inspired — dense, inline, data-forward
 */
import { useEffect, useState } from "react";
import {
  AlertTriangle, MapPin, Filter, ChevronRight,
  Copy, CheckCheck, ArrowRight, ArrowLeft, Mail,
  Users, Clock, Target, Newspaper
} from "lucide-react";
import Header from "@/components/Header";
import { Link } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { marketInsightForIndustry } from "@/lib/industryContext";
import { mapApiLeadToDeal, type ApiLead } from "@/lib/pipelineLeadMap";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { cleanAndClampText, cleanScrapedText } from "@/lib/text";

type Stage = "New Signal" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";

interface Deal {
  id: number;
  company: string;
  location: string;
  industry: string;
  score: number;
  signal: string;
  signalType: string;
  signalColor: string;
  stage: Stage;
  updatedAt: string;
  contact?: string;
  contactTitle?: string;
  outreachSubject?: string;
  outreachBody?: string;
  notes?: string;
  researchUpdates?: Array<{
    id: number;
    update_type?: string;
    title?: string;
    summary?: string;
    source_url?: string | null;
    source_domain?: string | null;
    detected_at?: string | null;
    significance_score?: number;
  }>;
  lastResearchedAt?: string | null;
  latestMaterialUpdate?: {
    id: number;
    title?: string;
    summary?: string;
    source_domain?: string | null;
    detected_at?: string | null;
    significance_score?: number;
  } | null;
}

interface ScoutActivationLead {
  id: string;
  company: string;
  score?: number | null;
  signal?: string | null;
  signalType?: string | null;
  action?: string | null;
}

interface ScoutActivation {
  id: number;
  status: string;
  statusFlow?: Array<{
    id: string;
    label: string;
    description: string;
    active: boolean;
  }>;
  sourceUrl?: string | null;
  material: "upload" | "suggest" | "skip";
  materialFilename?: string | null;
  scope: "all" | "selected" | "top";
  mode: "manual" | "assisted" | "autopilot";
  leadCount: number;
  leads: ScoutActivationLead[];
  workPlan?: {
    materials?: {
      next?: string;
    };
    deck_strategy?: {
      recommended_format?: string;
      sections?: string[];
      positioning?: string;
      next_output?: string;
    };
    safety_requirements?: Array<{
      key: string;
      label: string;
      required: boolean;
    }>;
    notification_policy?: {
      reply?: string;
      meeting?: string;
      email?: string;
    };
    steps?: string[];
    sending_policy?: string;
  };
  activityLog?: Array<{ type?: string; message?: string }>;
  createdAt?: string | null;
  requiresAccount?: boolean;
}

interface LeadSummary {
  total?: number;
  hot?: number;
  warm?: number;
  cold?: number;
  total_signals?: number;
  companies_in_database?: number;
  signals_in_database?: number;
}

interface MarketSnippet {
  label: string;
  headline: string;
  detail: string;
  color: string;
}

const STAGES: Stage[] = ["New Signal", "Draft Ready", "Outreach Sent", "Qualified", "Meeting Set"];

const STAGE_META: Record<Stage, { color: string; dot: string; label: string; desc: string }> = {
  "New Signal":    { color: "#a78bfa", dot: "#a78bfa", label: "New Signal",    desc: "Just detected" },
  "Draft Ready":   { color: "#60a5fa", dot: "#60a5fa", label: "Draft Ready",   desc: "Outreach drafted" },
  "Outreach Sent": { color: "#FFB000", dot: "#FFB000", label: "Outreach Sent", desc: "Awaiting reply" },
  "Qualified":     { color: "#34d399", dot: "#34d399", label: "Qualified",     desc: "Engaged buyer" },
  "Meeting Set":   { color: "#f472b6", dot: "#f472b6", label: "Meeting Set",   desc: "On the calendar" },
};

const scoreColor = (s: number) =>
  s >= 90 ? "#34d399" : s >= 75 ? "#a78bfa" : "#FFB000";

const statusLabel = (status: string) =>
  status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const displayStageLabel = (deal: Pick<Deal, "stage" | "signalType">) =>
  deal.stage === "New Signal" ? deal.signalType : deal.stage;

const displayStageColor = (deal: Pick<Deal, "stage" | "signalColor">) =>
  deal.stage === "New Signal" ? deal.signalColor : STAGE_META[deal.stage].color;

const formatActivationTime = (value?: string | null) => {
  if (!value) return "just now";
  const created = new Date(value);
  if (Number.isNaN(created.getTime())) return "just now";
  const diffMinutes = Math.max(0, Math.round((Date.now() - created.getTime()) / 60000));
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.round(diffHours / 24)}d ago`;
};

const activationSourceLabel = (sourceUrl?: string | null) =>
  cleanAndClampText(sourceUrl, 96) || "No source URL captured";

const activationLeadText = (lead: ScoutActivationLead) =>
  cleanAndClampText(lead.signal || lead.action, 160) || "Lead queued for SCOUT evaluation.";

const formatMetric = (value?: number) =>
  typeof value === "number" ? new Intl.NumberFormat("en-US").format(value) : "—";

const DEFAULT_MARKET_SNIPPET: MarketSnippet = {
  label: "Market movement",
  headline: "SCOUT is watching live buyer signals",
  detail: "As the pipeline loads, SCOUT is looking for expansion, labor, budget, procurement, deployment, and partnership signals that indicate robot demand is moving.",
  color: "#FFB000",
};

function marketSnippetFromDeals(deals: Deal[]): MarketSnippet {
  const first = deals.find((deal) => deal.signal && deal.signal !== "Buying signal detected");
  if (!first) return DEFAULT_MARKET_SNIPPET;
  const insightByIndustry = marketInsightForIndustry(first.industry);
  return {
    label: `${first.signalType} movement`,
    headline: `${first.company} is moving in ${first.industry || "the market"}`,
    detail: `${cleanAndClampText(first.signal, 180)} ${insightByIndustry}`,
    color: first.signalColor || "#FFB000",
  };
}

const formatResearchTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

function PipelineMetric({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
  return (
    <div className="rounded-2xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.03)" }}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/28">{label}</p>
        <span className="h-2 w-2 rounded-full" style={{ background: color, boxShadow: `0 0 18px ${color}66` }} />
      </div>
      <p className="font-mono text-2xl font-bold leading-none" style={{ color, fontFamily: "'JetBrains Mono', monospace" }}>
        {value}
      </p>
      <p className="mt-2 text-[11px] leading-relaxed text-white/35">{sub}</p>
    </div>
  );
}

export default function Pipeline() {
  const { session } = useAuth();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [summary, setSummary] = useState<LeadSummary | null>(null);
  const [marketSnippet, setMarketSnippet] = useState<MarketSnippet>(DEFAULT_MARKET_SNIPPET);
  const [activations, setActivations] = useState<ScoutActivation[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [industryQuery, setIndustryQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedActivationId, setSelectedActivationId] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingResearch, setLoadingResearch] = useState(false);
  const [loadingActivations, setLoadingActivations] = useState(true);
  const [loadErr, setLoadErr] = useState("");
  const [activationErr, setActivationErr] = useState("");

  useEffect(() => {
    const base = getApiBase();
    let cancelled = false;

    (async () => {
      setLoadingLeads(true);
      setLoadErr("");
      try {
        const leadsResponse = await fetch(`${base}/api/leads?limit=18&exclude_junk=true&sort=score`, liveFetchInit());
        if (!leadsResponse.ok) throw new Error(await leadsResponse.text());
        const rows = (await leadsResponse.json()) as ApiLead[];
        const mapped = Array.isArray(rows) ? rows.map(mapApiLeadToDeal) : [];
        if (cancelled) return;
        setDeals(mapped);
        setSelectedId(mapped[0]?.id ?? null);
        setMarketSnippet(marketSnippetFromDeals(mapped));
      } catch (e) {
        if (cancelled) return;
        setLoadErr(e instanceof Error ? e.message : "Could not load pipeline");
        setDeals([]);
        setSelectedId(null);
      } finally {
        if (!cancelled) setLoadingLeads(false);
      }
    })();

    (async () => {
      setLoadingSummary(true);
      try {
        const summaryResponse = await fetch(`${base}/api/leads/summary?exclude_junk=true`, liveFetchInit());
        if (!summaryResponse.ok) throw new Error(await summaryResponse.text());
        const payload = (await summaryResponse.json()) as LeadSummary;
        if (!cancelled) setSummary(payload);
      } catch {
        if (!cancelled) setSummary(null);
      } finally {
        if (!cancelled) setLoadingSummary(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    const existing = deals.find((deal) => deal.id === selectedId);
    if (existing?.researchUpdates) return;
    const base = getApiBase();
    (async () => {
      setLoadingResearch(true);
      try {
        const response = await fetch(`${base}/api/leads/by-id/${selectedId}`, liveFetchInit());
        if (!response.ok) throw new Error(await response.text());
        const lead = (await response.json()) as ApiLead;
        const mapped = mapApiLeadToDeal(lead);
        setDeals((prev) => prev.map((deal) => (deal.id === selectedId ? { ...deal, ...mapped } : deal)));
      } catch {
        // Research is additive; keep the core pipeline usable if detail enrichment misses.
      } finally {
        setLoadingResearch(false);
      }
    })();
  }, [selectedId, deals]);

  useEffect(() => {
    const base = getApiBase();
    (async () => {
      setLoadingActivations(true);
      setActivationErr("");
      try {
        const headers = authHeader(session?.access_token);
        const response = await fetch(
          `${base}/api/scout/activations?fingerprint=${encodeURIComponent(scoutFingerprint())}&limit=6`,
          liveFetchInit({ headers }),
        );
        if (!response.ok) throw new Error(await response.text());
        const payload = (await response.json()) as { activations?: ScoutActivation[] };
        const rows = Array.isArray(payload.activations) ? payload.activations : [];
        setActivations(rows);
        setSelectedActivationId(rows[0]?.id ?? null);
      } catch (e) {
        setActivationErr(e instanceof Error ? e.message : "Could not load SCOUT activations");
        setActivations([]);
        setSelectedActivationId(null);
      } finally {
        setLoadingActivations(false);
      }
    })();
  }, [session]);

  const industries = Array.from(new Set(deals.map((d) => d.industry).filter(Boolean))).sort();
  const resolvedIndustryFilter = industryQuery.trim() || filter;
  const filtered = !resolvedIndustryFilter || resolvedIndustryFilter === "All"
    ? deals
    : deals.filter((d) => d.industry.toLowerCase().includes(resolvedIndustryFilter.toLowerCase()));
  const selected = deals.find((d) => d.id === selectedId) ?? null;
  const selectedActivation = activations.find((a) => a.id === selectedActivationId) ?? activations[0] ?? null;

  const moveStage = (id: number, direction: 1 | -1) => {
    setDeals((prev) =>
      prev.map((d) => {
        if (d.id !== id) return d;
        const idx = STAGES.indexOf(d.stage);
        const next = STAGES[idx + direction];
        if (!next) return d;
        toast.success(`Moved "${d.company}" to ${next}`);
        return { ...d, stage: next, updatedAt: "just now" };
      })
    );
  };

  const copyDraft = () => {
    if (!selected?.outreachBody) return;
    navigator.clipboard.writeText(`Subject: ${selected.outreachSubject}\n\n${selected.outreachBody}`);
    setCopied(true);
    toast.success("Draft copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const totalDeals = summary?.total ?? filtered.length;
  const hotDeals = summary?.hot ?? filtered.filter((d) => d.score >= 85).length;
  const warmDeals = summary?.warm ?? filtered.filter((d) => d.score >= 65 && d.score < 85).length;
  const visibleDeals = filtered.length;
  const queuedActivations = activations.filter((a) => ["queued", "evaluating", "drafted", "awaiting_approval"].includes(a.status)).length;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-20 pb-6 px-4 lg:px-6">
        <div className="max-w-[1500px] mx-auto flex flex-col gap-4">

          {/* ── Top bar ── */}
          {loadErr && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/90">
              {loadErr}
            </div>
          )}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5" style={{ color: "#a78bfa" }}>SCOUT</p>
                <h1 className="font-extrabold text-white text-xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Active Signals → Live Pipeline
                </h1>
                <p className="text-[11px] text-white/35 mt-0.5 max-w-md">
                  Authoritative database counts up top. A focused working slice below.
                </p>
              </div>
            </div>

            {/* Industry filter */}
            <div className="relative w-full sm:w-[320px]">
              <Filter className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/25" />
              <input
                value={industryQuery}
                onChange={(e) => {
                  setIndustryQuery(e.target.value);
                  setFilter("All");
                }}
                list="pipeline-industries"
                placeholder="Filter by industry..."
                className="w-full rounded-xl border border-white/10 bg-white/[0.035] py-2.5 pl-9 pr-9 text-xs font-semibold text-white outline-none placeholder:text-white/25 focus:border-violet-400/60"
              />
              {industryQuery && (
                <button
                  type="button"
                  onClick={() => setIndustryQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-white/35 hover:text-white/70"
                >
                  Clear
                </button>
              )}
              <datalist id="pipeline-industries">
                {industries.map((ind) => (
                  <option key={ind} value={ind} />
                ))}
              </datalist>
            </div>
          </div>

          <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <PipelineMetric
              label="Database total"
              value={formatMetric(totalDeals)}
              sub={loadingSummary ? "Refreshing market totals..." : `${formatMetric(summary?.total_signals)} scored buying signals`}
              color="#ffffff"
            />
            <PipelineMetric
              label="Hot leads"
              value={formatMetric(hotDeals)}
              sub="Ready for direct sales motion"
              color="#34d399"
            />
            <PipelineMetric
              label="Warm leads"
              value={formatMetric(warmDeals)}
              sub="Sequence, monitor, and enrich"
              color="#FFB000"
            />
            <PipelineMetric
              label="Working slice"
              value={formatMetric(visibleDeals)}
              sub={`${formatMetric(queuedActivations)} SCOUT activations queued`}
              color="#a78bfa"
            />
          </section>

          <section
            className="rounded-2xl border px-4 py-3"
            style={{ background: "rgba(255,176,0,0.045)", borderColor: "rgba(255,176,0,0.16)" }}
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <div
                  className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border"
                  style={{ borderColor: `${marketSnippet.color}44`, background: `${marketSnippet.color}12` }}
                >
                  <Newspaper className="h-4 w-4" style={{ color: marketSnippet.color }} />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#FFB000" }}>
                    {marketSnippet.label}
                  </p>
                  <h2 className="mt-1 break-words text-sm font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {marketSnippet.headline}
                  </h2>
                  <p className="mt-1 break-words text-[12px] leading-relaxed" style={{ color: "#FFB000" }}>
                    {marketSnippet.detail}
                  </p>
                </div>
              </div>
              <Link
                href="/newsletter"
                className="inline-flex shrink-0 items-center gap-1.5 text-xs font-bold"
                style={{ color: "#FFB000" }}
              >
                Read daily brief <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </section>

          {/* ── SCOUT activation queue ── */}
          <div className="rounded-2xl border border-white/8 overflow-hidden" style={{ background: "rgba(255,255,255,0.025)" }}>
            <div className="flex flex-col xl:flex-row">
              <div className="xl:w-[360px] border-b xl:border-b-0 xl:border-r border-white/8">
                <div className="px-4 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#a78bfa" }}>SCOUT Queue</p>
                    <p className="text-xs text-white/35 mt-1">Recent sales activations from Results</p>
                  </div>
                  <span className="text-[10px] text-white/30">{loadingActivations ? "Loading…" : `${activations.length} active`}</span>
                </div>
                {activationErr && (
                  <div className="mx-4 mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100/90">
                    {activationErr}
                  </div>
                )}
                <div className="px-2 pb-3 flex xl:flex-col gap-2 overflow-x-auto">
                  {activations.length === 0 && !loadingActivations ? (
                    <div className="m-2 rounded-xl border border-dashed border-white/8 px-4 py-4 text-center">
                      <p className="text-xs font-semibold text-white/45">No SCOUT activations yet</p>
                      <p className="text-[11px] text-white/25 mt-1">Activate leads from the Results page and they will appear here.</p>
                    </div>
                  ) : (
                    activations.map((activation) => {
                      const isActive = activation.id === selectedActivation?.id;
                      return (
                        <button
                          key={activation.id}
                          onClick={() => setSelectedActivationId(activation.id)}
                          className="min-w-[260px] xl:min-w-0 text-left rounded-xl border px-3 py-2.5 transition-all"
                          style={
                            isActive
                              ? { background: "rgba(124,58,237,0.14)", borderColor: "rgba(124,58,237,0.38)" }
                              : { background: "rgba(255,255,255,0.025)", borderColor: "rgba(255,255,255,0.07)" }
                          }
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-white/80">{activation.leadCount} leads</span>
                            <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide" style={{ background: "rgba(167,139,250,0.14)", color: "#c4b5fd" }}>
                              {statusLabel(activation.status)}
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] text-white/35 truncate">
                            {activation.mode} · {activation.scope} · {formatActivationTime(activation.createdAt)}
                          </p>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="flex-1 p-4">
                {selectedActivation ? (
                  <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h2 className="text-sm font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                            Activation #{selectedActivation.id}
                          </h2>
                          <p className="mt-1 break-all text-[11px] text-white/35">
                            {activationSourceLabel(selectedActivation.sourceUrl)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] font-semibold text-white/45 capitalize">
                            {selectedActivation.mode}
                          </span>
                          {selectedActivation.requiresAccount && (
                            <span className="rounded-full px-2 py-1 text-[10px] font-bold" style={{ background: "rgba(251,146,60,0.12)", color: "#fdba74" }}>
                              Account required
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="grid sm:grid-cols-3 gap-2">
                        <div className="rounded-xl border border-white/7 bg-white/[0.02] p-3">
                          <p className="text-[10px] uppercase tracking-widest text-white/25">Materials</p>
                          <p className="mt-1 text-xs font-semibold text-white/70 capitalize">{selectedActivation.material}</p>
                        </div>
                        <div className="rounded-xl border border-white/7 bg-white/[0.02] p-3">
                          <p className="text-[10px] uppercase tracking-widest text-white/25">Scope</p>
                          <p className="mt-1 text-xs font-semibold text-white/70 capitalize">{selectedActivation.scope}</p>
                        </div>
                        <div className="rounded-xl border border-white/7 bg-white/[0.02] p-3">
                          <p className="text-[10px] uppercase tracking-widest text-white/25">Next action</p>
                          <p className="mt-1 text-xs font-semibold text-white/70">Evaluate leads</p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-white/7 bg-white/[0.02] p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock className="h-3.5 w-3.5" style={{ color: "#a78bfa" }} />
                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Status flow</p>
                        </div>
                        <div className="mb-3 flex gap-1 overflow-x-auto pb-1">
                          {(selectedActivation.statusFlow || []).map((step) => (
                            <div
                              key={step.id}
                              className="min-w-[96px] rounded-lg border px-2 py-1.5"
                              style={
                                step.active
                                  ? { background: "rgba(124,58,237,0.16)", borderColor: "rgba(124,58,237,0.4)" }
                                  : { background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.06)" }
                              }
                            >
                              <p className={step.active ? "text-[10px] font-bold text-violet-200" : "text-[10px] font-semibold text-white/35"}>
                                {step.label}
                              </p>
                            </div>
                          ))}
                        </div>
                        <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-white/25">Work plan</p>
                        <p className="break-words text-[11px] text-white/45 leading-relaxed">
                          {cleanScrapedText(selectedActivation.workPlan?.materials?.next) || "SCOUT will evaluate the selected leads and prepare outreach."}
                        </p>
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          {(selectedActivation.workPlan?.steps || []).slice(0, 4).map((step) => (
                            <div key={step} className="flex items-start gap-2 text-[11px] text-white/40">
                              <span className="mt-1.5 h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "#7c3aed" }} />
                              <span className="break-words">{cleanScrapedText(step)}</span>
                            </div>
                          ))}
                        </div>
                        {selectedActivation.workPlan?.deck_strategy && (
                          <div className="mt-3 rounded-lg border border-violet-400/15 bg-violet-400/5 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-violet-200/70">Deck strategy</p>
                            <p className="mt-1 text-[11px] font-semibold text-white/65">
                              {cleanScrapedText(selectedActivation.workPlan.deck_strategy.recommended_format)}
                            </p>
                            <p className="mt-1 text-[11px] text-white/40">
                              {cleanScrapedText(selectedActivation.workPlan.deck_strategy.positioning)}
                            </p>
                          </div>
                        )}
                        {(selectedActivation.workPlan?.safety_requirements || []).length > 0 && (
                          <div className="mt-3 rounded-lg border border-white/7 bg-black/10 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Sending guardrails</p>
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {(selectedActivation.workPlan?.safety_requirements || []).map((item) => (
                                <span
                                  key={item.key}
                                  className="rounded-full border px-2 py-1 text-[10px] font-semibold"
                                  style={
                                    item.required
                                      ? { borderColor: "rgba(251,146,60,0.25)", color: "#fdba74", background: "rgba(251,146,60,0.08)" }
                                      : { borderColor: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.35)", background: "rgba(255,255,255,0.02)" }
                                  }
                                >
                                  {item.label}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {selectedActivation.workPlan?.notification_policy && (
                          <div className="mt-3 rounded-lg border border-emerald-400/15 bg-emerald-400/5 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-200/70">Notifications</p>
                            <p className="mt-1 text-[11px] text-white/45">
                              {cleanScrapedText(selectedActivation.workPlan.notification_policy.reply)}
                            </p>
                            <p className="mt-1 text-[11px] text-white/35">
                              {cleanScrapedText(selectedActivation.workPlan.notification_policy.meeting)}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-xl border border-white/7 bg-white/[0.02] p-3">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Users className="h-3.5 w-3.5" style={{ color: "#34d399" }} />
                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Selected leads</p>
                        </div>
                        <span className="text-[10px] text-white/30">{selectedActivation.leadCount} total</span>
                      </div>
                      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                        {selectedActivation.leads.slice(0, 6).map((lead) => (
                          <div key={lead.id} className="rounded-lg border border-white/6 px-3 py-2" style={{ background: "rgba(255,255,255,0.02)" }}>
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-xs font-semibold text-white/75 truncate">{lead.company}</p>
                              {typeof lead.score === "number" && (
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(lead.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {lead.score}
                                </span>
                              )}
                            </div>
                            <p className="mt-1 line-clamp-2 break-words text-[11px] text-white/35">{activationLeadText(lead)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-white/8 px-4 py-6 text-center">
                    <p className="text-sm font-semibold text-white/40">SCOUT activity will appear here</p>
                    <p className="text-[11px] text-white/25 mt-1">Use Activate SCOUT on Results to create the first work queue item.</p>
                    <Link
                      href="/results?url="
                      className="mt-4 inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
                      style={{ color: "#FFB000", borderColor: "#FFB000" }}
                    >
                      <Target className="h-3.5 w-3.5" />
                      Activate SCOUT
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ── Two-panel layout ── */}
          <div className="flex gap-4" style={{ minHeight: "calc(100vh - 200px)" }}>

            {/* LEFT: Stage columns as inline row lists */}
            <div className="flex-1 flex flex-col gap-2 overflow-y-auto min-w-0">
              {STAGES.map((stage) => {
                const stageDeals = filtered.filter((d) => d.stage === stage);
                const meta = STAGE_META[stage];
                return (
                  <div key={stage}>
                    {/* Stage header row */}
                    <div className="flex items-center gap-2 px-3 py-2 mb-1">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{meta.label}</span>
                      <span className="text-[10px] text-white/25 ml-0.5">— {meta.desc}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded"
                        style={{ color: meta.color, background: `${meta.color}15` }}
                      >
                        {stageDeals.length}
                      </span>
                    </div>

                    {/* Inline deal rows */}
                    {stageDeals.length === 0 ? (
                      <div className="mx-1 mb-2 rounded-lg border border-dashed border-white/6 px-4 py-3">
                        <p className="text-[11px] text-white/20 italic">No deals in this stage</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-0.5 mb-2">
                        {stageDeals.map((deal) => {
                          const isSelected = deal.id === selectedId;
                          return (
                            <button
                              key={deal.id}
                              onClick={() => setSelectedId(deal.id)}
                              className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all group"
                              style={
                                isSelected
                                  ? { background: "rgba(124,58,237,0.12)", borderColor: "rgba(124,58,237,0.35)" }
                                  : { background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.05)" }
                              }
                            >
                              {/* Score ring */}
                              <div
                                className="h-7 w-7 rounded-full border flex items-center justify-center shrink-0"
                                style={{ borderColor: scoreColor(deal.score), background: `${scoreColor(deal.score)}10` }}
                              >
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(deal.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.score}
                                </span>
                              </div>

                              {/* Company + signal inline */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-sm font-semibold text-white truncate">{deal.company}</span>
                                  <span className="text-[10px] text-white/30 shrink-0">{deal.location}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: displayStageColor(deal), background: `${displayStageColor(deal)}15` }}
                                  >
                                    {displayStageLabel(deal)}
                                  </span>
                                </div>
                                <p className="text-[11px] text-white/40 truncate">{deal.signal}</p>
                              </div>

                              {/* Time + arrow */}
                              <div className="flex items-center gap-2 shrink-0">
                                <span className="text-[10px] text-white/20 font-mono hidden sm:block" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.updatedAt}
                                </span>
                                <ChevronRight
                                  className="h-3.5 w-3.5 transition-colors"
                                  style={{ color: isSelected ? "#a78bfa" : "rgba(255,255,255,0.15)" }}
                                />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* RIGHT: Deal detail + outreach draft */}
            <div
              className="w-[380px] xl:w-[420px] shrink-0 rounded-2xl border border-white/8 overflow-hidden flex flex-col"
              style={{ background: "rgba(255,255,255,0.025)", position: "sticky", top: "80px", maxHeight: "calc(100vh - 100px)" }}
            >
              {selected ? (
                <>
                  {/* Detail header */}
                  <div className="p-5 border-b border-white/8">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div>
                        <p className="text-base font-bold text-white mb-0.5" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                          {selected.company}
                        </p>
                        <div className="flex items-center gap-2 text-[11px] text-white/35">
                          <MapPin className="h-3 w-3" />
                          {selected.location}
                          <span className="text-white/15">·</span>
                          {selected.industry}
                        </div>
                      </div>
                      <div
                        className="h-10 w-10 rounded-full border flex items-center justify-center shrink-0"
                        style={{ borderColor: scoreColor(selected.score), background: `${scoreColor(selected.score)}12` }}
                      >
                        <span className="font-mono text-sm font-bold" style={{ color: scoreColor(selected.score), fontFamily: "'JetBrains Mono', monospace" }}>
                          {selected.score}
                        </span>
                      </div>
                    </div>

                    {/* Stage + contact inline */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <span
                        className="text-[10px] font-bold px-2 py-1 rounded-full"
                        style={{ color: displayStageColor(selected), background: `${displayStageColor(selected)}15`, border: `1px solid ${displayStageColor(selected)}25` }}
                      >
                        {displayStageLabel(selected)}
                      </span>
                      {selected.contact && (
                        <span className="text-[11px] text-white/40">
                          <span className="text-white/60 font-medium">{selected.contact}</span> · {selected.contactTitle}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Signal block */}
                  <div className="px-5 py-3 border-b border-white/6">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Trigger Signal</p>
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: selected.signalColor }} />
                      <div>
                        <p className="text-xs font-semibold mb-0.5" style={{ color: selected.signalColor }}>{selected.signalType}</p>
                        <p className="break-words text-[11px] leading-relaxed" style={{ color: "#FFB000" }}>{selected.signal}</p>
                      </div>
                    </div>
                    {selected.notes && (
                      <p className="mt-2 break-words border-t border-white/5 pt-2 text-[10px] italic leading-relaxed text-white/25">{selected.notes}</p>
                    )}
                  </div>

                  {/* Latest research */}
                  <div className="px-5 py-3 border-b border-white/6">
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Latest Research</p>
                      {selected.lastResearchedAt && (
                        <span className="text-[10px] text-white/25">
                          Checked {formatResearchTime(selected.lastResearchedAt)}
                        </span>
                      )}
                    </div>
                    {loadingResearch && !selected.researchUpdates ? (
                      <p className="text-[11px] leading-relaxed text-white/35">SCOUT is loading cited updates…</p>
                    ) : (selected.researchUpdates || []).length > 0 ? (
                      <div className="space-y-2">
                        {(selected.researchUpdates || []).slice(0, 3).map((update) => (
                          <div
                            key={update.id}
                            className="rounded-lg border p-2.5"
                            style={{ borderColor: "rgba(255,176,0,0.18)", background: "rgba(255,176,0,0.06)" }}
                          >
                            <div className="mb-1 flex items-center justify-between gap-2">
                              <p className="break-words text-[11px] font-semibold" style={{ color: "#FFB000" }}>
                                {cleanAndClampText(update.title, 120) || "Research update"}
                              </p>
                              {typeof update.significance_score === "number" && (
                                <span className="shrink-0 font-mono text-[10px]" style={{ color: "#FFB000" }}>
                                  {Math.round(update.significance_score * 100)}
                                </span>
                              )}
                            </div>
                            <p className="break-words text-[11px] leading-relaxed" style={{ color: "#FFB000" }}>
                              {cleanAndClampText(update.summary, 220)}
                            </p>
                            <div className="mt-1.5 flex items-center gap-2 text-[10px] text-white/25">
                              <Clock className="h-3 w-3" />
                              <span>{formatResearchTime(update.detected_at) || "recent"}</span>
                              {update.source_domain && (
                                <>
                                  <span>·</span>
                                  <span className="break-all">{update.source_domain}</span>
                                </>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] leading-relaxed text-white/35">
                        No material research updates yet. SCOUT will add cited changes as fresh signals arrive.
                      </p>
                    )}
                  </div>

                  {/* Outreach draft */}
                  <div className="flex-1 overflow-y-auto px-5 py-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Outreach Draft</p>
                      </div>
                      <button
                        onClick={copyDraft}
                        className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded transition-all"
                        style={
                          copied
                            ? { background: "rgba(52,211,153,0.12)", color: "#34d399" }
                            : { background: "rgba(124,58,237,0.12)", color: "#a78bfa" }
                        }
                      >
                        {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                        {copied ? "Copied!" : "Copy draft"}
                      </button>
                    </div>

                    {selected.outreachSubject && (
                      <div className="mb-2 p-2.5 rounded-lg" style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.18)" }}>
                        <p className="text-[10px] text-white/30 mb-0.5 uppercase tracking-wide">Subject</p>
                        <p className="text-xs font-semibold" style={{ color: "#FFB000" }}>{selected.outreachSubject}</p>
                      </div>
                    )}

                    {selected.outreachBody && (
                      <div className="p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <pre className="whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed text-white/55">
                          {selected.outreachBody}
                        </pre>
                      </div>
                    )}
                  </div>

                  {/* Action bar */}
                  <div className="p-4 border-t border-white/8 flex items-center gap-2">
                    {STAGES.indexOf(selected.stage) > 0 && (
                      <button
                        onClick={() => moveStage(selected.id, -1)}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg border transition-all"
                        style={{ borderColor: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.4)", background: "rgba(255,255,255,0.03)" }}
                      >
                        <ArrowLeft className="h-3 w-3" />
                        Back
                      </button>
                    )}
                    <button
                      onClick={() => {
                        copyDraft();
                        toast.success("Draft copied — ready to send");
                      }}
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg transition-all"
                      style={{ background: "rgba(124,58,237,0.2)", color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.3)" }}
                    >
                      <Mail className="h-3.5 w-3.5" />
                      Approve &amp; Copy
                    </button>
                    {STAGES.indexOf(selected.stage) < STAGES.length - 1 && (
                      <button
                        onClick={() => moveStage(selected.id, 1)}
                        className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg transition-all"
                        style={{ background: "#7c3aed", color: "#fff", border: "1px solid #7c3aed" }}
                      >
                        Advance
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <Target className="h-8 w-8 text-white/10 mb-3" />
                  <p className="text-sm text-white/25">Select a deal to see details and outreach draft</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
