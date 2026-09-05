/**
 * ScoutSettings — Pipeline Mode, Persona, and outreach timing settings.
 * Accessible from the hamburger menu. Settings are persisted via tRPC.
 */
import { useState, useEffect } from "react";
import { Zap, Bot, Building2, User, Clock, ChevronRight, Save, CheckCircle2, Info, Loader2, Lock } from "lucide-react";
import Header from "@/components/Header";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { getLoginUrl } from "@/const";

type PipelineMode = "assisted" | "autopilot";
type PersonaMode = "company" | "scout";

const SCORE_FACTORS = [
  { key: "readiness",   label: "Readiness to Buy",      weight: 25, tier: 1, desc: "Timing signals: hiring, CapEx announcements, expansion plans" },
  { key: "useCase",     label: "Use Case Clarity",       weight: 20, tier: 1, desc: "How well-defined the automation opportunity is" },
  { key: "roi",         label: "Achievable ROI",         weight: 15, tier: 1, desc: "Labor cost vs. robot cost math — is the payback period < 24 months?" },
  { key: "deployment",  label: "Deployment Scale",       weight: 15, tier: 2, desc: "Number of units, facilities, or robots in scope" },
  { key: "problem",     label: "Recognizable Problem",   weight: 15, tier: 2, desc: "Is this a known, documented pain point in the industry?" },
  { key: "customer",    label: "Customer Value",         weight: 10, tier: 2, desc: "Brand recognition, company size, reference account potential" },
];

const OUTREACH_STEPS = [
  { label: "Intro email",     channel: "Email",    delay: "Within 24h of signal detection" },
  { label: "Follow-up #1",    channel: "Email",    delay: "2 days if no reply" },
  { label: "LinkedIn touch",  channel: "LinkedIn", delay: "5 days if no reply" },
  { label: "Final follow-up", channel: "Email",    delay: "14 days if no reply" },
];

