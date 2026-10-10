import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { FetchTimeoutError, fetchWithTimeout } from "./apiBase";
import {
  beginFindResearch,
  FIND_RESEARCH_INTERRUPTED_MESSAGE,
  FIND_RESEARCH_TIMEOUT_MESSAGE,
  ensureFindStayVisit,
  findFailureBouncesHome,
  findFailureStayHref,
  findLookupFailureOutcome,
  findResearchFailureMessage,
  isFailedToFetchError,
  isFindAbortError,
  isLiveFindResearch,
  isTimeoutError,
  shouldContinueAfterListingError,
  shouldIgnoreStaleFindError,
} from "./findResearch";
import { canStartFindSubmit } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));
const A = "https://www.agrobot.com/";
const B = "https://www.greenfieldincorporated.com/";

describe("beginFindResearch never aborts the submit it just started", () => {
  it("first Greenfield submit is live and not aborted", () => {
    const first = beginFindResearch(null, B);
    expect(first.generation).toBe(1);
    expect(first.controller.signal.aborted).toBe(false);
    expect(isLiveFindResearch(first, first)).toBe(true);
    expect(shouldIgnoreStaleFindError({ current: first, handle: first })).toBe(
      false
    );
  });

  it("A then B aborts A and completes B", () => {
    const first = beginFindResearch(null, A);
    const second = beginFindResearch(first, B);
    expect(first.controller.signal.aborted).toBe(true);
    expect(second.controller.signal.aborted).toBe(false);
    expect(second.generation).toBe(2);
    expect(isLiveFindResearch(second, first)).toBe(false);
    expect(isLiveFindResearch(second, second)).toBe(true);
    expect(shouldIgnoreStaleFindError({ current: second, handle: first })).toBe(
      true
    );
    const safariFail = new TypeError("Failed to fetch");
    expect(shouldIgnoreStaleFindError({ current: second, handle: first })).toBe(
      true
    );
    expect(isFindAbortError(safariFail, first.controller.signal)).toBe(true);
    expect(isFindAbortError(safariFail, second.controller.signal)).toBe(false);
  });

  it("same-URL retry is a new generation so the first abort cannot paint failure", () => {
    const first = beginFindResearch(null, B);
    const retry = beginFindResearch(first, B);
    expect(first.controller.signal.aborted).toBe(true);
    expect(retry.controller.signal.aborted).toBe(false);
    expect(retry.generation).toBe(2);
    expect(isLiveFindResearch(retry, first)).toBe(false);
    expect(shouldIgnoreStaleFindError({ current: retry, handle: first })).toBe(
      true
    );
    const failedToFetch = new TypeError("Failed to fetch");
    expect(findResearchFailureMessage(failedToFetch, "Research failed.")).toBe(
      FIND_RESEARCH_TIMEOUT_MESSAGE
    );
    expect(
      findResearchFailureMessage(failedToFetch, "Research failed.")
    ).not.toMatch(/Failed to fetch/i);
  });

  it("listing timeout on a live submit continues to composed search", () => {
    const handle = beginFindResearch(null, B);
    const timeout = new FetchTimeoutError(5_000);
    expect(isTimeoutError(timeout)).toBe(true);
    expect(isFindAbortError(timeout, handle.controller.signal)).toBe(false);
    expect(
      shouldContinueAfterListingError({
        current: handle,
        handle,
        err: timeout,
      })
    ).toBe(true);
  });

  it("listing abort of a stale generation does not start search on a dead signal", () => {
    const first = beginFindResearch(null, A);
    const second = beginFindResearch(first, B);
    expect(
      shouldContinueAfterListingError({
        current: second,
        handle: first,
        err: new TypeError("Failed to fetch"),
      })
    ).toBe(false);
    expect(first.controller.signal.aborted).toBe(true);
  });
});

describe("FIND failure copy never surfaces Failed to fetch", () => {
  it("maps abort, timeout, and Safari Failed to fetch to retry copy", () => {
    expect(isFailedToFetchError(new TypeError("Failed to fetch"))).toBe(true);
    expect(
      findResearchFailureMessage(
        new TypeError("Failed to fetch"),
        "Research failed. Check the URL and try again."
      )
    ).toBe(FIND_RESEARCH_TIMEOUT_MESSAGE);
    expect(
      findResearchFailureMessage(
        new DOMException("The operation was aborted.", "AbortError"),
        "Research failed. Check the URL and try again."
      )
    ).toBe(FIND_RESEARCH_TIMEOUT_MESSAGE);
    expect(FIND_RESEARCH_INTERRUPTED_MESSAGE).not.toMatch(/Failed to fetch/i);
  });
});

