import type { SupabaseClient } from "@supabase/supabase-js";

/** Supabase OAuth errors land as query or hash params after provider redirect. */
export function readSupabaseOAuthError(): string | null {
  if (typeof window === "undefined") return null;

  const hash = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : "";
  const hashParams = new URLSearchParams(hash);
  const queryParams = new URLSearchParams(window.location.search);

  const description =
    hashParams.get("error_description") ||
    queryParams.get("error_description") ||
    hashParams.get("error") ||
    queryParams.get("error");

  if (!description) return null;
  return decodeURIComponent(description.replace(/\+/g, " "));
}

export function clearSupabaseOAuthParams(pathname: string, search: string): string {
  const params = new URLSearchParams(search);
  for (const key of ["code", "state", "error", "error_description", "error_code"]) {
    params.delete(key);
  }
  const next = params.toString();
  return next ? `${pathname}?${next}` : pathname;
}

/** Run PKCE exchange only on auth pages — not on /calendar (Google Calendar uses Fly callback). */
export async function finishSupabaseOAuthCallback(
  client: SupabaseClient,
  pathname: string,
  search: string,
): Promise<{ error: string | null }> {
  const params = new URLSearchParams(search);
  const code = params.get("code");
  if (!code) return { error: readSupabaseOAuthError() };

  const { error } = await client.auth.exchangeCodeForSession(code);
  if (error) {
    return { error: error.message || "Sign-in could not be completed." };
  }
  window.history.replaceState(null, "", clearSupabaseOAuthParams(pathname, search));
  return { error: null };
}
