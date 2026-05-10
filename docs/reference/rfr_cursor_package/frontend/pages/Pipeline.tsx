/**
 * Pipeline — ReadyForRobots CRM Board
 * Fully automated workflow: leads added from Results page appear here with
 * outreach drafts queued. One-click "Approve & Send" advances the stage in the DB.
 */
import { useState, useEffect } from "react";
import {
  ArrowRight, Zap, AlertTriangle, CheckCircle2,
  Clock, Target, MoreHorizontal, Archive, ToggleLeft, ToggleRight,
  Plus, RefreshCw, Building2, TrendingUp, ChevronDown, ChevronUp,
  FileText, Bot, Mail, X, Sparkles, Copy, Download,
} from "lucide-react";
import { Link } from "wouter";
import Header from "@/components/Header";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { getLoginUrl } from "@/const";

type Deal = {
  id: number;
  companyName: string;
  companyUrl?: string | null;
  industry?: string | null;
  robotCategory?: string | null;
  opportunityType: "sales_lead" | "partnership";
  signal?: string | null;
  signalSource?: string | null;
  scoutScore: number;
  pipelineMode: "assisted" | "autopilot";
  outreachStage: string;
  introSentAt?: number | null;
  followupSentAt?: number | null;
  linkedinSentAt?: number | null;
  finalSentAt?: number | null;
  scoreNotes?: Record<string, string> | null;
  createdAt?: number | null;
  contactEmail?: string | null;
};

const scoreColor = (s: number) =>
  s >= 90 ? "#03DAC5" : s >= 75 ? "#a78bfa" : "#fb923c";

// ── Shared: build PDF blob from proposal data ─────────────────────────────────
async function fetchPdfBlob(data: {
  proposal: string;
  companyName: string;
  senderCompany: string;
  senderName: string;
  senderTitle: string;
  generatedAt: number;
}, deal: Deal): Promise<Blob> {
  const res = await fetch("/api/proposal/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      companyName: data.companyName,
      senderCompany: data.senderCompany,
      senderName: data.senderName,
      senderTitle: data.senderTitle,
      robotCategory: deal.robotCategory ?? undefined,
      signal: deal.signal ?? undefined,
      scoutScore: deal.scoutScore,
      proposalText: data.proposal,
      generatedAt: data.generatedAt,
      inline: true,
    }),
  });
  if (!res.ok) throw new Error("PDF generation failed");
  return res.blob();
}

