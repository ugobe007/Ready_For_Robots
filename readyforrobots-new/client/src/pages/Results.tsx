/**
 * Results — ReadyForRobots
 * URL request → scan → matched prospect cards → SIGNAL activation.
 */
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Copy,
  FileText,
  LockKeyhole,
  MapPin,
  Shield,
  Users,
  Zap,
} from "lucide-react";
import { Link, useSearch } from "wouter";
import Header from "@/components/Header";
import ExperimentHeader from "@/components/ExperimentHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { useAuth } from "@/contexts/AuthContext";
import { OUTREACH_CTA, OUTREACH_SIGNATURE } from "@/lib/agentMessaging";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { getApiBase, getDirectApiBase, fetchWithTimeoutRetry, liveFetchInit } from "@/lib/apiBase";
import { trackUrlScan, readSupplyAttribution, trackSupplyConversion } from "@/lib/siteAnalytics";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";
import { cleanScrapedText } from "@/lib/text";
import { toast } from "sonner";
import LeadShareBar from "@/components/LeadShareBar";
import ResultsValueStrip from "@/components/results/ResultsValueStrip";
import { RESULTS_ANONYMOUS_UNLOCK } from "@/components/results/ResultsFomoBanner";
import ResultsNextStepCta from "@/components/results/ResultsNextStepCta";
import {
  OEM_CAL_RESULTS_HEAD_ANON,
  OEM_CAL_RESULTS_HEAD_SIGNED,
  oemCalResultsAnonLine,
} from "@/lib/oemCalCopy";
import { markReviewedFiveLeads } from "@/lib/signupWorkflowPath";
import { isJobsHandoffSrc, buyerLeadsHref, jobsSignupHref, persistJobsHandoffSrc, JOBS_SCAN_STEPS, JOBS_FOR_YOUR_ROBOT_CTA, JOBS_FOR_YOUR_ROBOT_HEADING, JOBS_FOR_YOUR_ROBOT_KEEP_CTA, JOBS_EXAMPLE_CAP } from "@/lib/jobsWorkflow";
import JobsHandoffBoard from "@/components/JobsHandoffBoard";

const SCAN_STEPS = [
  "Waiting for your robot or company URL…",
  "Using your URL as pipeline context…",
  "Loading pre-scored prospective sales leads…",
  "Matching fit, timing, and buying signals from the pipeline…",
  "Explaining why each lead is relevant…",
  "Preparing SIGNAL follow-up plans…",
];

type ApiLead = {
  id: number;
  company_name?: string;
  industry?: string | null;
  location_city?: string | null;
  location_state?: string | null;
  employee_estimate?: number | null;
  priority_tier?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
  share_summary?: string | null;
  robot_types_needed?: string[];
  score?: {
    overall_score?: number;
    lead_value_score?: number;
    signal_score?: number;
  };
  signals?: Array<{
    signal_type?: string;
    signal_label?: string;
    raw_text?: string;
    display_text?: string;
  }>;
  gtm?: {
    readiness_label?: string;
    why_now?: string[];
    suggested_motion?: string;
  };
  match_score?: number;
  value_proposition?: string;
  recommended_action?: string;
  key_signals?: string[];
  created_at?: string | null;
  hermes_job_titles?: string[];
  pipeline_action?: string | null;
  cal_seller_brief?: {
    headline?: string;
    why_now?: string;
    pitch?: string;
    robot_fit?: string;
    next_step?: string;
  } | null;
};

type RobotReadyResponse = {
  robot_name?: string;
  submitted_url?: string;
  robot_capabilities?: {
    type?: string;
    use_case?: string;
    capabilities?: string[];
    profile_score?: number;
  };
  matched_companies?: ApiLead[];
  overall_strategy?: string;
  estimated_deal_value?: number;
  top_industry?: string;
  total_leads?: number;
};

type SellerBrief = {
  headline: string;
  whyNow: string;
  pitch: string;
  robotFit: string;
  nextStep: string;
};

type Prospect = {
  id: string;
  company: string;
  location: string;
  industry: string;
  employees: string;
  score: number;
  signal: string;
  signalType: string;
  signalColor: string;
  timing: string;
  action: string;
  relevance: string;
  scoreReason: string;
  draft: string;
  outreachSubject: string;
  outreachBody: string;
  sellerBrief: SellerBrief;
  stage: string;
  leadId?: number;
  shareSummary?: string;
  priorityTier?: string;
  robotTypes?: string[];
  signalAge?: string;
};

function scoreColor(score: number): string {
  return score >= 90 ? "#34d399" : score >= 75 ? "#10b981" : "#FFB000";
}

function timingFromScore(score: number): string {
  if (score >= 90) return "Decision window: Now";
  if (score >= 75) return "Decision window: 1-3 months";
  return "Decision window: 3-6 months";
}

function buildOutreachFields(p: Pick<Prospect, "company" | "signal" | "relevance" | "action">) {
  const hook = p.action
    ? `I've been following ${p.company} — ${p.action.charAt(0).toLowerCase()}${p.action.slice(1)}`
    : `${p.company} stood out because ${p.relevance.toLowerCase()} The strongest signal: ${p.signal}`;

  const outreachSubject = `Automation opportunity at ${p.company}`;
  const outreachBody = `Hey,\n\n${hook}\n\n${OUTREACH_CTA}\n\n${OUTREACH_SIGNATURE}`;
  const draft = `Subject: ${outreachSubject}\n\n${outreachBody}`;
  return { outreachSubject, outreachBody, draft };
}

