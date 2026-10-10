/**
 * Post-first-save activation checklist.
 *
 * After a user saves their first lead, guide them through the remaining activation
 * steps: copy the outreach draft, then pick native CRM or HubSpot. Closing the
 * checklist stores a per-browser flag so it does not nag forever.
 */
import { useEffect, useState } from "react";
import { Link } from "wouter";
import { CheckCircle2, Circle, Copy, ExternalLink, X } from "lucide-react";

const DISMISS_KEY = "rfr_activation_checklist_done";

type Props = {
  company?: string | null;
  draftCopied?: boolean;
  onCopyDraft?: () => void;
  hasDraft?: boolean;
};

export function isActivationChecklistDismissed(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

export function dismissActivationChecklist(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DISMISS_KEY, "1");
  } catch {
    /* private mode */
  }
}

export default function ActivationChecklist({
  company,
  draftCopied = false,
  onCopyDraft,
  hasDraft = true,
}: Props) {
  const [open, setOpen] = useState(false);
  const name = (company || "this buyer").trim() || "this buyer";

  useEffect(() => {
    if (!isActivationChecklistDismissed()) setOpen(true);
  }, []);

  if (!open) return null;

  const steps = [
    { id: "saved", label: `Saved ${name}`, done: true },
    {
      id: "draft",
      label: draftCopied ? "Outreach draft copied" : "Copy the outreach draft",
      done: draftCopied,
      action: hasDraft && !draftCopied && onCopyDraft ? onCopyDraft : undefined,
      actionLabel: "Copy draft",
    },
    {
      id: "crm",
      label: "Open CRM or connect HubSpot",
      done: false,
    },
  ];

  const finish = () => {
    dismissActivationChecklist();
    setOpen(false);
  };

  return (
    <div className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-emerald-800">
            You&apos;re activated — finish setup
          </p>
          <p className="mt-0.5 text-xs text-emerald-900/80">
            Three steps turn a saved lead into pipeline motion.
          </p>
        </div>
        <button
          type="button"
          onClick={finish}
          className="rounded-lg p-1 text-emerald-700/70 hover:bg-emerald-100 hover:text-emerald-900"
          aria-label="Dismiss checklist"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <ol className="mt-3 space-y-2">
        {steps.map((step, i) => (
          <li
            key={step.id}
            className="flex items-center gap-2 text-xs text-emerald-950"
          >
            {step.done ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            ) : (
              <Circle className="h-4 w-4 shrink-0 text-emerald-400" />
            )}
            <span
              className={
                step.done ? "font-medium text-emerald-800" : "font-semibold"
              }
            >
              {i + 1}. {step.label}
            </span>
            {step.action && (
              <button
                type="button"
                onClick={step.action}
                className="ml-auto inline-flex items-center gap-1 rounded-lg border border-emerald-600 bg-white px-2 py-1 text-[10px] font-bold text-emerald-800 hover:bg-emerald-100"
              >
                <Copy className="h-3 w-3" />
                {step.actionLabel}
              </button>
            )}
          </li>
        ))}
      </ol>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          href="/crm"
          onClick={finish}
          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-[11px] font-bold text-white hover:bg-emerald-700"
        >
          Open native CRM
          <ExternalLink className="h-3 w-3" />
        </Link>
        <Link
          href="/integrations/hubspot"
          onClick={finish}
          className="inline-flex items-center gap-1 rounded-lg border border-emerald-600 bg-white px-3 py-1.5 text-[11px] font-bold text-emerald-800 hover:bg-emerald-100"
        >
          Connect HubSpot
        </Link>
      </div>
    </div>
  );
}