// ── PDF Preview Modal ─────────────────────────────────────────────────────────
function PdfPreviewModal({
  open,
  onClose,
  data,
  deal,
}: {
  open: boolean;
  onClose: () => void;
  data: { proposal: string; companyName: string; senderCompany: string; senderName: string; senderTitle: string; generatedAt: number };
  deal: Deal;
}) {
  // Editor state — initialised from the proposal text when modal opens
  const [editorText, setEditorText] = useState("");
  // The text that was last rendered into the current PDF blob
  const [renderedText, setRenderedText] = useState("");
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // Derived: editor has unsaved changes relative to the last render
  const isDirty = editorText !== renderedText && renderedText !== "";

  // Helper: generate PDF from a given text and update blob URL
  const renderPdf = async (text: string, signal?: AbortSignal) => {
    const overrideData = { ...data, proposal: text };
    const res = await fetch("/api/proposal/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      signal,
      body: JSON.stringify({
        companyName: overrideData.companyName,
        senderCompany: overrideData.senderCompany,
        senderName: overrideData.senderName,
        senderTitle: overrideData.senderTitle,
        robotCategory: deal.robotCategory ?? undefined,
        signal: deal.signal ?? undefined,
        scoutScore: deal.scoutScore,
        proposalText: text,
        generatedAt: overrideData.generatedAt,
        inline: true,
      }),
    });
    if (!res.ok) throw new Error("PDF generation failed");
    return res.blob();
  };

  // Initial render when modal opens
  useEffect(() => {
    if (!open) return;
    const text = data.proposal;
    setEditorText(text);
    setRenderedText("");
    setLoading(true);
    setError(false);
    setBlobUrl(null);
    let cancelled = false;
    const controller = new AbortController();
    renderPdf(text, controller.signal)
      .then((blob) => {
        if (!cancelled) {
          setBlobUrl(URL.createObjectURL(blob));
          setRenderedText(text);
        }
      })
      .catch(() => { if (!cancelled) setError(true); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => {
      cancelled = true;
      controller.abort();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // "Update Preview" — re-render with current editor text
  const handleUpdatePreview = async () => {
    setUpdating(true);
    setError(false);
    try {
      const blob = await renderPdf(editorText);
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      setBlobUrl(URL.createObjectURL(blob));
      setRenderedText(editorText);
    } catch {
      toast.error("Failed to update preview — please try again");
    } finally {
      setUpdating(false);
    }
  };

  // Download uses the latest rendered blob URL directly (no extra fetch)
  const handleDownload = async () => {
    if (!blobUrl) return;
    setDownloading(true);
    try {
      // Re-fetch with attachment disposition for a clean download
      const blob = await renderPdf(renderedText || editorText);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.companyName.replace(/[^a-z0-9]/gi, "-").toLowerCase()}-proposal.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Proposal PDF downloaded");
    } catch {
      toast.error("Failed to download PDF — please try again");
    } finally {
      setDownloading(false);
    }
  };

  const handleClose = () => {
    if (blobUrl) URL.revokeObjectURL(blobUrl);
    setBlobUrl(null);
    onClose();
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col"
      style={{ background: "#080415" }}
    >
      {/* ── Top bar ── */}
      <div
        className="flex items-center justify-between px-5 py-3 shrink-0"
        style={{ background: "#0d0520", borderBottom: "1px solid rgba(255,176,0,0.2)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="h-7 w-7 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.3)" }}
          >
            <FileText className="h-3.5 w-3.5" style={{ color: "#FFB000" }} />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-tight">Edit &amp; Preview Proposal</p>
            <p className="text-[10px] text-white/35">{data.companyName}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Dirty indicator */}
          {isDirty && (
            <span className="text-[10px] font-semibold px-2 py-1 rounded" style={{ color: "#FFB000", background: "rgba(255,176,0,0.1)", border: "1px solid rgba(255,176,0,0.25)" }}>
              Unsaved changes
            </span>
          )}
          <button
            onClick={handleDownload}
            disabled={downloading || loading || updating || !blobUrl}
            className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5 disabled:opacity-50"
            style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.45)", background: "rgba(255,176,0,0.07)" }}
          >
            {downloading ? (
              <><div className="h-3 w-3 rounded-full border-2 border-amber-400/40 border-t-amber-400 animate-spin" /> Saving…</>
            ) : (
              <><Download className="h-3.5 w-3.5" /> Download PDF</>
            )}
          </button>
          <button onClick={handleClose} className="p-1.5 rounded-lg hover:bg-white/5 transition-colors">
            <X className="h-4 w-4 text-white/40" />
          </button>
        </div>
      </div>

      {/* ── Split pane body ── */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">

        {/* Left: Editor */}
        <div
          className="flex flex-col lg:w-[42%] shrink-0 border-b lg:border-b-0 lg:border-r overflow-hidden"
          style={{ borderColor: "rgba(255,255,255,0.07)" }}
        >
          {/* Editor header */}
          <div
            className="flex items-center justify-between px-4 py-2.5 shrink-0"
            style={{ background: "#0d0520", borderBottom: "1px solid rgba(255,255,255,0.06)" }}
          >
            <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#a78bfa" }}>Editor</span>
            <button
              onClick={handleUpdatePreview}
              disabled={updating || loading || !isDirty}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:-translate-y-0.5 disabled:opacity-40"
              style={{ color: "#03DAC5", border: "1px solid rgba(3,218,197,0.45)", background: "rgba(3,218,197,0.06)" }}
            >
              {updating ? (
                <><div className="h-3 w-3 rounded-full border-2 border-teal-400/40 border-t-teal-400 animate-spin" /> Updating…</>
              ) : (
                <><RefreshCw className="h-3 w-3" /> Update Preview</>
              )}
            </button>
          </div>
          {/* Highlighted editor: transparent textarea over a rendered highlight div */}
          <div className="relative flex-1 overflow-hidden" style={{ background: "#0a0618" }}>
            {/* Highlight layer — renders coloured section headers behind the textarea */}
            <div
              aria-hidden="true"
              className="absolute inset-0 p-4 pointer-events-none overflow-hidden"
              style={{
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                fontSize: "12px",
                lineHeight: "1.7",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                color: "transparent",
              }}
            >
              {editorText.split("\n").map((line, i) => {
                const isHeader = /^[A-Z][A-Z\s]{3,}$/.test(line.trim()) && line.trim().length > 0;
                return (
                  <span
                    key={i}
                    style={isHeader ? { color: "#FFB000", fontWeight: 700 } : { color: "transparent" }}
                  >
                    {line + "\n"}
                  </span>
                );
              })}
            </div>
            {/* Transparent textarea on top — captures all input */}
            <textarea
              value={editorText}
              onChange={(e) => setEditorText(e.target.value)}
              spellCheck={false}
              className="absolute inset-0 w-full h-full resize-none p-4 focus:outline-none"
              style={{
                background: "transparent",
                color: "rgba(255,255,255,0.75)",
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                fontSize: "12px",
                lineHeight: "1.7",
                caretColor: "#FFB000",
                mixBlendMode: "normal",
              }}
              placeholder="Edit your proposal here…"
            />
          </div>
          {/* Editor footer hint */}
          <div
            className="px-4 py-2 shrink-0 text-[10px] text-white/20"
            style={{ background: "#0a0618", borderTop: "1px solid rgba(255,255,255,0.05)" }}
          >
            Section headers (e.g. EXECUTIVE SUMMARY) are detected automatically.
          </div>
        </div>

        {/* Right: PDF Preview */}
        <div className="flex-1 flex flex-col overflow-hidden p-3 gap-2">
          {/* Preview header */}
          <div className="flex items-center justify-between shrink-0">
            <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#a78bfa" }}>Preview</span>
            {(loading || updating) && (
              <span className="flex items-center gap-1.5 text-[10px] text-white/30">
                <div className="h-2.5 w-2.5 rounded-full border border-amber-400/40 border-t-amber-400 animate-spin" />
                {updating ? "Re-rendering…" : "Rendering…"}
              </span>
            )}
          </div>

          {/* Spinner overlay while loading */}
          {loading && !blobUrl && (
            <div className="flex-1 flex flex-col items-center justify-center gap-4">
              <div className="relative h-14 w-14">
                <div
                  className="absolute inset-0 rounded-full border-2 animate-spin"
                  style={{ borderColor: "rgba(255,176,0,0.3)", borderTopColor: "#FFB000" }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <FileText className="h-5 w-5" style={{ color: "#FFB000" }} />
                </div>
              </div>
              <p className="text-sm text-white/40">Rendering PDF…</p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
              <p className="text-sm text-red-400">Failed to render PDF preview.</p>
              <button
                onClick={() => handleUpdatePreview()}
                className="text-xs font-semibold px-4 py-2 rounded-lg"
                style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.4)", background: "transparent" }}
              >
                Try again
              </button>
            </div>
          )}

          {/* PDF iframe */}
          {blobUrl && (
            <div className="flex-1 flex flex-col gap-2 overflow-hidden">
              <iframe
                key={blobUrl}
                src={blobUrl}
                title="Proposal PDF Preview"
                className="flex-1 w-full rounded-xl"
                style={{
                  border: "1px solid rgba(255,176,0,0.15)",
                  opacity: updating ? 0.4 : 1,
                  transition: "opacity 0.2s",
                }}
              />
              <p className="text-center text-[10px] text-white/20">
                If the preview doesn't load,{" "}
                <a
                  href={blobUrl}
                  download={`${data.companyName.replace(/[^a-z0-9]/gi, "-").toLowerCase()}-proposal.pdf`}
                  className="underline hover:text-white/40 transition-colors"
                  style={{ color: "rgba(255,176,0,0.5)" }}
                >
                  click here to download directly
                </a>
                .
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── PDF Actions (Preview + Download) ─────────────────────────────────────────
function PdfDownloadButton({
  data,
  deal,
}: {
  data: { proposal: string; companyName: string; senderCompany: string; senderName: string; senderTitle: string; generatedAt: number };
  deal: Deal;
}) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await fetchPdfBlob(data, deal);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.companyName.replace(/[^a-z0-9]/gi, "-").toLowerCase()}-proposal.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Proposal PDF downloaded");
    } catch {
      toast.error("Failed to generate PDF — please try again");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      {/* Preview button */}
      <button
        onClick={() => setPreviewOpen(true)}
        className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-lg transition-all hover:-translate-y-0.5"
        style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.45)", background: "rgba(255,176,0,0.06)" }}
      >
        <FileText className="h-3.5 w-3.5" /> Preview PDF
      </button>
      {/* Download button */}
      <button
        onClick={handleDownload}
        disabled={downloading}
        className="flex items-center gap-1.5 text-xs font-medium px-4 py-2.5 rounded-lg transition-all hover:-translate-y-0.5 disabled:opacity-60"
        style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.25)", background: "transparent" }}
      >
        {downloading ? (
          <><div className="h-3.5 w-3.5 rounded-full border-2 border-amber-400/40 border-t-amber-400 animate-spin" /> Saving…</>
        ) : (
          <><Download className="h-3.5 w-3.5" /> Download PDF</>
        )}
      </button>
      {/* Full-screen preview modal */}
      <PdfPreviewModal
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        data={data}
        deal={deal}
      />
    </>
  );
}

const STAGE_CONFIG: Record<string, { label: string; color: string; next?: string; nextLabel?: string }> = {
  pending:          { label: "Draft Ready",     color: "#a78bfa", next: "intro_sent",    nextLabel: "Send Intro" },
  intro_scheduled:  { label: "Intro Scheduled", color: "#fb923c", next: "intro_sent",    nextLabel: "Mark Sent" },
  intro_sent:       { label: "Intro Sent",      color: "#34d399", next: "followup_sent", nextLabel: "Send Follow-up" },
  followup_sent:    { label: "Follow-up Sent",  color: "#34d399", next: "linkedin_sent", nextLabel: "LinkedIn Touch" },
  linkedin_sent:    { label: "LinkedIn Sent",   color: "#34d399", next: "final_sent",    nextLabel: "Send Final" },
  final_sent:       { label: "Final Sent",      color: "#fb923c", next: "meeting_booked",nextLabel: "Book Meeting" },
  meeting_booked:   { label: "Meeting Booked",  color: "#03DAC5", next: "closed",        nextLabel: "Mark Closed" },
  closed:           { label: "Closed",          color: "#03DAC5" },
  paused:           { label: "Paused",          color: "rgba(255,255,255,0.3)" },
};

function signalMeta(src?: string | null): { icon: React.ElementType; color: string } {
  const t = (src ?? "").toLowerCase();
  if (t.includes("labor") || t.includes("shortage")) return { icon: AlertTriangle, color: "#f87171" };
  if (t.includes("expansion") || t.includes("capex")) return { icon: TrendingUp, color: "#34d399" };
  if (t.includes("hiring") || t.includes("automation")) return { icon: Zap, color: "#a78bfa" };
  return { icon: Target, color: "#03DAC5" };
}

function daysAgo(ms?: number | null): string | null {
  if (!ms) return null;
  const d = Math.floor((Date.now() - ms) / 86400000);
  return d === 0 ? "today" : d === 1 ? "yesterday" : `${d}d ago`;
}

function nextStepDue(deal: Deal): string | null {
  if (deal.outreachStage === "intro_sent" && deal.introSentAt) {
    const due = deal.introSentAt + 2 * 86400000;
    const diff = Math.ceil((due - Date.now()) / 86400000);
    if (diff <= 0) return "Follow-up overdue";
    if (diff === 1) return "Follow-up due tomorrow";
    return `Follow-up due in ${diff}d`;
  }
  if (deal.outreachStage === "followup_sent" && deal.followupSentAt) {
    const due = deal.followupSentAt + 3 * 86400000;
    const diff = Math.ceil((due - Date.now()) / 86400000);
    if (diff <= 0) return "LinkedIn touch overdue";
    return `LinkedIn touch due in ${diff}d`;
  }
  return null;
}

function EmptyPipeline() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-6">
      <div
        className="h-16 w-16 rounded-2xl flex items-center justify-center"
        style={{ background: "rgba(255,176,0,0.08)", border: "1px solid rgba(255,176,0,0.2)" }}
      >
        <Bot className="h-7 w-7" style={{ color: "#FFB000" }} />
      </div>
      <div>
        <h2 className="text-lg font-bold text-white mb-2" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>
          SCOUT is ready — activate your pipeline
        </h2>
        <p className="text-sm text-white/40 max-w-sm">
          Scan your company URL to get matched prospects with buying signals. SCOUT scores, drafts outreach, and queues follow-ups automatically.
        </p>
      </div>
      {/* 3-step guide */}
      <div className="flex flex-col sm:flex-row gap-3 text-left w-full max-w-lg">
        {[
          { step: "1", label: "Scan your URL", desc: "Enter your robot company website" },
          { step: "2", label: "Review leads", desc: "SCOUT scores and drafts outreach" },
          { step: "3", label: "Approve & send", desc: "One click to start the campaign" },
        ].map((s) => (
          <div
            key={s.step}
            className="flex-1 rounded-xl p-4"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <div
              className="h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold mb-2"
              style={{ background: "rgba(255,176,0,0.12)", color: "#FFB000" }}
            >
              {s.step}
            </div>
            <p className="text-xs font-bold text-white mb-0.5">{s.label}</p>
            <p className="text-xs text-white/35">{s.desc}</p>
          </div>
        ))}
      </div>
      <Link href="/">
        <button
          className="flex items-center gap-2 font-semibold text-sm px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5"
          style={{ color: "#FFB000", border: "1.5px solid #FFB000", background: "transparent" }}
        >
          Activate Pipeline <ArrowRight className="h-4 w-4" />
        </button>
      </Link>
    </div>
  );
}

