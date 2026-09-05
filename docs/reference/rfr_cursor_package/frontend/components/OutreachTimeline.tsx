/**
 * OutreachTimeline — shows the 4-step SCOUT outreach sequence for a lead.
 * Steps: Intro Email → Follow-up (2d) → LinkedIn (5d) → Final (14d)
 * Accepts a currentStep (0-based) and mode to show Assisted vs Auto-pilot state.
 */
import { Mail, Linkedin, MessageSquare, CheckCircle2, Clock, Pause } from "lucide-react";

export type OutreachMode = "assisted" | "autopilot";

export type OutreachStep = {
  label: string;
  channel: "email" | "linkedin" | "message";
  delay: string;
  status: "sent" | "scheduled" | "pending" | "paused";
  sentAt?: string;
};

const CHANNEL_ICON = {
  email: Mail,
  linkedin: Linkedin,
  message: MessageSquare,
};

const STATUS_STYLE: Record<OutreachStep["status"], { color: string; bg: string; label: string }> = {
  sent:      { color: "#03DAC5", bg: "rgba(3,218,197,0.12)",  label: "Sent" },
  scheduled: { color: "#FFB000", bg: "rgba(255,176,0,0.12)",  label: "Scheduled" },
  pending:   { color: "rgba(255,255,255,0.3)", bg: "rgba(255,255,255,0.04)", label: "Pending" },
  paused:    { color: "#a78bfa", bg: "rgba(167,139,250,0.12)", label: "Paused" },
};

function defaultSteps(mode: OutreachMode): OutreachStep[] {
  return [
    {
      label: "Intro email",
      channel: "email",
      delay: "Now",
      status: mode === "autopilot" ? "scheduled" : "pending",
    },
    {
      label: "Follow-up",
      channel: "email",
      delay: "2d if no reply",
      status: "pending",
    },
    {
      label: "LinkedIn touch",
      channel: "linkedin",
      delay: "5d if no reply",
      status: "pending",
    },
    {
      label: "Final follow-up",
      channel: "email",
      delay: "14d if no reply",
      status: "pending",
    },
  ];
}

export default function OutreachTimeline({
  mode = "assisted",
  steps,
  onPause,
}: {
  mode?: OutreachMode;
  steps?: OutreachStep[];
  onPause?: () => void;
}) {
  const displaySteps = steps ?? defaultSteps(mode);

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: "1px solid rgba(255,255,255,0.07)", background: "rgba(255,255,255,0.02)" }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.02)" }}
      >
        <div className="flex items-center gap-2">
          <Clock className="h-3.5 w-3.5" style={{ color: "#a78bfa" }} />
          <span className="text-[11px] font-semibold" style={{ color: "rgba(255,255,255,0.6)" }}>
            Outreach Sequence
          </span>
          <span
            className="text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide"
            style={
              mode === "autopilot"
                ? { background: "rgba(3,218,197,0.12)", color: "#03DAC5" }
                : { background: "rgba(167,139,250,0.12)", color: "#a78bfa" }
            }
          >
            {mode === "autopilot" ? "Auto-pilot" : "Assisted"}
          </span>
        </div>
        {mode === "autopilot" && onPause && (
          <button
            onClick={onPause}
            className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-lg transition-all hover:bg-white/5"
            style={{ color: "rgba(255,255,255,0.35)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <Pause className="h-2.5 w-2.5" />
            Pause
          </button>
        )}
      </div>

      {/* Steps */}
      <div className="px-4 py-3 flex flex-col gap-0">
        {displaySteps.map((step, i) => {
          const Icon = CHANNEL_ICON[step.channel];
          const style = STATUS_STYLE[step.status];
          const isLast = i === displaySteps.length - 1;

          return (
            <div key={i} className="flex gap-3">
              {/* Timeline spine */}
              <div className="flex flex-col items-center">
                <div
                  className="h-6 w-6 rounded-full border flex items-center justify-center shrink-0 z-10"
                  style={{
                    borderColor: step.status === "pending" ? "rgba(255,255,255,0.1)" : style.color,
                    background: step.status === "pending" ? "rgba(255,255,255,0.03)" : style.bg,
                  }}
                >
                  {step.status === "sent" ? (
                    <CheckCircle2 className="h-3 w-3" style={{ color: style.color }} />
                  ) : (
                    <Icon className="h-3 w-3" style={{ color: step.status === "pending" ? "rgba(255,255,255,0.2)" : style.color }} />
                  )}
                </div>
                {!isLast && (
                  <div
                    className="w-px flex-1 my-0.5"
                    style={{
                      background: step.status === "sent"
                        ? "rgba(3,218,197,0.25)"
                        : "rgba(255,255,255,0.07)",
                      minHeight: "16px",
                    }}
                  />
                )}
              </div>

              {/* Step content */}
              <div className={`flex items-center justify-between flex-1 min-w-0 ${isLast ? "pb-0" : "pb-3"}`}>
                <div className="min-w-0">
                  <span
                    className="text-[11px] font-semibold"
                    style={{ color: step.status === "pending" ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.75)" }}
                  >
                    {step.label}
                  </span>
                  <span
                    className="ml-2 text-[10px]"
                    style={{ color: "rgba(255,255,255,0.2)" }}
                  >
                    {step.delay}
                  </span>
                  {step.sentAt && (
                    <span className="ml-2 text-[10px]" style={{ color: "rgba(255,255,255,0.2)" }}>
                      · {step.sentAt}
                    </span>
                  )}
                </div>
                <span
                  className="text-[9px] font-bold px-1.5 py-0.5 rounded-full shrink-0 ml-2"
                  style={{ background: style.bg, color: style.color }}
                >
                  {style.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
