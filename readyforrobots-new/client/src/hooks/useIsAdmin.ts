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
