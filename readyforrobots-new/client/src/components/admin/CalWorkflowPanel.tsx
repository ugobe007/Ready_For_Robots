/**
 * Cal operator workflow — one rail, one count per step, one primary action each.
 * No duplicate funnel pills, no decorative metric tiles, no passive "recommends" box.
 */
import { AlertTriangle, Bot, ChevronRight } from "lucide-react";

export type CalWorkflowMetrics = {
  total?: number;
  pending_draft?: number;
  no_email?: number;
  drafted?: number;
  unsent_drafted?: number;
  sendable?: number;
  sent?: number;
  opened?: number;
  replied?: number;
};

export type CalWorkflowStepId =
  | "fix_contacts"
  | "draft"
  | "redraft"
  | "review"
  | "send"
  | "follow_up";

type Props = {
  metrics: CalWorkflowMetrics;
  autopilotEnabled?: boolean;
  activeStep?: CalWorkflowStepId | null;
  busy: string;
  onDraftAll: () => void;
  onRedraft: () => void;
  onFixEmails: () => void;
  onReinfer: () => void;
  onReview: () => void;
  onSendAll: () => void;
  onRunCal: () => void;
  onOpenReplies: () => void;
  onTestDelivery: () => void;
  onStepFocus?: (step: CalWorkflowStepId) => void;
};

function n(v?: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : 0;
}

type StepDef = {
  id: CalWorkflowStepId;
  num: string;
  label: string;
  count: (m: CalWorkflowMetrics) => number;
  hint: string;
};

const STEPS: StepDef[] = [
  {
    id: "fix_contacts",
    num: "1",
    label: "Fix contacts",
    count: (m) => n(m.no_email),
    hint: "Drafts missing a send address",
  },
  {
    id: "draft",
    num: "2",
    label: "Draft",
    count: (m) => n(m.pending_draft),
    hint: "HOT/WARM leads with no Cal email yet",
  },
  {
    id: "redraft",
    num: "3",
    label: "Redraft",
    count: (m) => n(m.unsent_drafted) || n(m.drafted),
    hint: "Refresh voice & angle on existing drafts",
  },
  {
    id: "review",
    num: "4",
    label: "Review",
    count: (m) => n(m.unsent_drafted) || n(m.drafted),
    hint: "Read drafts before anything sends",
  },
  {
    id: "send",
    num: "5",
    label: "Send",
    count: (m) => n(m.sendable),
    hint: "Verified email + approved draft",
  },
  {
    id: "follow_up",
    num: "6",
    label: "Follow up",
    count: (m) => n(m.replied),
    hint: "Replies waiting in inbox",
  },
];

function suggestStep(m: CalWorkflowMetrics): CalWorkflowStepId {
  const noEmail = n(m.no_email);
  const pending = n(m.pending_draft);
  const sendable = n(m.sendable);
  const unsent = n(m.unsent_drafted) || n(m.drafted);
  const sent = n(m.sent);
  const replied = n(m.replied);

  if (noEmail > 0) return "fix_contacts";
  if (pending > 0) return "draft";
  if (sent >= 20 && replied === 0 && unsent > 0) return "redraft";
  if (sendable > 0 && unsent > 0) return "review";
  if (sendable > 0) return "send";
  if (replied > 0) return "follow_up";
  if (unsent > 0) return "review";
  return "follow_up";
}

type DoNow = {
  step: CalWorkflowStepId;
  title: string;
  detail: string;
  actionLabel: string;
  onAction: () => void;
  disabled?: boolean;
  busyKey?: string;
  tone: "warn" | "go";
};

