/**
 * The submitted company URL is the only identity key for FIND review,
 * qualify, and Jobs CRM. Never inherit from a previous FIND, class/tile,
 * accountRows[0], or robot-job-match tote list.
 */
export type RobotPipelineIdentity = {
  url: string;
  productName: string;
  companyName?: string;
};

/** Canonical host+path used to bind FIND, handoff, and the CRM desk. */
export function canonicalRobotUrl(url: string): string {
  const raw = (url || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw);
    parsed.hash = "";
    const path = parsed.pathname.replace(/\/+$/, "") || "";
    return `${parsed.protocol}//${parsed.host.toLowerCase()}${path}${parsed.search}`;
  } catch {
    return raw.replace(/\/+$/, "");
  }
}

export function sameRobotUrl(
  a?: string | null,
  b?: string | null,
): boolean {
  const left = canonicalRobotUrl(a || "");
  const right = canonicalRobotUrl(b || "");
  return Boolean(left && right && left === right);
}

export function emptyRobotIdentity(
  url: string,
  productName = "",
): RobotPipelineIdentity {
  return {
    url: canonicalRobotUrl(url),
    productName: (productName || "").trim(),
  };
}

export function isCurrentRobotSubmit(
  currentUrl?: string | null,
  submitUrl?: string | null,
): boolean {
  return sameRobotUrl(currentUrl, submitUrl);
}

export function isAbortError(err: unknown, signal?: AbortSignal): boolean {
  if (signal?.aborted) return true;
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name?: string }).name) : "";
  const message =
    "message" in err ? String((err as { message?: string }).message) : "";
  if (name === "TimeoutError") return false;
  return name === "AbortError" || /aborted|abort/i.test(message);
}

function errorMessage(err: unknown): string {
  if (!err) return "";
  if (typeof err === "string") return err;
  if (typeof err === "object" && "message" in err) {
    return String((err as { message?: string }).message || "");
  }
  return String(err);
}

/**
 * Self-abort of in-flight FIND (bindSubmittedRobot / new URL) must not paint
 * "Research failed" or "Failed to fetch". Browsers often surface abort as
 * TypeError Failed to fetch instead of AbortError.
 */
export function isSilentFindError(err: unknown): boolean {
  if (isAbortError(err)) return true;
  return /failed to fetch/i.test(errorMessage(err));
}

/** User-visible FIND error, or null when the request was aborted/superseded. */
export function findUserFacingError(
  err: unknown,
  fallback: string,
): string | null {
  if (isSilentFindError(err)) return null;
  const detail = errorMessage(err).trim();
  if (/failed to fetch/i.test(detail)) return null;
  if (/timeout/i.test(detail)) {
    return "Lookup took too long. Try again — a manufacturer homepage is fine if we already know their robots.";
  }
  if (detail && !/^robot-(profile|job-search|oem-listing)\s+\d+$/i.test(detail)) {
    return `${fallback} ${detail}`.trim();
  }
  return fallback;
}
