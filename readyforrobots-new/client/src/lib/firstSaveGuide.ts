const SEEN_KEY = "rfr_first_save_guide_seen_v1";
const FRESH_SIGNUP_KEY = "rfr_fresh_signup";

export function markFreshSignup(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(FRESH_SIGNUP_KEY, "1");
  } catch {
    /* private mode */
  }
}

export function hasSeenFirstSaveGuide(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return true;
  }
}

export function isFreshSignup(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.sessionStorage.getItem(FRESH_SIGNUP_KEY) === "1";
  } catch {
    return false;
  }
}

export function markFirstSaveGuideSeen(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SEEN_KEY, "1");
    window.sessionStorage.removeItem(FRESH_SIGNUP_KEY);
  } catch {
    /* private mode */
  }
}

export function shouldShowFirstSaveGuide(): boolean {
  // Disabled: popup blocked Step 4 customer-info flow. Keep helpers for future guided tours.
  return false;
}
