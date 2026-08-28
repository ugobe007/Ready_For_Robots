/**
 * Product presentation offer — after Job Cards, behind signup + pay.
 * Value-first: never in front of FIND. No fake finished deck.
 */
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { authHeader } from "@/lib/supabase";
import { signupHrefForCheckout } from "@/lib/authNext";
import { jobsSignupHref } from "@/lib/jobsWorkflow";

export const JOBS_PRESENTATION_CTA = "Build a product presentation";
export const JOBS_PRESENTATION_HINT =
  "After Job Cards: a product presentation for this robot company. Sign up and pay first. We do not fake a finished deck.";
export const JOBS_PRESENTATION_PAY_HINT =
  "This offer requires a paid plan. Checkout unlocks the queue — we build it after payment.";
export const JOBS_PRESENTATION_QUEUED =
  "Queued. We will build this after payment. No finished deck until a provider returns one.";

export function jobsPresentationPaid(plan?: string | null): boolean {
  const slug = (plan || "").trim().toLowerCase();
  return slug === "paid" || slug === "pro" || slug === "premium";
}

export function jobsPresentationHref(opts: {
  signedIn: boolean;
  paid: boolean;
}): string {
  if (!opts.signedIn) {
    return jobsSignupHref("/pricing?upgrade=pro&src=jobs_presentation", "jobs_presentation");
  }
  if (!opts.paid) return "/pricing?upgrade=pro&src=jobs_presentation";
  return "#jobs-presentation";
}

export function jobsPresentationCheckoutHref(): string {
  return signupHrefForCheckout("pro");
}

export type PresentationRequestResult = {
  id?: number;
  status?: string;
  provider?: string | null;
  deck_url?: string | null;
  note?: string | null;
  paid?: boolean;
  queued?: boolean;
  provider_configured?: boolean;
  hint?: string;
};

export async function requestRobotPresentation(
  token: string,
  body: { url: string; companyName?: string; productName?: string },
): Promise<PresentationRequestResult> {
  const base = getApiBase();
  const res = await fetch(
    `${base}/api/jobs-crm/presentation`,
    liveFetchInit({
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...authHeader(token),
      },
      body: JSON.stringify({
        url: body.url,
        company_name: body.companyName || null,
        product_name: body.productName || null,
      }),
    }),
  );
  const data = (await res.json().catch(() => ({}))) as PresentationRequestResult & {
    detail?: string;
  };
  if (res.status === 402) {
    const err = new Error(data.detail || JOBS_PRESENTATION_PAY_HINT);
    (err as Error & { code?: string }).code = "payment_required";
    throw err;
  }
  if (!res.ok) {
    throw new Error(data.detail || data.hint || "Could not queue the presentation.");
  }
  return data;
}
