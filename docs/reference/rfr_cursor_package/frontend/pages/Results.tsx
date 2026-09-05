/**
 * Results — ReadyForRobots
 * Calls trpc.scout.scanForResults with the real company URL.
 * Scan animation runs while the LLM call is in-flight, then real prospect cards appear.
 * Color system: #0d0520 bg · #7c3aed purple · #03DAC5 teal
 */
import { useState, useEffect, useRef } from "react";
import {
  ArrowRight, Zap, TrendingUp, MapPin, Users, AlertTriangle,
  CheckCircle2, FileText, ChevronDown, ChevronUp, Lock, X, Handshake, RefreshCw, Plus, Target, Briefcase,
  Bot, Sparkles, Eye, Mail,
} from "lucide-react";
import { Link, useSearch, useLocation } from "wouter";
import Header from "@/components/Header";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { getLoginUrl } from "@/const";

const SCAN_STEPS = [
  "Analyzing company profile…",
  "Scanning 150+ signal sources…",
  "Matching automation readiness patterns…",
  "Scoring qualification factors…",
  "Generating outreach drafts…",
  "Pipeline ready.",
];

// Minimum animation duration (ms) so the scan feels deliberate even on fast connections
const MIN_SCAN_MS = 3200;

// Map signalType string → icon + color
function signalMeta(signalType: string): { icon: React.ElementType; color: string } {
  const t = signalType.toLowerCase();
  if (t.includes("labor") || t.includes("shortage")) return { icon: AlertTriangle, color: "#f87171" };
  if (t.includes("expansion") || t.includes("capex")) return { icon: TrendingUp, color: "#34d399" };
  if (t.includes("safety")) return { icon: AlertTriangle, color: "#fb923c" };
  if (t.includes("hiring") || t.includes("automation")) return { icon: Zap, color: "#a78bfa" };
  return { icon: TrendingUp, color: "#03DAC5" };
}

const scoreColor = (s: number) =>
  s >= 90 ? "#03DAC5" : s >= 75 ? "#a78bfa" : "#fb923c";

