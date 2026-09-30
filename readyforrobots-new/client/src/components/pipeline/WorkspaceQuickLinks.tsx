/**
 * Signed-in workspace shortcuts — not a second CRM how-to.
 * CRM activate / saved jobs live in PipelineCrmMotion + the job workspace.
 */
import { Link } from "wouter";
import { Inbox, Zap } from "lucide-react";

type Props = {
  hubspotConnected?: boolean;
  queuedActions?: number;
  variant?: "light" | "dark";
};

export default function WorkspaceQuickLinks({
  hubspotConnected,
  queuedActions = 0,
  variant = "light",
}: Props) {
  const dark = variant === "dark";

  return (
    <div
      className={
        dark
          ? "flex flex-wrap items-center justify-end gap-1.5 rounded-xl border border-white/10 bg-[#0f1628] px-3 py-2"
          : "flex flex-wrap items-center justify-end gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2"
      }
    >
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
    </div>
  );
}
