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

export function isAbortError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name?: string }).name) : "";
  const message =
    "message" in err ? String((err as { message?: string }).message) : "";
  return name === "AbortError" || /aborted|abort/i.test(message);
}
