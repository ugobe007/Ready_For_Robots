/**
 * LoginModal — inline sign-in modal
 * Uses the same magic-link flow as /login but without navigating away.
 */
import { useState } from 'react';
import { supabase } from '../lib/supabase';

export default function LoginModal({ onClose }) {
  const [email,  setEmail]  = useState('');
  const [status, setStatus] = useState('idle'); // idle | sending | sent | error
  const [errMsg, setErrMsg] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus('sending');

    const redirectUrl =
      typeof window !== 'undefined'
        ? `${window.location.origin}/login?next=${encodeURIComponent(window.location.pathname)}`
        : 'https://ready-2-robot.fly.dev/login';

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { emailRedirectTo: redirectUrl },
      });
      if (error) { setStatus('error'); setErrMsg(error.message); }
      else setStatus('sent');
    } catch (err) {
      setStatus('error');
      setErrMsg(err?.message || 'Unexpected error — check your connection.');
    }
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 9998,
               display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}
      onClick={onClose}>
      <div
        style={{ background: '#0a0a0a', border: '1px solid #262626', borderRadius: '12px',
                 padding: '1.75rem', width: '100%', maxWidth: '22rem', position: 'relative' }}
        onClick={e => e.stopPropagation()}>

        {/* close */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '0.875rem', right: '0.875rem',
                   background: 'none', border: 'none', color: '#525252', cursor: 'pointer', fontSize: '16px' }}>
          ✕
        </button>

        {status === 'sent' ? (
          /* ── success ── */
          <div style={{ textAlign: 'center', padding: '0.75rem 0' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>✉</div>
            <p style={{ color: '#e5e5e5', fontWeight: 600, fontSize: '14px', marginBottom: '0.5rem' }}>
              Check your email
            </p>
            <p style={{ color: '#737373', fontSize: '12px', lineHeight: 1.6 }}>
              Magic link sent to{' '}
              <span style={{ color: '#34d399' }}>{email}</span>.{' '}
              Click it to sign in — no password needed.
            </p>
            <button
              onClick={() => setStatus('idle')}
              style={{ marginTop: '1.25rem', background: 'none', border: 'none',
                       color: '#525252', fontSize: '11px', cursor: 'pointer' }}>
              ← use a different email
            </button>
          </div>
        ) : (
          /* ── form ── */
          <>
            <h2 style={{ color: '#e5e5e5', fontSize: '14px', fontWeight: 600, marginBottom: '0.25rem' }}>
              Sign in to Ready for Robots
            </h2>
            <p style={{ color: '#525252', fontSize: '12px', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              Enter your work email — we'll send a one-click magic link.
              No password needed.
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={status === 'sending'}
                style={{ background: 'transparent', border: '1px solid #404040', borderRadius: '6px',
                         padding: '0.5rem 0.75rem', color: '#e5e5e5', fontSize: '13px',
                         outline: 'none', width: '100%', boxSizing: 'border-box',
                         opacity: status === 'sending' ? 0.5 : 1 }}
              />

              {status === 'error' && (
                <p style={{ color: '#f87171', fontSize: '11px', border: '1px solid #7f1d1d',
                            borderRadius: '4px', padding: '0.375rem 0.625rem' }}>
                  {errMsg}
                </p>
              )}

              <button
                type="submit"
                disabled={status === 'sending' || !email.trim()}
                style={{ background: 'transparent', border: '1px solid #065f46', color: '#34d399',
                         borderRadius: '6px', padding: '0.5rem', fontSize: '13px', cursor: 'pointer',
                         fontWeight: 500, opacity: (status === 'sending' || !email.trim()) ? 0.4 : 1,
                         transition: 'border-color 0.15s, opacity 0.15s' }}>
                {status === 'sending' ? 'Sending…' : 'Send magic link'}
              </button>
            </form>

            <p style={{ marginTop: '0.875rem', fontSize: '10px', color: '#404040', textAlign: 'center' }}>
              First time? An account is created automatically.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
