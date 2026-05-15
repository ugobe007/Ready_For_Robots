/**
 * Login page: magic-link + GitHub OAuth
 * Route: /login
 *
 * Magic link flow:
 *  1. User enters email → supabase.auth.signInWithOtp({ email })
 *  2. Supabase emails a magic link
 *  3. Clicking the link redirects to /login (detectSessionInUrl: true handles the hash)
 *  4. onAuthStateChange fires → redirect to /profile
 *
 * OAuth flow (GitHub, Google):
 *  1. User clicks "Sign in with X" → supabase.auth.signInWithOAuth({ provider })
 *  2. Redirect to provider → authorize → redirect to Supabase callback → back to /login with session
 *  3. onAuthStateChange fires → redirect to /profile
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { supabase } from '../lib/supabase';
import { getApiBase } from '../lib/apiBase';

const API = getApiBase();

export default function LoginPage() {
  const router = useRouter();
  const [email,   setEmail]   = useState('');
  const [status,  setStatus]  = useState('idle'); // idle | sending | sent | error | redirect
  const [errMsg,  setErrMsg]  = useState('');

  // If already logged in, or magic link / OAuth just completed, redirect to profile
  useEffect(() => {
    if (!supabase) return;

    // Check for OAuth error in URL hash (Supabase redirects back with errors)
    if (typeof window !== 'undefined' && window.location.hash) {
      const params = new URLSearchParams(window.location.hash.slice(1));
      const err = params.get('error');
      const desc = params.get('error_description');
      if (err) {
        setStatus('error');
        setErrMsg(desc || err);
        // Clear hash so it doesn't persist
        window.history.replaceState(null, '', window.location.pathname);
        return;
      }
    }

    async function redirectAfterLogin(session) {
      if (!session) return;
      const apiBase = API;
      try {
        // Use auth-debug (no DB) for redirect — works even when profile tables aren't ready
        const res = await fetch(`${apiBase}/api/user/auth-debug`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (data?.is_admin) {
            window.location.replace('https://ready-2-robot.fly.dev/admin');
            return;
          }
        } else if (process.env.NODE_ENV === 'development') {
          console.warn('[Login] /api/user/auth-debug returned', res.status, await res.text().catch(() => ''));
        }
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('[Login] /api/user/auth-debug failed:', e?.message || e);
        }
      }
      router.replace('/profile');
    }

    supabase.auth.getSession().then(({ data }) => {
      if (data?.session) redirectAfterLogin(data.session);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) redirectAfterLogin(session);
    });
    return () => listener?.subscription?.unsubscribe();
  }, [router]);

  async function handleOAuthSignIn(provider) {
    if (!supabase) {
      setStatus('error');
      setErrMsg('Auth is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY (or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY).');
      return;
    }
    setErrMsg('');
    setStatus('idle');
    const redirectTo =
      typeof window !== 'undefined'
        ? `${window.location.origin}/login`
        : 'https://readyforrobots.com/login';
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo },
    });
    if (error) {
      setStatus('error');
      setErrMsg(error.message);
    }
    // Success: Supabase redirects to provider, then back with session
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim() || !supabase) return;
    setStatus('sending');
    setErrMsg('');

    const redirectUrl =
      typeof window !== 'undefined'
        ? `${window.location.origin}/login`
        : 'https://readyforrobots.com/login';

    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirectUrl },
    });

    if (error) {
      setStatus('error');
      setErrMsg(error.message);
    } else {
      setStatus('sent');
    }
  }

  return (
    <div className="min-h-screen bg-[#080808] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* logo */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-white tracking-tight">Ready for Robots</h1>
          <p className="text-xs text-neutral-500 mt-1">Lead Intelligence Platform</p>
        </div>

        {status === 'sent' ? (
          /* ── Success state ───────────────────────────────────────────── */
          <div className="border border-emerald-800 rounded-lg px-6 py-8 text-center">
            <div className="text-3xl mb-3">✉</div>
            <h2 className="text-base font-semibold text-neutral-100 mb-2">Check your email</h2>
            <p className="text-sm text-neutral-400 leading-relaxed">
              We sent a magic link to <span className="text-emerald-400">{email}</span>.
              Click the link to sign in — no password needed.
            </p>
            <button
              onClick={() => setStatus('idle')}
              className="mt-5 text-xs text-neutral-600 hover:text-neutral-400 transition-colors">
              ← use a different email
            </button>
          </div>
        ) : (
          /* ── Login form ──────────────────────────────────────────────── */
          <div className="border border-neutral-800 rounded-lg px-6 py-8">
            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Sign in with Google, GitHub, or email</p>
            {/* OAuth buttons */}
            <div className="flex flex-col gap-2 mb-5">
              <button
                type="button"
                onClick={() => handleOAuthSignIn('google')}
                disabled={!supabase}
                className="w-full flex items-center justify-center gap-2 border border-neutral-600 rounded px-4 py-2.5 text-sm text-neutral-200 hover:border-neutral-500 hover:bg-neutral-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" aria-hidden>
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google
              </button>
              <button
                type="button"
                onClick={() => handleOAuthSignIn('github')}
                disabled={!supabase}
                className="w-full flex items-center justify-center gap-2 border border-neutral-600 rounded px-4 py-2.5 text-sm text-neutral-200 hover:border-neutral-500 hover:bg-neutral-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
                Sign in with GitHub
              </button>
            </div>

            <div className="flex items-center gap-3 mb-5">
              <span className="flex-1 h-px bg-neutral-800" />
              <span className="text-[10px] text-neutral-600 uppercase tracking-wider">or</span>
              <span className="flex-1 h-px bg-neutral-800" />
            </div>

            <h2 className="text-sm font-semibold text-neutral-200 mb-1">Sign in with magic link</h2>
            <p className="text-xs text-neutral-600 mb-5">
              Enter your work email — we'll send a one-click login link. No password needed.
            </p>

            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={status === 'sending'}
                className="w-full bg-transparent border border-neutral-700 rounded px-3 py-2 text-sm text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-neutral-500 transition-colors disabled:opacity-50"
              />

              {status === 'error' && (
                <p className="text-xs text-red-400 border border-red-900 rounded px-3 py-2">
                  {errMsg || 'Something went wrong — check your Supabase config.'}
                </p>
              )}

              <button
                type="submit"
                disabled={status === 'sending' || !email.trim()}
                className="w-full border border-emerald-900 text-emerald-400 rounded px-4 py-2 text-sm hover:border-emerald-700 transition-colors disabled:opacity-40">
                {status === 'sending' ? 'Sending…' : 'Send magic link'}
              </button>
            </form>

            <p className="mt-4 text-[10px] text-neutral-700 text-center">
              First time? An account is created automatically when you sign in.
            </p>
          </div>
        )}

        <div className="mt-6 text-center">
          <Link href="/" className="text-xs text-neutral-700 hover:text-neutral-400 transition-colors">
            ← back to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
