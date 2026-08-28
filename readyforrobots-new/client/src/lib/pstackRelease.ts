/**
 * pstack release helpers — How / Act / Critic fixtures.
 *
 * Not site chrome. FIND/CRM must not treat JobsPstackProtocol as a merge gate.
 * These fixtures are the checks that would have failed #173 (self-abort FIND
 * shown as Failed to fetch) and #172 (strawberry CRM leftover).
 */
import {
  findUserFacingError,
  isSilentFindError,
} from "./robotUrlIdentity";
import { crmDeskForCurrentRobot } from "./jobsCrmAccount";
import { beginJobsHandoffForUrl } from "./jobsHandoffSnapshot";
import type { MatchJob } from "./robotJobMatch";
import type { KeptJobRow } from "./jobsCrmAccount";

export const PSTACK_RELEASE_CHROME_REQUIRED = false;

export const FIND_ABORT_FIXTURE = {
  id: "find_abort",
  abort: { name: "AbortError", message: "The operation was aborted" },
  failedToFetch: { name: "TypeError", message: "Failed to fetch" },
  fallback: "Research failed. Check the URL and try again.",
} as const;

export const CRM_LEFTOVER_FIXTURE = {
  id: "crm_leftover",
  priorUrl: "https://www.agrobot.com/",
  priorProduct: "strawberry robot",
  nextUrl: "https://www.greenfieldincorporated.com/",
  nextProduct: "BOT#25",
} as const;

export function abortMustNotSurfaceAsResearchFailed(): boolean {
  const abort = findUserFacingError(
    FIND_ABORT_FIXTURE.abort,
    FIND_ABORT_FIXTURE.fallback,
  );
  const fetchFail = findUserFacingError(
    FIND_ABORT_FIXTURE.failedToFetch,
    FIND_ABORT_FIXTURE.fallback,
  );
  return (
    abort === null &&
    fetchFail === null &&
    isSilentFindError(FIND_ABORT_FIXTURE.abort) &&
    isSilentFindError(FIND_ABORT_FIXTURE.failedToFetch)
  );
}

export function leftoverCrmMustNotKeepPriorRobot(opts: {
  snap: { url: string; productName: string; jobs: MatchJob[] } | null;
  accountRows: KeptJobRow[];
}): boolean {
  const desk = crmDeskForCurrentRobot(opts);
  const product = desk.product.toLowerCase();
  return (
    desk.robotUrl.includes("greenfieldincorporated") &&
    !/strawberry/.test(product) &&
    !desk.jobs.some(job => /orchard|strawberry/i.test(job.title))
  );
}

export function bindUrlFlushesPriorRobot(): boolean {
  const snap = beginJobsHandoffForUrl(
    CRM_LEFTOVER_FIXTURE.nextUrl,
    CRM_LEFTOVER_FIXTURE.nextProduct,
  );
  return Boolean(
    snap &&
      snap.url.includes("greenfieldincorporated") &&
      snap.jobs.length === 0 &&
      !/strawberry/i.test(snap.productName),
  );
}

export const CLASS_PICKER_FIXTURE = {
  id: "class_picker",
  url: "https://www.agtonomy.com/",
  classId: "agriculture",
  prompt: "What type of robot?",
  emptyCopy: "No agriculture jobs for this robot yet.",
} as const;