export default function Results() {
  const search = useSearch();
  const [, navigate] = useLocation();
  const params = new URLSearchParams(search);
  const inputUrl = params.get("url") || "";
  const { isAuthenticated } = useAuth();

  // Scan animation state
  const [scanStep, setScanStep] = useState(0);
  const [animDone, setAnimDone] = useState(false);
  const scanStartRef = useRef(Date.now());

  // UI state
  const [expandedDraft, setExpandedDraft] = useState<number | null>(null);
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());
  const [showModal, setShowModal] = useState(false);
  const [modalSubmitted, setModalSubmitted] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const lockedRef = useRef<HTMLDivElement>(null);

  // Cached scan data restored from sessionStorage after OAuth redirect
  const [cachedScanData, setCachedScanData] = useState<NonNullable<typeof scanMutation.data> | null>(null);

  // tRPC: real scan
  const scanMutation = trpc.scout.scanForResults.useMutation({
    onSuccess: (data) => {
      // Cache scan results in sessionStorage so they survive an OAuth redirect
      try {
        sessionStorage.setItem(
          `rfr_scan_${inputUrl}`,
          JSON.stringify({ data, ts: Date.now() })
        );
      } catch { /* storage quota exceeded — ignore */ }
    },
  });

  // tRPC: add to pipeline
  const addToPipeline = trpc.pipeline.add.useMutation({
    onSuccess: (_data, variables) => {
      toast.success(`${variables.companyName} added to your pipeline`, {
        action: { label: "View Pipeline", onClick: () => navigate("/pipeline") },
      });
    },
    onError: () => toast.error("Failed to add to pipeline — please sign in first"),
  });

  const handleAddToPipeline = (p: NonNullable<typeof scanMutation.data>["prospects"][0], idx: number) => {
    if (!isAuthenticated) {
      // Save scan results to sessionStorage before redirecting to login
      try {
        if (scanMutation.data) {
          sessionStorage.setItem(
            `rfr_scan_${inputUrl}`,
            JSON.stringify({ data: scanMutation.data, ts: Date.now() })
          );
        }
      } catch { /* ignore */ }
      // Pass current page as returnPath so OAuth redirects back here after login
      const returnPath = `/results?url=${encodeURIComponent(inputUrl)}`;
      toast.info("Sign in to activate your pipeline", {
        action: { label: "Sign in", onClick: () => { window.location.href = getLoginUrl(returnPath); } },
      });
      return;
    }
    if (addedIds.has(idx)) {
      navigate("/pipeline");
      return;
    }
    setAddedIds((prev) => { const next = new Set(prev); next.add(idx); return next; });
    // Show onboarding modal on very first activation (once per session)
    if (addedIds.size === 0) {
      const seen = sessionStorage.getItem("rfr_onboarding_shown");
      if (!seen) {
        sessionStorage.setItem("rfr_onboarding_shown", "1");
        setTimeout(() => setShowOnboarding(true), 800);
      }
    }
    // Trigger SCOUT step animation
    setAnimatingIds((prev) => { const next = new Set(prev); next.add(idx); return next; });
    setTimeout(() => setAnimatingIds((prev) => { const next = new Set(prev); next.delete(idx); return next; }), 1800);
    addToPipeline.mutate({
      companyName: p.company,
      industry: p.industry,
      robotCategory: scanMutation.data?.robotCategory ?? scanData?.robotCategory,
      signal: p.signal,
      signalType: p.signalType,
      scoutScore: p.score,
      outreachDraft: p.draft,
      opportunityType: "sales_lead",
      contactEmail: p.contactEmail,
    });
  };

  // URL entry state (when navigating to /results without a URL)
  const [urlInput, setUrlInput] = useState("");
  const [scanStarted, setScanStarted] = useState(!!inputUrl);
  const [showScanAnotherForm, setShowScanAnotherForm] = useState(false);
  const [anotherUrl, setAnotherUrl] = useState("");
  // Track which lead indices are animating their SCOUT step (Follow-up scheduled)
  const [animatingIds, setAnimatingIds] = useState<Set<number>>(new Set());
  // Onboarding modal — shown once on first pipeline activation
  const [showOnboarding, setShowOnboarding] = useState(false);

  const startScan = (url: string) => {
    const clean = url.trim().replace(/^https?:\/\//i, "").replace(/\/+$/, "");
    if (!clean) return;
    navigate(`/results?url=${encodeURIComponent(clean)}`);
  };

  // Fire the scan on mount only if we have a URL
  useEffect(() => {
    if (!inputUrl) return;
    setScanStarted(true);
    scanStartRef.current = Date.now();
    // Try to restore from sessionStorage cache first (survives OAuth redirect)
    try {
      const cached = sessionStorage.getItem(`rfr_scan_${inputUrl}`);
      if (cached) {
        const { data, ts } = JSON.parse(cached);
        // Use cache if less than 30 minutes old
        if (Date.now() - ts < 30 * 60 * 1000 && data) {
          setCachedScanData(data);
          // Skip the LLM call — animation still runs for UX
          return;
        }
      }
    } catch { /* ignore */ }
    scanMutation.mutate({ companyUrl: inputUrl });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputUrl]);

  // Step through the animation log
  useEffect(() => {
    if (animDone) return;
    if (scanStep < SCAN_STEPS.length - 1) {
      const t = setTimeout(() => setScanStep((s) => s + 1), 600);
      return () => clearTimeout(t);
    } else {
      // Animation finished — wait for both min time and data
      const elapsed = Date.now() - scanStartRef.current;
      const remaining = Math.max(0, MIN_SCAN_MS - elapsed);
      const t = setTimeout(() => setAnimDone(true), remaining + 400);
      return () => clearTimeout(t);
    }
  }, [scanStep, animDone]);

  // Show results only when both animation and data are ready
  // Use cachedScanData if available (restored after OAuth redirect), otherwise use mutation data
  const scanning = !animDone || (scanMutation.isPending && !cachedScanData);
  const scanError = scanMutation.isError && !cachedScanData;
  const scanData = cachedScanData ?? scanMutation.data;

  // Derived display data
  const prospects = scanData?.prospects ?? [];
  const lockedTeasers = scanData?.lockedTeasers ?? [];
  const totalFound = scanData?.totalFound ?? prospects.length + lockedTeasers.length;
  const robotCategory = scanData?.robotCategory ?? "";
  const companySummary = scanData?.companySummary ?? "";

  // Show modal when user scrolls to locked section
  useEffect(() => {
    if (scanning || modalSubmitted) return;
    const el = lockedRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setShowModal(true); },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [scanning, modalSubmitted]);

  const captureLead = trpc.leads.capture.useMutation({
    onSuccess: () => {
      setSubmitting(false);
      setModalSubmitted(true);
      setShowModal(false);
      toast.success("Pipeline unlocked! We'll be in touch with your full report.");
    },
    onError: () => {
      setSubmitting(false);
      toast.error("Something went wrong — please try again.");
    },
  });

  const handleLeadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      toast.error("Please enter your name and email");
      return;
    }
    setSubmitting(true);
    captureLead.mutate({
      name: name.trim(),
      email: email.trim(),
      companyUrl: inputUrl !== "yourcompany.com" ? inputUrl : undefined,
      source: "results-modal",
    });
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-20 pb-14 px-6">
        <div className="max-w-4xl mx-auto">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-white/30 mb-8">
            <Link href="/" className="hover:text-white/60 transition-colors">Home</Link>
            <span>/</span>
            <span className="text-white/50">Results for {inputUrl}</span>
          </div>

          {/* ── No URL: show entry form ── */}
          {!inputUrl ? (
            <div className="flex flex-col items-center justify-center py-24 gap-8 max-w-lg mx-auto text-center">
              <div
                className="h-14 w-14 rounded-2xl flex items-center justify-center"
                style={{ background: "rgba(255,176,0,0.1)", border: "1px solid rgba(255,176,0,0.3)" }}
              >
                <Bot className="h-7 w-7" style={{ color: "#FFB000" }} />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-white mb-2" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Activate Pipeline with SCOUT
                </h1>
                <p className="text-sm text-white/40">
                  Enter your robot company website. SCOUT will scan for buying signals, score matched prospects, and draft outreach — automatically.
                </p>
              </div>
              <form
                onSubmit={(e) => { e.preventDefault(); startScan(urlInput); }}
                className="w-full flex flex-col sm:flex-row gap-3"
              >
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="yourcompany.com"
                  className="flex-1 px-4 py-3 text-sm text-white rounded-xl border border-white/12 bg-white/6 placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
                  autoFocus
                />
                <button
                  type="submit"
                  className="shrink-0 flex items-center gap-2 text-sm font-bold px-5 py-3 rounded-xl transition-all hover:-translate-y-0.5"
                  style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
                >
                  <Zap className="h-4 w-4" /> Activate
                </button>
              </form>
              <p className="text-xs text-white/20">No signup required · Free to start · Results in seconds</p>
            </div>

          ) : scanning ? (
          /* ── Scanning state ── */
            <div className="flex flex-col items-center justify-center py-24 gap-8">
              <div className="relative h-20 w-20">
                <div
                  className="absolute inset-0 rounded-full border-2 animate-ping"
                  style={{ borderColor: "rgba(3,218,197,0.2)", animationDuration: "1.5s" }}
                />
                <div className="absolute inset-2 rounded-full border-2 animate-spin" style={{ borderColor: "rgba(3,218,197,0.4)", animationDuration: "2s" }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="h-6 w-6" style={{ color: "#03DAC5" }} />
                </div>
              </div>

              <div className="w-full max-w-sm space-y-2">
                {SCAN_STEPS.slice(0, scanStep + 1).map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 text-sm"
                    style={{ opacity: i === scanStep ? 1 : 0.35 }}
                  >
                    {i < scanStep ? (
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0" style={{ color: "#03DAC5" }} />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-violet-500/60 shrink-0 animate-pulse" />
                    )}
                    <span
                      className="font-mono text-xs"
                      style={{ color: i === scanStep ? "#c4b5fd" : "#ffffff55", fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {step}
                    </span>
                  </div>
                ))}
              </div>

              <p className="text-xs text-white/20 mt-2" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                SCOUT is scanning signals for {inputUrl}
              </p>
            </div>

          ) : scanError ? (
            /* ── Error state ── */
            <div className="flex flex-col items-center justify-center py-24 gap-6 text-center">
              <div className="h-16 w-16 rounded-2xl flex items-center justify-center" style={{ background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.25)" }}>
                <AlertTriangle className="h-7 w-7" style={{ color: "#f87171" }} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white mb-2">Scan failed</h2>
                <p className="text-sm text-white/40 max-w-sm">
                  SCOUT couldn't complete the scan. This sometimes happens with unusual URLs. Try again or go back and enter a different URL.
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setScanStep(0);
                    setAnimDone(false);
                    scanStartRef.current = Date.now();
                    scanMutation.mutate({ companyUrl: inputUrl });
                  }}
                  className="flex items-center gap-2 text-sm font-semibold px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
                  style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "transparent" }}
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Try again
                </button>
                <Link href="/">
                  <button className="flex items-center gap-2 text-sm font-semibold px-5 py-2.5 rounded-xl text-white/60 border border-white/10 hover:border-white/20 transition-colors" style={{ background: "rgba(255,255,255,0.04)" }}>
                    Go back
                  </button>
                </Link>
              </div>
            </div>

          ) : (
            /* ── Results state ── */
            <>
              {/* ── SCOUT Activation Banner ── */}
              <div
                className="rounded-2xl border mb-8 overflow-hidden"
                style={{ background: "rgba(255,176,0,0.04)", borderColor: "rgba(255,176,0,0.2)" }}
              >
                {/* Banner header */}
                <div className="px-6 py-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                  <div
                    className="h-11 w-11 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.3)" }}
                  >
                    <Bot className="h-5 w-5" style={{ color: "#FFB000" }} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold" style={{ color: "#FFB000" }}>SCOUT has activated your pipeline</span>
                      <span
                        className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full animate-pulse"
                        style={{ color: "#FFB000", background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.25)" }}
                      >
                        Live
                      </span>
                    </div>
                    <p className="text-xs text-white/40">
                      SCOUT scanned {totalFound} opportunities, scored each lead, and drafted outreach for {prospects.length} qualified prospects.
                      {robotCategory && <> Category detected: <span className="text-violet-300">{robotCategory}</span>.</>}
                    </p>
                  </div>
                </div>
                {/* SCOUT did / You do delineation */}
                <div className="grid grid-cols-2 border-t" style={{ borderColor: "rgba(255,176,0,0.12)" }}>
                  <div className="px-5 py-4 border-r" style={{ borderColor: "rgba(255,176,0,0.12)" }}>
                    <p className="text-[9px] font-bold uppercase tracking-widest mb-3" style={{ color: "rgba(255,176,0,0.6)" }}>SCOUT completed</p>
                    <div className="space-y-2">
                      {[
                        "Scanned 150+ signal sources",
                        "Matched prospects to your category",
                        "Scored each lead (6-factor model)",
                        "Drafted personalised outreach",
                      ].map((item) => (
                        <div key={item} className="flex items-center gap-2">
                          <CheckCircle2 className="h-3 w-3 shrink-0" style={{ color: "#FFB000" }} />
                          <span className="text-xs text-white/50">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="px-5 py-4">
                    <p className="text-[9px] font-bold uppercase tracking-widest mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>Your action</p>
                    <div className="space-y-2">
                      {[
                        { text: "Review matched prospects below", amber: false },
                        { text: "Approve outreach drafts", amber: false },
                        { text: "Activate Pipeline with SCOUT", amber: true },
                        { text: "SCOUT handles the rest", amber: true },
                      ].map((item, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full border shrink-0 flex items-center justify-center"
                            style={{ borderColor: item.amber ? "rgba(255,176,0,0.4)" : "rgba(255,255,255,0.3)" }}
                          >
                            {item.amber && <div className="h-1.5 w-1.5 rounded-full" style={{ background: "#FFB000" }} />}
                          </div>
                          <span className="text-xs" style={{ color: item.amber ? "rgba(255,176,0,0.8)" : "rgba(255,255,255,0.5)" }}>{item.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Results header */}
              <div className="mb-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-1" style={{ color: "#a78bfa" }}>
                      {totalFound} opportunities matched
                    </p>
                    <h1
                      className="font-extrabold text-white leading-tight"
                      style={{ fontSize: "clamp(1.6rem, 2.8vw, 2.2rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
                    >
                      Review &amp; activate your pipeline
                    </h1>
                    <p className="text-sm text-white/35 mt-1.5">
                      SCOUT drafted outreach for each lead. Review, then activate — SCOUT runs the sales process from here.
                    </p>
                  </div>
                  {/* Scan another URL */}
                  <div className="shrink-0">
                    {!showScanAnotherForm ? (
                      <button
                        onClick={() => setShowScanAnotherForm(true)}
                        className="flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl transition-all hover:-translate-y-0.5"
                        style={{ color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.12)", background: "transparent" }}
                      >
                        <RefreshCw className="h-3 w-3" /> Scan another URL
                      </button>
                    ) : (
                      <form
                        onSubmit={(e) => { e.preventDefault(); if (anotherUrl.trim()) startScan(anotherUrl); }}
                        className="flex items-center gap-2"
                      >
                        <input
                          type="text"
                          value={anotherUrl}
                          onChange={(e) => setAnotherUrl(e.target.value)}
                          placeholder="anothercompany.com"
                          className="w-44 px-3 py-2 text-xs text-white rounded-xl border border-white/15 bg-white/6 placeholder:text-white/25 focus:outline-none focus:ring-1 focus:ring-amber-500/40"
                          autoFocus
                        />
                        <button
                          type="submit"
                          className="flex items-center gap-1 text-xs font-bold px-3 py-2 rounded-xl transition-all"
                          style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
                        >
                          <Zap className="h-3 w-3" /> Scan
                        </button>
                        <button
                          type="button"
                          onClick={() => { setShowScanAnotherForm(false); setAnotherUrl(""); }}
                          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                        >
                          <X className="h-3.5 w-3.5 text-white/30" />
                        </button>
                      </form>
                    )}
                  </div>
                </div>
              </div>

              {/* Prospect cards */}
              <div className="space-y-4">
                {prospects.map((p, idx) => {
                  const { icon: SignalIcon, color: signalColor } = signalMeta(p.signalType);
                  const draftOpen = expandedDraft === idx;
                  return (
                    <div
                      key={idx}
                      className="rounded-2xl border border-white/8 overflow-hidden hover:border-violet-500/25 transition-colors"
                      style={{ background: "rgba(255,255,255,0.03)" }}
                    >
                      {/* Card header */}
                      <div className="px-6 pt-6 pb-4 flex flex-col sm:flex-row sm:items-start gap-4">
                        {/* Score ring */}
                        <div className="shrink-0 flex flex-col items-center gap-1">
                          <div
                            className="h-14 w-14 rounded-full border-2 flex items-center justify-center"
                            style={{ borderColor: scoreColor(p.score), background: `${scoreColor(p.score)}12` }}
                          >
                            <span
                              className="font-mono text-lg font-bold"
                              style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {p.score}
                            </span>
                          </div>
                          <span className="text-[9px] text-white/25 uppercase tracking-widest">score</span>
                        </div>

                        {/* Company info */}
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-white">{p.company}</h2>
                            <span
                              className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                              style={{ color: "#a78bfa", background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
                            >
                              {p.stage}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-white/35 mb-3">
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />{p.location}
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />{p.employees} employees
                            </span>
                            <span>{p.industry}</span>
                          </div>

                          {/* Signal */}
                          <div
                            className="flex items-start gap-2.5 p-3 rounded-xl"
                            style={{ background: `${signalColor}0d`, border: `1px solid ${signalColor}25` }}
                          >
                            <SignalIcon className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: signalColor }} />
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-widest mr-2" style={{ color: signalColor }}>
                                {p.signalType}
                              </span>
                              <span className="text-xs text-white/50">{p.signal}</span>
                            </div>
                          </div>

                          {/* Inferred contact email */}
                          {p.contactEmail && (
                            <div className="flex items-center gap-2 mt-2">
                              <Mail className="h-3 w-3 shrink-0" style={{ color: "rgba(3,218,197,0.6)" }} />
                              <span className="text-[10px] text-white/35">Suggested contact:</span>
                              <a
                                href={`mailto:${p.contactEmail}`}
                                className="text-[10px] font-mono hover:underline"
                                style={{ color: "#03DAC5", fontFamily: "'JetBrains Mono', monospace" }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {p.contactEmail}
                              </a>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Per-lead SCOUT process steps */}
                      <div className="px-6 py-3 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                        <div className="flex items-center gap-1 mb-2">
                          <Bot className="h-3 w-3" style={{ color: "rgba(255,176,0,0.5)" }} />
                          <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "rgba(255,176,0,0.5)" }}>SCOUT process</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {[
                            { label: "Signal detected", done: true, animating: false },
                            { label: "Qualified", done: true, animating: false },
                            { label: "Outreach drafted", done: true, animating: false },
                            { label: "Follow-up scheduled", done: addedIds.has(idx), animating: animatingIds.has(idx) },
                            { label: "Sent", done: false, animating: false },
                          ].map((step, si) => (
                            <div key={si}
                              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition-all duration-500"
                              style={{
                                background: step.animating
                                  ? "rgba(255,176,0,0.18)"
                                  : step.done ? "rgba(255,176,0,0.07)" : "rgba(255,255,255,0.03)",
                                border: `1px solid ${step.animating ? "rgba(255,176,0,0.5)" : step.done ? "rgba(255,176,0,0.2)" : "rgba(255,255,255,0.07)"}`,
                                boxShadow: step.animating ? "0 0 12px rgba(255,176,0,0.25)" : "none",
                              }}
                            >
                              {step.done
                                ? <CheckCircle2
                                    className={`h-2.5 w-2.5 transition-all duration-300 ${step.animating ? "scale-125" : ""}`}
                                    style={{ color: step.animating ? "#FFD700" : "#FFB000" }}
                                  />
                                : <div className="h-2.5 w-2.5 rounded-full border" style={{ borderColor: "rgba(255,255,255,0.2)" }} />
                              }
                              <span
                                className="text-[9px] font-semibold transition-colors duration-300"
                                style={{ color: step.animating ? "#FFD700" : step.done ? "rgba(255,176,0,0.8)" : "rgba(255,255,255,0.25)" }}
                              >
                                {step.label}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* SCOUT action label + Activate Pipeline with SCOUT */}
                      <div className="px-6 pb-4 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 pt-4">
                          {/* SCOUT recommendation */}
                          <div className="flex items-start gap-2 flex-1">
                            <Bot className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: "#FFB000" }} />
                            <div>
                              <span className="text-[9px] font-bold uppercase tracking-widest mr-1.5" style={{ color: "rgba(255,176,0,0.6)" }}>SCOUT recommends</span>
                              <span className="text-xs text-white/55">{p.action}</span>
                              <span
                                className="ml-2 text-[9px] font-bold px-1.5 py-0.5 rounded"
                                style={{ color: "#FFB000", background: "rgba(255,176,0,0.1)" }}
                              >
                                {p.timing}
                              </span>
                            </div>
                          </div>
                          {/* Activate Pipeline with SCOUT — amber stroke, no fill */}
                          <button
                            onClick={() => handleAddToPipeline(p, idx)}
                            disabled={addToPipeline.isPending && !addedIds.has(idx)}
                            className="shrink-0 flex items-center gap-1.5 text-xs font-bold px-4 py-2.5 rounded-xl transition-all hover:-translate-y-0.5 disabled:opacity-60"
                            style={addedIds.has(idx)
                              ? { color: "#34d399", border: "1.5px solid rgba(52,211,153,0.5)", background: "transparent" }
                              : { color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }
                            }
                          >
                            {addedIds.has(idx) ? (
                              <><CheckCircle2 className="h-3.5 w-3.5" /> In Pipeline</>
                            ) : (
                              <><Zap className="h-3.5 w-3.5" /> Activate Pipeline with SCOUT</>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Draft outreach toggle */}
                      <div className="border-t border-white/6">
                        <button
                          onClick={() => setExpandedDraft(draftOpen ? null : idx)}
                          className="w-full flex items-center justify-between px-6 py-3.5 text-left hover:bg-white/2 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-3.5 w-3.5" style={{ color: "#7c3aed" }} />
                            <span className="text-xs font-semibold" style={{ color: "#a78bfa" }}>SCOUT-drafted outreach</span>
                          </div>
                          {draftOpen
                            ? <ChevronUp className="h-3.5 w-3.5 text-white/25" />
                            : <ChevronDown className="h-3.5 w-3.5 text-white/25" />
                          }
                        </button>
                        {draftOpen && (
                          <div className="px-6 pb-5 border-t border-white/6">
                            <pre
                              className="text-xs text-white/50 leading-relaxed whitespace-pre-wrap pt-4"
                              style={{ fontFamily: "'JetBrains Mono', monospace" }}
                            >
                              {p.draft}
                            </pre>
                            <div className="flex gap-2 mt-4">
                              <button
                                onClick={() => handleAddToPipeline(p, idx)}
                                className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5 hover:bg-teal-400/8"
                                style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
                              >
                                <Zap className="h-3.5 w-3.5" /> Activate Pipeline with SCOUT
                              </button>
                              <button
                                onClick={() => toast.info("Opening editor…")}
                                className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg text-white/60 border border-white/10 hover:border-white/20 transition-colors"
                                style={{ background: "rgba(255,255,255,0.04)" }}
                              >
                                Edit draft
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Locked prospects section */}
              {lockedTeasers.length > 0 && (
                <div ref={lockedRef} className="mt-6 relative">
                  {/* Unlock banner */}
                  {!modalSubmitted && (
                    <div
                      className="relative z-10 rounded-2xl border p-6 mb-4 flex flex-col sm:flex-row items-center gap-4"
                      style={{ background: "rgba(124,58,237,0.08)", borderColor: "rgba(124,58,237,0.3)" }}
                    >
                      <div className="h-10 w-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: "rgba(124,58,237,0.15)" }}>
                        <Lock className="h-5 w-5" style={{ color: "#a78bfa" }} />
                      </div>
                      <div className="flex-1 text-center sm:text-left">
                        <p className="text-sm font-bold text-white mb-0.5">
                          {lockedTeasers.length} more opportunities found
                        </p>
                        <p className="text-xs text-white/40">
                          Enter your email to unlock the full pipeline — no credit card required.
                        </p>
                      </div>
                      <button
                        onClick={() => setShowModal(true)}
                        className="shrink-0 flex items-center gap-2 font-semibold text-sm px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5 hover:bg-teal-400/8"
                        style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "transparent" }}
                      >
                        Unlock full pipeline <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Blurred locked cards */}
                  <div className={`space-y-3 ${!modalSubmitted ? "pointer-events-none" : ""}`}>
                    {lockedTeasers.map((p, i) => (
                      <div
                        key={i}
                        className="rounded-2xl border border-white/6 px-6 py-5 flex items-center gap-4"
                        style={{
                          background: "rgba(255,255,255,0.02)",
                          filter: modalSubmitted ? "none" : "blur(4px)",
                          opacity: modalSubmitted ? 1 : 0.6,
                          transition: "filter 0.5s, opacity 0.5s",
                        }}
                      >
                        <div
                          className="h-12 w-12 rounded-full border-2 flex items-center justify-center shrink-0"
                          style={{ borderColor: scoreColor(p.score), background: `${scoreColor(p.score)}12` }}
                        >
                          <span className="font-mono text-base font-bold" style={{ color: scoreColor(p.score), fontFamily: "'JetBrains Mono', monospace" }}>
                            {p.score}
                          </span>
                        </div>
                        <div className="flex-1">
                          <div className="h-3 w-32 rounded-full mb-2" style={{ background: "rgba(255,255,255,0.12)" }} />
                          <div className="flex items-center gap-3 text-xs text-white/30">
                            <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>
                            <span>{p.industry}</span>
                          </div>
                        </div>
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                          style={{ color: "#a78bfa", background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
                        >
                          {p.signalType}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Gradient fade over locked cards */}
                  {!modalSubmitted && (
                    <div
                      className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none rounded-b-2xl"
                      style={{ background: "linear-gradient(to bottom, transparent, #0d0520)" }}
                    />
                  )}
                </div>
              )}

              {/* spacer so sticky banner doesn't cover last card */}
              {addedIds.size > 0 && <div className="h-20" />}

              {/* Post-unlock CTA */}
              {modalSubmitted && (
                <div
                  className="mt-8 rounded-2xl border border-teal-500/20 p-8 text-center"
                  style={{ background: "rgba(3,218,197,0.05)" }}
                >
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-3" style={{ color: "#03DAC5" }} />
                  <h3 className="font-bold text-white text-lg mb-2" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                    Full pipeline unlocked
                  </h3>
                  <p className="text-sm text-white/40 mb-5">
                    SCOUT is building your complete matched pipeline. Check your inbox for the full report.
                  </p>
                  <Link href="/pipeline">
                    <button
                      className="inline-flex items-center gap-2 font-semibold text-sm px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5 hover:bg-teal-400/8"
                      style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "transparent" }}
                    >
                      View your pipeline <ArrowRight className="h-4 w-4" />
                    </button>
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Sticky "View Pipeline" banner — appears after first lead is activated */}
      {addedIds.size > 0 && (
        <div
          className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-between gap-4 px-6 py-4 border-t"
          style={{
            background: "rgba(13,5,32,0.92)",
            backdropFilter: "blur(16px)",
            borderColor: "rgba(255,176,0,0.25)",
            boxShadow: "0 -4px 32px rgba(255,176,0,0.08)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.25)" }}
            >
              <CheckCircle2 className="h-4 w-4" style={{ color: "#FFB000" }} />
            </div>
            <div>
              <p className="text-sm font-bold text-white">
                {addedIds.size} lead{addedIds.size > 1 ? "s" : ""} activated
              </p>
              <p className="text-xs text-white/35">SCOUT is running your pipeline</p>
            </div>
          </div>
          <Link href="/pipeline">
            <button
              className="flex items-center gap-2 text-sm font-bold px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
              style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
            >
              View Pipeline <ArrowRight className="h-4 w-4" />
            </button>
          </Link>
        </div>
      )}

      {/* Lead capture modal */}
      {showModal && !modalSubmitted && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
        >
          <div
            className="relative w-full max-w-md rounded-2xl border border-white/10 p-8 shadow-2xl"
            style={{ background: "#130828" }}
          >
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-white/30 hover:text-white/60 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            <div
              className="h-12 w-12 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: "rgba(3,218,197,0.12)", border: "1px solid rgba(3,218,197,0.25)" }}
            >
              <Handshake className="h-6 w-6" style={{ color: "#03DAC5" }} />
            </div>

            <h2
              className="font-extrabold text-white mb-2"
              style={{ fontSize: "1.4rem", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Unlock your full pipeline
            </h2>
            <p className="text-sm text-white/45 mb-6 leading-relaxed">
              SCOUT found <strong className="text-white">{lockedTeasers.length} more matched opportunities</strong> for{" "}
              <span className="font-medium" style={{ color: "#03DAC5" }}>{inputUrl}</span>. Enter your details to get the full report — no credit card, no commitment.
            </p>

            <form onSubmit={handleLeadSubmit} className="flex flex-col gap-3">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className="w-full px-4 py-3 text-sm text-white rounded-xl border border-white/10 bg-white/5 placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-teal-500/40 transition"
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Work email"
                className="w-full px-4 py-3 text-sm text-white rounded-xl border border-white/10 bg-white/5 placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-teal-500/40 transition"
              />
              <button
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 font-semibold text-sm py-3.5 rounded-xl transition-all hover:-translate-y-0.5 hover:bg-teal-400/8 disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "transparent" }}
              >
                {submitting ? "Unlocking…" : <>Get full pipeline <ArrowRight className="h-4 w-4" /></>}
              </button>
            </form>

            <p className="text-[11px] text-white/20 text-center mt-4">
              No spam. No credit card. Unsubscribe any time.
            </p>

            <div className="mt-5 pt-4 border-t border-white/6 flex items-center justify-center gap-4">
              {[
                { value: "500+", label: "deals influenced" },
                { value: "60+", label: "companies served" },
                { value: "14-day", label: "free trial" },
              ].map((s) => (
                <div key={s.label} className="text-center">
                  <p className="font-mono text-sm font-bold" style={{ color: "#a78bfa", fontFamily: "'JetBrains Mono', monospace" }}>{s.value}</p>
                  <p className="text-[10px] text-white/25">{s.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {/* Onboarding modal — shown once on first pipeline activation */}
      {showOnboarding && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(10px)" }}
        >
          <div
            className="relative w-full max-w-lg rounded-2xl border p-8 shadow-2xl"
            style={{ background: "#130828", borderColor: "rgba(255,176,0,0.3)" }}
          >
            <button
              onClick={() => setShowOnboarding(false)}
              className="absolute top-4 right-4 text-white/30 hover:text-white/60 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            {/* SCOUT avatar */}
            <div className="flex items-center gap-3 mb-6">
              <div
                className="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0"
                style={{ background: "rgba(255,176,0,0.12)", border: "1.5px solid rgba(255,176,0,0.4)" }}
              >
                <Bot className="h-6 w-6" style={{ color: "#FFB000" }} />
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest mb-0.5" style={{ color: "#FFB000" }}>SCOUT</p>
                <h2 className="text-xl font-extrabold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
                  Your pipeline is now active
                </h2>
              </div>
            </div>

            <p className="text-sm text-white/55 leading-relaxed mb-6">
              SCOUT has taken over your sales process. Here's what happens next — automatically.
            </p>

            {/* What SCOUT does vs. what you do */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div
                className="rounded-xl p-4"
                style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.15)" }}
              >
                <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#FFB000" }}>SCOUT handles</p>
                {[
                  "Monitors for new signals daily",
                  "Scores & qualifies each lead",
                  "Drafts outreach per signal",
                  "Schedules follow-ups automatically",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-2 mb-2">
                    <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color: "#FFB000" }} />
                    <span className="text-xs text-white/60">{item}</span>
                  </div>
                ))}
              </div>
              <div
                className="rounded-xl p-4"
                style={{ background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.15)" }}
              >
                <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#a78bfa" }}>You approve</p>
                {[
                  "Review drafted outreach",
                  "One-click send or edit",
                  "See pipeline in real time",
                  "Close the deal",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-2 mb-2">
                    <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color: "#a78bfa" }} />
                    <span className="text-xs text-white/60">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Link href="/pipeline" className="flex-1">
                <button
                  className="w-full flex items-center justify-center gap-2 text-sm font-bold py-3 rounded-xl transition-all hover:-translate-y-0.5"
                  style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
                  onClick={() => setShowOnboarding(false)}
                >
                  View Pipeline <ArrowRight className="h-4 w-4" />
                </button>
              </Link>
              <button
                onClick={() => setShowOnboarding(false)}
                className="px-5 py-3 rounded-xl text-sm font-medium text-white/40 hover:text-white/60 transition-colors"
                style={{ border: "1px solid rgba(255,255,255,0.08)" }}
              >
                Continue scanning
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
