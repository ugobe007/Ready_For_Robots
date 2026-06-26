/**
 * ScoutActionBar — fixed 4-button bar: [Run SIGNAL] [Activate SIGNAL] [Track SIGNAL] [TEST]
 * Sits at the top of any panel that manages Cal outreach.
 * Also owns the TEST diagnostic modal.
 */
import { useState } from "react";
import { Zap, Send, BarChart2, FlaskConical, X, RefreshCw, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

/* ── Types ─────────────────────────────────────────────────────────────── */
export interface ScoutStats {
  total: number;
  drafted: number;
  sent: number;
  opened: number;
  clicked: number;
  replied: number;
}

interface DiagnosticConfig {
  from_email: string | null;
  reply_to: string | null;
  api_key_set: boolean;
  delivery_webhook_configured: boolean;
  inbound_webhook_configured: boolean;
}

interface DiagnosticStats {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  replied: number;
  total: number;
}

interface RecentEmail {
  id: string;
  to: string;
  subject: string;
  status: string;
  sent_at: string | null;
  company: string;
}

interface DiagnosticData {
  config: DiagnosticConfig;
  stats_30d: DiagnosticStats;
  recent_emails: RecentEmail[];
  issues: string[];
  health: "ok" | "warn" | "error";
}

/* ── Helpers ────────────────────────────────────────────────────────────── */
function statusColor(status: string): string {
  if (["opened", "clicked"].includes(status)) return "#34d399";
  if (["sent", "delivered"].includes(status)) return "#60a5fa";
  if (["bounced", "complained", "suppressed"].includes(status)) return "#f87171";
  if (status === "replied") return "#a78bfa";
  return "rgba(255,255,255,0.3)";
}

function HealthIcon({ health }: { health: "ok" | "warn" | "error" }) {
  if (health === "ok") return <CheckCircle2 className="h-4 w-4" style={{ color: "#34d399" }} />;
  if (health === "warn") return <AlertTriangle className="h-4 w-4" style={{ color: "#FFB000" }} />;
  return <XCircle className="h-4 w-4" style={{ color: "#f87171" }} />;
}

function StatPill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-xl border border-white/8 px-3 py-2 text-center" style={{ background: "rgba(255,255,255,0.02)" }}>
      <p className="font-mono text-lg font-bold" style={{ color }}>{value}</p>
      <p className="text-[10px] uppercase tracking-widest text-white/30 mt-0.5">{label}</p>
    </div>
  );
}

/* ── Component ─────────────────────────────────────────────────────────── */
interface Props {
  accessToken: string | undefined;
  stats: ScoutStats | null;
  busy: "draft" | "send" | null;
  onRunScout: () => void;
  onActivateScout: () => void;
  onTrackScout: () => void;
}

