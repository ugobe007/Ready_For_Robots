import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import ExperimentHeader from "@/components/ExperimentHeader";
import { supabase } from "@/lib/supabase";
import {
  clearSupabaseOAuthParams,
  readSupabaseOAuthError,
  finishSupabaseOAuthCallback,
} from "@/lib/authCallback";
import {
  clearPendingNext,
  readNextParam,
  peekPendingNext,
  postAuthRedirectTarget,
  navigateAfterAuth,
} from "@/lib/authNext";
import { markJobsWorkspaceRestoreIfHome } from "@/lib/jobsWorkflow";
import { markFreshSignup } from "@/lib/firstSaveGuide";
import { trackSignupComplete } from "@/lib/siteAnalytics";

export default function AuthCallback() {
  const [, setLocation] = useLocation();
  const [message, setMessage] = useState("Completing sign-in…");

  useEffect(() => {
    if (!supabase) {
      setMessage("Auth is not configured on this site.");
      return;
    }
    const client = supabase;
    const pathname = window.location.pathname;
    const search = window.location.search;
    const explicitNext = readNextParam(search) ?? peekPendingNext();
    const next = explicitNext ?? postAuthRedirectTarget("/");
    if (explicitNext) markJobsWorkspaceRestoreIfHome(explicitNext);

    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      markFreshSignup();
      // Funnel #20: account created (fires once per browser). OAuth + magic link
      // both land here, so this is the single completion point.
      trackSignupComplete({ next });
      window.history.replaceState(
        null,
        "",
        clearSupabaseOAuthParams(
          "/auth/callback",
          `?next=${encodeURIComponent(next)}`
        )
      );
      navigateAfterAuth(next);
    };

    void (async () => {
      const oauthErr = readSupabaseOAuthError();
      if (oauthErr) {
        // If a session already exists, suppress transient OAuth error params and continue.
        const { data } = await client.auth.getSession();
        if (data?.session) {
          finish();
          return;
        }
        const detail = oauthErr.includes("Unable to exchange external code")
          ? `${oauthErr}\n\nGoogle Cloud has the right Client ID, but Supabase cannot exchange the code — the Client secret saved in Supabase → Authentication → Providers → Google does not match Google Cloud.\n\nFix: Google Cloud → Credentials → your Web client → Reset secret → copy the new GOCSPX-… secret → paste into Supabase Google provider → Save. Also add http://localhost:3000/** to Supabase URL Configuration if testing locally.`
          : oauthErr;
        setLocation(
          `/login?next=${encodeURIComponent(next)}&auth_error=${encodeURIComponent(detail)}`
        );
        return;
      }

      const { error } = await finishSupabaseOAuthCallback(
        client,
        pathname,
        search
      );
      if (error) {
        // Double callbacks can throw exchange errors after session is already established.
        const { data } = await client.auth.getSession();
        if (!data?.session) {
          setLocation(
            `/login?next=${encodeURIComponent(next)}&auth_error=${encodeURIComponent(error)}`
          );
          return;
        }
      }
      const { data } = await client.auth.getSession();
      if (data.session) finish();
    })();

    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) finish();
    });

    const timer = window.setTimeout(() => {
      if (!done) {
        setMessage(
          "Sign-in is taking longer than expected. Try again or use a magic link."
        );
      }
    }, 12_000);

    return () => {
      window.clearTimeout(timer);
      sub.subscription.unsubscribe();
    };
  }, [setLocation]);

  return (
    <div className="min-h-screen bg-[#081126] text-slate-100">
      <ExperimentHeader />
      <main className="mx-auto max-w-md px-6 pt-32 text-center">
        <p className="text-base text-slate-300">{message}</p>
        <Link
          href="/login"
          className="mt-6 inline-block text-base font-semibold text-emerald-400"
        >
          Back to sign in
        </Link>
      </main>
    </div>
  );
}
