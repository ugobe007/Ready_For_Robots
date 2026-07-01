import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import { supabase } from "@/lib/supabase";
import { clearSupabaseOAuthParams, readSupabaseOAuthError, finishSupabaseOAuthCallback } from "@/lib/authCallback";
import { clearPendingNext, readNextParam, peekPendingNext, postAuthRedirectTarget, navigateAfterAuth } from "@/lib/authNext";
import { markFreshSignup } from "@/lib/firstSaveGuide";

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
    const next = readNextParam(search) ?? peekPendingNext() ?? postAuthRedirectTarget("/pipeline");

    const oauthErr = readSupabaseOAuthError();
    if (oauthErr) {
      const detail = oauthErr.includes("Unable to exchange external code")
        ? `${oauthErr}\n\nGoogle Cloud has the right Client ID, but Supabase cannot exchange the code — the Client secret saved in Supabase → Authentication → Providers → Google does not match Google Cloud.\n\nFix: Google Cloud → Credentials → your Web client → Reset secret → copy the new GOCSPX-… secret → paste into Supabase Google provider → Save. Also add http://localhost:3000/** to Supabase URL Configuration if testing locally.`
        : oauthErr;
      setLocation(`/login?next=${encodeURIComponent(next)}&auth_error=${encodeURIComponent(detail)}`);
      return;
    }

    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      markFreshSignup();
      window.history.replaceState(null, "", clearSupabaseOAuthParams("/auth/callback", `?next=${encodeURIComponent(next)}`));
      navigateAfterAuth(next);
    };

    void (async () => {
      const { error } = await finishSupabaseOAuthCallback(client, pathname, search);
      if (error) {
        setLocation(`/login?next=${encodeURIComponent(next)}&auth_error=${encodeURIComponent(error)}`);
        return;
      }
      const { data } = await client.auth.getSession();
      if (data.session) finish();
    })();

    const { data: sub } = client.auth.onAuthStateChange((_event, session) => {
      if (session) finish();
    });

    const timer = window.setTimeout(() => {
      if (!done) {
        setMessage("Sign-in is taking longer than expected. Try again or use a magic link.");
      }
    }, 12_000);

    return () => {
      window.clearTimeout(timer);
      sub.subscription.unsubscribe();
    };
  }, [setLocation]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="mx-auto max-w-md px-6 pt-32 text-center">
        <p className="text-sm text-gray-600">{message}</p>
        <Link href="/login" className="mt-6 inline-block text-sm font-semibold text-emerald-700">
          Back to sign in
        </Link>
      </main>
    </div>
  );
}
