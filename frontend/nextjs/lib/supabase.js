import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
// Dashboard may label this "anon" (JWT) or "publishable" (sb_publishable_…); either works in the browser.
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const supabase =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      })
    : null;

if (!supabase && typeof window !== 'undefined') {
  console.warn(
    '[Supabase] Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY ' +
      '(or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY). Auth disabled until then.'
  );
}

/**
 * Returns the current session's access_token for backend API calls.
 * Usage:  fetch('/api/user/me', { headers: authHeader(token) })
 */
export function authHeader(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Convenience: get the current session (null if not logged in or not configured).
 */
export async function getSession() {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data?.session ?? null;
}
