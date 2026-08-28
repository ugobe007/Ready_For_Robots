/**
 * FIND research generations.
 *
 * Abort only the *previous* in-flight request. Never abort the controller
 * returned for the submit that just started. URL identity isolation still
 * drops late A responses after B starts; a same-URL retry is a new generation
 * so the first attempt cannot paint "Failed to fetch" over the second.
 */
import {
  isCurrentRobotSubmit,
  sameRobotUrl,
} from "@/lib/robotUrlIdentity";

export type FindResearchHandle = {
  url: string;
  generation: number;
  controller: AbortController;
};

export const FIND_RESEARCH_TIMEOUT_MESSAGE =
  "Lookup took too long. Try again — a manufacturer homepage is fine if we already know their robots.";

export const FIND_RESEARCH_INTERRUPTED_MESSAGE =
  "Research was interrupted. Try again.";

export function isFailedToFetchError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name?: string }).name) : "";
  const message =
    "message" in err ? String((err as { message?: string }).message) : "";
  if (name === "TypeError" && /failed to fetch|load failed|networkerror/i.test(message)) {
    return true;
  }
  return /^failed to fetch$/i.test(message.trim());
}

export function isTimeoutError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name?: string }).name) : "";
  const message =
    "message" in err ? String((err as { message?: string }).message) : "";
  return name === "TimeoutError" || /timed out after\s+\d/i.test(message);
}

/** Parent abort. Safari often surfaces CORS abort as TypeError Failed to fetch. */
export function isFindAbortError(err: unknown, signal?: AbortSignal): boolean {
  if (signal?.aborted) return true;
  if (!err || typeof err !== "object") return false;
  const name = "name" in err ? String((err as { name?: string }).name) : "";
  const message =
    "message" in err ? String((err as { message?: string }).message) : "";
  if (name === "TimeoutError") return false;
  return name === "AbortError" || /aborted|abort/i.test(message);
}

export function beginFindResearch(
  previous: FindResearchHandle | null,
  url: string,
): FindResearchHandle {
  const handle: FindResearchHandle = {
    url,
    generation: (previous?.generation ?? 0) + 1,
    controller: new AbortController(),
  };
  if (previous && previous.controller !== handle.controller) {
    previous.controller.abort();
  }
  return handle;
}

export function isLiveFindResearch(
  current: FindResearchHandle | null,
  handle: FindResearchHandle,
): boolean {
  return Boolean(
    current &&
      current.generation === handle.generation &&
      current.controller === handle.controller &&
      sameRobotUrl(current.url, handle.url) &&
      isCurrentRobotSubmit(current.url, handle.url),
  );
}

/** Late response from a previous URL or generation — drop it. */
export function shouldIgnoreStaleFindError(opts: {
  current: FindResearchHandle | null;
  handle: FindResearchHandle;
}): boolean {
  return !isLiveFindResearch(opts.current, opts.handle);
}

export function findResearchFailureMessage(err: unknown, fallback: string): string {
  if (
    isFindAbortError(err) ||
    isTimeoutError(err) ||
    isFailedToFetchError(err)
  ) {
    return FIND_RESEARCH_TIMEOUT_MESSAGE;
  }
  const detail = err instanceof Error ? err.message.trim() : "";
  if (
    detail &&
    !/^robot-(profile|job-search|oem-listing)\s+\d+$/i.test(detail)
  ) {
    return `${fallback} ${detail}`;
  }
  return fallback;
}

/**
 * Listing miss / timeout should fall through to composed search.
 * Parent abort of a stale generation must not start search on a dead signal.
 */
export function shouldContinueAfterListingError(opts: {
  current: FindResearchHandle | null;
  handle: FindResearchHandle;
  err: unknown;
}): boolean {
  if (!isLiveFindResearch(opts.current, opts.handle)) return false;
  if (opts.handle.controller.signal.aborted) return false;
  if (isFindAbortError(opts.err, opts.handle.controller.signal)) return false;
  return true;
}
