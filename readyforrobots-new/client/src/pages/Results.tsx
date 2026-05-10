/**
 * Results — ReadyForRobots
 * URL request → scan → matched prospect cards → SCOUT activation.
 */
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Bell,
  Bot,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
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
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { scoutFingerprint } from "@/lib/scoutFingerprint";
import { authHeader } from "@/lib/supabase";
import { toast } from "sonner";

const SCAN_STEPS = [
  "Waiting for your robot or company URL…",
  "Using your URL as pipeline context…",
  "Loading pre-scored prospective sales leads…",
  "Matching fit, timing, and buying signals from the pipeline…",
  "Explaining why each lead is relevant…",
  "Preparing SCOUT follow-up plans…",
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
  stage: string;
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
    desc: "Give SCOUT your current presentation so follow-up uses your actual positioning.",
    icon: UploadCloud,
  },
  {
    id: "suggest",
    title: "Suggest deck strategy",
    desc: "SCOUT proposes a deck format, proof points, and ROI story for you to implement.",
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
  { id: "all", title: "Activate all leads", desc: "SCOUT works every matched lead in this results set." },
  { id: "selected", title: "Use selected leads", desc: "Only the leads you checked below move into SCOUT activation." },
  { id: "top", title: "Let SCOUT prioritize", desc: "SCOUT starts with the strongest three leads by score and signal quality." },
];

const MODE_OPTIONS: Array<{
  id: ModeChoice;
  title: string;
  desc: string;
  gated: boolean;
}> = [
  { id: "manual", title: "Manual", desc: "SCOUT evaluates leads and drafts strategy/emails for review.", gated: false },
  { id: "assisted", title: "Assisted", desc: "SCOUT drafts, asks before sending, then tracks replies.", gated: true },
  { id: "autopilot", title: "Autopilot", desc: "SCOUT sends, replies, follows up, and schedules meetings.", gated: true },
];

function normalizeUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
}

function scoreColor(score: number): string {
  return score >= 90 ? "#34d399" : score >= 75 ? "#a78bfa" : "#fb923c";
}

function timingFromScore(score: number): string {
  if (score >= 90) return "Decision window: Now";
  if (score >= 75) return "Decision window: 1-3 months";
  return "Decision window: 3-6 months";
}

function draftOutreach(p: Pick<Prospect, "company" | "signal" | "relevance" | "action">): string {
  return `Subject: Automation opportunity at ${p.company}

Hi [Name],

SCOUT flagged ${p.company} because ${p.relevance.toLowerCase()}

The strongest signal we found: ${p.signal}

Recommended next step: ${p.action}

Would it make sense to compare where automation could reduce labor pressure, improve throughput, or support the timing behind this signal?

Best,
[Your name]`;
}

function formatEmployees(value: number | null | undefined): string {
  if (!value || value <= 0) return "Unknown";
  return new Intl.NumberFormat("en-US").format(value);
}