export default function ScoutSettings() {
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [pipelineMode, setPipelineMode] = useState<PipelineMode>("assisted");
  const [personaMode, setPersonaMode] = useState<PersonaMode>("company");
  const [companyName, setCompanyName] = useState("");
  const [senderName, setSenderName] = useState("");
  const [senderTitle, setSenderTitle] = useState("");
  const [saved, setSaved] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Load saved settings from backend
  const { data: savedSettings, isLoading: settingsLoading } = trpc.settings.get.useQuery(
    undefined,
    { enabled: isAuthenticated, retry: false }
  );

  // Populate form when data arrives
  useEffect(() => {
    if (!savedSettings) return;
    setPipelineMode(savedSettings.defaultPipelineMode as PipelineMode);
    setPersonaMode(savedSettings.outreachPersona === "on_behalf" ? "company" : "scout");
    setCompanyName(savedSettings.senderCompanyName ?? "");
    setSenderName(savedSettings.senderName ?? "");
    setSenderTitle(savedSettings.senderTitle ?? "");
  }, [savedSettings]);

  const utils = trpc.useUtils();
  const saveMutation = trpc.settings.save.useMutation({
    onSuccess: (result) => {
      if (result?.success) {
        setSaved(true);
        toast.success("SCOUT settings saved");
        utils.settings.get.invalidate();
        setTimeout(() => setSaved(false), 2500);
      } else {
        toast.error("Could not save settings — please try again");
      }
    },
    onError: () => {
      toast.error("Failed to save settings");
    },
  });

  const handleSave = () => {
    setValidationError(null);
    // Validate required fields for company persona
    if (personaMode === "company") {
      if (!companyName.trim()) {
        setValidationError("Company Name is required when using Your Company persona.");
        return;
      }
      if (!senderName.trim()) {
        setValidationError("Sender Name is required when using Your Company persona.");
        return;
      }
    }
    saveMutation.mutate({
      defaultPipelineMode: pipelineMode,
      outreachPersona: personaMode === "company" ? "on_behalf" : "independent",
      senderCompanyName: companyName.trim() || undefined,
      senderName: senderName.trim() || undefined,
      senderTitle: senderTitle.trim() || undefined,
    });
  };

  const isLoading = authLoading || settingsLoading;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />

      <main className="flex-1 pt-24 pb-12 px-4 lg:px-6">
        <div className="max-w-2xl mx-auto flex flex-col gap-8">

          {/* Page header */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] mb-1" style={{ color: "#a78bfa" }}>
              Configuration
            </p>
            <h1 className="font-extrabold text-white text-2xl mb-1" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
              SCOUT Settings
            </h1>
            <p className="text-sm" style={{ color: "rgba(255,255,255,0.4)" }}>
              Control how SCOUT qualifies leads, sends outreach, and represents your company.
            </p>
          </div>

          {/* Auth gate */}
          {!authLoading && !isAuthenticated && (
            <div
              className="flex flex-col items-center gap-4 py-10 rounded-2xl border text-center"
              style={{ borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}
            >
              <Lock className="h-8 w-8" style={{ color: "rgba(255,255,255,0.25)" }} />
              <div>
                <p className="text-sm font-semibold text-white/70 mb-1">Sign in to save your settings</p>
                <p className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
                  Settings are persisted to your account. You can still explore the options below.
                </p>
              </div>
              <a
                href={getLoginUrl()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all"
                style={{ background: "rgba(255,176,0,0.1)", color: "#FFB000", border: "1px solid rgba(255,176,0,0.35)" }}
              >
                Sign in to save settings
              </a>
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin" style={{ color: "#a78bfa" }} />
            </div>
          )}

          {/* Settings form — always visible, but save is gated */}
          {!authLoading && (
            <>
              {/* ── SECTION 1: Pipeline Mode ── */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="h-4 w-4" style={{ color: "#FFB000" }} />
                  <h2 className="text-sm font-bold text-white">Pipeline Mode</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Assisted */}
                  <button
                    onClick={() => setPipelineMode("assisted")}
                    className="text-left p-4 rounded-xl border transition-all"
                    style={
                      pipelineMode === "assisted"
                        ? { borderColor: "#a78bfa", background: "rgba(167,139,250,0.08)" }
                        : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }
                    }
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" style={{ color: "#a78bfa" }} />
                        <span className="text-sm font-bold text-white">Assisted</span>
                      </div>
                      {pipelineMode === "assisted" && (
                        <CheckCircle2 className="h-4 w-4" style={{ color: "#a78bfa" }} />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: "rgba(255,255,255,0.45)" }}>
                      SCOUT drafts outreach and queues it for your approval. You review and send each message. Full control, no surprises.
                    </p>
                    <div className="mt-3 flex items-center gap-1.5">
                      <span
                        className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
                        style={{ background: "rgba(167,139,250,0.12)", color: "#a78bfa" }}
                      >
                        Default
                      </span>
                    </div>
                  </button>

                  {/* Auto-pilot */}
                  <button
                    onClick={() => setPipelineMode("autopilot")}
                    className="text-left p-4 rounded-xl border transition-all"
                    style={
                      pipelineMode === "autopilot"
                        ? { borderColor: "#03DAC5", background: "rgba(3,218,197,0.06)" }
                        : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }
                    }
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4" style={{ color: "#03DAC5" }} />
                        <span className="text-sm font-bold text-white">Auto-pilot</span>
                      </div>
                      {pipelineMode === "autopilot" && (
                        <CheckCircle2 className="h-4 w-4" style={{ color: "#03DAC5" }} />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: "rgba(255,255,255,0.45)" }}>
                      SCOUT sends the first outreach automatically within 24h of a signal. You see everything in the pipeline — no approval needed per message.
                    </p>
                    <div className="mt-3 flex items-center gap-1.5">
                      <span
                        className="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
                        style={{ background: "rgba(3,218,197,0.1)", color: "#03DAC5" }}
                      >
                        Recommended
                      </span>
                    </div>
                  </button>
                </div>

                {pipelineMode === "autopilot" && (
                  <div
                    className="mt-3 flex items-start gap-2 p-3 rounded-xl text-[11px]"
                    style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.15)", color: "rgba(255,255,255,0.5)" }}
                  >
                    <Info className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: "#FFB000" }} />
                    <span>
                      In Auto-pilot mode, SCOUT sends outreach on your behalf using your configured persona. You can pause any individual lead at any time from the Pipeline page.
                    </span>
                  </div>
                )}
              </section>

              {/* ── SECTION 2: Outreach Sequence ── */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="h-4 w-4" style={{ color: "#03DAC5" }} />
                  <h2 className="text-sm font-bold text-white">Outreach Sequence</h2>
                  <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.25)" }}>· applies to all leads</span>
                </div>

                <div
                  className="rounded-xl overflow-hidden"
                  style={{ border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}
                >
                  {OUTREACH_STEPS.map((step, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-4 px-4 py-3"
                      style={i < OUTREACH_STEPS.length - 1 ? { borderBottom: "1px solid rgba(255,255,255,0.05)" } : {}}
                    >
                      <div
                        className="h-6 w-6 rounded-full flex items-center justify-center shrink-0 font-mono text-[10px] font-bold"
                        style={{ background: "rgba(3,218,197,0.1)", color: "#03DAC5", border: "1px solid rgba(3,218,197,0.2)" }}
                      >
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-[12px] font-semibold text-white/80">{step.label}</span>
                        <span
                          className="ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide"
                          style={
                            step.channel === "LinkedIn"
                              ? { background: "rgba(96,165,250,0.12)", color: "#60a5fa" }
                              : { background: "rgba(167,139,250,0.12)", color: "#a78bfa" }
                          }
                        >
                          {step.channel}
                        </span>
                      </div>
                      <span className="text-[11px] shrink-0" style={{ color: "rgba(255,255,255,0.3)" }}>
                        {step.delay}
                      </span>
                      <ChevronRight className="h-3.5 w-3.5 shrink-0" style={{ color: "rgba(255,255,255,0.15)" }} />
                    </div>
                  ))}
                </div>
              </section>

              {/* ── SECTION 3: SCOUT Score Weights ── */}
              <section>
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="h-4 w-4" style={{ color: "#a78bfa" }} />
                  <h2 className="text-sm font-bold text-white">SCOUT Score Criteria</h2>
                </div>
                <p className="text-[11px] mb-4" style={{ color: "rgba(255,255,255,0.3)" }}>
                  Every lead is scored 0–100 across six factors. Tier 1 factors determine deal quality; Tier 2 factors determine deal value.
                </p>

                <div
                  className="rounded-xl overflow-hidden"
                  style={{ border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}
                >
                  {/* Tier 1 */}
                  <div className="px-4 py-2" style={{ background: "rgba(3,218,197,0.04)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "#03DAC5" }}>
                      Tier 1 — Deal Quality (60 pts)
                    </span>
                  </div>
                  {SCORE_FACTORS.filter((f) => f.tier === 1).map((f, i, arr) => (
                    <div
                      key={f.key}
                      className="flex items-start gap-3 px-4 py-3"
                      style={i < arr.length - 1 ? { borderBottom: "1px solid rgba(255,255,255,0.04)" } : {}}
                    >
                      <div
                        className="h-6 w-10 rounded flex items-center justify-center shrink-0 font-mono text-[10px] font-bold"
                        style={{ background: "rgba(3,218,197,0.1)", color: "#03DAC5" }}
                      >
                        /{f.weight}
                      </div>
                      <div>
                        <p className="text-[12px] font-semibold text-white/80">{f.label}</p>
                        <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>{f.desc}</p>
                      </div>
                    </div>
                  ))}

                  {/* Tier 2 */}
                  <div className="px-4 py-2" style={{ background: "rgba(167,139,250,0.04)", borderTop: "1px solid rgba(255,255,255,0.06)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "#a78bfa" }}>
                      Tier 2 — Deal Value (40 pts)
                    </span>
                  </div>
                  {SCORE_FACTORS.filter((f) => f.tier === 2).map((f, i, arr) => (
                    <div
                      key={f.key}
                      className="flex items-start gap-3 px-4 py-3"
                      style={i < arr.length - 1 ? { borderBottom: "1px solid rgba(255,255,255,0.04)" } : {}}
                    >
                      <div
                        className="h-6 w-10 rounded flex items-center justify-center shrink-0 font-mono text-[10px] font-bold"
                        style={{ background: "rgba(167,139,250,0.1)", color: "#a78bfa" }}
                      >
                        /{f.weight}
                      </div>
                      <div>
                        <p className="text-[12px] font-semibold text-white/80">{f.label}</p>
                        <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>{f.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* ── SECTION 4: Outreach Persona ── */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Building2 className="h-4 w-4" style={{ color: "#FFB000" }} />
                  <h2 className="text-sm font-bold text-white">Outreach Persona</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                  {/* On behalf of company */}
                  <button
                    onClick={() => { setPersonaMode("company"); setValidationError(null); }}
                    className="text-left p-4 rounded-xl border transition-all"
                    style={
                      personaMode === "company"
                        ? { borderColor: "#FFB000", background: "rgba(255,176,0,0.06)" }
                        : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }
                    }
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4" style={{ color: "#FFB000" }} />
                        <span className="text-sm font-bold text-white">Your Company</span>
                      </div>
                      {personaMode === "company" && (
                        <CheckCircle2 className="h-4 w-4" style={{ color: "#FFB000" }} />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: "rgba(255,255,255,0.45)" }}>
                      SCOUT sends outreach as a named rep from your company. Prospects see your brand and sender name.
                    </p>
                  </button>

                  {/* Independent SCOUT */}
                  <button
                    onClick={() => { setPersonaMode("scout"); setValidationError(null); }}
                    className="text-left p-4 rounded-xl border transition-all"
                    style={
                      personaMode === "scout"
                        ? { borderColor: "#a78bfa", background: "rgba(167,139,250,0.06)" }
                        : { borderColor: "rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }
                    }
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4" style={{ color: "#a78bfa" }} />
                        <span className="text-sm font-bold text-white">SCOUT (Independent)</span>
                      </div>
                      {personaMode === "scout" && (
                        <CheckCircle2 className="h-4 w-4" style={{ color: "#a78bfa" }} />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: "rgba(255,255,255,0.45)" }}>
                      SCOUT reaches out as ReadyForRobots SCOUT — an AI sales agent. Transparent, no impersonation, and clearly AI-driven.
                    </p>
                  </button>
                </div>

                {/* Company persona fields */}
                {personaMode === "company" && (
                  <div className="flex flex-col gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold mb-1.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                        Company Name <span style={{ color: "#f87171" }}>*</span>
                      </label>
                      <input
                        type="text"
                        value={companyName}
                        onChange={(e) => { setCompanyName(e.target.value); setValidationError(null); }}
                        placeholder="e.g. Apex Robotics Inc."
                        className="w-full px-3 py-2.5 text-sm text-white rounded-xl border bg-transparent placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-violet-500/40 transition"
                        style={{
                          borderColor: validationError && !companyName.trim() ? "#f87171" : "rgba(255,255,255,0.1)",
                          background: "rgba(255,255,255,0.03)"
                        }}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold mb-1.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                          Sender Name <span style={{ color: "#f87171" }}>*</span>
                        </label>
                        <input
                          type="text"
                          value={senderName}
                          onChange={(e) => { setSenderName(e.target.value); setValidationError(null); }}
                          placeholder="e.g. Alex Johnson"
                          className="w-full px-3 py-2.5 text-sm text-white rounded-xl border bg-transparent placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-violet-500/40 transition"
                          style={{
                            borderColor: validationError && !senderName.trim() ? "#f87171" : "rgba(255,255,255,0.1)",
                            background: "rgba(255,255,255,0.03)"
                          }}
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold mb-1.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                          Sender Title
                        </label>
                        <input
                          type="text"
                          value={senderTitle}
                          onChange={(e) => setSenderTitle(e.target.value)}
                          placeholder="e.g. VP of Sales"
                          className="w-full px-3 py-2.5 text-sm text-white rounded-xl border bg-transparent placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-violet-500/40 transition"
                          style={{ borderColor: "rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.03)" }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Validation error */}
                {validationError && (
                  <div
                    className="mt-3 flex items-center gap-2 p-3 rounded-xl text-[11px]"
                    style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.25)", color: "#f87171" }}
                  >
                    <Info className="h-3.5 w-3.5 shrink-0" />
                    {validationError}
                  </div>
                )}
              </section>

              {/* Save button */}
              <div className="flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={saveMutation.isPending || !isAuthenticated}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  style={
                    saved
                      ? { background: "rgba(3,218,197,0.1)", color: "#03DAC5", border: "1px solid rgba(3,218,197,0.3)" }
                      : { background: "rgba(255,176,0,0.08)", color: "#FFB000", border: "1px solid rgba(255,176,0,0.35)" }
                  }
                >
                  {saveMutation.isPending
                    ? <Loader2 className="h-4 w-4 animate-spin" />
                    : saved
                      ? <CheckCircle2 className="h-4 w-4" />
                      : <Save className="h-4 w-4" />
                  }
                  {saveMutation.isPending ? "Saving…" : saved ? "Saved!" : "Save Settings"}
                </button>
              </div>
            </>
          )}

        </div>
      </main>
    </div>
  );
}
