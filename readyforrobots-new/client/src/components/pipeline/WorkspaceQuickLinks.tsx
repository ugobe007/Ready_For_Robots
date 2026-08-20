/**
 * Signed-in workspace nav — pipeline-first; CRM is advanced, not the primary path.
 */
import { Link } from "wouter";
import { ArrowRight, Inbox, Zap } from "lucide-react";

type Props = {
  savedCount: number;
  hubspotConnected?: boolean;
  queuedActions?: number;
  variant?: "light" | "dark";
};

export default function WorkspaceQuickLinks({
  savedCount,
  hubspotConnected,
  queuedActions = 0,
  variant = "light",
}: Props) {
  const dark = variant === "dark";

  return (
    <div
      className={
        dark
          ? "flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0f1628] px-4 py-3 shadow-lg sm:flex-row sm:items-center sm:justify-between"
          : "flex flex-col gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between"
      }
    >
      <div>
        <p
          className={`text-[10px] font-bold uppercase tracking-widest ${
            dark ? "text-emerald-300" : "text-emerald-800"
          }`}
        >
          Everything happens on this page
        </p>
        <p className={`mt-0.5 text-xs ${dark ? "text-slate-300" : "text-gray-600"}`}>
          Pick a buyer → Activate CRM by saving → copy the draft and send from the right panel.{" "}
          {savedCount > 0
            ? `${savedCount} saved in your CRM.`
            : "Save your first buyer to activate CRM."}
        </p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Link
          href="/sales-workflow"
          className={
            dark
              ? "inline-flex items-center gap-1 rounded-lg border border-emerald-400/40 bg-emerald-500/15 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-100 hover:bg-emerald-500/25"
              : "inline-flex items-center gap-1 rounded-lg border border-emerald-300 bg-emerald-50 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-900 hover:bg-emerald-100"
          }
        >
          <Zap className="h-3 w-3" />
          Activity
          {queuedActions > 0 ? ` (${queuedActions})` : ""}
        </Link>
        <Link
          href="/inbox"
          className={
            dark
              ? "inline-flex items-center gap-1 rounded-lg border border-white/15 bg-white/5 px-2.5 py-1.5 text-[11px] font-semibold text-slate-100 hover:bg-white/10"
              : "inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-[11px] font-semibold text-gray-800 hover:bg-gray-100"
          }
        >
          <Inbox className="h-3 w-3" />
          Replies
        </Link>
        <Link
          href="/integrations/hubspot"
          className={
            dark
              ? "inline-flex items-center gap-1 rounded-lg border border-amber-400/40 bg-amber-500/15 px-2.5 py-1.5 text-[11px] font-semibold text-amber-100 hover:bg-amber-500/25"
              : "inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-[11px] font-semibold text-amber-950 hover:bg-amber-100"
          }
        >
          {hubspotConnected ? "HubSpot ✓" : "HubSpot sync"}
        </Link>
        {savedCount === 0 && (
          <span
            className={`inline-flex items-center gap-1 px-1 text-[11px] font-medium ${
              dark ? "text-amber-200" : "text-amber-800"
            }`}
          >
            Save a lead below
            <ArrowRight className="h-3 w-3" />
          </span>
        )}
      </div>
    </div>
  );
}
