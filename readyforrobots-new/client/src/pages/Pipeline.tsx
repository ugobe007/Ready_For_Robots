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
import PageHeroDark from "@/components/layout/PageHeroDark";
import ProposalPdfModal, { type ProposalData } from "@/components/ProposalPdfModal";
import { Link, useLocation, useSearch } from "wouter";
import { openWorkspaceHref } from "@/lib/adminNavLinks";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import {
  fetchWithTimeout,
  fetchWithTimeoutRetry,
  getApiBase,
  getPublicReadApiBase,
  liveFetchInit,
  publicFetchInit,
  readSurfaceCache,
  writeSurfaceCache,
} from "@/lib/apiBase";
import { marketInsightForIndustry } from "@/lib/industryContext";
import { dealMatchesIndustrySearch, pipelineSearchSuggestions } from "@/lib/industrySearchLexicon";
import { mapApiLeadToDeal, crmOutreachStageFromPipelineStage, type ApiLead } from "@/lib/pipelineLeadMap";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { cleanAndClampText, cleanScrapedText } from "@/lib/text";
import { signupHrefForLead } from "@/lib/signupHref";
import { trackFirstSave, trackMarketingEvent } from "@/lib/siteAnalytics";
import {
  isFreshSignup,
  markFirstSaveGuideSeen,
  shouldShowFirstSaveGuide,
} from "@/lib/firstSaveGuide";
import LeadShareBar from "@/components/LeadShareBar";
import CrmPathFork from "@/components/pipeline/CrmPathFork";
import FirstSaveNudge from "@/components/pipeline/FirstSaveNudge";
import FirstSaveGuideModal from "@/components/pipeline/FirstSaveGuideModal";
import PipelineLeadActionMeta from "@/components/pipeline/PipelineLeadActionMeta";
import PipelineOutreachValuePanel from "@/components/pipeline/PipelineOutreachValuePanel";
import CalLeadDrop, { dealToCalDrop } from "@/components/pipeline/CalLeadDrop";
import AnonymousValueStrip from "@/components/pipeline/AnonymousValueStrip";
import ActivationChecklist from "@/components/pipeline/ActivationChecklist";
import WorkspaceQuickLinks from "@/components/pipeline/WorkspaceQuickLinks";
import PipelineSalesWorkflowRail from "@/components/pipeline/PipelineSalesWorkflowRail";
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

type Stage = "New Signal" | "Discovered" | "Draft Ready" | "Outreach Sent" | "Qualified" | "Meeting Set";
type QualityBandFilter = "all" | "high" | "medium" | "low";
type QualitySort =
  | "default"
  | "quality_desc"
  | "quality_asc"
  | "buyer_authenticity"
  | "urgency_window"
  | "robot_fit_confidence"
  | "decision_maker_confidence"
  | "contactability_confidence";

type FirstThreeActionsState = {
  started: boolean;
  saved: boolean;
  copied: boolean;
  sent: boolean;
  dismissed: boolean;
};

