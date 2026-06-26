/**
 * Results — ReadyForRobots
 * URL request → scan → matched prospect cards → SIGNAL activation.
 */
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Bell,
  Bot,
  CalendarCheck,
  CheckCircle2,
  FileText,
  LockKeyhole,
  MapPin,
  MousePointer2,
  Presentation,
  Send,
  Sparkles,
  TrendingUp,
  UploadCloud,
  Users,
  Zap,
} from "lucide-react";
import { Link, useSearch } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";
import { useAuth } from "@/contexts/AuthContext";
import { OUTREACH_CTA, OUTREACH_SIGNATURE } from "@/lib/agentMessaging";
import { normalizeUrl } from "@/lib/normalizeUrl";
import { getApiBase, fetchWithTimeoutRetry, liveFetchInit } from "@/lib/apiBase";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { cleanScrapedText } from "@/lib/text";
import { toast } from "sonner";
import LeadShareBar from "@/components/LeadShareBar";
import PipelineOutreachValuePanel from "@/components/pipeline/PipelineOutreachValuePanel";
import ResultsValueStrip from "@/components/results/ResultsValueStrip";

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
};

type MaterialChoice = "upload" | "suggest" | "skip";
type ScopeChoice = "all" | "selected" | "top";
type ModeChoice = "manual" | "assisted" | "autopilot";

const MATERIAL_OPTIONS: Array<{
  id: MaterialChoice;
  title: string;
  desc: string;
  icon: typeof UploadCloud;
}> = [
  {
    id: "upload",
    title: "Upload sales deck",
    desc: "Give SIGNAL your current presentation so follow-up uses your actual positioning.",
    icon: UploadCloud,
  },
  {
    id: "suggest",
    title: "Suggest deck strategy",
    desc: "SIGNAL proposes a deck format, proof points, and ROI story for you to implement.",
    icon: Presentation,
  },
  {
    id: "skip",
    title: "Skip materials",
    desc: "Start with lead evaluation, sales strategy, activity schedule, and draft outreach.",
    icon: Sparkles,
  },
];

const SCOPE_OPTIONS: Array<{ id: ScopeChoice; title: string; desc: string }> = [
  { id: "all", title: "Activate all leads", desc: "SIGNAL works every matched lead in this results set." },
  { id: "selected", title: "Use selected leads", desc: "Only the leads you checked below move into SIGNAL activation." },
  { id: "top", title: "Let SIGNAL prioritize", desc: "SIGNAL starts with the strongest three leads by score and signal quality." },
];

const MODE_OPTIONS: Array<{
  id: ModeChoice;
  title: string;
  desc: string;
  gated: boolean;
}> = [
  { id: "manual", title: "Manual", desc: "SIGNAL evaluates leads and prepares strategy plus draft outreach for your review.", gated: false },
  { id: "assisted", title: "Assisted", desc: "SIGNAL drafts outreach, asks before sending, then tracks replies.", gated: true },
  { id: "autopilot", title: "Autopilot", desc: "SIGNAL sends approved messages, follows up, and escalates technical questions when needed.", gated: true },
];

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