export default function ScoutActionBar({
  accessToken,
  stats,
  busy,
  onRunScout,
  onActivateScout,
  onTrackScout,
}: Props) {
  const [testOpen, setTestOpen] = useState(false);
  const [diagnostic, setDiagnostic] = useState<DiagnosticData | null>(null);
  const [loadingDiag, setLoadingDiag] = useState(false);

  const openTest = async () => {
    setTestOpen(true);
    if (diagnostic) return; // already loaded
    if (!accessToken) { toast.info("Sign in to run a diagnostic."); return; }
    setLoadingDiag(true);
    try {
      const r = await fetch(
        `${getApiBase()}/api/admin/scout/diagnostic`,
        liveFetchInit({ headers: authHeader(accessToken) }),
      );
      if (!r.ok) throw new Error(await r.text());
      setDiagnostic(await r.json() as DiagnosticData);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Diagnostic failed");
    } finally {
      setLoadingDiag(false);
    }
  };

  const refreshDiag = async () => {
    if (!accessToken) return;
    setDiagnostic(null);
    setLoadingDiag(true);
    try {
      const r = await fetch(
        `${getApiBase()}/api/admin/scout/diagnostic`,
        liveFetchInit({ headers: authHeader(accessToken) }),
      );
      if (!r.ok) throw new Error(await r.text());
      setDiagnostic(await r.json() as DiagnosticData);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Diagnostic failed");
    } finally {
      setLoadingDiag(false);
    }
  };

  return (
    <>
      {/* ── Action bar ── */}
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-gray-50 px-4 py-3">
        <span className="mr-2 text-[10px] font-bold uppercase tracking-[0.18em] text-violet-700">SIGNAL</span>

        {/* Step 1 — Draft */}
        <button
          type="button"
          disabled={!!busy}
          onClick={onRunScout}
          className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-blue-800 transition-all hover:-translate-y-px disabled:opacity-50"
          title="Step 1 — Write Cal outreach emails for all prospects (buyer & vendor templates)"
        >
          {busy === "draft" ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
          1 · Draft emails
        </button>

        <span className="text-xs text-gray-400">→</span>

        {/* Step 2 — Send */}
        <button
          type="button"
          disabled={!!busy}
          onClick={onActivateScout}
          className="flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-bold text-emerald-800 transition-all hover:-translate-y-px disabled:opacity-50"
          title="Step 2 — Send all drafted emails via Resend (all at once)"
        >
          {busy === "send" ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
          2 · Send all{stats?.drafted ? ` (${stats.drafted})` : ""}
        </button>

        <span className="text-xs text-gray-400">→</span>

        {/* Step 3 — Track */}
        <button
          type="button"
          onClick={onTrackScout}
          className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-[11px] font-bold text-amber-900 transition-all hover:-translate-y-px"
          title="Step 3 — Refresh open / click / reply stats"
        >
          <BarChart2 className="h-3 w-3" />
          3 · Track stats
        </button>

        {/* TEST */}
        <button
          type="button"
          onClick={() => void openTest()}
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-[11px] font-bold text-violet-800 transition-all hover:-translate-y-px"
          title="Run workflow diagnostic — check reply routing, webhooks, and delivery stats"
        >
          <FlaskConical className="h-3 w-3" />
          TEST
        </button>
      </div>

      {/* ── TEST / Diagnostic modal ── */}
      {testOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)" }}
          onClick={() => setTestOpen(false)}
        >
          <div
            className="relative w-full max-w-2xl rounded-2xl border flex flex-col"
            style={{
              background: "#0d0520",
              borderColor: "rgba(124,58,237,0.35)",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
              <div className="flex items-center gap-3">
                <FlaskConical className="h-5 w-5" style={{ color: "#a78bfa" }} />
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#a78bfa" }}>Workflow Diagnostic</p>
                  <p className="text-sm font-bold text-white" style={{ fontFamily: "'Sora', system-ui, sans-serif" }}>SIGNAL / Cal Outreach Health</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {diagnostic && <HealthIcon health={diagnostic.health} />}
                <button
                  type="button"
                  onClick={() => void refreshDiag()}
                  disabled={loadingDiag}
                  className="text-white/30 hover:text-white/70 p-1 rounded transition-all disabled:opacity-40"
                >
                  <RefreshCw className={`h-4 w-4 ${loadingDiag ? "animate-spin" : ""}`} />
                </button>
                <button onClick={() => setTestOpen(false)} className="text-white/30 hover:text-white/70 p-1 rounded">
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {loadingDiag && !diagnostic && (
              <div className="px-6 py-10 text-center text-sm text-white/35">Running diagnostic…</div>
            )}

            {diagnostic && (
              <div className="px-6 py-5 flex flex-col gap-5">

                {/* Issues */}
                {diagnostic.issues.length > 0 && (
                  <div className="rounded-xl border border-amber-400/25 bg-amber-400/6 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-amber-200/70 mb-2">Issues found</p>
                    <ul className="space-y-1">
                      {diagnostic.issues.map((issue, i) => (
                        <li key={i} className="flex items-start gap-2 text-[11px] text-amber-100/80">
                          <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" style={{ color: "#FFB000" }} />
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Send path */}
                <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.02)" }}>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-3">Email routing</p>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                    <div>
                      <p className="text-[10px] text-white/30 uppercase tracking-wide mb-0.5">Cal sends from</p>
                      <p className="text-xs font-semibold text-white/75 break-all">{diagnostic.config.from_email || <span className="text-red-400">Not set</span>}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/30 uppercase tracking-wide mb-0.5">Replies go to</p>
                      <p className="text-xs font-semibold text-white/75 break-all">
                        {diagnostic.config.reply_to || <span className="italic text-amber-300">Same as from (RESEND_REPLY_TO not set)</span>}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/30 uppercase tracking-wide mb-0.5">Resend API key</p>
                      <p className="text-xs font-semibold" style={{ color: diagnostic.config.api_key_set ? "#34d399" : "#f87171" }}>
                        {diagnostic.config.api_key_set ? "✓ Configured" : "✗ Missing"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Webhook status */}
                <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.02)" }}>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-3">Tracking webhooks</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex items-center gap-2">
                      {diagnostic.config.delivery_webhook_configured
                        ? <CheckCircle2 className="h-4 w-4 shrink-0" style={{ color: "#34d399" }} />
                        : <XCircle className="h-4 w-4 shrink-0" style={{ color: "#f87171" }} />
                      }
                      <div>
                        <p className="text-xs font-semibold text-white/70">Delivery events</p>
                        <p className="text-[10px] text-white/30">Open / click / bounce tracking</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {diagnostic.config.inbound_webhook_configured
                        ? <CheckCircle2 className="h-4 w-4 shrink-0" style={{ color: "#34d399" }} />
                        : <XCircle className="h-4 w-4 shrink-0" style={{ color: "#f87171" }} />
                      }
                      <div>
                        <p className="text-xs font-semibold text-white/70">Inbound replies</p>
                        <p className="text-[10px] text-white/30">Captures prospect replies to Cal</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 30-day delivery stats */}
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Delivery stats — last 30 days</p>
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                    <StatPill label="Sent" value={diagnostic.stats_30d.sent} color="#60a5fa" />
                    <StatPill label="Delivered" value={diagnostic.stats_30d.delivered} color="#93c5fd" />
                    <StatPill label="Opened" value={diagnostic.stats_30d.opened} color="#34d399" />
                    <StatPill label="Clicked" value={diagnostic.stats_30d.clicked} color="#6ee7b7" />
                    <StatPill label="Bounced" value={diagnostic.stats_30d.bounced} color="#f87171" />
                    <StatPill label="Replied" value={diagnostic.stats_30d.replied} color="#a78bfa" />
                  </div>
                </div>

                {/* Recent emails */}
                {diagnostic.recent_emails.length > 0 && (
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-white/25 mb-2">Recent emails</p>
                    <div className="space-y-1.5">
                      {/* Header */}
                      <div className="grid grid-cols-[1.5fr_1.5fr_1fr_0.8fr] gap-3 border-b border-white/7 pb-1.5 text-[9px] uppercase tracking-widest text-white/25">
                        <span>Company</span>
                        <span>To</span>
                        <span>Subject</span>
                        <span>Status</span>
                      </div>
                      {diagnostic.recent_emails.map((msg) => (
                        <div key={msg.id} className="grid grid-cols-[1.5fr_1.5fr_1fr_0.8fr] gap-3 rounded-lg px-0 py-1 text-[11px]">
                          <span className="text-white/65 truncate">{msg.company}</span>
                          <span className="font-mono text-white/40 truncate">{msg.to}</span>
                          <span className="text-white/35 truncate">{msg.subject}</span>
                          <span className="font-bold capitalize" style={{ color: statusColor(msg.status) }}>{msg.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* How to check replies */}
                <div className="rounded-xl border border-violet-400/15 bg-violet-400/5 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-violet-200/70 mb-2">How to check replies</p>
                  <ul className="space-y-1.5">
                    <li className="text-[11px] text-white/55">
                      <span className="font-semibold text-white/75">1. Inbox</span> — Check{" "}
                      <span className="font-mono text-violet-300">{diagnostic.config.reply_to || diagnostic.config.from_email || "your reply-to inbox"}</span>{" "}
                      for prospect replies. Cal routes them here automatically.
                    </li>
                    <li className="text-[11px] text-white/55">
                      <span className="font-semibold text-white/75">2. Sales Console</span> — Go to{" "}
                      <a href="/sales-console" className="text-violet-300 underline underline-offset-2">/sales-console</a>{" "}
                      to see all captured replies in your SIGNAL workflow queue.
                    </li>
                    <li className="text-[11px] text-white/55">
                      <span className="font-semibold text-white/75">3. Resend Dashboard</span> — Open{" "}
                      <a href="https://resend.com/emails" target="_blank" rel="noreferrer" className="text-violet-300 underline underline-offset-2">resend.com/emails</a>{" "}
                      for per-email delivery events, open pixel data, and bounce details.
                    </li>
                  </ul>
                </div>

              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
