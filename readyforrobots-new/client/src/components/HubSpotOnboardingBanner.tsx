/**
 * Post-signup CRM fork: native pipeline vs HubSpot connect.
 */
import { useEffect, useState } from "react";
import { Link } from "wouter";
import { X, LayoutDashboard, Plug } from "lucide-react";

const DISMISS_KEY = "rfr_hubspot_onboarding_dismissed";

type Props = {
  connected?: boolean;
  hasSession: boolean;
};

export default function HubSpotOnboardingBanner({ connected, hasSession }: Props) {
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

  return (
    <div className="relative rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-emerald-50 px-4 py-3 sm:px-5">
      <button
        type="button"
        onClick={dismiss}
        className="absolute right-3 top-3 rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
      <p className="text-[10px] font-bold uppercase tracking-widest text-amber-800">Choose your CRM path</p>
      <p className="mt-1 max-w-2xl text-sm text-gray-700">
        Run deals in our native pipeline or sync scored leads into HubSpot — same SIGNAL intelligence either way.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-2 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-900">
          <LayoutDashboard className="h-3.5 w-3.5" />
          Native CRM — active
        </span>
        <Link
          href="/integrations/hubspot"
          className="inline-flex items-center gap-2 rounded-lg border border-amber-400 bg-white px-3 py-2 text-xs font-bold text-amber-900 transition-colors hover:bg-amber-50"
        >
          <Plug className="h-3.5 w-3.5" />
          Connect HubSpot
        </Link>
        <Link
          href="/compare"
          className="inline-flex items-center gap-1 rounded-lg px-2 py-2 text-xs font-semibold text-gray-500 hover:text-emerald-800"
        >
          Why not a data tool?
        </Link>
      </div>
    </div>
  );
}
