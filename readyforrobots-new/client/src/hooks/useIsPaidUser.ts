import { useAuth } from "@/contexts/AuthContext";

/**
 * Checks if a session has active paid subscription metadata.
 * Free accounts (including signed up users) have lead emails blurred per Vault Contact Protection policy.
 */
export function isPaidSubscriber(session: any, overrideIsPaid?: boolean): boolean {
  if (overrideIsPaid) return true;
  if (!session?.user) return false;

  const isPaidMetadata = Boolean(
    session.user.user_metadata?.subscription_tier === "paid" ||
      session.user.user_metadata?.is_paid === true ||
      session.user.app_metadata?.subscription_tier === "paid" ||
      session.user.app_metadata?.is_paid === true
  );

  return isPaidMetadata;
}

/**
 * React hook returning true if the current user has an active paid subscription plan ($19.99/mo Basic, Pro, or Premium).
 * Free registered users have lead emails blurred in accordance with Vault Contact Protection policy.
 */
export function useIsPaidUser(overrideIsPaid?: boolean): boolean {
  const { session } = useAuth();
  return isPaidSubscriber(session, overrideIsPaid);
}
