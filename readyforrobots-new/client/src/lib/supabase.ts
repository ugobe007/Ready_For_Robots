import { createClient, type Session } from "@supabase/supabase-js";

const url = import.meta.env.VITE_PUBLIC_SUPABASE_URL || "";
const anon =
  import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  "";

export const AUTH_UNAVAILABLE_MSG =
  "Sign-in is not configured in this build, so Google, GitHub, and email links cannot run. Refresh, or email support@readyforrobots.com.";

export const supabase =
  url && anon
    ? createClient(url, anon, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
          flowType: "pkce",
        },
      })
    : null;

/** Build redirect URL for Supabase OAuth — always land on /auth/callback first. */
export function supabaseOAuthRedirect(nextPath = "/pipeline"): string {
  if (typeof window === "undefined") return "/auth/callback";
  const next = nextPath.startsWith("/") ? nextPath : "/pipeline";
  return `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
}

export function authHeader(token: string | undefined): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Fresh access token from the Supabase client (auto-refreshes if expired).
 * Use for admin API calls so a stale in-memory session never sends a bare
 * request that the backend rejects with "Authorization: Bearer <token> required".
 */
export async function getFreshAccessToken(
  fallback?: string
): Promise<string | undefined> {
  if (!supabase) return fallback;
  try {
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || fallback;
  } catch {
    return fallback;
  }
}

export type { Session };