function DealCard({
  deal,
  onAdvance,
  onToggleMode,
  onArchive,
}: {
  deal: Deal;
  onAdvance: (id: number, stage: string) => void;
  onToggleMode: (id: number, mode: "assisted" | "autopilot") => void;
  onArchive: (id: number) => void;
}) {
  const [showDraft, setShowDraft] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showProposal, setShowProposal] = useState(false);
  const stage = STAGE_CONFIG[deal.outreachStage] ?? { label: deal.outreachStage, color: "#a78bfa" };
  const { icon: SignalIcon, color: signalColor } = signalMeta(deal.signalSource);
  const due = nextStepDue(deal);
  const draft = (deal.scoreNotes as any)?.outreachDraft as string | undefined;

  const generateProposal = trpc.pipeline.generateProposal.useMutation({
    onError: () => toast.error("Failed to generate proposal — please try again"),
  });

  return (
    <div
      className="rounded-2xl border overflow-hidden transition-all"
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: deal.outreachStage === "meeting_booked" || deal.outreachStage === "closed"
          ? "rgba(3,218,197,0.3)"
          : "rgba(255,255,255,0.07)",
      }}
    >
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start gap-4">
          <div className="shrink-0 flex flex-col items-center gap-1">
            <div
              className="h-12 w-12 rounded-full border-2 flex items-center justify-center"
              style={{ borderColor: scoreColor(deal.scoutScore), background: `${scoreColor(deal.scoutScore)}12` }}
            >
              <span
                className="font-mono text-base font-bold"
                style={{ color: scoreColor(deal.scoutScore), fontFamily: "'JetBrains Mono', monospace" }}
              >
                {deal.scoutScore}
              </span>
            </div>
            <span className="text-[9px] text-white/20 uppercase tracking-widest">score</span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h3 className="text-sm font-bold text-white">{deal.companyName}</h3>
              <span
                className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{ color: stage.color, background: `${stage.color}18`, border: `1px solid ${stage.color}40` }}
              >
                {stage.label}
              </span>
              {deal.opportunityType === "partnership" && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ color: "#fb923c", background: "rgba(251,146,60,0.1)", border: "1px solid rgba(251,146,60,0.3)" }}>
                  Partner
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-white/30 mb-2">
              {deal.industry && <span className="flex items-center gap-1"><Building2 className="h-3 w-3" />{deal.industry}</span>}
              {deal.robotCategory && <span className="flex items-center gap-1"><Zap className="h-3 w-3" />{deal.robotCategory}</span>}
              {deal.createdAt && <span className="flex items-center gap-1"><Clock className="h-3 w-3" />Added {daysAgo(deal.createdAt)}</span>}
            </div>
            {deal.signal && (
              <div className="flex items-start gap-2 p-2.5 rounded-lg mb-2" style={{ background: `${signalColor}0d`, border: `1px solid ${signalColor}20` }}>
                <SignalIcon className="h-3 w-3 shrink-0 mt-0.5" style={{ color: signalColor }} />
                <p className="text-xs text-white/50 leading-relaxed">{deal.signal}</p>
              </div>
            )}
            {due && (
              <div className="flex items-center gap-1.5 text-xs" style={{ color: due.includes("overdue") ? "#f87171" : "#fb923c" }}>
                <Clock className="h-3 w-3" />
                {due}
              </div>
            )}
            {deal.contactEmail && (
              <div className="flex items-center gap-1.5 mt-1.5">
                <Mail className="h-3 w-3 shrink-0" style={{ color: "rgba(3,218,197,0.5)" }} />
                <a
                  href={`mailto:${deal.contactEmail}`}
                  className="text-[10px] font-mono hover:underline"
                  style={{ color: "rgba(3,218,197,0.7)", fontFamily: "'JetBrains Mono', monospace" }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {deal.contactEmail}
                </a>
              </div>
            )}
          </div>

          <div className="relative shrink-0">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
              style={{ color: "rgba(255,255,255,0.3)" }}
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            {showMenu && (
              <div
                className="absolute right-0 top-8 z-20 rounded-xl border border-white/10 py-1 w-44 shadow-2xl"
                style={{ background: "#1a0a30" }}
              >
                <button
                  onClick={() => {
                    onToggleMode(deal.id, deal.pipelineMode === "assisted" ? "autopilot" : "assisted");
                    setShowMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                >
                  {deal.pipelineMode === "assisted"
                    ? <><ToggleRight className="h-3.5 w-3.5" style={{ color: "#03DAC5" }} /> Switch to Auto-pilot</>
                    : <><ToggleLeft className="h-3.5 w-3.5" /> Switch to Assisted</>
                  }
                </button>
                <button
                  onClick={() => { onArchive(deal.id); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-white/40 hover:text-red-400 hover:bg-white/5 transition-colors"
                >
                  <Archive className="h-3.5 w-3.5" /> Archive
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="px-5 pb-4 flex flex-wrap items-center gap-2">
        <span
          className="text-[10px] font-bold px-2 py-1 rounded-full"
          style={deal.pipelineMode === "autopilot"
            ? { color: "#03DAC5", background: "rgba(3,218,197,0.08)", border: "1px solid rgba(3,218,197,0.25)" }
            : { color: "#a78bfa", background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.25)" }
          }
        >
          {deal.pipelineMode === "autopilot" ? "Auto-pilot" : "Assisted"}
        </span>

        {stage.next && (
          <button
            onClick={() => onAdvance(deal.id, stage.next!)}
            className="flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
            style={{ color: "#03DAC5", background: "rgba(3,218,197,0.08)", border: "1px solid rgba(3,218,197,0.35)" }}
          >
            <CheckCircle2 className="h-3.5 w-3.5" /> {stage.nextLabel}
          </button>
        )}

        {draft && (
          <button
            onClick={() => setShowDraft(!showDraft)}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg transition-colors hover:bg-white/5"
            style={{ color: "rgba(255,255,255,0.35)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <FileText className="h-3 w-3" />
            {showDraft ? <><ChevronUp className="h-3 w-3" /> Hide draft</> : <><ChevronDown className="h-3 w-3" /> View draft</>}
          </button>
        )}

        {/* Generate Proposal button */}
        <button
          onClick={() => {
            setShowProposal(true);
            if (!generateProposal.data) {
              generateProposal.mutate({
                companyName: deal.companyName,
                industry: deal.industry ?? undefined,
                robotCategory: deal.robotCategory ?? undefined,
                signal: deal.signal ?? undefined,
                scoutScore: deal.scoutScore,
                contactEmail: deal.contactEmail ?? undefined,
              });
            }
          }}
          className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg transition-all hover:-translate-y-0.5"
          style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.35)", background: "rgba(255,176,0,0.04)" }}
        >
          <Sparkles className="h-3 w-3" /> Generate Proposal
        </button>
      </div>

      {showDraft && draft && (
        <div className="px-5 pb-5 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="mt-4 rounded-xl p-4" style={{ background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.15)" }}>
            <p className="text-[10px] font-bold uppercase tracking-wider mb-3" style={{ color: "#a78bfa" }}>
              SCOUT-drafted outreach
            </p>
            <pre className="text-xs text-white/50 leading-relaxed whitespace-pre-wrap" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {draft}
            </pre>
            <div className="flex gap-2 mt-4">
              {stage.next && (
                <button
                  onClick={() => onAdvance(deal.id, stage.next!)}
                  className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
                  style={{ color: "#03DAC5", border: "1px solid rgba(3,218,197,0.5)", background: "transparent" }}
                >
                  <CheckCircle2 className="h-3.5 w-3.5" /> Approve & {stage.nextLabel}
                </button>
              )}
              <button
                onClick={() => { navigator.clipboard.writeText(draft); toast.success("Draft copied"); }}
                className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg text-white/40 border border-white/10 hover:border-white/20 transition-colors"
                style={{ background: "rgba(255,255,255,0.03)" }}
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Proposal Modal ── */}
      {showProposal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.75)" }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowProposal(false); }}
        >
          <div
            className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border"
            style={{ background: "#0d0520", borderColor: "rgba(255,176,0,0.25)" }}
          >
            {/* Modal header */}
            <div
              className="sticky top-0 flex items-center justify-between px-6 py-4 border-b"
              style={{ background: "#0d0520", borderColor: "rgba(255,176,0,0.15)" }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="h-8 w-8 rounded-lg flex items-center justify-center"
                  style={{ background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.3)" }}
                >
                  <Sparkles className="h-4 w-4" style={{ color: "#FFB000" }} />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">SCOUT Proposal</p>
                  <p className="text-[10px] text-white/35">{deal.companyName}</p>
                </div>
              </div>
              <button
                onClick={() => setShowProposal(false)}
                className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
              >
                <X className="h-4 w-4 text-white/40" />
              </button>
            </div>

            {/* Modal body */}
            <div className="px-6 py-5">
              {generateProposal.isPending ? (
                <div className="flex flex-col items-center justify-center py-12 gap-4">
                  <div className="relative h-12 w-12">
                    <div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: "rgba(255,176,0,0.4)", borderTopColor: "#FFB000" }} />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Sparkles className="h-4 w-4" style={{ color: "#FFB000" }} />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-semibold text-white/70">SCOUT is writing your proposal…</p>
                    <p className="text-xs text-white/30 mt-1">Tailoring to {deal.companyName}'s buying signal</p>
                  </div>
                </div>
              ) : generateProposal.data ? (
                <>
                  <div
                    className="rounded-xl p-5 mb-4"
                    style={{ background: "rgba(255,176,0,0.04)", border: "1px solid rgba(255,176,0,0.12)" }}
                  >
                    <pre
                      className="text-sm text-white/70 leading-relaxed whitespace-pre-wrap"
                      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
                    >
                      {generateProposal.data.proposal}
                    </pre>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(generateProposal.data!.proposal);
                        toast.success("Proposal copied to clipboard");
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-lg transition-all hover:-translate-y-0.5"
                      style={{ color: "#03DAC5", border: "1px solid rgba(3,218,197,0.5)", background: "transparent" }}
                    >
                      <Copy className="h-3.5 w-3.5" /> Copy Proposal
                    </button>
                    <PdfDownloadButton
                      data={generateProposal.data!}
                      deal={deal}
                    />
                    <button
                      onClick={() => {
                        generateProposal.reset();
                        generateProposal.mutate({
                          companyName: deal.companyName,
                          industry: deal.industry ?? undefined,
                          robotCategory: deal.robotCategory ?? undefined,
                          signal: deal.signal ?? undefined,
                          scoutScore: deal.scoutScore,
                          contactEmail: deal.contactEmail ?? undefined,
                        });
                      }}
                      className="flex items-center gap-1.5 text-xs font-medium px-3 py-2.5 rounded-lg text-white/30 hover:text-white/50 transition-colors"
                    >
                      <RefreshCw className="h-3 w-3" /> Regenerate
                    </button>
                  </div>
                </>
              ) : generateProposal.isError ? (
                <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
                  <p className="text-sm text-red-400">Failed to generate proposal. Please try again.</p>
                  <button
                    onClick={() => generateProposal.mutate({
                      companyName: deal.companyName,
                      industry: deal.industry ?? undefined,
                      robotCategory: deal.robotCategory ?? undefined,
                      signal: deal.signal ?? undefined,
                      scoutScore: deal.scoutScore,
                      contactEmail: deal.contactEmail ?? undefined,
                    })}
                    className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg"
                    style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.4)", background: "transparent" }}
                  >
                    <RefreshCw className="h-3.5 w-3.5" /> Try again
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Pipeline() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [filter, setFilter] = useState<"all" | "active" | "meeting_booked" | "closed">("all");
  const [showEmailBanner, setShowEmailBanner] = useState(true);

  const { data: deals, isLoading, refetch } = trpc.pipeline.list.useQuery(undefined, {
    enabled: isAuthenticated,
    refetchOnWindowFocus: false,
  });

  const advanceStage = trpc.pipeline.advanceStage.useMutation({
    onSuccess: () => { refetch(); },
    onError: () => toast.error("Failed to update stage"),
  });

  const toggleMode = trpc.pipeline.toggleMode.useMutation({
    onSuccess: (_, vars) => {
      toast.success(`Switched to ${vars.mode === "autopilot" ? "Auto-pilot" : "Assisted"} mode`);
      refetch();
    },
    onError: () => toast.error("Failed to update mode"),
  });

  const archiveDeal = trpc.pipeline.archive.useMutation({
    onSuccess: () => { toast.success("Deal archived"); refetch(); },
    onError: () => toast.error("Failed to archive deal"),
  });

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="h-8 w-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
        <Header />
        <div className="flex-1 flex flex-col items-center justify-center gap-6 text-center px-6">
          <div className="h-14 w-14 rounded-2xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.25)" }}>
            <Target className="h-6 w-6" style={{ color: "#7c3aed" }} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white mb-2">Sign in to view your pipeline</h2>
            <p className="text-sm text-white/40">Your matched leads and outreach drafts are saved to your account.</p>
          </div>
          <button
            onClick={() => { window.location.href = getLoginUrl(); }}
            className="flex items-center gap-2 font-semibold text-sm px-6 py-3 rounded-xl transition-all hover:-translate-y-0.5"
            style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.5)", background: "transparent" }}
          >
            Sign in with Manus <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  const activeDealList: Deal[] = (deals ?? []).map((d) => ({ ...d, createdAt: d.createdAt instanceof Date ? d.createdAt.getTime() : d.createdAt, introSentAt: d.introSentAt ?? null, followupSentAt: d.followupSentAt ?? null, linkedinSentAt: d.linkedinSentAt ?? null, finalSentAt: d.finalSentAt ?? null, })) as Deal[];
  const filteredDeals = activeDealList.filter((d) => {
    if (filter === "all") return d.outreachStage !== "closed" && d.outreachStage !== "paused";
    if (filter === "active") return !["closed", "paused", "meeting_booked"].includes(d.outreachStage);
    return d.outreachStage === filter;
  });

  const total = activeDealList.length;
  const hot = activeDealList.filter((d) => d.scoutScore >= 85).length;
  const meetings = activeDealList.filter((d) => d.outreachStage === "meeting_booked").length;
  const closed = activeDealList.filter((d) => d.outreachStage === "closed").length;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0d0520" }}>
      <Header />
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-12 pt-28">

        {/* Connect email banner — shown when user has deals but no email connected */}
        {showEmailBanner && total > 0 && (
          <div
            className="flex items-center gap-4 rounded-xl px-5 py-4 mb-6"
            style={{ background: "rgba(255,176,0,0.06)", border: "1px solid rgba(255,176,0,0.25)" }}
          >
            <div
              className="h-9 w-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: "rgba(255,176,0,0.12)", border: "1px solid rgba(255,176,0,0.3)" }}
            >
              <Mail className="h-4 w-4" style={{ color: "#FFB000" }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-white mb-0.5">Connect your email to send outreach</p>
              <p className="text-xs text-white/40">SCOUT has your drafts ready. Connect Gmail or Outlook so SCOUT can send on your behalf.</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link href="/scout-settings">
                <button
                  className="text-xs font-bold px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
                  style={{ color: "#FFB000", border: "1px solid rgba(255,176,0,0.5)", background: "transparent" }}
                >
                  Connect email
                </button>
              </Link>
              <button
                onClick={() => setShowEmailBanner(false)}
                className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                style={{ color: "rgba(255,255,255,0.25)" }}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1
              className="font-extrabold text-white leading-tight mb-1"
              style={{ fontSize: "clamp(1.6rem, 3vw, 2rem)", fontFamily: "'Sora', system-ui, sans-serif" }}
            >
              Your Pipeline
            </h1>
            <p className="text-sm text-white/40">
              SCOUT-managed outreach · {total} deal{total !== 1 ? "s" : ""} tracked
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-2 rounded-lg hover:bg-white/5 transition-colors"
              style={{ color: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <Link href="/">
              <button
                className="flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
                style={{ color: "#03DAC5", border: "1.5px solid rgba(3,218,197,0.4)", background: "transparent" }}
              >
                <Plus className="h-3.5 w-3.5" /> Add leads
              </button>
            </Link>
          </div>
        </div>

        {total > 0 && (
          <div className="grid grid-cols-4 gap-3 mb-8">
            {[
              { label: "Total", value: total, color: "#a78bfa" },
              { label: "Hot (85+)", value: hot, color: "#f87171" },
              { label: "Meetings", value: meetings, color: "#03DAC5" },
              { label: "Closed", value: closed, color: "#34d399" },
            ].map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-white/6 px-3 py-3 text-center"
                style={{ background: "rgba(255,255,255,0.02)" }}
              >
                <p className="font-mono text-xl font-bold" style={{ color: s.color, fontFamily: "'JetBrains Mono', monospace" }}>
                  {s.value}
                </p>
                <p className="text-[10px] text-white/30 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {total > 0 && (
          <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
            {(["all", "active", "meeting_booked", "closed"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                style={filter === f
                  ? { color: "#03DAC5", background: "rgba(3,218,197,0.1)", border: "1px solid rgba(3,218,197,0.3)" }
                  : { color: "rgba(255,255,255,0.35)", border: "1px solid rgba(255,255,255,0.08)", background: "transparent" }
                }
              >
                {f === "all" ? "Active" : f === "active" ? "In Progress" : f === "meeting_booked" ? "Meetings" : "Closed"}
              </button>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-24">
            <div className="h-8 w-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
          </div>
        )}

        {!isLoading && total === 0 && <EmptyPipeline />}

        {!isLoading && filteredDeals.length > 0 && (
          <div className="space-y-4">
            {filteredDeals.map((deal) => (
              <DealCard
                key={deal.id}
                deal={deal}
                onAdvance={(id, stage) => advanceStage.mutate({ id, stage: stage as any })}
                onToggleMode={(id, mode) => toggleMode.mutate({ id, mode })}
                onArchive={(id) => archiveDeal.mutate({ id })}
              />
            ))}
          </div>
        )}

        {!isLoading && total > 0 && filteredDeals.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <p className="text-sm text-white/40">No deals in this view</p>
            <button
              onClick={() => setFilter("all")}
              className="text-xs font-semibold px-4 py-2 rounded-lg"
              style={{ color: "#a78bfa", border: "1px solid rgba(124,58,237,0.3)", background: "rgba(124,58,237,0.06)" }}
            >
              Show all
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
