/**
 * Signed-in workspace nav — pipeline-first landing with CRM path visible.
 */
import { Link } from "wouter";
import { ArrowRight, LayoutDashboard, Plug, Zap } from "lucide-react";

type Props = {
  savedCount: number;
  hubspotConnected?: boolean;
  queuedActions?: number;
};

export default function WorkspaceQuickLinks({ savedCount, hubspotConnected, queuedActions = 0 }: Props) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">Your sales workspace</p>
        <p className="mt-0.5 text-xs text-gray-600">
          {savedCount === 0
            ? "Save a lead below, then run outreach in native CRM or HubSpot."
            : `${savedCount} saved lead${savedCount === 1 ? "" : "s"} · pick native CRM or HubSpot sync anytime.`}
        </p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Link
          href="/crm"
          className="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-[11px] font-semibold text-gray-800 hover:bg-gray-100"
        >
          <LayoutDashboard className="h-3 w-3" />
          CRM
        </Link>
        <Link
          href="/integrations/hubspot"
          className="inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-[11px] font-semibold text-amber-950 hover:bg-amber-100"
        >
          <Plug className="h-3 w-3" />
          {hubspotConnected ? "HubSpot ✓" : "HubSpot"}
        </Link>
        <Link
          href="/sales-workflow"
          className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 bg-emerald-50 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-900 hover:bg-emerald-100"
        >
          <Zap className="h-3 w-3" />
          Next actions
          {queuedActions > 0 ? ` (${queuedActions})` : ""}
        </Link>
        {savedCount === 0 && (
          <span className="inline-flex items-center gap-1 px-1 text-[11px] font-medium text-amber-800">
            Save first lead
            <ArrowRight className="h-3 w-3" />
          </span>
        )}
      </div>
    </div>
  );
}
