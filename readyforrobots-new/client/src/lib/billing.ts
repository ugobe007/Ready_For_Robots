import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";

export type BillingConfig = {
  enabled?: boolean;
  pro_available?: boolean;
  premium_available?: boolean;
  checkout_tiers?: string[];
};

export async function fetchBillingConfig(): Promise<BillingConfig> {
  const res = await fetch(
    `${getApiBase()}/api/billing/config`,
    liveFetchInit()
  );
  if (!res.ok) return { enabled: false };
  return res.json();
}

export async function startCheckout(
  accessToken: string,
  tier: "pro" | "premium"
): Promise<string> {
  const res = await fetch(
    `${getApiBase()}/api/billing/checkout`,
    liveFetchInit({
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeader(accessToken),
      },
      body: JSON.stringify({ tier }),
    })
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(String(data.detail || "Could not start checkout"));
  }
  const url = data.checkout_url as string | undefined;
  if (!url) throw new Error("Checkout URL missing from server response");
  return url;
}

export async function syncCheckoutSession(
  accessToken: string,
  sessionId: string
): Promise<void> {
  const res = await fetch(
    `${getApiBase()}/api/billing/sync?session_id=${encodeURIComponent(sessionId)}`,
    liveFetchInit({ headers: authHeader(accessToken) })
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(String(data.detail || "Could not sync subscription"));
  }
}

export async function openBillingPortal(accessToken: string): Promise<string> {
  const res = await fetch(
    `${getApiBase()}/api/billing/portal`,
    liveFetchInit({
      method: "POST",
      headers: authHeader(accessToken),
    })
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(String(data.detail || "Could not open billing portal"));
  const url = data.portal_url as string | undefined;
  if (!url) throw new Error("Portal URL missing");
  return url;
}
