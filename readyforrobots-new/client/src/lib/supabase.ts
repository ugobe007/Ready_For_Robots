import { createClient, type Session } from "@supabase/supabase-js";

const url = import.meta.env.VITE_PUBLIC_SUPABASE_URL || "";
const anon =
  import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  "";

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

export type { Session };