function buildSellerBrief(
  company: string,
  opts: {
    fromApi?: ApiLead["cal_seller_brief"];
    relevance: string;
    action: string;
    signal: string;
    robotTypes?: string[];
    hermesJobs?: string[];
  },
): SellerBrief {
  const api = opts.fromApi;
  const robots = (opts.robotTypes || []).map((r) => String(r).trim()).filter(Boolean).slice(0, 3);
  const robotFit = api?.robot_fit || robots.join(", ") || "the robot class you sell";
  if (api?.headline && api?.why_now) {
    return {
      headline: api.headline,
      whyNow: api.why_now,
      pitch: api.pitch || opts.action,
      robotFit,
      nextStep: api.next_step || `Save ${company} → copy Cal's brief → start the conversation`,
    };
  }
  const hermesJob = (opts.hermesJobs || []).find((t) => (t || "").trim())?.trim();
  const whyNow = hermesJob
    ? `${company} is hiring for ${hermesJob} — timing that usually means operational load is already rising.`
    : opts.relevance || opts.signal;
  return {
    headline: `Why ${company} is a fit for your robot`,
    whyNow,
    pitch: opts.action || `Lead with how ${robotFit} removes a concrete workflow bottleneck — not a generic automation pitch.`,
    robotFit,
    nextStep: `Save ${company} → copy Cal's brief → start the conversation`,
  };
}

function buildRfqSpecPacket(p: Pick<Prospect, "company" | "industry" | "action" | "signal">) {
  const subject = `RFQ or bid-project request for ${p.company}`;
  const body = [
    "Hi,",
    "",
    `I'm reaching out because ${p.company} surfaced with an active automation signal in ${p.industry}.`,
    `Context: ${p.signal}`,
    "",
    "Are you currently preparing RFQs or bid projects for the robot workflows you are evaluating?",
    "If yes, could you share the requirements (robot type, throughput, payload, site constraints, integration requirements, timeline, and budget band)?",
    "",
    "If it helps, I can send a short RFQ and bid-project checklist your team can edit quickly.",
    "",
    "Best,",
    "[Your name]",
    "",
    "---",
    `Internal handoff note: Route this lead to Robert after RFQ/bid-project details are received. Suggested next step: ${p.action}`,
  ].join("\n");

  return `Subject: ${subject}\n\n${body}`;
}

function formatEmployees(value: number | null | undefined): string {
  if (!value || value <= 0) return "Unknown";
  return new Intl.NumberFormat("en-US").format(value);
}

