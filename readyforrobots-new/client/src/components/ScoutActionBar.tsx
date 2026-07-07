/**
 * ScoutActionBar — Cal autopilot controls (Supabase inline links only)
 */
import { useState } from "react";
import { AlertTriangle, CheckCircle2, X } from "lucide-react";
import { toast } from "sonner";
import SupabaseInlineLink from "@/components/admin/SupabaseInlineLink";
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
  config: {
    from_email: string | null;
    reply_to: string | null;
    api_key_set: boolean;
    delivery_webhook_configured: boolean;
    inbound_webhook_configured: boolean;
    webhook_urls?: { delivery: string; inbound: string };
  };
  stats_30d: { sent: number; delivered: number; opened: number; clicked: number; bounced: number; replied: number; total: number };
  recent_emails: Array<{ id: string; to: string; subject: string; status: string; sent_at: string | null; company: string }>;
  issues: string[];
  hints?: string[];
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
      <div className="border-b border-gray-200 bg-gradient-to-r from-emerald-50 to-white px-4 py-3 text-sm">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-800">Cal autopilot</p>
        <p className="mb-1 text-[10px] text-gray-600">
          {autopilotEnabled
            ? `On · drafts, sends (${sendLimit}/run), follow-ups every ${everyHours}h`
            : "Off · enable on worker or run Cal now"}
        </p>
        <div>
          <SupabaseInlineLink onClick={onRunNow} busy={busy === "run"}>
            Run Cal now
          </SupabaseInlineLink>
          <span className="text-gray-400"> · </span>
          <SupabaseInlineLink tone="blue" onClick={onViewQueue}>
            Queue{stats?.sendable ? ` (${stats.sendable} sendable)` : ""}
          </SupabaseInlineLink>
          <span className="text-gray-400"> · </span>
          <SupabaseInlineLink tone="amber" onClick={onViewReplies}>
            Replies{stats?.replied ? ` (${stats.replied})` : ""}
          </SupabaseInlineLink>
          <span className="text-gray-400"> · </span>
          <SupabaseInlineLink tone="gray" onClick={() => void openTest()}>
            Test delivery
          </SupabaseInlineLink>
        </div>
      </div>

      {testOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.75)" }} onClick={() => setTestOpen(false)}>
          <div className="relative w-full max-w-lg rounded-2xl border bg-[#0d0520] p-6" style={{ borderColor: "rgba(124,58,237,0.35)" }} onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm font-bold text-white">Cal delivery health</p>
              <SupabaseInlineLink tone="gray" onClick={() => setTestOpen(false)} className="text-white/70 hover:text-white">
                Close
              </SupabaseInlineLink>
            </div>
            {loadingDiag && <p className="text-sm text-white/40">Running…</p>}
            {diagnostic && (
              <div className="space-y-3 text-[11px] text-white/70">
                <div className="grid grid-cols-4 gap-2 rounded-lg border border-white/10 bg-white/5 p-2 text-center">
                  {(["sent", "opened", "clicked", "replied"] as const).map((k) => (
                    <div key={k}>
                      <p className="text-lg font-bold text-white">{diagnostic.stats_30d[k]}</p>
                      <p className="text-[9px] uppercase tracking-wider text-white/40">{k} · 30d</p>
                    </div>
                  ))}
                </div>
                {diagnostic.issues.map((issue, i) => (
                  <p key={i} className="flex gap-2"><AlertTriangle className="h-3 w-3 text-amber-400 shrink-0" />{issue}</p>
                ))}
                {!diagnostic.issues.length && (
                  <p className="flex gap-2"><CheckCircle2 className="h-3 w-3 text-emerald-400" />API key and webhook secrets are set on Fly.</p>
                )}
                {(diagnostic.hints ?? []).map((hint, i) => (
                  <p key={`h-${i}`} className="text-white/50">{hint}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
