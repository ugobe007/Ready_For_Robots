/**
 * HubSpot connect onboarding — Profile, CRM, and workspace surfaces.
 * Honest tier gate: OAuth connect is free; auto-sync all leads is Pro+.
 */
import { Link } from "wouter";
import { Check, LayoutDashboard, Plug } from "lucide-react";

export type HubSpotIntegrationStatus = {
  connected?: boolean;
  entitled?: boolean;
  entitlement_message?: string | null;
  account_login?: string | null;
  account_name?: string | null;
};

type Props = {
  status: HubSpotIntegrationStatus | null;
  loading?: boolean;
  variant?: "profile" | "compact";
};

export default function HubSpotConnectPanel({ status, loading, variant = "profile" }: Props) {
  const connected = Boolean(status?.connected);
  const accountLabel = status?.account_login || status?.account_name;
  const tierNote =
    status?.entitlement_message ||
    "Connect free on any workspace. Auto-sync all saved leads requires Pro or Premium.";

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4 text-xs text-gray-500">
        Loading HubSpot status…
      </div>
    );
  }

  const isCompact = variant === "compact";

  return (
    <div
      className={
        isCompact
          ? "rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2.5"
          : "rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-emerald-50 p-4"
      }
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-widest text-amber-900">
            HubSpot sync
          </p>
          {connected ? (
            <>
              <p className="mt-1 inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-800">
                <Check className="h-4 w-4 shrink-0" />
                Connected{accountLabel ? ` · ${accountLabel}` : ""}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-gray-600">
                Saved leads sync into HubSpot. Manage auto-sync vs hand-picked accounts on the integration page.
              </p>
            </>
          ) : (
            <>
              <p className={`mt-1 text-gray-800 ${isCompact ? "text-xs" : "text-sm"}`}>
                Already on HubSpot? Connect in one click — SIGNAL pushes scored buyer leads while your team closes in
                familiar CRM.
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-gray-600">{tierNote}</p>
            </>
          )}
        </div>
        {!isCompact && connected && (
          <span className="shrink-0 rounded-full border border-emerald-300 bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-900">
            Active
          </span>
        )}
      </div>

      <div className={`flex flex-wrap gap-2 ${isCompact ? "mt-2" : "mt-3"}`}>
        <Link
          href="/integrations/hubspot"
          className={
            connected
              ? "inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-800 hover:bg-gray-50"
              : "inline-flex items-center gap-1.5 rounded-lg border border-amber-400 bg-amber-500 px-3 py-2 text-xs font-bold text-gray-900 hover:bg-amber-400"
          }
        >
          <Plug className="h-3.5 w-3.5" />
          {connected ? "Manage HubSpot sync" : "Connect HubSpot"}
        </Link>
        <Link
          href="/crm"
          className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-100"
        >
          <LayoutDashboard className="h-3.5 w-3.5" />
          Native CRM
        </Link>
        {!connected && !isCompact && (
          <Link href="/pricing?reason=hubspot" className="inline-flex items-center px-2 py-2 text-xs font-semibold text-gray-500 hover:text-emerald-800">
            Pro auto-sync →
          </Link>
        )}
      </div>
    </div>
  );
}
