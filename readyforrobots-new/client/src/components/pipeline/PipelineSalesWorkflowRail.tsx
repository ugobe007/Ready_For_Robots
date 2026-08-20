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
  /** After Results preview — curate list first, then outreach. */
  browseFirst?: boolean;
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
  if (props.browseFirst && !props.hasSelection) return "browse";
  if (props.hasSession) return "save";
  return "browse";
}

export default function PipelineSalesWorkflowRail(props: Props) {
  const { hasSession, browseFirst = false, variant = "light" } = props;
  const dark = variant === "dark";
  const current = resolveCurrent(props);

  const steps: { id: Stage; label: string; hint: string; icon: typeof Target }[] = browseFirst
    ? [
        { id: "browse", label: "1. Browse", hint: "Explore the full live pipeline", icon: Target },
        { id: "save", label: "2. Curate", hint: "Save best-fit companies to your list", icon: Zap },
        { id: "draft", label: "3. Draft", hint: "Copy outreach for the company", icon: Mail },
        { id: "send", label: "4. Send", hint: "Send from the detail panel", icon: Mail },
        { id: "track", label: "5. Replies", hint: "Track in Inbox", icon: ArrowRight },
      ]
    : [
        { id: "browse", label: "1. Pick", hint: "Select the highest-fit HOT lead", icon: Target },
        { id: "save", label: "2. Activate CRM", hint: "Save this buyer to start a real pipeline", icon: Zap },
        { id: "draft", label: "3. Draft", hint: "Copy SIGNAL outreach", icon: Mail },
        { id: "send", label: "4. Send", hint: "Send from the detail panel", icon: Mail },
        { id: "track", label: "5. Replies", hint: "Track in Inbox", icon: ArrowRight },
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
          {browseFirst ? "Curate · Outreach" : "Sales pipeline workflow"}
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
      <p className={`mt-2 text-[11px] ${dark ? "text-slate-300" : "text-gray-600"}`}>
        {browseFirst
          ? current === "browse" || current === "save"
            ? "After instructions: Build your 25-lead pipeline, then Save fits and copy outreach."
            : current === "draft"
              ? "Outreach: copy the draft in the detail panel, then send."
              : current === "send"
                ? "Send the message, then return to the list to curate the next account."
                : "Track replies in Inbox and keep curating toward your 25-lead list."
          : hasSession
            ? current === "browse" || current === "save"
              ? "Select a buyer, then activate CRM with the yellow button."
              : current === "draft"
                ? "Copy the outreach draft in the right panel."
                : current === "send"
                  ? "Send the draft, then watch Inbox for replies."
                  : "Check Inbox and advance the opportunity."
            : "Pick a buyer, then start a free workspace to activate CRM."}
      </p>
    </div>
  );
}
