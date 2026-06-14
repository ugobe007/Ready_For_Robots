/**
 * Pipeline — ReadyForRobots
 * Two-panel layout: left = inline deal rows grouped by stage, right = selected deal detail + outreach draft
 * Violet palette: #0d0520 bg · #7c3aed accent · cream text
 * Design: Linear/Raycast-inspired — dense, inline, data-forward
 */
import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  AlertTriangle, MapPin, Filter, ChevronRight, ChevronDown, ChevronUp,
  Copy, CheckCheck, ArrowRight, ArrowLeft, Mail,
  Users, Clock, Target, Newspaper, Send, Eye, MousePointerClick,
  Zap, RefreshCw
} from "lucide-react";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import ScoutActionBar from "@/components/ScoutActionBar";
import { Link, useSearch } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import {
  fetchWithTimeout,
  fetchWithTimeoutRetry,
  getApiBase,
  liveFetchInit,
  publicFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";
import { marketInsightForIndustry } from "@/lib/industryContext";
import { mapApiLeadToDeal, type ApiLead } from "@/lib/pipelineLeadMap";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import LeadShareBar from "@/components/LeadShareBar";

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
  shareSummary?: string;
  shareBlurb?: string;
  priorityTier?: string;
  robotTypesNeeded?: string[];
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
  projectTiming?: {
    label?: string;
    display_phrase?: string;
    source?: string;
    day_min?: number | null;
    day_max?: number | null;
    confidence?: number;
  };
  leadHighlights?: {
    specific_problem?: string | null;
    why_lead?: string[];
    procurement?: Record<string, unknown>;
    problem_size?: Record<string, unknown>;
    robot_categories?: string[];
    application_areas?: string[];
    agent_enrichment?: {
      rich_facts?: Array<{ claim?: string; evidence_span?: string }>;
      procurement_clues?: string[];
      timing_clues?: string[];
      ontology_gaps?: string[];
    };
  };
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

type ScoutAutomationLevel = "manual" | "assisted" | "auto";

interface UserSettings {
  scout_automation_level?: ScoutAutomationLevel;
  reply_forwarding_enabled?: boolean;
  reply_forward_email?: string | null;
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
  "Meeting Set":   { color: "#FFB000", dot: "#FFB000", label: "Meeting Set",   desc: "On the calendar" },
};

type UserBucket = "Hot Leads" | "Warm Leads" | "Monitoring";

const PIPELINE_HOT_SLOTS = 15;
const PIPELINE_WARM_SLOTS = 20;
const PIPELINE_MONITOR_SLOTS = 15;

const USER_BUCKETS: UserBucket[] = ["Hot Leads", "Warm Leads", "Monitoring"];

const USER_BUCKET_META: Record<UserBucket, { color: string; dot: string; desc: string; slotCap: number }> = {
  "Hot Leads":   { color: "#34d399", dot: "#34d399", desc: "High-confidence robot-ready opportunities", slotCap: PIPELINE_HOT_SLOTS },
  "Warm Leads":  { color: "#FFB000", dot: "#FFB000", desc: "Strong signals — qualify and track", slotCap: PIPELINE_WARM_SLOTS },
  "Monitoring":  { color: "#a78bfa", dot: "#a78bfa", desc: "Early signals SIGNAL is tracking", slotCap: PIPELINE_MONITOR_SLOTS },
};

const userBucketForDeal = (deal: Pick<Deal, "score" | "priorityTier">): UserBucket => {
  const tier = (deal.priorityTier || "").toUpperCase();
  if (tier === "HOT") return "Hot Leads";
  if (tier === "WARM") return "Warm Leads";
  if (tier === "COLD") return "Monitoring";
  if (deal.score >= 85) return "Hot Leads";
  if (deal.score >= 65) return "Warm Leads";
  return "Monitoring";
};

const userTierBadge = (deal: Pick<Deal, "score" | "priorityTier">) => {
  const tier = (deal.priorityTier || "").toUpperCase();
  if (tier === "HOT") return { label: "HOT", color: "#34d399" };
  if (tier === "WARM") return { label: "WARM", color: "#FFB000" };
  if (tier === "COLD") return { label: "MONITOR", color: "#a78bfa" };
  if (deal.score >= 85) return { label: "HOT", color: "#34d399" };
  if (deal.score >= 65) return { label: "WARM", color: "#FFB000" };
  return { label: "MONITOR", color: "#a78bfa" };
};

const scoreColor = (s: number) =>
  s >= 90 ? "#34d399" : s >= 75 ? "#a78bfa" : "#FFB000";

const statusLabel = (status: string) =>
  status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const displayStageLabel = (deal: Pick<Deal, "stage" | "signalType">, _adminView?: boolean) =>
  deal.stage === "New Signal" ? deal.signalType : stageLabel(deal.stage);

const displayStageColor = (deal: Pick<Deal, "stage" | "signalColor">) =>
  deal.stage === "New Signal" ? deal.signalColor : STAGE_META[deal.stage].color;

const stageLabel = (stage: Stage) => STAGE_META[stage].label;

const stageDesc = (stage: Stage) => STAGE_META[stage].desc;

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
  cleanAndClampText(lead.signal || lead.action, 160) || "Lead queued for SIGNAL evaluation.";

const formatMetric = (value?: number) =>
  typeof value === "number" ? new Intl.NumberFormat("en-US").format(value) : "—";

const DEFAULT_MARKET_SNIPPET: MarketSnippet = {
  label: "Market movement",
  headline: "SIGNAL is watching live buyer signals",
  detail: "As the pipeline loads, SIGNAL is looking for expansion, labor, budget, procurement, deployment, and partnership signals that indicate robot demand is moving.",
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

const scoutVerdictForDeal = (deal: Pick<Deal, "score">) => {
  if (deal.score >= 85) {
    return {
      headline: "High-confidence opportunity",
      detail: "SIGNAL rates timing, signal strength, and industry fit as strong — worth prioritizing now.",
      color: "#34d399",
    };
  }
  if (deal.score >= 65) {
    return {
      headline: "Meaningful buying pressure",
      detail: "SIGNAL sees real automation intent. Qualify and monitor before full outreach.",
      color: "#FFB000",
    };
  }
  return {
    headline: "Early signal — SIGNAL is watching",
    detail: "Activity is building. SIGNAL will flag when corroboration strengthens the case.",
    color: "#a78bfa",
  };
};

const panelSectionLabel = "text-[10px] font-bold uppercase tracking-[0.14em] text-violet-200/90";

type PipelineEntitlements = {
  plan: "anonymous" | "free" | "paid";
  pipeline_limit: number;
  visible_count: number;
  saved_limit: number | null;
  upgrade_url: string;
};

const PIPELINE_LIMIT_FREE = 50;
const PIPELINE_LIMIT_PAID = 50;
const PIPELINE_SESSION_KEY = "pipeline_feed_v2";
const PIPELINE_SESSION_TTL_MS = 2 * 60 * 60 * 1000;

function parsePipelineLeadIdFromSearch(search: string): number | null {
  const params = new URLSearchParams(search);
  const leadParam = params.get("lead");
  if (leadParam) {
    const id = Number.parseInt(leadParam, 10);
    if (Number.isFinite(id) && id > 0) return id;
  }
  return null;
}

/** Newsletter/homepage deep links use ?lead= or legacy #id. */
function resolvePipelineLeadId(search: string): number | null {
  const fromSearch = parsePipelineLeadIdFromSearch(search);
  if (fromSearch != null) return fromSearch;
  if (typeof window === "undefined") return null;
  const hash = window.location.hash.replace(/^#/, "").trim();
  if (hash) {
    const id = Number.parseInt(hash, 10);
    if (Number.isFinite(id) && id > 0) return id;
  }
  return null;
}
const PIPELINE_FRESH_MS = 90 * 1000;
const PIPELINE_TIMEOUT = 8_000;

type PipelineFeedPayload = {
  summary?: LeadSummary;
  leads?: ApiLead[];
  entitlements?: PipelineEntitlements;
};

function mapPipelineRows(apiRows: ApiLead[]): Deal[] {
  const mapped: Deal[] = [];
  for (const row of apiRows) {
    try {
      mapped.push(mapApiLeadToDeal(row) as Deal);
    } catch {
      /* skip malformed pipeline row */
    }
  }
  return mapped;
}

function mergePipelineFeedDeals(mapped: Deal[], prev: Deal[]): Deal[] {
  const deepLinkId =
    typeof window !== "undefined"
      ? resolvePipelineLeadId(window.location.search)
      : null;
  if (deepLinkId == null) return mapped;
  const pinned = prev.find((d) => d.id === deepLinkId);
  if (!pinned || mapped.some((d) => d.id === deepLinkId)) return mapped;
  return [pinned, ...mapped];
}

function applyPipelineFeed(
  payload: PipelineFeedPayload,
  setters: {
    setDeals: Dispatch<SetStateAction<Deal[]>>;
    setSelectedId: (fn: (prev: number | null) => number | null) => void;
    setSummary: (v: LeadSummary | null) => void;
    setEntitlements: (v: PipelineEntitlements | null) => void;
    setMarketSnippet: (v: MarketSnippet) => void;
  },
) {
  const rows = Array.isArray(payload.leads) ? payload.leads : [];
  if (payload.entitlements) setters.setEntitlements(payload.entitlements);
  if (payload.summary && ((payload.summary.total ?? 0) > 0 || (payload.summary.hot ?? 0) > 0)) {
    setters.setSummary(payload.summary);
  }
  if (rows.length > 0) {
    const mapped = mapPipelineRows(rows);
    setters.setDeals((prev) => mergePipelineFeedDeals(mapped, prev));
    const deepLinkId =
      typeof window !== "undefined"
        ? resolvePipelineLeadId(window.location.search)
        : null;
    setters.setSelectedId((prev) => {
      if (deepLinkId != null) return deepLinkId;
      return prev && mapped.some((d) => d.id === prev) ? prev : mapped[0]?.id ?? null;
    });
    setters.setMarketSnippet(marketSnippetFromDeals(mapped));
    return true;
  }
  return false;
}
const HUBSPOT_CONNECT_PATH = "/integrations/hubspot";
const HUBSPOT_SIGNUP_PATH = `/signup?intent=hubspot&next=${encodeURIComponent("/integrations/hubspot")}`;

function HubSpotCtaLink({
  connected,
  hasSession,
  className = "px-4 py-2.5 text-sm",
}: {
  connected?: boolean;
  hasSession: boolean;
  className?: string;
}) {
  return (
    <Link
      href={hasSession ? HUBSPOT_CONNECT_PATH : HUBSPOT_SIGNUP_PATH}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border font-bold transition-all hover:bg-[#FFB000]/[0.06] ${className}`}
      style={{ borderColor: "#FFB000", color: "#FFB000", background: "transparent" }}
    >
      {connected ? (
        <>
          <CheckCheck className="h-4 w-4" />
          HubSpot connected
        </>
      ) : (
        "Connect to Hubspot"
      )}
    </Link>
  );
}

const panelPlanFor = (isAdmin: boolean, entitlements: PipelineEntitlements | null): PipelineEntitlements["plan"] =>
  isAdmin ? "paid" : (entitlements?.plan ?? "anonymous");

const SEARCH_TERM_ALIASES: Record<string, string[]> = {
  restaurant: ["restaurant", "restaurants", "food service", "qsr", "fast food", "fast casual", "dining", "kitchen", "catering", "foodservice"],
  hospitality: ["hospitality", "hotel", "housekeeping", "room service"],
  logistics: ["logistics", "warehouse", "fulfillment", "distribution", "3pl"],
  manufacturing: ["manufacturing", "factory", "packaging", "assembly"],
};

function dealMatchesSearchQuery(deal: Deal, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const blob = `${deal.company} ${deal.industry} ${deal.signal || ""} ${deal.shareSummary || ""}`.toLowerCase();
  const terms = SEARCH_TERM_ALIASES[q] || [q];
  return terms.some((term) => blob.includes(term));
}

async function fetchLeadsBySearch(base: string, query: string, headers?: HeadersInit): Promise<Deal[]> {
  const params = new URLSearchParams({
    search: query,
    limit: String(PIPELINE_LIMIT_PAID),
    sort: "score",
    exclude_junk: "true",
  });
  const res = await fetchWithTimeout(
    `${base}/api/leads?${params}`,
    liveFetchInit({ headers }),
    30_000,
  );
  if (!res.ok) return [];
  const rows = (await res.json()) as ApiLead[];
  if (!Array.isArray(rows)) return [];
  const mapped: Deal[] = [];
  for (const row of rows) {
    try {
      mapped.push(mapApiLeadToDeal(row) as Deal);
    } catch {
      /* skip malformed row */
    }
  }
  return mapped;
}

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
    <div className="rounded-xl border border-white/8 px-3 py-2" style={{ background: "rgba(255,255,255,0.03)" }}>
      <div className="mb-1 flex items-center justify-between gap-2">
        <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-white/28">{label}</p>
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color, boxShadow: `0 0 12px ${color}66` }} />
      </div>
      <p className="font-mono text-xl font-bold leading-none" style={{ color, fontFamily: "'JetBrains Mono', monospace" }}>
        {value}
      </p>
      <p className="mt-1 text-[10px] leading-snug text-white/35">{sub}</p>
    </div>
  );
}

