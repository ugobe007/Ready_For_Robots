/**
 * Pipeline — ReadyForRobots
 * Two-panel layout: left = inline deal rows grouped by stage, right = selected deal detail + outreach draft
 * Violet palette: #111827 bg · #059669 accent · cream text
 * Design: Linear/Raycast-inspired — dense, inline, data-forward
 */
import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  AlertTriangle, MapPin, Filter, ChevronRight, ChevronDown, ChevronUp,
  Copy, CheckCheck, ArrowRight, ArrowLeft, Mail,
  Users, Clock, Target, Newspaper, Send, Eye, MousePointerClick,
  Zap, RefreshCw, FileText, Sparkles, Download
} from "lucide-react";
import Header from "@/components/Header";
import AdminNav from "@/components/AdminNav";
import ScoutActionBar from "@/components/ScoutActionBar";
import ProposalPdfModal, { type ProposalData } from "@/components/ProposalPdfModal";
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
import { dealMatchesIndustrySearch, pipelineSearchSuggestions } from "@/lib/industrySearchLexicon";
import { mapApiLeadToDeal, type ApiLead } from "@/lib/pipelineLeadMap";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import LeadShareBar from "@/components/LeadShareBar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

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
  pipelineAction?: string;
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

function parseSavedLeadsLimitMessage(errText: string): string | null {
  try {
    const parsed = JSON.parse(errText) as { detail?: { code?: string; message?: string } | string };
    const detail = parsed.detail;
    if (typeof detail === "object" && detail?.code === "saved_leads_limit") {
      return detail.message || "Free workspace lead limit reached.";
    }
  } catch {
    /* not JSON */
  }
  return null;
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
  "New Signal":    { color: "#10b981", dot: "#10b981", label: "New Signal",    desc: "Just detected" },
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
  "Monitoring":  { color: "#059669", dot: "#059669", desc: "Early signals SIGNAL is tracking", slotCap: PIPELINE_MONITOR_SLOTS },
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
  if (tier === "COLD") return { label: "MONITOR", color: "#059669" };
  if (deal.score >= 85) return { label: "HOT", color: "#34d399" };
  if (deal.score >= 65) return { label: "WARM", color: "#FFB000" };
  return { label: "MONITOR", color: "#059669" };
};

const dealTierColor = (deal: Pick<Deal, "score" | "priorityTier">) =>
  USER_BUCKET_META[userBucketForDeal(deal)].color;

const scoreColor = (s: number) =>
  s >= 90 ? "#34d399" : s >= 75 ? "#10b981" : "#FFB000";

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
    color: "#10b981",
  };
};

const panelSectionLabel = "text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-800";

type PipelineEntitlements = {
  plan: "anonymous" | "free" | "paid";
  pipeline_limit: number;
  visible_count: number;
  saved_limit: number | null;
  upgrade_url: string;
  features?: {
    research_updates?: boolean;
    hubspot_auto_sync?: boolean;
    unlimited_saves?: boolean;
    full_lead_intel?: boolean;
  };
};

const PIPELINE_LIMIT_FREE = 50;
const PIPELINE_LIMIT_PAID = 50;
const PIPELINE_SESSION_KEY = "pipeline_feed_v4";
const PIPELINE_SESSION_TTL_MS = 2 * 60 * 60 * 1000;
/** Stale paint while API revalidates — avoids blank page when Fly is slow. */
const PIPELINE_STALE_PAINT_MS = 7 * 24 * 60 * 60 * 1000;

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
const PIPELINE_TIMEOUT = 15_000;

type PipelineFeedPayload = {
  summary?: LeadSummary;
  leads?: ApiLead[];
  entitlements?: PipelineEntitlements;
  cache_pending?: boolean;
};

async function fetchPipelineLeadsFallback(base: string, headers?: HeadersInit): Promise<ApiLead[]> {
  const res = await fetchWithTimeoutRetry(
    `${base}/api/leads?limit=50&sort=score&exclude_junk=true`,
    liveFetchInit({ headers }),
    PIPELINE_TIMEOUT,
    { retries: 2, retryDelayMs: 1000 },
  );
  if (!res.ok) return [];
  const data = await res.json();
  if (Array.isArray(data)) return data as ApiLead[];
  if (Array.isArray((data as { leads?: unknown }).leads)) {
    return (data as { leads: ApiLead[] }).leads;
  }
  return [];
}

async function fetchPipelineSummaryFallback(base: string): Promise<LeadSummary | null> {
  const res = await fetchWithTimeoutRetry(
    `${base}/api/leads/summary?exclude_junk=true`,
    liveFetchInit(),
    PIPELINE_TIMEOUT,
    { retries: 2, retryDelayMs: 1000 },
  );
  if (!res.ok) return null;
  return (await res.json()) as LeadSummary;
}

