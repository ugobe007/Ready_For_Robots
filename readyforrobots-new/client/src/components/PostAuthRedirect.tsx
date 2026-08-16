/**
 * After OAuth/magic-link, Supabase may land on `/` without `next`.
 * Resume stored deep-link intent only — never invent a /pipeline bounce from the product home.
 */
import { useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  clearPendingNext,
  peekPendingNext,
  navigateAfterAuth,
} from "@/lib/authNext";
import { normalizeJobsReturnPath, isJobsProductReturnPath } from "@/lib/signupWorkflowPath";

const NEUTRAL_PATHS = new Set(["/", "/login", "/signup", "/auth/callback", "/pricing"]);

export default function PostAuthRedirect() {
  const { session, loading } = useAuth();
  const handled = useRef(false);

  useEffect(() => {
    if (loading || !session || handled.current) return;
    const pending = peekPendingNext();
    if (!pending) return;

    const path = window.location.pathname;
    if (!NEUTRAL_PATHS.has(path)) return;

    let target = isJobsProductReturnPath(pending) ? normalizeJobsReturnPath(pending) : pending;
    const current = `${window.location.pathname}${window.location.search}`;
    if (current === target) {
      clearPendingNext();
      handled.current = true;
      return;
    }
    // Already on product home with a home-shaped pending (e.g. / or /?src=) — stay if paths match.
    if (path === "/" && target.split("?")[0] === "/" && !target.includes("?")) {
      clearPendingNext();
      handled.current = true;
      return;
    }

    handled.current = true;
    navigateAfterAuth(target);
  }, [loading, session]);

  return null;
}