export default function Results() {
  const search = useSearch();
  const params = new URLSearchParams(search);
  const initialUrl = params.get("url")?.trim() || "";
  const { session } = useAuth();

  const [urlInput, setUrlInput] = useState(initialUrl);
  const [submittedUrl, setSubmittedUrl] = useState(initialUrl);
  const [scanStep, setScanStep] = useState(initialUrl ? 1 : 0);
  const [scanning, setScanning] = useState(Boolean(initialUrl));
  const [loading, setLoading] = useState(Boolean(initialUrl));
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [copiedProspectId, setCopiedProspectId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [choosingScout, setChoosingScout] = useState(false);
  const [activatedIds, setActivatedIds] = useState<Set<string>>(new Set());
  const [usingFallback, setUsingFallback] = useState(false);
  const [materialChoice, setMaterialChoice] = useState<MaterialChoice>("suggest");
  const [scopeChoice, setScopeChoice] = useState<ScopeChoice>("top");
  const [modeChoice, setModeChoice] = useState<ModeChoice>("manual");
  const [deckFileName, setDeckFileName] = useState("");
  const [activationId, setActivationId] = useState<number | null>(null);
  const [activatingScout, setActivatingScout] = useState(false);

  const selectedCount = selectedIds.size;
  const activatedCount = activatedIds.size;
  const isSignedIn = Boolean(session);
  const topProspect = useMemo(
    () => [...prospects].sort((a, b) => b.score - a.score)[0] ?? null,
    [prospects],
  );

  const resultsSignupNext = submittedUrl
    ? `/results?url=${encodeURIComponent(submittedUrl)}`
    : "/results";

  const copyProspectDraft = (prospect: Prospect) => {
    const text = `Subject: ${prospect.outreachSubject}\n\n${prospect.outreachBody}`;
    void navigator.clipboard.writeText(text).then(() => {
      setCopiedProspectId(prospect.id);
      toast.success("Draft copied to clipboard");
      window.setTimeout(() => setCopiedProspectId(null), 2000);
    });
  };

  useEffect(() => {
    if (!submittedUrl) return;
    setScanStep(1);
    setScanning(true);
    setLoading(true);
    setProspects([]);
    setSelectedIds(new Set());
    setActivatedIds(new Set());
    setChoosingScout(false);
    setMaterialChoice("suggest");
    setScopeChoice("top");
    setModeChoice("manual");
    setDeckFileName("");
    setActivationId(null);
    setActivatingScout(false);
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
              limit: 8,
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
        const mapped = matches.slice(0, 8).map(mapApiLead);
        if (!mapped.length) throw new Error("No URL-specific matches returned");
        if (!cancelled) setProspects(mapped);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setUsingFallback(true);
          setProspects(fallbackProspects);
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
  }, [submittedUrl]);

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

  function activationIdsForScope(scope = scopeChoice): string[] {
    if (scope === "all") return prospects.map((p) => p.id);
    if (scope === "selected") return Array.from(selectedIds);
    return [...prospects]
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
      .map((p) => p.id);
  }

  async function activateScout(overrides: { scope?: ScopeChoice; mode?: ModeChoice; material?: MaterialChoice } = {}) {
    if (!session?.access_token) {
      const next = typeof window !== "undefined" ? `${window.location.pathname}${window.location.search}` : "/results";
      toast.info("Sign up or sign in before SIGNAL can save leads to CRM or prepare outbound work.");
      window.location.href = `/signup?next=${encodeURIComponent(next)}`;
      return;
    }
    const scope = overrides.scope ?? scopeChoice;
    const mode = overrides.mode ?? modeChoice;
    const material = overrides.material ?? materialChoice;
    const ids = activationIdsForScope(scope);
    if (!ids.length) {
      toast.error("Select at least one lead for SIGNAL.");
      return;
    }
    setScopeChoice(scope);
    setModeChoice(mode);
    setMaterialChoice(material);
    setActivatingScout(true);
    try {
      const selectedLeads = prospects
        .filter((p) => ids.includes(p.id))
        .map((p) => ({
          id: p.id,
          company: p.company,
          score: p.score,
          signal: p.signal,
          signalType: p.signalType,
          action: p.action,
          timing: p.timing,
          relevance: p.relevance,
        }));
      const response = await fetch(`${getApiBase()}/api/scout/activations`, liveFetchInit({
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader(session?.access_token),
        },
        body: JSON.stringify({
          fingerprint: scoutFingerprint(),
          sourceUrl: submittedUrl,
          materialChoice: material,
          materialFilename: deckFileName || undefined,
          scopeChoice: scope,
          modeChoice: mode,
          leads: selectedLeads,
        }),
      }));
      if (!response.ok) throw new Error(await response.text());
      const activation = await response.json();
      setActivationId(Number(activation.id) || null);
      setActivatedIds(new Set(ids));
      setChoosingScout(false);
      toast.success(`SIGNAL review queue #${activation.id} created. Leads are saved to CRM and waiting for your approval.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not activate SIGNAL.");
    } finally {
      setActivatingScout(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="flex-1 pt-20 sm:pt-24 pb-16 sm:pb-20 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 text-xs text-gray-600 mb-6 sm:mb-8">
            <Link href="/" className="hover:text-gray-600 transition-colors">Home</Link>
            <span>/</span>
            <span className="text-gray-500">{submittedUrl ? `Results for ${submittedUrl}` : "Activate SIGNAL"}</span>
          </div>

          {!submittedUrl && (
            <section className="py-10 sm:py-16">
              <div className="rounded-3xl border border-amber-200 bg-amber-50 p-6 sm:p-10 shadow-sm">
                <p className="text-[10px] font-normal uppercase tracking-[0.2em] mb-3" style={{ color: "#FFB000" }}>
                  Activate SIGNAL
                </p>
                <h1 className="font-extrabold text-gray-900 leading-tight mb-3" style={{ fontSize: "clamp(2rem, 4vw, 3.25rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Give SIGNAL a URL first.
                </h1>
                <p className="text-sm text-gray-700 max-w-xl mb-8">
                  Paste your robot, company, or product URL. SIGNAL will scan it, match prospective sales leads, explain why each one is relevant, and score the opportunity.
                </p>
                <form onSubmit={submitUrl} className="flex flex-col sm:flex-row gap-3">
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://your-robot-company.com/product"
                    className="min-w-0 flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-base sm:text-sm text-gray-900 outline-none placeholder:text-gray-500 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20"
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
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                    ) : (
                      <div className={`h-3.5 w-3.5 rounded-full border shrink-0 ${active ? "border-amber-500 animate-pulse" : "border-gray-300"}`} />
                    )}
                    <span
                      className={`font-mono text-xs font-medium ${active ? "text-amber-700" : done ? "text-emerald-700" : "text-gray-600"}`}
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
              <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] mb-2 text-emerald-700">
                    Scan complete · {prospects.length} opportunities found{usingFallback ? " · sample mode" : ""}
                  </p>
                  <h1 className="font-extrabold text-gray-900 leading-tight" style={{ fontSize: "clamp(1.5rem, 4vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                    Your matched pipeline
                  </h1>
                  <p className="text-sm text-gray-700 mt-2">
                    Based on <span className="text-gray-900 font-medium break-all">{submittedUrl}</span>. Select the leads you want SIGNAL to develop.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setChoosingScout((current) => !current)}
                  className="inline-flex w-full sm:w-auto items-center justify-center gap-2.5 rounded-2xl border-2 border-amber-500 bg-amber-500 px-6 py-3 text-sm font-bold text-gray-900 transition-all hover:bg-amber-400 sm:shrink-0"
                >
                  <Bot className="h-4 w-4" /> Activate SIGNAL
                </button>
              </div>

              {!isSignedIn && (
                <ResultsValueStrip leadCount={prospects.length} scanUrl={submittedUrl} />
              )}

              {topProspect && !isSignedIn && (
                <div className="mb-6">
                  <PipelineOutreachValuePanel
                    deal={{
                      id: topProspect.leadId ?? 0,
                      company: topProspect.company,
                      outreachSubject: topProspect.outreachSubject,
                      outreachBody: topProspect.outreachBody,
                    }}
                    hasSession={false}
                    copied={copiedProspectId === topProspect.id}
                    onCopy={() => copyProspectDraft(topProspect)}
                    signupNext={resultsSignupNext}
                  />
                </div>
              )}

              {choosingScout && (
                <div className="mb-6 rounded-2xl border border-gray-200 bg-white px-5 py-4">
                  <div className="flex flex-col gap-3 border-b border-gray-100 pb-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-start gap-3">
                      <Bot className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "#FFB000" }} />
                      <div>
                        <p className="text-sm font-semibold text-gray-900" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                          Activate SIGNAL sales motion
                        </p>
                        <p className="mt-1 max-w-2xl text-xs leading-relaxed text-gray-500">
                          Choose materials, lead scope, and operating mode. SIGNAL will save leads to CRM and prepare the workflow before any outbound messages or follow-ups.
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-800">
                        <CheckCircle2 className="h-3 w-3" /> {activationIdsForScope().length} leads selected for review
                      </span>
                      {!isSignedIn && (
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-900">
                          <LockKeyhole className="h-3 w-3" /> Account required to send
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 grid gap-4">
                    <div className="border-b border-gray-100 pb-4">
                      <div className="mb-2 flex items-center gap-2">
                        <span className="text-[10px] font-normal" style={{ color: "#047857" }}>01</span>
                        <p className="text-[10px] font-normal uppercase tracking-widest" style={{ color: "#047857" }}>Sales materials</p>
                      </div>
                      <div className="grid gap-2 md:grid-cols-3">
                        {MATERIAL_OPTIONS.map((option) => {
                          const Icon = option.icon;
                          const active = materialChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setMaterialChoice(option.id)}
                              className="rounded-xl border px-3 py-2.5 text-left transition-all hover:bg-gray-50"
                              style={active
                                ? { borderColor: "rgba(5,150,105,0.45)", background: "rgba(5,150,105,0.08)" }
                                : { borderColor: "#e5e7eb", background: "#ffffff" }}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <span className="flex min-w-0 items-center gap-2">
                                  <Icon className="h-3.5 w-3.5 shrink-0" style={{ color: active ? "#047857" : "#9ca3af" }} />
                                  <span className="truncate text-xs font-bold text-gray-900">{option.title}</span>
                                </span>
                                {active && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                              </div>
                              <p className="mt-1 text-[11px] leading-relaxed text-gray-600">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                      {materialChoice === "upload" && (
                        <label className="mt-2 flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-dashed border-gray-200 bg-white px-3 py-2.5 text-xs text-gray-500 hover:border-emerald-300">
                          <span>{deckFileName || "Choose a PDF, PPT, or deck file"}</span>
                          <span className="font-normal text-emerald-700">Browse</span>
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf,.ppt,.pptx"
                            onChange={(e) => setDeckFileName(e.target.files?.[0]?.name || "")}
                          />
                        </label>
                      )}
                    </div>

                    <div className="border-b border-gray-100 pb-4">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-normal text-emerald-700">02</span>
                          <p className="text-[10px] font-normal uppercase tracking-widest text-emerald-700">Lead scope</p>
                        </div>
                        <p className="text-[11px] text-gray-600">
                          {selectedCount} selected
                        </p>
                      </div>
                      <div className="grid gap-2 md:grid-cols-3">
                        {SCOPE_OPTIONS.map((option) => {
                          const active = scopeChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setScopeChoice(option.id)}
                              className="rounded-xl border px-3 py-2.5 text-left transition-all hover:bg-gray-50"
                              style={active
                                ? { borderColor: "rgba(5,150,105,0.42)", background: "rgba(5,150,105,0.08)" }
                                : { borderColor: "#e5e7eb", background: "#ffffff" }}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-xs font-bold text-gray-900">{option.title}</p>
                                {active && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                              </div>
                              <p className="mt-1 text-[11px] leading-relaxed text-gray-600">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="border-b border-gray-100 pb-4">
                      <div className="mb-2 flex items-center gap-2">
                        <span className="text-[10px] font-normal text-emerald-700">03</span>
                        <p className="text-[10px] font-normal uppercase tracking-widest text-emerald-700">Automation mode</p>
                      </div>
                      <div className="grid gap-2 md:grid-cols-3">
                        {MODE_OPTIONS.map((option) => {
                          const active = modeChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setModeChoice(option.id)}
                              className="rounded-xl border px-3 py-2.5 text-left transition-all hover:bg-gray-50"
                              style={active
                                ? { borderColor: "rgba(5,150,105,0.42)", background: "rgba(5,150,105,0.08)" }
                                : { borderColor: "#e5e7eb", background: "#ffffff" }}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-xs font-bold text-gray-900">{option.title}</p>
                                {active ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : option.gated && !isSignedIn && <LockKeyhole className="h-3 w-3 text-gray-400" />}
                              </div>
                              <p className="mt-1 text-[11px] leading-relaxed text-gray-600">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div>
                      <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-emerald-800">SIGNAL starts with</p>
                      <div className="grid gap-x-4 gap-y-1.5 text-[11px] text-gray-700 md:grid-cols-4">
                        <span className="flex items-center gap-1.5"><FileText className="h-3.5 w-3.5 text-emerald-600" /> Lead evaluation</span>
                        <span className="flex items-center gap-1.5"><Presentation className="h-3.5 w-3.5 text-emerald-600" /> Sales strategy</span>
                        <span className="flex items-center gap-1.5"><CalendarCheck className="h-3.5 w-3.5 text-emerald-600" /> Activity schedule</span>
                        <span className="flex items-center gap-1.5"><Bell className="h-3.5 w-3.5 text-emerald-600" /> Reply alerts</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center">
                      <button
                        type="button"
                        onClick={() => activateScout()}
                        disabled={activatingScout}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-amber-500 bg-amber-500 px-4 py-2.5 text-xs font-bold text-gray-900 transition-all hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {activatingScout ? "Creating activation..." : "Start SIGNAL activation"} <Send className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          activateScout({ mode: "manual", material: "skip", scope: "top" });
                        }}
                        disabled={activatingScout}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-300 bg-gray-50 px-5 py-3 text-xs font-bold text-gray-800 transition-all hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Skip setup and draft only <MousePointer2 className="h-3.5 w-3.5" />
                      </button>
                      <p className="text-[11px] text-gray-600 sm:ml-auto">
                        Auth first. CRM capture first. Sending stays gated by your review.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activatedCount > 0 && (
                <div className="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                  <p className="text-sm font-bold text-emerald-900 mb-1">SIGNAL review queue created</p>
                  <p className="text-xs text-gray-700">
                    {activationId ? `Activation #${activationId}: ` : ""}
                    Leads were saved to CRM. Review SIGNAL&apos;s workflow, draft outreach, timing, and cadence before any outbound action begins.
                  </p>
                </div>
              )}

              <div className="space-y-4">
                {prospects.map((p) => {
                  const isSelected = selectedIds.has(p.id);
                  const isActive = activatedIds.has(p.id);
                  return (
                    <div key={p.id} className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden hover:border-emerald-300 transition-colors">
                      <div className="px-4 sm:px-6 pt-5 sm:pt-6 pb-4 flex flex-col sm:flex-row sm:items-start gap-4">
                        <label className="flex items-center gap-2 text-xs text-gray-700 sm:pt-4">
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
                          <span className="text-[9px] text-gray-600 uppercase tracking-widest">score</span>
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-gray-900">{p.company}</h2>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: isActive ? "#34d399" : "#10b981", background: isActive ? "rgba(52,211,153,0.12)" : "rgba(5,150,105,0.15)", border: isActive ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(5,150,105,0.3)" }}>
                              {isActive ? "Review Queued" : p.stage}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600 mb-3">
                            <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>
                            <span className="flex items-center gap-1"><Users className="h-3 w-3" />{p.employees} employees</span>
                            <span>{p.industry}</span>
                          </div>

                          <div className="flex min-w-0 items-start gap-2.5 overflow-hidden p-3 rounded-xl" style={{ background: `${p.signalColor}0d`, border: `1px solid ${p.signalColor}25` }}>
                            <TrendingUp className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: p.signalColor }} />
                            <div className="min-w-0">
                              <span className="text-[10px] font-bold uppercase tracking-widest mr-2" style={{ color: p.signalColor }}>{p.signalType}</span>
                              <span className="mt-1 block break-words text-xs font-normal leading-relaxed" style={{ color: "#FFB000", overflowWrap: "anywhere" }}>{p.signal}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {(p.shareSummary || (p.robotTypes && p.robotTypes.length > 0)) && (
                        <div className="px-4 sm:px-6 pb-2">
                          <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-800 mb-1">Intelligence</p>
                            {p.shareSummary && (
                              <p className="text-xs text-gray-700 leading-relaxed">{p.shareSummary}</p>
                            )}
                            {p.robotTypes && p.robotTypes.length > 0 && (
                              <p className="mt-2 text-[11px] text-gray-700">
                                <span className="font-semibold text-gray-900">Robots: </span>
                                {p.robotTypes.join(" · ")}
                              </p>
                            )}
                            {p.leadId != null && (
                              <div className="mt-3">
                                <LeadShareBar
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

                      <div className="px-4 sm:px-6 pb-4 grid gap-3 sm:grid-cols-2">
                        <div className="min-w-0 rounded-xl border border-gray-200 bg-gray-50 p-3">
                          <p className="text-[10px] font-semibold uppercase tracking-widest mb-1 text-emerald-800">Why relevant</p>
                          <p className="mb-3 block break-words rounded-lg border-l-2 border-amber-500 bg-amber-50 px-3 py-2 text-sm font-medium leading-relaxed text-amber-900" style={{ overflowWrap: "anywhere" }}>
                            “{p.signal}”
                          </p>
                          <p className="break-words text-xs text-gray-700 leading-relaxed" style={{ overflowWrap: "anywhere" }}>{p.relevance}</p>
                        </div>
                        <div className="min-w-0 rounded-xl border border-gray-200 bg-gray-50 p-3">
                          <p className="text-[10px] font-semibold uppercase tracking-widest mb-1 text-emerald-800">Score rationale</p>
                          <p className="text-xs text-gray-700 leading-relaxed">{p.scoreReason}</p>
                        </div>
                      </div>

                      <div className="px-4 sm:px-6 pb-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                        <div className="flex items-center gap-2 flex-1">
                          <ArrowRight className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                          <span className="text-sm text-gray-800">{p.action}</span>
                        </div>
                        <span className="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0 text-emerald-800 bg-emerald-50 border border-emerald-200">
                          {p.timing}
                        </span>
                      </div>

                      {isActive && (
                        <div className="mx-4 sm:mx-6 mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-900 mb-1">SIGNAL follow-up plan</p>
                          <p className="text-xs text-gray-700 leading-relaxed">
                            Draft signal-specific outreach, send first touch after approval, follow up in 3 business days, track response, and escalate technical questions when needed.
                          </p>
                        </div>
                      )}

                      <div className="px-4 sm:px-6 pb-5 border-t border-gray-100">
                        <PipelineOutreachValuePanel
                          deal={{
                            id: p.leadId ?? 0,
                            company: p.company,
                            outreachSubject: p.outreachSubject,
                            outreachBody: p.outreachBody,
                          }}
                          hasSession={isSignedIn}
                          copied={copiedProspectId === p.id}
                          onCopy={() => copyProspectDraft(p)}
                          signupNext={resultsSignupNext}
                          variant="compact"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
