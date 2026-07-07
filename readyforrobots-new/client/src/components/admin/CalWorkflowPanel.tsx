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

/** Single prioritized recommendation from live metrics — Cal's "what to do now". */
function calRecommendation(m: CalWorkflowMetrics): { tone: "warn" | "go"; text: string } {
  const pending = n(m.pending_draft);
  const noEmail = n(m.no_email);
  const sendable = n(m.sendable);
  const sent = n(m.sent);
  const replied = n(m.replied);

  // A lot sent, nothing back → stop blasting, fix targeting/copy first.
  if (sent >= 40 && replied === 0) {
    return {
      tone: "warn",
      text:
        `You've sent ${sent.toLocaleString()} intros with 0 replies. Don't send more on volume — ` +
        `fix any blocked drafts, tighten who's actually a buyer, and let the new copy prove out on a ` +
        `small batch (20–30) before another bulk send.`,
    };
  }
  if (pending > 0) {
    return {
      tone: "go",
      text:
        `Start at Step 1: draft the ${pending.toLocaleString()} pending leads, then skim a few in the ` +
        `editor before anything sends.`,
    };
  }
  if (noEmail > 0) {
    return {
      tone: "warn",
      text:
        `Step 2: ${noEmail.toLocaleString()} drafts have no contact email. Fix those first — a send with ` +
        `no address is a wasted, un-tracked attempt.`,
    };
  }
  if (sendable > 0) {
    return {
      tone: "go",
      text:
        `Step 3 → 4: review a handful of drafts for fit, then send the ${sendable.toLocaleString()} that ` +
        `are ready. Small, deliberate batches beat one big blast.`,
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
  const replied = n(metrics.replied);
  const rec = calRecommendation(metrics);

  return (
    <div className="mb-5">
      {/* Cal recommends — the AI agent's read on what to do next */}
      <div
        className={`mb-4 flex gap-3 rounded-xl border p-3 ${
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

      {/* Numbered, sequential workflow — each step wired to its API call */}
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-5">
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
          detail={`${drafted.toLocaleString()} drafted — check fit before sending`}
        >
          <SupabaseInlineLink tone="blue" onClick={onReview}>
            Review drafts below
          </SupabaseInlineLink>
        </StepCard>

        <StepCard
          index={4}
          title="Send"
          detail={`${sendable.toLocaleString()} ready to send`}
          done={sendable === 0 && drafted === 0}
        >
          <SupabaseInlineLink tone="amber" onClick={onSendAll} disabled={sendable === 0} busy={busy === "cal-send"}>
            Send {sendable > 0 ? sendable.toLocaleString() : "all"}
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
