/**
 * CalWorkflowPanel — Cal's operator flow as a numbered, sequential set of steps,
 * each wired to a real API action, plus a live "Cal recommends" banner that reads
 * the current queue state and tells the operator the single next move.
 */
import { AlertTriangle, CheckCircle2, Circle, Sparkles } from "lucide-react";
import SupabaseInlineLink from "@/components/admin/SupabaseInlineLink";

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

type Props = {
  metrics: CalWorkflowMetrics;
  autopilotEnabled?: boolean;
  busy: string;
  onDraftAll: () => void;
  onRegenerate: () => void;
  onFixEmails: () => void;
  onReinfer: () => void;
  onReview: () => void;
  onSendAll: () => void;
  onRunCal: () => void;
  onOpenReplies: () => void;
  onTestDelivery: () => void;
};

function n(v?: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : 0;
}

const STAGE_TONE: Record<"gray" | "amber" | "emerald" | "blue", string> = {
  gray: "bg-gray-100 text-gray-700",
  amber: "bg-amber-100 text-amber-900",
  emerald: "bg-emerald-100 text-emerald-800",
  blue: "bg-blue-100 text-blue-800",
};

function FunnelStage({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: keyof typeof STAGE_TONE;
}) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${STAGE_TONE[tone]}`}>
      <span className="font-bold tabular-nums">{value.toLocaleString()}</span>
      <span className="font-medium">{label}</span>
    </span>
  );
}

/** Single prioritized recommendation from live metrics — Cal's "what to do now". */
function calRecommendation(m: CalWorkflowMetrics): { tone: "warn" | "go"; text: string } {
  const pending = n(m.pending_draft);
  const noEmail = n(m.no_email);
  const sendable = n(m.sendable);
  const sent = n(m.sent);
  const replied = n(m.replied);

  // A lot sent, nothing back → stop blasting. Those were the old copy; the fix
  // is to regenerate with the new trust-first angles and prove a small batch.
  if (sent >= 40 && replied === 0 && sendable > 0) {
    return {
      tone: "warn",
      text:
        `${sent.toLocaleString()} intros are out with 0 replies so far. Don't blast — open Step 3, read 3–4 ` +
        `drafts for fit, then press the amber "Send ${sendable.toLocaleString()}" button in Step 4. That ` +
        `sends only the drafts that already have a verified contact email.`,
    };
  }
  if (pending > 0) {
    return {
      tone: "go",
      text:
        `Start at Step 1: press "Draft all pending" to write the ${pending.toLocaleString()} pending leads, ` +
        `then read a few in Step 3 before anything sends.`,
    };
  }
  if (noEmail > 0) {
    return {
      tone: "warn",
      text:
        `Step 2: ${noEmail.toLocaleString()} drafts have no contact email. Press "Fix ${noEmail.toLocaleString()} emails" ` +
        `first — a send with no address is a wasted, un-tracked attempt.`,
    };
  }
  if (sendable > 0) {
    return {
      tone: "go",
      text:
        `You have ${sendable.toLocaleString()} drafts ready. Read 3–4 in Step 3 for fit, then press the amber ` +
        `"Send ${sendable.toLocaleString()}" button in Step 4 (it asks you to confirm first). Small batches beat one blast.`,
    };
  }
  if (replied > 0) {
    return {
      tone: "go",
      text: `You have ${replied.toLocaleString()} repl${replied === 1 ? "y" : "ies"} — Step 5: work the inbox. A reply cools off fast.`,
    };
  }
  return { tone: "go", text: "Queue is clean. Keep autopilot on and check replies once a day." };
}

