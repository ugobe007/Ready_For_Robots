/**
 * After OAuth/magic-link, Supabase sometimes lands on `/` without `next`.
 * When a session appears on a neutral page, resume stored checkout/deep-link intent.
 */
import { useEffect, useRef } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { clearPendingNext, peekPendingNext, postAuthRedirectTarget } from "@/lib/authNext";

const NEUTRAL_PATHS = new Set(["/", "/login", "/signup", "/auth/callback"]);

export default function PostAuthRedirect() {
  const { session, loading } = useAuth();
  const [, setLocation] = useLocation();
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
    clearPendingNext();
    setLocation(target);
  }, [loading, session, setLocation]);

  return null;
}