function buildDoNow(
  m: CalWorkflowMetrics,
  handlers: Pick<
    Props,
    | "onFixEmails"
    | "onDraftAll"
    | "onRedraft"
    | "onReview"
    | "onSendAll"
    | "onOpenReplies"
  >,
): DoNow {
  const step = suggestStep(m);
  const noEmail = n(m.no_email);
  const pending = n(m.pending_draft);
  const sendable = n(m.sendable);
  const unsent = n(m.unsent_drafted) || n(m.drafted);
  const sent = n(m.sent);
  const replied = n(m.replied);

  switch (step) {
    case "fix_contacts":
      return {
        step,
        tone: "warn",
        title: "Fix contacts first",
        detail: `${noEmail.toLocaleString()} draft${noEmail === 1 ? "" : "s"} can't send without an email address.`,
        actionLabel: `Fix ${noEmail.toLocaleString()} email${noEmail === 1 ? "" : "s"}`,
        onAction: handlers.onFixEmails,
        disabled: noEmail === 0,
        busyKey: "cleanup",
      };
    case "draft":
      return {
        step,
        tone: "go",
        title: "Write first drafts",
        detail: `${pending.toLocaleString()} HOT/WARM lead${pending === 1 ? "" : "s"} still need Cal's intro.`,
        actionLabel: `Draft ${pending.toLocaleString()} pending`,
        onAction: handlers.onDraftAll,
        disabled: pending === 0,
        busyKey: "cal-draft",
      };
    case "redraft":
      return {
        step,
        tone: "warn",
        title: "Redraft before you send",
        detail:
          `${sent.toLocaleString()} intros out with ${replied} repl${replied === 1 ? "y" : "ies"}. ` +
          `Refresh ${unsent.toLocaleString()} unsent draft${unsent === 1 ? "" : "s"} to the current Cal voice before review.`,
        actionLabel: `Redraft ${unsent.toLocaleString()}`,
        onAction: handlers.onRedraft,
        disabled: unsent === 0,
        busyKey: "cal-draft",
      };
    case "review":
      return {
        step,
        tone: sendable > 0 ? "warn" : "go",
        title: "Review before send",
        detail:
          sendable > 0
            ? `${sendable.toLocaleString()} ready to send — read 3–4 drafts for fit, names, and angle first.`
            : `${unsent.toLocaleString()} unsent draft${unsent === 1 ? "" : "s"} in the queue below.`,
        actionLabel: "Open review queue",
        onAction: handlers.onReview,
      };
    case "send":
      return {
        step,
        tone: "go",
        title: "Send a small batch",
        detail: `${sendable.toLocaleString()} draft${sendable === 1 ? "" : "s"} have verified emails. You'll confirm before anything goes out.`,
        actionLabel: `Send ${sendable.toLocaleString()}`,
        onAction: handlers.onSendAll,
        disabled: sendable === 0,
        busyKey: "cal-send",
      };
    case "follow_up":
    default:
      return {
        step: "follow_up",
        tone: replied > 0 ? "go" : "go",
        title: replied > 0 ? "Work the inbox" : "Queue is caught up",
        detail:
          replied > 0
            ? `${replied.toLocaleString()} repl${replied === 1 ? "y" : "ies"} waiting — Cal pauses automation when someone writes back.`
            : "Autopilot handles the next draft/send cycle. Check replies once a day.",
        actionLabel: replied > 0 ? `Open ${replied.toLocaleString()} repl${replied === 1 ? "y" : "ies"}` : "Open inbox",
        onAction: handlers.onOpenReplies,
      };
  }
}

function StepButton({
  label,
  disabled,
  busy,
  tone,
  onClick,
}: {
  label: string;
  disabled?: boolean;
  busy?: boolean;
  tone: "primary" | "secondary" | "amber";
  onClick: () => void;
}) {
  const base =
    "mt-2 w-full rounded-lg px-2.5 py-2 text-[11px] font-bold transition disabled:cursor-not-allowed disabled:opacity-40";
  const styles =
    tone === "primary"
      ? "bg-emerald-600 text-white hover:bg-emerald-700"
      : tone === "amber"
        ? "bg-amber-500 text-gray-950 hover:bg-amber-400"
        : "border border-gray-300 bg-white text-gray-800 hover:border-gray-400 hover:bg-gray-50";
  return (
    <button type="button" className={`${base} ${styles}`} disabled={disabled || busy} onClick={onClick}>
      {busy ? "Working…" : label}
    </button>
  );
}

