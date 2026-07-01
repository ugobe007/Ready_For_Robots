/**
 * Detect → Qualify → Engage → Advance — one rail on /pipeline so users aren't lost in CRM/Cal/admin.
 */
import { Link } from "wouter";
import { ArrowRight, CheckCircle2, Circle, Mail, Target, Zap } from "lucide-react";

type Stage = "browse" | "save" | "draft" | "send" | "track";

type Props = {
  hasSession: boolean;
  hasSavedLeads: boolean;
  hasSelection: boolean;
  hasDraft: boolean;
  hasContact: boolean;
  sent: boolean;
  variant?: "dark" | "light";
};

function stepState(current: Stage, step: Stage): "done" | "active" | "upcoming" {
  const order: Stage[] = ["browse", "save", "draft", "send", "track"];
  const ci = order.indexOf(current);
  const si = order.indexOf(step);
  if (si < ci) return "done";
  if (si === ci) return "active";
  return "upcoming";
}

function resolveCurrent(props: Props): Stage {
  if (props.sent) return "track";
  if (props.hasDraft && props.hasContact) return "send";
  if (props.hasDraft || (props.hasSelection && props.hasSavedLeads)) return "draft";
  if (props.hasSession && props.hasSavedLeads) return "save";
  if (props.hasSession) return "save";
  return "browse";
}

export default function PipelineSalesWorkflowRail(props: Props) {
  const { hasSession, variant = "light" } = props;
  const dark = variant === "dark";
  const current = resolveCurrent(props);

  const steps: { id: Stage; label: string; hint: string; icon: typeof Target }[] = [
    { id: "browse", label: "Pick lead", hint: "Select a HOT/WARM row", icon: Target },
    { id: "save", label: "Save", hint: "Add to your workspace", icon: Zap },
    { id: "draft", label: "Draft", hint: "Develop with SIGNAL", icon: Mail },
    { id: "send", label: "Send", hint: "One click from the panel", icon: Mail },
    { id: "track", label: "Replies", hint: "Inbox & activity feed", icon: ArrowRight },
  ];

  return (
    <div
      className={
        dark
          ? "rounded-xl border border-white/10 bg-[#0f1628]/90 px-3 py-2.5"
          : "rounded-xl border border-gray-200 bg-white px-3 py-2.5 shadow-sm"
      }
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className={`text-[10px] font-bold uppercase tracking-[0.18em] ${dark ? "text-emerald-300" : "text-emerald-800"}`}>
          Sales pipeline workflow
        </p>
        {hasSession && (
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            <Link
              href="/inbox"
              className={`rounded-md px-2 py-0.5 font-semibold ${dark ? "text-slate-300 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}
            >
              Inbox
            </Link>
            <Link
              href="/sales-workflow"
              className={`rounded-md px-2 py-0.5 font-semibold ${dark ? "text-slate-300 hover:text-white" : "text-gray-600 hover:text-gray-900"}`}
            >
              Activity feed
            </Link>
          </div>
        )}
      </div>
      <ol className="flex flex-wrap items-center gap-1 sm:gap-2">
        {steps.map((step, idx) => {
          const state = stepState(current, step.id);
          const Icon = step.icon;
          const done = state === "done";
          const active = state === "active";
          return (
            <li key={step.id} className="flex items-center gap-1 sm:gap-2">
              <div
                className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 ${
                  active
                    ? dark
                      ? "border-emerald-400/60 bg-emerald-500/15 text-emerald-100"
                      : "border-emerald-400 bg-emerald-50 text-emerald-900"
                    : done
                      ? dark
                        ? "border-white/10 bg-white/5 text-slate-300"
                        : "border-gray-200 bg-gray-50 text-gray-700"
                      : dark
                        ? "border-white/5 text-slate-500"
                        : "border-transparent text-gray-400"
                }`}
                title={step.hint}
              >
                {done ? (
                  <CheckCircle2 className={`h-3 w-3 shrink-0 ${dark ? "text-emerald-400" : "text-emerald-600"}`} />
                ) : (
                  <Icon className="h-3 w-3 shrink-0 opacity-70" />
                )}
                <span className="text-[10px] font-bold whitespace-nowrap">{step.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <Circle className={`hidden h-1 w-1 shrink-0 fill-current sm:block ${dark ? "text-slate-600" : "text-gray-300"}`} />
              )}
            </li>
          );
        })}
      </ol>
      {!hasSession && (
        <p className={`mt-2 text-[11px] ${dark ? "text-slate-400" : "text-gray-500"}`}>
          Sign in to save leads, draft outreach, and send from this page — no separate CRM required.
        </p>
      )}
    </div>
  );
}