export default function Pipeline() {
  const { session } = useAuth();
  const search = useSearch();
  const deepLinkLeadId = useMemo(() => resolvePipelineLeadId(search), [search]);
  const [isAdmin, setIsAdmin] = useState(false);
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
  const [advancingLeadId, setAdvancingLeadId] = useState<number | null>(null);
  const [automationLevel, setAutomationLevel] = useState<ScoutAutomationLevel>("assisted");
  const [activationControlBusy, setActivationControlBusy] = useState(false);
  const [messageNote, setMessageNote] = useState("");
  const [timingNote, setTimingNote] = useState("");
  const [cadenceNote, setCadenceNote] = useState("");
  const [loadErr, setLoadErr] = useState("");
  const [serverSearchDeals, setServerSearchDeals] = useState<Deal[]>([]);
  const [serverSearchLoading, setServerSearchLoading] = useState(false);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [activationErr, setActivationErr] = useState("");
  // SIGNAL bulk outreach state
  const [scoutStats, setScoutStats] = useState<{
    total: number; drafted: number; sent: number; opened: number; clicked: number; replied: number;
  } | null>(null);
  const [scoutBusy, setScoutBusy] = useState<"draft" | "send" | null>(null);
  const [scoutConfirm, setScoutConfirm] = useState<"draft" | "send" | null>(null);
  const [sendingLeadId, setSendingLeadId] = useState<number | null>(null);
  const [developingLeadId, setDevelopingLeadId] = useState<number | null>(null);
  // Draft preview email modal
  const [previewOpen, setPreviewOpen] = useState(false);
  const [intelligenceOpen, setIntelligenceOpen] = useState(true);
  const [researchOpen, setResearchOpen] = useState(false);
  const [entitlements, setEntitlements] = useState<PipelineEntitlements | null>(null);
  const [hubspotIntegration, setHubspotIntegration] = useState<{
    connected: boolean;
    entitled: boolean;
  } | null>(null);
  const [deepLinkLoadFailed, setDeepLinkLoadFailed] = useState(false);
  const [deepLinkRetryNonce, setDeepLinkRetryNonce] = useState(0);
  const dealsRef = useRef(deals);
  dealsRef.current = deals;
  const deepLinkInflightRef = useRef<number | null>(null);

  const retryDeepLink = () => {
    deepLinkInflightRef.current = null;
    setDeepLinkLoadFailed(false);
    setDeepLinkRetryNonce((n) => n + 1);
  };

  const panelPlan = panelPlanFor(isAdmin, entitlements);
  const showFullPanel = panelPlan === "paid";
  const showStandardPanel = panelPlan === "free";

  useEffect(() => {
    setIntelligenceOpen(true);
    setResearchOpen(false);
  }, [selectedId]);

  useEffect(() => {
    if (!session?.access_token) {
      setHubspotIntegration(null);
      return;
    }
    const token = session.access_token;
    let cancelled = false;
    void fetch(
      `${getApiBase()}/api/integrations`,
      liveFetchInit({ headers: { ...authHeader(token) } }),
    )
      .then(async (res) => {
        if (cancelled || !res.ok) return;
        const payload = (await res.json()) as {
          integrations?: Array<{ provider: string; connected?: boolean; entitled?: boolean }>;
        };
        const hubspot = (payload.integrations || []).find((row) => row.provider === "hubspot");
        if (hubspot) {
          setHubspotIntegration({
            connected: Boolean(hubspot.connected),
            entitled: hubspot.entitled !== false,
          });
        }
      })
      .catch(() => {
        if (!cancelled) setHubspotIntegration(null);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  useEffect(() => {
    const base = getApiBase();
    let cancelled = false;
    setLoadErr("");

    const feedSetters = {
      setDeals,
      setSelectedId,
      setSummary,
      setEntitlements,
      setMarketSnippet,
    };

    const cachedEntry = readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_SESSION_TTL_MS);
    const paintedFromCache = cachedEntry ? applyPipelineFeed(cachedEntry.data, feedSetters) : false;
    setLoadingLeads(!paintedFromCache);
    setLoadingSummary(!paintedFromCache);

    const loadPipeline = async (token?: string) => {
      const headers = token ? authHeader(token) : undefined;
      const res = await fetchWithTimeout(
        `${base}/api/leads/pipeline`,
        publicFetchInit({ headers }),
        PIPELINE_TIMEOUT,
        { publicCache: true },
      );
      if (!res.ok) throw new Error("Could not load pipeline");
      const payload = (await res.json()) as PipelineFeedPayload;
      if (cancelled) return;
      writeSurfaceCache(PIPELINE_SESSION_KEY, payload);
      const painted = applyPipelineFeed(payload, feedSetters);
      if (!painted && (payload.summary?.hot ?? 0) > 0) {
        setDeals([]);
        setSelectedId(null);
      } else if (!painted) {
        setDeals([]);
        setSelectedId(null);
      }
    };

    void loadPipeline(session?.access_token)
      .catch((e) => {
        if (cancelled) return;
        if (!paintedFromCache) {
          const aborted = e instanceof DOMException && e.name === "AbortError";
          setLoadErr(
            aborted
              ? "Pipeline request timed out — try refreshing in a moment."
              : e instanceof Error
                ? e.message
                : "Could not load pipeline",
          );
          setDeals([]);
          setSelectedId(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingLeads(false);
          setLoadingSummary(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setDeepLinkLoadFailed(false);
  }, [deepLinkLeadId]);

  useEffect(() => {
    if (!deepLinkLeadId || loadingLeads) return;
    const onOnline = () => retryDeepLink();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [deepLinkLeadId, loadingLeads]);

  // Deep link from newsletter / homepage (?lead=123 or legacy #123).
  useEffect(() => {
    if (!deepLinkLeadId || loadingLeads) return;

    setSelectedId(deepLinkLeadId);
    setDeepLinkLoadFailed(false);

    if (dealsRef.current.some((d) => d.id === deepLinkLeadId)) {
      deepLinkInflightRef.current = null;
      return;
    }
    if (deepLinkInflightRef.current === deepLinkLeadId) return;

    deepLinkInflightRef.current = deepLinkLeadId;
    let cancelled = false;
    void (async () => {
      const base = getApiBase();
      try {
        const response = await fetchWithTimeoutRetry(
          `${base}/api/leads/by-id/${deepLinkLeadId}`,
          publicFetchInit(),
          12_000,
          { publicCache: true, retries: 2, retryDelayMs: 1200 },
        );
        if (cancelled) return;
        if (!response.ok) {
          deepLinkInflightRef.current = null;
          setDeepLinkLoadFailed(true);
          return;
        }
        const lead = (await response.json()) as ApiLead;
        const mapped = mapApiLeadToDeal(lead) as Deal;
        if (cancelled) return;
        deepLinkInflightRef.current = null;
        setDeepLinkLoadFailed(false);
        setDeals((prev) => {
          if (prev.some((d) => d.id === deepLinkLeadId)) return prev;
          return [mapped, ...prev];
        });
      } catch {
        if (!cancelled) {
          deepLinkInflightRef.current = null;
          setDeepLinkLoadFailed(true);
        }
      }
    })();

    return () => {
      cancelled = true;
      if (deepLinkInflightRef.current === deepLinkLeadId) {
        deepLinkInflightRef.current = null;
      }
    };
  }, [deepLinkLeadId, loadingLeads, deepLinkRetryNonce]);

  // Background entitlement refresh when auth resolves — skip if feed is already fresh.
  useEffect(() => {
    const token = session?.access_token;
    if (!token) return;
    const fresh = readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_FRESH_MS);
    if (fresh?.data?.leads?.length) return;
    const base = getApiBase();
    let cancelled = false;
    void fetchWithTimeout(
      `${base}/api/leads/pipeline`,
      publicFetchInit({ headers: authHeader(token) }),
      PIPELINE_TIMEOUT,
      { publicCache: true },
    )
      .then(async (res) => {
        if (cancelled || !res.ok) return;
        const payload = (await res.json()) as PipelineFeedPayload;
        writeSurfaceCache(PIPELINE_SESSION_KEY, payload);
        applyPipelineFeed(payload, {
          setDeals,
          setSelectedId,
          setSummary,
          setEntitlements,
          setMarketSnippet,
        });
      })
      .catch(() => { /* keep cached/anonymous feed */ });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  // Auth-only extras — do not re-fetch public leads when Supabase session resolves.
  useEffect(() => {
    const base = getApiBase();
    let cancelled = false;
    const token = session?.access_token;
    const authHdr = authHeader(token);

    setLoadingActivations(true);
    setActivationErr("");

    if (!token) {
      setIsAdmin(false);
      setActivations([]);
      setSelectedActivationId(null);
      setLoadingActivations(false);
      return () => { cancelled = true; };
    }

    Promise.allSettled([
      fetchWithTimeout(`${base}/api/user/me`, { headers: authHdr }, 8_000),
      fetchWithTimeout(`${base}/api/user/settings`, { headers: authHdr }, 8_000),
    ]).then(async ([meResult, settingsResult]) => {
      if (cancelled) return;

      let admin = false;
      try {
        if (meResult.status === "fulfilled" && meResult.value?.ok) {
          const me = (await meResult.value.json()) as { is_admin?: boolean };
          admin = Boolean(me.is_admin);
          setIsAdmin(admin);
        }
      } catch {
        setIsAdmin(false);
      }

      try {
        if (admin) {
          const fingerprint = encodeURIComponent(scoutFingerprint());
          const activationsRes = await fetchWithTimeout(
            `${base}/api/scout/activations?fingerprint=${fingerprint}&limit=6`,
            { headers: authHdr },
            8_000,
          );
          if (activationsRes.ok) {
            const payload = (await activationsRes.json()) as { activations?: ScoutActivation[] };
            const rows = Array.isArray(payload.activations) ? payload.activations : [];
            setActivations(rows);
            setSelectedActivationId(rows[0]?.id ?? null);
          } else {
            setActivations([]);
          }
        } else {
          setActivations([]);
          setSelectedActivationId(null);
        }
      } catch (e) {
        if (admin) {
          setActivationErr(e instanceof Error ? e.message : "Could not load SIGNAL activations");
        }
        setActivations([]);
      } finally {
        if (!cancelled) setLoadingActivations(false);
      }

      try {
        if (admin && settingsResult.status === "fulfilled" && settingsResult.value?.ok) {
          const settings = (await settingsResult.value.json()) as UserSettings;
          if (settings.scout_automation_level) setAutomationLevel(settings.scout_automation_level);
        }
      } catch { /* non-critical */ }
    });

    return () => { cancelled = true; };
  }, [session?.access_token]);

  // Lazy detail enrichment when a slim pipeline row is selected — deferred so list paint stays fast.
  useEffect(() => {
    if (!selectedId) return;
    const existing = deals.find((deal) => deal.id === selectedId);
    if (existing?.leadHighlights) return;
    const base = getApiBase();
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void (async () => {
        setLoadingResearch(true);
        try {
          const response = await fetchWithTimeout(
            `${base}/api/leads/by-id/${selectedId}`,
            publicFetchInit(),
            8_000,
            { publicCache: true },
          );
          if (!response.ok) throw new Error(await response.text());
          const lead = (await response.json()) as ApiLead;
          const mapped = mapApiLeadToDeal(lead) as Deal;
          if (!cancelled) {
            setDeals((prev) => {
              if (prev.some((deal) => deal.id === selectedId)) {
                return prev.map((deal) => (deal.id === selectedId ? { ...deal, ...mapped } : deal));
              }
              return [mapped, ...prev];
            });
          }
        } catch {
          // Research is additive; keep the core pipeline usable if detail enrichment misses.
        } finally {
          if (!cancelled) setLoadingResearch(false);
        }
      })();
    }, 120);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  // Depend only on selectedId, not deals, to prevent re-firing on every deals update.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  // Load SIGNAL stats once when authenticated admin
  useEffect(() => {
    if (session?.access_token && isAdmin) void loadScoutStats();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token, isAdmin]);

  useEffect(() => {
    const q = industryQuery.trim() || (filter !== "All" ? filter : "");
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    if (!q || q.toLowerCase() === "all") {
      setServerSearchDeals([]);
      setServerSearchLoading(false);
      return;
    }
    setServerSearchLoading(true);
    setServerSearchDeals([]);
    searchDebounceRef.current = setTimeout(() => {
      const base = getApiBase();
      const headers = session?.access_token ? authHeader(session.access_token) : undefined;
      void fetchLeadsBySearch(base, q, headers)
        .then((rows) => setServerSearchDeals(rows))
        .catch(() => setServerSearchDeals([]))
        .finally(() => setServerSearchLoading(false));
    }, 350);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [industryQuery, filter, session?.access_token]);

  const industries = Array.from(new Set(deals.map((d) => d.industry).filter(Boolean))).sort();
  const activeSearchQuery = industryQuery.trim() || (filter !== "All" ? filter : "");
  const hasActiveSearch = Boolean(activeSearchQuery);
  const clientSearchMatches = useMemo(
    () => (hasActiveSearch ? deals.filter((d) => dealMatchesSearchQuery(d, activeSearchQuery)) : deals),
    [deals, hasActiveSearch, activeSearchQuery],
  );
  const filtered = hasActiveSearch
    ? serverSearchDeals.length > 0
      ? serverSearchDeals
      : serverSearchLoading
        ? []
        : clientSearchMatches
    : deals;
  const pendingDeepLink =
    selectedId != null &&
    deepLinkLeadId === selectedId &&
    !filtered.some((d) => d.id === selectedId);
  const effectiveSelectedId =
    selectedId != null && (filtered.some((d) => d.id === selectedId) || pendingDeepLink)
      ? selectedId
      : (filtered[0]?.id ?? null);
  const selected = filtered.find((d) => d.id === effectiveSelectedId) ?? null;
  const selectedActivation = activations.find((a) => a.id === selectedActivationId) ?? activations[0] ?? null;

  const moveStage = (id: number, direction: 1 | -1) => {
    setDeals((prev) =>
      prev.map((d) => {
        if (d.id !== id) return d;
        const idx = STAGES.indexOf(d.stage);
        const next = STAGES[idx + direction];
        if (!next) return d;
        toast.success(`Moved "${d.company}" to ${stageLabel(next)}`);
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

  const handleSaveLead = async (deal: Deal) => {
    if (!session?.access_token) {
      const next = `/pipeline?lead=${deal.id}`;
      window.location.href = `/signup?next=${encodeURIComponent(next)}`;
      return;
    }
    setAdvancingLeadId(deal.id);
    const base = getApiBase();
    const headers = { ...authHeader(session.access_token), "Content-Type": "application/json" };
    try {
      const createResponse = await fetch(
        `${base}/api/crm/accounts`,
        liveFetchInit({
          method: "POST",
          headers,
          body: JSON.stringify({
            company_id: deal.id,
            name: deal.company,
            industry: deal.industry,
          }),
        }),
      );
      if (!createResponse.ok) {
        const errText = await createResponse.text();
        try {
          const parsed = JSON.parse(errText) as { detail?: { code?: string; message?: string } | string };
          const detail = parsed.detail;
          if (typeof detail === "object" && detail?.code === "saved_leads_limit") {
            toast.error(detail.message || "Free workspace lead limit reached.");
            return;
          }
        } catch {
          /* not JSON */
        }
        throw new Error(errText);
      }
      setDeals((prev) => prev.map((d) => (d.id === deal.id ? { ...d, stage: "Qualified", updatedAt: "just now" } : d)));
      toast.success("SIGNAL saved this lead to your workspace.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save lead with SIGNAL");
    } finally {
      setAdvancingLeadId(null);
    }
  };

  const handleAdvanceLead = async (deal: Deal) => {
    if (!isAdmin) {
      await handleSaveLead(deal);
      return;
    }
    if (!session?.access_token) {
      const next = `/pipeline?lead=${deal.id}`;
      window.location.href = `/signup?next=${encodeURIComponent(next)}`;
      return;
    }
    setAdvancingLeadId(deal.id);
    const base = getApiBase();
    const headers = { ...authHeader(session.access_token), "Content-Type": "application/json" };
    try {
      const createResponse = await fetch(
        `${base}/api/crm/accounts`,
        liveFetchInit({
          method: "POST",
          headers,
          body: JSON.stringify({
            company_id: deal.id,
            name: deal.company,
            industry: deal.industry,
          }),
        }),
      );
      if (!createResponse.ok) throw new Error(await createResponse.text());
      const account = (await createResponse.json()) as { id: string };
      const patchResponse = await fetch(
        `${base}/api/crm/accounts/${account.id}`,
        liveFetchInit({
          method: "PATCH",
          headers,
          body: JSON.stringify({
            outreach_draft: deal.outreachBody || "",
            outreach_stage: automationLevel === "manual" ? "draft_approved" : "draft_ready",
          }),
        }),
      );
      if (!patchResponse.ok) throw new Error(await patchResponse.text());

      if (automationLevel === "auto" && deal.contact) {
        const sendResponse = await fetch(
          `${base}/api/crm/accounts/${account.id}/send-outreach`,
          liveFetchInit({
            method: "POST",
            headers,
            body: JSON.stringify({
              contact_email: deal.contact,
              subject: deal.outreachSubject,
              outreach_draft: deal.outreachBody,
              send_identity: "scout",
            }),
          }),
        );
        if (!sendResponse.ok) throw new Error(await sendResponse.text());
        setDeals((prev) => prev.map((d) => (d.id === deal.id ? { ...d, stage: "Outreach Sent", updatedAt: "just now" } : d)));
        toast.success("Cal sent the outreach. Replies will return to the Sales Console and notify you.");
        return;
      }

      setDeals((prev) => prev.map((d) => (d.id === deal.id ? { ...d, stage: "Draft Ready", updatedAt: "just now" } : d)));
      if (automationLevel === "manual") {
        copyDraft();
        toast.success("Lead captured in CRM. Draft approved for manual send.");
      } else if (!deal.contact) {
        toast.success("Lead captured in CRM. Add a recipient email before Cal sends.");
      } else {
        toast.success("Lead captured in CRM. Cal is ready when you approve send.");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not advance lead with SIGNAL");
    } finally {
      setAdvancingLeadId(null);
    }
  };

  const controlActivation = async (action: "pause" | "resume" | "update_plan") => {
    if (!selectedActivation || !session?.access_token) {
      toast.info("Sign in to control SIGNAL activity.");
      return;
    }
    setActivationControlBusy(true);
    try {
      const response = await fetch(
        `${getApiBase()}/api/scout/activations/${selectedActivation.id}/control`,
        liveFetchInit({
          method: "PATCH",
          headers: { ...authHeader(session.access_token), "Content-Type": "application/json" },
          body: JSON.stringify({
            action,
            message_note: messageNote,
            timing_note: timingNote,
            cadence_note: cadenceNote,
          }),
        }),
      );
      if (!response.ok) throw new Error(await response.text());
      const updated = (await response.json()) as ScoutActivation;
      setActivations((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setSelectedActivationId(updated.id);
      toast.success(action === "pause" ? "SIGNAL paused for review." : action === "resume" ? "SIGNAL resumed in approval-gated mode." : "SIGNAL plan updated.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not update SIGNAL activity");
    } finally {
      setActivationControlBusy(false);
    }
  };

  // Load Cal outreach summary (cached snapshot first — never block on full prospect rebuild)
  const loadScoutStats = async () => {
    if (!session?.access_token) return;
    const base = getApiBase();
    const hdrs = liveFetchInit({ headers: authHeader(session.access_token) });
    try {
      const snap = await fetch(`${base}/api/admin/snapshot/section/cal`, hdrs);
      if (snap.ok) {
        const patch = await snap.json() as { data?: { summary?: typeof scoutStats } };
        if (patch.data?.summary) {
          setScoutStats(patch.data.summary);
          return;
        }
      }
      const r = await fetch(`${base}/api/admin/cal/draft-status?include_prospects=false`, hdrs);
      if (r.ok) {
        const d = await r.json() as { summary?: typeof scoutStats };
        setScoutStats(d.summary ?? null);
      }
    } catch { /* advisory */ }
  };

  const runScoutDraftAll = async () => {
    if (!session?.access_token) return;
    setScoutBusy("draft");
    setScoutConfirm(null);
    const base = getApiBase();
    try {
      const r = await fetch(`${base}/api/admin/scout/bulk-activate`, liveFetchInit({
        method: "POST",
        headers: { ...authHeader(session.access_token), "Content-Type": "application/json" },
      }));
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json() as { activated: number };
      toast.success(`Cal drafted ${d.activated} emails.`);
      await loadScoutStats();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setScoutBusy(null);
    }
  };

  const runScoutSendAll = async () => {
    if (!session?.access_token) return;
    setScoutBusy("send");
    setScoutConfirm(null);
    const base = getApiBase();
    try {
      const r = await fetch(`${base}/api/admin/scout/bulk-send`, liveFetchInit({
        method: "POST",
        headers: { ...authHeader(session.access_token), "Content-Type": "application/json" },
      }));
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json() as { sent: number };
      toast.success(`Cal sent ${d.sent} emails.`);
      await loadScoutStats();
      setDeals((prev) => prev.map((d2) => d2.stage === "Draft Ready" ? { ...d2, stage: "Outreach Sent" as Stage, updatedAt: "just now" } : d2));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Send failed");
    } finally {
      setScoutBusy(null);
    }
  };

  const sendOneLead = async (deal: Deal) => {
    if (!session?.access_token) {
      toast.info("Sign in to send outreach.");
      return;
    }
    if (!deal.contact) {
      toast.error("No contact email for this lead.");
      return;
    }
    setSendingLeadId(deal.id);
    const base = getApiBase();
    const headers = { ...authHeader(session.access_token), "Content-Type": "application/json" };
    try {
      // First create/ensure CRM account
      const createRes = await fetch(`${base}/api/crm/accounts`, liveFetchInit({
        method: "POST", headers,
        body: JSON.stringify({ company_id: deal.id, name: deal.company, industry: deal.industry }),
      }));
      if (!createRes.ok) throw new Error(await createRes.text());
      const acct = (await createRes.json()) as { id: string };
      // Save draft
      await fetch(`${base}/api/crm/accounts/${acct.id}`, liveFetchInit({
        method: "PATCH", headers,
        body: JSON.stringify({ outreach_draft: deal.outreachBody, outreach_stage: "draft_approved" }),
      }));
      // Send
      const sendRes = await fetch(`${base}/api/crm/accounts/${acct.id}/send-outreach`, liveFetchInit({
        method: "POST", headers,
        body: JSON.stringify({ contact_email: deal.contact, subject: deal.outreachSubject, outreach_draft: deal.outreachBody, send_identity: "scout" }),
      }));
      if (!sendRes.ok) throw new Error(await sendRes.text());
      setDeals((prev) => prev.map((d) => d.id === deal.id ? { ...d, stage: "Outreach Sent" as Stage, updatedAt: "just now" } : d));
      toast.success(`Cal sent the email to ${deal.contact}.`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Send failed");
    } finally {
      setSendingLeadId(null);
    }
  };

  const developLeadWithScout = async (deal: Deal) => {
    setDevelopingLeadId(deal.id);
    const base = getApiBase();
    try {
      const response = await fetch(`${base}/api/scout/develop-lead`, liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fingerprint: scoutFingerprint(),
          company_id: deal.id,
          refresh_inference: true,
        }),
      }));
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json() as {
        brief?: {
          draft_subject?: string;
          draft_body?: string;
          share_summary?: string;
          sales_angle?: string;
          timing_label?: string;
          talk_track?: string[];
          robot_fit?: string[];
        };
      };
      const brief = data.brief;
      if (!brief) throw new Error("No development brief returned");
      setDeals((prev) =>
        prev.map((d) =>
          d.id === deal.id
            ? {
                ...d,
                outreachSubject: brief.draft_subject || d.outreachSubject,
                outreachBody: brief.draft_body || d.outreachBody,
                shareSummary: brief.share_summary || d.shareSummary,
                stage: brief.draft_body ? ("Draft Ready" as Stage) : d.stage,
                updatedAt: "just now",
                leadHighlights: {
                  ...d.leadHighlights,
                  specific_problem: brief.sales_angle || d.leadHighlights?.specific_problem,
                  why_lead: brief.talk_track || d.leadHighlights?.why_lead,
                },
                projectTiming: brief.timing_label
                  ? { display_phrase: brief.timing_label, label: brief.timing_label, source: "scout" }
                  : d.projectTiming,
                robotTypesNeeded: brief.robot_fit?.length ? brief.robot_fit : d.robotTypesNeeded,
              }
            : d,
        ),
      );
      toast.success("SIGNAL developed this lead — inference, brief, and Cal draft are ready.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "SIGNAL could not develop this lead");
    } finally {
      setDevelopingLeadId(null);
    }
  };

  const dbTotal = summary?.companies_in_database ?? summary?.total ?? (loadingSummary ? undefined : filtered.length);
  const hotDeals = summary?.hot ?? (loadingSummary ? undefined : filtered.filter((d) => d.score >= 85).length);
  const warmDeals = summary?.warm ?? (loadingSummary ? undefined : filtered.filter((d) => d.score >= 65 && d.score < 85).length);
  const visibleDeals = filtered.length;
  const filteredHot = filtered.filter((d) => d.score >= 85).length;
  const filteredWarm = filtered.filter((d) => d.score >= 65 && d.score < 85).length;
  const queuedActivations = activations.filter((a) => ["queued", "evaluating", "drafted", "awaiting_approval"].includes(a.status)).length;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-20 pb-6 px-4 lg:px-6">
        <div className="max-w-[1500px] mx-auto flex flex-col gap-4">
          {isAdmin && <AdminNav />}

          {/* ── Top bar ── */}
          {loadErr && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/90">
              {loadErr}
            </div>
          )}
          {!loadingLeads && !loadErr && !hasActiveSearch && filtered.length === 0 && (
            <div className="rounded-lg border border-violet-400/25 bg-violet-400/8 px-3 py-2 text-xs text-violet-100/85">
              Pipeline data is syncing from the database. Reload in a moment if tiers still look empty.
            </div>
          )}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5" style={{ color: "#a78bfa" }}>SIGNAL</p>
                <h1 className="font-extrabold text-white text-xl" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  {isAdmin ? "Active Signals → Live Pipeline" : "Sales Pipeline"}
                </h1>
                <p className="text-[11px] text-white/35 mt-0.5 max-w-md">
                  {isAdmin
                    ? "Authoritative database counts up top. Cal outreach controls below."
                    : panelPlan === "anonymous"
                      ? `Preview ${entitlements?.pipeline_limit ?? 12} SIGNAL-ranked leads — sign up for ${PIPELINE_LIMIT_FREE} and put SIGNAL on your workspace.`
                      : panelPlan === "free"
                        ? `Your free workspace: ${entitlements?.visible_count ?? deals.length} of ${entitlements?.pipeline_limit ?? PIPELINE_LIMIT_FREE} live leads · save up to ${entitlements?.saved_limit ?? 5}.`
                        : `${PIPELINE_HOT_SLOTS} hot · ${PIPELINE_WARM_SLOTS} warm · ${PIPELINE_MONITOR_SLOTS} monitoring — ranked by buyer intent and timing.`}
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
                placeholder="Search industry, company, or signal…"
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

          <section className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            <PipelineMetric
              label={isAdmin ? "Database total" : "Market watchlist"}
              value={formatMetric(dbTotal)}
              sub={loadingSummary
                ? "Refreshing market totals..."
                : `${formatMetric(summary?.signals_in_database ?? summary?.total_signals)} scored buying signals`}
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
              label={isAdmin ? "Working slice" : "In this view"}
              value={formatMetric(visibleDeals)}
              sub={isAdmin
                ? `${formatMetric(queuedActivations)} SIGNAL activations queued`
                : hasActiveSearch
                  ? `${formatMetric(filteredHot)} hot · ${formatMetric(filteredWarm)} warm matching search`
                  : `${formatMetric(hotDeals)} hot · ${formatMetric(warmDeals)} warm leads loaded`}
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

          {/* ── SIGNAL activation queue (admin only) ── */}
          {isAdmin && (
          <div className="rounded-2xl border border-white/8 overflow-hidden" style={{ background: "rgba(255,255,255,0.025)" }}>
            <div className="flex flex-col xl:flex-row">
              <div className="xl:w-[360px] border-b xl:border-b-0 xl:border-r border-white/8">
                <div className="px-4 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#a78bfa" }}>SIGNAL Queue</p>
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
                      <p className="text-xs font-semibold text-white/45">No SIGNAL activations yet</p>
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
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <h2 className="text-base font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                            Activation #{selectedActivation.id}
                          </h2>
                          <p className="mt-1 break-all text-xs text-white/40">
                            {activationSourceLabel(selectedActivation.sourceUrl)}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 shrink-0">
                          <span className="rounded-full border border-white/10 px-2.5 py-1 text-xs font-semibold text-white/50 capitalize">
                            {selectedActivation.mode}
                          </span>
                          {selectedActivation.requiresAccount && (
                            <span className="rounded-full px-2.5 py-1 text-xs font-bold" style={{ background: "rgba(251,146,60,0.12)", color: "#fdba74" }}>
                              Account required
                            </span>
                          )}
                          <HubSpotCtaLink
                            connected={hubspotIntegration?.connected}
                            hasSession={Boolean(session?.access_token)}
                          />
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
                        <p className="mb-2 text-xs font-bold uppercase tracking-widest text-white/30">Work plan</p>
                        <p className="break-words text-sm text-white/55 leading-relaxed">
                          {cleanScrapedText(selectedActivation.workPlan?.materials?.next) || "SIGNAL will evaluate the selected leads and prepare Cal outreach."}
                        </p>
                        {((selectedActivation.workPlan?.steps || []).length > 0
                          || selectedActivation.workPlan?.deck_strategy
                          || (selectedActivation.workPlan?.safety_requirements || []).length > 0
                          || selectedActivation.workPlan?.notification_policy) && (
                          <details className="mt-3 rounded-lg border border-white/7 bg-black/10 group">
                            <summary className="cursor-pointer list-none px-3 py-2.5 text-xs font-semibold text-white/45 hover:text-white/65 [&::-webkit-details-marker]:hidden">
                              <span className="inline-flex items-center gap-1.5">
                                <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                                Work plan details
                              </span>
                            </summary>
                            <div className="border-t border-white/6 px-3 py-3 space-y-3">
                              {(selectedActivation.workPlan?.steps || []).length > 0 && (
                                <div className="grid gap-2 sm:grid-cols-2">
                                  {(selectedActivation.workPlan?.steps || []).slice(0, 4).map((step) => (
                                    <div key={step} className="flex items-start gap-2 text-xs text-white/45">
                                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "#7c3aed" }} />
                                      <span className="break-words">{cleanScrapedText(step)}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {selectedActivation.workPlan?.deck_strategy && (
                                <div className="rounded-lg border border-violet-400/15 bg-violet-400/5 p-3">
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-violet-200/70">Deck strategy</p>
                                  <p className="mt-1 text-xs font-semibold text-white/65">
                                    {cleanScrapedText(selectedActivation.workPlan.deck_strategy.recommended_format)}
                                  </p>
                                  <p className="mt-1 text-xs text-white/40">
                                    {cleanScrapedText(selectedActivation.workPlan.deck_strategy.positioning)}
                                  </p>
                                </div>
                              )}
                              {(selectedActivation.workPlan?.safety_requirements || []).length > 0 && (
                                <div className="rounded-lg border border-white/7 bg-black/10 p-3">
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
                                <div className="rounded-lg border border-emerald-400/15 bg-emerald-400/5 p-3">
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-200/70">Notifications</p>
                                  <p className="mt-1 text-xs text-white/45">
                                    {cleanScrapedText(selectedActivation.workPlan.notification_policy.reply)}
                                  </p>
                                  <p className="mt-1 text-xs text-white/35">
                                    {cleanScrapedText(selectedActivation.workPlan.notification_policy.meeting)}
                                  </p>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                        <details className="mt-3 rounded-lg border border-amber-400/20 bg-amber-400/5 group">
                          <summary className="cursor-pointer list-none px-3 py-2.5 text-xs font-bold uppercase tracking-widest text-amber-200/80 hover:text-amber-100 [&::-webkit-details-marker]:hidden">
                            <span className="inline-flex items-center gap-1.5">
                              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                              Adjust SIGNAL
                            </span>
                          </summary>
                          <div className="border-t border-amber-400/15 px-3 py-3">
                            <p className="text-xs leading-relaxed text-white/45">
                              Pause SIGNAL or change Cal&apos;s message, timing, and cadence before any outbound step.
                            </p>
                            <div className="mt-3 grid gap-2">
                              <textarea
                                value={messageNote}
                                onChange={(e) => setMessageNote(e.target.value)}
                                rows={2}
                                placeholder="Message changes, e.g. shorter, more technical, ask for call first..."
                                className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                              />
                              <div className="grid gap-2 sm:grid-cols-2">
                                <input
                                  value={timingNote}
                                  onChange={(e) => setTimingNote(e.target.value)}
                                  placeholder="Timing, e.g. wait until next Tuesday"
                                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                                />
                                <input
                                  value={cadenceNote}
                                  onChange={(e) => setCadenceNote(e.target.value)}
                                  placeholder="Cadence, e.g. follow up once after 5 days"
                                  className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/25"
                                />
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() => void controlActivation("pause")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-amber-400/40 bg-amber-400/10 px-4 py-2.5 text-sm font-bold text-amber-100 disabled:opacity-50"
                              >
                                Pause SIGNAL
                              </button>
                              <button
                                type="button"
                                onClick={() => void controlActivation("update_plan")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-violet-400/35 bg-violet-400/10 px-4 py-2.5 text-sm font-bold text-violet-100 disabled:opacity-50"
                              >
                                Save adjustments
                              </button>
                              <button
                                type="button"
                                onClick={() => void controlActivation("resume")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-emerald-400/35 bg-emerald-400/10 px-4 py-2.5 text-sm font-bold text-emerald-100 disabled:opacity-50"
                              >
                                Resume review queue
                              </button>
                            </div>
                          </div>
                        </details>
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
                    <p className="text-sm font-semibold text-white/40">SIGNAL activity will appear here</p>
                    <p className="text-[11px] text-white/25 mt-1">Use Activate SIGNAL on Results to create the first work queue item.</p>
                    <Link
                      href="/results?url="
                      className="mt-4 inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black transition-all hover:-translate-y-0.5 hover:bg-amber-400/6"
                      style={{ color: "#FFB000", borderColor: "#FFB000" }}
                    >
                      <Target className="h-3.5 w-3.5" />
                      Activate SIGNAL
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
          )}

          {/* ── SIGNAL stats strip (admin only) ── */}
          {isAdmin && session?.access_token && scoutStats && (
            <div className="flex items-center gap-3 flex-wrap text-[11px] text-white/40 px-1">
              <span className="font-bold uppercase tracking-[0.15em] text-[10px]" style={{ color: "#a78bfa" }}>Cal</span>
              <span>{scoutStats.drafted} drafted</span>
              <span className="text-white/15">·</span>
              <span>{scoutStats.sent} sent</span>
              <span className="text-white/15">·</span>
              <span style={{ color: scoutStats.opened > 0 ? "#34d399" : undefined }}>{scoutStats.opened} opened</span>
              <span className="text-white/15">·</span>
              <span style={{ color: scoutStats.replied > 0 ? "#a78bfa" : undefined }}>{scoutStats.replied} replied</span>
              <button
                type="button"
                onClick={() => void loadScoutStats()}
                className="ml-auto flex items-center gap-1 text-[10px] text-white/25 hover:text-white/60 transition-all"
              >
                <RefreshCw className="h-3 w-3" />
                Refresh
              </button>
            </div>
          )}

          {/* Confirm modals for bulk actions (admin only) */}
          {isAdmin && scoutConfirm === "draft" && (
            <div className="rounded-xl border border-blue-400/30 bg-blue-400/8 px-4 py-3 flex items-center gap-3">
              <p className="text-[11px] text-blue-100/80 flex-1">Cal will draft outreach emails for all HOT and WARM prospects that don't have one yet. Continue?</p>
              <button onClick={() => void runScoutDraftAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-blue-500/20 border border-blue-400/40 text-blue-100">Run</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white/40">Cancel</button>
            </div>
          )}
          {isAdmin && scoutConfirm === "send" && (
            <div className="rounded-xl border border-emerald-400/30 bg-emerald-400/8 px-4 py-3 flex items-center gap-3">
              <p className="text-[11px] text-emerald-100/80 flex-1">Cal will send all drafted outreach emails. This triggers live sends via Resend. Continue?</p>
              <button onClick={() => void runScoutSendAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-emerald-500/20 border border-emerald-400/40 text-emerald-100">Send</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white/40">Cancel</button>
            </div>
          )}

          {/* ── Two-panel layout ── */}
          <div className="flex gap-4 min-h-0" style={{ minHeight: "calc(100vh - 200px)" }}>

            {/* LEFT: Lead pipeline (users) or admin stage columns */}
            <div className="flex-1 flex flex-col gap-2 overflow-y-auto min-w-0">
              {(loadingLeads || serverSearchLoading) && filtered.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/8 px-6 py-12 text-center">
                  <RefreshCw className="mx-auto h-6 w-6 animate-spin text-white/20" />
                  <p className="mt-3 text-sm text-white/35">
                    {serverSearchLoading ? `Searching for "${activeSearchQuery}"…` : "Loading sales pipeline…"}
                  </p>
                </div>
              ) : isAdmin ? (
              STAGES.map((stage) => {
                const stageDeals = filtered.filter((d) => d.stage === stage);
                const meta = STAGE_META[stage];
                return (
                  <div key={stage}>
                    {/* Stage header row */}
                    <div className="flex items-center gap-2 px-3 py-2 mb-1">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{stageLabel(stage)}</span>
                      <span className="text-[10px] text-white/25 ml-0.5">— {stageDesc(stage)}</span>
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
                          const isSelected = deal.id === effectiveSelectedId;
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
                              <div
                                className="h-7 w-7 rounded-full border flex items-center justify-center shrink-0"
                                style={{ borderColor: scoreColor(deal.score), background: `${scoreColor(deal.score)}10` }}
                              >
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(deal.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.score}
                                </span>
                              </div>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-sm font-semibold text-white truncate">{deal.company}</span>
                                  <span className="text-[10px] text-white/30 shrink-0">{deal.location}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: displayStageColor(deal), background: `${displayStageColor(deal)}15` }}
                                  >
                                    {displayStageLabel(deal, true)}
                                  </span>
                                </div>
                                <p className="text-[11px] text-white/40 truncate">{deal.signal}</p>
                              </div>

                              <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                                <LeadShareBar
                                  compact
                                  lead={{
                                    id: deal.id,
                                    company_name: deal.company,
                                    priority_tier: deal.priorityTier,
                                    share_summary: deal.shareSummary,
                                    share_blurb: deal.shareBlurb,
                                  }}
                                />
                                {deal.stage === "Outreach Sent" && (
                                  <span title="Email sent"><Send className="h-3 w-3" style={{ color: "#34d399" }} /></span>
                                )}
                                {deal.stage === "Draft Ready" && (
                                  <span title="Draft ready"><Mail className="h-3 w-3" style={{ color: "#60a5fa" }} /></span>
                                )}
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
              })
              ) : (
              USER_BUCKETS.map((bucket) => {
                const bucketDeals = filtered.filter((d) => userBucketForDeal(d) === bucket);
                const meta = USER_BUCKET_META[bucket];
                return (
                  <div key={bucket}>
                    <div className="flex items-center gap-2 px-3 py-2 mb-1">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{bucket}</span>
                      <span className="text-[10px] text-white/25 ml-0.5">— {meta.desc}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded font-mono"
                        style={{ color: meta.color, background: `${meta.color}15`, fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {bucketDeals.length}
                        {!hasActiveSearch && bucketDeals.length < meta.slotCap ? (
                          <span className="text-white/25 font-normal"> / {meta.slotCap}</span>
                        ) : null}
                      </span>
                    </div>

                    {bucketDeals.length === 0 ? (
                      <div className="mx-1 mb-2 rounded-lg border border-dashed border-white/6 px-4 py-3">
                        <p className="text-[11px] text-white/20 italic">No leads in this tier right now</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-0.5 mb-2">
                        {bucketDeals.map((deal) => {
                          const isSelected = deal.id === effectiveSelectedId;
                          const tier = userTierBadge(deal);
                          return (
                            <button
                              key={deal.id}
                              type="button"
                              onClick={() => setSelectedId(deal.id)}
                              className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all group"
                              style={
                                isSelected
                                  ? { background: "rgba(124,58,237,0.12)", borderColor: "rgba(124,58,237,0.35)" }
                                  : { background: "rgba(255,255,255,0.02)", borderColor: "rgba(255,255,255,0.05)" }
                              }
                            >
                              <div
                                className="h-7 w-7 rounded-full border flex items-center justify-center shrink-0"
                                style={{ borderColor: scoreColor(deal.score), background: `${scoreColor(deal.score)}10` }}
                              >
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(deal.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.score}
                                </span>
                              </div>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-sm font-semibold text-white truncate">{deal.company}</span>
                                  <span className="text-[10px] text-white/30 shrink-0">{deal.industry}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: tier.color, background: `${tier.color}15` }}
                                  >
                                    {tier.label}
                                  </span>
                                </div>
                                <p className="text-[11px] text-white/40 truncate">{deal.signal}</p>
                              </div>

                              <div className="flex items-center gap-2 shrink-0">
                                <span
                                  className="hidden sm:inline text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide"
                                  style={{ color: deal.signalColor, background: `${deal.signalColor}12` }}
                                >
                                  {deal.signalType}
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
              })
              )}
            </div>

            {/* RIGHT: selected lead detail */}
            <div
              className="w-[380px] xl:w-[420px] shrink-0 rounded-2xl border border-white/8 overflow-hidden flex flex-col h-[calc(100vh-100px)] max-h-[calc(100vh-100px)]"
              style={{ background: "rgba(255,255,255,0.025)", position: "sticky", top: "80px" }}
            >
              {isAdmin && (
              <ScoutActionBar
                accessToken={session?.access_token}
                stats={scoutStats}
                busy={scoutBusy}
                onRunScout={() => setScoutConfirm("draft")}
                onActivateScout={() => setScoutConfirm("send")}
                onTrackScout={() => void loadScoutStats()}
              />
              )}

              {selected ? (
                <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                  {/* Detail header */}
                  <div className="shrink-0 px-4 py-3 border-b border-white/8">
                    <div className="flex items-start justify-between gap-2 mb-2">
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

                    {/* Tier / stage badge + contact inline */}
                    <div className="flex items-center gap-3 flex-wrap">
                      {isAdmin ? (
                        <span
                          className="text-[10px] font-bold px-2 py-1 rounded-full"
                          style={{ color: displayStageColor(selected), background: `${displayStageColor(selected)}15`, border: `1px solid ${displayStageColor(selected)}25` }}
                        >
                          {displayStageLabel(selected, true)}
                        </span>
                      ) : (
                        <span
                          className="text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wide"
                          style={{
                            color: userTierBadge(selected).color,
                            background: `${userTierBadge(selected).color}15`,
                            border: `1px solid ${userTierBadge(selected).color}25`,
                          }}
                        >
                          {userTierBadge(selected).label}
                        </span>
                      )}
                      {selected.contact && (
                        <span className="text-[11px] text-white/40">
                          <span className="text-white/60 font-medium">{selected.contact}</span> · {selected.contactTitle}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain flex flex-col">
                  {/* Signal block */}
                  <div className="shrink-0 px-4 py-2 border-b border-white/6">
                    {!isAdmin && (() => {
                      const verdict = scoutVerdictForDeal(selected);
                      return (
                        <p className="mb-1.5 flex items-center gap-1.5 text-[11px] leading-snug text-white/62">
                          <Zap className="h-3 w-3 shrink-0" style={{ color: verdict.color }} />
                          <span className="font-semibold text-white/78">SIGNAL · {verdict.headline}</span>
                          <span className="text-white/40">—</span>
                          <span>{verdict.detail}</span>
                        </p>
                      );
                    })()}
                    <p className={`${panelSectionLabel} mb-1`}>Buying signal</p>
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: selected.signalColor }} />
                      <div>
                        <p className="text-xs font-semibold mb-0.5" style={{ color: selected.signalColor }}>{selected.signalType}</p>
                        <p className="break-words text-[12px] leading-relaxed text-white/80">{selected.signal}</p>
                      </div>
                    </div>
                    {(selected.projectTiming?.label || selected.projectTiming?.day_min != null) && (
                      <div className="mt-1.5 flex items-center gap-2 text-[11px] text-white/60">
                        <Clock className="h-3 w-3 shrink-0 text-violet-300/90" />
                        <span>
                          <span className="font-semibold text-white/75">Project window: </span>
                          {selected.projectTiming?.day_min != null && selected.projectTiming?.day_max != null
                            ? `${selected.projectTiming.day_min}–${selected.projectTiming.day_max} days`
                            : selected.projectTiming?.label}
                          {selected.projectTiming?.source === "estimated" && (
                            <span className="text-white/40"> · estimated from signals</span>
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                  {(selected.notes || selected.shareSummary || selected.leadHighlights || (selected.robotTypesNeeded && selected.robotTypesNeeded.length > 0)) && (
                    <div className="shrink-0 px-4 py-2 border-b border-white/6">
                      <button
                        type="button"
                        onClick={() => setIntelligenceOpen((open) => !open)}
                        className="w-full flex items-center gap-2 text-left rounded-lg py-1 transition-colors hover:bg-white/[0.03]"
                        aria-expanded={intelligenceOpen}
                      >
                        <span className={panelSectionLabel}>SIGNAL intelligence</span>
                        {!intelligenceOpen && (
                          <span className="flex-1 min-w-0 text-[11px] leading-snug text-white/65 truncate">
                            {cleanAndClampText(
                              selected.leadHighlights?.specific_problem
                                || selected.shareSummary
                                || selected.notes
                                || "Problem, robot fit, and why this lead matters",
                              72,
                            )}
                          </span>
                        )}
                        {intelligenceOpen ? (
                          <ChevronUp className="h-3.5 w-3.5 shrink-0 text-white/50" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-white/50" />
                        )}
                      </button>
                      {intelligenceOpen && (
                        <div className="pt-2 space-y-2">
                          {selected.leadHighlights?.specific_problem && (
                            <p className="break-words text-[12px] leading-relaxed text-white/80">
                              <span className="font-semibold text-white">Problem: </span>
                              {cleanAndClampText(
                                selected.leadHighlights.specific_problem,
                                panelPlan === "anonymous" ? 220 : 280,
                              )}
                            </p>
                          )}
                          {(selected.leadHighlights?.why_lead || []).length > 0 && (
                            <ul className="list-disc pl-4 text-[11px] leading-relaxed text-white/70 space-y-1">
                              {(selected.leadHighlights?.why_lead || [])
                                .slice(0, panelPlan === "anonymous" ? 2 : 3)
                                .map((line, i) => (
                                  <li key={i}>{cleanAndClampText(line, panelPlan === "anonymous" ? 140 : 160)}</li>
                                ))}
                            </ul>
                          )}
                          {(selected.notes || selected.shareSummary) && (
                            <p className="break-words text-[12px] leading-relaxed text-white/75">
                              {cleanAndClampText(
                                selected.notes || selected.shareSummary,
                                panelPlan === "anonymous" ? 240 : 360,
                              )}
                            </p>
                          )}
                          {selected.robotTypesNeeded && selected.robotTypesNeeded.length > 0 && (
                            <p className="text-[11px] leading-relaxed text-white/70">
                              <span className="font-semibold text-white/90">Robot fit: </span>
                              {selected.robotTypesNeeded.join(" · ")}
                            </p>
                          )}
                          {showFullPanel && (selected.leadHighlights?.agent_enrichment?.rich_facts || []).length > 0 && (
                            <div className="space-y-1 rounded-lg border border-violet-400/15 bg-violet-400/5 p-2.5">
                              {(selected.leadHighlights?.agent_enrichment?.rich_facts || []).slice(0, 2).map((fact, i) => (
                                <p key={i} className="text-[11px] leading-relaxed text-violet-100/85">
                                  {cleanAndClampText(fact.claim || "", 200)}
                                </p>
                              ))}
                            </div>
                          )}
                          {panelPlan === "anonymous" && (
                            <p className="text-[10px] leading-relaxed text-violet-200/75">
                              Sign up free to unlock full SIGNAL research and connect to Hubspot.
                            </p>
                          )}
                          {panelPlan !== "anonymous" && (
                            <LeadShareBar
                              lead={{
                                id: selected.id,
                                company_name: selected.company,
                                priority_tier: selected.priorityTier,
                                share_summary: selected.shareSummary,
                                share_blurb: selected.shareBlurb,
                              }}
                            />
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Latest research — paid workspace */}
                  {showFullPanel && (
                  <div className="shrink-0 px-5 py-3 border-b border-white/6">
                    <button
                      type="button"
                      onClick={() => setResearchOpen((open) => !open)}
                      className="w-full flex items-center gap-2 text-left rounded-lg py-1 transition-colors hover:bg-white/[0.03]"
                      aria-expanded={researchOpen}
                    >
                      <span className={panelSectionLabel}>SIGNAL research</span>
                      {!researchOpen && (
                        <span className="flex-1 min-w-0 text-[11px] text-white/55 truncate">
                          {(selected.researchUpdates || []).length > 0
                            ? `${(selected.researchUpdates || []).length} cited update(s)`
                            : "Monitoring for new material"}
                        </span>
                      )}
                      {researchOpen ? (
                        <ChevronUp className="h-3.5 w-3.5 shrink-0 text-white/50" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5 shrink-0 text-white/50" />
                      )}
                    </button>
                    {researchOpen && (
                      <div className="pt-3">
                        {selected.lastResearchedAt && (
                          <p className="mb-2 text-[10px] text-white/45">
                            Last checked {formatResearchTime(selected.lastResearchedAt)}
                          </p>
                        )}
                        {loadingResearch && !selected.researchUpdates ? (
                          <p className="text-[11px] leading-relaxed text-white/55">SIGNAL is loading cited updates…</p>
                        ) : (selected.researchUpdates || []).length > 0 ? (
                          <div className="space-y-2">
                            {(selected.researchUpdates || []).slice(0, 3).map((update) => (
                              <div
                                key={update.id}
                                className="rounded-lg border p-2.5"
                                style={{ borderColor: "rgba(255,176,0,0.22)", background: "rgba(255,176,0,0.08)" }}
                              >
                                <div className="mb-1 flex items-center justify-between gap-2">
                                  <p className="break-words text-[11px] font-semibold text-amber-200">
                                    {cleanAndClampText(update.title, 120) || "Research update"}
                                  </p>
                                  {typeof update.significance_score === "number" && (
                                    <span className="shrink-0 font-mono text-[10px] text-amber-200/90">
                                      {Math.round(update.significance_score * 100)}
                                    </span>
                                  )}
                                </div>
                                <p className="break-words text-[11px] leading-relaxed text-white/75">
                                  {cleanAndClampText(update.summary, 220)}
                                </p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[11px] leading-relaxed text-white/55">
                            SIGNAL will add cited updates when fresh signals arrive for this account.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                  )}

                  {/* Cal outreach — admin only */}
                  {isAdmin && (
                  <div className="shrink-0 px-5 py-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-white/25">Cal&apos;s Draft</p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setPreviewOpen(true)}
                          className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded transition-all"
                          style={{ background: "rgba(255,176,0,0.08)", color: "#FFB000" }}
                        >
                          <Eye className="h-3 w-3" />
                          Preview
                        </button>
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
                          {copied ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </div>

                    {selected.stage === "Outreach Sent" && (
                      <div className="mb-2 flex items-center gap-2 flex-wrap">
                        <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-full" style={{ background: "rgba(52,211,153,0.1)", color: "#34d399", border: "1px solid rgba(52,211,153,0.2)" }}>
                          <Send className="h-2.5 w-2.5" /> Sent
                        </span>
                        <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full text-white/30" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
                          <Eye className="h-2.5 w-2.5" /> Tracking active
                        </span>
                      </div>
                    )}

                    {selected.outreachSubject && (
                      <div className="mb-2 p-2.5 rounded-lg" style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.18)" }}>
                        <p className="text-[10px] text-white/30 mb-0.5 uppercase tracking-wide">Subject</p>
                        <p className="text-xs font-semibold" style={{ color: "#FFB000" }}>{selected.outreachSubject}</p>
                      </div>
                    )}

                    {selected.outreachBody ? (
                      <div className="p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <pre className="whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed text-white/55">
                          {selected.outreachBody}
                        </pre>
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-white/10 px-3 py-4">
                        <p className="text-[11px] leading-relaxed text-white/35 mb-3">
                          No Cal draft yet. Run SIGNAL on this lead to refresh inference and generate outreach.
                        </p>
                        <button
                          type="button"
                          disabled={developingLeadId === selected.id}
                          onClick={() => void developLeadWithScout(selected)}
                          className="w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-[11px] font-bold border transition-all disabled:opacity-50"
                          style={{ background: "rgba(3,218,197,0.08)", borderColor: "rgba(3,218,197,0.28)", color: "#6ee7d7" }}
                        >
                          {developingLeadId === selected.id
                            ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            : <Zap className="h-3.5 w-3.5" />
                          }
                          {developingLeadId === selected.id ? "SIGNAL developing…" : "Develop lead with SIGNAL"}
                        </button>
                      </div>
                    )}

                    {selected.outreachBody && isAdmin && (
                      <button
                        type="button"
                        disabled={developingLeadId === selected.id}
                        onClick={() => void developLeadWithScout(selected)}
                        className="mt-2 w-full flex items-center justify-center gap-2 rounded-lg py-2 text-[10px] font-semibold border transition-all disabled:opacity-50"
                        style={{ borderColor: "rgba(3,218,197,0.2)", color: "rgba(3,218,197,0.85)" }}
                      >
                        {developingLeadId === selected.id ? "Refreshing…" : "Re-run SIGNAL development"}
                      </button>
                    )}

                    {selected.contact && selected.stage !== "Outreach Sent" && session?.access_token && (
                      <button
                        type="button"
                        disabled={sendingLeadId === selected.id}
                        onClick={() => void sendOneLead(selected)}
                        className="mt-3 w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-[11px] font-bold border transition-all disabled:opacity-50"
                        style={{ background: "rgba(52,211,153,0.08)", borderColor: "rgba(52,211,153,0.28)", color: "#6ee7b7" }}
                      >
                        {sendingLeadId === selected.id
                          ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          : <Send className="h-3.5 w-3.5" />
                        }
                        {sendingLeadId === selected.id ? "Sending..." : `Send to ${selected.contact}`}
                      </button>
                    )}
                  </div>
                  )}

                  </div>

                  {!isAdmin && (
                    <div
                      className="shrink-0 z-20 px-3 py-2.5 pb-12 border-t border-teal-400/20 shadow-[0_-8px_24px_rgba(0,0,0,0.4)]"
                      style={{ background: "linear-gradient(180deg, rgba(3,218,197,0.12) 0%, rgba(13,5,32,0.98) 50%)" }}
                    >
                      <HubSpotCtaLink
                        connected={hubspotIntegration?.connected}
                        hasSession={Boolean(session?.access_token)}
                        className="w-full px-4 py-3 text-base"
                      />
                      {session?.access_token ? (
                        <button
                          type="button"
                          onClick={() => void handleSaveLead(selected)}
                          disabled={advancingLeadId === selected.id}
                          className="mt-1.5 w-full flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold transition-all disabled:opacity-50 hover:brightness-110"
                          style={{ color: "#0d0520", background: "#03DAC5", border: "1px solid #03DAC5" }}
                        >
                          {advancingLeadId === selected.id
                            ? <RefreshCw className="h-4 w-4 animate-spin" />
                            : <Zap className="h-4 w-4" />
                          }
                          {advancingLeadId === selected.id ? "Saving…" : "Save to SIGNAL workspace"}
                        </button>
                      ) : (
                        <Link
                          href={`/signup?next=${encodeURIComponent(`/pipeline?lead=${selected.id}`)}`}
                          className="mt-1.5 w-full flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold transition-all hover:brightness-110"
                          style={{ color: "#0d0520", background: "#03DAC5", border: "1px solid #03DAC5" }}
                        >
                          Activate SIGNAL — free
                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      )}
                    </div>
                  )}

                  {/* Action bar — admin only */}
                  {isAdmin && (
                  <div className="shrink-0 p-4 border-t border-white/8 flex items-center gap-2">
                    {
                      <>
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
                            onClick={() => void handleAdvanceLead(selected)}
                            disabled={advancingLeadId === selected.id}
                            className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg transition-all"
                            style={{
                              background: advancingLeadId === selected.id ? "rgba(124,58,237,0.45)" : "#7c3aed",
                              color: "#fff",
                              border: "1px solid #7c3aed",
                            }}
                          >
                            {advancingLeadId === selected.id ? "Advancing..." : "Advance with Cal"}
                            <ArrowRight className="h-3 w-3" />
                          </button>
                        )}
                      </>
                    }
                  </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                  <Target className="h-8 w-8 text-white/10 mb-3" />
                  <p className="text-sm text-white/25">
                    {pendingDeepLink && deepLinkLoadFailed
                      ? "Network interrupted while loading this lead."
                      : pendingDeepLink
                      ? "Loading linked lead…"
                      : hasActiveSearch && filtered.length === 0 && !serverSearchLoading
                      ? `No leads match "${activeSearchQuery}". Try food service, hospitality, logistics, or a company name.`
                      : isAdmin
                        ? "Select a deal to review signal detail and Cal outreach"
                        : "Select a lead to review signals, research, and SIGNAL scoring"}
                  </p>
                  {pendingDeepLink && deepLinkLoadFailed ? (
                    <button
                      type="button"
                      onClick={retryDeepLink}
                      className="mt-4 rounded-lg border border-white/15 px-4 py-2 text-xs font-semibold text-white/70 transition-colors hover:border-white/25 hover:text-white"
                    >
                      Retry loading lead
                    </button>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Email Preview Modal — admin only */}
      {isAdmin && previewOpen && selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
          onClick={() => setPreviewOpen(false)}
        >
          <div
            className="relative w-full max-w-lg rounded-2xl border p-6 flex flex-col gap-4"
            style={{ background: "#0d0520", borderColor: "rgba(124,58,237,0.3)", maxHeight: "85vh", overflowY: "auto" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5" style={{ color: "#a78bfa" }}>Email Preview</p>
                <p className="text-sm font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>{selected.company}</p>
              </div>
              <button
                onClick={() => setPreviewOpen(false)}
                className="text-white/30 hover:text-white/70 text-xs font-semibold px-2 py-1 rounded"
              >
                Close
              </button>
            </div>
            <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.02)" }}>
              <p className="text-[10px] uppercase tracking-widest text-white/25 mb-1">From</p>
              <p className="text-xs text-white/60">Cal &lt;cal@readyforrobots.com&gt;</p>
            </div>
            {selected.contact && (
              <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.02)" }}>
                <p className="text-[10px] uppercase tracking-widest text-white/25 mb-1">To</p>
                <p className="text-xs text-white/60">{selected.contact}</p>
              </div>
            )}
            <div className="rounded-xl border border-amber-400/20 p-4" style={{ background: "rgba(255,176,0,0.05)" }}>
              <p className="text-[10px] uppercase tracking-widest text-white/25 mb-1">Subject</p>
              <p className="text-xs font-semibold" style={{ color: "#FFB000" }}>{selected.outreachSubject}</p>
            </div>
            <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.02)" }}>
              <p className="text-[10px] uppercase tracking-widest text-white/25 mb-2">Message</p>
              <pre className="whitespace-pre-wrap break-words font-sans text-[12px] leading-loose text-white/65">
                {selected.outreachBody}
              </pre>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyDraft}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-[11px] font-bold border transition-all"
                style={copied
                  ? { background: "rgba(52,211,153,0.1)", borderColor: "rgba(52,211,153,0.3)", color: "#6ee7b7" }
                  : { background: "rgba(124,58,237,0.1)", borderColor: "rgba(124,58,237,0.3)", color: "#c4b5fd" }
                }
              >
                {copied ? <CheckCheck className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied!" : "Copy draft"}
              </button>
              {selected.contact && selected.stage !== "Outreach Sent" && session?.access_token && (
                <button
                  disabled={sendingLeadId === selected.id}
                  onClick={async () => { await sendOneLead(selected); setPreviewOpen(false); }}
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-[11px] font-bold border transition-all disabled:opacity-50"
                  style={{ background: "rgba(52,211,153,0.1)", borderColor: "rgba(52,211,153,0.3)", color: "#6ee7b7" }}
                >
                  <Send className="h-3.5 w-3.5" />
                  {sendingLeadId === selected.id ? "Sending..." : "Send now"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
