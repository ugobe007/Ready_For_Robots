import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

/** True when the signed-in user's email is in server ADMIN_EMAILS. */
export function useIsAdmin(): boolean {
  const { session } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = session?.access_token;
    if (!token) {
      setIsAdmin(false);
      return;
    }
    let cancelled = false;
    void fetch(
      `${getApiBase()}/api/user/me`,
      liveFetchInit({ headers: authHeader(token) })
    )
      .then(res => (res.ok ? res.json() : null))
      .then((data: { is_admin?: boolean } | null) => {
        if (!cancelled) setIsAdmin(Boolean(data?.is_admin));
      })
      .catch(() => {
        if (!cancelled) setIsAdmin(false);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  return isAdmin;
}

export type AdminAccess = "loading" | "admin" | "signin" | "denied";

/** Resolves after auth and `/api/user/me`, so a route can wait before rendering. */
export function useAdminAccess(): AdminAccess {
  const { session, loading } = useAuth();
  const [access, setAccess] = useState<AdminAccess>("loading");

  useEffect(() => {
    if (loading) return;
    const token = session?.access_token;
    if (!token) {
      setAccess("signin");
      return;
    }
    let cancelled = false;
    setAccess("loading");
    void fetch(
      `${getApiBase()}/api/user/me`,
      liveFetchInit({ headers: authHeader(token) })
    )
      .then(res => (res.ok ? res.json() : null))
      .then((data: { is_admin?: boolean } | null) => {
        if (!cancelled) setAccess(data?.is_admin ? "admin" : "denied");
      })
      .catch(() => {
        if (!cancelled) setAccess("denied");
      });
    return () => {
      cancelled = true;
    };
  }, [loading, session?.access_token]);

  if (loading) return "loading";
  return access;
}
