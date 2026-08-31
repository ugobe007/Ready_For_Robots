/**
 * Native CRM vs HubSpot fork — shown for signed-in users on pipeline and CRM.
 */
import { useEffect, useState } from "react";
import { Link } from "wouter";
import { X, LayoutDashboard, Plug, ArrowRight } from "lucide-react";

const DISMISS_KEY = "rfr_crm_fork_dismissed";

type Props = {
  connected?: boolean;
  hasSession: boolean;
  savedCount: number;
  variant?: "banner" | "compact";
};

export default function CrmPathFork({
  connected,
  hasSession,
  savedCount,
  variant = "banner",
}: Props) {
  const [dismissed, setDismissed] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setDismissed(window.localStorage.getItem(DISMISS_KEY) === "1");
  }, []);

  if (!hasSession || connected || dismissed) return null;

  const dismiss = () => {
    window.localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  const isCompact = variant === "compact";
  const preSave = savedCount < 1;

  return (
    <div
      className={
        isCompact
          ? "relative rounded-lg border border-amber-200 bg-amber-50/90 px-3 py-2.5"
          : "relative rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-emerald-50 px-4 py-3 sm:px-5"
      }
    >
      <button
        type="button"
        onClick={dismiss}
        className="absolute right-3 top-3 rounded-md p-1 text-slate-500 hover:bg-emerald-100/80 hover:text-slate-800"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
      <p className="text-[10px] font-bold uppercase tracking-widest text-amber-800">
        {preSave
          ? "Choose your CRM path"
          : savedCount === 1
            ? "Lead saved — pick your CRM path"
            : "Choose your CRM path"}
      </p>
      <p
        className={`mt-1 max-w-2xl text-gray-700 ${isCompact ? "text-xs" : "text-sm"}`}
      >
        {preSave
          ? "Run deals in our native pipeline or connect HubSpot — same SIGNAL-ranked buyers either way. You can switch anytime."
          : "Run deals in our native pipeline or sync scored leads into HubSpot — same buyer intelligence either way."}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          href="/crm"
          className="inline-flex items-center gap-2 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-900 transition-colors hover:bg-emerald-100"
        >
          <LayoutDashboard className="h-3.5 w-3.5" />
          Native CRM
          <ArrowRight className="h-3 w-3 opacity-70" />
        </Link>
        <Link
          href="/integrations/hubspot"
          className="inline-flex items-center gap-2 rounded-lg border border-amber-400 bg-white px-3 py-2 text-xs font-bold text-amber-900 transition-colors hover:bg-amber-50"
        >
          <Plug className="h-3.5 w-3.5" />
          Connect HubSpot
        </Link>
        <Link
          href="/compare"
          className="inline-flex items-center gap-1 rounded-lg px-2 py-2 text-xs font-semibold text-slate-700 hover:text-emerald-900"
        >
          Why not a data tool?
        </Link>
      </div>
    </div>
  );
}
