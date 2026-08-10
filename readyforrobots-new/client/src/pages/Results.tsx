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
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import { Link, useSearch } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import PageHeroDark from "@/components/layout/PageHeroDark";
import { useAuth } from "@/contexts/AuthContext";
import { OUTREACH_CTA, OUTREACH_SIGNATURE } from "@/lib/agentMessaging";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { getApiBase, fetchWithTimeoutRetry, liveFetchInit } from "@/lib/apiBase";
import { trackUrlScan, readSupplyAttribution, trackSupplyConversion } from "@/lib/siteAnalytics";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader, getFreshAccessToken } from "@/lib/supabase";
import { cleanScrapedText } from "@/lib/text";
import { toast } from "sonner";
import LeadShareBar from "@/components/LeadShareBar";
import ResultsValueStrip from "@/components/results/ResultsValueStrip";
import ResultsFomoBanner, { RESULTS_ANONYMOUS_UNLOCK } from "@/components/results/ResultsFomoBanner";
import ResultsNextStepCta from "@/components/results/ResultsNextStepCta";

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
  if (!Number.isFinite(parsed)) return 8;
  return Math.max(3, Math.min(30, Math.round(parsed)));
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
  const company = lead.company_name || `Matched Lead ${index + 1}`;
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
    action: lead.recommended_action || lead.gtm?.suggested_motion || "Reach out with a personalized automation use case",
    relevance,
    scoreReason,
    draft: "",
    outreachSubject: "",
    outreachBody: "",
    stage,
    leadId: typeof lead.id === "number" ? lead.id : undefined,
    shareSummary: lead.share_summary || undefined,
    priorityTier: lead.priority_tier || undefined,
    robotTypes: lead.robot_types_needed,
    signalAge: formatSignalAge(lead.created_at),
  };
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
    stage: row.tier ? `${row.tier} Lead` : score >= 85 ? "Draft Ready" : "New Signal",
    leadId: row.id && /^\d+$/.test(String(row.id)) ? Number(row.id) : undefined,
    priorityTier: row.tier,
  };
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
  return { ...p, ...outreach };
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
  const requestedLimit = clampResultsLimit(params.get("limit"));
  const sampleMode = params.get("sample") === "1";
  const sampleName = (params.get("sample_name") || "").trim();
  const { session, loading: authLoading } = useAuth();

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
  const anonymousUnlockedCount = Math.min(RESULTS_ANONYMOUS_UNLOCK, sortedProspects.length);
  const topLeadId = sortedProspects[0]?.leadId;

  const resultsPageHref = useMemo(() => {
    const next = new URLSearchParams();
    if (submittedUrl) next.set("url", submittedUrl);
    next.set("limit", String(requestedLimit));
    next.set("src", "signup_return_results");
    return `/results?${next.toString()}`;
  }, [requestedLimit, submittedUrl]);

  const fullPipelineHref = useMemo(() => {
    const params = new URLSearchParams();
    params.set("src", "results_scan");
    params.set("view", "all");
    if (submittedUrl) params.set("url", submittedUrl);
    if (topLeadId != null) params.set("lead", String(topLeadId));
    return `/pipeline?${params.toString()}`;
  }, [submittedUrl, topLeadId]);

  // After signup from Results, land back on the 5-lead preview — then Pipeline is step 3.
  const resultsSignupNext = resultsPageHref;
  const resultsSignupHref = `/signup?next=${encodeURIComponent(resultsSignupNext)}&src=results_gate`;

  // Workflow: URL → signup (new) → Results → Pipeline. Keep unsigned users on the signup step.
  useEffect(() => {
    if (sampleMode || authLoading) return;
    if (session?.access_token) return;
    if (!submittedUrl) return;
    window.location.replace(resultsSignupHref);
  }, [authLoading, resultsSignupHref, sampleMode, session?.access_token, submittedUrl]);

  const copyRfqPacket = (prospect: Prospect) => {
    const packet = buildRfqSpecPacket(prospect);
    void navigator.clipboard.writeText(packet).then(() => {
      toast.success("RFQ/bid-project request packet copied");
    });
  };

  useEffect(() => {
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
    const stepTimer = window.setInterval(() => {
      setScanStep((current) => Math.min(current + 1, SCAN_STEPS.length - 1));
    }, 650);

    async function runScan() {
      try {
        const host = (() => {
          try {
            return new URL(submittedUrl).hostname.replace(/^www\./, "");
          } catch {
            return "prospect";
          }
        })();
        const scoutRes = await fetchWithTimeoutRetry(
          `${getApiBase()}/api/scout/scan-for-results`,
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
          25_000,
          { retries: 1, retryDelayMs: 800 },
        );
        if (scoutRes.ok) {
          const scoutData = await scoutRes.json() as { prospects?: ScoutProspectRow[] };
          const rows = Array.isArray(scoutData.prospects) ? scoutData.prospects : [];
          const mapped = rows.map(mapScoutProspect);
          if (mapped.length) {
            if (!cancelled) setProspects(mapped);
            return;
          }
        }
        const response = await fetchWithTimeoutRetry(
          `${getApiBase()}/api/robot-ready/submit`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              robot_name: host,
              url: submittedUrl,
            }),
          },
          25_000,
          { retries: 1, retryDelayMs: 800 },
        );
        if (!response.ok) throw new Error(`Scan failed with ${response.status}`);
        const data = await response.json() as RobotReadyResponse;
        const matches = Array.isArray(data.matched_companies) ? data.matched_companies : [];
        const mapped = matches.slice(0, requestedLimit).map(mapApiLead);
        if (!mapped.length) throw new Error("No URL-specific matches returned");
        if (!cancelled) setProspects(mapped);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setUsingFallback(true);
          setProspects(fallbackProspectsForLimit(requestedLimit));
          toast.info("SIGNAL could not reach the matcher in time — showing sample leads while the API recovers.");
        }
      } finally {
        if (!cancelled) {
          window.clearInterval(stepTimer);
          setScanStep(SCAN_STEPS.length - 1);
          window.setTimeout(() => {
            if (!cancelled) {
              setLoading(false);
              setScanning(false);
            }
          }, 450);
        }
      }
    }

    runScan();
    return () => {
      cancelled = true;
      window.clearInterval(stepTimer);
    };
  }, [requestedLimit, sampleAccessAllowed, sampleAccessLoading, sampleMode, submittedUrl]);

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

  // Workflow gate: new users sign up before the 5-lead Results page.
  if (!sampleMode && submittedUrl && (authLoading || !session?.access_token)) {
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
    <div className="min-h-screen flex flex-col bg-[#081126]">
      <Header />

      {!submittedUrl ? (
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
                {SCAN_STEPS.slice(0, scanStep + 1).map((step, i) => {
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

              <ResultsFomoBanner
                prospects={sortedProspects}
                isSignedIn={isSignedIn}
                scanUrl={submittedUrl}
              />

              <div className="mb-6 rounded-2xl border border-amber-400/40 bg-amber-400/10 px-4 py-4 sm:px-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-300">Step 2 of 3 · 5 sales leads</p>
                    <p className="mt-1 text-base font-bold text-white sm:text-lg">
                      Review these 5 leads — then open the large Pipeline
                    </p>
                    <p className="mt-1 text-sm text-slate-300">
                      Matches for{" "}
                      <span className="font-medium text-slate-100 break-all">{submittedUrl}</span>
                      {usingFallback ? " · sample mode" : ""}. No email drafting on this page — Pipeline comes next with instructions.
                    </p>
                  </div>
                  <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[260px]">
                    {isSignedIn ? (
                      <Link
                        href={fullPipelineHref}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-amber-300"
                      >
                        Open Pipeline with instructions
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    ) : (
                      <Link
                        href={resultsSignupHref}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-xl border-2 border-amber-400 bg-amber-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-amber-300"
                      >
                        Sign up to see 5 leads
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>

              {!isSignedIn && (
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

              <div className="space-y-4">
                {sortedProspects.map((p, index) => {
                  const isSelected = selectedIds.has(p.id);
                  const isActive = activatedIds.has(p.id);
                  const isLocked = !isSignedIn && index >= RESULTS_ANONYMOUS_UNLOCK;
                  return (
                    <div
                      key={p.id}
                      className={`rounded-2xl border bg-[#0b162f] shadow-[0_20px_45px_-30px_rgba(0,0,0,0.85)] overflow-hidden transition-colors ${
                        isLocked ? "border-sky-400/30 hover:border-sky-400/50" : "border-white/10 hover:border-emerald-400/40"
                      }`}
                    >
                      <div className="px-4 sm:px-6 pt-5 sm:pt-6 pb-4 flex flex-col sm:flex-row sm:items-start gap-4">
                        <label className="flex items-center gap-2 text-xs text-slate-300 sm:pt-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelected(p.id)}
                            className="h-4 w-4 accent-emerald-600"
                          />
                          Select
                        </label>
                        <div className="shrink-0 flex flex-col items-center gap-1">
                          <div className="h-14 w-14 rounded-full border-2 flex items-center justify-center" style={{ borderColor: scoreColor(p.score), background: `${scoreColor(p.score)}12` }}>
                            <span className="font-mono text-lg font-bold" style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}>
                              {p.score}
                            </span>
                          </div>
                          <span className="text-[9px] text-slate-500 uppercase tracking-widest">score</span>
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h2 className={`text-base font-bold ${isLocked ? "text-slate-500" : "text-slate-50"}`}>
                              {isLocked ? `Locked lead · ${p.industry}` : p.company}
                            </h2>
                            {!isLocked && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: isActive ? "#34d399" : "#10b981", background: isActive ? "rgba(52,211,153,0.12)" : "rgba(5,150,105,0.15)", border: isActive ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(5,150,105,0.3)" }}>
                                {isActive ? "Review Queued" : p.stage}
                              </span>
                            )}
                            {isLocked && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full text-sky-100 bg-sky-400/15 border border-sky-400/35">
                                <LockKeyhole className="h-3 w-3" /> Sign up to unlock
                              </span>
                            )}
                            {p.signalAge && !isLocked && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full text-amber-200 bg-amber-400/15 border border-amber-400/35">
                                {p.signalAge}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mb-3">
                            {!isLocked && (
                              <>
                                <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>
                                <span className="flex items-center gap-1"><Users className="h-3 w-3" />{p.employees} employees</span>
                              </>
                            )}
                            <span>{p.industry}</span>
                            {isLocked && p.priorityTier && (
                              <span className="font-semibold text-amber-300">{p.priorityTier}</span>
                            )}
                          </div>

                          {isLocked ? (
                            <div className="flex min-w-0 items-start gap-2.5 overflow-hidden p-3 rounded-xl border border-sky-400/30 bg-sky-400/10">
                              <TrendingUp className="h-3.5 w-3.5 shrink-0 mt-0.5 text-sky-300" />
                              <p className="text-xs leading-relaxed text-sky-100">
                                {p.priorityTier ? `${p.priorityTier} · ` : ""}
                                {p.industry} buyer with robot-fit signal — sign up to read the full evidence and outreach draft.
                              </p>
                            </div>
                          ) : (
                            <div className="flex min-w-0 items-start gap-2.5 overflow-hidden p-3 rounded-xl" style={{ background: `${p.signalColor}0d`, border: `1px solid ${p.signalColor}25` }}>
                              <TrendingUp className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: p.signalColor }} />
                              <div className="min-w-0">
                                <span className="text-[10px] font-bold uppercase tracking-widest mr-2" style={{ color: p.signalColor }}>{p.signalType}</span>
                                <span className="mt-1 block break-words text-xs font-normal leading-relaxed" style={{ color: "#FFB000", overflowWrap: "anywhere" }}>{p.signal}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {!isLocked && (p.shareSummary || (p.robotTypes && p.robotTypes.length > 0)) && (
                        <div className="px-4 sm:px-6 pb-2">
                          <div className="rounded-xl border border-cyan-400/30 bg-cyan-400/10 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-200 mb-1">Intelligence</p>
                            {p.shareSummary && (
                              <p className="text-xs text-slate-300 leading-relaxed">{p.shareSummary}</p>
                            )}
                            {p.robotTypes && p.robotTypes.length > 0 && (
                              <p className="mt-2 text-[11px] text-slate-300">
                                <span className="font-semibold text-slate-100">Robots: </span>
                                {p.robotTypes.join(" · ")}
                              </p>
                            )}
                            {p.leadId != null && (
                              <div className="mt-3">
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
                        </div>
                      )}

                      {!isLocked && (
                        <div className="px-4 sm:px-6 pb-4 grid gap-3 sm:grid-cols-2">
                          <div className="min-w-0 rounded-xl border border-white/10 bg-[#081126]/70 p-3">
                            <p className="text-[10px] font-semibold uppercase tracking-widest mb-1 text-emerald-300">Why relevant</p>
                            <p className="mb-3 block break-words rounded-lg border-l-2 border-amber-400 bg-amber-400/10 px-3 py-2 text-sm font-medium leading-relaxed text-amber-200" style={{ overflowWrap: "anywhere" }}>
                              “{p.signal}”
                            </p>
                            <p className="break-words text-xs text-slate-300 leading-relaxed" style={{ overflowWrap: "anywhere" }}>{p.relevance}</p>
                          </div>
                          <div className="min-w-0 rounded-xl border border-white/10 bg-[#081126]/70 p-3">
                            <p className="text-[10px] font-semibold uppercase tracking-widest mb-1 text-emerald-300">Score rationale</p>
                            <p className="text-xs text-slate-300 leading-relaxed">{p.scoreReason}</p>
                          </div>
                        </div>
                      )}

                      {!isLocked && (
                        <div className="px-4 sm:px-6 pb-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                          <div className="flex items-center gap-2 flex-1">
                            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-emerald-300" />
                            <span className="text-sm text-slate-200">{p.action}</span>
                          </div>
                          <span className="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0 text-emerald-200 bg-emerald-400/10 border border-emerald-400/30">
                            {p.timing}
                          </span>
                        </div>
                      )}

                      {!isLocked && (
                        <div className="px-4 sm:px-6 pb-4">
                          <button
                            type="button"
                            onClick={() => copyRfqPacket(p)}
                            className="inline-flex items-center gap-2 rounded-lg border border-cyan-400/35 bg-cyan-400/10 px-3 py-1.5 text-[11px] font-semibold text-cyan-100 hover:bg-cyan-400/20"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            Copy RFQ/bid-project request + handoff note
                          </button>
                        </div>
                      )}

                      {isActive && (
                        <div className="mx-4 sm:mx-6 mb-4 rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-200 mb-1">SIGNAL follow-up plan</p>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            Draft signal-specific outreach, send first touch after approval, follow up in 3 business days, track response, and escalate technical questions when needed.
                          </p>
                        </div>
                      )}

                      <div className="px-4 sm:px-6 pb-5 border-t border-white/10 pt-4">
                        {isLocked ? (
                          <Link
                            href={resultsSignupHref}
                            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-amber-400/40 bg-amber-400/10 px-4 py-2.5 text-xs font-bold text-amber-100 hover:bg-amber-400/20 sm:w-auto"
                          >
                            Sign up to unlock · then open Pipeline
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>
                        ) : (
                          <Link
                            href={
                              p.leadId != null
                                ? `/pipeline?src=results_scan&view=all&lead=${p.leadId}${submittedUrl ? `&url=${encodeURIComponent(submittedUrl)}` : ""}`
                                : fullPipelineHref
                            }
                            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-amber-400/40 bg-amber-400/10 px-4 py-2.5 text-xs font-bold text-amber-100 hover:bg-amber-400/20 sm:w-auto"
                          >
                            Open in Pipeline
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <ResultsNextStepCta
                matchCount={sortedProspects.length}
                pipelineHref={fullPipelineHref}
                isSignedIn={isSignedIn}
                signupHref={resultsSignupHref}
              />
            </>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
