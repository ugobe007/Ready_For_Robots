/**
 * After OAuth/magic-link, Supabase sometimes lands on `/` without `next`.
 * When a session appears on a neutral page, resume stored checkout/deep-link intent.
 */
import { useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { peekPendingNext, postAuthRedirectTarget, navigateAfterAuth } from "@/lib/authNext";

const NEUTRAL_PATHS = new Set(["/", "/login", "/signup", "/auth/callback", "/pricing"]);

export default function PostAuthRedirect() {
  const { session, loading } = useAuth();
  const handled = useRef(false);

  useEffect(() => {
    if (loading || !session || handled.current) return;
    const pending = peekPendingNext();
    const dest = postAuthRedirectTarget("/pipeline");
    const target = pending && pending !== "/" ? pending : dest !== "/" ? dest : null;
    if (!target) return;
    const path = window.location.pathname;
    if (!NEUTRAL_PATHS.has(path)) return;
    handled.current = true;
    navigateAfterAuth(target);
  }, [loading, session]);

  return null;
}