function titleize(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function cleanRelevanceCopy(raw: string, quotedSignal: string): string {
  const cleaned = cleanScrapedText(raw);
  return cleaned
    .replace(/\bKey evidence\s*[-:]\s*[^.]+(?:\.\s*|$)/gi, "")
    .replace(quotedSignal, "")
    .replace(/\s+/g, " ")
    .trim();
}

function formatSignalAge(iso?: string | null): string | undefined {
  if (!iso) return undefined;
  const parsed = Date.parse(iso);
  if (Number.isNaN(parsed)) return undefined;
  const days = Math.floor((Date.now() - parsed) / 86_400_000);
  if (days <= 0) return "Signal today";
  if (days === 1) return "Signal 1d ago";
  if (days < 14) return `Signal ${days}d ago`;
  if (days < 60) return `Signal ${Math.floor(days / 7)}w ago`;
  return `Signal ${Math.floor(days / 30)}mo ago`;
}

function clampResultsLimit(raw: string | null): number {
  const parsed = Number(raw || "");
  if (!Number.isFinite(parsed) || parsed <= 0) return 5;
  return Math.max(1, Math.min(15, Math.round(parsed)));
}

function mapApiLead(lead: ApiLead, index: number): Prospect {
  const score = Math.round(
    lead.match_score ??
      lead.score?.lead_value_score ??
      lead.score?.overall_score ??
      lead.priority_score ??
      70,
  );
  const firstSignal = lead.signals?.[0];
  const signal = cleanScrapedText(firstSignal?.display_text || firstSignal?.raw_text || lead.key_signals?.[0] || lead.share_summary || "") || "SIGNAL found a sales-fit pattern worth reviewing.";
  const signalType = firstSignal?.signal_label || titleize(firstSignal?.signal_type || "buying_signal");
  const companyRaw = (lead.company_name || "").trim();
  const company =
    companyRaw.toLowerCase() === "cheese"
      ? "Santori Cheese"
      : companyRaw || `Matched Lead ${index + 1}`;
  const stage = lead.priority_tier ? `${lead.priority_tier} Lead` : score >= 85 ? "Draft Ready" : "New Signal";
  const whyNow = lead.gtm?.why_now?.filter(Boolean) || [];
  const relevance =
    cleanScrapedText(lead.share_summary || "") ||
    cleanRelevanceCopy(lead.value_proposition || whyNow.join(" "), signal) ||
    `${company} is looking for automation based on active buying signals in our feed.`;
  const scoreReason = [
    `${score}/100 match score`,
    lead.priority_tier ? `${lead.priority_tier} priority` : "qualified lead",
    lead.match_score ? "matched to scanned URL profile" : "",
    ...(lead.priority_reasons || whyNow).slice(0, 2),
  ].filter(Boolean).join(" · ");
  const prospect = {
    id: String(lead.id ?? `${company}-${index}`),
    company,
    location: [lead.location_city, lead.location_state].filter(Boolean).join(", ") || "Location unknown",
    industry: lead.industry || "Industry unknown",
    employees: formatEmployees(lead.employee_estimate),
    score,
    signal,
    signalType,
    signalColor: scoreColor(score),
    timing: lead.gtm?.readiness_label ? `Stage: ${lead.gtm.readiness_label}` : timingFromScore(score),
    action: lead.pipeline_action || lead.recommended_action || lead.gtm?.suggested_motion || "Reach out with a personalized automation use case",
    relevance,
    scoreReason,
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    sellerBrief: {
      headline: "",
      whyNow: "",
      pitch: "",
      robotFit: "",
      nextStep: "",
    },
    stage,
    leadId: typeof lead.id === "number" ? lead.id : undefined,
    shareSummary: lead.share_summary || undefined,
    priorityTier: lead.priority_tier || undefined,
    robotTypes: lead.robot_types_needed,
    signalAge: formatSignalAge(lead.created_at),
  };
  prospect.sellerBrief = buildSellerBrief(company, {
    fromApi: lead.cal_seller_brief,
    relevance: prospect.relevance,
    action: prospect.action,
    signal: prospect.signal,
    robotTypes: lead.robot_types_needed,
    hermesJobs: lead.hermes_job_titles,
  });
  const outreach = buildOutreachFields(prospect);
  prospect.outreachSubject = outreach.outreachSubject;
  prospect.outreachBody = outreach.outreachBody;
  prospect.draft = outreach.draft;
  return prospect;
}

type ScoutProspectRow = {
  id?: string;
  company?: string;
  industry?: string;
  location?: string;
  score?: number;
  tier?: string;
  signal?: string;
  signalType?: string;
  timing?: string;
  action?: string;
  relevance?: string;
  match_score?: number;
};

function mapScoutProspect(row: ScoutProspectRow, index: number): Prospect {
  const score = Math.round(row.match_score ?? row.score ?? 70);
  const company = row.company || `Matched Lead ${index + 1}`;
  const signal = cleanScrapedText(row.signal || "") || "SIGNAL matched this account to your URL profile.";
  const signalType = titleize((row.signalType || "buying_signal").replace(/_/g, " "));
  const prospect: Prospect = {
    id: String(row.id ?? `${company}-${index}`),
    company,
    location: row.location || "Location unknown",
    industry: row.industry || "Industry unknown",
    employees: "—",
    score,
    signal,
    signalType,
    signalColor: scoreColor(score),
    timing: row.timing || timingFromScore(score),
    action: row.action || "Reach out with a personalized automation use case",
    relevance: cleanScrapedText(row.relevance || "") || `${company} shows active buying signals in the ReadyForRobots pipeline.`,
    scoreReason: [
      `${score}/100 match score`,
      row.tier ? `${row.tier} priority` : "",
      "matched via SIGNAL scan-for-results",
    ].filter(Boolean).join(" · "),
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    sellerBrief: {
      headline: "",
      whyNow: "",
      pitch: "",
      robotFit: "",
      nextStep: "",
    },
    stage: row.tier ? `${row.tier} Lead` : score >= 85 ? "Draft Ready" : "New Signal",
    leadId: row.id && /^\d+$/.test(String(row.id)) ? Number(row.id) : undefined,
    priorityTier: row.tier,
  };
  prospect.sellerBrief = buildSellerBrief(company, {
    relevance: prospect.relevance,
    action: prospect.action,
    signal: prospect.signal,
  });
  const outreach = buildOutreachFields(prospect);
  prospect.outreachSubject = outreach.outreachSubject;
  prospect.outreachBody = outreach.outreachBody;
  prospect.draft = outreach.draft;
  return prospect;
}

const fallbackProspects: Prospect[] = [
  {
    id: "silver-peak",
    company: "Silver Peak Hospitality Group",
    location: "Phoenix, AZ",
    industry: "Hospitality",
    employees: "2,400",
    score: 94,
    signal: "Earnings call: 40% housekeeping vacancy and difficulty staffing overnight shifts.",
    signalType: "Labor shortage",
    signalColor: "#34d399",
    timing: "Decision window: Now",
    action: "Reach out with overnight automation case study",
    relevance: "Hospitality labor pressure maps directly to service and cleaning automation, and the staffing gap is urgent enough for immediate outreach.",
    scoreReason: "94/100 match score · labor pain · urgent timing · high operational fit",
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    stage: "HOT Lead",
  },
  {
    id: "desertline",
    company: "DesertLine Logistics",
    location: "Las Vegas, NV",
    industry: "Logistics",
    employees: "1,800",
    score: 88,
    signal: "Hiring an Automation Engineer while opening two new distribution centers.",
    signalType: "Expansion signal",
    signalColor: "#10b981",
    timing: "Decision window: 1-3 months",
    action: "Contact during facility design phase",
    relevance: "New facilities plus an automation hire indicate budget, ownership, and a near-term design window for robotics decisions.",
    scoreReason: "88/100 match score · expansion · automation owner identified · strong timing",
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    stage: "WARM Lead",
  },
  {
    id: "apex",
    company: "Apex Manufacturing Co.",
    location: "Tucson, AZ",
    industry: "Manufacturing",
    employees: "950",
    score: 79,
    signal: "Recent repetitive strain filings plus a new process improvement manager role.",
    signalType: "Safety signal",
    signalColor: "#FFB000",
    timing: "Decision window: 3-6 months",
    action: "Lead with safety ROI and ergonomics case",
    relevance: "Safety incidents and process improvement hiring create a clear reason to discuss automation for repetitive workflows.",
    scoreReason: "79/100 match score · safety pain · process owner hiring · moderate timing",
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    stage: "Review Lead",
  },
].map((p) => {
  const outreach = buildOutreachFields(p);
  const sellerBrief = buildSellerBrief(p.company, {
    relevance: p.relevance,
    action: p.action,
    signal: p.signal,
  });
  return { ...p, ...outreach, sellerBrief };
});

function fallbackProspectsForLimit(limit: number): Prospect[] {
  if (limit <= fallbackProspects.length) return fallbackProspects.slice(0, limit);
  return Array.from({ length: limit }, (_, index) => {
    const base = fallbackProspects[index % fallbackProspects.length];
    const pass = Math.floor(index / fallbackProspects.length);
    if (pass === 0) return base;
    return {
      ...base,
      id: `${base.id}-sample-${pass + 1}`,
      company: `${base.company} ${pass + 1}`,
      stage: base.stage.includes("Lead") ? base.stage : `${base.stage} Lead`,
    };
  });
}

export default function Results() {
  const search = useSearch();
  const params = new URLSearchParams(search);
  const initialUrl = params.get("url")?.trim() || "";
  const urlLimit = clampResultsLimit(params.get("limit"));
  const sampleMode = params.get("sample") === "1";
  const sampleName = (params.get("sample_name") || "").trim();
  const { session, loading: authLoading } = useAuth();
  const jobsHandoff = isJobsHandoffSrc(params.get("src"));
  const jobsSrc = persistJobsHandoffSrc(params.get("src"));
  const scanSteps = jobsHandoff ? JOBS_SCAN_STEPS : SCAN_STEPS;
  // Results is the 5-job preview on the Jobs path. More than 5 lives only on /pipeline.
  const requestedLimit = Math.min(urlLimit, 5);

  useEffect(() => {
    const attribution = readSupplyAttribution(search);
    if (!attribution.utmSource && !attribution.robotCompanyId) return;
    trackSupplyConversion({
      page: "results",
      utm_source: attribution.utmSource,
      rc: attribution.robotCompanyId,
      msg: attribution.messageToken,
      referrer: typeof document !== "undefined" ? document.referrer || null : null,
    });
  }, [search]);

  const [urlInput, setUrlInput] = useState(initialUrl);
  const [submittedUrl, setSubmittedUrl] = useState(initialUrl);
  const [scanStep, setScanStep] = useState(initialUrl ? 1 : 0);
  const [scanning, setScanning] = useState(Boolean(initialUrl));
  const [loading, setLoading] = useState(Boolean(initialUrl));
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activatedIds, setActivatedIds] = useState<Set<string>>(new Set());
  const [usingFallback, setUsingFallback] = useState(false);
  const [activationId, setActivationId] = useState<number | null>(null);
  const [sampleAccessLoading, setSampleAccessLoading] = useState(sampleMode);
  const [sampleAccessAllowed, setSampleAccessAllowed] = useState(!sampleMode);
  const [sampleAccessEmail, setSampleAccessEmail] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function verifySampleAccess() {
      if (!sampleMode) {
        if (!cancelled) {
          setSampleAccessAllowed(true);
          setSampleAccessLoading(false);
        }
        return;
      }
      if (authLoading) return;
      if (!session?.access_token) {
        if (!cancelled) {
          setSampleAccessAllowed(false);
          setSampleAccessLoading(false);
        }
        return;
      }
      setSampleAccessLoading(true);
      try {
        const token = await getFreshAccessToken(session.access_token);
        const meRes = await fetch(`${getApiBase()}/api/user/me`, liveFetchInit({ headers: authHeader(token) }));
        if (!meRes.ok) throw new Error(`user/me ${meRes.status}`);
        const me = await meRes.json() as { email?: string; is_admin?: boolean };
        if (!cancelled) {
          setSampleAccessEmail(me.email || "");
          setSampleAccessAllowed(Boolean(me.is_admin));
        }
      } catch {
        if (!cancelled) setSampleAccessAllowed(false);
      } finally {
        if (!cancelled) setSampleAccessLoading(false);
      }
    }
    void verifySampleAccess();
    return () => {
      cancelled = true;
    };
  }, [authLoading, sampleMode, session?.access_token]);

  const activatedCount = activatedIds.size;
  const isSignedIn = Boolean(session);
  const sortedProspects = useMemo(
    () => [...prospects].sort((a, b) => b.score - a.score),
    [prospects],
  );
  const anonymousUnlockedCount = Math.min(
    jobsHandoff ? requestedLimit : RESULTS_ANONYMOUS_UNLOCK,
    sortedProspects.length,
  );
  const topLeadId = sortedProspects[0]?.leadId;

  const resultsPageHref = useMemo(() => {
    const next = new URLSearchParams();
    if (submittedUrl) next.set("url", submittedUrl);
    next.set("limit", String(requestedLimit));
    next.set("src", "signup_return_results");
    return `/results?${next.toString()}`;
  }, [requestedLimit, submittedUrl]);

  const fullPipelineHref = useMemo(() => {
    if (jobsHandoff) {
      return buyerLeadsHref({
        robotUrl: submittedUrl,
        signedIn: true,
        src: jobsSrc,
        leadId: topLeadId,
      });
    }
    const q = new URLSearchParams();
    q.set("src", "results_scan");
    if (submittedUrl) q.set("url", submittedUrl);
    if (topLeadId != null) q.set("lead", String(topLeadId));
    return `/pipeline?${q.toString()}`;
  }, [jobsHandoff, jobsSrc, submittedUrl, topLeadId]);

  const resultsSignupHref = jobsHandoff
    ? jobsSignupHref(fullPipelineHref, jobsSrc)
    : `/signup?next=${encodeURIComponent(fullPipelineHref)}&src=results_gate`;

  // Anonymous users can review 5 leads here. Signup then opens the 15-lead pipeline.

  const copyRfqPacket = (prospect: Prospect) => {
    const packet = buildRfqSpecPacket(prospect);
    void navigator.clipboard.writeText(packet).then(() => {
      toast.success("RFQ/bid-project request packet copied");
    });
  };

  useEffect(() => {
    if (jobsHandoff) return;
    if (sampleMode && (sampleAccessLoading || !sampleAccessAllowed)) return;
    if (!submittedUrl) return;
    trackUrlScan(submittedUrl, "results");
    setScanStep(1);
    setScanning(true);
    setLoading(true);
    setProspects([]);
    setSelectedIds(new Set());
    setActivatedIds(new Set());
    setActivationId(null);
    setUsingFallback(false);

    let cancelled = false;
    let finished = false;
    let hardDeadline = 0;
    const stepTimer = window.setInterval(() => {
      setScanStep((current) => Math.min(current + 1, scanSteps.length - 1));
    }, 650);

    const finishScan = (mapped: Prospect[], usedFallback: boolean) => {
      if (cancelled || finished) return;
      finished = true;
      window.clearInterval(stepTimer);
      if (hardDeadline) window.clearTimeout(hardDeadline);
      setScanStep(scanSteps.length - 1);
      setProspects(mapped);
      setUsingFallback(usedFallback);
      // Gate Pipeline step 4/5 — signup must not jump past this 5-lead review.
      markReviewedFiveLeads();
      if (usedFallback) {
        toast.info(
          jobsHandoff
            ? "Could not reach the matcher in time — showing sample jobs while the API recovers."
            : "SIGNAL could not reach the matcher in time — showing sample leads while the API recovers.",
        );
      }
      window.setTimeout(() => {
        if (!cancelled) {
          setLoading(false);
          setScanning(false);
        }
      }, 350);
    };

    async function runScan() {
      const apiBase = getDirectApiBase();
      try {
        // Fast path: same matcher Pipeline uses (avoids slow scout/robot-ready scrape).
        const matchRes = await fetchWithTimeoutRetry(
          `${apiBase}/api/leads/match-url?url=${encodeURIComponent(submittedUrl)}&limit=${requestedLimit}`,
          liveFetchInit(
            session?.access_token ? { headers: authHeader(session.access_token) } : {},
          ),
          12_000,
          { retries: 0 },
        );
        if (matchRes.ok) {
          const matchData = (await matchRes.json()) as { leads?: ApiLead[] };
          const rows = Array.isArray(matchData.leads) ? matchData.leads : [];
          const mapped = rows.slice(0, requestedLimit).map(mapApiLead);
          if (mapped.length) {
            finishScan(mapped, false);
            return;
          }
        }

        const host = (() => {
          try {
            return new URL(submittedUrl).hostname.replace(/^www\./, "");
          } catch {
            return "prospect";
          }
        })();
        const scoutRes = await fetchWithTimeoutRetry(
          `${apiBase}/api/scout/scan-for-results`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              company_url: submittedUrl,
              fingerprint: scoutFingerprint(),
              robot_name: host,
              limit: requestedLimit,
            }),
          },
          10_000,
          { retries: 0 },
        );
        if (scoutRes.ok) {
          const scoutData = (await scoutRes.json()) as { prospects?: ScoutProspectRow[] };
          const rows = Array.isArray(scoutData.prospects) ? scoutData.prospects : [];
          const mapped = rows.map(mapScoutProspect);
          if (mapped.length) {
            finishScan(mapped, false);
            return;
          }
        }
        throw new Error(`Scan failed with ${scoutRes.status}`);
      } catch (error) {
        console.error(error);
        finishScan(fallbackProspectsForLimit(requestedLimit), true);
      }
    }

    // Hard wall-clock: never leave the scan spinner spinning.
    hardDeadline = window.setTimeout(() => {
      finishScan(fallbackProspectsForLimit(requestedLimit), true);
    }, 16_000);

    void runScan();
    return () => {
      cancelled = true;
      window.clearInterval(stepTimer);
      if (hardDeadline) window.clearTimeout(hardDeadline);
    };
  }, [jobsHandoff, requestedLimit, sampleAccessAllowed, sampleAccessLoading, sampleMode, scanSteps.length, session?.access_token, submittedUrl]);

  useEffect(() => {
    setSelectedIds(new Set(prospects.map((p) => p.id)));
  }, [prospects]);

  function submitUrl(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const normalized = normalizeUrl(urlInput);
    if (!normalized) {
      toast.error("Enter a URL first.");
      return;
    }
    setSubmittedUrl(normalized);
    window.history.replaceState(null, "", `/results?url=${encodeURIComponent(normalized)}`);
  }

  function toggleSelected(id: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (sampleMode && (authLoading || sampleAccessLoading)) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Header />
        <main className="mx-auto max-w-4xl px-6 pt-28 text-center text-gray-500">Checking admin access...</main>
      </div>
    );
  }

  if (sampleMode && !session) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <Shield className="mx-auto mb-4 h-7 w-7 text-amber-500" />
          <h1 className="text-2xl font-bold text-gray-900">Admin sign in required</h1>
          <p className="mt-3 text-sm text-gray-600">Sample pipeline links are private to admin accounts.</p>
          <Link href={`/login?next=${encodeURIComponent(`/results?${params.toString()}`)}`} className="mt-6 inline-flex rounded-xl border border-amber-500 px-5 py-3 text-sm font-bold text-amber-600">
            Sign in
          </Link>
        </main>
      </div>
    );
  }

  if (sampleMode && !sampleAccessAllowed) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center">
          <AlertTriangle className="mx-auto mb-4 h-7 w-7 text-red-400" />
          <h1 className="text-2xl font-bold text-gray-900">Admin access required</h1>
          <p className="mt-3 text-sm text-gray-600">
            {sampleAccessEmail || "This account"} is signed in but not in ADMIN_EMAILS.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <Link href="/admin" className="inline-flex rounded-xl border border-gray-300 px-5 py-3 text-sm font-bold text-gray-700">
              Open admin
            </Link>
            <Link href="/pipeline" className="inline-flex rounded-xl border border-amber-500 px-5 py-3 text-sm font-bold text-amber-600">
              Back to pipeline
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (jobsHandoff && submittedUrl) {
    return (
      <div className="flex min-h-screen flex-col bg-[#081126] pt-[44px]">
        <ExperimentHeader />
        <JobsHandoffBoard
          robotUrl={submittedUrl}
          cap={JOBS_EXAMPLE_CAP}
          src={jobsSrc}
          signedIn={isSignedIn}
          variant="results"
        />
      </div>
    );
  }

  // SIGNAL path can ask for signup first. Jobs handoff must show the 5
  // jobs — signup is the next step after those 5, not a wall before them.
  if (
    !sampleMode &&
    !jobsHandoff &&
    submittedUrl &&
    (authLoading || !session?.access_token)
  ) {
    return (
      <div className="min-h-screen flex flex-col bg-[#081126]">
        <Header />
        <main className="mx-auto max-w-xl px-6 pt-28 text-center text-slate-300">
          <p className="text-sm font-semibold text-white">
            {authLoading ? "Checking your workspace…" : "Sign up to see your matched sales leads…"}
          </p>
          {!authLoading && (
            <Link
              href={resultsSignupHref}
              className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950"
            >
              Continue to sign up
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col bg-[#081126] ${jobsHandoff ? "pt-[44px]" : ""}`}>
      {jobsHandoff ? <ExperimentHeader /> : <Header />}

      {submittedUrl && jobsHandoff ? (
        <div className="border-b border-slate-700 bg-[#081126] px-4 py-6 sm:px-6">
          <div className="mx-auto max-w-4xl">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400">
              {JOBS_FOR_YOUR_ROBOT_HEADING}
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold text-slate-100 sm:text-3xl">
              {JOBS_FOR_YOUR_ROBOT_HEADING}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Same Jobs terminal. 5 jobs to review. More than 5 jobs live after you sign up.
            </p>
          </div>
        </div>
      ) : !submittedUrl ? (
        <>
          <PageHeroDark
            maxWidthClass="max-w-4xl"
            eyebrow="Activate SIGNAL"
            title="Give SIGNAL a URL first."
            description="Paste your robot, company, or product URL. SIGNAL will scan it, match prospective sales leads, explain why each one is relevant, and score the opportunity."
            innerClassName="pb-10"
          />
          <div className="page-hero-fade" aria-hidden />
        </>
      ) : (
        <>
          <PageHeroDark
            maxWidthClass="max-w-4xl"
            badge={<div className="page-hero-badge">Scan complete · matched buyers ready</div>}
            eyebrow="SIGNAL results"
            title={scanning ? "Scanning for aligned buyers…" : sampleMode ? `Your ${requestedLimit}-company sample pipeline` : "Your qualified, aligned buyers"}
            description={
              submittedUrl
                ? sampleMode
                  ? `Sample pipeline for ${sampleName || submittedUrl} · ${requestedLimit} companies you can share with prospects.`
                  : `Results for ${submittedUrl} — review qualified buyers, prepare outreach, and move the strongest matches into your pipeline.`
                : undefined
            }
            innerClassName="pb-8"
          />
          <div className="page-hero-fade" aria-hidden />
        </>
      )}

      <main className="flex-1 pb-16 sm:pb-20 px-4 sm:px-6 text-slate-100">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-6 sm:mb-8">
            <Link href="/" className="hover:text-slate-200 transition-colors">Home</Link>
            <span>/</span>
            <span className="text-slate-500">{submittedUrl ? `Results for ${submittedUrl}` : "Activate SIGNAL"}</span>
          </div>

          {!submittedUrl && (
            <section className="py-4 sm:py-8">
              <div className="rounded-3xl border border-white/10 bg-[#0b162f] p-6 sm:p-10 shadow-[0_20px_45px_-30px_rgba(0,0,0,0.8)]">
                <form onSubmit={submitUrl} className="flex flex-col sm:flex-row gap-3">
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://your-robot-company.com/product"
                    className="min-w-0 flex-1 rounded-xl border border-white/15 bg-[#081126] px-4 py-3 text-base sm:text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/20"
                  />
                  <button
                    type="submit"
                    className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-amber-500 bg-amber-500 px-5 py-3 text-sm font-bold text-gray-900 transition-all hover:bg-amber-400 hover:border-amber-400"
                  >
                    Scan URL <Zap className="h-4 w-4" />
                  </button>
                </form>
              </div>
            </section>
          )}

          {submittedUrl && scanning && (
            <div className="flex flex-col items-center justify-center py-24 gap-8">
              <div className="relative h-20 w-20">
                <div className="absolute inset-0 rounded-full border-2 border-amber-400/20 animate-ping" style={{ animationDuration: "1.5s" }} />
                <div className="absolute inset-2 rounded-full border-2 border-amber-400/45 animate-spin" style={{ animationDuration: "2s" }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="h-6 w-6" style={{ color: "#FFB000" }} />
                </div>
              </div>

              <div className="w-full max-w-sm space-y-2">
                {scanSteps.slice(0, scanStep + 1).map((step, i) => {
                  const done = i < scanStep;
                  const active = i === scanStep;
                  return (
                  <div key={step} className="flex items-center gap-3 text-sm">
                    {done ? (
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-300" />
                    ) : (
                      <div className={`h-3.5 w-3.5 rounded-full border shrink-0 ${active ? "border-amber-400 animate-pulse" : "border-slate-600"}`} />
                    )}
                    <span
                      className={`font-mono text-xs font-medium ${active ? "text-amber-300" : done ? "text-emerald-300" : "text-slate-500"}`}
                      style={{ fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {step}
                    </span>
                  </div>
                  );
                })}
              </div>
            </div>
          )}

          {submittedUrl && !loading && !scanning && (
            <>
              {sampleMode && typeof window !== "undefined" && (
                <div className="mb-4 flex flex-col gap-2 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100 sm:flex-row sm:items-center sm:justify-between">
                  <p>
                    Share-ready sample pipeline: <span className="font-semibold">{requestedLimit} companies</span>
                    {sampleName ? <span> for <span className="font-semibold">{sampleName}</span></span> : null}
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      void navigator.clipboard.writeText(window.location.href).then(() => {
                        toast.success("Sample pipeline link copied");
                      });
                    }}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-400/40 bg-[#081126]/60 px-3 py-1.5 text-xs font-semibold text-emerald-200 hover:bg-emerald-400/15"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Copy link
                  </button>
                </div>
              )}

              {!jobsHandoff ? (
              <div className="mb-3 border border-amber-400/50 bg-transparent px-2.5 py-2">
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-300">
                  {isSignedIn ? "Step 3 of 5 · 5 sales leads" : "Step 2 of 5 · Sign up for 5 sales leads"}
                  {sortedProspects.length > 0 ? (
                    <>
                      {" · "}
                      <span className="text-emerald-300">
                        {sortedProspects.length} buyers
                        {sortedProspects.filter((p) => p.priorityTier === "HOT" || (p.stage || "").toUpperCase().includes("HOT")).length > 0
                          ? ` · ${sortedProspects.filter((p) => p.priorityTier === "HOT" || (p.stage || "").toUpperCase().includes("HOT")).length} HOT`
                          : ""}
                      </span>
                    </>
                  ) : null}
                </p>
                <p className="mt-0.5 text-sm font-semibold text-white">
                  {isSignedIn ? OEM_CAL_RESULTS_HEAD_SIGNED : OEM_CAL_RESULTS_HEAD_ANON}
                </p>
                <p className="mt-0.5 text-[11px] text-emerald-200/90">
                  {isSignedIn
                    ? "Cal matched these buyers to your robot URL — add company details next to unlock 15."
                    : oemCalResultsAnonLine(sortedProspects.length)}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-400">
                  <span className="break-all text-slate-300">{submittedUrl}</span>
                  {usingFallback ? " · sample mode" : ""}
                  {" · "}
                  Use Cal · OEM next step below when ready.
                </p>
                {!isSignedIn && (
                  <p className="mt-1 text-[11px] text-slate-500">
                    Free signup keeps these matches in your workspace, then Pipeline.
                  </p>
                )}
              </div>
              ) : null}

              {!isSignedIn && !jobsHandoff && (
                <ResultsValueStrip
                  leadCount={sortedProspects.length}
                  scanUrl={submittedUrl}
                  unlockedCount={anonymousUnlockedCount}
                />
              )}

              {activatedCount > 0 && (
                <div className="mb-5 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-5">
                  <p className="text-sm font-bold text-emerald-100 mb-1">SIGNAL review queue created</p>
                  <p className="text-xs text-slate-300">
                    {activationId ? `Activation #${activationId}: ` : ""}
                    Leads were saved to CRM. Review SIGNAL&apos;s workflow, draft outreach, timing, and cadence before any outbound action begins.
                  </p>
                </div>
              )}

              <div className="space-y-2">
                {sortedProspects.map((p, index) => {
                  const isSelected = selectedIds.has(p.id);
                  const isActive = activatedIds.has(p.id);
                  const isLocked = !isSignedIn && index >= anonymousUnlockedCount;
                  return (
                    <div
                      key={p.id}
                      className={`rounded-lg border bg-transparent overflow-hidden transition-colors ${
                        isLocked ? "border-sky-400/40 hover:border-sky-400/60" : "border-white/20 hover:border-emerald-400/50"
                      }`}
                    >
                      <div className="px-2.5 py-1.5 flex flex-col sm:flex-row sm:items-start gap-2">
                        <label className="flex items-center gap-1.5 text-[10px] text-slate-400 sm:pt-0.5">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelected(p.id)}
                            className="h-3.5 w-3.5 accent-emerald-600"
                          />
                          Select
                        </label>
                        <div className="shrink-0 flex items-center gap-1.5 sm:flex-col sm:gap-0">
                          <div
                            className="h-7 w-7 rounded-full border flex items-center justify-center bg-transparent"
                            style={{ borderColor: scoreColor(p.score) }}
                          >
                            <span
                              className="font-mono text-xs font-bold"
                              style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {p.score}
                            </span>
                          </div>
                          <span className="text-[7px] text-slate-500 uppercase tracking-widest">score</span>
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                            <h2 className={`text-sm font-bold leading-tight ${isLocked ? "text-slate-500" : "text-slate-50"}`}>
                              {isLocked ? `Locked lead · ${p.industry}` : p.company}
                            </h2>
                            {!isLocked && (
                              <span
                                className="text-[10px] font-semibold"
                                style={{ color: isActive ? "#34d399" : "#6ee7b7" }}
                              >
                                {isActive ? "Review Queued" : p.stage}
                              </span>
                            )}
                            {isLocked && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-sky-300">
                                <LockKeyhole className="h-3 w-3" /> Sign up to unlock
                              </span>
                            )}
                            {p.signalAge && !isLocked && (
                              <span className="text-[10px] font-medium text-amber-300/90">{p.signalAge}</span>
                            )}
                          </div>
                          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0 text-[11px] text-slate-400">
                            {!isLocked && (
                              <>
                                <span className="inline-flex items-center gap-0.5"><MapPin className="h-3 w-3" />{p.location}</span>
                                <span className="inline-flex items-center gap-0.5"><Users className="h-3 w-3" />{p.employees}</span>
                              </>
                            )}
                            <span>{p.industry}</span>
                            {isLocked && p.priorityTier && (
                              <span className="font-semibold text-amber-300">{p.priorityTier}</span>
                            )}
                          </p>

                          {isLocked ? (
                            <p className="mt-1.5 border-l border-sky-400/50 pl-2 text-[11px] leading-snug text-sky-100/90">
                              {p.priorityTier ? `${p.priorityTier} · ` : ""}
                              {p.industry} buyer with robot-fit signal — sign up for full evidence.
                            </p>
                          ) : (
                            <p className="mt-1.5 border-l pl-2 text-[11px] leading-snug" style={{ borderColor: `${p.signalColor}80` }}>
                              <span className="font-semibold uppercase tracking-wide mr-1.5" style={{ color: p.signalColor }}>{p.signalType}</span>
                              <span className="text-amber-200/90">{p.signal}</span>
                            </p>
                          )}
                        </div>
                      </div>

                      {!isLocked && (p.shareSummary || (p.robotTypes && p.robotTypes.length > 0)) && (
                        <div className="mx-3 mb-1.5 border-l border-cyan-400/50 pl-2">
                          <p className="text-[10px] leading-snug text-cyan-100/90">
                            <span className="font-semibold uppercase tracking-wide text-cyan-300">Intelligence · </span>
                            {p.shareSummary || ""}
                            {p.robotTypes && p.robotTypes.length > 0 ? (
                              <span className="text-slate-400"> · Robots: {p.robotTypes.join(" · ")}</span>
                            ) : null}
                          </p>
                          {p.leadId != null && (
                            <div className="mt-1">
                              <LeadShareBar
                                variant="dark"
                                lead={{
                                  id: p.leadId,
                                  company_name: p.company,
                                  priority_tier: p.priorityTier,
                                  share_summary: p.shareSummary,
                                }}
                              />
                            </div>
                          )}
                        </div>
                      )}

                      {!isLocked && (
                        <div className="mx-3 mb-1.5 border-l border-emerald-400/50 pl-2">
                          <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                            Cal → you · seller brief
                          </p>
                          <p className="mt-0.5 text-[11px] font-semibold text-slate-100">{p.sellerBrief.headline}</p>
                          <p className="mt-1 text-[10px] leading-snug text-slate-300">
                            <span className="font-semibold text-amber-200">Why now · </span>
                            {p.sellerBrief.whyNow}
                          </p>
                          <p className="mt-0.5 text-[10px] leading-snug text-slate-300">
                            <span className="font-semibold text-amber-200">Pitch · </span>
                            {p.sellerBrief.pitch}
                          </p>
                          <p className="mt-0.5 text-[10px] leading-snug text-slate-400">
                            <span className="font-semibold text-cyan-300">Robot fit · </span>
                            {p.sellerBrief.robotFit}
                            <span className="text-slate-500"> · {p.scoreReason}</span>
                          </p>
                        </div>
                      )}

                      {!isLocked && (
                        <div className="mx-3 mb-1.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px]">
                          <span className="inline-flex items-center gap-1 text-emerald-200">
                            <ArrowRight className="h-3 w-3 text-emerald-300" />
                            {p.sellerBrief.nextStep}
                          </span>
                          <span className="font-semibold text-emerald-300">{p.timing}</span>
                          <button
                            type="button"
                            onClick={() => copyRfqPacket(p)}
                            className="inline-flex items-center gap-1 border border-cyan-400/40 bg-transparent px-1.5 py-0.5 text-[10px] font-semibold text-cyan-100 hover:border-cyan-300"
                          >
                            <FileText className="h-3 w-3" />
                            Copy RFQ note
                          </button>
                        </div>
                      )}

                      {isActive && (
                        <p className="mx-3 mb-1.5 border-l border-emerald-400/50 pl-2 text-[10px] leading-snug text-emerald-100/90">
                          <span className="font-semibold uppercase tracking-wide text-emerald-300">SIGNAL plan · </span>
                          Draft outreach, send after approval, follow up in 3 days, track response.
                        </p>
                      )}

                      {!(jobsHandoff && !isSignedIn) ? (
                      <div className="mx-3 mb-2 flex flex-wrap items-center gap-2 border-t border-white/10 pt-1.5">
                        {isLocked ? (
                          <Link
                            href={resultsSignupHref}
                            className="inline-flex items-center gap-1.5 border border-amber-400/50 bg-transparent px-2.5 py-1 text-[11px] font-bold text-amber-100 hover:border-amber-300"
                          >
                            Sign up to unlock
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        ) : (
                          <Link
                            href={
                              p.leadId != null
                                ? jobsHandoff
                                  ? buyerLeadsHref({
                                      robotUrl: submittedUrl,
                                      signedIn: true,
                                      src: jobsSrc,
                                      leadId: p.leadId,
                                    })
                                  : `/pipeline?src=results_scan&lead=${p.leadId}${submittedUrl ? `&url=${encodeURIComponent(submittedUrl)}` : ""}`
                                : fullPipelineHref
                            }
                            className="inline-flex items-center gap-1.5 border border-amber-400/50 bg-transparent px-2.5 py-1 text-[11px] font-bold text-amber-100 hover:border-amber-300"
                          >
                            Open in Pipeline
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>

              {jobsHandoff ? (
                <div className="sticky bottom-2 z-40 mt-6">
                  <div className="border border-emerald-500/40 bg-[#0b162f]/95 px-4 py-3 text-center">
                    <p className="text-[12px] text-slate-300">
                      {isSignedIn
                        ? "More than 5 jobs for your robot live on the pipeline."
                        : "Sign up to keep these 5 jobs for your robot. More than 5 jobs live on the pipeline."}
                    </p>
                    <Link
                      href={isSignedIn ? fullPipelineHref : resultsSignupHref}
                      className="mt-3 inline-flex items-center justify-center bg-emerald-400 px-5 py-3 text-sm font-bold uppercase tracking-[0.06em] text-[#04122a] hover:bg-emerald-300"
                    >
                      {isSignedIn ? JOBS_FOR_YOUR_ROBOT_CTA : JOBS_FOR_YOUR_ROBOT_KEEP_CTA}
                    </Link>
                  </div>
                </div>
              ) : (
              <ResultsNextStepCta
                matchCount={sortedProspects.length}
                pipelineHref={fullPipelineHref}
                isSignedIn={isSignedIn}
                signupHref={resultsSignupHref}
              />
              )}
            </>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
