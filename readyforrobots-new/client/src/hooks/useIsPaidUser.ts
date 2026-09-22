import { useAuth } from "@/contexts/AuthContext";

/**
 * Checks if a session has paid subscriber status or internal admin credentials.
 */
export function isPaidSubscriber(session: any, overrideIsPaid?: boolean): boolean {
  if (overrideIsPaid) return true;
  if (!session?.user) return false;

  const email = String(session.user.email || "").toLowerCase();
  const isAdminOrInternal =
    email.endsWith("@readyforrobots.com") || email === "ugobe07@gmail.com";

  if (isAdminOrInternal) return true;

  const isPaidMetadata = Boolean(
    session.user.user_metadata?.subscription_tier === "paid" ||
      session.user.user_metadata?.is_paid === true ||
      session.user.app_metadata?.subscription_tier === "paid" ||
      session.user.app_metadata?.is_paid === true
  );

  return isPaidMetadata;
}

/**
 * React hook returning true if the current user has paid subscriber status or internal admin access.
 * Non-paid registered users have lead emails blurred in accordance with Vault Contact Protection policy.
 */
export function useIsPaidUser(overrideIsPaid?: boolean): boolean {
  const { session } = useAuth();
  return isPaidSubscriber(session, overrideIsPaid);
}
