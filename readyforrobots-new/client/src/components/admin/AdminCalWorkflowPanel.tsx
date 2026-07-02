import { ArrowRight, FileText, List, Mail, Play, Send, ShieldCheck } from "lucide-react";
import { Link } from "wouter";

type Summary = {
  hot?: number;
  warm?: number;
  sendable?: number;
  pending_draft?: number;
  drafted?: number;
  sent?: number;
  needs_approval?: number;
  no_email?: number;
  unsent_drafted?: number;
};

type Props = {
  summary: Summary | null | undefined;
  autopilotEnabled: boolean;
  everyHours: number;
  sendLimit: number;
  manualApproval: boolean;
  assemblyRequired: boolean;
  busy: boolean;
  onRunCal: () => void;
  onSendAll: () => void;
  onDraftPending: () => void;
  onScrollToQueue: () => void;
  onApproveAll?: () => void;
};

function StepCard({
  step,
  title,
  description,
  children,
}: {
  step: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-700">Step {step}</p>
      <h2 className="mt-1 font-display text-base font-bold text-gray-950">{title}</h2>
      <p className="mt-1 text-sm leading-relaxed text-gray-700">{description}</p>
      <div className="mt-4 flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

export default function AdminCalWorkflowPanel({
  summary,
  autopilotEnabled,
  everyHours,
  sendLimit,
  manualApproval,
  assemblyRequired,
  busy,
  onRunCal,
  onSendAll,
  onDraftPending,
  onScrollToQueue,
  onApproveAll,
}: Props) {
  const sendable = summary?.sendable ?? 0;
  const pending = summary?.pending_draft ?? 0;
  const needsApproval = summary?.needs_approval ?? 0;
  const noEmail = summary?.no_email ?? 0;
  const unsentDrafted = summary?.unsent_drafted ?? summary?.drafted ?? 0;
  const hot = summary?.hot ?? 0;
  const warm = summary?.warm ?? 0;

  return (
    <div className="mb-6 space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
        <p className="text-sm font-bold text-gray-950">Cal buyer queue (admin-cal-outreach)</p>
        <p className="mt-1 text-sm text-gray-700">
          This tab is the operator send list — not the public pipeline page. Cal emails HOT/WARM scored buyers
          ({hot} hot · {warm} warm) who have CRM drafts on your admin team.
        </p>
        <p className="mt-2 text-xs text-gray-600">
          Worker autopilot is {autopilotEnabled ? "on" : "off"} (every {everyHours}h, up to {sendLimit} intros/run).
          {assemblyRequired ? " Autopilot sends pass the assembly review gate." : " Assembly review is off."}
          {manualApproval ? " Manual approval is required before any send." : " Drafts are sendable once written (no approve step)."}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs">
          <span className="text-gray-500">Need draft</span>
          <p className="text-lg font-black text-gray-900">{pending}</p>
        </div>
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-2.5 text-xs">
          <span className="text-blue-800">Unsent drafts</span>
          <p className="text-lg font-black text-blue-950">{unsentDrafted}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-xs">
          <span className="text-emerald-800">Sendable now</span>
          <p className="text-lg font-black text-emerald-950">{sendable}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs">
          <span className="text-amber-800">Blocked</span>
          <p className="text-lg font-black text-amber-950">
            {needsApproval > 0 ? `${needsApproval} need approve` : noEmail > 0 ? `${noEmail} no email` : "—"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        <StepCard
          step="1"
          title="Generate drafts"
          description={
            pending > 0
              ? `${pending} HOT/WARM lead(s) have no Cal draft yet. Draft them before preview or send.`
              : "All leads in the Cal universe have drafts. Skip to preview unless you want to regenerate."
          }
        >
          <button
            type="button"
            disabled={busy || pending === 0}
            onClick={onDraftPending}
            className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2.5 text-sm font-bold text-emerald-900 disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            Draft pending ({pending})
          </button>
          <Link
            href="/pipeline"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-semibold text-gray-700"
          >
            Review lead quality
            <ArrowRight className="h-4 w-4" />
          </Link>
        </StepCard>

        <StepCard
          step="2"
          title="Preview & edit"
          description={`Expand a row in the queue below (filter: drafted). ${sendable} sendable · ${noEmail} missing contact email.`}
        >
          <button
            type="button"
            onClick={onScrollToQueue}
            className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-bold text-blue-900"
          >
            <List className="h-4 w-4" />
            Open send queue
          </button>
        </StepCard>

        {manualApproval ? (
          <StepCard
            step="3"
            title="Approve drafts"
            description={
              needsApproval > 0
                ? `${needsApproval} draft(s) must be approved before Send all ready or per-row send.`
                : "All unsent drafts are approved."
            }
          >
            <button
              type="button"
              disabled={busy || needsApproval === 0 || !onApproveAll}
              onClick={onApproveAll}
              className="inline-flex items-center gap-2 rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-bold text-violet-900 disabled:opacity-50"
            >
              <ShieldCheck className="h-4 w-4" />
              Approve all ({needsApproval})
            </button>
          </StepCard>
        ) : null}

        <StepCard
          step={manualApproval ? "4" : "3"}
          title="Send (pick one path)"
          description="Run Cal now = draft + assembly-gated send + follow-ups. Send all ready = only sends existing sendable drafts (skips assembly)."
        >
          <button
            type="button"
            disabled={busy}
            onClick={onRunCal}
            className="inline-flex items-center gap-2 rounded-xl border border-emerald-500 bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {busy ? "Running…" : "Run Cal now"}
          </button>
          <button
            type="button"
            disabled={busy || sendable === 0}
            onClick={onSendAll}
            className="inline-flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-100 px-4 py-2.5 text-sm font-bold text-amber-950 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            Send all ready ({sendable})
          </button>
          <Link
            href="/sales-workflow"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-semibold text-gray-700"
          >
            <Mail className="h-4 w-4" />
            Replies
          </Link>
        </StepCard>
      </div>
    </div>
  );
}
