import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import Header from "@/components/Header";
import { supabase } from "@/lib/supabase";
import { clearSupabaseOAuthParams, readSupabaseOAuthError } from "@/lib/authCallback";

function safeNext(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/pipeline";
}

export default function AuthCallback() {
  const [, setLocation] = useLocation();
  const [message, setMessage] = useState("Completing sign-in…");

  useEffect(() => {
    if (!supabase) {
      setMessage("Auth is not configured on this site.");
      return;
    }
    const client = supabase;
    const params = new URLSearchParams(window.location.search);
    const next = safeNext(params.get("next"));

    const oauthErr = readSupabaseOAuthError();
    if (oauthErr) {
      const detail = oauthErr.includes("Unable to exchange external code")
        ? `${oauthErr} — Re-save the Google Client secret in Supabase → Authentication → Providers → Google (no spaces). Or use magic link below.`
        : oauthErr;
      setLocation(`/login?next=${encodeURIComponent(next)}&auth_error=${encodeURIComponent(detail)}`);
      return;
    }

    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      window.history.replaceState(null, "", clearSupabaseOAuthParams("/auth/callback", `?next=${encodeURIComponent(next)}`));
      setLocation(next);
    };

    void client.auth.getSession().then(({ data }) => {
      if (data.session) finish();
    });

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
