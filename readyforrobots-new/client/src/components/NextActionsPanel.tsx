/**
 * NextActionsPanel — top 3 autonomous pipeline actions (UX north star: Advance, not browse).
 * Dark editorial styling for home hero + pipeline surfaces.
 */
import { ArrowRight, ChevronRight, Zap } from "lucide-react";
import { Link, useLocation } from "wouter";
import type { NextAction } from "@/types/readyForRobots";

type Props = {
  actions: NextAction[];
  loading?: boolean;
  compact?: boolean;
  onSelect?: (action: NextAction) => void;
  className?: string;
};

const priorityStyles: Record<
  NextAction["priority"],
  { dot: string; border: string; bg: string; text: string }
> = {
  high: {
    dot: "#f87171",
    border: "rgba(248,113,113,0.28)",
    bg: "rgba(248,113,113,0.08)",
    text: "#fecaca",
  },
  medium: {
    dot: "#a78bfa",
    border: "rgba(167,139,250,0.28)",
    bg: "rgba(167,139,250,0.08)",
    text: "#ddd6fe",
  },
  low: {
    dot: "rgba(255,255,255,0.35)",
    border: "rgba(255,255,255,0.1)",
    bg: "rgba(255,255,255,0.03)",
    text: "rgba(255,255,255,0.55)",
  },
};

export default function NextActionsPanel({
  actions,
  loading = false,
  compact = false,
  onSelect,
  className = "",
}: Props) {
  const [, navigate] = useLocation();
  const sorted = [...actions].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.priority] - order[b.priority];
  });
  const visible = sorted.slice(0, 3);

  const handleClick = (action: NextAction) => {
    if (onSelect) {
      onSelect(action);
      return;
    }
    if (action.route) {
      const path =
        action.entity_type === "company" && action.entity_id
          ? `${action.route}?lead=${action.entity_id}`
          : action.route;
      navigate(path);
    }
  };

  return (
    <aside
      className={`rounded-2xl border border-white/10 ${compact ? "p-4" : "p-5"} ${className}`}
      style={{ background: "rgba(255,255,255,0.035)" }}
      aria-labelledby="next-actions-heading"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="mb-2 inline-flex items-center gap-2">
            <span
              className="h-1.5 w-1.5 rounded-full animate-pulse"
              style={{ background: "#03DAC5" }}
            />
            <p
              id="next-actions-heading"
              className="text-[10px] font-bold uppercase tracking-[0.2em]"
              style={{ color: "#03DAC5" }}
            >
              Next actions
            </p>
          </div>
          <p className="text-sm font-bold text-white">
            What SIGNAL recommends now
          </p>
          {!compact && (
            <p className="mt-1 text-[11px] leading-relaxed text-white/40">
              Top autonomous moves ranked by buyer intent and timing.
            </p>
          )}
        </div>
        <Zap className="h-4 w-4 shrink-0 text-violet-300/80" />
      </div>

      {loading ? (
        <p className="text-xs text-white/35">Loading ranked actions…</p>
      ) : visible.length === 0 ? (
        <p className="text-xs leading-relaxed text-white/35">
          Pipeline actions appear when SIGNAL surfaces ranked leads.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {visible.map((action, index) => {
            const style = priorityStyles[action.priority];
            return (
              <button
                key={action.id}
                type="button"
                onClick={() => handleClick(action)}
                className="group w-full rounded-xl border px-3 py-3 text-left transition-all hover:-translate-y-0.5"
                style={{ borderColor: style.border, background: style.bg }}
              >
                <div className="flex items-start gap-3">
                  <div className="flex flex-col items-center gap-1 pt-0.5">
                    <span
                      className="font-mono text-[10px] text-white/30"
                      style={{ fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: style.dot }}
                    />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[12px] font-semibold leading-snug text-white/90">
                      {action.label}
                    </p>
                    {(action.meta?.humanoid_pilot_tier === "ACTIVE_PILOT" ||
                      action.meta?.humanoid_pilot_tier === "PILOT_INTENT") && (
                      <span
                        className="mt-1 inline-flex rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide"
                        style={{
                          color: "#03DAC5",
                          background: "rgba(3,218,197,0.12)",
                          border: "1px solid rgba(3,218,197,0.22)",
                        }}
                      >
                        {String(
                          action.meta?.humanoid_pilot_label || "Humanoid pilot"
                        )}
                      </span>
                    )}
                    <p
                      className="mt-0.5 truncate text-[11px]"
                      style={{ color: style.text }}
                    >
                      {action.companyName}
                    </p>
                  </div>
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-white/20 transition-colors group-hover:text-white/55" />
                </div>
              </button>
            );
          })}
        </div>
      )}

      <Link
        href="/pipeline"
        className="mt-4 inline-flex w-full items-center justify-between rounded-xl border border-white/10 px-3 py-2.5 text-[11px] font-bold text-white/45 transition-colors hover:border-violet-400/35 hover:text-white/75"
      >
        Open full pipeline
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </aside>
  );
}