function mapPipelineRows(apiRows: ApiLead[], crmStages: Record<number, string> = {}): Deal[] {
  const mapped: Deal[] = [];
  for (const row of apiRows) {
    try {
      mapped.push(mapApiLeadToDeal(row, crmStages[row.id]) as Deal);
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
  if (!pinned) return mapped;
  const merged = mapped.map((d) => (d.id === deepLinkId ? { ...d, ...pinned } : d));
  if (merged.some((d) => d.id === deepLinkId)) return merged;
  return [pinned, ...merged];
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
  crmStages: Record<number, string> = {},
) {
  const rows = Array.isArray(payload.leads) ? payload.leads : [];
  if (payload.entitlements) setters.setEntitlements(payload.entitlements);
  if (payload.summary && ((payload.summary.total ?? 0) > 0 || (payload.summary.hot ?? 0) > 0)) {
    setters.setSummary(payload.summary);
  }
  if (rows.length > 0) {
    const mapped = mapPipelineRows(rows, crmStages);
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

function dealMatchesSearchQuery(deal: Deal, query: string): boolean {
  return dealMatchesIndustrySearch(
    {
      industry: deal.industry,
      company: deal.company,
      signal: deal.signal,
      location: deal.location,
    },
    query,
  );
}

async function fetchLeadsBySearch(base: string, query: string, headers?: HeadersInit): Promise<Deal[]> {
  const params = new URLSearchParams({
    search: query,
    limit: String(PIPELINE_LIMIT_PAID),
    sort: "score",
    exclude_junk: "true",
  });
  const res = await fetchWithTimeoutRetry(
    `${base}/api/leads?${params}`,
    liveFetchInit({ headers }),
    35_000,
    { retries: 2, retryDelayMs: 1000 },
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
    <div className="pipeline-metric-card" style={{ ["--metric-accent" as string]: color }}>
      <div className="mb-1.5 flex items-center justify-between gap-2 pl-2">
        <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-stone-600">{label}</p>
        <span className="h-2 w-2 rounded-full ring-2 ring-white" style={{ background: color }} />
      </div>
      <p className="pl-2 font-mono-data text-xl font-semibold leading-none" style={{ color }}>
        {value}
      </p>
      <p className="mt-1 pl-2 text-[10px] leading-snug text-gray-600">{sub}</p>
    </div>
  );
}

function dealRowSurface(isSelected: boolean) {
  return isSelected ? "pipeline-deal-row pipeline-deal-row-selected" : "pipeline-deal-row pipeline-deal-row-hover";
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
  const [proposalOpen, setProposalOpen] = useState(false);
  const [proposalData, setProposalData] = useState<ProposalData | null>(null);
  const [proposalBusy, setProposalBusy] = useState(false);
  const [saveLimitOpen, setSaveLimitOpen] = useState(false);
  const [saveLimitMessage, setSaveLimitMessage] = useState("");
  const [crmStageByCompanyId, setCrmStageByCompanyId] = useState<Record<number, string>>({});
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
  const showKanban = isAdmin || Boolean(session?.access_token);

  useEffect(() => {
    if (!session?.access_token) {
      setCrmStageByCompanyId({});
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const teamsRes = await fetch(
          `${getApiBase()}/api/crm/teams`,
          liveFetchInit({ headers: authHeader(session.access_token) }),
        );
        if (!teamsRes.ok) return;
        const teams = (await teamsRes.json()) as Array<{ id: string }>;
        const teamId = teams[0]?.id;
        if (!teamId) return;
        const accountsRes = await fetch(
          `${getApiBase()}/api/crm/accounts?team_id=${encodeURIComponent(teamId)}`,
          liveFetchInit({ headers: authHeader(session.access_token) }),
        );
        if (!accountsRes.ok) return;
        const accounts = (await accountsRes.json()) as Array<{
          company_id?: number | null;
          outreach_stage?: string | null;
        }>;
        if (cancelled) return;
        const next: Record<number, string> = {};
        for (const acct of accounts) {
          if (acct.company_id && acct.outreach_stage) next[acct.company_id] = acct.outreach_stage;
        }
        setCrmStageByCompanyId(next);
        setDeals((prev) =>
          prev.map((deal) => {
            const stage = next[deal.id];
            if (!stage) return deal;
            const mapped = mapApiLeadToDeal(
              {
                id: deal.id,
                company_name: deal.company,
                industry: deal.industry,
                priority_tier: deal.priorityTier,
                score: deal.score,
                signals: [{ signal_type: deal.signalType, text: deal.signal }],
              },
              stage,
            ) as Deal;
            return { ...deal, stage: mapped.stage, updatedAt: "synced" };
          }),
        );
      } catch {
        /* CRM stage sync is additive */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

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

    const cachedEntry =
      readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_SESSION_TTL_MS)
      ?? readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_STALE_PAINT_MS);
    const paintedFromCache = cachedEntry ? applyPipelineFeed(cachedEntry.data, feedSetters) : false;
    setLoadingLeads(!paintedFromCache);
    setLoadingSummary(!paintedFromCache);

    const loadPipeline = async (token?: string) => {
      const headers = token ? authHeader(token) : undefined;
      const res = await fetchWithTimeoutRetry(
        `${base}/api/leads/pipeline`,
        liveFetchInit({ headers }),
        PIPELINE_TIMEOUT,
        { retries: 3, retryDelayMs: 1500 },
      );
      if (!res.ok) throw new Error("Could not load pipeline");
      let payload = (await res.json()) as PipelineFeedPayload;
      if (cancelled) return;

      const leadRows = Array.isArray(payload.leads) ? payload.leads : [];
      if (leadRows.length === 0) {
        const fallbackLeads = await fetchPipelineLeadsFallback(base, headers);
        if (cancelled) return;
        if (fallbackLeads.length > 0) {
          payload = { ...payload, leads: fallbackLeads };
          const summaryStale =
            !payload.summary?.hot &&
            !payload.summary?.companies_in_database &&
            !payload.summary?.signals_in_database;
          if (summaryStale) {
            const summary = await fetchPipelineSummaryFallback(base);
            if (cancelled) return;
            if (summary && (summary.hot ?? summary.companies_in_database)) {
              payload = { ...payload, summary };
            }
          }
        }
      }

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
    if (!deepLinkLeadId) return;
    const onOnline = () => retryDeepLink();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [deepLinkLeadId]);

  // Deep link from newsletter / homepage (?lead=123 or legacy #123).
  // Fire immediately in parallel with the pipeline feed — do not wait for loadingLeads.
  useEffect(() => {
    if (!deepLinkLeadId) return;

    setSelectedId(deepLinkLeadId);
    setDeepLinkLoadFailed(false);

    if (deepLinkInflightRef.current === deepLinkLeadId) return;

    deepLinkInflightRef.current = deepLinkLeadId;
    let cancelled = false;
    void (async () => {
      const base = getApiBase();
      try {
        const response = await fetchWithTimeoutRetry(
          `${base}/api/leads/by-id/${deepLinkLeadId}`,
          liveFetchInit(),
          12_000,
          { retries: 2, retryDelayMs: 1200 },
        );
        if (cancelled) return;
        if (!response.ok) {
          deepLinkInflightRef.current = null;
          setDeepLinkLoadFailed(true);
          return;
        }
        const lead = (await response.json()) as ApiLead;
        const mapped = mapApiLeadToDeal(lead, crmStageByCompanyId[lead.id]) as Deal;
        if (cancelled) return;
        deepLinkInflightRef.current = null;
        setDeepLinkLoadFailed(false);
        setDeals((prev) => {
          const mappedRow = mapped as Deal;
          if (prev.some((d) => d.id === deepLinkLeadId)) {
            return prev.map((d) => (d.id === deepLinkLeadId ? { ...d, ...mappedRow } : d));
          }
          return [mappedRow, ...prev];
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
  }, [deepLinkLeadId, deepLinkRetryNonce]);

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

  // Lazy detail enrichment — always refresh selected row from by-id (feed/session cache can be stale).
  useEffect(() => {
    if (!selectedId) return;
    if (deepLinkInflightRef.current === selectedId) return;
    const base = getApiBase();
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void (async () => {
        setLoadingResearch(true);
        try {
          const response = await fetchWithTimeout(
            `${base}/api/leads/by-id/${selectedId}`,
            liveFetchInit(),
            8_000,
          );
          if (!response.ok) throw new Error(await response.text());
          const lead = (await response.json()) as ApiLead;
          const mapped = mapApiLeadToDeal(lead, crmStageByCompanyId[lead.id]) as Deal;
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
        .catch(() => {
          setServerSearchDeals([]);
          toast.error(`Pipeline search timed out for "${q}". Showing matches from the loaded slice — retry in a moment.`);
        })
        .finally(() => setServerSearchLoading(false));
    }, 350);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [industryQuery, filter, session?.access_token]);

  const industries = Array.from(new Set(deals.map((d) => d.industry).filter(Boolean))).sort();
  const searchSuggestions = useMemo(
    () => Array.from(new Set([...pipelineSearchSuggestions(), ...industries])).sort(),
    [industries],
  );
  const activeSearchQuery = industryQuery.trim() || (filter !== "All" ? filter : "");
  const hasActiveSearch = Boolean(activeSearchQuery);
  const clientSearchMatches = useMemo(
    () => (hasActiveSearch ? deals.filter((d) => dealMatchesSearchQuery(d, activeSearchQuery)) : deals),
    [deals, hasActiveSearch, activeSearchQuery],
  );
  const filtered = useMemo(() => {
    if (!hasActiveSearch) return deals;
    if (serverSearchDeals.length > 0) return serverSearchDeals;
    return clientSearchMatches;
  }, [deals, hasActiveSearch, serverSearchDeals, clientSearchMatches]);
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

  const generateProposalForDeal = async (deal: Deal) => {
    if (!session?.access_token) {
      toast.error("Sign in to generate a proposal");
      return;
    }
    setProposalBusy(true);
    try {
      const res = await fetch(
        `${getApiBase()}/api/proposals/generate`,
        liveFetchInit({
          method: "POST",
          headers: { ...authHeader(session.access_token), "Content-Type": "application/json" },
          body: JSON.stringify({
            company_name: deal.company,
            company_id: deal.id,
            industry: deal.industry,
            robot_category: deal.robotTypesNeeded?.[0],
            signal: deal.signal,
            scout_score: deal.score,
            contact_email: deal.contact,
          }),
        }),
      );
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as ProposalData;
      setProposalData(data);
      setProposalOpen(true);
      toast.success("Proposal generated");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not generate proposal");
    } finally {
      setProposalBusy(false);
    }
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
        const limitMessage = parseSavedLeadsLimitMessage(errText);
        if (limitMessage) {
          setSaveLimitMessage(limitMessage);
          setSaveLimitOpen(true);
          return;
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
  const hotDeals = summary?.hot ?? (loadingSummary ? undefined : filtered.filter((d) => userBucketForDeal(d) === "Hot Leads").length);
  const warmDeals = summary?.warm ?? (loadingSummary ? undefined : filtered.filter((d) => userBucketForDeal(d) === "Warm Leads").length);
  const visibleDeals = filtered.length;
  const filteredHot = filtered.filter((d) => userBucketForDeal(d) === "Hot Leads").length;
  const filteredWarm = filtered.filter((d) => userBucketForDeal(d) === "Warm Leads").length;
  const queuedActivations = activations.filter((a) => ["queued", "evaluating", "drafted", "awaiting_approval"].includes(a.status)).length;

  return (
    <div className="pipeline-page-bg flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 px-4 pb-6 pt-20 lg:px-6">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-2">
          {isAdmin && <AdminNav />}

          <div className="pipeline-workspace">
            {/* ── Page header ── */}
            <div className="pipeline-page-header">
              <div className="pipeline-page-header-inner flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div>
                  <p className="sb-kicker mb-0.5 text-emerald-800">SIGNAL · Sales intelligence</p>
                  <h1 className="font-display text-xl font-semibold tracking-tight text-gray-900 sm:text-2xl">
                    {isAdmin ? "Active Signals → Live Pipeline" : "Sales Pipeline"}
                  </h1>
                  <p className="mt-1 max-w-xl text-xs leading-relaxed text-gray-700 sm:text-sm">
                    {isAdmin
                      ? "Authoritative database counts up top. Cal outreach controls below."
                      : panelPlan === "anonymous"
                        ? `Preview ${entitlements?.pipeline_limit ?? 12} SIGNAL-ranked leads — sign up for ${PIPELINE_LIMIT_FREE} and put SIGNAL on your workspace.`
                        : panelPlan === "free"
                          ? `Your free workspace: ${entitlements?.visible_count ?? deals.length} of ${entitlements?.pipeline_limit ?? PIPELINE_LIMIT_FREE} live leads · save up to ${entitlements?.saved_limit ?? 5}.`
                          : `${PIPELINE_HOT_SLOTS} hot · ${PIPELINE_WARM_SLOTS} warm · ${PIPELINE_MONITOR_SLOTS} monitoring — ranked by buyer intent and timing.`}
                  </p>
                </div>

                <div className="relative w-full sm:w-[340px]">
                  <Filter className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                  <input
                    value={industryQuery}
                    onChange={(e) => {
                      setIndustryQuery(e.target.value);
                      setFilter("All");
                    }}
                    list="pipeline-industries"
                    placeholder="Search industry, company, or signal…"
                    className="sb-input py-2 pl-9 pr-10"
                  />
                  {industryQuery && (
                    <button
                      type="button"
                      onClick={() => setIndustryQuery("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-bold text-stone-500 hover:text-stone-800"
                    >
                      Clear
                    </button>
                  )}
                  <datalist id="pipeline-industries">
                    {searchSuggestions.map((ind) => (
                      <option key={ind} value={ind} />
                    ))}
                  </datalist>
                </div>
              </div>
            </div>

            {/* ── Alerts ── */}
            {(loadErr || (!loadingLeads && !loadErr && !hasActiveSearch && filtered.length === 0)) && (
              <div className="space-y-1.5 border-b border-gray-200 px-3 py-2 sm:px-4">
                {loadErr && (
                  <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
                    {loadErr}
                  </div>
                )}
                {!loadingLeads && !loadErr && !hasActiveSearch && filtered.length === 0 && (
                  <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-900">
                    Pipeline data is syncing from the database. Reload in a moment if tiers still look empty.
                  </div>
                )}
              </div>
            )}

            <section className="pipeline-metrics-grid">
            <PipelineMetric
              label={isAdmin ? "Database total" : "Market watchlist"}
              value={formatMetric(dbTotal)}
              sub={loadingSummary
                ? "Refreshing market totals..."
                : `${formatMetric(summary?.signals_in_database ?? summary?.total_signals)} scored buying signals`}
              color="#111827"
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
              color="#10b981"
            />
          </section>

          <section className="mx-3 mb-2 rounded-md border border-amber-200 bg-amber-50/80 px-3 py-2 sm:mx-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <div
                  className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border"
                  style={{ borderColor: `${marketSnippet.color}44`, background: `${marketSnippet.color}12` }}
                >
                  <Newspaper className="h-4 w-4" style={{ color: marketSnippet.color }} />
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-800">
                    {marketSnippet.label}
                  </p>
                  <h2 className="mt-1 break-words text-sm font-bold text-gray-900" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    {marketSnippet.headline}
                  </h2>
                  <p className="mt-1 break-words text-[12px] leading-relaxed text-gray-700">
                    {marketSnippet.detail}
                  </p>
                </div>
              </div>
              <Link
                href="/newsletter"
                className="inline-flex shrink-0 items-center gap-1.5 text-xs font-bold text-amber-800 hover:text-amber-900"
              >
                Read daily brief <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </section>

          {/* ── SIGNAL activation queue (admin only) ── */}
          {isAdmin && (
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
            <div className="flex flex-col xl:flex-row">
              <div className="xl:w-[360px] border-b xl:border-b-0 xl:border-r border-gray-100">
                <div className="px-4 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#10b981" }}>SIGNAL Queue</p>
                    <p className="text-xs text-gray-400 mt-1">Recent sales activations from Results</p>
                  </div>
                  <span className="text-[10px] text-gray-400">{loadingActivations ? "Loading…" : `${activations.length} active`}</span>
                </div>
                {activationErr && (
                  <div className="mx-4 mb-3 rounded-lg border border-amber-500/30 bg-amber-50 px-3 py-2 text-[11px] text-amber-900">
                    {activationErr}
                  </div>
                )}
                <div className="px-2 pb-3 flex xl:flex-col gap-2 overflow-x-auto">
                  {activations.length === 0 && !loadingActivations ? (
                    <div className="m-2 rounded-xl border border-dashed border-gray-100 px-4 py-4 text-center">
                      <p className="text-xs font-semibold text-gray-500">No SIGNAL activations yet</p>
                      <p className="text-[11px] text-gray-400 mt-1">Activate leads from the Results page and they will appear here.</p>
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
                              ? { background: "rgba(5,150,105,0.14)", borderColor: "rgba(5,150,105,0.38)" }
                              : { background: "#ffffff", borderColor: "#e5e7eb" }
                          }
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-gray-800">{activation.leadCount} leads</span>
                            <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide" style={{ background: "rgba(167,139,250,0.14)", color: "#047857" }}>
                              {statusLabel(activation.status)}
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] text-gray-400 truncate">
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
                          <h2 className="text-base font-bold text-gray-900" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                            Activation #{selectedActivation.id}
                          </h2>
                          <p className="mt-1 break-all text-xs text-gray-500">
                            {activationSourceLabel(selectedActivation.sourceUrl)}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 shrink-0">
                          <span className="rounded-full border border-gray-200 px-2.5 py-1 text-xs font-semibold text-gray-500 capitalize">
                            {selectedActivation.mode}
                          </span>
                          {selectedActivation.requiresAccount && (
                            <span className="rounded-full px-2.5 py-1 text-xs font-bold text-amber-800" style={{ background: "rgba(251,146,60,0.12)" }}>
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
                        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-3">
                          <p className="text-[10px] uppercase tracking-widest text-gray-400">Materials</p>
                          <p className="mt-1 text-xs font-semibold text-gray-600 capitalize">{selectedActivation.material}</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-3">
                          <p className="text-[10px] uppercase tracking-widest text-gray-400">Scope</p>
                          <p className="mt-1 text-xs font-semibold text-gray-600 capitalize">{selectedActivation.scope}</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-3">
                          <p className="text-[10px] uppercase tracking-widest text-gray-400">Next action</p>
                          <p className="mt-1 text-xs font-semibold text-gray-600">Evaluate leads</p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock className="h-3.5 w-3.5" style={{ color: "#10b981" }} />
                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Status flow</p>
                        </div>
                        <div className="mb-3 flex gap-1 overflow-x-auto pb-1">
                          {(selectedActivation.statusFlow || []).map((step) => (
                            <div
                              key={step.id}
                              className="min-w-[96px] rounded-lg border px-2 py-1.5"
                              style={
                                step.active
                                  ? { background: "rgba(5,150,105,0.16)", borderColor: "rgba(5,150,105,0.4)" }
                                  : { background: "#f9fafb", borderColor: "#e5e7eb" }
                              }
                            >
                              <p className={step.active ? "text-[10px] font-bold text-emerald-700" : "text-[10px] font-semibold text-gray-400"}>
                                {step.label}
                              </p>
                            </div>
                          ))}
                        </div>
                        <p className="mb-2 text-xs font-bold uppercase tracking-widest text-gray-400">Work plan</p>
                        <p className="break-words text-sm text-gray-500 leading-relaxed">
                          {cleanScrapedText(selectedActivation.workPlan?.materials?.next) || "SIGNAL will evaluate the selected leads and prepare Cal outreach."}
                        </p>
                        {((selectedActivation.workPlan?.steps || []).length > 0
                          || selectedActivation.workPlan?.deck_strategy
                          || (selectedActivation.workPlan?.safety_requirements || []).length > 0
                          || selectedActivation.workPlan?.notification_policy) && (
                          <details className="mt-3 rounded-lg border border-gray-200 bg-gray-50 group">
                            <summary className="cursor-pointer list-none px-3 py-2.5 text-xs font-semibold text-gray-500 hover:text-gray-600 [&::-webkit-details-marker]:hidden">
                              <span className="inline-flex items-center gap-1.5">
                                <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                                Work plan details
                              </span>
                            </summary>
                            <div className="border-t border-gray-100 px-3 py-3 space-y-3">
                              {(selectedActivation.workPlan?.steps || []).length > 0 && (
                                <div className="grid gap-2 sm:grid-cols-2">
                                  {(selectedActivation.workPlan?.steps || []).slice(0, 4).map((step) => (
                                    <div key={step} className="flex items-start gap-2 text-xs text-gray-500">
                                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "#059669" }} />
                                      <span className="break-words">{cleanScrapedText(step)}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {selectedActivation.workPlan?.deck_strategy && (
                                <div className="rounded-lg border border-emerald-400/15 bg-emerald-50 p-3">
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-700/70">Deck strategy</p>
                                  <p className="mt-1 text-xs font-semibold text-gray-600">
                                    {cleanScrapedText(selectedActivation.workPlan.deck_strategy.recommended_format)}
                                  </p>
                                  <p className="mt-1 text-xs text-gray-500">
                                    {cleanScrapedText(selectedActivation.workPlan.deck_strategy.positioning)}
                                  </p>
                                </div>
                              )}
                              {(selectedActivation.workPlan?.safety_requirements || []).length > 0 && (
                                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Sending guardrails</p>
                                  <div className="mt-2 flex flex-wrap gap-1.5">
                                    {(selectedActivation.workPlan?.safety_requirements || []).map((item) => (
                                      <span
                                        key={item.key}
                                        className="rounded-full border px-2 py-1 text-[10px] font-semibold"
                                        style={
                                          item.required
                                            ? { borderColor: "rgba(251,146,60,0.4)", color: "#92400e", background: "rgba(251,146,60,0.12)" }
                                            : { borderColor: "#e5e7eb", color: "#6b7280", background: "#f9fafb" }
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
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">Notifications</p>
                                  <p className="mt-1 text-xs text-gray-500">
                                    {cleanScrapedText(selectedActivation.workPlan.notification_policy.reply)}
                                  </p>
                                  <p className="mt-1 text-xs text-gray-400">
                                    {cleanScrapedText(selectedActivation.workPlan.notification_policy.meeting)}
                                  </p>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                        <details className="mt-3 rounded-lg border border-amber-400/20 bg-amber-400/5 group">
                          <summary className="cursor-pointer list-none px-3 py-2.5 text-xs font-bold uppercase tracking-widest text-amber-800 hover:text-amber-900 [&::-webkit-details-marker]:hidden">
                            <span className="inline-flex items-center gap-1.5">
                              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                              Adjust SIGNAL
                            </span>
                          </summary>
                          <div className="border-t border-amber-400/15 px-3 py-3">
                            <p className="text-xs leading-relaxed text-gray-500">
                              Pause SIGNAL or change Cal&apos;s message, timing, and cadence before any outbound step.
                            </p>
                            <div className="mt-3 grid gap-2">
                              <textarea
                                value={messageNote}
                                onChange={(e) => setMessageNote(e.target.value)}
                                rows={2}
                                placeholder="Message changes, e.g. shorter, more technical, ask for call first..."
                                className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                              />
                              <div className="grid gap-2 sm:grid-cols-2">
                                <input
                                  value={timingNote}
                                  onChange={(e) => setTimingNote(e.target.value)}
                                  placeholder="Timing, e.g. wait until next Tuesday"
                                  className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                                />
                                <input
                                  value={cadenceNote}
                                  onChange={(e) => setCadenceNote(e.target.value)}
                                  placeholder="Cadence, e.g. follow up once after 5 days"
                                  className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                                />
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() => void controlActivation("pause")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-amber-400/40 bg-amber-50 px-4 py-2.5 text-sm font-bold text-amber-900 disabled:opacity-50"
                              >
                                Pause SIGNAL
                              </button>
                              <button
                                type="button"
                                onClick={() => void controlActivation("update_plan")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-emerald-400/35 bg-violet-400/10 px-4 py-2.5 text-sm font-bold text-gray-700 disabled:opacity-50"
                              >
                                Save adjustments
                              </button>
                              <button
                                type="button"
                                onClick={() => void controlActivation("resume")}
                                disabled={activationControlBusy}
                                className="rounded-lg border border-emerald-400/35 bg-emerald-50 px-4 py-2.5 text-sm font-bold text-emerald-800 disabled:opacity-50"
                              >
                                Resume review queue
                              </button>
                            </div>
                          </div>
                        </details>
                      </div>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-3">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Users className="h-3.5 w-3.5" style={{ color: "#34d399" }} />
                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Selected leads</p>
                        </div>
                        <span className="text-[10px] text-gray-400">{selectedActivation.leadCount} total</span>
                      </div>
                      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                        {selectedActivation.leads.slice(0, 6).map((lead) => (
                          <div key={lead.id} className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-xs font-semibold text-gray-700 truncate">{lead.company}</p>
                              {typeof lead.score === "number" && (
                                <span className="font-mono text-[10px] font-bold" style={{ color: scoreColor(lead.score), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {lead.score}
                                </span>
                              )}
                            </div>
                            <p className="mt-1 line-clamp-2 break-words text-[11px] text-gray-400">{activationLeadText(lead)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-gray-100 px-4 py-6 text-center">
                    <p className="text-sm font-semibold text-gray-500">SIGNAL activity will appear here</p>
                    <p className="text-[11px] text-gray-400 mt-1">Use Activate SIGNAL on Results to create the first work queue item.</p>
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
            <div className="flex items-center gap-3 flex-wrap text-[11px] text-gray-500 px-1">
              <span className="font-bold uppercase tracking-[0.15em] text-[10px]" style={{ color: "#10b981" }}>Cal</span>
              <span>{scoutStats.drafted} drafted</span>
              <span className="text-gray-300">·</span>
              <span>{scoutStats.sent} sent</span>
              <span className="text-gray-300">·</span>
              <span style={{ color: scoutStats.opened > 0 ? "#34d399" : undefined }}>{scoutStats.opened} opened</span>
              <span className="text-gray-300">·</span>
              <span style={{ color: scoutStats.replied > 0 ? "#10b981" : undefined }}>{scoutStats.replied} replied</span>
              <button
                type="button"
                onClick={() => void loadScoutStats()}
                className="ml-auto flex items-center gap-1 text-[10px] text-gray-400 hover:text-gray-600 transition-all"
              >
                <RefreshCw className="h-3 w-3" />
                Refresh
              </button>
            </div>
          )}

          {/* Confirm modals for bulk actions (admin only) */}
          {isAdmin && scoutConfirm === "draft" && (
            <div className="rounded-xl border border-blue-400/30 bg-blue-400/8 px-4 py-3 flex items-center gap-3">
              <p className="text-[11px] text-blue-900 flex-1">Cal will draft outreach emails for all HOT and WARM prospects that don't have one yet. Continue?</p>
              <button onClick={() => void runScoutDraftAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-blue-50 border border-blue-400/40 text-blue-800">Run</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-gray-500">Cancel</button>
            </div>
          )}
          {isAdmin && scoutConfirm === "send" && (
            <div className="rounded-xl border border-emerald-400/30 bg-emerald-400/8 px-4 py-3 flex items-center gap-3">
              <p className="text-[11px] text-emerald-900 flex-1">Cal will send all drafted outreach emails. This triggers live sends via Resend. Continue?</p>
              <button onClick={() => void runScoutSendAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-emerald-50 border border-emerald-400/40 text-emerald-800">Send</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-gray-500">Cancel</button>
            </div>
          )}

          {/* ── Two-panel layout ── */}
          <div className="flex min-h-0 gap-2 border-t border-gray-200 p-2 sm:p-3" style={{ minHeight: "calc(100vh - 200px)" }}>

            {/* LEFT: Lead pipeline (users) or admin stage columns */}
            <div className="pipeline-list-shell flex min-w-0 flex-1 flex-col gap-1 overflow-y-auto">
              <div className="pipeline-list-columns">
                <div className="col-span-5">Company</div>
                <div className="col-span-4 hidden md:block">Signal</div>
                <div className="col-span-1 text-center">Score</div>
                <div className="col-span-2 text-right">Tier</div>
              </div>
              {(loadingLeads || serverSearchLoading) && filtered.length === 0 ? (
                <div className="mx-1 mb-2 rounded-xl border border-dashed border-stone-400 bg-stone-100/80 px-4 py-8 text-center">
                  <RefreshCw className="mx-auto h-6 w-6 animate-spin text-emerald-600" />
                  <p className="mt-3 text-sm font-medium text-stone-700">
                    {serverSearchLoading ? `Searching for "${activeSearchQuery}"…` : "Loading sales pipeline…"}
                  </p>
                </div>
              ) : showKanban ? (
              STAGES.map((stage) => {
                const stageDeals = filtered.filter((d) => d.stage === stage);
                const meta = STAGE_META[stage];
                return (
                  <div key={stage}>
                    {/* Stage header row */}
                    <div className="pipeline-tier-header">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{stageLabel(stage)}</span>
                      <span className="ml-0.5 text-[10px] font-medium text-stone-600">— {stageDesc(stage)}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded"
                        style={{ color: meta.color, background: `${meta.color}15` }}
                      >
                        {stageDeals.length}
                      </span>
                    </div>

                    {/* Inline deal rows */}
                    {stageDeals.length === 0 ? (
                      <div className="mx-1 mb-2 rounded-xl border border-dashed border-gray-200 bg-gray-50/80 px-4 py-3">
                        <p className="text-[11px] text-gray-400 italic">No deals in this stage</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-1.5 mb-3">
                        {stageDeals.map((deal) => {
                          const isSelected = deal.id === effectiveSelectedId;
                          return (
                            <button
                              key={deal.id}
                              onClick={() => setSelectedId(deal.id)}
                              className={`group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${dealRowSurface(isSelected)}`}
                              style={{ borderLeftColor: dealTierColor(deal) }}
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
                                  <span className="text-sm font-semibold text-gray-900 truncate">{deal.company}</span>
                                  <span className="text-[10px] text-gray-400 shrink-0">{deal.location}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: displayStageColor(deal), background: `${displayStageColor(deal)}15` }}
                                  >
                                    {displayStageLabel(deal, true)}
                                  </span>
                                  {(deal as { humanoidPilotTier?: string }).humanoidPilotTier &&
                                    ["ACTIVE_PILOT", "PILOT_INTENT"].includes(
                                      String((deal as { humanoidPilotTier?: string }).humanoidPilotTier),
                                    ) && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      style={{ color: "#059669", background: "rgba(3,218,197,0.12)", border: "1px solid rgba(3,218,197,0.25)" }}
                                    >
                                      Humanoid
                                    </span>
                                  )}
                                </div>
                                <p className="truncate text-[11px] text-stone-700">
                                  {cleanAndClampText(deal.pipelineAction || deal.signal, 160)}
                                </p>
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
                                <span className="text-[10px] text-gray-400 font-mono-data hidden sm:block">
                                  {deal.updatedAt}
                                </span>
                                <ChevronRight
                                  className={`h-3.5 w-3.5 transition-colors ${isSelected ? "text-emerald-600" : "text-gray-300 group-hover:text-emerald-500"}`}
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
                    <div className="pipeline-tier-header">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: meta.dot }} />
                      <span className="text-xs font-bold" style={{ color: meta.color }}>{bucket}</span>
                      <span className="ml-0.5 text-[10px] font-medium text-stone-600">— {meta.desc}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded font-mono"
                        style={{ color: meta.color, background: `${meta.color}15`, fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {bucketDeals.length}
                        {!hasActiveSearch && bucketDeals.length < meta.slotCap ? (
                          <span className="text-gray-400 font-normal"> / {meta.slotCap}</span>
                        ) : null}
                      </span>
                    </div>

                    {bucketDeals.length === 0 ? (
                      <div className="mx-1 mb-2 rounded-xl border border-dashed border-gray-200 bg-gray-50/80 px-4 py-3">
                        <p className="text-[11px] text-gray-400 italic">No leads in this tier right now</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-1.5 mb-3">
                        {bucketDeals.map((deal) => {
                          const isSelected = deal.id === effectiveSelectedId;
                          const tier = userTierBadge(deal);
                          return (
                            <button
                              key={deal.id}
                              type="button"
                              onClick={() => setSelectedId(deal.id)}
                              className={`group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${dealRowSurface(isSelected)}`}
                              style={{ borderLeftColor: dealTierColor(deal) }}
                            >
                              <div
                                className="h-7 w-7 rounded-full border flex items-center justify-center shrink-0"
                                style={{ borderColor: dealTierColor(deal), background: `${dealTierColor(deal)}10` }}
                              >
                                <span className="font-mono text-[10px] font-bold" style={{ color: dealTierColor(deal), fontFamily: "'JetBrains Mono', monospace" }}>
                                  {deal.score}
                                </span>
                              </div>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-sm font-semibold text-gray-900 truncate">{deal.company}</span>
                                  <span className="text-[10px] text-gray-500 shrink-0">{deal.industry}</span>
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                    style={{ color: tier.color, background: `${tier.color}15` }}
                                  >
                                    {tier.label}
                                  </span>
                                  {deal.humanoidPilotTier &&
                                    ["ACTIVE_PILOT", "PILOT_INTENT"].includes(deal.humanoidPilotTier) && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      style={{ color: "#059669", background: "rgba(3,218,197,0.12)", border: "1px solid rgba(3,218,197,0.25)" }}
                                    >
                                      Humanoid
                                    </span>
                                  )}
                                </div>
                                <p className="truncate text-[11px] text-stone-700">
                                  {cleanAndClampText(deal.pipelineAction || deal.signal, 160)}
                                </p>
                              </div>

                              <div className="flex items-center gap-2 shrink-0">
                                <span
                                  className="hidden sm:inline text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide"
                                  style={{ color: deal.signalColor, background: `${deal.signalColor}12` }}
                                >
                                  {deal.signalType}
                                </span>
                                <ChevronRight
                                  className={`h-3.5 w-3.5 transition-colors ${isSelected ? "text-emerald-600" : "text-gray-300 group-hover:text-emerald-500"}`}
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
              className="pipeline-detail-shell flex h-[calc(100vh-100px)] max-h-[calc(100vh-100px)] w-full shrink-0 flex-col overflow-hidden lg:w-[380px] xl:w-[400px] lg:sticky lg:top-20"
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
                  <div className="pipeline-detail-header">
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <div>
                        <p className="mb-0.5 font-display text-base font-semibold text-gray-900">
                          {selected.company}
                        </p>
                        <div className="flex items-center gap-2 text-[11px] text-gray-600">
                          <MapPin className="h-3 w-3" />
                          {selected.location}
                          <span className="text-gray-400">·</span>
                          {selected.industry}
                        </div>
                      </div>
                      <div
                        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 bg-white shadow-sm"
                        style={{ borderColor: dealTierColor(selected), background: `${dealTierColor(selected)}14` }}
                      >
                        <span className="font-mono text-sm font-bold" style={{ color: dealTierColor(selected), fontFamily: "'JetBrains Mono', monospace" }}>
                          {selected.score}
                        </span>
                      </div>
                    </div>

                    {/* Tier / stage badge + contact inline */}
                    <div className="flex items-center gap-3 flex-wrap">
                      {showKanban ? (
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
                        <span className="text-[11px] text-gray-500">
                          <span className="text-gray-600 font-medium">{selected.contact}</span> · {selected.contactTitle}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain flex flex-col">
                  {/* Signal block */}
                  <div className="pipeline-detail-section">
                    {!isAdmin && (() => {
                      const verdict = scoutVerdictForDeal(selected);
                      return (
                        <p className="mb-1.5 flex items-center gap-1.5 text-[11px] leading-snug text-gray-700">
                          <Zap className="h-3 w-3 shrink-0" style={{ color: verdict.color }} />
                          <span className="font-semibold text-gray-900">SIGNAL · {verdict.headline}</span>
                          <span className="text-gray-400">—</span>
                          <span className="text-gray-600">{verdict.detail}</span>
                        </p>
                      );
                    })()}
                    <p className={`${panelSectionLabel} mb-1`}>Buying signal</p>
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: selected.signalColor }} />
                      <div>
                        <p className="text-xs font-semibold mb-0.5" style={{ color: selected.signalColor }}>{selected.signalType}</p>
                        <p className="break-words text-[12px] leading-relaxed text-gray-800">{selected.signal}</p>
                      </div>
                    </div>
                    {(selected.projectTiming?.label || selected.projectTiming?.day_min != null) && (
                      <div className="mt-1.5 flex items-center gap-2 text-[11px] text-gray-600">
                        <Clock className="h-3 w-3 shrink-0 text-emerald-600/90" />
                        <span>
                          <span className="font-semibold text-gray-700">Project window: </span>
                          {selected.projectTiming?.day_min != null && selected.projectTiming?.day_max != null
                            ? `${selected.projectTiming.day_min}–${selected.projectTiming.day_max} days`
                            : selected.projectTiming?.label}
                          {selected.projectTiming?.source === "estimated" && (
                            <span className="text-gray-500"> · estimated from signals</span>
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                  {(selected.notes || selected.shareSummary || selected.leadHighlights || (selected.robotTypesNeeded && selected.robotTypesNeeded.length > 0)) && (
                    <div className="pipeline-detail-section-muted">
                      <button
                        type="button"
                        onClick={() => setIntelligenceOpen((open) => !open)}
                        className="w-full flex items-center gap-2 text-left rounded-lg py-1 transition-colors hover:bg-white"
                        aria-expanded={intelligenceOpen}
                      >
                        <span className={panelSectionLabel}>SIGNAL intelligence</span>
                        {!intelligenceOpen && (
                          <span className="flex-1 min-w-0 text-[11px] leading-snug text-gray-600 truncate">
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
                          <ChevronUp className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                        )}
                      </button>
                      {intelligenceOpen && (
                        <div className="pt-2 space-y-2">
                          {selected.leadHighlights?.specific_problem && (
                            <p className="break-words text-[12px] leading-relaxed text-gray-800">
                              <span className="font-semibold text-gray-900">Problem: </span>
                              {cleanAndClampText(
                                selected.leadHighlights.specific_problem,
                                panelPlan === "anonymous" ? 220 : 280,
                              )}
                            </p>
                          )}
                          {(selected.leadHighlights?.why_lead || []).length > 0 && (
                            <ul className="list-disc pl-4 text-[11px] leading-relaxed text-gray-600 space-y-1">
                              {(selected.leadHighlights?.why_lead || [])
                                .slice(0, panelPlan === "anonymous" ? 2 : 3)
                                .map((line, i) => (
                                  <li key={i}>{cleanAndClampText(line, panelPlan === "anonymous" ? 140 : 160)}</li>
                                ))}
                            </ul>
                          )}
                          {(selected.notes || selected.shareSummary) && (
                            <p className="break-words text-[12px] leading-relaxed text-gray-700">
                              {cleanAndClampText(
                                selected.notes || selected.shareSummary,
                                panelPlan === "anonymous" ? 240 : 360,
                              )}
                            </p>
                          )}
                          {selected.robotTypesNeeded && selected.robotTypesNeeded.length > 0 && (
                            <p className="text-[11px] leading-relaxed text-gray-600">
                              <span className="font-semibold text-gray-900/90">Robot fit: </span>
                              {selected.robotTypesNeeded.join(" · ")}
                            </p>
                          )}
                          {showFullPanel && (selected.leadHighlights?.agent_enrichment?.rich_facts || []).length > 0 && (
                            <div className="space-y-1 rounded-lg border border-emerald-200 bg-emerald-50/60 p-2.5">
                              {(selected.leadHighlights?.agent_enrichment?.rich_facts || []).slice(0, 2).map((fact, i) => (
                                <p key={i} className="text-[11px] leading-relaxed text-gray-700">
                                  {cleanAndClampText(fact.claim || "", 200)}
                                </p>
                              ))}
                            </div>
                          )}
                          {panelPlan === "anonymous" && (
                            <p className="text-[10px] leading-relaxed text-emerald-700">
                              Sign up free to unlock full SIGNAL research and connect to HubSpot.
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
                  <div className="shrink-0 px-5 py-3 border-b border-gray-100">
                    <button
                      type="button"
                      onClick={() => setResearchOpen((open) => !open)}
                      className="w-full flex items-center gap-2 text-left rounded-lg py-1 transition-colors hover:bg-white"
                      aria-expanded={researchOpen}
                    >
                      <span className={panelSectionLabel}>SIGNAL research</span>
                      {!researchOpen && (
                        <span className="flex-1 min-w-0 text-[11px] text-gray-500 truncate">
                          {(selected.researchUpdates || []).length > 0
                            ? `${(selected.researchUpdates || []).length} cited update(s)`
                            : "Monitoring for new material"}
                        </span>
                      )}
                      {researchOpen ? (
                        <ChevronUp className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                      )}
                    </button>
                    {researchOpen && (
                      <div className="pt-3">
                        {selected.lastResearchedAt && (
                          <p className="mb-2 text-[10px] text-gray-500">
                            Last checked {formatResearchTime(selected.lastResearchedAt)}
                          </p>
                        )}
                        {loadingResearch && !selected.researchUpdates ? (
                          <p className="text-[11px] leading-relaxed text-gray-500">SIGNAL is loading cited updates…</p>
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
                                <p className="break-words text-[11px] leading-relaxed text-gray-700">
                                  {cleanAndClampText(update.summary, 220)}
                                </p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[11px] leading-relaxed text-gray-500">
                            SIGNAL will add cited updates when fresh signals arrive for this account.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                  )}

                  {/* SIGNAL research upsell — free signed-in workspace */}
                  {showStandardPanel && (
                    <div className="shrink-0 px-5 py-3 border-b border-gray-100">
                      <div className="relative overflow-hidden rounded-xl border border-emerald-400/20 p-3" style={{ background: "rgba(5,150,105,0.06)" }}>
                        <div className="pointer-events-none select-none space-y-2 blur-[3px] opacity-60" aria-hidden>
                          <div className="rounded-lg border p-2.5" style={{ borderColor: "rgba(255,176,0,0.22)", background: "rgba(255,176,0,0.08)" }}>
                            <p className="text-[11px] font-semibold text-amber-200">Cited research update</p>
                            <p className="mt-1 text-[11px] text-gray-600">New procurement signal with source link and timing window…</p>
                          </div>
                          <div className="rounded-lg border p-2.5" style={{ borderColor: "rgba(255,176,0,0.22)", background: "rgba(255,176,0,0.08)" }}>
                            <p className="text-[11px] font-semibold text-amber-200">Material change detected</p>
                            <p className="mt-1 text-[11px] text-gray-600">Budget language and deployment timeline extracted…</p>
                          </div>
                        </div>
                        <div className="relative mt-3 space-y-2">
                          <p className={panelSectionLabel}>SIGNAL research</p>
                          <p className="text-[11px] leading-relaxed text-gray-600">
                            Pro unlocks cited research updates on HOT and WARM leads — budget, timing, and source links refreshed automatically.
                          </p>
                          <Link
                            href="/pricing?reason=research"
                            className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold text-gray-900 transition-colors hover:opacity-90"
                            style={{ background: "#059669" }}
                          >
                            Upgrade to Pro
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Cal outreach — workspace users */}
                  {showKanban && session?.access_token && (
                  <div className="shrink-0 px-5 py-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5" style={{ color: "#059669" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Cal&apos;s Draft</p>
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
                              : { background: "rgba(5,150,105,0.12)", color: "#10b981" }
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
                        <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full text-gray-600 bg-gray-100 border border-gray-200">
                          <Eye className="h-2.5 w-2.5" /> Tracking active
                        </span>
                      </div>
                    )}

                    {selected.outreachSubject && (
                      <div className="mb-2 p-2.5 rounded-lg" style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.18)" }}>
                        <p className="text-[10px] text-gray-400 mb-0.5 uppercase tracking-wide">Subject</p>
                        <p className="text-xs font-semibold" style={{ color: "#FFB000" }}>{selected.outreachSubject}</p>
                      </div>
                    )}

                    {selected.outreachBody ? (
                      <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
                        <pre className="whitespace-pre-wrap break-words font-sans text-[11px] leading-relaxed text-gray-500">
                          {selected.outreachBody}
                        </pre>
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-gray-200 px-3 py-4">
                        <p className="text-[11px] leading-relaxed text-gray-400 mb-3">
                          No Cal draft yet. Run SIGNAL on this lead to refresh inference and generate outreach.
                        </p>
                        <button
                          type="button"
                          disabled={developingLeadId === selected.id}
                          onClick={() => void developLeadWithScout(selected)}
                          className="w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-[11px] font-bold border transition-all disabled:opacity-50"
                          style={{ background: "rgba(3,218,197,0.08)", borderColor: "rgba(3,218,197,0.28)", color: "#047857" }}
                        >
                          {developingLeadId === selected.id
                            ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            : <Zap className="h-3.5 w-3.5" />
                          }
                          {developingLeadId === selected.id ? "SIGNAL developing…" : "Develop lead with SIGNAL"}
                        </button>
                      </div>
                    )}

                    {selected.outreachBody && showKanban && (
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
                        style={{ background: "rgba(52,211,153,0.08)", borderColor: "rgba(52,211,153,0.28)", color: "#047857" }}
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

                  {!showKanban && (
                    <div className="pipeline-detail-actions">
                      <HubSpotCtaLink
                        connected={hubspotIntegration?.connected}
                        hasSession={Boolean(session?.access_token)}
                        className="sb-btn"
                      />
                      {session?.access_token ? (
                        <button
                          type="button"
                          onClick={() => void handleSaveLead(selected)}
                          disabled={advancingLeadId === selected.id}
                          className="sb-btn sb-btn-primary"
                        >
                          {advancingLeadId === selected.id
                            ? <RefreshCw className="h-3 w-3 animate-spin" />
                            : <Zap className="h-3 w-3" />
                          }
                          {advancingLeadId === selected.id ? "Saving…" : "Save to workspace"}
                        </button>
                      ) : (
                        <Link
                          href={`/signup?next=${encodeURIComponent(`/pipeline?lead=${selected.id}`)}`}
                          className="sb-btn sb-btn-primary"
                        >
                          Activate SIGNAL
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      )}
                    </div>
                  )}

                  {showKanban && session?.access_token && selected && (
                    <div className="shrink-0 px-5 py-3 border-t border-gray-100">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5">
                          <FileText className="h-3.5 w-3.5" style={{ color: "#fbbf24" }} />
                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Proposal</p>
                        </div>
                        <button
                          type="button"
                          disabled={proposalBusy}
                          onClick={() => void generateProposalForDeal(selected)}
                          className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded transition-all disabled:opacity-50"
                          style={{ background: "rgba(251,191,36,0.12)", color: "#fbbf24" }}
                        >
                          {proposalBusy ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                          {proposalBusy ? "Generating…" : "Generate"}
                        </button>
                      </div>
                      <p className="text-[11px] text-gray-500 leading-relaxed">
                        SCOUT writes a structured proposal from this lead&apos;s signal, score, and industry — then preview or download PDF.
                      </p>
                      {proposalData && (
                        <button
                          type="button"
                          onClick={() => setProposalOpen(true)}
                          className="mt-2 inline-flex items-center gap-1.5 text-[10px] font-bold text-amber-800 underline"
                        >
                          <Download className="h-3 w-3" />
                          Open last proposal preview
                        </button>
                      )}
                    </div>
                  )}

                  {/* Action bar — workspace kanban */}
                  {showKanban && session?.access_token && selected && (
                  <div className="pipeline-detail-actions">
                    {STAGES.indexOf(selected.stage) > 0 && (
                      <button
                        onClick={() => moveStage(selected.id, -1)}
                        className="sb-btn"
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
                      className="sb-btn"
                    >
                      <Mail className="h-3 w-3" />
                      Approve &amp; Copy
                    </button>
                    {STAGES.indexOf(selected.stage) < STAGES.length - 1 && (
                      <button
                        onClick={() => void handleAdvanceLead(selected)}
                        disabled={advancingLeadId === selected.id}
                        className="sb-btn sb-btn-primary"
                      >
                        {advancingLeadId === selected.id ? "Advancing..." : "Advance with Cal"}
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center bg-stone-50 p-8 text-center">
                  <Target className="mb-3 h-10 w-10 text-stone-400" />
                  <p className="text-sm font-medium text-stone-700">
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
                      className="mt-4 rounded-lg border border-gray-200 px-4 py-2 text-xs font-semibold text-gray-600 transition-colors hover:border-gray-300 hover:text-gray-900"
                    >
                      Retry loading lead
                    </button>
                  ) : null}
                </div>
              )}
            </div>
          </div>
          </div>
        </div>
      </main>

      {/* Email Preview Modal — workspace users */}
      {showKanban && previewOpen && selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
          onClick={() => setPreviewOpen(false)}
        >
          <div
            className="relative w-full max-w-lg rounded-2xl border p-6 flex flex-col gap-4"
            style={{ background: "#ffffff", borderColor: "rgba(5,150,105,0.3)", maxHeight: "85vh", overflowY: "auto" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-0.5" style={{ color: "#10b981" }}>Email Preview</p>
                <p className="text-sm font-bold text-gray-900" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>{selected.company}</p>
              </div>
              <button
                onClick={() => setPreviewOpen(false)}
                className="text-gray-400 hover:text-gray-600 text-xs font-semibold px-2 py-1 rounded"
              >
                Close
              </button>
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-[10px] uppercase tracking-widest text-gray-400 mb-1">From</p>
              <p className="text-xs text-gray-600">Cal &lt;cal@readyforrobots.com&gt;</p>
            </div>
            {selected.contact && (
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <p className="text-[10px] uppercase tracking-widest text-gray-400 mb-1">To</p>
                <p className="text-xs text-gray-600">{selected.contact}</p>
              </div>
            )}
            <div className="rounded-xl border border-amber-400/20 p-4" style={{ background: "rgba(255,176,0,0.05)" }}>
              <p className="text-[10px] uppercase tracking-widest text-gray-400 mb-1">Subject</p>
              <p className="text-xs font-semibold" style={{ color: "#FFB000" }}>{selected.outreachSubject}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-[10px] uppercase tracking-widest text-gray-400 mb-2">Message</p>
              <pre className="whitespace-pre-wrap break-words font-sans text-[12px] leading-loose text-gray-600">
                {selected.outreachBody}
              </pre>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyDraft}
                className="flex-1 flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-[11px] font-bold border transition-all"
                style={copied
                  ? { background: "rgba(52,211,153,0.1)", borderColor: "rgba(52,211,153,0.3)", color: "#047857" }
                  : { background: "rgba(5,150,105,0.1)", borderColor: "rgba(5,150,105,0.3)", color: "#047857" }
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
      {session?.access_token && (
        <ProposalPdfModal
          open={proposalOpen}
          onClose={() => setProposalOpen(false)}
          data={proposalData}
          accessToken={session.access_token}
          dealMeta={
            selected
              ? {
                  robotCategory: selected.robotTypesNeeded?.[0],
                  signal: selected.signal,
                  scoutScore: selected.score,
                }
              : undefined
          }
        />
      )}
      <AlertDialog open={saveLimitOpen} onOpenChange={setSaveLimitOpen}>
        <AlertDialogContent className="border-emerald-500/30 bg-[#12082a] text-cream">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-cream">Workspace lead limit reached</AlertDialogTitle>
            <AlertDialogDescription className="text-cream/70">
              {saveLimitMessage || "Upgrade to Pro to save more pipeline leads and unlock research."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-gray-200 bg-transparent text-cream hover:bg-white/5">
              Not now
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-emerald-600 text-white hover:bg-emerald-600"
              onClick={() => {
                window.location.href = "/pricing?reason=saved_leads";
              }}
            >
              Upgrade to Pro
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