export default function CalWorkflowPanel({
  metrics,
  autopilotEnabled,
  activeStep,
  busy,
  onDraftAll,
  onRedraft,
  onFixEmails,
  onReinfer,
  onReview,
  onSendAll,
  onRunCal,
  onOpenReplies,
  onTestDelivery,
  onStepFocus,
}: Props) {
  const suggested = suggestStep(metrics);
  const focused = activeStep ?? suggested;
  const doNow = buildDoNow(metrics, {
    onFixEmails,
    onDraftAll,
    onRedraft,
    onReview,
    onSendAll,
    onOpenReplies,
  });

  const unsent = n(metrics.unsent_drafted) || n(metrics.drafted);
  const sent = n(metrics.sent);

  return (
    <div className="mb-5">
      {/* Do now — one action, tied to the step rail */}
      <div
        className={`mb-4 flex flex-col gap-3 rounded-xl border-2 p-4 sm:flex-row sm:items-center sm:justify-between ${
          doNow.tone === "warn"
            ? "border-amber-500 bg-amber-50"
            : "border-emerald-600 bg-emerald-50"
        }`}
      >
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
              doNow.tone === "warn" ? "bg-amber-500 text-white" : "bg-emerald-600 text-white"
            }`}
          >
            {doNow.tone === "warn" ? (
              <AlertTriangle className="h-5 w-5" />
            ) : (
              <Bot className="h-5 w-5" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-700">
              Do now · Step {STEPS.find((s) => s.id === doNow.step)?.num}
            </p>
            <p className="text-sm font-extrabold text-gray-950">{doNow.title}</p>
            <p className="mt-0.5 text-xs leading-snug text-gray-700">{doNow.detail}</p>
          </div>
        </div>
        <StepButton
          label={doNow.actionLabel}
          tone={doNow.step === "send" ? "amber" : "primary"}
          disabled={doNow.disabled}
          busy={!!doNow.busyKey && busy === doNow.busyKey}
          onClick={doNow.onAction}
        />
      </div>

      {/* Single workflow rail — count on each step matches the action below */}
      <div className="overflow-x-auto rounded-xl border-2 border-gray-900 bg-gray-950 p-3 text-white">
        <div className="mb-2 flex items-center justify-between gap-2">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Cal workflow
          </p>
          <p className="text-[10px] text-gray-400">
            Autopilot{" "}
            <span className={autopilotEnabled ? "font-bold text-emerald-400" : "font-bold text-amber-400"}>
              {autopilotEnabled ? "ON" : "OFF"}
            </span>
            <span className="text-gray-600"> · </span>
            {sent.toLocaleString()} sent · {unsent.toLocaleString()} unsent
          </p>
        </div>

        <div className="flex min-w-[52rem] items-stretch gap-1">
          {STEPS.map((step, i) => {
            const count = step.count(metrics);
            const isActive = focused === step.id;
            const isSuggested = suggested === step.id;
            return (
              <div key={step.id} className="flex flex-1 items-stretch">
                <button
                  type="button"
                  onClick={() => onStepFocus?.(step.id)}
                  className={`flex flex-1 flex-col rounded-lg border px-2.5 py-2.5 text-left transition ${
                    isActive
                      ? "border-amber-400 bg-gray-900 ring-1 ring-amber-400/60"
                      : isSuggested
                        ? "border-emerald-500/50 bg-gray-900 hover:border-emerald-400"
                        : "border-gray-700 bg-gray-900/80 hover:border-gray-500"
                  }`}
                >
                  <div className="mb-1 flex items-center gap-1.5">
                    <span className="text-[10px] font-bold text-gray-500">{step.num}</span>
                    <span className="text-xs font-bold text-white">{step.label}</span>
                    {count > 0 ? (
                      <span
                        className={`ml-auto rounded-full px-1.5 py-0.5 text-[10px] font-bold tabular-nums ${
                          isActive ? "bg-amber-400 text-gray-950" : "bg-gray-700 text-gray-100"
                        }`}
                      >
                        {count.toLocaleString()}
                      </span>
                    ) : null}
                  </div>
                  <p className="text-[10px] leading-snug text-gray-400">{step.hint}</p>
                </button>
                {i < STEPS.length - 1 ? (
                  <ChevronRight className="mx-0.5 h-4 w-4 shrink-0 self-center text-gray-600" />
                ) : null}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step actions — one primary button per step, visible (not buried links) */}
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <div className="rounded-xl border border-gray-300 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">1 · Fix</p>
          <StepButton
            label={`Fix ${n(metrics.no_email).toLocaleString()} emails`}
            tone="secondary"
            disabled={n(metrics.no_email) === 0}
            busy={busy === "cleanup"}
            onClick={onFixEmails}
          />
          <button
            type="button"
            className="mt-1.5 text-[10px] font-medium text-gray-500 underline underline-offset-2 hover:text-gray-800"
            disabled={busy === "cal-reinfer"}
            onClick={onReinfer}
          >
            {busy === "cal-reinfer" ? "Re-inferring…" : "Re-infer contacts"}
          </button>
        </div>

        <div className="rounded-xl border border-gray-300 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">2 · Draft</p>
          <StepButton
            label={`Draft ${n(metrics.pending_draft).toLocaleString()} pending`}
            tone="primary"
            disabled={n(metrics.pending_draft) === 0}
            busy={busy === "cal-draft" && n(metrics.pending_draft) > 0}
            onClick={onDraftAll}
          />
        </div>

        <div className="rounded-xl border border-amber-300 bg-amber-50/80 p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-amber-900">3 · Redraft</p>
          <StepButton
            label={`Redraft ${unsent.toLocaleString()}`}
            tone="amber"
            disabled={unsent === 0}
            busy={busy === "cal-draft" && n(metrics.pending_draft) === 0}
            onClick={onRedraft}
          />
          <p className="mt-1.5 text-[10px] leading-snug text-amber-950/80">
            Rewrites all unsent drafts with Cal&apos;s current voice.
          </p>
        </div>

        <div className="rounded-xl border border-gray-300 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">4 · Review</p>
          <StepButton label="Open queue" tone="secondary" onClick={onReview} />
        </div>

        <div className="rounded-xl border border-gray-300 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">5 · Send</p>
          <StepButton
            label={`Send ${n(metrics.sendable).toLocaleString()}`}
            tone="amber"
            disabled={n(metrics.sendable) === 0}
            busy={busy === "cal-send"}
            onClick={onSendAll}
          />
        </div>

        <div className="rounded-xl border border-gray-300 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">6 · Follow up</p>
          <StepButton
            label={n(metrics.replied) > 0 ? `Inbox (${n(metrics.replied)})` : "Open inbox"}
            tone="secondary"
            onClick={onOpenReplies}
          />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-gray-600">
        <button
          type="button"
          className="font-semibold text-gray-800 underline underline-offset-2 hover:text-gray-950 disabled:opacity-40"
          disabled={busy === "cal-run"}
          onClick={onRunCal}
        >
          {busy === "cal-run" ? "Running Cal…" : "Run Cal now"}
        </button>
        <span className="text-gray-300">·</span>
        <button
          type="button"
          className="font-medium text-gray-600 underline underline-offset-2 hover:text-gray-900"
          onClick={onTestDelivery}
        >
          Test delivery
        </button>
        <span className="text-gray-300">·</span>
        <span>
          Opened {n(metrics.opened).toLocaleString()} · Sent {sent.toLocaleString()} total
        </span>
      </div>
    </div>
  );
}
