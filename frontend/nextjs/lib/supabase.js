import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL      = process.env.NEXT_PUBLIC_SUPABASE_URL      || '';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const SUPABASE_CONFIGURED = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

if (!SUPABASE_CONFIGURED && typeof window !== 'undefined') {
  console.warn(
    '[Supabase] NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY is not set. ' +
    'Auth features will be disabled.'
  );
}

// Stub used when credentials are absent — prevents createClient crash
const _stubClient = {
  auth: {
    getSession:    () => Promise.resolve({ data: { session: null }, error: null }),
    onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
    signInWithOtp: () => Promise.resolve({ error: { message: 'Auth not configured' } }),
    signOut:       () => Promise.resolve({}),
  },
};

// Singleton client — safe to import anywhere
export const supabase = SUPABASE_CONFIGURED
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession:     true,
        autoRefreshToken:   true,
        detectSessionInUrl: true,
        flowType:           'implicit',
      },
    })
  : _stubClient;

/**
 * Returns the current session's access_token for backend API calls.
 * Usage:  fetch('/api/user/me', { headers: authHeader(token) })
 */
export function authHeader(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Convenience: get the current session (null if not logged in).
 */
export async function getSession() {
  const { data } = await supabase.auth.getSession();
  return data?.session ?? null;
}