function StepCard({
  index,
  title,
  detail,
  done,
  children,
}: {
  index: number;
  title: string;
  detail: string;
  done?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3 rounded-xl border border-gray-200 bg-white p-3">
      <div className="mt-0.5 shrink-0">
        {done ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
        ) : (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-[11px] font-bold text-white">
            {index}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-gray-900">{title}</p>
        <p className="mt-0.5 text-[11px] text-gray-600">{detail}</p>
        <div className="mt-1.5 text-sm">{children}</div>
      </div>
    </div>
  );
}

export default function CalWorkflowPanel({
  metrics,
  autopilotEnabled,
  busy,
  onDraftAll,
  onRegenerate,
  onFixEmails,
  onReinfer,
  onReview,
  onSendAll,
  onRunCal,
  onOpenReplies,
  onTestDelivery,
}: Props) {
  const pending = n(metrics.pending_draft);
  const noEmail = n(metrics.no_email);
  const sendable = n(metrics.sendable);
  const drafted = n(metrics.drafted);
  const unsent = n(metrics.unsent_drafted);
  const sent = n(metrics.sent);
  const replied = n(metrics.replied);
  const rec = calRecommendation(metrics);

  return (
    <div className="mb-5">
      {/* Cal recommends — the AI agent's read on what to do next */}
      <div
        className={`mb-3 flex gap-3 rounded-xl border p-3 ${
          rec.tone === "warn"
            ? "border-amber-300 bg-amber-50"
            : "border-emerald-300 bg-emerald-50"
        }`}
      >
        {rec.tone === "warn" ? (
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
        ) : (
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
        )}
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-600">
            Cal recommends
          </p>
          <p className={`mt-0.5 text-sm ${rec.tone === "warn" ? "text-amber-950" : "text-emerald-950"}`}>
            {rec.text}
          </p>
        </div>
      </div>

      {/* Funnel legend — ties the numbers together so the stages read as one story */}
      <div className="mb-3 rounded-xl border border-gray-200 bg-white px-3 py-2.5">
        <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[12px] font-medium text-gray-700">
          <FunnelStage label="Pending" value={pending} tone="gray" />
          <span className="text-gray-300">→</span>
          <FunnelStage label="Drafted" value={drafted} tone="gray" />
          <span className="text-gray-300">→</span>
          <FunnelStage label="Ready to send" value={sendable} tone="amber" />
          <span className="text-gray-300">→</span>
          <FunnelStage label="Sent" value={sent} tone="emerald" />
          <span className="text-gray-300">→</span>
          <FunnelStage label="Replied" value={replied} tone="blue" />
        </div>
        <p className="mt-1.5 text-[11px] leading-snug text-gray-500">
          <strong>Pending</strong> = still needs a draft. <strong>Ready to send</strong> = a draft that
          already has a verified contact email (this is the number the Send button uses — it can differ
          from Pending). Sending never duplicates the {sent.toLocaleString()} already sent.
        </p>
      </div>

      {/* Numbered, sequential workflow — each step wired to its API call.
          One column on small screens so 1→2→3→4→5 always reads top-to-bottom;
          a single 5-across row on large screens. */}
      <div className="grid grid-cols-1 gap-2 lg:grid-cols-5">
        <StepCard
          index={1}
          title="Draft"
          detail={`${pending.toLocaleString()} leads need a draft`}
          done={pending === 0}
        >
          <SupabaseInlineLink onClick={onDraftAll} disabled={pending === 0} busy={busy === "cal-draft"}>
            Draft all pending
          </SupabaseInlineLink>
          <span className="text-gray-400"> · </span>
          <SupabaseInlineLink tone="gray" onClick={onRegenerate} busy={busy === "cal-draft"}>
            Regenerate
          </SupabaseInlineLink>
        </StepCard>

        <StepCard
          index={2}
          title="Fix contacts"
          detail={noEmail > 0 ? `${noEmail.toLocaleString()} drafts missing an email` : "All drafts have an address"}
          done={noEmail === 0}
        >
          {noEmail > 0 ? (
            <>
              <SupabaseInlineLink tone="amber" onClick={onFixEmails} busy={busy === "cleanup"}>
                Fix {noEmail.toLocaleString()} emails
              </SupabaseInlineLink>
              <span className="text-gray-400"> · </span>
            </>
          ) : null}
          <SupabaseInlineLink tone="gray" onClick={onReinfer} busy={busy === "cal-reinfer"}>
            Re-infer contacts
          </SupabaseInlineLink>
        </StepCard>

        <StepCard
          index={3}
          title="Review"
          detail="Read 3–4: right company & angle, name correct, contact looks real, no filler"
        >
          <SupabaseInlineLink tone="blue" onClick={onReview}>
            Open {drafted.toLocaleString()} drafts below
          </SupabaseInlineLink>
        </StepCard>

        <StepCard
          index={4}
          title="Send"
          detail={
            sendable > 0
              ? `${sendable.toLocaleString()} drafts with a verified email — asks you to confirm first`
              : "Nothing ready to send yet"
          }
          done={sendable === 0 && drafted === 0}
        >
          <SupabaseInlineLink tone="amber" onClick={onSendAll} disabled={sendable === 0} busy={busy === "cal-send"}>
            {sendable > 0 ? `Send ${sendable.toLocaleString()}` : "Send"}
          </SupabaseInlineLink>
        </StepCard>

        <StepCard
          index={5}
          title="Follow up"
          detail={replied > 0 ? `${replied.toLocaleString()} replied — work the inbox` : "No replies yet"}
          done={false}
        >
          <SupabaseInlineLink tone="blue" onClick={onOpenReplies}>
            Open replies{replied > 0 ? ` (${replied.toLocaleString()})` : ""}
          </SupabaseInlineLink>
        </StepCard>
      </div>

      {/* Autopilot + delivery utilities (secondary to the numbered flow) */}
      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-gray-600">
        <Circle
          className={`h-2.5 w-2.5 ${autopilotEnabled ? "fill-emerald-500 text-emerald-500" : "fill-gray-300 text-gray-300"}`}
        />
        <span className="font-medium">Autopilot {autopilotEnabled ? "ON" : "OFF"}</span>
        <span className="text-gray-300">·</span>
        <SupabaseInlineLink tone="gray" onClick={onRunCal} busy={busy === "cal-run"}>
          Run Cal now
        </SupabaseInlineLink>
        <span className="text-gray-300">·</span>
        <SupabaseInlineLink tone="gray" onClick={onTestDelivery}>
          Test delivery
        </SupabaseInlineLink>
      </div>
    </div>
  );
}
