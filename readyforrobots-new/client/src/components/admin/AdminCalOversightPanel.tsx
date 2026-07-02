import { AlertCircle, Bot, Calendar, CheckCircle2, Clock, Mail, MessageSquare, Play, RefreshCw, Send } from "lucide-react";
import { Link } from "wouter";

export type CalActivityTimelineItem = {
  id?: string;
  kind?: string;
  at?: string | null;
  title?: string;
  detail?: string;
  entity?: string;
  action_url?: string;
};

export type CalActivityData = {
  autopilot?: {
    enabled?: boolean;
    every_hours?: number;
    send_limit?: number;
    followup_limit?: number;
    manual_approval?: boolean;
    assembly?: { assembly_required?: boolean; llm_review_enabled?: boolean };
  };
  sequences?: { active?: number; due_now?: number; paused?: number };
  timeline?: CalActivityTimelineItem[];
  needs_you?: Array<{ kind?: string; title?: string; detail?: string; action_url?: string }>;
  capabilities?: {
    draft_autonomous?: boolean;
    send_autonomous?: boolean;
    followup_autonomous?: boolean;
    reply_autonomous?: boolean;
    meeting_autonomous?: boolean;
    meeting_note?: string;
  };
};

type Props = {
  data: CalActivityData | null;
  loading?: boolean;
  busy?: boolean;
  onRefresh: () => void;
  onRunCal: () => void;
  onOpenQueue: () => void;
};

const KIND_LABEL: Record<string, string> = {
  intro_sent: "Intro sent",
  followup_sent: "Follow-up sent",
  reply_received: "Reply received",
  auto_reply_sent: "Cal auto-replied",
  cal_planned_action: "Cal planned",
  assembly_blocked: "Blocked by assembly",
};

function formatWhen(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export default function AdminCalOversightPanel({
  data,
  loading,
  busy,
  onRefresh,
  onRunCal,
  onOpenQueue,
}: Props) {
  const ap = data?.autopilot;
  const caps = data?.capabilities;
  const seq = data?.sequences;

  return (
    <div className="mb-6 space-y-4">
      <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-white px-5 py-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-emerald-600 p-2.5 text-white">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-display text-lg font-bold text-gray-950">Cal is your autonomous operator</h2>
              <p className="mt-1 max-w-2xl text-sm text-gray-700">
                Cal drafts HOT/WARM buyer emails, sends them on schedule, runs day-3/day-7 follow-ups, and auto-replies to
                inbound messages. You only step in to edit copy, approve edge cases, or book meetings Cal cannot schedule alone.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              type="button"
              onClick={onRunCal}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-xl border border-emerald-400 bg-emerald-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5" />
              Run cycle now
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
          <span className="rounded-full border border-emerald-300 bg-emerald-100 px-3 py-1 font-semibold text-emerald-900">
            Autopilot {ap?.enabled ? "ON" : "OFF"} · every {ap?.every_hours ?? 3}h · up to {ap?.send_limit ?? 25} intros/run
          </span>
          {ap?.assembly?.assembly_required ? (
            <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 font-semibold text-violet-900">
              Assembly review ON{ap.assembly.llm_review_enabled ? " + LLM" : ""}
            </span>
          ) : null}
          {ap?.manual_approval ? (
            <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 font-semibold text-amber-900">
              Manual approval required before send
            </span>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {[
          { label: "Drafts", ok: caps?.draft_autonomous, icon: Mail },
          { label: "Sends", ok: caps?.send_autonomous, icon: Send },
          { label: "Follow-ups", ok: caps?.followup_autonomous, icon: Clock },
          { label: "Replies", ok: caps?.reply_autonomous, icon: MessageSquare },
          { label: "Meetings", ok: caps?.meeting_autonomous, icon: Calendar, note: caps?.meeting_note },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-gray-200 bg-white px-3 py-3">
            <div className="flex items-center gap-2">
              <item.icon className="h-4 w-4 text-gray-500" />
              <span className="text-xs font-bold text-gray-800">{item.label}</span>
              {item.ok ? (
                <CheckCircle2 className="ml-auto h-4 w-4 text-emerald-600" />
              ) : (
                <AlertCircle className="ml-auto h-4 w-4 text-amber-600" />
              )}
            </div>
            <p className="mt-1 text-[10px] leading-relaxed text-gray-600">
              {item.ok ? "Autonomous" : item.note || "You confirm in admin"}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 lg:col-span-1">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Follow-up sequences</p>
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-600">Active</span><span className="font-bold">{seq?.active ?? 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-600">Due now</span><span className="font-bold text-emerald-700">{seq?.due_now ?? 0}</span></div>
            <div className="flex justify-between"><span className="text-gray-600">Paused (replied)</span><span className="font-bold">{seq?.paused ?? 0}</span></div>
          </div>
        </div>

        <div className="rounded-2xl border border-amber-200 bg-amber-50/40 p-4 lg:col-span-2">
          <p className="text-[10px] font-bold uppercase tracking-widest text-amber-900">Needs you</p>
          {loading ? (
            <p className="mt-3 text-sm text-gray-600">Loading…</p>
          ) : (data?.needs_you?.length ?? 0) === 0 ? (
            <p className="mt-3 text-sm text-gray-700">Nothing flagged — Cal is handling the loop. Check activity below or open the draft queue to spot-check copy.</p>
          ) : (
            <ul className="mt-3 max-h-48 space-y-2 overflow-y-auto">
              {(data?.needs_you ?? []).map((item, idx) => (
                <li key={`${item.title}-${idx}`} className="rounded-lg border border-amber-200 bg-white px-3 py-2">
                  <Link href={item.action_url || "/sales-console"} className="block">
                    <p className="text-sm font-bold text-gray-900">{item.title}</p>
                    {item.detail ? <p className="text-xs text-gray-600">{item.detail}</p> : null}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" onClick={onOpenQueue} className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-800">
              Edit draft queue
            </button>
            <Link href="/sales-console" className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-800">
              Sales console
            </Link>
            <Link href="/calendar" className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-800">
              Calendar
            </Link>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Recent Cal activity</p>
        {loading ? (
          <p className="mt-4 py-6 text-center text-sm text-gray-500">Loading activity…</p>
        ) : (data?.timeline?.length ?? 0) === 0 ? (
          <p className="mt-4 py-6 text-center text-sm text-gray-500">No recent sends or replies yet — autopilot will populate this after the next cycle.</p>
        ) : (
          <div className="mt-3 max-h-80 overflow-y-auto">
            {(data?.timeline ?? []).map((row) => (
              <div key={row.id || `${row.at}-${row.title}`} className="flex flex-wrap items-start gap-3 border-b border-gray-100 py-3 last:border-b-0">
                <div className="min-w-[110px] text-[11px] text-gray-400">{formatWhen(row.at)}</div>
                <div className="min-w-[100px]">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-700">
                    {KIND_LABEL[row.kind || ""] || row.kind || "event"}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-gray-900">{row.title}</p>
                  <p className="text-xs text-gray-600">{row.entity}{row.detail ? ` · ${row.detail}` : ""}</p>
                </div>
                {row.action_url ? (
                  <Link href={row.action_url} className="shrink-0 text-xs font-bold text-emerald-700 hover:underline">
                    Open
                  </Link>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
