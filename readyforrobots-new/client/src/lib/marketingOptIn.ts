import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

const KEY = "rfr_marketing_opt_in";

/** OAuth redirects can't carry user metadata, so the choice waits here until sign-in. */
export function storeMarketingOptIn(optIn: boolean): void {
  try {
    window.localStorage.setItem(KEY, optIn ? "1" : "0");
  } catch {
    /* storage blocked: the account keeps the default (not opted in) */
  }
}

export function takeMarketingOptIn(): boolean | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    window.localStorage.removeItem(KEY);
    return raw === "1" ? true : raw === "0" ? false : null;
  } catch {
    return null;
  }
}

export function applyPendingMarketingOptIn(session: Session | null): void {
  if (!session || !supabase || typeof window === "undefined") return;
  const optIn = takeMarketingOptIn();
  if (optIn === null) return;
  void supabase.auth.updateUser({ data: { marketing_opt_in: optIn } });
}
