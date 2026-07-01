/**
 * ScoutActionBar — Cal autopilot controls (draft, send, follow-up on schedule)
 */
import { useState } from "react";
import { Zap, Inbox, List, FlaskConical, X, RefreshCw, AlertTriangle, XCircle, CheckCircle2 } from "lucide-react";
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

interface DiagnosticData {
  config: { from_email: string | null; reply_to: string | null; api_key_set: boolean; delivery_webhook_configured: boolean; inbound_webhook_configured: boolean };
  stats_30d: { sent: number; delivered: number; opened: number; clicked: number; bounced: number; replied: number; total: number };
  recent_emails: Array<{ id: string; to: string; subject: string; status: string; sent_at: string | null; company: string }>;
  issues: string[];
  health: "ok" | "warn" | "error";
}

interface Props {
  accessToken: string | undefined;
  stats: ScoutStats | null;
  busy: "run" | null;
  autopilotEnabled?: boolean;
  everyHours?: number;
  sendLimit?: number;
  onRunNow: () => void;
  onViewQueue: () => void;
  onViewReplies: () => void;
}

export default function ScoutActionBar({
  accessToken,
  stats,
  busy,
  autopilotEnabled = true,
  everyHours = 3,
  sendLimit = 25,
  onRunNow,
  onViewQueue,
  onViewReplies,
}: Props) {
  const [testOpen, setTestOpen] = useState(false);
  const [diagnostic, setDiagnostic] = useState<DiagnosticData | null>(null);
  const [loadingDiag, setLoadingDiag] = useState(false);

  const openTest = async () => {
    setTestOpen(true);
    if (diagnostic || !accessToken) return;
    setLoadingDiag(true);
    try {
      const r = await fetch(`${getApiBase()}/api/admin/scout/diagnostic`, liveFetchInit({ headers: authHeader(accessToken) }));
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
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-gradient-to-r from-emerald-50 to-white px-4 py-3">
        <div className="mr-1 min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-800">Cal autopilot</p>
          <p className="text-[10px] text-gray-600">
            {autopilotEnabled
              ? `On · drafts, sends (${sendLimit}/run), follow-ups every ${everyHours}h`
              : "Off · enable on worker or Run Cal now"}
          </p>
        </div>

        <button
          type="button"
          disabled={!!busy}
          onClick={onRunNow}
          className="flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-100 px-3 py-1.5 text-[11px] font-bold text-emerald-900 disabled:opacity-50"
        >
          {busy === "run" ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
          Run Cal now
        </button>

        <button
          type="button"
          onClick={onViewQueue}
          className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-blue-900"
        >
          <List className="h-3 w-3" />
          Queue{stats?.sendable ? ` (${stats.sendable})` : ""}
        </button>

        <button
          type="button"
          onClick={onViewReplies}
          className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-[11px] font-bold text-amber-900"
        >
          <Inbox className="h-3 w-3" />
          Replies{stats?.replied ? ` (${stats.replied})` : ""}
        </button>

        <button
          type="button"
          onClick={() => void openTest()}
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-[11px] font-bold text-violet-800"
        >
          <FlaskConical className="h-3 w-3" />
          TEST
        </button>
      </div>

      {testOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.75)" }} onClick={() => setTestOpen(false)}>
          <div className="relative w-full max-w-lg rounded-2xl border bg-[#0d0520] p-6" style={{ borderColor: "rgba(124,58,237,0.35)" }} onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm font-bold text-white">Cal delivery health</p>
              <button onClick={() => setTestOpen(false)}><X className="h-4 w-4 text-white/50" /></button>
            </div>
            {loadingDiag && <p className="text-sm text-white/40">Running…</p>}
            {diagnostic && (
              <div className="space-y-2 text-[11px] text-white/70">
                {diagnostic.issues.map((issue, i) => (
                  <p key={i} className="flex gap-2"><AlertTriangle className="h-3 w-3 text-amber-400 shrink-0" />{issue}</p>
                ))}
                {!diagnostic.issues.length && (
                  <p className="flex gap-2"><CheckCircle2 className="h-3 w-3 text-emerald-400" />Routing and API key look OK.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