type FirstThreeStep = "save_lead" | "copy_draft" | "send_outreach";

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
  contactPhone?: string;
  linkedInProfile?: {
    url?: string;
    score?: number;
    confidence?: string;
    person?: string;
    person_title?: string;
  };
  contactTitle?: string;
  outreachSubject?: string;
  outreachBody?: string;
  notes?: string;
  shareSummary?: string;
  shareBlurb?: string;
  pipelineAction?: string;
  leadQuality?: {
    schema?: string;
    overall_score?: number;
    confidence_band?: string;
    dimension_scores?: Record<string, number>;
    weights?: Record<string, number>;
    weight_source?: string;
    missing_fields_count?: number;
    evidence_traces?: Array<{ dimension?: string; score?: number; evidence?: string }>;
    quality_gate?: { passed?: boolean; reason?: string };
  };
  confidenceBand?: string;
  evidenceTrace?: Array<{ dimension?: string; score?: number; evidence?: string }>;
  humanoidPilotTier?: string;
  humanoidPilotScore?: number;
  humanoidPilotLabel?: string;
  humanoidPilotAction?: string;
  humanoidOriginStatus?: string;
  humanoidNonUsVendorFlag?: boolean;
  humanoidNonUsVendorCount?: number;
  humanoidNonUsVendorModels?: string[];
  priorityTier?: string;
  robotTypesNeeded?: string[];
  workUnitId?: string;
  workflowFamily?: string;
  workTask?: string;
  workMatch?: number;
  workMatchLabel?: string;
  workMatchScore?: number;
  workMatchManufacturer?: string;
  workHardBlockers?: string[];
  comparableDeployment?: {
    deployment_id?: string;
    robot?: string | null;
    customer?: string | null;
    facility?: string | null;
    work_type?: string | null;
    deployment_stage?: string | null;
    evidence_level?: string | null;
    confidence?: number | null;
  };
  hermesQualify?: {
    automation_fit?: number | null;
    labor_intensity?: string | null;
    facility_clarity?: string | null;
    blockers?: string[];
    rationale?: string | null;
    vendor_shortlist?: Array<{ vendor?: string | null; model?: string | null; why?: string | null }>;
    truth_state?: string | null;
    updated_at?: string | null;
  };
  hermesJobTitles?: string[];
  hermesDecisionMakers?: Array<{
    name?: string;
    title?: string | null;
    source_url?: string | null;
    confidence?: number | null;
  }>;
  researchUpdates?: Array<{
    id: number;
    update_type?: string;
    title?: string;
    summary?: string;
    source_url?: string | null;
    source_domain?: string | null;
    source_kind?: string | null;
    source_label?: string | null;
    evidence_tension?: string | null;
    recommended_action?: string | null;
    detected_at?: string | null;
    significance_score?: number;
  }>;
  lastResearchedAt?: string | null;
  latestMaterialUpdate?: {
    id: number;
    title?: string;
    summary?: string;
    source_domain?: string | null;
    source_kind?: string | null;
    source_label?: string | null;
    evidence_tension?: string | null;
    recommended_action?: string | null;
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
  crmEvidence?: {
    friction_point?: string | null;
    workflow_scope?: {
      count?: number;
      label?: string | null;
      items?: string[];
    };
    timing?: {
      label?: string | null;
      source?: string | null;
      confidence?: number | null;
    };
    robot_type?: {
      label?: string | null;
      items?: string[];
    };
    budget?: {
      top_amount?: string | null;
      signals?: Array<{ amount?: string; context?: string; source_url?: string }>;
      has_budget?: boolean;
    };
    decision_makers?: Array<{ name?: string; title?: string; source_url?: string; confidence?: number }>;
    similar_deployments?: Array<{
      title?: string | null;
      summary?: string | null;
      source_domain?: string | null;
      source_url?: string | null;
      source_label?: string | null;
      evidence_tension?: string | null;
    }>;
    missing_fields?: Array<{
      key?: string;
      label?: string;
      status?: string;
      research_prompt?: string;
    }>;
    research_status?: {
      needs_research?: boolean;
      state?: string;
      missing_count?: number;
    };
  };
  contactIntelligence?: {
    status?: string;
    updated_at?: string;
    phone?: {
      best?: {
        phone?: string;
        raw?: string;
        source?: string;
        score?: number;
        evidence?: string;
      } | null;
      candidates?: Array<{
        phone?: string;
        raw?: string;
        source?: string;
        score?: number;
        evidence?: string;
      }>;
    };
    linkedin?: {
      status?: string;
      best_profile?: {
        url?: string;
        title?: string;
        snippet?: string;
        score?: number;
        confidence?: string;
        person?: string;
        person_title?: string;
      } | null;
      disambiguation?: {
        status?: string;
        target_person?: string;
        target_company?: string;
        reason?: string;
        script?: string[];
        candidates?: Array<{
          url?: string;
          title?: string;
          snippet?: string;
          score?: number;
        }>;
      } | null;
    };
    sales_intuition?: {
      why_sales_lead?: {
        specific_problem?: string | null;
        reasons?: string[];
      };
      robot_history?: Array<{
        signal_type?: string | null;
        summary?: string;
        source_url?: string | null;
      }>;
      larger_opportunity?: {
        industry?: string | null;
        points?: string[];
      };
      competitor_robot_usage?: Array<{
        title?: string;
        summary?: string;
        source_url?: string | null;
        source_domain?: string | null;
      }>;
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

const STAGES: Stage[] = ["New Signal", "Discovered", "Draft Ready", "Outreach Sent", "Qualified", "Meeting Set"];

const STAGE_META: Record<Stage, { color: string; dot: string; label: string; desc: string }> = {
  "New Signal":    { color: "#10b981", dot: "#10b981", label: "New Signal",    desc: "Just detected" },
  "Discovered":    { color: "#14b8a6", dot: "#14b8a6", label: "Discovered",    desc: "Saved for review" },
  "Draft Ready":   { color: "#60a5fa", dot: "#60a5fa", label: "Draft Ready",   desc: "Outreach drafted" },
  "Outreach Sent": { color: "#FFB000", dot: "#FFB000", label: "Outreach Sent", desc: "Awaiting reply" },
  "Qualified":     { color: "#34d399", dot: "#34d399", label: "Qualified",     desc: "Engaged buyer" },
  "Meeting Set":   { color: "#FFB000", dot: "#FFB000", label: "Meeting Set",   desc: "On the calendar" },
};

type UserBucket = "Hot Leads" | "Warm Leads" | "Monitoring";

const PIPELINE_HOT_SLOTS = 40;
const PIPELINE_WARM_SLOTS = 30;
const PIPELINE_MONITOR_SLOTS = 20;
const PIPELINE_FEED_TOTAL = PIPELINE_HOT_SLOTS + PIPELINE_WARM_SLOTS + PIPELINE_MONITOR_SLOTS;

const USER_BUCKETS: UserBucket[] = ["Hot Leads", "Warm Leads", "Monitoring"];

const FIRST_THREE_ACTIONS_KEY = "rfr_first_three_actions_v1";
const FIRST_THREE_ABANDON_MS = 120_000;
const FIRST_THREE_ACTIONS_INITIAL: FirstThreeActionsState = {
  started: false,
  saved: false,
  copied: false,
  sent: false,
  dismissed: false,
};

function firstThreeNextStep(state: FirstThreeActionsState): FirstThreeStep | null {
  if (!state.saved) return "save_lead";
  if (!state.copied) return "copy_draft";
  if (!state.sent) return "send_outreach";
  return null;
}

function firstThreeCompletedCount(state: FirstThreeActionsState): number {
  return [state.saved, state.copied, state.sent].filter(Boolean).length;
}

function readFirstThreeActions(): FirstThreeActionsState {
  if (typeof window === "undefined") return FIRST_THREE_ACTIONS_INITIAL;
  try {
    const raw = window.localStorage.getItem(FIRST_THREE_ACTIONS_KEY);
    if (!raw) return FIRST_THREE_ACTIONS_INITIAL;
    const parsed = JSON.parse(raw) as Partial<FirstThreeActionsState>;
    return {
      started: Boolean(parsed.started),
      saved: Boolean(parsed.saved),
      copied: Boolean(parsed.copied),
      sent: Boolean(parsed.sent),
      dismissed: Boolean(parsed.dismissed),
    };
  } catch {
    return FIRST_THREE_ACTIONS_INITIAL;
  }
}

function writeFirstThreeActions(state: FirstThreeActionsState) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(FIRST_THREE_ACTIONS_KEY, JSON.stringify(state));
  } catch {
    /* private mode */
  }
}

function FirstThreeActionsProgress({
  state,
  onCopyDraft,
  onPrimaryAction,
  primaryActionLabel,
  primaryActionDisabled,
  helperText,
  onDismiss,
}: {
  state: FirstThreeActionsState;
  onCopyDraft: () => void;
  onPrimaryAction: () => void;
  primaryActionLabel: string;
  primaryActionDisabled: boolean;
  helperText: string;
  onDismiss: () => void;
}) {
  const steps = [state.saved, state.copied, state.sent];
  const completed = firstThreeCompletedCount(state);
  const pct = Math.round((completed / steps.length) * 100);
  const next = firstThreeNextStep(state);
  const nextStep = next === "save_lead"
    ? "Save your first lead"
    : next === "copy_draft"
      ? "Copy the outreach draft"
      : next === "send_outreach"
        ? "Send first outreach"
        : "Completed";

  return (
    <div className="mb-2 rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-2.5">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-800">First 3 actions</p>
          <p className="text-[11px] text-emerald-900/80">Continue where you left off: {nextStep}</p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="text-[10px] font-semibold text-emerald-700 hover:text-emerald-900"
        >
          Hide
        </button>
      </div>

      <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-emerald-100">
        <div className="h-full rounded-full bg-emerald-600 transition-all" style={{ width: `${pct}%` }} />
      </div>

      <div className="grid grid-cols-3 gap-2 text-[10px] text-gray-700">
        <span className={state.saved ? "font-semibold text-emerald-700" : ""}>1. Save lead</span>
        <button
          type="button"
          onClick={onCopyDraft}
          disabled={state.copied}
          className={`text-left ${state.copied ? "font-semibold text-emerald-700" : "hover:text-emerald-800"}`}
        >
          2. Copy draft
        </button>
        <span className={state.sent ? "font-semibold text-emerald-700" : ""}>3. Send outreach</span>
      </div>

      {!state.sent && (
        <div className="mt-2 rounded-lg border border-emerald-200/80 bg-white/80 px-2.5 py-2">
          <p className="text-[10px] text-gray-600">{helperText}</p>
          <button
            type="button"
            disabled={primaryActionDisabled}
            onClick={onPrimaryAction}
            className="mt-1.5 inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-2.5 py-1.5 text-[10px] font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {primaryActionLabel}
            <ArrowRight className="h-2.5 w-2.5" />
          </button>
        </div>
      )}
    </div>
  );
}

const USER_BUCKET_META: Record<UserBucket, { color: string; dot: string; desc: string; slotCap: number }> = {
  "Hot Leads":   { color: "#34d399", dot: "#34d399", desc: "High-alignment opportunities ready for MSD", slotCap: PIPELINE_HOT_SLOTS },
  "Warm Leads":  { color: "#FFB000", dot: "#FFB000", desc: "Qualified signals pending deeper alignment", slotCap: PIPELINE_WARM_SLOTS },
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

const PIPELINE_LIMIT_FREE = PIPELINE_FEED_TOTAL;
const PIPELINE_LIMIT_PAID = PIPELINE_FEED_TOTAL;
/** Target curated working list after Results → Pipeline onboarding. */
const BUILD_PIPELINE_TARGET = 15;
/** Time each lead stays in the CRM detail panel during auto-rotation (anonymous browse). */
const PIPELINE_LEAD_READ_MS = 7_000;
const PIPELINE_SESSION_KEY = "pipeline_feed_v6";
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
const PIPELINE_TIMEOUT = 8_000;
const PIPELINE_SUBMIT_CONTEXT_KEY = "rfr_pipeline_submit_context";
const PIPELINE_SUBMIT_CONTEXT_TTL_MS = 2 * 60 * 60 * 1000;

function getSubmittedUrlFromStorage(): string {
  if (typeof window === "undefined") return "";
  try {
    const raw = window.sessionStorage.getItem(PIPELINE_SUBMIT_CONTEXT_KEY);
    if (!raw) return "";
    const parsed = JSON.parse(raw) as { url?: string; ts?: number };
    const url = (parsed.url || "").trim();
    const ts = Number(parsed.ts || 0);
    if (!url) return "";
    if (Date.now() - ts > PIPELINE_SUBMIT_CONTEXT_TTL_MS) return "";
    return url;
  } catch {
    return "";
  }
}
const BY_ID_TIMEOUT_MS = 8_000;
const BY_ID_DEEPLINK_TIMEOUT_MS = 12_000;
const BY_ID_FAIL_COOLDOWN_MS = 90 * 1000;
const BY_ID_BREAKER_OPEN_MS = 45 * 1000;
const BY_ID_BREAKER_FAIL_STREAK = 3;
const BY_ID_COOLDOWN_TRACK_MAX = 300;

type PipelineFeedPayload = {
  summary?: LeadSummary;
  leads?: ApiLead[];
  entitlements?: PipelineEntitlements;
  cache_pending?: boolean;
};
type SubmittedUrlMatchPayload = {
  submitted_url?: string;
  submitted_domain?: string;
  matching_mode?: "matched" | "no_match" | "no_profile";
  robot_capabilities?: { type?: string; use_case?: string; capabilities?: string[]; profile_score?: number };
  match_count?: number;
  leads?: ApiLead[];
};

async function fetchPipelineLeadsFallback(base: string, headers?: HeadersInit): Promise<ApiLead[]> {
  const res = await fetchWithTimeoutRetry(
    `${base}/api/leads?limit=50&sort=score&exclude_junk=true`,
    publicFetchInit({ headers }),
    PIPELINE_TIMEOUT,
    { retries: 1, retryDelayMs: 800 },
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
    publicFetchInit(),
    PIPELINE_TIMEOUT,
    { retries: 1, retryDelayMs: 800 },
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

async function hydratePipelineFallback(
  base: string,
  headers: HeadersInit | undefined,
  setters: {
    setDeals: Dispatch<SetStateAction<Deal[]>>;
    setSelectedId: (fn: (prev: number | null) => number | null) => void;
    setSummary: (v: LeadSummary | null) => void;
    setEntitlements: (v: PipelineEntitlements | null) => void;
    setMarketSnippet: (v: MarketSnippet) => void;
  },
  crmStages: Record<number, string>,
  isCancelled: () => boolean,
) {
  const [fallbackLeads, summary] = await Promise.all([
    fetchPipelineLeadsFallback(base, headers),
    fetchPipelineSummaryFallback(base),
  ]);
  if (isCancelled()) return;

  const payload: PipelineFeedPayload = {};
  if (fallbackLeads.length > 0) payload.leads = fallbackLeads;
  if (summary && (summary.hot ?? summary.companies_in_database)) payload.summary = summary;
  if (!payload.leads?.length && !payload.summary) return;

  writeSurfaceCache(PIPELINE_SESSION_KEY, payload);
  applyPipelineFeed(payload, setters, crmStages);
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
        <p className="pipeline-metric-label">{label}</p>
        <span className="h-2 w-2 rounded-full ring-2 ring-slate-200" style={{ background: color }} />
      </div>
      <p className="pipeline-metric-value font-mono-data pl-2">{value}</p>
      <p className="pipeline-metric-sub mt-1 pl-2">{sub}</p>
    </div>
  );
}

function dealRowSurface(isSelected: boolean) {
  return isSelected ? "pipeline-deal-row pipeline-deal-row-selected" : "pipeline-deal-row pipeline-deal-row-hover";
}

function buildRotatedPipelineDeals(source: Deal[], offset: number): Deal[] {
  const out: Deal[] = [];
  for (const [bucketIndex, bucket] of USER_BUCKETS.entries()) {
    const pool = source.filter((d) => userBucketForDeal(d) === bucket);
    const cap = USER_BUCKET_META[bucket].slotCap;
    if (pool.length <= cap) {
      out.push(...pool);
      continue;
    }
    const start = (offset + bucketIndex * 7) % pool.length;
    for (let i = 0; i < cap; i += 1) {
      out.push(pool[(start + i) % pool.length]);
    }
  }
  return out;
}

function pickRotatingWindow(source: Deal[], limit: number, offset: number): Deal[] {
  if (source.length <= limit) return source;
  const start = offset % source.length;
  const out: Deal[] = [];
  for (let i = 0; i < limit; i += 1) {
    out.push(source[(start + i) % source.length]);
  }
  return out;
}

function bucketPoolCanRotate(source: Deal[]): boolean {
  return USER_BUCKETS.some((bucket) => {
    const count = source.filter((d) => userBucketForDeal(d) === bucket).length;
    return count > USER_BUCKET_META[bucket].slotCap;
  });
}

function PipelineScoreBadge({
  score,
  deal,
  size = "sm",
}: {
  score: number;
  deal?: Pick<Deal, "score" | "priorityTier">;
  size?: "sm" | "lg";
}) {
  const accent = deal ? dealTierColor(deal) : scoreColor(score);
  return (
    <div
      className={size === "lg" ? "pipeline-score-badge pipeline-score-badge-lg" : "pipeline-score-badge"}
      style={{ borderColor: accent }}
    >
      <span>{score}</span>
    </div>
  );
}

function workflowFamilyLabel(family?: string): string {
  if (!family || family === "unknown") return "";
  return family.replace(/_/g, " ");
}

function WorkMatchBadge({
  deal,
  size = "sm",
}: {
  deal: Pick<
    Deal,
    | "workMatch"
    | "workMatchLabel"
    | "workMatchManufacturer"
    | "workflowFamily"
    | "workHardBlockers"
    | "comparableDeployment"
    | "hermesQualify"
  >;
  size?: "sm" | "lg";
}) {
  const wm = deal.workMatch;
  const blockers = deal.workHardBlockers || [];
  const family = workflowFamilyLabel(deal.workflowFamily);
  if (wm == null && !family) return null;
  const blocked = blockers.length > 0;
  const label =
    wm != null
      ? `WM ${Math.round(wm)}`
      : family
        ? `Work`
        : null;
  if (!label) return null;
  const titleParts = [
    wm != null ? `Work Match ${Math.round(wm)}%${deal.workMatchLabel ? ` (${deal.workMatchLabel})` : ""}` : null,
    family ? `Workflow: ${family}` : null,
    deal.workMatchManufacturer ? `Best robot: ${deal.workMatchManufacturer}` : null,
    deal.hermesQualify?.automation_fit != null
      ? `Hermes automation fit ${Math.round(Number(deal.hermesQualify.automation_fit))}`
      : null,
    blocked ? `Blockers: ${blockers.join(", ")}` : null,
    deal.comparableDeployment?.robot
      ? `Evidence: ${deal.comparableDeployment.robot} @ ${deal.comparableDeployment.customer || "site"}`
      : null,
  ].filter(Boolean);
  const color = blocked ? "#b45309" : wm != null && wm >= 70 ? "#047857" : wm != null && wm >= 50 ? "#0369a1" : "#57534e";
  return (
    <div
      className={size === "lg" ? "pipeline-score-badge pipeline-score-badge-lg" : "pipeline-score-badge"}
      style={{ borderColor: color, color, minWidth: size === "lg" ? undefined : "2.75rem" }}
      title={titleParts.join(" · ")}
    >
      <span className="text-[10px] font-bold tracking-tight">{label}</span>
    </div>
  );
}

function dealToShareLead(deal: Deal) {
  return {
    id: deal.id,
    company_name: deal.company,
    priority_tier: deal.priorityTier,
    share_summary: deal.shareSummary || deal.signal,
    share_blurb: deal.shareBlurb,
    signal_type: deal.signalType,
    pipeline_action: deal.pipelineAction,
    robot_types_needed: robotTypesForDeal(deal),
  };
}

function robotTypesForDeal(deal: Deal): string[] {
  const fromApi = (deal.robotTypesNeeded || []).filter(Boolean);
  if (fromApi.length) return fromApi;
  const highlights = deal.leadHighlights;
  const fallback = [
    ...(highlights?.robot_categories || []),
    ...(highlights?.application_areas || []),
  ].filter(Boolean) as string[];
  return fallback;
}

function evidenceStackForDeal(deal: Deal) {
  const evidence = deal.crmEvidence;
  const workflowItems = (evidence?.workflow_scope?.items || []).filter(Boolean);
  const robotItems = (evidence?.robot_type?.items || []).filter(Boolean);
  const budgetSignals = (evidence?.budget?.signals || []).filter(Boolean);
  const decisionMakers = (evidence?.decision_makers || []).filter(Boolean);
  const deploymentExamples = (evidence?.similar_deployments || []).filter(Boolean);
  const fallbackDeploymentExamples = (deal.researchUpdates || [])
    .filter((update) => update.update_type === "deployment" || update.update_type === "partnership")
    .slice(0, 3)
    .map((update) => ({
      title: update.title,
      summary: update.summary,
      source_domain: update.source_domain,
      source_url: update.source_url,
      source_label: update.source_label,
      evidence_tension: update.evidence_tension,
    }));
  const missingByKey = new Map<string, { key: string; label: string; status: string; researchPrompt?: string }>();
  (evidence?.missing_fields || []).forEach((row) => {
    if (!row?.key) return;
    missingByKey.set(row.key, {
      key: row.key,
      label: row.label || row.key,
      status: row.status || "empty",
      researchPrompt: row.research_prompt,
    });
  });

  return {
    frictionPoint:
      evidence?.friction_point
      || deal.leadHighlights?.specific_problem
      || deal.shareSummary
      || deal.signal,
    workflowLabel: evidence?.workflow_scope?.label || (workflowItems.length > 1 ? "Multiple workflows" : "One workflow"),
    workflowItems,
    timingLabel: evidence?.timing?.label || deal.projectTiming?.display_phrase || deal.projectTiming?.label,
    robotLabel: evidence?.robot_type?.label || robotItems[0] || (robotTypesForDeal(deal)[0] ?? null),
    robotItems: robotItems.length ? robotItems : robotTypesForDeal(deal),
    budgetTopAmount: evidence?.budget?.top_amount || null,
    budgetSignals,
    decisionMakers,
    deploymentExamples: deploymentExamples.length > 0 ? deploymentExamples : fallbackDeploymentExamples,
    missingByKey,
    researchState: evidence?.research_status?.state || null,
  };
}

function missingEvidenceCountForDeal(deal: Deal): number {
  const rows = deal.crmEvidence?.missing_fields || [];
  if (!Array.isArray(rows)) return 0;
  return rows.filter((row) => {
    const status = String(row?.status || "").toLowerCase();
    return ["empty", "researching", "monitoring"].includes(status);
  }).length;
}

function gapChipStyle(count: number): { color: string; background: string; border: string; label: string } {
  if (count >= 5) {
    return {
      color: "#b91c1c",
      background: "rgba(239,68,68,0.14)",
      border: "1px solid rgba(239,68,68,0.30)",
      label: "urgent",
    };
  }
  if (count >= 3) {
    return {
      color: "#c2410c",
      background: "rgba(249,115,22,0.14)",
      border: "1px solid rgba(249,115,22,0.30)",
      label: "watch",
    };
  }
  return {
    color: "#b45309",
    background: "rgba(245,158,11,0.14)",
    border: "1px solid rgba(245,158,11,0.28)",
    label: "light",
  };
}

function robotPriorityForDeal(deal: Deal): string | null {
  const action = cleanAndClampText(deal.pipelineAction, 480);
  if (action) return action;
  const humanoid = deal.humanoidPilotAction || deal.humanoidPilotLabel;
  if (humanoid) return cleanAndClampText(String(humanoid), 480);
  return null;
}

function PipelineRobotPriorityPanel({ deal }: { deal: Deal }) {
  const priorityLine = robotPriorityForDeal(deal);
  const robotTypes = robotTypesForDeal(deal);
  const hasHumanoid =
    deal.humanoidPilotTier &&
    ["ACTIVE_PILOT", "PILOT_INTENT"].includes(String(deal.humanoidPilotTier));
  const nonUsCount = Number(deal.humanoidNonUsVendorCount || 0);
  const nonUsModels = (deal.humanoidNonUsVendorModels || []).filter(Boolean);

  if (!priorityLine && robotTypes.length === 0 && !hasHumanoid && !deal.humanoidNonUsVendorFlag) return null;

  const priorityPrefix = priorityLine?.split(":")[0]?.trim();
  const priorityBody =
    priorityLine && priorityLine.includes(":")
      ? priorityLine.slice(priorityLine.indexOf(":") + 1).trim()
      : priorityLine;

  return (
    <div className="pipeline-detail-section">
      <p className={`${panelSectionLabel} mb-1.5`}>Robot priority</p>
      {priorityLine && (
        <p className="text-[12px] leading-relaxed text-gray-800">
          {priorityPrefix && priorityBody ? (
            <>
              <span className="font-bold text-emerald-800">{priorityPrefix}:</span> {priorityBody}
            </>
          ) : (
            priorityLine
          )}
        </p>
      )}
      {robotTypes.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {robotTypes.map((type) => (
            <span
              key={type}
              className="pipeline-robot-type-chip"
            >
              {type}
            </span>
          ))}
        </div>
      )}
      {hasHumanoid && (
        <p className="mt-2 text-[11px] text-emerald-800">
          <span className="font-semibold">Humanoid signal:</span>{" "}
          {cleanAndClampText(deal.humanoidPilotLabel || "Active pilot intent", 120)}
        </p>
      )}
      {deal.humanoidNonUsVendorFlag && (
        <p className="mt-2 text-[11px] text-amber-800">
          <span className="font-semibold">Origin risk:</span>{" "}
          {nonUsCount > 0 ? `${nonUsCount} non-US humanoid vendor model${nonUsCount === 1 ? "" : "s"} detected` : "Non-US humanoid vendor detected"}
          {nonUsModels.length > 0 ? ` (${cleanAndClampText(nonUsModels.slice(0, 3).join(", "), 140)})` : ""}
        </p>
      )}
    </div>
  );
}

function PipelineLeadQualityPanel({ deal }: { deal: Deal }) {
  const quality = deal.leadQuality;
  const traces = deal.evidenceTrace || quality?.evidence_traces || [];
  if (!quality && traces.length === 0) return null;

  const dimensionScores = quality?.dimension_scores || {};
  const weights = quality?.weights || {};
  const orderedDimensions = [
    "buyer_authenticity",
    "urgency_window",
    "robot_fit_confidence",
    "decision_maker_confidence",
    "contactability_confidence",
  ].filter((key) => typeof dimensionScores[key] === "number");
  const confidenceBand = (deal.confidenceBand || quality?.confidence_band || "band unknown").toLowerCase();
  const gatePassed = quality?.quality_gate?.passed !== false;
  const gateReason = cleanAndClampText(quality?.quality_gate?.reason || "evidence sufficient", 80);

  const bandTone =
    confidenceBand === "high"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : confidenceBand === "medium"
        ? "border-amber-200 bg-amber-50 text-amber-800"
        : "border-rose-200 bg-rose-50 text-rose-800";

  const dimensionLabel = (key: string) => {
    if (key === "buyer_authenticity") return "Buyer authenticity";
    if (key === "urgency_window") return "Urgency window";
    if (key === "robot_fit_confidence") return "Robot fit";
    if (key === "decision_maker_confidence") return "Decision-maker confidence";
    if (key === "contactability_confidence") return "Contactability";
    return key.replace(/_/g, " ");
  };

  return (
    <div className="pipeline-detail-section-muted mt-2">
      <p className={panelSectionLabel}>Quality signal</p>
      <div className="mt-2 rounded-xl border border-slate-200 bg-white/85 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Lead quality score</p>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${bandTone}`}>
            {cleanAndClampText(confidenceBand, 24)}
          </span>
        </div>
        <div className="mt-2 flex items-end justify-between gap-3">
          <p className="text-[24px] font-semibold leading-none text-slate-900">
            {typeof quality?.overall_score === "number" ? quality.overall_score.toFixed(1) : "—"}
          </p>
          <div className="text-right">
            <p className={`text-[10px] font-semibold uppercase tracking-wide ${gatePassed ? "text-emerald-700" : "text-rose-700"}`}>
              {gatePassed ? "quality gate passed" : "quality gate blocked"}
            </p>
            <p className="mt-0.5 text-[10px] text-slate-500">{gateReason}</p>
          </div>
        </div>
        {orderedDimensions.length > 0 && (
          <div className="mt-3 space-y-2">
            {orderedDimensions.map((dimension) => {
              const score = Number(dimensionScores[dimension] ?? 0);
              const weight = Number(weights[dimension] ?? 0) * 100;
              return (
                <div key={dimension}>
                  <div className="mb-1 flex items-center justify-between gap-2 text-[10px]">
                    <span className="font-semibold uppercase tracking-wide text-slate-600">{dimensionLabel(dimension)}</span>
                    <span className="font-mono text-slate-500">{score.toFixed(0)} · {weight.toFixed(0)}% wt</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500"
                      style={{ width: `${Math.max(6, Math.min(100, score))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-700">
            {quality?.weight_source || "baseline_v1"}
          </span>
          {(quality?.missing_fields_count || 0) > 0 && (
            <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-800">
              {quality?.missing_fields_count} evidence gap{quality?.missing_fields_count === 1 ? "" : "s"}
            </span>
          )}
        </div>
        {traces.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Evidence traces</p>
            {traces.slice(0, 5).map((trace, index) => (
              <div key={`${trace.dimension || index}`} className="rounded-lg border border-slate-200 bg-slate-50/70 px-2.5 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-700">
                    {dimensionLabel(trace.dimension || "signal")}
                  </span>
                  {typeof trace.score === "number" ? (
                    <span className="font-mono text-[10px] text-slate-500">{trace.score.toFixed(0)}</span>
                  ) : null}
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-slate-700">
                  {cleanAndClampText(trace.evidence || "No trace available.", 220)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PipelineContactIntelligencePanel({ deal }: { deal: Deal }) {
  const intel = deal.contactIntelligence;
  const phoneBest = intel?.phone?.best;
  const linkedinBest = intel?.linkedin?.best_profile || deal.linkedInProfile;
  const disambiguation = intel?.linkedin?.disambiguation;
  const whyLead = intel?.sales_intuition?.why_sales_lead;
  const opportunityPoints = (intel?.sales_intuition?.larger_opportunity?.points || []).filter(Boolean);
  const competitorClues = (intel?.sales_intuition?.competitor_robot_usage || []).filter(Boolean);
  const robotHistory = (intel?.sales_intuition?.robot_history || []).filter(Boolean);

  if (!intel && !deal.contactPhone && !deal.linkedInProfile) return null;

  return (
    <div className="pipeline-detail-section-muted mt-2">
      <p className={panelSectionLabel}>Contact intelligence</p>
      <div className="mt-2 space-y-2 rounded-xl border border-slate-200 bg-white/85 p-3">
        <div className="grid gap-2 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Phone</p>
            <p className="mt-1 text-[12px] font-semibold text-slate-900">
              {cleanAndClampText(phoneBest?.phone || deal.contactPhone || "not found", 40)}
            </p>
            {phoneBest?.evidence && (
              <p className="mt-1 text-[10px] leading-relaxed text-slate-600">
                {cleanAndClampText(phoneBest.evidence, 140)}
              </p>
            )}
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">LinkedIn profile</p>
            {linkedinBest?.url ? (
              <>
                <a
                  href={linkedinBest.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex text-[12px] font-semibold text-emerald-800 underline"
                >
                  Open profile
                </a>
                <p className="mt-1 text-[10px] text-slate-600">
                  {cleanAndClampText(linkedinBest.person || linkedinBest.person_title || "Best match", 80)}
                </p>
              </>
            ) : (
              <p className="mt-1 text-[12px] text-slate-700">No confirmed profile yet</p>
            )}
          </div>
        </div>

        {disambiguation?.status === "required" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50/80 p-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-800">LinkedIn disambiguation required</p>
            <p className="mt-1 text-[11px] leading-relaxed text-amber-900">
              {cleanAndClampText(disambiguation.reason || "Multiple plausible profiles found", 180)}
            </p>
            {(disambiguation.script || []).slice(0, 3).map((step, i) => (
              <p key={`${step}-${i}`} className="mt-1 text-[10px] leading-relaxed text-amber-800">
                {i + 1}. {cleanAndClampText(step, 180)}
              </p>
            ))}
          </div>
        )}

        {(whyLead?.specific_problem || (whyLead?.reasons || []).length > 0) && (
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Why this is a sales lead</p>
            {whyLead?.specific_problem && (
              <p className="mt-1 text-[12px] leading-relaxed text-slate-800">
                {cleanAndClampText(whyLead.specific_problem, 180)}
              </p>
            )}
            {(whyLead?.reasons || []).slice(0, 2).map((reason, idx) => (
              <p key={`${reason}-${idx}`} className="mt-1 text-[11px] leading-relaxed text-slate-700">
                • {cleanAndClampText(reason, 150)}
              </p>
            ))}
          </div>
        )}

        {(opportunityPoints.length > 0 || robotHistory.length > 0 || competitorClues.length > 0) && (
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Opportunity and competitive context</p>
            {opportunityPoints.slice(0, 2).map((point, idx) => (
              <p key={`${point}-${idx}`} className="mt-1 text-[11px] leading-relaxed text-slate-700">
                • {cleanAndClampText(point, 170)}
              </p>
            ))}
            {robotHistory[0]?.summary && (
              <p className="mt-1 text-[11px] leading-relaxed text-slate-700">
                <span className="font-semibold text-slate-900">Robot history:</span> {cleanAndClampText(robotHistory[0].summary, 170)}
              </p>
            )}
            {competitorClues[0]?.summary && (
              <p className="mt-1 text-[11px] leading-relaxed text-slate-700">
                <span className="font-semibold text-slate-900">Competitor clue:</span> {cleanAndClampText(competitorClues[0].summary, 170)}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Pipeline() {
  const { session } = useAuth();
  const [, setLocation] = useLocation();
  const search = useSearch();
  const [storageSubmittedUrl, setStorageSubmittedUrl] = useState("");
  const submittedUrlFromQuery = useMemo(() => {
    const params = new URLSearchParams(search);
    return (params.get("url") || "").trim();
  }, [search]);
  const submittedSrcFromQuery = useMemo(() => {
    const params = new URLSearchParams(search);
    return (params.get("src") || "").trim();
  }, [search]);
  const viewFromQuery = useMemo(() => {
    const params = new URLSearchParams(search);
    return (params.get("view") || "").trim().toLowerCase();
  }, [search]);
  const activationIdFromQuery = useMemo(() => {
    const value = Number(new URLSearchParams(search).get("activation"));
    return Number.isFinite(value) && value > 0 ? value : null;
  }, [search]);
  const arrivedFromSignalActivation = submittedSrcFromQuery === "signal_activation";
  const arrivedFromResultsScan =
    submittedSrcFromQuery === "results_scan" || submittedSrcFromQuery === "results_next_step";
  /** URL submit searches stay on matched prospects — never default to the global market queue. */
  const preferUrlMatchedPipeline = Boolean(submittedUrlFromQuery || arrivedFromResultsScan);

  useEffect(() => {
    if (submittedUrlFromQuery) {
      setStorageSubmittedUrl("");
      return;
    }
    setStorageSubmittedUrl(getSubmittedUrlFromStorage());
  }, [submittedUrlFromQuery]);

  const deepLinkLeadId = useMemo(() => resolvePipelineLeadId(search), [search]);
  const submittedUrl = submittedUrlFromQuery || storageSubmittedUrl;

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (submittedUrlFromQuery || !storageSubmittedUrl) return;
    const params = new URLSearchParams(search);
    params.set("url", storageSubmittedUrl);
    if (!submittedSrcFromQuery) params.set("src", "home_url_submit_recovered");
    const next = `/pipeline?${params.toString()}`;
    window.history.replaceState({}, "", next);
    setLocation(next);
  }, [search, setLocation, storageSubmittedUrl, submittedSrcFromQuery, submittedUrlFromQuery]);
  const submittedHostname = useMemo(() => {
    if (!submittedUrl) return "";
    try {
      const normalized = submittedUrl.includes("://") ? submittedUrl : `https://${submittedUrl}`;
      return new URL(normalized).hostname.toLowerCase().replace(/^www\./, "");
    } catch {
      return submittedUrl.toLowerCase().replace(/^www\./, "").split("/")[0].split("?")[0].trim();
    }
  }, [submittedUrl]);
  const [scopeToSubmittedUrl, setScopeToSubmittedUrl] = useState(false);
  const [submittedUrlMatches, setSubmittedUrlMatches] = useState<ApiLead[]>([]);
  const [submittedUrlMatchLoading, setSubmittedUrlMatchLoading] = useState(false);
  const [submittedUrlMatchError, setSubmittedUrlMatchError] = useState(false);
  const [submittedUrlWeakProfile, setSubmittedUrlWeakProfile] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [rotationPool, setRotationPool] = useState<Deal[]>([]);
  const [rotateOffset, setRotateOffset] = useState(0);
  // Once an anonymous visitor clicks a lead to read its outreach draft, freeze the
  // 7s auto-rotation so we never yank the value-proof view out from under them
  // mid-read (value_first_principle: read the full draft before signup).
  const [rotationPaused, setRotationPaused] = useState(false);
  const [summary, setSummary] = useState<LeadSummary | null>(null);
  const [marketSnippet, setMarketSnippet] = useState<MarketSnippet>(DEFAULT_MARKET_SNIPPET);
  const [activations, setActivations] = useState<ScoutActivation[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [industryQuery, setIndustryQuery] = useState("");
  const [qualityBandFilter, setQualityBandFilter] = useState<QualityBandFilter>("all");
  const [qualitySort, setQualitySort] = useState<QualitySort>("default");
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
  const [capturedContactEmail, setCapturedContactEmail] = useState("");
  const [developingLeadId, setDevelopingLeadId] = useState<number | null>(null);
  // Draft preview email modal
  const [previewOpen, setPreviewOpen] = useState(false);
  const [proposalOpen, setProposalOpen] = useState(false);
  const [proposalData, setProposalData] = useState<ProposalData | null>(null);
  const [proposalBusy, setProposalBusy] = useState(false);
  const [saveLimitOpen, setSaveLimitOpen] = useState(false);
  const [saveLimitMessage, setSaveLimitMessage] = useState("");
  const [crmStageByCompanyId, setCrmStageByCompanyId] = useState<Record<number, string>>({});
  const [crmAccountIdByCompanyId, setCrmAccountIdByCompanyId] = useState<Record<number, string>>({});
  const [savedLeadCount, setSavedLeadCount] = useState(0);
  /** After Results: show instructions first; CTA unlocks the 15-lead URL-matched pipeline. */
  const [build25Started, setBuild25Started] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return sessionStorage.getItem("rfr_build15_started") === "1" || sessionStorage.getItem("rfr_build25_started") === "1";
    } catch {
      return false;
    }
  });
  const step3Intro = arrivedFromResultsScan && !build25Started;

  // Land on instructions — never restore scroll to the lead list (browse-and-leave trap).
  useEffect(() => {
    if (!step3Intro || typeof window === "undefined") return;
    try {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual";
      }
    } catch {
      /* ignore */
    }
    const jump = () => {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      document.getElementById("pipeline-step3-guide")?.scrollIntoView({ block: "start", behavior: "auto" });
    };
    jump();
    const t0 = window.setTimeout(jump, 50);
    const t1 = window.setTimeout(jump, 250);
    const t2 = window.setTimeout(jump, 800);
    return () => {
      window.clearTimeout(t0);
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [step3Intro, loadingLeads]);

  const [firstSaveGuideOpen, setFirstSaveGuideOpen] = useState(false);
  const [showActivationChecklist, setShowActivationChecklist] = useState(false);
  const [draftCopiedForActivation, setDraftCopiedForActivation] = useState(false);
  const [firstThreeActions, setFirstThreeActions] = useState<FirstThreeActionsState>(() => readFirstThreeActions());
  const [outreachDraftSpotlight, setOutreachDraftSpotlight] = useState(false);
  const [checklistVariantOverride, setChecklistVariantOverride] = useState<"a" | "b" | null>(null);
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
  const byIdInFlightRef = useRef<Map<number, Promise<Deal | null>>>(new Map());
  const byIdFailureCooldownUntilRef = useRef<Map<number, number>>(new Map());
  const byIdFailureStreakRef = useRef(0);
  const byIdBreakerOpenUntilRef = useRef(0);
  const outreachDraftRef = useRef<HTMLDivElement | null>(null);
  const firstThreePrevRef = useRef<FirstThreeActionsState>(firstThreeActions);

  useEffect(() => {
    if (!arrivedFromSignalActivation) return;
    setFirstThreeActions((prev) => ({
      ...prev,
      started: true,
      saved: true,
      dismissed: false,
    }));
  }, [arrivedFromSignalActivation]);

  useEffect(() => {
    if (!activationIdFromQuery || !activations.some((activation) => activation.id === activationIdFromQuery)) return;
    setSelectedActivationId(activationIdFromQuery);
  }, [activationIdFromQuery, activations]);

  useEffect(() => {
    // URL submit → matched prospects only (not the global market queue).
    if (submittedHostname || preferUrlMatchedPipeline) {
      setScopeToSubmittedUrl(true);
    }
  }, [preferUrlMatchedPipeline, submittedHostname]);
  useEffect(() => {
    if (!submittedUrl) {
      setSubmittedUrlMatches([]);
      setSubmittedUrlMatchLoading(false);
      setSubmittedUrlMatchError(false);
      setSubmittedUrlWeakProfile(false);
      return;
    }
    let cancelled = false;
    const base = getPublicReadApiBase();
    setSubmittedUrlMatchError(false);
    setSubmittedUrlMatchLoading(true);
    void fetchWithTimeoutRetry(
      `${base}/api/leads/match-url?url=${encodeURIComponent(submittedUrl)}&limit=${BUILD_PIPELINE_TARGET}`,
      publicFetchInit(),
      PIPELINE_TIMEOUT,
      { retries: 1, retryDelayMs: 800 },
    )
      .then(async (res) => {
        if (cancelled) return;
        if (!res.ok) {
          setSubmittedUrlMatchError(true);
          return;
        }
        const payload = (await res.json()) as SubmittedUrlMatchPayload;
        if (cancelled) return;
        const capabilityType = String(payload.robot_capabilities?.type || "").toLowerCase();
        const capabilityCount = Array.isArray(payload.robot_capabilities?.capabilities)
          ? payload.robot_capabilities!.capabilities!.length
          : 0;
        const profileScore = Number(payload.robot_capabilities?.profile_score ?? 0);
        const weakProfile =
          payload.matching_mode === "no_profile" ||
          ((capabilityType === "" || capabilityType === "unknown") && capabilityCount === 0 && profileScore < 50);

        setSubmittedUrlMatchError(false);
        setSubmittedUrlWeakProfile(weakProfile);
        setSubmittedUrlMatches(weakProfile ? [] : Array.isArray(payload.leads) ? payload.leads : []);
      })
      .catch(() => {
        if (!cancelled) {
          // Keep last successful scoped result set if present; transient network aborts
          // during dev-server reload should not be shown as "no match".
          setSubmittedUrlMatchError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setSubmittedUrlMatchLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [submittedUrl]);
  const firstThreeEnteredRef = useRef<FirstThreeStep | null>(null);
  const firstThreeAbandonTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const firstThreeAbandonSignaturesRef = useRef<Set<string>>(new Set());
  const contactAssistSeenLeadIdsRef = useRef<Set<number>>(new Set());
  const sendChecklistSeenLeadIdsRef = useRef<Set<number>>(new Set());
  const sendChecklistReadyLeadIdsRef = useRef<Set<number>>(new Set());
  const byIdTelemetryRef = useRef({
    attempts: 0,
    successes: 0,
    failures: 0,
    cooldownSkips: 0,
    breakerSkips: 0,
    inflightDedupes: 0,
    breakerOpenCount: 0,
    lastError: "",
  });

  const pruneByIdCooldowns = () => {
    const now = Date.now();
    for (const [id, until] of byIdFailureCooldownUntilRef.current.entries()) {
      if (until <= now) byIdFailureCooldownUntilRef.current.delete(id);
    }
    // Keep map bounded in case of prolonged browsing through many unique ids.
    if (byIdFailureCooldownUntilRef.current.size > BY_ID_COOLDOWN_TRACK_MAX) {
      const sorted = Array.from(byIdFailureCooldownUntilRef.current.entries())
        .sort((a, b) => a[1] - b[1]);
      const keep = sorted.slice(-BY_ID_COOLDOWN_TRACK_MAX);
      byIdFailureCooldownUntilRef.current = new Map(keep);
    }
  };

  const publishByIdTelemetry = () => {
    if (typeof window === "undefined") return;
    pruneByIdCooldowns();
    const attempts = byIdTelemetryRef.current.attempts;
    const failures = byIdTelemetryRef.current.failures;
    const failRate = attempts > 0 ? Number((failures / attempts).toFixed(3)) : 0;
    (window as Window & { __rfrPipelineByIdTelemetry?: Record<string, unknown> }).__rfrPipelineByIdTelemetry = {
      ...byIdTelemetryRef.current,
      failRate,
      breakerThreshold: BY_ID_BREAKER_FAIL_STREAK,
      breakerWindowMs: BY_ID_BREAKER_OPEN_MS,
      idCooldownMs: BY_ID_FAIL_COOLDOWN_MS,
      breakerOpen: Date.now() < byIdBreakerOpenUntilRef.current,
      breakerOpenForMs: Math.max(0, byIdBreakerOpenUntilRef.current - Date.now()),
      cooldownIds: byIdFailureCooldownUntilRef.current.size,
      inFlight: byIdInFlightRef.current.size,
    };
  };

  const getPipelineFallbackDealById = (leadId: number): Deal | null => {
    const fromCurrent = dealsRef.current.find((d) => d.id === leadId);
    if (fromCurrent) return fromCurrent;
    const cached =
      readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_SESSION_TTL_MS)
      ?? readSurfaceCache<PipelineFeedPayload>(PIPELINE_SESSION_KEY, PIPELINE_STALE_PAINT_MS);
    const rows = Array.isArray(cached?.data?.leads) ? cached?.data?.leads : [];
    if (!rows.length) return null;
    const raw = rows.find((r) => r.id === leadId);
    if (!raw) return null;
    try {
      return mapApiLeadToDeal(raw, crmStageByCompanyId[leadId]) as Deal;
    } catch {
      return null;
    }
  };

  const fetchByIdWithGuards = async (
    leadId: number,
    opts: { timeoutMs: number; retries?: number; retryDelayMs?: number },
  ): Promise<Deal | null> => {
    pruneByIdCooldowns();
    const inFlight = byIdInFlightRef.current.get(leadId);
    if (inFlight) {
      byIdTelemetryRef.current.inflightDedupes += 1;
      publishByIdTelemetry();
      return inFlight;
    }

    const now = Date.now();
    if (now < byIdBreakerOpenUntilRef.current) {
      byIdTelemetryRef.current.cooldownSkips += 1;
      byIdTelemetryRef.current.breakerSkips += 1;
      publishByIdTelemetry();
      return getPipelineFallbackDealById(leadId);
    }

    const cooldownUntil = byIdFailureCooldownUntilRef.current.get(leadId) ?? 0;
    if (now < cooldownUntil) {
      byIdTelemetryRef.current.cooldownSkips += 1;
      publishByIdTelemetry();
      return getPipelineFallbackDealById(leadId);
    }

    byIdTelemetryRef.current.attempts += 1;
    publishByIdTelemetry();

    const request = (async () => {
      const base = getApiBase();
      try {
        const response = await fetchWithTimeoutRetry(
          `${base}/api/leads/by-id/${leadId}`,
          liveFetchInit(),
          opts.timeoutMs,
          {
            retries: opts.retries ?? 0,
            retryDelayMs: opts.retryDelayMs ?? 800,
          },
        );
        if (!response.ok) throw new Error(`by-id ${response.status}`);
        const lead = (await response.json()) as ApiLead;
        const mapped = mapApiLeadToDeal(lead, crmStageByCompanyId[lead.id]) as Deal;
        byIdFailureStreakRef.current = 0;
        byIdFailureCooldownUntilRef.current.delete(leadId);
        byIdTelemetryRef.current.successes += 1;
        byIdTelemetryRef.current.lastError = "";
        publishByIdTelemetry();
        return mapped;
      } catch (e) {
        const message = e instanceof Error ? e.message : "by-id request failed";
        byIdTelemetryRef.current.failures += 1;
        byIdTelemetryRef.current.lastError = message;
        byIdFailureStreakRef.current += 1;
        byIdFailureCooldownUntilRef.current.set(leadId, Date.now() + BY_ID_FAIL_COOLDOWN_MS);
        if (byIdFailureStreakRef.current >= BY_ID_BREAKER_FAIL_STREAK) {
          byIdBreakerOpenUntilRef.current = Date.now() + BY_ID_BREAKER_OPEN_MS;
          byIdTelemetryRef.current.breakerOpenCount += 1;
          byIdFailureStreakRef.current = 0;
        }
        publishByIdTelemetry();
        return getPipelineFallbackDealById(leadId);
      } finally {
        byIdInFlightRef.current.delete(leadId);
      }
    })();

    byIdInFlightRef.current.set(leadId, request);
    return request;
  };

  const retryDeepLink = () => {
    deepLinkInflightRef.current = null;
    byIdFailureCooldownUntilRef.current.delete(deepLinkLeadId ?? -1);
    byIdBreakerOpenUntilRef.current = 0;
    publishByIdTelemetry();
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
      setSavedLeadCount(0);
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
          id?: string;
          company_id?: number | null;
          outreach_stage?: string | null;
        }>;
        if (cancelled) return;
        const next: Record<number, string> = {};
        const accountIds: Record<number, string> = {};
        for (const acct of accounts) {
          if (acct.company_id && acct.outreach_stage) next[acct.company_id] = acct.outreach_stage;
          if (acct.company_id && acct.id) accountIds[acct.company_id] = acct.id;
        }
        setCrmStageByCompanyId(next);
        setCrmAccountIdByCompanyId(accountIds);
        setSavedLeadCount(accounts.filter((acct) => acct.company_id).length);
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
    const base = getPublicReadApiBase();
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
        publicFetchInit({ headers }),
        PIPELINE_TIMEOUT,
        { retries: 1, retryDelayMs: 800 },
      );
      if (!res.ok) throw new Error("Could not load pipeline");
      const payload = (await res.json()) as PipelineFeedPayload;
      if (cancelled) return;

      if (payload.entitlements) setEntitlements(payload.entitlements);
      if (
        payload.summary
        && ((payload.summary.total ?? 0) > 0 || (payload.summary.hot ?? 0) > 0)
      ) {
        setSummary(payload.summary);
      }

      const leadRows = Array.isArray(payload.leads) ? payload.leads : [];
      if (leadRows.length > 0) {
        writeSurfaceCache(PIPELINE_SESSION_KEY, payload);
        applyPipelineFeed(payload, feedSetters);
        return;
      }

      // Primary feed empty (cache rebuild) — stop blocking the UI; hydrate in background.
      if (payload.cache_pending) {
        void hydratePipelineFallback(
          base,
          headers,
          feedSetters,
          crmStageByCompanyId,
          () => cancelled,
        ).catch(() => undefined);
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

  // Extended lead pool for tier-slot rotation (anonymous bucket view).
  useEffect(() => {
    if (deals.length >= (entitlements?.pipeline_limit ?? 12)) return;
    let cancelled = false;
    const base = getPublicReadApiBase();
    const headers = session?.access_token ? authHeader(session.access_token) : undefined;
    void fetchPipelineLeadsFallback(base, headers).then((rows) => {
      if (cancelled || rows.length === 0) return;
      setRotationPool(mapPipelineRows(rows, crmStageByCompanyId));
    });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token, crmStageByCompanyId, deals.length, entitlements?.pipeline_limit]);

  // Keep pipeline feed fresh — server rotation slot advances on the cache clock.
  useEffect(() => {
    const base = getPublicReadApiBase();
    let cancelled = false;
    const refresh = () => {
      const token = session?.access_token;
      const headers = token ? authHeader(token) : undefined;
      void fetchWithTimeoutRetry(
        `${base}/api/leads/pipeline`,
        publicFetchInit({ headers }),
        PIPELINE_TIMEOUT,
        { retries: 1, retryDelayMs: 800 },
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
          }, crmStageByCompanyId);
        })
        .catch(() => undefined);
    };
    const timer = window.setInterval(refresh, 2 * 60 * 1000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [session?.access_token, crmStageByCompanyId]);

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
      try {
        const mapped = await fetchByIdWithGuards(deepLinkLeadId, {
          timeoutMs: BY_ID_DEEPLINK_TIMEOUT_MS,
          retries: 2,
          retryDelayMs: 1200,
        });
        if (cancelled) return;
        if (!mapped) {
          deepLinkInflightRef.current = null;
          setDeepLinkLoadFailed(true);
          return;
        }
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
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void (async () => {
        const now = Date.now();
        const breakerOpen = now < byIdBreakerOpenUntilRef.current;
        const cooldownOpen = now < (byIdFailureCooldownUntilRef.current.get(selectedId) ?? 0);
        if (!breakerOpen && !cooldownOpen) {
          setLoadingResearch(true);
        }
        try {
          const mapped = await fetchByIdWithGuards(selectedId, {
            timeoutMs: BY_ID_TIMEOUT_MS,
            retries: 0,
          });
          if (!mapped) return;
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
  }, [selectedId, deepLinkRetryNonce]);

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
  const qualityControlsActive = qualityBandFilter !== "all" || qualitySort !== "default";
  const activeSearchQuery = industryQuery.trim() || (filter !== "All" ? filter : "");
  const hasActiveSearch = Boolean(activeSearchQuery);
  const pipelineSource = rotationPool.length > deals.length ? rotationPool : deals;
  const previewLimit = entitlements?.pipeline_limit ?? PIPELINE_LIMIT_FREE;
  const freeLeadCap = Math.min(entitlements?.pipeline_limit ?? PIPELINE_LIMIT_FREE, PIPELINE_LIMIT_FREE);
  const freeVisibleLeads = Math.min(entitlements?.visible_count ?? deals.length, freeLeadCap);
  const freeLeadsRemaining = Math.max(0, freeLeadCap - freeVisibleLeads);
  const freeUpgradeMessage =
    freeLeadsRemaining <= 2
      ? `You have viewed ${freeVisibleLeads}/${freeLeadCap} leads. Upgrade to Pro to unlock more buyers and automate your sales pipeline.`
      : `Ready to scale beyond ${freeLeadCap} leads? Upgrade to Pro to unlock more buyers and automate your sales pipeline.`;
  const sessionDisplayName =
    session?.user?.user_metadata?.full_name
    || session?.user?.user_metadata?.name
    || session?.user?.email?.split("@")[0]
    || "there";
  const rotationSource = useMemo(() => {
    if (hasActiveSearch || qualityControlsActive || showKanban) return pipelineSource;
    if (panelPlan === "anonymous" && pipelineSource.length > previewLimit) {
      return pickRotatingWindow(pipelineSource, previewLimit, rotateOffset);
    }
    return pipelineSource;
  }, [hasActiveSearch, qualityControlsActive, showKanban, panelPlan, pipelineSource, previewLimit, rotateOffset]);
  const rotatedDeals = useMemo(() => {
    if (hasActiveSearch || qualityControlsActive || showKanban || panelPlan !== "anonymous") return null;
    return buildRotatedPipelineDeals(rotationSource, rotateOffset);
  }, [hasActiveSearch, qualityControlsActive, showKanban, panelPlan, rotationSource, rotateOffset]);
  const listDeals = rotatedDeals ?? deals;
  const dealQualityScore = (deal: Deal) => Number(deal.leadQuality?.overall_score ?? 0);
  const dealBand = (deal: Deal) => String(deal.confidenceBand || deal.leadQuality?.confidence_band || "").toLowerCase();
  const dealDimensionScore = (deal: Deal, dimension: Exclude<QualitySort, "default" | "quality_desc" | "quality_asc">) =>
    Number(deal.leadQuality?.dimension_scores?.[dimension] ?? 0);
  const clientSearchMatches = useMemo(
    () => (hasActiveSearch ? listDeals.filter((d) => dealMatchesSearchQuery(d, activeSearchQuery)) : listDeals),
    [listDeals, hasActiveSearch, activeSearchQuery],
  );
  const filtered = useMemo(() => {
    const base = !hasActiveSearch
      ? listDeals
      : serverSearchDeals.length > 0
        ? serverSearchDeals
        : clientSearchMatches;

    let next = qualityBandFilter === "all"
      ? base
      : base.filter((deal) => dealBand(deal) === qualityBandFilter);

    if (qualitySort !== "default") {
      next = [...next].sort((a, b) => {
        if (qualitySort === "quality_desc") return dealQualityScore(b) - dealQualityScore(a);
        if (qualitySort === "quality_asc") return dealQualityScore(a) - dealQualityScore(b);
        return dealDimensionScore(b, qualitySort) - dealDimensionScore(a, qualitySort);
      });
    }

    if (panelPlan === "free" && next.length > PIPELINE_LIMIT_FREE) {
      return next.slice(0, PIPELINE_LIMIT_FREE);
    }
    return next;
  }, [
    listDeals,
    hasActiveSearch,
    serverSearchDeals,
    clientSearchMatches,
    qualityBandFilter,
    qualitySort,
    panelPlan,
  ]);

  const matchedScopedDeals = useMemo(
    () => mapPipelineRows(submittedUrlMatches, crmStageByCompanyId).slice(0, BUILD_PIPELINE_TARGET),
    [submittedUrlMatches, crmStageByCompanyId],
  );
  const scopeMatchesCount = matchedScopedDeals.length;
  const scopedNoMatches = scopeToSubmittedUrl && !submittedUrlMatchLoading && !submittedUrlMatchError && scopeMatchesCount === 0;
  const displayedDeals = useMemo(
    () => (scopeToSubmittedUrl ? matchedScopedDeals : filtered),
    [filtered, matchedScopedDeals, scopeToSubmittedUrl],
  );

  useEffect(() => {
    if (hasActiveSearch || qualityControlsActive || showKanban || rotationPaused || step3Intro) return;
    const canRotate =
      bucketPoolCanRotate(rotationSource) ||
      (panelPlan === "anonymous" && pipelineSource.length > previewLimit);
    if (!canRotate) return;
    const timer = window.setInterval(
      () => setRotateOffset((offset) => offset + 1),
      PIPELINE_LEAD_READ_MS,
    );
    return () => window.clearInterval(timer);
  }, [hasActiveSearch, qualityControlsActive, showKanban, rotationPaused, rotationSource, pipelineSource.length, panelPlan, previewLimit, step3Intro]);

  // Keep CRM detail panel in sync with the rotating spotlight lead.
  useEffect(() => {
    if (hasActiveSearch || qualityControlsActive || showKanban || rotationPaused || deepLinkLeadId != null || step3Intro) return;
    const canRotate =
      bucketPoolCanRotate(rotationSource) ||
      (panelPlan === "anonymous" && pipelineSource.length > previewLimit);
    if (!canRotate || displayedDeals.length === 0) return;
    setSelectedId(displayedDeals[0].id);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- advance panel only on rotation tick
  }, [rotateOffset, step3Intro]);

  useEffect(() => {
    if (!session?.access_token || savedLeadCount !== 0 || loadingLeads) return;
    if (!shouldShowFirstSaveGuide()) return;
    const leadId = selectedId ?? displayedDeals[0]?.id;
    if (leadId == null || !displayedDeals.some((d) => d.id === leadId)) return;
    const delay = isFreshSignup() ? 400 : 1200;
    const timer = window.setTimeout(() => setFirstSaveGuideOpen(true), delay);
    return () => window.clearTimeout(timer);
  }, [session?.access_token, savedLeadCount, loadingLeads, displayedDeals, selectedId]);

  const pendingDeepLink =
    selectedId != null &&
    deepLinkLeadId === selectedId &&
    !displayedDeals.some((d) => d.id === selectedId);
  const effectiveSelectedId =
    selectedId != null && (displayedDeals.some((d) => d.id === selectedId) || pendingDeepLink)
      ? selectedId
      : (displayedDeals[0]?.id ?? null);
  const selected =
    displayedDeals.find((d) => d.id === effectiveSelectedId)
    ?? (pendingDeepLink && effectiveSelectedId != null
      ? deals.find((d) => d.id === effectiveSelectedId) ?? null
      : null);
  const selectedActivation = activations.find((a) => a.id === selectedActivationId) ?? activations[0] ?? null;
  const isSignedIn = Boolean(session?.access_token);
  const isFirstWorkspaceRun = isSignedIn && savedLeadCount === 0;
  const hasSavedLead = savedLeadCount > 0;
  const build25Progress = Math.min(savedLeadCount, BUILD_PIPELINE_TARGET);
  const nextStepsTitle = arrivedFromResultsScan ? "Step 3 · URL-matched sales pipeline" : "Next step";
  const nextStepsHeadline = arrivedFromResultsScan
    ? !build25Started
      ? "Your free workspace unlocks 15 buyers matched to your robot URL"
      : `Building your matched pipeline · ${build25Progress}/${BUILD_PIPELINE_TARGET} saved`
    : "Pick a lead → save it → copy draft → send";
  const nextStepsItems = arrivedFromResultsScan
    ? !build25Started
      ? [
          "We looked up your URL, scored your robot company, and matched equally scored buyer opportunities.",
          `Free account unlocks your working list of ${BUILD_PIPELINE_TARGET} matched sales leads — not the global market queue.`,
          "Then curate the best companies and run outreach for each.",
        ]
      : [
          `Curate: Save strong fits until you reach ${BUILD_PIPELINE_TARGET} in your matched list (${build25Progress} saved).`,
          "Outreach: open a saved company, review why-now signals, copy the draft.",
          "Send, then keep shortlisting the next matched accounts.",
        ]
    : submittedHostname
    ? scopedNoMatches
      ? [
          `Widen the search: try the homepage URL for ${submittedHostname}.`,
          "Switch to full pipeline results and pick the strongest HOT lead.",
          isSignedIn
            ? "Save that lead, copy the outreach draft, and send."
            : "Start a free workspace, save that lead, then copy and send the draft.",
        ]
      : isFirstWorkspaceRun
        ? [
            `Pick the best buyer related to ${submittedHostname} from the list (left).`,
            "Click Save to put them in your working pipeline.",
            "Copy the outreach draft in the detail panel, then send.",
          ]
        : isSignedIn && hasSavedLead
          ? [
              `Keep the strongest ${submittedHostname} matches in scope.`,
              "Advance your saved lead or save one more high-fit account.",
              "Copy the draft from the detail panel and send your next touch.",
            ]
        : [
            `Review matches for ${submittedHostname} and pick one HOT lead.`,
            "Save it to your workspace (or start free to unlock save).",
            "Copy the outreach draft and keep moving in the panel on the right.",
          ]
    : isFirstWorkspaceRun
      ? [
          "Select the highest-fit HOT lead in the list.",
          "Save it — that opens your working pipeline.",
          "Copy the outreach draft and send your first message.",
        ]
      : isSignedIn && hasSavedLead
        ? [
            "Open your saved lead first, then add the next best account.",
            "Copy the outreach draft from the details panel.",
            "Send, then track replies in Inbox.",
          ]
      : [
          "Select the highest-fit HOT lead in the list.",
          "Save it (or start free workspace to unlock save + drafts).",
          "Copy the outreach draft and send from the detail panel.",
        ];
  const canSaveSelected = Boolean(selected) && (!isSignedIn || !crmAccountIdByCompanyId[selected!.id]);
  const canCopySelectedDraft = Boolean(selected?.outreachBody);
  const canOpenSelectedDraft = Boolean(selected?.outreachBody) && showKanban && Boolean(session?.access_token);
  const nextStepPrimaryLabel = arrivedFromResultsScan
    ? !build25Started
      ? isSignedIn
        ? `Open your ${BUILD_PIPELINE_TARGET} matched sales leads`
        : `Create free account · unlock ${BUILD_PIPELINE_TARGET} matched leads`
      : canSaveSelected
        ? `Save lead · ${build25Progress}/${BUILD_PIPELINE_TARGET}`
        : canCopySelectedDraft
          ? "Outreach: Copy draft"
          : selected
            ? "Outreach: Review this company"
            : "Pick a lead to curate"
    : !isSignedIn
    ? "Next step: Start free workspace"
    : canSaveSelected
      ? "Next step: Save selected lead"
      : canCopySelectedDraft
        ? "Next step: Copy outreach draft"
        : canOpenSelectedDraft
          ? "Next step: Open selected lead"
          : selected
            ? "Next step: Review selected lead"
            : "Next step: Pick a HOT lead";

  // Manual lead click = engagement. Pin the selection and stop auto-rotation so the
  // visitor can finish reading the outreach draft before we ask them to sign up.
  const selectLead = (id: number) => {
    setRotationPaused(true);
    setSelectedId(id);
  };

  const moveStage = (id: number, direction: 1 | -1) => {
    let nextStage: Stage | null = null;
    setDeals((prev) =>
      prev.map((d) => {
        if (d.id !== id) return d;
        const idx = STAGES.indexOf(d.stage);
        const next = STAGES[idx + direction];
        if (!next) return d;
        nextStage = next;
        toast.success(`Moved "${d.company}" to ${stageLabel(next)}`);
        return { ...d, stage: next, updatedAt: "just now" };
      }),
    );
    const accountId = crmAccountIdByCompanyId[id];
    const token = session?.access_token;
    if (!nextStage || !accountId || !token) return;
    const outreachStage = crmOutreachStageFromPipelineStage(nextStage);
    void fetch(
      `${getApiBase()}/api/crm/accounts/${accountId}`,
      liveFetchInit({
        method: "PATCH",
        headers: { ...authHeader(token), "Content-Type": "application/json" },
        body: JSON.stringify({ outreach_stage: outreachStage }),
      }),
    )
      .then((res) => {
        if (!res.ok) return;
        setCrmStageByCompanyId((prev) => ({ ...prev, [id]: outreachStage }));
      })
      .catch(() => {
        /* stage sync is best-effort */
      });
  };

  const copyDraft = () => {
    if (!selected?.outreachBody) return;
    navigator.clipboard.writeText(`Subject: ${selected.outreachSubject}\n\n${selected.outreachBody}`);
    setCopied(true);
    setDraftCopiedForActivation(true);
    setFirstThreeActions((prev) => ({ ...prev, started: true, copied: true, dismissed: false }));
    trackMarketingEvent("pipeline_draft_copy", {
      lead_id: selected.id,
      company: selected.company,
      stage: selected.stage,
    });
    toast.success("Draft copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const spotlightOutreachDraft = () => {
    const panel = outreachDraftRef.current;
    if (!panel) return;
    setOutreachDraftSpotlight(true);
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      panel.scrollIntoView({ behavior: "smooth", block: "center" });
      panel.focus({ preventScroll: true });
      panel.animate(
        [
          { transform: "scale(1)", boxShadow: "0 0 0 rgba(16, 185, 129, 0)" },
          { transform: "scale(1.015)", boxShadow: "0 0 0 8px rgba(16, 185, 129, 0.18)" },
          { transform: "scale(1)", boxShadow: "0 0 0 0 rgba(16, 185, 129, 0)" },
        ],
        { duration: 900, easing: "ease-out" },
      );
    }, 140);
    window.setTimeout(() => setOutreachDraftSpotlight(false), 2400);
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

  const handleSaveLead = async (deal: Deal): Promise<boolean> => {
    if (!session?.access_token) {
      window.location.href = signupHrefForLead(deal.id, deal.company, { src: "pipeline_save" });
      return false;
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
          return false;
        }
        throw new Error(errText);
      }
      const account = (await createResponse.json()) as { id: string; outreach_stage?: string | null };
      setCrmAccountIdByCompanyId((prev) => ({ ...prev, [deal.id]: account.id }));
      setCrmStageByCompanyId((prev) => ({ ...prev, [deal.id]: account.outreach_stage || "new" }));
      setDeals((prev) => prev.map((d) => (d.id === deal.id ? { ...d, stage: "Discovered", updatedAt: "just now" } : d)));
      // Funnel #20: activation — first saved lead (fires once per browser).
      trackFirstSave({ company: deal.company, industry: deal.industry || null });
      trackMarketingEvent("pipeline_save_success", {
        lead_id: deal.id,
        company: deal.company,
        industry: deal.industry || null,
        stage_before: deal.stage,
      });
      setFirstThreeActions((prev) => ({ ...prev, started: true, saved: true, dismissed: false }));
      setSavedLeadCount((count) => count + 1);
      setShowActivationChecklist(true);
      toast.success("Lead saved — develop with SIGNAL and send from the panel on the right.");
      return true;
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not save lead with SIGNAL");
      return false;
    } finally {
      setAdvancingLeadId(null);
    }
  };

  const startBuild25Pipeline = () => {
    setBuild25Started(true);
    try {
      sessionStorage.setItem("rfr_build15_started", "1");
    } catch {
      /* ignore */
    }
    document.getElementById("pipeline-leads")?.scrollIntoView({ behavior: "smooth", block: "start" });
    toast.success(`Matched pipeline unlocked — save up to ${BUILD_PIPELINE_TARGET} leads scored against your URL.`);
  };

  const matchedPipelineSignupHref = (() => {
    const params = new URLSearchParams();
    params.set("src", "results_scan");
    if (submittedUrl) params.set("url", submittedUrl);
    if (selected?.id != null) params.set("lead", String(selected.id));
    return `/signup?next=${encodeURIComponent(`/pipeline?${params.toString()}`)}&src=pipeline_matched_unlock&company_url=${encodeURIComponent(submittedUrl || "")}`;
  })();

  const startFreeWorkspaceHref = (() => {
    if (selected?.id != null) {
      const nextParams: Record<string, string> = {};
      if (submittedUrl) nextParams.url = submittedUrl;
      if (arrivedFromResultsScan) nextParams.src = "results_scan";
      return signupHrefForLead(selected.id, selected.company, {
        src: "pipeline_next_step",
        nextParams,
      });
    }
    const params = new URLSearchParams();
    params.set("src", arrivedFromResultsScan ? "results_scan" : "pipeline_next_step");
    if (submittedUrl) params.set("url", submittedUrl);
    return `/signup?next=${encodeURIComponent(`/pipeline?${params.toString()}`)}&src=pipeline_next_step`;
  })();

  const runNextStepPrimary = () => {
    if (arrivedFromResultsScan && !build25Started) {
      if (!isSignedIn) {
        window.location.href = matchedPipelineSignupHref;
        return;
      }
      startBuild25Pipeline();
      return;
    }
    if (arrivedFromResultsScan && build25Started && !selected) {
      document.getElementById("pipeline-leads")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (!isSignedIn) {
      // Navigation-only — do not call URL-submit / scan handlers from this CTA.
      window.location.href = startFreeWorkspaceHref;
      return;
    }
    if (arrivedFromResultsScan && canSaveSelected && selected) {
      void handleSaveLead(selected);
      return;
    }
    if (arrivedFromResultsScan && canCopySelectedDraft) {
      copyDraft();
      spotlightOutreachDraft();
      return;
    }
    if (canSaveSelected && selected) {
      void handleSaveLead(selected);
      return;
    }
    if (canCopySelectedDraft) {
      copyDraft();
      return;
    }
    if (canOpenSelectedDraft) {
      spotlightOutreachDraft();
    }
  };

  // Resume-save: a visitor who clicked "save & copy" on a specific lead is routed through
  // signup with ?resume=save. On return (now authenticated) we auto-complete that save so
  // the expressed intent becomes an activation (first_save) rather than a re-click new users
  // routinely skip — the largest gap in the signup → first-save funnel.
  const resumeSaveHandledRef = useRef(false);
  useEffect(() => {
    if (resumeSaveHandledRef.current || typeof window === "undefined") return;
    const url = new URLSearchParams(window.location.search);
    if (url.get("resume") !== "save") return;
    if (!session?.access_token) return; // wait for auth to resolve before saving
    const clearResumeParam = () => {
      url.delete("resume");
      const qs = url.toString();
      const nextUrl = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
      window.history.replaceState(null, "", nextUrl);
    };
    // Already activated in this workspace — honor the intent as done; never double-save.
    if (savedLeadCount !== 0) {
      resumeSaveHandledRef.current = true;
      clearResumeParam();
      return;
    }
    // Only auto-save once the exact lead the user acted on is loaded into the panel.
    const target =
      deepLinkLeadId != null
        ? selected && selected.id === deepLinkLeadId
          ? selected
          : null
        : selected;
    if (!target) return;
    resumeSaveHandledRef.current = true;
    clearResumeParam();
    void handleSaveLead(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleSaveLead is stable enough; ref guards re-entry
  }, [session?.access_token, savedLeadCount, selected, deepLinkLeadId]);

  const handleAdvanceLead = async (deal: Deal) => {
    if (!session?.access_token) {
      window.location.href = signupHrefForLead(deal.id, deal.company, { src: "pipeline_advance" });
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
        trackMarketingEvent("pipeline_outreach_sent", {
          lead_id: deal.id,
          company: deal.company,
          mode: "advance_auto",
        });
        setFirstThreeActions((prev) => ({ ...prev, started: true, sent: true, dismissed: false }));
        toast.success("Outreach sent. Replies will return to your workspace.");
        return;
      }

      setDeals((prev) => prev.map((d) => (d.id === deal.id ? { ...d, stage: "Draft Ready", updatedAt: "just now" } : d)));
      if (automationLevel === "manual") {
        copyDraft();
        toast.success("Lead saved. Draft ready — click Send outreach when you're happy with it.");
      } else if (!deal.contact) {
        toast.success("Lead saved. Add a contact email, then Send outreach.");
      } else {
        toast.success("Lead saved — SIGNAL can send when you're ready.");
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
      const r = await fetch(`${base}/api/admin/cal/draft-status?include_prospects=false`, hdrs);
      if (r.ok) {
        const d = await r.json() as { summary?: typeof scoutStats };
        if (d.summary) {
          setScoutStats(d.summary);
          return;
        }
      }
      const snap = await fetch(`${base}/api/admin/snapshot/section/cal?refresh=1`, hdrs);
      if (snap.ok) {
        const patch = await snap.json() as { data?: { summary?: typeof scoutStats } };
        if (patch.data?.summary) setScoutStats(patch.data.summary);
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
      toast.success(`SIGNAL drafted ${d.activated} emails.`);
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
      toast.success(`SIGNAL sent ${d.sent} emails.`);
      await loadScoutStats();
      setDeals((prev) => prev.map((d2) => d2.stage === "Draft Ready" ? { ...d2, stage: "Outreach Sent" as Stage, updatedAt: "just now" } : d2));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Send failed");
    } finally {
      setScoutBusy(null);
    }
  };

  const sendOneLead = async (deal: Deal, contactOverride?: string) => {
    if (!session?.access_token) {
      toast.info("Sign in to send outreach.");
      return;
    }
    const contactEmail = (contactOverride || deal.contact || "").trim();
    if (!contactEmail) {
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
        body: JSON.stringify({ contact_email: contactEmail, subject: deal.outreachSubject, outreach_draft: deal.outreachBody, send_identity: "scout" }),
      }));
      if (!sendRes.ok) throw new Error(await sendRes.text());
      setDeals((prev) => prev.map((d) => d.id === deal.id ? { ...d, stage: "Outreach Sent" as Stage, contact: d.contact || contactEmail, updatedAt: "just now" } : d));
      trackMarketingEvent("pipeline_outreach_sent", {
        lead_id: deal.id,
        company: deal.company,
        mode: "send_one",
      });
      const checklistVariant = deal.id % 2 === 0 ? "a" : "b";
      trackMarketingEvent(`pipeline_outreach_sent_variant_${checklistVariant}`, {
        lead_id: deal.id,
        company: deal.company,
        variant: checklistVariant,
        mode: "send_one",
      });
      if (contactOverride) {
        trackMarketingEvent("pipeline_send_with_captured_contact", {
          lead_id: deal.id,
          company: deal.company,
          email_domain: contactEmail.split("@")[1] || null,
        });
      }
      setFirstThreeActions((prev) => ({ ...prev, started: true, sent: true, dismissed: false }));
      toast.success(`Outreach sent to ${contactEmail}.`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Send failed");
    } finally {
      setSendingLeadId(null);
    }
  };

  const runContactAssistSend = () => {
    if (!selected) return;
    const email = capturedContactEmail.trim().toLowerCase();
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    if (!valid) {
      trackMarketingEvent("pipeline_contact_assist_invalid", {
        lead_id: selected.id,
        company: selected.company,
      });
      toast.error("Enter a valid contact email before sending.");
      return;
    }
    trackMarketingEvent("pipeline_contact_assist_submit", {
      lead_id: selected.id,
      company: selected.company,
      email_domain: email.split("@")[1] || null,
    });
    void sendOneLead(selected, email);
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
      toast.success("SIGNAL developed this lead — inference, brief, and outreach draft are ready.");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "SIGNAL could not develop this lead");
    } finally {
      setDevelopingLeadId(null);
    }
  };

  const dbTotal =
    scopeToSubmittedUrl
      ? displayedDeals.length
      : summary?.companies_in_database ?? summary?.total ?? (loadingSummary ? undefined : displayedDeals.length);
  const hotDeals =
    scopeToSubmittedUrl
      ? displayedDeals.filter((d) => userBucketForDeal(d) === "Hot Leads").length
      : summary?.hot ?? (loadingSummary ? undefined : displayedDeals.filter((d) => userBucketForDeal(d) === "Hot Leads").length);
  const warmDeals =
    scopeToSubmittedUrl
      ? displayedDeals.filter((d) => userBucketForDeal(d) === "Warm Leads").length
      : summary?.warm ?? (loadingSummary ? undefined : displayedDeals.filter((d) => userBucketForDeal(d) === "Warm Leads").length);
  const visibleDeals = displayedDeals.length;
  const filteredHot = displayedDeals.filter((d) => userBucketForDeal(d) === "Hot Leads").length;
  const filteredWarm = displayedDeals.filter((d) => userBucketForDeal(d) === "Warm Leads").length;
  const queuedActivations = activations.filter((a) => ["queued", "evaluating", "drafted", "awaiting_approval"].includes(a.status)).length;

  useEffect(() => {
    if (!session?.access_token) return;
    if (savedLeadCount > 0) {
      setFirstThreeActions((prev) => ({ ...prev, started: true, saved: true }));
    }
  }, [session?.access_token, savedLeadCount]);

  useEffect(() => {
    writeFirstThreeActions(firstThreeActions);
  }, [firstThreeActions]);

  useEffect(() => {
    let cancelled = false;
    const resolveChecklistVariantOverride = async () => {
      try {
        const response = await fetch(`${getApiBase()}/api/analytics?range=7d`, liveFetchInit());
        if (!response.ok) return;
        const payload = await response.json() as {
          marketing_conversion?: {
            events?: Record<string, number | undefined>;
            rates?: Record<string, number | undefined>;
            prev_events?: Record<string, number | undefined>;
          };
        };
        const mc = payload.marketing_conversion;
        if (!mc) return;
        const events = mc.events || {};
        const rates = mc.rates || {};
        const prev = mc.prev_events || {};
        const minSends = 20;
        const liftThreshold = 6;
        const sendsA = Number(events.pipeline_outreach_sent_variant_a ?? 0);
        const sendsB = Number(events.pipeline_outreach_sent_variant_b ?? 0);
        if (sendsA < minSends || sendsB < minSends) {
          if (!cancelled) setChecklistVariantOverride(null);
          return;
        }
        const currentLift = Number(rates.send_checklist_variant_b_ready_rate ?? 0) - Number(rates.send_checklist_variant_a_ready_rate ?? 0);
        const prevAViews = Number(prev.pipeline_send_checklist_variant_a_view ?? 0);
        const prevBViews = Number(prev.pipeline_send_checklist_variant_b_view ?? 0);
        const prevAReady = Number(prev.pipeline_send_checklist_variant_a_ready ?? 0);
        const prevBReady = Number(prev.pipeline_send_checklist_variant_b_ready ?? 0);
        const prevARate = prevAViews > 0 ? (prevAReady / prevAViews) * 100 : 0;
        const prevBRate = prevBViews > 0 ? (prevBReady / prevBViews) * 100 : 0;
        const prevLift = prevBRate - prevARate;

        let override: "a" | "b" | null = null;
        if (currentLift >= liftThreshold && prevLift >= liftThreshold) override = "b";
        if (currentLift <= -liftThreshold && prevLift <= -liftThreshold) override = "a";
        if (!cancelled) setChecklistVariantOverride(override);
      } catch {
        if (!cancelled) setChecklistVariantOverride(null);
      }
    };
    void resolveChecklistVariantOverride();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selected || selected.stage !== "Outreach Sent") return;
    setFirstThreeActions((prev) => ({ ...prev, started: true, sent: true }));
  }, [selected]);

  const showFirstThreeActionsProgress =
    Boolean(session?.access_token)
    && firstThreeActions.started
    && !firstThreeActions.dismissed
    && !firstThreeActions.sent;

  const nextFirstThreeStep = showFirstThreeActionsProgress ? firstThreeNextStep(firstThreeActions) : null;

  useEffect(() => {
    if (!selected) return;
    setCapturedContactEmail(selected.contact || "");
  }, [selected?.id, selected?.contact]);

  useEffect(() => {
    if (!selected || !session?.access_token || selected.contact || !selected.outreachBody) return;
    if (contactAssistSeenLeadIdsRef.current.has(selected.id)) return;
    contactAssistSeenLeadIdsRef.current.add(selected.id);
    trackMarketingEvent("pipeline_contact_assist_open", {
      lead_id: selected.id,
      company: selected.company,
    });
  }, [selected, session?.access_token]);

  const canSendSelectedOutreach = Boolean(
    selected
      && selected.contact
      && selected.outreachBody
      && selected.stage !== "Outreach Sent"
      && session?.access_token
      && sendingLeadId !== selected.id,
  );
  const selectedSendBlockers = selected
    ? [
        !selected.contact ? "missing_contact" : null,
        !selected.outreachBody ? "missing_draft" : null,
        selected.stage === "Outreach Sent" ? "already_sent" : null,
        !session?.access_token ? "not_authenticated" : null,
      ].filter((reason): reason is string => Boolean(reason))
    : [];
  const sendReadiness = {
    hasContact: Boolean(selected?.contact),
    hasDraft: Boolean(selected?.outreachBody),
    alreadySent: Boolean(selected?.stage === "Outreach Sent"),
  };
  const first3SaveCtaVariant = selected && selected.id % 2 === 0 ? "a" : "b";
  const first3SaveCtaLabel = first3SaveCtaVariant === "a"
    ? "Save this lead"
    : "Save lead and open your CRM workspace";
  const first3SaveHelperText = first3SaveCtaVariant === "a"
    ? "Save now to open your CRM workspace with draft, send, and reply tracking for this lead."
    : "One click opens your CRM workspace for this lead with draft and send tracking ready to run.";
  const sendChecklistAssignedVariant = selected && selected.id % 2 === 0 ? "a" : "b";
  const sendChecklistVariant = checklistVariantOverride || sendChecklistAssignedVariant;
  const sendChecklistVariantLabel = sendChecklistVariant === "a" ? "Variant A" : "Variant B";
  const sendChecklistVariantAutoPromoted = checklistVariantOverride === sendChecklistVariant;
  const sendChecklistItems = sendChecklistVariant === "a"
    ? [
        {
          key: "contact" as const,
          ready: sendReadiness.hasContact,
          readyLabel: "Contact email confirmed",
          blockedLabel: "Contact email missing",
        },
        {
          key: "draft" as const,
          ready: sendReadiness.hasDraft,
          readyLabel: "Outreach draft ready",
          blockedLabel: "Outreach draft missing",
        },
        {
          key: "status" as const,
          ready: !sendReadiness.alreadySent,
          readyLabel: "Not already sent",
          blockedLabel: "Already sent",
        },
      ]
    : [
        {
          key: "status" as const,
          ready: !sendReadiness.alreadySent,
          readyLabel: "Lead still open for send",
          blockedLabel: "Already sent",
        },
        {
          key: "contact" as const,
          ready: sendReadiness.hasContact,
          readyLabel: "Buyer contact email ready",
          blockedLabel: "Add buyer contact email",
        },
        {
          key: "draft" as const,
          ready: sendReadiness.hasDraft,
          readyLabel: "Draft approved for send",
          blockedLabel: "Generate outreach draft",
        },
      ];

  useEffect(() => {
    if (!selected || !session?.access_token) return;
    if (!sendChecklistSeenLeadIdsRef.current.has(selected.id)) {
      sendChecklistSeenLeadIdsRef.current.add(selected.id);
      trackMarketingEvent("pipeline_send_checklist_view", {
        lead_id: selected.id,
        company: selected.company,
        has_contact: sendReadiness.hasContact,
        has_draft: sendReadiness.hasDraft,
        already_sent: sendReadiness.alreadySent,
        blocker_count: selectedSendBlockers.length,
        variant: sendChecklistVariant,
      });
      trackMarketingEvent(`pipeline_send_checklist_variant_${sendChecklistVariant}_view`, {
        lead_id: selected.id,
        company: selected.company,
        variant: sendChecklistVariant,
      });
    }
    const isReady = sendReadiness.hasContact && sendReadiness.hasDraft && !sendReadiness.alreadySent;
    if (isReady && !sendChecklistReadyLeadIdsRef.current.has(selected.id)) {
      sendChecklistReadyLeadIdsRef.current.add(selected.id);
      trackMarketingEvent("pipeline_send_checklist_ready", {
        lead_id: selected.id,
        company: selected.company,
        variant: sendChecklistVariant,
      });
      trackMarketingEvent(`pipeline_send_checklist_variant_${sendChecklistVariant}_ready`, {
        lead_id: selected.id,
        company: selected.company,
        variant: sendChecklistVariant,
      });
    }
  }, [selected, session?.access_token, sendReadiness.hasContact, sendReadiness.hasDraft, sendReadiness.alreadySent, selectedSendBlockers.length, sendChecklistVariant]);

  const firstThreePrimaryActionLabel = nextFirstThreeStep === "save_lead"
    ? first3SaveCtaLabel
    : nextFirstThreeStep === "copy_draft"
      ? "Go to outreach draft"
      : nextFirstThreeStep === "send_outreach"
        ? (canSendSelectedOutreach ? "Send outreach now" : "Review send requirements")
        : "Continue";
  const firstThreePrimaryActionDisabled = nextFirstThreeStep === "save_lead"
    ? Boolean(!selected || advancingLeadId === selected.id)
    : nextFirstThreeStep === "copy_draft"
      ? false
      : nextFirstThreeStep === "send_outreach"
        ? Boolean(!selected || sendingLeadId === selected.id)
        : true;
  const firstThreeHelperText = nextFirstThreeStep === "save_lead"
    ? first3SaveHelperText
    : nextFirstThreeStep === "copy_draft"
      ? "Step 2 is fastest from the Outreach draft panel. We will highlight it now."
      : nextFirstThreeStep === "send_outreach"
        ? (canSendSelectedOutreach
          ? "Step 3 closes the loop. Send one live email to move this lead into outreach tracking."
          : `Send is blocked by: ${selectedSendBlockers.length ? selectedSendBlockers.join(", ") : "missing requirements"}. We will jump you to the draft area.`)
        : "All first actions complete.";

  const runFirstThreePrimaryAction = () => {
    if (!nextFirstThreeStep || !selected) return;
    trackMarketingEvent("pipeline_first3_coaching_click", {
      step: nextFirstThreeStep,
      lead_id: selected.id,
      company: selected.company,
      completed_count: firstThreeCompletedCount(firstThreeActions),
      save_cta_variant: nextFirstThreeStep === "save_lead" ? first3SaveCtaVariant : null,
    });
    if (nextFirstThreeStep === "save_lead") {
      void handleSaveLead(selected);
      return;
    }
    if (nextFirstThreeStep === "copy_draft") {
      spotlightOutreachDraft();
      return;
    }
    if (canSendSelectedOutreach) {
      void sendOneLead(selected);
      return;
    }
    trackMarketingEvent("pipeline_send_readiness_blocker", {
      step: "send_outreach",
      lead_id: selected.id,
      company: selected.company,
      blockers: selectedSendBlockers,
      blocker_reason: selectedSendBlockers[0] || "unknown",
    });
    spotlightOutreachDraft();
  };

  useEffect(() => {
    const prev = firstThreePrevRef.current;
    const newlyCompleted: FirstThreeStep[] = [];
    if (!prev.saved && firstThreeActions.saved) newlyCompleted.push("save_lead");
    if (!prev.copied && firstThreeActions.copied) newlyCompleted.push("copy_draft");
    if (!prev.sent && firstThreeActions.sent) newlyCompleted.push("send_outreach");
    for (const step of newlyCompleted) {
      trackMarketingEvent("pipeline_first3_step_completed", {
        step,
        completed_count: firstThreeCompletedCount(firstThreeActions),
        lead_id: selected?.id ?? null,
        company: selected?.company ?? null,
      });
      if (step === "save_lead") {
        trackMarketingEvent(`pipeline_first3_save_variant_${first3SaveCtaVariant}_completed`, {
          lead_id: selected?.id ?? null,
          company: selected?.company ?? null,
          variant: first3SaveCtaVariant,
        });
      }
    }
    firstThreePrevRef.current = firstThreeActions;
  }, [firstThreeActions, selected?.id, selected?.company, first3SaveCtaVariant]);

  useEffect(() => {
    if (!nextFirstThreeStep || !selected) {
      firstThreeEnteredRef.current = null;
      return;
    }
    if (firstThreeEnteredRef.current === nextFirstThreeStep) return;
    firstThreeEnteredRef.current = nextFirstThreeStep;
    trackMarketingEvent("pipeline_first3_step_entered", {
      step: nextFirstThreeStep,
      completed_count: firstThreeCompletedCount(firstThreeActions),
      lead_id: selected.id,
      company: selected.company,
      save_cta_variant: nextFirstThreeStep === "save_lead" ? first3SaveCtaVariant : null,
    });
    if (nextFirstThreeStep === "save_lead") {
      trackMarketingEvent(`pipeline_first3_save_variant_${first3SaveCtaVariant}_entered`, {
        lead_id: selected.id,
        company: selected.company,
        variant: first3SaveCtaVariant,
      });
    }
  }, [nextFirstThreeStep, selected, firstThreeActions, first3SaveCtaVariant]);

  useEffect(() => {
    if (firstThreeAbandonTimerRef.current) {
      clearTimeout(firstThreeAbandonTimerRef.current);
      firstThreeAbandonTimerRef.current = null;
    }
    if (!showFirstThreeActionsProgress || !nextFirstThreeStep || !selected) return;
    const signature = `${firstThreeActions.saved ? 1 : 0}${firstThreeActions.copied ? 1 : 0}${firstThreeActions.sent ? 1 : 0}:${nextFirstThreeStep}`;
    firstThreeAbandonTimerRef.current = setTimeout(() => {
      if (firstThreeAbandonSignaturesRef.current.has(signature)) return;
      firstThreeAbandonSignaturesRef.current.add(signature);
      trackMarketingEvent("pipeline_first3_step_abandoned", {
        step: nextFirstThreeStep,
        inactivity_seconds: FIRST_THREE_ABANDON_MS / 1000,
        completed_count: firstThreeCompletedCount(firstThreeActions),
        lead_id: selected.id,
        company: selected.company,
      });
    }, FIRST_THREE_ABANDON_MS);
    return () => {
      if (firstThreeAbandonTimerRef.current) {
        clearTimeout(firstThreeAbandonTimerRef.current);
        firstThreeAbandonTimerRef.current = null;
      }
    };
  }, [showFirstThreeActionsProgress, nextFirstThreeStep, firstThreeActions, selected]);

  return (
    <div className="pipeline-page-bg flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 px-4 pb-6 pt-4 lg:px-6">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-3">
          {!step3Intro ? (
            <PageHeroDark
              maxWidthClass="max-w-[1500px]"
              showGrid={false}
              badge={
                <div className="page-hero-badge">
                  {typeof dbTotal === "number" ? dbTotal.toLocaleString() : "Loading"} active opportunities · updated live
                </div>
              }
              eyebrow="SIGNAL · Sales intelligence"
              title={isAdmin ? "Active Signals → Live Pipeline" : "Live Pipeline"}
              description={
                session?.access_token
                  ? "SIGNAL automates your sales pipeline and CRM process. It continuously reads market movement, and ReadyForRobots turns that analysis into outreach-ready pipeline decisions. Pick a lead on the left → develop with SIGNAL → send from the panel on the right. Replies land in Inbox."
                  : "SIGNAL automates your sales pipeline and CRM process. It continuously reads market movement, and ReadyForRobots turns that analysis into outreach-ready pipeline decisions. Every lead shows what to pitch — not just who to call. Pipeline actions and robot categories on every row."
              }
              stats={[
                { label: "Total leads", value: typeof dbTotal === "number" ? dbTotal.toLocaleString() : "Loading", tone: "white" },
                { label: "Hot", value: typeof hotDeals === "number" ? hotDeals : "Loading", tone: "amber" },
                { label: "Warm", value: typeof warmDeals === "number" ? warmDeals : "Loading", tone: "amber" },
                { label: "Visible", value: visibleDeals, tone: "emerald" },
              ]}
              innerClassName="pb-6 pt-20"
            />
          ) : (
            <div className="flex items-center justify-between gap-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              <span>ReadyForRobots · Workspace</span>
              {session?.access_token ? (
                <span className="normal-case tracking-normal text-emerald-300/90">Signed in · {sessionDisplayName}</span>
              ) : null}
            </div>
          )}

          {!step3Intro ? (
            <div className="pipeline-command-rail flex flex-col gap-3">
              {session?.access_token && <AdminNav variant="dark" />}

              <PipelineSalesWorkflowRail
                hasSession={Boolean(session?.access_token)}
                hasSavedLeads={savedLeadCount > 0}
                hasSelection={Boolean(selected)}
                hasDraft={Boolean(selected?.outreachBody)}
                hasContact={Boolean(selected?.contact)}
                sent={selected?.stage === "Outreach Sent"}
                variant="dark"
                browseFirst={arrivedFromResultsScan}
              />
              {session?.access_token && (
                <WorkspaceQuickLinks
                  savedCount={savedLeadCount}
                  hubspotConnected={hubspotIntegration?.connected}
                  queuedActions={queuedActivations}
                  variant="dark"
                />
              )}
            </div>
          ) : null}

          {arrivedFromResultsScan && !arrivedFromSignalActivation && (
            <section
              id="pipeline-step3-guide"
              className={`scroll-mt-4 overflow-hidden rounded-2xl border shadow-[0_24px_60px_-28px_rgba(245,158,11,0.55)] ${
                build25Started
                  ? "border-emerald-400/35 bg-[#071a14]"
                  : "border-amber-400/50 bg-gradient-to-br from-[#1c1608] via-[#12100a] to-[#0b1220]"
              }`}
            >
              {!build25Started ? (
                <div className="px-5 py-7 sm:px-8 sm:py-9 lg:px-10 lg:py-10">
                  <p className="text-xs font-bold uppercase tracking-[0.22em] text-amber-300 sm:text-sm">
                    Step 3 of 3 · URL-matched sales pipeline
                  </p>
                  <h2 className="mt-3 max-w-4xl text-3xl font-bold leading-[1.15] tracking-tight text-white sm:text-4xl lg:text-[2.65rem]">
                    {isSignedIn
                      ? `Open ${BUILD_PIPELINE_TARGET} buyers matched to your robot URL.`
                      : `Create a free account to unlock ${BUILD_PIPELINE_TARGET} matched sales leads.`}
                  </h2>
                  <p className="mt-4 max-w-3xl text-base leading-relaxed text-slate-300 sm:text-lg sm:leading-8">
                    Lookup → score → match. We scored
                    {submittedHostname ? (
                      <>
                        {" "}
                        <span className="font-semibold text-amber-100">{submittedHostname}</span>
                      </>
                    ) : (
                      " your robot company"
                    )}{" "}
                    and paired it with equally scored customer opportunities — not the global market queue.
                    {isSignedIn
                      ? " Unlock your matched list, save fits, then run outreach."
                      : " Free account details unlock the matched pipeline."}
                  </p>

                  <ol className="mt-7 grid gap-3 sm:grid-cols-3">
                    {[
                      { n: "1", t: "URL scored", d: "Your robot company profile from the submitted URL." },
                      { n: "2", t: `${BUILD_PIPELINE_TARGET} matched leads`, d: "Buyers scored in the same band as your robot profile." },
                      { n: "3", t: "Curate + outreach", d: "Save fits, copy Cal’s note, send." },
                    ].map((step) => (
                      <li
                        key={step.n}
                        className="rounded-xl border border-amber-400/25 bg-black/25 px-4 py-4"
                      >
                        <p className="text-xs font-bold uppercase tracking-[0.18em] text-amber-300">Step {step.n}</p>
                        <p className="mt-2 text-lg font-semibold text-white sm:text-xl">{step.t}</p>
                        <p className="mt-1.5 text-sm leading-relaxed text-slate-400 sm:text-[15px]">{step.d}</p>
                      </li>
                    ))}
                  </ol>

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                    <button
                      type="button"
                      onClick={runNextStepPrimary}
                      className="inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-amber-400 px-7 py-4 text-base font-extrabold text-slate-950 transition hover:bg-amber-300 sm:w-auto sm:min-w-[280px] sm:text-lg"
                    >
                      {nextStepPrimaryLabel}
                      <ArrowRight className="h-5 w-5" />
                    </button>
                    <p className="text-sm text-slate-400 sm:max-w-xs">
                      {isSignedIn
                        ? "Opens your URL-matched list only — browse-the-market is not this path."
                        : "Account first, then your 15 matched leads. Preview stays on Results."}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 px-5 py-5 sm:px-7 lg:grid-cols-[1fr_auto] lg:items-center">
                  <div className="min-w-0">
                    <span className="inline-flex items-center rounded-full border border-emerald-400/40 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-200">
                      Building · {build25Progress}/{BUILD_PIPELINE_TARGET} leads
                    </span>
                    <h2 className="mt-2 text-2xl font-bold text-white sm:text-3xl">
                      Curate sales leads &amp; run outreach
                    </h2>
                    <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-300 sm:text-base">
                      Save the best companies into your working list (goal: {BUILD_PIPELINE_TARGET}). Open each lead for why-now signals, copy Cal’s note, and send.
                    </p>
                    <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs font-semibold text-slate-300 sm:text-sm">
                      <span className={build25Progress > 0 ? "text-emerald-300" : "text-amber-200"}>
                        1. Save leads ({build25Progress}/{BUILD_PIPELINE_TARGET})
                      </span>
                      <span>2. Copy outreach draft</span>
                      <span>3. Send &amp; continue</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={runNextStepPrimary}
                    className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-amber-400 px-5 py-3 text-sm font-extrabold text-slate-950 transition hover:bg-amber-300 lg:w-auto"
                  >
                    {nextStepPrimaryLabel}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              )}
            </section>
          )}

          {arrivedFromSignalActivation && (
            <section className="overflow-hidden rounded-xl border border-emerald-400/40 bg-[#071a19] shadow-[0_18px_45px_-30px_rgba(16,185,129,0.85)]">
              <div className="grid gap-4 px-4 py-4 sm:px-5 lg:grid-cols-[1fr_auto] lg:items-center">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center rounded-full border border-emerald-400/40 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-200">
                      SIGNAL activated
                    </span>
                    {activationIdFromQuery && (
                      <span className="text-[11px] font-medium text-slate-400">Queue #{activationIdFromQuery}</span>
                    )}
                  </div>
                  <h2 className="mt-2 text-xl font-bold text-white sm:text-2xl">
                    {selected ? `${selected.company} is ready for your review.` : "Your buyer pipeline is being prepared."}
                  </h2>
                  <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-300">
                    SIGNAL saved the selected buyers to CRM and is preparing account-specific outreach. Review the why-now evidence, then copy the draft and send your first message.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-[11px] font-semibold text-slate-300">
                    <span className="text-emerald-300">1. Buyers saved</span>
                    <span className={firstThreeActions.copied ? "text-emerald-300" : ""}>2. Review and copy draft</span>
                    <span className={firstThreeActions.sent ? "text-emerald-300" : ""}>3. Send outreach</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={runFirstThreePrimaryAction}
                  disabled={!selected || firstThreePrimaryActionDisabled}
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-amber-400 px-5 py-3 text-sm font-extrabold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
                >
                  {selected?.outreachBody ? "Review prepared outreach" : "Review selected buyer"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </section>
          )}

          {step3Intro ? (
            <div className="pipeline-workspace overflow-hidden rounded-2xl border border-amber-400/40 bg-gradient-to-b from-slate-50 to-white shadow-[0_20px_50px_-30px_rgba(15,23,42,0.45)]">
              <div className="border-b border-amber-200/80 bg-amber-50/80 px-5 py-4 sm:px-8">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-800">URL-matched queue · locked</p>
                <p className="mt-1 text-xl font-bold text-slate-900 sm:text-2xl">
                  {scopeMatchesCount > 0
                    ? `${Math.min(scopeMatchesCount, BUILD_PIPELINE_TARGET)} buyers matched to your robot profile`
                    : `${BUILD_PIPELINE_TARGET} matched sales leads waiting`}
                </p>
                <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-base">
                  These {BUILD_PIPELINE_TARGET} leads are scored against your robot URL profile. Unlock the matched list to curate and outreach — not the global market feed.
                </p>
              </div>
              <div className="relative px-5 py-6 sm:px-8 sm:py-8">
                <ul className="pointer-events-none select-none space-y-2 opacity-45 blur-[1.5px]">
                  {(displayedDeals.length > 0 ? displayedDeals : deals).slice(0, 5).map((deal) => (
                    <li
                      key={deal.id}
                      className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3"
                    >
                      <span className="truncate text-sm font-semibold text-slate-800">{deal.company}</span>
                      <span className="text-xs font-bold uppercase tracking-wide text-slate-500">{deal.priorityTier || deal.stage}</span>
                    </li>
                  ))}
                  {(displayedDeals.length > 0 ? displayedDeals : deals).length === 0 ? (
                    <li className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                      Loading matched opportunities…
                    </li>
                  ) : null}
                </ul>
                <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-white via-white/85 to-white/40 px-4">
                  <div className="w-full max-w-md rounded-2xl border border-amber-400/60 bg-white/95 p-5 text-center shadow-xl sm:p-6">
                    <p className="text-sm font-semibold text-slate-800 sm:text-base">
                      {isSignedIn
                        ? `Unlock your ${BUILD_PIPELINE_TARGET} URL-matched sales leads.`
                        : `Free account unlocks ${BUILD_PIPELINE_TARGET} matched leads for your robot URL.`}
                    </p>
                    <button
                      type="button"
                      onClick={runNextStepPrimary}
                      className="mt-4 inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-amber-400 px-6 py-4 text-base font-extrabold text-slate-950 transition hover:bg-amber-300 sm:text-lg"
                    >
                      {nextStepPrimaryLabel}
                      <ArrowRight className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
          <div className="pipeline-workspace">
            {/* ── Workspace toolbar ── */}
            <div className="pipeline-page-header">
              <div className="pipeline-page-header-inner flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div className="min-w-0">
                  <span className="inline-flex items-center rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-900">
                    Search pipeline
                  </span>
                  <p className="mt-1 text-sm font-semibold text-slate-900">Find buyers by industry, company, or signal.</p>
                  {session?.access_token && (
                    <p className="mt-1 text-[12px] font-medium text-emerald-900">
                      Welcome back, {sessionDisplayName}. Your sales workspace is active.
                    </p>
                  )}
                  {submittedHostname && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center rounded-full border border-emerald-700 bg-emerald-200 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-emerald-950">
                        URL matched · {BUILD_PIPELINE_TARGET} max
                      </span>
                      <span className="inline-flex items-center rounded-full border border-slate-500 bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-900">
                        Submitted URL: {submittedHostname}
                      </span>
                      <p className="text-[11px] font-medium text-slate-800">
                        {submittedUrlMatchLoading
                          ? `Looking up ${submittedHostname}, scoring the robot company, matching opportunities…`
                          : submittedUrlMatchError
                          ? `Temporarily unable to refresh matches for ${submittedHostname}. Showing latest available matched results.`
                          : scopeMatchesCount === 0
                          ? submittedUrlWeakProfile
                            ? `No matches for ${submittedHostname}. We could not score enough robot profile detail from that URL yet.`
                            : `No equal-score matches for ${submittedHostname} yet. Try the company homepage URL.`
                          : `Showing ${scopeMatchesCount} buyers matched to ${submittedHostname} (equally scored opportunities).`}
                      </p>
                      {!preferUrlMatchedPipeline && !submittedUrlMatchLoading ? (
                        <button
                          type="button"
                          onClick={() => setScopeToSubmittedUrl((v) => !v)}
                          className="rounded-md border border-slate-600 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-900 hover:border-slate-800 hover:bg-slate-100"
                        >
                          {scopeToSubmittedUrl ? "Show all results" : "Show submitted URL scope"}
                        </button>
                      ) : null}
                    </div>
                  )}
                  <div className="mt-2 w-full rounded-xl border border-emerald-700/80 bg-[#0b162f] px-4 py-4 text-[13px] text-slate-100 shadow-sm sm:px-5 sm:py-5 sm:text-sm">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-amber-300 sm:text-xs">{nextStepsTitle}</p>
                    <p className="mt-2 text-base font-semibold text-white sm:text-lg">
                      {nextStepsHeadline}
                    </p>
                    <ol className="mt-3 space-y-2 pl-5 text-slate-300 sm:text-[15px]">
                      {nextStepsItems.map((item, index) => (
                        <li key={`${index}-${item.slice(0, 24)}`} className="list-decimal leading-relaxed">
                          {item}
                        </li>
                      ))}
                    </ol>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {!isSignedIn && !arrivedFromResultsScan ? (
                        <Link
                          href={startFreeWorkspaceHref}
                          className="inline-flex items-center justify-center rounded-lg border-2 border-amber-400 bg-amber-400 px-3 py-2 text-[11px] font-bold text-slate-950 hover:bg-amber-300"
                        >
                          {nextStepPrimaryLabel}
                        </Link>
                      ) : (
                        <button
                          type="button"
                          onClick={runNextStepPrimary}
                          disabled={
                            arrivedFromResultsScan && (!build25Started || !selected)
                              ? false
                              : isSignedIn && !selected && !canCopySelectedDraft
                          }
                          className="inline-flex items-center justify-center rounded-lg border-2 border-amber-400 bg-amber-400 px-3 py-2 text-[11px] font-bold text-slate-950 hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {nextStepPrimaryLabel}
                        </button>
                      )}
                      {isSignedIn && canCopySelectedDraft && canSaveSelected ? (
                        <button
                          type="button"
                          onClick={copyDraft}
                          className="inline-flex items-center justify-center rounded-lg border border-white/20 bg-white/5 px-2.5 py-1.5 text-[11px] font-semibold text-slate-100 hover:bg-white/10"
                        >
                          {copied ? "Copied draft" : "Copy draft"}
                        </button>
                      ) : null}
                      {canOpenSelectedDraft ? (
                        <button
                          type="button"
                          onClick={spotlightOutreachDraft}
                          className="inline-flex items-center justify-center rounded-lg border border-white/20 bg-white/5 px-2.5 py-1.5 text-[11px] font-semibold text-slate-100 hover:bg-white/10"
                        >
                          Open selected lead
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className="relative w-full sm:w-[340px]">
                  <Filter className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />
                  <input
                    value={industryQuery}
                    onChange={(e) => {
                      setIndustryQuery(e.target.value);
                      setFilter("All");
                    }}
                    list="pipeline-industries"
                    placeholder="Search pipeline: industry, company, or signal…"
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
              <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-wrap gap-2">
                  {([
                    { key: "all", label: "All confidence" },
                    { key: "high", label: "High confidence" },
                    { key: "medium", label: "Medium confidence" },
                    { key: "low", label: "Low confidence" },
                  ] as const).map((option) => {
                    const active = qualityBandFilter === option.key;
                    return (
                      <button
                        key={option.key}
                        type="button"
                        onClick={() => setQualityBandFilter(option.key)}
                        className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors ${
                          active
                            ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                            : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900"
                        }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <select
                    value={qualitySort}
                    onChange={(e) => setQualitySort(e.target.value as QualitySort)}
                    className="sb-input min-w-[230px] py-2 text-sm"
                  >
                    <option value="default">Default ranking</option>
                    <option value="quality_desc">Sort: lead quality high → low</option>
                    <option value="quality_asc">Sort: lead quality low → high</option>
                    <option value="buyer_authenticity">Sort: buyer authenticity</option>
                    <option value="urgency_window">Sort: urgency window</option>
                    <option value="robot_fit_confidence">Sort: robot fit</option>
                    <option value="decision_maker_confidence">Sort: decision-maker confidence</option>
                    <option value="contactability_confidence">Sort: contactability</option>
                  </select>
                  {qualityControlsActive && (
                    <button
                      type="button"
                      onClick={() => {
                        setQualityBandFilter("all");
                        setQualitySort("default");
                      }}
                      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-semibold text-slate-600 hover:text-slate-900"
                    >
                      Reset quality view
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="px-3 sm:px-4 pt-2">
              <div className="sticky top-2 z-30 mb-2 rounded-xl border-2 border-amber-400 bg-gradient-to-r from-amber-100 via-white to-emerald-100 px-4 py-3 shadow-[0_14px_28px_-16px_rgba(245,158,11,0.9)]">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="inline-flex items-center rounded-full border border-amber-300 bg-amber-200/70 px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.16em] text-amber-900">
                      Priority
                    </p>
                    <p className="mt-1 flex items-center gap-1.5 text-base font-extrabold text-emerald-900">
                      <Sparkles className="h-4 w-4 text-amber-600" />
                      Upgrade to Pro and begin building your sales campaign.
                    </p>
                  </div>
                  <Link
                    href="/pricing?upgrade=pro&src=pipeline_top_banner"
                    className="inline-flex items-center justify-center rounded-lg border-2 border-amber-500 bg-amber-400 px-4 py-2 text-sm font-extrabold text-amber-950 shadow-sm transition hover:bg-amber-300"
                  >
                    Upgrade to Pro
                  </Link>
                </div>
              </div>
              {panelPlan === "anonymous" && (
                <AnonymousValueStrip
                  leadCount={deals.length}
                  limit={entitlements?.pipeline_limit ?? previewLimit}
                  selectedCompany={selected?.company}
                  selectedLeadId={selected?.id}
                />
              )}
              {panelPlan === "anonymous" && rotationPaused && (
                <div className="mt-2 flex items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-[11px] text-gray-500">
                  <span>Rotation paused — read the full draft, then save it free.</span>
                  <button
                    type="button"
                    onClick={() => setRotationPaused(false)}
                    className="shrink-0 font-semibold text-emerald-700 hover:text-emerald-800"
                  >
                    Resume live ↻
                  </button>
                </div>
              )}
              {session?.access_token && savedLeadCount === 0 && selected && (
                <div className={panelPlan === "anonymous" ? "mt-2" : "mt-0 mb-2"}>
                  <FirstSaveNudge
                    deal={selected}
                    saving={advancingLeadId === selected.id}
                    onSave={() => void handleSaveLead(selected)}
                  />
                </div>
              )}
              {session?.access_token && (showActivationChecklist || savedLeadCount === 1) && (
                <div className="mt-2">
                  <ActivationChecklist
                    company={selected?.company}
                    draftCopied={draftCopiedForActivation}
                    hasDraft={Boolean(selected?.outreachBody)}
                    onCopyDraft={copyDraft}
                  />
                </div>
              )}
              <div className={panelPlan === "anonymous" ? "mt-2" : savedLeadCount === 0 ? "" : "mt-2"}>
                <CrmPathFork
                  connected={hubspotIntegration?.connected}
                  hasSession={Boolean(session?.access_token)}
                  savedCount={savedLeadCount}
                />
              </div>
              {session?.access_token && panelPlan === "free" && (
                <div className="mt-2 rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-white px-4 py-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-sm font-semibold text-emerald-900">
                      {freeUpgradeMessage}
                    </p>
                    <Link
                      href="/pricing?upgrade=pro"
                      className="inline-flex items-center justify-center rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:border-emerald-400"
                    >
                      Upgrade to Pro
                    </Link>
                  </div>
                </div>
              )}
            </div>
            {(loadErr || (!loadingLeads && !loadErr && !hasActiveSearch && displayedDeals.length === 0)) && (
              <div className="space-y-1.5 border-b border-gray-200 px-3 py-2 sm:px-4">
                {loadErr && (
                  <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
                    <div className="flex items-center justify-between gap-2">
                      <span>{loadErr}</span>
                      <button
                        type="button"
                        onClick={() => window.location.reload()}
                        className="shrink-0 rounded-md border border-amber-300 bg-white px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-amber-900 hover:bg-amber-100"
                      >
                        Retry
                      </button>
                    </div>
                  </div>
                )}
                {!loadingLeads && !loadErr && !hasActiveSearch && displayedDeals.length === 0 && (
                  <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2.5 text-emerald-900">
                    {scopedNoMatches ? (
                      <>
                        <p className="text-xs font-semibold">
                          No direct buyer matches yet for {submittedHostname}.
                        </p>
                        <p className="mt-1 text-[11px] leading-snug text-emerald-800">
                          SIGNAL did not find a direct URL match in this pass. Switch to full pipeline results now, or try the company root domain to widen matching.
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-xs font-semibold">
                          Live pipeline is rebuilding — your buyers are still here.
                        </p>
                        <p className="mt-1 text-[11px] leading-snug text-emerald-800">
                          {typeof hotDeals === "number" || typeof warmDeals === "number"
                            ? `${formatMetric(hotDeals)} hot · ${formatMetric(warmDeals)} warm robot buyers scored across ${formatMetric(dbTotal)} tracked accounts. The ranked feed paints in seconds — keep moving while it syncs.`
                            : "The ranked buyer feed paints in a few seconds. Keep moving while it syncs."}
                        </p>
                      </>
                    )}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {scopedNoMatches ? (
                        <button
                          type="button"
                          onClick={() => setScopeToSubmittedUrl(false)}
                          className="inline-flex items-center rounded-md bg-emerald-600 px-2.5 py-1 text-[11px] font-semibold text-white transition hover:bg-emerald-700"
                        >
                          Show full pipeline results
                        </button>
                      ) : null}
                      <Link
                        href="/signals"
                        className="inline-flex items-center rounded-md bg-emerald-600 px-2.5 py-1 text-[11px] font-semibold text-white transition hover:bg-emerald-700"
                      >
                        Browse live buyer signals →
                      </Link>
                      <Link
                        href="/results?url="
                        className="inline-flex items-center rounded-md border border-emerald-400 bg-white px-2.5 py-1 text-[11px] font-semibold text-emerald-800 transition hover:bg-emerald-100"
                      >
                        Scan a company URL
                      </Link>
                    </div>
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

          {/* ── SIGNAL stats strip (admin only) ── */}
          {isAdmin && session?.access_token && scoutStats && (
            <div className="flex items-center gap-3 flex-wrap text-[11px] text-gray-500 px-1">
              <span className="font-bold uppercase tracking-[0.15em] text-[10px]" style={{ color: "#10b981" }}>SIGNAL</span>
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
              <p className="text-[11px] text-blue-900 flex-1">SIGNAL will draft MSD outreach for all HOT and WARM prospects that do not have one yet. Continue?</p>
              <button onClick={() => void runScoutDraftAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-blue-50 border border-blue-400/40 text-blue-800">Run</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-gray-500">Cancel</button>
            </div>
          )}
          {isAdmin && scoutConfirm === "send" && (
            <div className="rounded-xl border border-emerald-400/30 bg-emerald-400/8 px-4 py-3 flex items-center gap-3">
              <p className="text-[11px] text-emerald-900 flex-1">SIGNAL will activate all drafted outreach now. This triggers live sends via Resend. Continue?</p>
              <button onClick={() => void runScoutSendAll()} className="px-3 py-1.5 rounded-lg text-[11px] font-bold bg-emerald-50 border border-emerald-400/40 text-emerald-800">Send</button>
              <button onClick={() => setScoutConfirm(null)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-gray-500">Cancel</button>
            </div>
          )}

          {/* ── Two-panel layout ── */}
          <div id="pipeline-leads" className="pipeline-deals-layout flex min-h-0 flex-col gap-2 p-2 sm:p-3 lg:min-h-[calc(100vh-200px)] lg:flex-row">

            {/* LEFT: Lead pipeline (users) or admin stage columns */}
            <div className="pipeline-list-shell flex min-w-0 flex-1 flex-col gap-1 overflow-y-auto">
              <div className="pipeline-list-columns">
                <div className="col-span-5">Company</div>
                <div className="col-span-4 hidden md:block">Signal</div>
                <div className="col-span-1 text-center">Score</div>
                <div className="col-span-2 text-right">Tier</div>
              </div>
              {(loadingLeads || serverSearchLoading) && displayedDeals.length === 0 ? (
                <div className="mx-1 mb-2 rounded-xl border border-dashed border-stone-400 bg-stone-100/80 px-4 py-8 text-center">
                  <RefreshCw className="mx-auto h-6 w-6 animate-spin text-emerald-600" />
                  <p className="mt-3 text-sm font-medium text-stone-700">
                    {serverSearchLoading ? `Searching for "${activeSearchQuery}"…` : "Loading sales pipeline…"}
                  </p>
                </div>
              ) : showKanban ? (
              STAGES.map((stage) => {
                const stageDeals = displayedDeals.filter((d) => d.stage === stage);
                const meta = STAGE_META[stage];
                return (
                  <div key={stage}>
                    {/* Stage header row */}
                    <div className="pipeline-tier-header">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: meta.dot }} />
                      <span className="pipeline-tier-title">{stageLabel(stage)}</span>
                      <span className="ml-0.5 text-[10px] font-medium text-slate-600">— {stageDesc(stage)}</span>
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
                          const missingCount = missingEvidenceCountForDeal(deal);
                          const chip = gapChipStyle(missingCount);
                          return (
                            <div
                              key={deal.id}
                              role="button"
                              tabIndex={0}
                              onClick={() => selectLead(deal.id)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  selectLead(deal.id);
                                }
                              }}
                              className={`group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${dealRowSurface(isSelected)}`}
                              style={{ borderLeftColor: dealTierColor(deal) }}
                            >
                              <PipelineScoreBadge score={deal.score} deal={deal} />
                              <WorkMatchBadge deal={deal} />

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
                                  {missingCount > 0 && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      title={`Evidence gaps: ${chip.label} priority`}
                                      style={{ color: chip.color, background: chip.background, border: chip.border }}
                                    >
                                      {missingCount} gap{missingCount === 1 ? "" : "s"}
                                    </span>
                                  )}
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
                                  {deal.humanoidNonUsVendorFlag && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      style={{ color: "#b45309", background: "rgba(245,158,11,0.14)", border: "1px solid rgba(245,158,11,0.28)" }}
                                    >
                                      Non-US
                                    </span>
                                  )}
                                </div>
                                <PipelineLeadActionMeta lead={deal} variant="compact" />
                              </div>

                              <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                                <LeadShareBar compact lead={dealToShareLead(deal)} />
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
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
              ) : (
              USER_BUCKETS.map((bucket) => {
                const bucketDeals = displayedDeals.filter((d) => userBucketForDeal(d) === bucket);
                const meta = USER_BUCKET_META[bucket];
                return (
                  <div key={bucket}>
                    <div className="pipeline-tier-header">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: meta.dot }} />
                      <span className="pipeline-tier-title">{bucket}</span>
                      <span className="ml-0.5 text-[10px] font-medium text-slate-600">— {meta.desc}</span>
                      <span
                        className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded font-mono"
                        style={{ color: meta.color, background: `${meta.color}15`, fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {bucketDeals.length}
                        {panelPlan === "anonymous" && !hasActiveSearch && bucketDeals.length < meta.slotCap ? (
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
                          const missingCount = missingEvidenceCountForDeal(deal);
                          const chip = gapChipStyle(missingCount);
                          return (
                            <div
                              key={deal.id}
                              role="button"
                              tabIndex={0}
                              onClick={() => selectLead(deal.id)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  selectLead(deal.id);
                                }
                              }}
                              className={`group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${dealRowSurface(isSelected)}`}
                              style={{ borderLeftColor: dealTierColor(deal) }}
                            >
                              <PipelineScoreBadge score={deal.score} deal={deal} />
                              <WorkMatchBadge deal={deal} />

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
                                  {missingCount > 0 && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      title={`Evidence gaps: ${chip.label} priority`}
                                      style={{ color: chip.color, background: chip.background, border: chip.border }}
                                    >
                                      {missingCount} gap{missingCount === 1 ? "" : "s"}
                                    </span>
                                  )}
                                  {deal.humanoidPilotTier &&
                                    ["ACTIVE_PILOT", "PILOT_INTENT"].includes(deal.humanoidPilotTier) && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      style={{ color: "#059669", background: "rgba(3,218,197,0.12)", border: "1px solid rgba(3,218,197,0.25)" }}
                                    >
                                      Humanoid
                                    </span>
                                  )}
                                  {deal.humanoidNonUsVendorFlag && (
                                    <span
                                      className="text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 uppercase tracking-wide"
                                      style={{ color: "#b45309", background: "rgba(245,158,11,0.14)", border: "1px solid rgba(245,158,11,0.28)" }}
                                    >
                                      Non-US
                                    </span>
                                  )}
                                </div>
                                <PipelineLeadActionMeta lead={deal} variant="compact" />
                              </div>

                              <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                                <LeadShareBar compact lead={dealToShareLead(deal)} />
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
                            </div>
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
              className="pipeline-detail-shell flex h-auto max-h-none w-full shrink-0 flex-col overflow-hidden lg:sticky lg:top-20 lg:h-[calc(100vh-100px)] lg:max-h-[calc(100vh-100px)] lg:w-[380px] xl:w-[400px]"
            >
              {selected ? (
                <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                  {/* Detail header */}
                  <div className="pipeline-detail-header">
                    <div className="pipeline-detail-header-inner">
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <div>
                        <p className="sb-kicker mb-0.5 text-emerald-800">CRM · Lead workspace</p>
                        <p className="font-display text-base font-semibold text-gray-900">
                          {selected.company}
                        </p>
                        <div className="mt-1 flex items-center gap-2 text-[11px] text-gray-600">
                          <MapPin className="h-3 w-3" />
                          {selected.location}
                          <span className="text-gray-400">·</span>
                          {selected.industry}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <PipelineScoreBadge score={selected.score} deal={selected} size="lg" />
                        <WorkMatchBadge deal={selected} size="lg" />
                        {selected.workMatch != null && (
                          <p className="max-w-[11rem] text-right text-[10px] leading-snug text-stone-500">
                            Work Match {Math.round(selected.workMatch)}%
                            {selected.workMatchManufacturer ? ` · ${selected.workMatchManufacturer}` : ""}
                            {selected.comparableDeployment?.robot
                              ? ` · Evidence: ${selected.comparableDeployment.robot}`
                              : ""}
                          </p>
                        )}
                        {selected.hermesQualify?.automation_fit != null && (
                          <p className="max-w-[11rem] text-right text-[10px] leading-snug text-sky-700">
                            Hermes fit {Math.round(Number(selected.hermesQualify.automation_fit))}
                            {selected.hermesQualify.vendor_shortlist?.[0]?.vendor
                              ? ` · ${selected.hermesQualify.vendor_shortlist[0].vendor}`
                              : ""}
                          </p>
                        )}
                        {isAdmin && (
                          <button
                            type="button"
                            onClick={() => openWorkspaceHref("/admin#cal-outreach", setLocation)}
                            className="rounded-md border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-800 transition-colors hover:bg-emerald-100"
                            title="Open SIGNAL Ops"
                          >
                            Ops
                          </button>
                        )}
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
                  </div>

                  {(selected.hermesQualify ||
                    (selected.hermesJobTitles && selected.hermesJobTitles.length > 0) ||
                    (selected.hermesDecisionMakers && selected.hermesDecisionMakers.length > 0)) && (
                    <div className="border-b border-slate-100 bg-sky-50/60 px-5 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-sky-900">
                        Hermes intelligence
                        {selected.hermesQualify?.truth_state ? (
                          <span className="ml-1.5 font-semibold normal-case tracking-normal text-sky-700/80">
                            · overlay (not CRM truth)
                          </span>
                        ) : null}
                      </p>
                      {selected.hermesQualify?.automation_fit != null && (
                        <p className="mt-1 text-[12px] leading-snug text-slate-800">
                          Automation fit{" "}
                          <span className="font-semibold">{Math.round(Number(selected.hermesQualify.automation_fit))}</span>
                          {selected.hermesQualify.labor_intensity
                            ? ` · labor ${selected.hermesQualify.labor_intensity}`
                            : ""}
                          {selected.hermesQualify.facility_clarity
                            ? ` · facility ${selected.hermesQualify.facility_clarity}`
                            : ""}
                        </p>
                      )}
                      {selected.hermesQualify?.rationale && (
                        <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
                          {selected.hermesQualify.rationale}
                        </p>
                      )}
                      {(selected.hermesQualify?.vendor_shortlist || []).length > 0 && (
                        <ul className="mt-1.5 space-y-0.5 text-[11px] text-slate-700">
                          {(selected.hermesQualify?.vendor_shortlist || []).slice(0, 3).map((v, i) => (
                            <li key={`${v.vendor || "v"}-${i}`}>
                              <span className="font-medium">{v.vendor}</span>
                              {v.model ? ` · ${v.model}` : ""}
                              {v.why ? ` — ${v.why}` : ""}
                            </li>
                          ))}
                        </ul>
                      )}
                      {(selected.hermesQualify?.blockers || []).length > 0 && (
                        <p className="mt-1 text-[11px] text-amber-800">
                          Blockers: {(selected.hermesQualify?.blockers || []).join("; ")}
                        </p>
                      )}
                      {(selected.hermesJobTitles || []).length > 0 && (
                        <p className="mt-1.5 text-[11px] text-slate-700">
                          <span className="font-semibold text-slate-800">Open roles: </span>
                          {(selected.hermesJobTitles || []).slice(0, 3).join(" · ")}
                        </p>
                      )}
                      {(selected.hermesDecisionMakers || []).length > 0 && (
                        <ul className="mt-1.5 space-y-0.5 text-[11px] text-slate-700">
                          {(selected.hermesDecisionMakers || []).slice(0, 4).map((dm, i) => (
                            <li key={`${dm.name || "dm"}-${i}`}>
                              <span className="font-medium">{dm.name}</span>
                              {dm.title ? ` · ${dm.title}` : ""}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain flex flex-col">
                  {showFirstThreeActionsProgress && (
                    <div className="px-5 pt-3">
                      <FirstThreeActionsProgress
                        state={firstThreeActions}
                        onCopyDraft={copyDraft}
                        onPrimaryAction={runFirstThreePrimaryAction}
                        primaryActionLabel={firstThreePrimaryActionLabel}
                        primaryActionDisabled={firstThreePrimaryActionDisabled}
                        helperText={firstThreeHelperText}
                        onDismiss={() => setFirstThreeActions((prev) => ({ ...prev, dismissed: true }))}
                      />
                    </div>
                  )}
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

                  <div className="pipeline-detail-section-muted -mt-1">
                        {(() => {
                          const evidence = evidenceStackForDeal(selected);
                          const gapCount = evidence.missingByKey.size;
                          const summary = cleanAndClampText(
                            selected.leadHighlights?.specific_problem
                              || selected.shareSummary
                              || selected.notes
                              || "Buyer intent and workflow context are being summarized.",
                            170,
                          );
                          return (
                            <div className="rounded-xl border border-emerald-200/70 bg-gradient-to-br from-emerald-50 via-white to-emerald-50/70 p-2.5 shadow-[0_1px_0_rgba(16,185,129,0.06)]">
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-800">SIGNAL intelligence</p>
                                  <p className="mt-0.5 text-[11px] leading-snug text-slate-600">Buyer context first, operator controls second.</p>
                                </div>
                                <div className="flex flex-wrap items-center justify-end gap-1.5">
                                  {gapCount > 0 && (
                                    <span className="inline-flex items-center rounded-full border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-amber-800">
                                      {gapCount} gap{gapCount === 1 ? "" : "s"}
                                    </span>
                                  )}
                                  {evidence.researchState === "researching" && (
                                    <span className="inline-flex items-center rounded-full border border-emerald-300 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-emerald-800">
                                      AI researching gaps
                                    </span>
                                  )}
                                </div>
                              </div>
                              <p className="mt-2 text-[12px] leading-relaxed text-slate-700">{summary}</p>
                              {selected.pipelineAction && (
                                <div className="mt-2 rounded-lg border border-emerald-200/80 bg-white/85 px-2.5 py-2">
                                  <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700">Next action</p>
                                  <p className="mt-0.5 text-[11px] leading-relaxed text-emerald-900">
                                    {cleanAndClampText(selected.pipelineAction, 180)}
                                  </p>
                                </div>
                              )}
                            </div>
                          );
                        })()}

                        <div className="pt-1.5 space-y-2">
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
                                <PipelineLeadQualityPanel deal={selected} />
                            </ul>
                          )}

                          {/* CRM evidence — what the buyer actually cares about */}
                          {(() => {
                            const evidence = evidenceStackForDeal(selected);
                            const hasEvidence = Boolean(
                              evidence.frictionPoint
                              || evidence.workflowItems.length
                              || evidence.timingLabel
                              || evidence.robotLabel
                              || evidence.budgetTopAmount
                              || evidence.decisionMakers.length
                              || evidence.deploymentExamples.length,
                            );
                            if (!hasEvidence) return null;

                            const missingTag = (fieldKey: string) => {
                              const missing = evidence.missingByKey.get(fieldKey);
                              if (!missing) return null;
                              const state = String(missing.status || "empty").toLowerCase();
                              const label = state === "researching"
                                ? "Researching"
                                : state === "monitoring"
                                  ? "Monitoring"
                                  : "Missing";
                              const tone = state === "researching"
                                ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                                : state === "monitoring"
                                  ? "border-slate-300 bg-slate-100 text-slate-700"
                                  : "border-amber-300 bg-amber-50 text-amber-800";
                              return (
                                <span className={`ml-1.5 inline-flex items-center rounded-full border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${tone}`}>
                                  {label}
                                </span>
                              );
                            };

                            return (
                              <div className="pipeline-detail-section-muted">
                                <p className={panelSectionLabel}>
                                  Buyer evidence
                                  {evidence.researchState === "researching" ? (
                                    <span className="ml-2 inline-flex items-center rounded-full border border-emerald-300 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-emerald-800">
                                      AI researching gaps
                                    </span>
                                  ) : null}
                                </p>
                                <div className="mt-2 grid gap-2">
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Friction point{missingTag("friction_point")}</p>
                                    <p className="mt-1 text-[12px] leading-relaxed text-gray-800">
                                      {cleanAndClampText(evidence.frictionPoint || "Not yet summarized", 220)}
                                    </p>
                                  </div>
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Workflow scope{missingTag("workflow_scope")}</p>
                                    <p className="mt-1 text-[12px] leading-relaxed text-gray-800">
                                      <span className="font-semibold text-slate-900">{evidence.workflowLabel}:</span>{" "}
                                      {evidence.workflowItems.length > 0 ? cleanAndClampText(evidence.workflowItems.join(", "), 180) : "workflow not yet identified"}
                                    </p>
                                  </div>
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Timing and robot fit{missingTag("timing")}{missingTag("robot_type")}</p>
                                    <p className="mt-1 text-[12px] leading-relaxed text-gray-800">
                                      <span className="font-semibold text-slate-900">Timing:</span> {cleanAndClampText(evidence.timingLabel || "not yet clear", 80)}
                                      <span className="mx-1 text-gray-400">·</span>
                                      <span className="font-semibold text-slate-900">Robots:</span> {cleanAndClampText(evidence.robotLabel || "not yet clear", 80)}
                                    </p>
                                  </div>
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Budget{missingTag("budget")}</p>
                                    <p className="mt-1 text-[12px] leading-relaxed text-gray-800">
                                      {evidence.budgetTopAmount ? (
                                        <>
                                          <span className="font-semibold text-slate-900">{evidence.budgetTopAmount}</span> appears in the evidence set.
                                        </>
                                      ) : (
                                        "No public budget signal yet. Confirm range and budget owner on the first call."
                                      )}
                                    </p>
                                    {evidence.budgetSignals.length > 0 && (
                                      <ul className="mt-1.5 space-y-1 text-[11px] leading-relaxed text-gray-600">
                                        {evidence.budgetSignals.slice(0, 2).map((signal, index) => (
                                          <li key={index}>{cleanAndClampText(signal.context || signal.amount || "Budget mention", 160)}</li>
                                        ))}
                                      </ul>
                                    )}
                                  </div>
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Decision makers{missingTag("decision_makers")}</p>
                                    {evidence.decisionMakers.length > 0 ? (
                                      <ul className="mt-1 space-y-1 text-[12px] leading-relaxed text-gray-800">
                                        {evidence.decisionMakers.slice(0, 3).map((person, index) => (
                                          <li key={index}>
                                            <span className="font-semibold text-slate-900">{cleanAndClampText(person.name || "Unknown", 60)}</span>
                                            {person.title ? <span className="text-gray-500"> · {cleanAndClampText(person.title, 80)}</span> : null}
                                          </li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="mt-1 text-[12px] leading-relaxed text-gray-800">Decision owner not identified yet. Ask who signs off on operations automation.</p>
                                    )}
                                  </div>
                                  <div className="rounded-lg border border-slate-200 bg-white/80 p-2.5">
                                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Similar deployments{missingTag("similar_deployments")}</p>
                                    {evidence.deploymentExamples.length > 0 ? (
                                      <ul className="mt-1 space-y-2 text-[12px] leading-relaxed text-gray-800">
                                        {evidence.deploymentExamples.slice(0, 3).map((example, index) => (
                                          <li key={index} className="rounded-md bg-slate-50 px-2 py-1.5">
                                            <p className="font-semibold text-slate-900">{cleanAndClampText(example.title || "Deployment example", 120)}</p>
                                            <p className="text-[11px] text-gray-600">{cleanAndClampText(example.summary || "", 150)}</p>
                                          </li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="mt-1 text-[12px] leading-relaxed text-gray-800">No matched deployment example yet. SIGNAL will add one as new evidence is published.</p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                          {(selected.notes || selected.shareSummary) && (
                            <p className="break-words text-[12px] leading-relaxed text-gray-700">
                              {cleanAndClampText(
                                selected.notes || selected.shareSummary,
                                panelPlan === "anonymous" ? 240 : 360,
                              )}
                            </p>
                          )}
                          {!selected.leadHighlights?.specific_problem
                            && (selected.leadHighlights?.why_lead || []).length === 0
                            && !selected.notes
                            && !selected.shareSummary
                            && !selected.crmEvidence
                            && (
                              <p className="text-[11px] leading-relaxed text-gray-500">
                                SIGNAL is monitoring this account and will surface friction, workflow scope, timing, and robot fit as new evidence arrives.
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
                              Free workspace unlocks up to 15 leads, save up to 5 leads, and copy outreach drafts. Upgrade to Pro to unlock more leads and automate your sales pipeline.
                            </p>
                          )}
                        </div>
                    </div>

                  <PipelineRobotPriorityPanel deal={selected} />
                  <PipelineContactIntelligencePanel deal={selected} />

                  {selected && ["HOT", "WARM"].includes((selected.priorityTier || "").toUpperCase()) && (
                    <CalLeadDrop
                      drop={dealToCalDrop(selected)}
                      variant="compact"
                      showDraft={Boolean(session?.access_token)}
                      onMoveNow={
                        session?.access_token
                          ? () => void developLeadWithScout(selected)
                          : undefined
                      }
                      pipelineHref={`/pipeline?lead=${selected.id}`}
                    />
                  )}

                  {!session?.access_token && selected && (
                    <PipelineOutreachValuePanel
                      deal={selected}
                      hasSession={false}
                      copied={copied}
                      onCopy={copyDraft}
                    />
                  )}

                  <div className="pipeline-detail-section-muted">
                    <LeadShareBar panel lead={dealToShareLead(selected)} />
                  </div>

                  {/* Latest research — paid workspace */}
                  {showFullPanel && (
                  <div className="shrink-0 px-5 py-3 border-b border-gray-100">
                    <button
                      type="button"
                      onClick={() => setResearchOpen((open) => !open)}
                      className="w-full flex items-center gap-2 text-left rounded-lg py-1 transition-colors hover:bg-white"
                      aria-expanded={researchOpen}
                    >
                      <span className={panelSectionLabel}>Evidence stack</span>
                      {!researchOpen && (
                        <span className="flex-1 min-w-0 text-[11px] text-gray-500 truncate">
                          {(selected.researchUpdates || []).length > 0
                            ? `${(selected.researchUpdates || []).length} cited update(s)`
                            : "Monitoring for source-backed evidence"}
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
                          <p className="text-[11px] leading-relaxed text-gray-500">SIGNAL is loading cited evidence…</p>
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
                                <div className="mb-1.5 flex flex-wrap gap-1.5">
                                  {update.source_label && (
                                    <span className="rounded-full border border-amber-300/30 bg-amber-100/80 px-2 py-0.5 text-[10px] font-semibold text-amber-900">
                                      {update.source_label}
                                    </span>
                                  )}
                                  {(update.source_domain || update.source_kind) && (
                                    <span className="rounded-full border border-slate-300 bg-white/70 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                                      {update.source_domain || update.source_kind}
                                    </span>
                                  )}
                                  {update.evidence_tension && (
                                    <span className="rounded-full border border-emerald-300/40 bg-emerald-100/80 px-2 py-0.5 text-[10px] font-semibold text-emerald-900">
                                      {update.evidence_tension}
                                    </span>
                                  )}
                                </div>
                                <p className="break-words text-[11px] leading-relaxed text-gray-700">
                                  {cleanAndClampText(update.summary, 220)}
                                </p>
                                {update.recommended_action && (
                                  <p className="mt-1.5 break-words text-[11px] leading-relaxed text-slate-700">
                                    <span className="font-semibold text-slate-900">Next action: </span>
                                    {cleanAndClampText(update.recommended_action, 180)}
                                  </p>
                                )}
                                {update.source_url && (
                                  <a
                                    href={update.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="mt-1 inline-flex text-[10px] font-semibold text-amber-700 underline underline-offset-2 hover:text-amber-800"
                                  >
                                    Open source evidence
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[11px] leading-relaxed text-gray-500">
                            SIGNAL will add source-backed evidence when fresh news, LinkedIn posts, blog posts, and industry updates arrive.
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
                          <p className={panelSectionLabel}>Evidence stack</p>
                          <p className="text-[11px] leading-relaxed text-gray-600">
                            Pro unlocks cited evidence on HOT and WARM leads so reps can verify alignment quickly — budget, timing, source links, and recommended actions refreshed automatically.
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

                  {/* Outreach draft — primary send path lives here (CRM is advanced editor only) */}
                  {showKanban && session?.access_token && (
                  <div
                    ref={outreachDraftRef}
                    tabIndex={-1}
                    className={`shrink-0 scroll-mt-24 px-5 py-3 outline-none transition-all duration-500 ${outreachDraftSpotlight ? "rounded-2xl bg-emerald-100/90 ring-4 ring-emerald-400 shadow-[0_0_0_10px_rgba(16,185,129,0.18)]" : ""}`}
                  >
                    {outreachDraftSpotlight && (
                      <div className="mb-2 inline-flex items-center rounded-full border border-emerald-300 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-900 shadow-sm">
                        Draft ready below
                      </div>
                    )}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3.5 w-3.5" style={{ color: "#059669" }} />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                          Outreach draft
                        </p>
                      </div>
                      {isAdmin && (
                        <button
                          type="button"
                          onClick={() => openWorkspaceHref("/admin#cal-outreach", setLocation)}
                          className="text-[10px] font-semibold text-emerald-700 underline-offset-2 hover:underline"
                        >
                          SIGNAL bulk queue
                        </button>
                      )}
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

                    <div className="mb-2 rounded-lg border border-slate-200 bg-slate-50/80 p-2.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-700">Pre-send checklist</p>
                        <span className="rounded-full border border-slate-300 bg-white px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-600">
                          {sendChecklistVariantLabel}
                        </span>
                      </div>
                      {sendChecklistVariantAutoPromoted && (
                        <p className="mt-1 text-[10px] font-semibold text-emerald-700">
                          SIGNAL auto-promotion active for this variant.
                        </p>
                      )}
                      <p className="mt-1 text-[10px] text-slate-600">
                        {sendChecklistVariant === "a"
                          ? "Checklist order: contact, draft, send status."
                          : "Checklist order: send status first, then contact and draft."}
                      </p>
                      <div className="mt-1.5 grid gap-1 text-[10px] text-gray-700 md:grid-cols-3">
                        {sendChecklistItems.map((item) => (
                          <span
                            key={item.key}
                            className={item.ready ? "font-semibold text-emerald-700" : (item.key === "status" ? "text-slate-600" : "text-amber-800")}
                          >
                            {item.ready ? "✓" : "•"} {item.ready ? item.readyLabel : item.blockedLabel}
                          </span>
                        ))}
                      </div>
                    </div>

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
                          No draft yet. Run SIGNAL on this lead to refresh inference and generate outreach.
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

                    {selected.contact && selected.outreachBody && selected.stage !== "Outreach Sent" && session?.access_token && (
                      <button
                        type="button"
                        disabled={sendingLeadId === selected.id}
                        onClick={() => void sendOneLead(selected)}
                        className="mt-3 w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-[11px] font-bold border transition-all disabled:opacity-50"
                        style={{ background: "rgba(52,211,153,0.12)", borderColor: "rgba(52,211,153,0.35)", color: "#047857" }}
                      >
                        {sendingLeadId === selected.id
                          ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          : <Send className="h-3.5 w-3.5" />
                        }
                        {sendingLeadId === selected.id ? "Sending..." : `Send outreach to ${selected.contact}`}
                      </button>
                    )}
                    {!selected.contact && selected.outreachBody && (
                      <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50/70 p-2.5">
                        <p className="text-[10px] text-amber-900">
                          Add a contact email to send now. This removes the top step-3 blocker.
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <input
                            type="email"
                            value={capturedContactEmail}
                            onChange={(e) => setCapturedContactEmail(e.target.value)}
                            placeholder="name@company.com"
                            className="h-8 flex-1 rounded-md border border-amber-200 bg-white px-2 text-[11px] text-gray-800 outline-none ring-0 focus:border-emerald-400"
                          />
                          <button
                            type="button"
                            disabled={sendingLeadId === selected.id}
                            onClick={runContactAssistSend}
                            className="inline-flex h-8 items-center gap-1 rounded-md border border-emerald-300 bg-emerald-100 px-2.5 text-[10px] font-semibold text-emerald-800 disabled:opacity-60"
                          >
                            <Send className="h-3 w-3" />
                            {sendingLeadId === selected.id ? "Sending..." : "Send now"}
                          </button>
                        </div>
                      </div>
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
                          href={signupHrefForLead(selected.id, selected.company, { src: "pipeline_detail" })}
                          className="sb-btn sb-btn-primary"
                        >
                          Sign up free — save &amp; copy
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
                    {selected.contact && selected.outreachBody && selected.stage !== "Outreach Sent" && (
                      <button
                        type="button"
                        disabled={sendingLeadId === selected.id}
                        onClick={() => void sendOneLead(selected)}
                        className="sb-btn sb-btn-primary"
                      >
                        {sendingLeadId === selected.id ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : (
                          <Send className="h-3 w-3" />
                        )}
                        {sendingLeadId === selected.id ? "Sending…" : "Send outreach"}
                      </button>
                    )}
                    <button
                      onClick={copyDraft}
                      className="sb-btn"
                    >
                      <Copy className="h-3 w-3" />
                      Copy draft
                    </button>
                    {STAGES.indexOf(selected.stage) < STAGES.length - 1 && (
                      <button
                        onClick={() => void handleAdvanceLead(selected)}
                        disabled={advancingLeadId === selected.id}
                        className="sb-btn"
                      >
                        {advancingLeadId === selected.id ? "Advancing..." : "Next stage"}
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
                      : hasActiveSearch && displayedDeals.length === 0 && !serverSearchLoading
                      ? `No leads match "${activeSearchQuery}". Try food service, hospitality, logistics, or a company name.`
                      : isAdmin
                        ? isAdmin
                          ? "Select a deal to review signal detail and SIGNAL outreach"
                          : "Select a deal to review signal detail and outreach draft"
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
          <div className="border-t border-slate-200 px-3 py-3 sm:px-4">
            <div className="rounded-xl border-2 border-amber-400 bg-gradient-to-r from-amber-100 via-white to-emerald-100 px-4 py-3 shadow-[0_14px_28px_-16px_rgba(245,158,11,0.9)]">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="inline-flex items-center rounded-full border border-amber-300 bg-amber-200/70 px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.16em] text-amber-900">
                    Priority
                  </p>
                  <p className="mt-1 flex items-center gap-1.5 text-base font-extrabold text-emerald-900">
                    <Sparkles className="h-4 w-4 text-amber-600" />
                    Upgrade to Pro and begin building your sales campaign.
                  </p>
                </div>
                <Link
                  href="/pricing?upgrade=pro&src=pipeline_bottom_banner"
                  className="inline-flex items-center justify-center rounded-lg border-2 border-amber-500 bg-amber-400 px-4 py-2 text-sm font-extrabold text-amber-950 shadow-sm transition hover:bg-amber-300"
                >
                  Upgrade to Pro
                </Link>
              </div>
            </div>
          </div>
          </div>
          )}
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
                <p className="text-sm font-bold text-gray-900">{selected.company}</p>
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
              <p className="text-xs text-gray-600">[Your name] &lt;you@company.com&gt;</p>
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
      <FirstSaveGuideModal
        open={firstSaveGuideOpen}
        onOpenChange={setFirstSaveGuideOpen}
        deal={selected}
        saving={Boolean(selected && advancingLeadId === selected.id)}
        onDismiss={() => {
          markFirstSaveGuideSeen();
          setFirstSaveGuideOpen(false);
        }}
        onSave={() => {
          if (!selected) return;
          void handleSaveLead(selected).then((saved) => {
            if (!saved) return;
            markFirstSaveGuideSeen();
            setFirstSaveGuideOpen(false);
          });
        }}
      />
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