function titleize(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function mapApiLead(lead: ApiLead, index: number): Prospect {
  const score = Math.round(
    lead.score?.lead_value_score ??
      lead.score?.overall_score ??
      lead.priority_score ??
      70,
  );
  const firstSignal = lead.signals?.[0];
  const signal = firstSignal?.display_text || firstSignal?.raw_text || lead.share_summary || "SCOUT found a sales-fit pattern worth reviewing.";
  const signalType = firstSignal?.signal_label || titleize(firstSignal?.signal_type || "buying_signal");
  const company = lead.company_name || `Matched Lead ${index + 1}`;
  const stage = lead.priority_tier ? `${lead.priority_tier} Lead` : score >= 85 ? "Draft Ready" : "New Signal";
  const whyNow = lead.gtm?.why_now?.filter(Boolean) || [];
  const relevance = lead.share_summary || whyNow.join(" ") || `${company} is relevant because SCOUT found active buying signals and a strong automation fit.`;
  const scoreReason = [
    `${score}/100 match score`,
    lead.priority_tier ? `${lead.priority_tier} priority` : "qualified lead",
    ...(lead.priority_reasons || whyNow).slice(0, 2),
  ].join(" · ");
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
    action: lead.gtm?.suggested_motion || "Reach out with a personalized automation use case",
    relevance,
    scoreReason,
    draft: "",
    stage,
  };
  prospect.draft = draftOutreach(prospect);
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
    signalColor: "#a78bfa",
    timing: "Decision window: 1-3 months",
    action: "Contact during facility design phase",
    relevance: "New facilities plus an automation hire indicate budget, ownership, and a near-term design window for robotics decisions.",
    scoreReason: "88/100 match score · expansion · automation owner identified · strong timing",
    draft: "",
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
    signalColor: "#fb923c",
    timing: "Decision window: 3-6 months",
    action: "Lead with safety ROI and ergonomics case",
    relevance: "Safety incidents and process improvement hiring create a clear reason to discuss automation for repetitive workflows.",
    scoreReason: "79/100 match score · safety pain · process owner hiring · moderate timing",
    draft: "",
    stage: "Review Lead",
  },
].map((p) => ({ ...p, draft: draftOutreach(p) }));

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
  const [expandedDraft, setExpandedDraft] = useState<string | null>(null);
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
        const response = await fetch(
          `${getApiBase()}/api/leads?limit=8&tier=HOT&sort=score&exclude_junk=true`,
          liveFetchInit(),
        );
        if (!response.ok) throw new Error(`Scan failed with ${response.status}`);
        const data = await response.json();
        const matches = Array.isArray(data) ? data : [];
        const mapped = matches.slice(0, 8).map(mapApiLead);
        if (!mapped.length) throw new Error("No live matches returned");
        if (!cancelled) setProspects(mapped);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setUsingFallback(true);
          setProspects(fallbackProspects);
          toast.info("Using sample matches while SCOUT reloads the lead pipeline.");
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
    const scope = overrides.scope ?? scopeChoice;
    const mode = overrides.mode ?? modeChoice;
    const material = overrides.material ?? materialChoice;
    const ids = activationIdsForScope(scope);
    if (!ids.length) {
      toast.error("Select at least one lead for SCOUT.");
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
      if (activation.requiresAccount) {
        toast.info("SCOUT preview is saved. Sign in to send emails, track replies, and schedule meetings.");
      } else {
        toast.success(`SCOUT activation #${activation.id} created for ${ids.length} lead${ids.length === 1 ? "" : "s"}.`);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not activate SCOUT.");
    } finally {
      setActivatingScout(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 text-xs text-white/30 mb-8">
            <Link href="/" className="hover:text-white/60 transition-colors">Home</Link>
            <span>/</span>
            <span className="text-white/50">{submittedUrl ? `Results for ${submittedUrl}` : "Activate Pipeline"}</span>
          </div>

          {!submittedUrl && (
            <section className="py-16">
              <div className="rounded-3xl border border-violet-500/20 p-8 sm:p-10" style={{ background: "rgba(124,58,237,0.06)" }}>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-3" style={{ color: "#a78bfa" }}>
                  Activate Pipeline
                </p>
                <h1 className="font-extrabold text-white leading-tight mb-3" style={{ fontSize: "clamp(2rem, 4vw, 3.25rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Give SCOUT a URL first.
                </h1>
                <p className="text-sm text-white/45 max-w-xl mb-8">
                  Paste your robot, company, or product URL. SCOUT will scan it, match prospective sales leads, explain why each one is relevant, and score the opportunity.
                </p>
                <form onSubmit={submitUrl} className="flex flex-col sm:flex-row gap-3">
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://your-robot-company.com/product"
                    className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-violet-400/60"
                  />
                  <button
                    type="submit"
                    className="inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-bold text-white transition-all hover:-translate-y-0.5"
                    style={{ background: "#7c3aed", boxShadow: "0 8px 24px rgba(124,58,237,0.35)" }}
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
                <div className="absolute inset-0 rounded-full border-2 border-violet-500/20 animate-ping" style={{ animationDuration: "1.5s" }} />
                <div className="absolute inset-2 rounded-full border-2 border-violet-500/40 animate-spin" style={{ animationDuration: "2s" }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="h-6 w-6" style={{ color: "#7c3aed" }} />
                </div>
              </div>

              <div className="w-full max-w-sm space-y-2">
                {SCAN_STEPS.slice(0, scanStep + 1).map((step, i) => (
                  <div key={step} className="flex items-center gap-3 text-sm" style={{ opacity: i === scanStep ? 1 : 0.35 }}>
                    {i < scanStep ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-violet-500/60 shrink-0 animate-pulse" />
                    )}
                    <span className="font-mono text-xs" style={{ color: i === scanStep ? "#c4b5fd" : "#ffffff55", fontFamily: "'JetBrains Mono', monospace" }}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {submittedUrl && !loading && !scanning && (
            <>
              <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-2" style={{ color: "#a78bfa" }}>
                    Scan complete · {prospects.length} opportunities found{usingFallback ? " · sample mode" : ""}
                  </p>
                  <h1 className="font-extrabold text-white leading-tight" style={{ fontSize: "clamp(1.8rem, 3vw, 2.5rem)", fontFamily: "'Sora', system-ui, sans-serif" }}>
                    Your matched pipeline
                  </h1>
                  <p className="text-sm text-white/40 mt-2">
                    Based on <span className="text-white/60 font-medium">{submittedUrl}</span>. Select the leads you want SCOUT to develop.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setChoosingScout((current) => !current)}
                  className="inline-flex items-center justify-center gap-2 rounded-xl border px-5 py-3 text-sm font-bold text-white transition-all hover:-translate-y-0.5"
                  style={{
                    background: "linear-gradient(135deg, rgba(124,58,237,0.95), rgba(14,165,233,0.72))",
                    borderColor: "rgba(196,181,253,0.35)",
                    boxShadow: "0 14px 36px rgba(124,58,237,0.28), inset 0 1px 0 rgba(255,255,255,0.18)",
                  }}
                >
                  <Bot className="h-4 w-4" /> Activate SCOUT
                </button>
              </div>

              {choosingScout && (
                <div
                  className="relative mb-6 overflow-hidden rounded-3xl border p-5 sm:p-6"
                  style={{
                    background:
                      "radial-gradient(circle at top left, rgba(124,58,237,0.22), transparent 34%), radial-gradient(circle at top right, rgba(45,212,191,0.14), transparent 30%), rgba(9,6,24,0.92)",
                    borderColor: "rgba(196,181,253,0.18)",
                    boxShadow: "0 24px 80px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)",
                  }}
                >
                  <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-violet-300/50 to-transparent" />
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-start gap-4">
                      <div
                        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border"
                        style={{ background: "rgba(124,58,237,0.16)", borderColor: "rgba(196,181,253,0.25)" }}
                      >
                        <Bot className="h-5 w-5 text-violet-200" />
                      </div>
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-teal-200/70">SCOUT sales motion</p>
                        <h2 className="mt-1 text-lg font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                          Activate follow-up automation
                        </h2>
                        <p className="mt-2 max-w-2xl text-xs leading-relaxed text-white/50">
                          Choose materials, lead scope, and operating mode. SCOUT will turn this results set into a structured sales motion with strategy, drafts, activity timing, reply monitoring, and user alerts.
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300/15 bg-emerald-300/8 px-2.5 py-1 text-[10px] font-bold text-emerald-100/70">
                        <CheckCircle2 className="h-3 w-3" /> {activationIdsForScope().length} leads queued
                      </span>
                      {!isSignedIn && (
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/20 bg-amber-300/10 px-2.5 py-1 text-[10px] font-bold text-amber-100/75">
                          <LockKeyhole className="h-3 w-3" /> Account required to send
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 grid gap-5">
                    <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
                      <div className="mb-3 flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-violet-400/15 text-[10px] font-bold text-violet-100">1</span>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-white/35">Sales materials</p>
                      </div>
                      <div className="grid gap-3 md:grid-cols-3">
                        {MATERIAL_OPTIONS.map((option) => {
                          const Icon = option.icon;
                          const active = materialChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setMaterialChoice(option.id)}
                              className="group rounded-2xl border p-4 text-left transition-all hover:-translate-y-0.5"
                              style={active
                                ? { borderColor: "rgba(196,181,253,0.45)", background: "linear-gradient(135deg, rgba(124,58,237,0.18), rgba(45,212,191,0.06))", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.08)" }
                                : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.025)" }}
                            >
                              <div className="mb-3 flex items-center justify-between gap-3">
                                <span
                                  className="flex h-8 w-8 items-center justify-center rounded-xl border"
                                  style={{
                                    borderColor: active ? "rgba(196,181,253,0.28)" : "rgba(255,255,255,0.08)",
                                    background: active ? "rgba(196,181,253,0.12)" : "rgba(255,255,255,0.03)",
                                  }}
                                >
                                  <Icon className="h-4 w-4" style={{ color: active ? "#c4b5fd" : "rgba(255,255,255,0.35)" }} />
                                </span>
                                {active && <CheckCircle2 className="h-4 w-4 text-teal-200" />}
                              </div>
                              <span className="text-xs font-bold text-white/80">{option.title}</span>
                              <p className="mt-1.5 text-[11px] leading-relaxed text-white/42">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                      {materialChoice === "upload" && (
                        <label className="mt-3 flex cursor-pointer items-center justify-between gap-3 rounded-2xl border border-dashed border-white/12 bg-white/[0.025] px-4 py-3 text-xs text-white/50 hover:border-violet-300/35">
                          <span>{deckFileName || "Choose a PDF, PPT, or deck file"}</span>
                          <span className="font-bold text-violet-200">Browse</span>
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf,.ppt,.pptx"
                            onChange={(e) => setDeckFileName(e.target.files?.[0]?.name || "")}
                          />
                        </label>
                      )}
                    </div>

                    <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sky-400/15 text-[10px] font-bold text-sky-100">2</span>
                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/35">Lead scope</p>
                        </div>
                        <p className="text-[11px] text-white/35">
                          {selectedCount} selected
                        </p>
                      </div>
                      <div className="grid gap-3 md:grid-cols-3">
                        {SCOPE_OPTIONS.map((option) => {
                          const active = scopeChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setScopeChoice(option.id)}
                              className="rounded-2xl border p-4 text-left transition-all hover:-translate-y-0.5"
                              style={active
                                ? { borderColor: "rgba(56,189,248,0.42)", background: "linear-gradient(135deg, rgba(56,189,248,0.14), rgba(124,58,237,0.07))" }
                                : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.025)" }}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-xs font-bold text-white/80">{option.title}</p>
                                {active && <CheckCircle2 className="h-4 w-4 text-sky-200" />}
                              </div>
                              <p className="mt-1 text-[11px] leading-relaxed text-white/40">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
                      <div className="mb-3 flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-300/15 text-[10px] font-bold text-teal-100">3</span>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-white/35">Automation mode</p>
                      </div>
                      <div className="grid gap-3 md:grid-cols-3">
                        {MODE_OPTIONS.map((option) => {
                          const active = modeChoice === option.id;
                          return (
                            <button
                              key={option.id}
                              type="button"
                              onClick={() => setModeChoice(option.id)}
                              className="rounded-2xl border p-4 text-left transition-all hover:-translate-y-0.5"
                              style={active
                                ? { borderColor: "rgba(45,212,191,0.42)", background: "linear-gradient(135deg, rgba(45,212,191,0.13), rgba(124,58,237,0.06))" }
                                : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.025)" }}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-xs font-bold text-white/80">{option.title}</p>
                                {active ? <CheckCircle2 className="h-4 w-4 text-teal-200" /> : option.gated && !isSignedIn && <LockKeyhole className="h-3 w-3 text-white/25" />}
                              </div>
                              <p className="mt-1 text-[11px] leading-relaxed text-white/40">{option.desc}</p>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
                      <p className="mb-3 text-xs font-bold text-white/72">SCOUT will start with</p>
                      <div className="grid gap-2 text-[11px] text-white/50 md:grid-cols-4">
                        <span className="flex items-center gap-2 rounded-xl bg-white/[0.03] px-3 py-2"><FileText className="h-3.5 w-3.5 text-violet-200" /> Lead evaluation</span>
                        <span className="flex items-center gap-2 rounded-xl bg-white/[0.03] px-3 py-2"><Presentation className="h-3.5 w-3.5 text-sky-200" /> Sales strategy</span>
                        <span className="flex items-center gap-2 rounded-xl bg-white/[0.03] px-3 py-2"><CalendarCheck className="h-3.5 w-3.5 text-teal-200" /> Activity schedule</span>
                        <span className="flex items-center gap-2 rounded-xl bg-white/[0.03] px-3 py-2"><Bell className="h-3.5 w-3.5 text-emerald-200" /> Reply alerts</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                      <button
                        type="button"
                        onClick={() => activateScout()}
                        disabled={activatingScout}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border px-5 py-3 text-xs font-bold text-white transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                        style={{
                          background: "linear-gradient(135deg, #7c3aed, #0ea5e9)",
                          borderColor: "rgba(196,181,253,0.28)",
                          boxShadow: "0 12px 28px rgba(14,165,233,0.18)",
                        }}
                      >
                        {activatingScout ? "Creating activation..." : "Start SCOUT activation"} <Send className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          activateScout({ mode: "manual", material: "skip", scope: "top" });
                        }}
                        disabled={activatingScout}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.035] px-5 py-3 text-xs font-bold text-white/65 transition-all hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Skip setup and draft only <MousePointer2 className="h-3.5 w-3.5" />
                      </button>
                      <p className="text-[11px] text-white/30 sm:ml-auto">
                        Drafts first. Sending stays gated by account and safety rules.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activatedCount > 0 && (
                <div className="mb-5 rounded-2xl border border-emerald-400/20 p-5" style={{ background: "rgba(52,211,153,0.06)" }}>
                  <p className="text-sm font-bold text-emerald-300 mb-1">SCOUT service active</p>
                  <p className="text-xs text-white/45">
                    {activationId ? `Activation #${activationId}: ` : ""}
                    SCOUT is queued to evaluate each lead, develop a sales strategy, draft emails and introductions, schedule activities, track replies, and ping you when a lead becomes active.
                  </p>
                </div>
              )}

              <div className="space-y-4">
                {prospects.map((p) => {
                  const draftOpen = expandedDraft === p.id;
                  const isSelected = selectedIds.has(p.id);
                  const isActive = activatedIds.has(p.id);
                  return (
                    <div key={p.id} className="rounded-2xl border border-white/8 overflow-hidden hover:border-violet-500/25 transition-colors" style={{ background: "rgba(255,255,255,0.03)" }}>
                      <div className="px-6 pt-6 pb-4 flex flex-col sm:flex-row sm:items-start gap-4">
                        <label className="flex items-center gap-2 text-xs text-white/40 sm:pt-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelected(p.id)}
                            className="h-4 w-4 accent-violet-500"
                          />
                          Select
                        </label>
                        <div className="shrink-0 flex flex-col items-center gap-1">
                          <div className="h-14 w-14 rounded-full border-2 flex items-center justify-center" style={{ borderColor: scoreColor(p.score), background: `${scoreColor(p.score)}12` }}>
                            <span className="font-mono text-lg font-bold" style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}>
                              {p.score}
                            </span>
                          </div>
                          <span className="text-[9px] text-white/25 uppercase tracking-widest">score</span>
                        </div>

                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-white">{p.company}</h2>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: isActive ? "#34d399" : "#a78bfa", background: isActive ? "rgba(52,211,153,0.12)" : "rgba(124,58,237,0.15)", border: isActive ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(124,58,237,0.3)" }}>
                              {isActive ? "SCOUT Active" : p.stage}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-white/35 mb-3">
                            <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>
                            <span className="flex items-center gap-1"><Users className="h-3 w-3" />{p.employees} employees</span>
                            <span>{p.industry}</span>
                          </div>

                          <div className="flex items-start gap-2.5 p-3 rounded-xl" style={{ background: `${p.signalColor}0d`, border: `1px solid ${p.signalColor}25` }}>
                            <TrendingUp className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: p.signalColor }} />
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-widest mr-2" style={{ color: p.signalColor }}>{p.signalType}</span>
                              <span className="text-xs text-white/50">{p.signal}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="px-6 pb-4 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-xl border border-white/6 p-3" style={{ background: "rgba(255,255,255,0.02)" }}>
                          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#a78bfa" }}>Why relevant</p>
                          <p className="text-xs text-white/50 leading-relaxed">{p.relevance}</p>
                        </div>
                        <div className="rounded-xl border border-white/6 p-3" style={{ background: "rgba(255,255,255,0.02)" }}>
                          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#a78bfa" }}>Score rationale</p>
                          <p className="text-xs text-white/50 leading-relaxed">{p.scoreReason}</p>
                        </div>
                      </div>

                      <div className="px-6 pb-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                        <div className="flex items-center gap-2 flex-1">
                          <ArrowRight className="h-3.5 w-3.5 shrink-0" style={{ color: "#7c3aed" }} />
                          <span className="text-sm text-white/60">{p.action}</span>
                        </div>
                        <span className="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0" style={{ color: "#34d399", background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.25)" }}>
                          {p.timing}
                        </span>
                      </div>

                      {isActive && (
                        <div className="mx-6 mb-4 rounded-xl border border-emerald-400/20 p-3" style={{ background: "rgba(52,211,153,0.05)" }}>
                          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-300 mb-1">SCOUT follow-up plan</p>
                          <p className="text-xs text-white/45 leading-relaxed">
                            Draft signal-specific outreach, send first touch after approval, follow up in 3 business days, track response, and escalate if buying intent increases.
                          </p>
                        </div>
                      )}

                      <div className="border-t border-white/6">
                        <button onClick={() => setExpandedDraft(draftOpen ? null : p.id)} className="w-full flex items-center justify-between px-6 py-3.5 text-left hover:bg-white/2 transition-colors">
                          <div className="flex items-center gap-2">
                            <FileText className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                            <span className="text-xs font-semibold" style={{ color: "#a78bfa" }}>View drafted outreach</span>
                          </div>
                          {draftOpen ? <ChevronUp className="h-3.5 w-3.5 text-white/25" /> : <ChevronDown className="h-3.5 w-3.5 text-white/25" />}
                        </button>
                        {draftOpen && (
                          <div className="px-6 pb-5 border-t border-white/6">
                            <pre className="text-xs text-white/50 leading-relaxed whitespace-pre-wrap pt-4" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                              {p.draft}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
