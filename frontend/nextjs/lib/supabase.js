import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL      = process.env.NEXT_PUBLIC_SUPABASE_URL      || '';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // Warn in development only — in production the build args ensure these exist
  if (typeof window !== 'undefined') {
    console.warn(
      '[Supabase] NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY is not set.\n' +
      'Auth features will be disabled. See README for setup instructions.'
    );
  }
}

// Singleton client — safe to import anywhere
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession:    true,
    autoRefreshToken:  true,
    detectSessionInUrl: true,   // picks up magic-link hash on redirect
  },
});

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