describe("canStartFindSubmit allows retry after a failed Greenfield submit", () => {
  it("same URL retry works when research is leftover but not in flight", () => {
    expect(
      canStartFindSubmit({
        url: B,
        inFlight: false,
        stage: "research",
        currentUrl: B,
      })
    ).toBe(true);
    expect(
      canStartFindSubmit({
        url: B,
        inFlight: true,
        stage: "research",
        currentUrl: B,
      })
    ).toBe(false);
    expect(
      canStartFindSubmit({
        url: B,
        inFlight: true,
        stage: "research",
        currentUrl: A,
      })
    ).toBe(true);
  });
});

describe("fetchWithTimeout distinguishes parent abort from timeout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("throws AbortError without fetching when the parent signal is already aborted", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const ac = new AbortController();
    ac.abort();
    await expect(
      fetchWithTimeout("https://example.test/api", { signal: ac.signal }, 5_000)
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("throws TimeoutError when the timer fires and the parent is still live", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(
              new DOMException("The operation was aborted.", "AbortError")
            );
          });
        });
      })
    );
    const ac = new AbortController();
    const pending = fetchWithTimeout(
      "https://example.test/api",
      { signal: ac.signal },
      50
    );
    const assertion = expect(pending).rejects.toBeInstanceOf(FetchTimeoutError);
    await vi.advanceTimersByTimeAsync(60);
    await assertion;
    expect(ac.signal.aborted).toBe(false);
  });
});

describe("FIND workspace canaries — no self-abort after bind", () => {
  it("submitFind uses the controller bindSubmittedRobot just created", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    const submitFind = workspace.slice(
      workspace.indexOf("async function submitFind"),
      workspace.indexOf("async function confirmSelection")
    );
    expect(submitFind).toMatch(
      /const research = bindSubmittedRobot\(submitUrl\)/
    );
    expect(submitFind).toMatch(/const ac = research\.controller/);
    expect(submitFind).not.toMatch(/researchAbortRef\.current\?\.abort\(\)/);
    expect(submitFind).not.toMatch(/new AbortController/);
    expect(submitFind).toMatch(/shouldIgnoreStaleFindError/);
    expect(submitFind).toMatch(/shouldContinueAfterListingError/);
    expect(workspace).toMatch(/beginFindResearch/);
    expect(workspace).not.toMatch(/action="\/"/);
    const listing = readFileSync(join(here, "./robotProfile.ts"), "utf8");
    const search = readFileSync(join(here, "./robotJobSearch.ts"), "utf8");
    expect(listing).toMatch(/getApiBase\(\)/);
    expect(search).toMatch(/getPublicReadApiBase\(\)/);
    expect(search).not.toMatch(/getApiBase\(\)/);
    expect(submitFind).toMatch(/ensureFindStayVisit\(\)/);
    expect(submitFind).not.toMatch(/goJobsFreshHome/);
    expect(submitFind).not.toMatch(/JOBS_FRESH_HOME_EVENT/);
    expect(submitFind).not.toMatch(/\?new=1/);
    expect(submitFind).not.toMatch(/setLocation\("\/"\)/);
  });
});

describe("FIND timeout / 500 / abort stay on /?visit=jobs", () => {
  it("does not bounce timeout, 500, or Failed to fetch to landing", () => {
    expect(findFailureStayHref()).toBe("/?visit=jobs");
    expect(findFailureBouncesHome(null)).toBe(false);
    expect(findFailureBouncesHome("/?visit=jobs")).toBe(false);
    expect(findFailureBouncesHome("/")).toBe(true);
    expect(findFailureBouncesHome("/?new=1")).toBe(true);
    expect(findFailureBouncesHome("/?visit=candidates")).toBe(true);
    for (const err of [
      new FetchTimeoutError(8_000),
      new TypeError("Failed to fetch"),
      new Error("robot-job-search 500"),
      new DOMException("The operation was aborted.", "AbortError"),
    ]) {
      const out = findLookupFailureOutcome(err);
      expect(out.stage).toBe("find");
      expect(out.href).toBe("/?visit=jobs");
      expect(out.bounceHome).toBe(false);
      expect(out.error.length).toBeGreaterThan(0);
      expect(out.error).not.toMatch(/Failed to fetch/i);
      expect(findFailureBouncesHome(out.href)).toBe(false);
    }
  });

  it("rewrites a stripped visit back to FIND step 1", () => {
    const replaced: string[] = [];
    const loc = { pathname: "/", search: "?new=1", hash: "" };
    Object.defineProperty(globalThis, "window", {
      value: {
        location: loc,
        history: {
          state: null,
          replaceState: (_s: unknown, _t: string, url: string) => {
            replaced.push(String(url));
            const q = String(url).indexOf("?");
            loc.search = q >= 0 ? String(url).slice(q) : "";
          },
        },
      },
      configurable: true,
    });
    expect(ensureFindStayVisit()).toBe(true);
    expect(replaced[0]).toContain("visit=jobs");
    expect(ensureFindStayVisit()).toBe(false);
  });
});
