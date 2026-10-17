import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

const KEY = "rfr_marketing_opt_in";
const MAX_AGE_MS = 60 * 60 * 1000;
const CLOCK_SKEW_MS = 5 * 60 * 1000;

type Pending = { optIn: boolean; at: number };

/** OAuth redirects can't carry user metadata, so the choice waits here until sign-in. */
export function storeMarketingOptIn(optIn: boolean): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify({ optIn, at: Date.now() }));
  } catch {
    /* storage blocked: the account keeps the default (not opted in) */
  }
}

function readPending(): Pending | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Pending>;
    if (typeof parsed.optIn !== "boolean" || typeof parsed.at !== "number") {
      clearPending();
      return null;
    }
    return { optIn: parsed.optIn, at: parsed.at };
  } catch {
    clearPending();
    return null;
  }
}

function clearPending(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* storage blocked */
  }
}

/** Only new accounts created by the OAuth sign-up that stored the choice get it. */
export function applyPendingMarketingOptIn(session: Session | null): void {
  if (!session || !supabase || typeof window === "undefined") return;
  const pending = readPending();
  if (!pending) return;
  const user = session.user;
  const createdAt = Date.parse(user.created_at);
  if (
    Date.now() - pending.at > MAX_AGE_MS ||
    user.user_metadata?.marketing_opt_in !== undefined ||
    !Number.isFinite(createdAt) ||
    createdAt < pending.at - CLOCK_SKEW_MS
  ) {
    clearPending();
    return;
  }
  void supabase.auth
    .updateUser({ data: { marketing_opt_in: pending.optIn } })
    .then(({ error }) => {
      if (!error) clearPending();
    });
}
