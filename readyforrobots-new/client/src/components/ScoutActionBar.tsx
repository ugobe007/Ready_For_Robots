/**
 * ScoutActionBar — Cal outreach workflow: Review → Approve → Send → Responses
 */
import { useState } from "react";
import { Eye, CheckCircle2, Send, Inbox, FlaskConical, X, RefreshCw, AlertTriangle, XCircle, CheckCircle2 as CheckOk } from "lucide-react";
import { toast } from "sonner";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

export interface ScoutStats {
  total: number;
  drafted: number;
  sendable: number;
  needsApproval?: number;
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

function statusColor(status: string): string {
  if (["opened", "clicked"].includes(status)) return "#34d399";
  if (["sent", "delivered"].includes(status)) return "#60a5fa";
  if (["bounced", "complained", "suppressed"].includes(status)) return "#f87171";
  if (status === "replied") return "#a78bfa";
  return "rgba(255,255,255,0.3)";
}

function HealthIcon({ health }: { health: "ok" | "warn" | "error" }) {
  if (health === "ok") return <CheckOk className="h-4 w-4" style={{ color: "#34d399" }} />;
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

interface Props {
  accessToken: string | undefined;
  stats: ScoutStats | null;
  busy: "draft" | "send" | "approve" | null;
  onStep1Review: () => void;
  onStep2Approve: () => void;
  onStep3Send: () => void;
  onStep4Responses: () => void;
}

export default function ScoutActionBar({
  accessToken,
  stats,
  busy,
  onStep1Review,
  onStep2Approve,
  onStep3Send,
  onStep4Responses,
}: Props) {
  const [testOpen, setTestOpen] = useState(false);
  const [diagnostic, setDiagnostic] = useState<DiagnosticData | null>(null);
  const [loadingDiag, setLoadingDiag] = useState(false);

  const openTest = async () => {
    setTestOpen(true);
    if (diagnostic) return;
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

  const stepBtn = (
    step: number,
    label: string,
    icon: React.ReactNode,
    onClick: () => void,
    colors: { border: string; bg: string; text: string },
    count?: number,
    disabled?: boolean,
  ) => (
    <button
      type="button"
      disabled={disabled || !!busy}
      onClick={onClick}
      className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px] font-bold transition-all hover:-translate-y-px disabled:opacity-50"
      style={{ borderColor: colors.border, background: colors.bg, color: colors.text }}
      title={`Step ${step} — ${label}`}
    >
      {icon}
      {step} · {label}{count != null && count > 0 ? ` (${count})` : ""}
    </button>
  );

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-gray-50 px-4 py-3">
        <span className="mr-1 text-[10px] font-bold uppercase tracking-[0.18em] text-violet-700">Cal workflow</span>

        {stepBtn(1, "Review drafts", <Eye className="h-3 w-3" />, onStep1Review, {
          border: "rgba(96,165,250,0.35)",
          bg: "rgba(96,165,250,0.08)",
          text: "#1d4ed8",
        }, stats?.drafted)}

        <span className="text-xs font-semibold text-gray-400">→</span>

        {stepBtn(2, "Approve & edit", busy === "approve" ? <RefreshCw className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />, onStep2Approve, {
          border: "rgba(167,139,250,0.35)",
          bg: "rgba(167,139,250,0.08)",
          text: "#6d28d9",
        }, stats?.needsApproval)}

        <span className="text-xs font-semibold text-gray-400">→</span>

        {stepBtn(3, "Send emails", busy === "send" ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />, onStep3Send, {
          border: "rgba(52,211,153,0.35)",
          bg: "rgba(52,211,153,0.08)",
          text: "#047857",
        }, stats?.sendable)}

        <span className="text-xs font-semibold text-gray-400">→</span>

        {stepBtn(4, "Review replies", <Inbox className="h-3 w-3" />, onStep4Responses, {
          border: "rgba(251,191,36,0.45)",
          bg: "rgba(251,191,36,0.1)",
          text: "#92400e",
        }, stats?.replied || stats?.sent)}

        <button
          type="button"
          onClick={() => void openTest()}
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-[11px] font-bold text-violet-800 transition-all hover:-translate-y-px"
          title="Run workflow diagnostic"
        >
          <FlaskConical className="h-3 w-3" />
          TEST
        </button>
      </div>

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
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
              <div className="flex items-center gap-3">
                <FlaskConical className="h-5 w-5" style={{ color: "#a78bfa" }} />
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#a78bfa" }}>Workflow Diagnostic</p>
                  <p className="text-sm font-bold text-white">Cal Outreach Health</p>
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
                        {diagnostic.config.reply_to || <span className="italic text-amber-300">Same as from</span>}
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

                <div className="rounded-xl border border-violet-400/15 bg-violet-400/5 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-violet-200/70 mb-2">Step 4 — How to check replies</p>
                  <ul className="space-y-1.5 text-[11px] text-white/55">
                    <li><span className="font-semibold text-white/75">Inbox</span> — Check your reply-to address for prospect replies.</li>
                    <li><span className="font-semibold text-white/75">Sales workflow</span> — <a href="/sales-workflow" className="text-violet-300 underline">/sales-workflow</a> for captured replies.</li>
                    <li><span className="font-semibold text-white/75">Resend</span> — <a href="https://resend.com/emails" target="_blank" rel="noreferrer" className="text-violet-300 underline">resend.com/emails</a> for delivery events.</li>
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
