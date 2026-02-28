/**
 * Magic-link login page
 * Route: /login
 *
 * Flow:
 *  1. User enters email → supabase.auth.signInWithOtp({ email })
 *  2. Supabase emails a magic link
 *  3. Clicking the link redirects to /login (detectSessionInUrl: true handles the hash)
 *  4. onAuthStateChange fires → redirect to /profile
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { supabase } from '../lib/supabase';

export default function LoginPage() {
  const router = useRouter();
  const [email,   setEmail]   = useState('');
  const [status,  setStatus]  = useState('idle'); // idle | sending | sent | error | redirect
  const [errMsg,  setErrMsg]  = useState('');

  // If already logged in, or magic link just clicked, redirect to profile
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data?.session) router.replace('/profile');
    });

    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) router.replace('/profile');
    });
    return () => listener?.subscription?.unsubscribe();
  }, [router]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus('sending');
    setErrMsg('');

    const redirectUrl =
      typeof window !== 'undefined'
        ? `${window.location.origin}/login`
        : 'https://ready-2-robot.fly.dev/login';

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
          <p className="text-xs text-neutral-500 mt-1">Richtech Robotics · Lead Intelligence</p>
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
