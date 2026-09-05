/**
 * Post-auth navigation — preserve checkout and deep-link intent across OAuth/magic-link redirects.
 *
 * Supabase may land users on Site URL (/) when emailRedirectTo query strings are stripped.
 * localStorage + sessionStorage keep intent until auth completes.
 */

export const PENDING_NEXT_KEY = "rfr_pending_next";
export const PENDING_PLAN_KEY = "rfr_pending_plan";

function isSafePath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//");
}

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    const value =
      window.sessionStorage.getItem(key) ?? window.localStorage.getItem(key);
    return value && isSafePath(value) ? value : null;
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  if (typeof window === "undefined" || !isSafePath(value)) return;
  try {
    window.sessionStorage.setItem(key, value);
    window.localStorage.setItem(key, value);
  } catch {
    /* private mode */
  }
}

function removeStorage(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(key);
    window.localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

/** Read `next` from the current URL (or provided search string). */
export function readNextParam(search?: string): string | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(search ?? window.location.search).get("next");
  if (!raw) return null;
  try {
    const decoded = decodeURIComponent(raw);
    if (isSafePath(decoded)) return decoded;
  } catch {
    /* ignore malformed encoding */
  }
  return isSafePath(raw) ? raw : null;
}

export function storePendingNext(path: string): void {
  if (!isSafePath(path.split("?")[0] || path)) return;
  writeStorage(PENDING_NEXT_KEY, path);
}

export function storeCheckoutIntent(tier: "pro" | "premium"): void {
  const returnTo = `/pricing?upgrade=${tier}`;
  storePendingNext(returnTo);
  try {
    window.localStorage.setItem(PENDING_PLAN_KEY, tier);
    window.sessionStorage.setItem(PENDING_PLAN_KEY, tier);
  } catch {
    /* ignore */
  }
}

export function peekPendingPlan(): "pro" | "premium" | null {
  if (typeof window === "undefined") return null;
  try {
    const tier =
      window.sessionStorage.getItem(PENDING_PLAN_KEY) ??
      window.localStorage.getItem(PENDING_PLAN_KEY);
    return tier === "pro" || tier === "premium" ? tier : null;
  } catch {
    return null;
  }
}

export function peekPendingNext(): string | null {
  const stored = readStorage(PENDING_NEXT_KEY);
  if (stored) return stored;
  const plan = peekPendingPlan();
  return plan ? `/pricing?upgrade=${plan}` : null;
}

export function clearPendingNext(): void {
  removeStorage(PENDING_NEXT_KEY);
  removeStorage(PENDING_PLAN_KEY);
}

/** Read intended post-auth path without clearing stored intent. */
export function postAuthRedirectTarget(defaultPath = "/pipeline"): string {
  const fromUrl = readNextParam();
  if (fromUrl) return fromUrl;
  const pending = peekPendingNext();
  if (pending) return pending;
  return defaultPath;
}

/** Resolve where to send the user after auth; clears stored intent when used. */
export function resolvePostAuthPath(defaultPath = "/pipeline"): string {
  const dest = postAuthRedirectTarget(defaultPath);
  if (dest !== defaultPath || readNextParam() || peekPendingNext()) {
    clearPendingNext();
  }
  return dest;
}

/** Login href that returns to the current page (or an explicit path). */
export function loginHref(returnTo?: string): string {
  const target =
    returnTo ??
    (typeof window !== "undefined"
      ? `${window.location.pathname}${window.location.search}`
      : "/");
  const pathOnly = target.split("?")[0] || "/";
  if (!isSafePath(pathOnly)) {
    return "/login";
  }
  if (target.startsWith("/login") || target.startsWith("/signup")) {
    const search = typeof window !== "undefined" ? window.location.search : "";
    return search ? `/login${search}` : "/login";
  }
  storePendingNext(target);
  return `/login?next=${encodeURIComponent(target)}`;
}

/** Auth wall for Stripe checkout — sign in then resume checkout on /pricing. */
export function checkoutLoginPath(tier: "pro" | "premium"): string {
  const returnTo = `/pricing?upgrade=${tier}`;
  return `/login?next=${encodeURIComponent(returnTo)}&plan=${tier}`;
}

export function checkoutAuthHref(tier: "pro" | "premium"): string {
  storeCheckoutIntent(tier);
  return checkoutLoginPath(tier);
}

export function signupHrefForCheckout(tier: "pro" | "premium"): string {
  storeCheckoutIntent(tier);
  const returnTo = `/pricing?upgrade=${tier}`;
  return `/signup?plan=${tier}&next=${encodeURIComponent(returnTo)}`;
}

/**
 * Full-page navigation after auth — preserves query strings (wouter setLocation drops ?upgrade=pro).
 */
export function navigateAfterAuth(
  path: string,
  opts?: { clearIntent?: boolean }
): void {
  if (typeof window === "undefined" || !isSafePath(path.split("?")[0] || path))
    return;
  if (opts?.clearIntent !== false) clearPendingNext();
  if (`${window.location.pathname}${window.location.search}` === path) return;
  window.location.replace(path);
}

/** True when URL carries plan=pro|premium (upgrade intent). */
export function readPlanParam(search?: string): "pro" | "premium" | null {
  if (typeof window === "undefined") return null;
  const plan = (
    new URLSearchParams(search ?? window.location.search).get("plan") || ""
  ).toLowerCase();
  return plan === "pro" || plan === "premium" ? plan : null;
}
