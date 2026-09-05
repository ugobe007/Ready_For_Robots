/**
 * pstack release helpers — How / Act / Critic fixtures.
 *
 * Not site chrome. FIND/CRM must not treat JobsPstackProtocol as a merge gate.
 * These fixtures are the checks that would have failed #173 (self-abort FIND
 * shown as Failed to fetch) and #172 (strawberry CRM leftover).
 */
import { findUserFacingError, isSilentFindError } from "./robotUrlIdentity";
import {
  findFailureBouncesHome,
  findLookupFailureOutcome,
} from "./findResearch";
import { crmDeskForCurrentRobot } from "./jobsCrmAccount";
import { beginJobsHandoffForUrl } from "./jobsHandoffSnapshot";
import { classJobsEmptyCopy } from "./jobsWorkflow";
import { CLASS_OPTION_IDS } from "./robotClassOptions";
import { lookupKnownOem } from "./knownOemLineups";
import type { MatchJob } from "./robotJobMatch";
import type { KeptJobRow } from "./jobsCrmAccount";

export const PSTACK_RELEASE_CHROME_REQUIRED = false;

export const FIND_ABORT_FIXTURE = {
  id: "find_abort",
  abort: { name: "AbortError", message: "The operation was aborted" },
  failedToFetch: { name: "TypeError", message: "Failed to fetch" },
  fallback: "Research failed. Check the URL and try again.",
} as const;

export const FIND_NO_HOME_FIXTURE = {
  id: "find_no_home",
  timeout: { name: "TimeoutError", message: "Timed out after 8000ms" },
  http500: { name: "Error", message: "robot-job-search 500" },
  landingHrefs: ["/", "/?new=1"] as const,
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
    FIND_ABORT_FIXTURE.fallback
  );
  const fetchFail = findUserFacingError(
    FIND_ABORT_FIXTURE.failedToFetch,
    FIND_ABORT_FIXTURE.fallback
  );
  return (
    abort === null &&
    fetchFail === null &&
    isSilentFindError(FIND_ABORT_FIXTURE.abort) &&
    isSilentFindError(FIND_ABORT_FIXTURE.failedToFetch)
  );
}

export function findErrorMustStayOnFind(err: unknown): boolean {
  const out = findLookupFailureOutcome(err);
  return (
    out.stage === "find" &&
    out.href === "/?visit=jobs" &&
    out.bounceHome === false &&
    Boolean(out.error) &&
    !findFailureBouncesHome(out.href) &&
    FIND_NO_HOME_FIXTURE.landingHrefs.every(href =>
      findFailureBouncesHome(href)
    )
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
    CRM_LEFTOVER_FIXTURE.nextProduct
  );
  return Boolean(
    snap &&
      snap.url.includes("greenfieldincorporated") &&
      snap.jobs.length === 0 &&
      !/strawberry/i.test(snap.productName)
  );
}

export const CLASS_PICKER_FIXTURE = {
  id: "class_picker",
  url: "https://www.agtonomy.com/",
  classId: "agriculture",
  prompt: "What type of robot?",
  emptyCopy: "No agriculture jobs for this robot yet.",
} as const;

export const HEALTHCARE_CLASS_FIXTURE = {
  id: "healthcare_class",
  url: "https://www.diligentrobots.com/",
  productName: "Moxi",
  classId: "healthcare",
  emptyCopy: "No healthcare jobs for this robot yet.",
  forbidClass: "humanoid",
  forbidEmpty: "No humanoid jobs for this robot yet.",
  extraTiles: [
    "mining",
    "warehouse",
    "logistics",
    "factory",
    "hospitality",
    "food_prep",
    "serving",
    "cleaning",
  ],
} as const;

export const URL_WORKFLOW_FIXTURE = {
  id: "url_workflow",
  command: "python3 scripts/url_workflow_critic.py --fixtures",
  corpus: "app/data/url_workflow_corpus.json",
  breaks: [
    "mixed_range_flattened",
    "chrome_as_sku",
    "cleaning_drone_as_scrubber",
    "company_class_not_product_class",
  ],
} as const;

/** Critic fixture: Diligent/Moxi is healthcare, Healthcare tile exists, empty copy is not humanoid. */
export function diligentMustNotBeHumanoidEmpty(): boolean {
  const listing = lookupKnownOem(HEALTHCARE_CLASS_FIXTURE.url);
  const moxi = listing?.robots.find(
    row => (row.name || "").toLowerCase() === "moxi"
  );
  const cls = String(moxi?.display_class || "").toLowerCase();
  const empty = classJobsEmptyCopy(HEALTHCARE_CLASS_FIXTURE.classId);
  const humanoidEmpty = classJobsEmptyCopy(
    HEALTHCARE_CLASS_FIXTURE.forbidClass
  );
  const hasNewTiles = HEALTHCARE_CLASS_FIXTURE.extraTiles.every(id =>
    CLASS_OPTION_IDS.includes(id)
  );
  return (
    Boolean(listing?.vendor_name?.toLowerCase().includes("diligent")) &&
    cls === HEALTHCARE_CLASS_FIXTURE.classId &&
    cls !== HEALTHCARE_CLASS_FIXTURE.forbidClass &&
    CLASS_OPTION_IDS.includes("healthcare") &&
    hasNewTiles &&
    CLASS_OPTION_IDS.length === 20 &&
    CLASS_OPTION_IDS.includes("food_prep") &&
    CLASS_OPTION_IDS.includes("serving") &&
    CLASS_OPTION_IDS.includes("cleaning") &&
    !CLASS_OPTION_IDS.includes("medical") &&
    empty === HEALTHCARE_CLASS_FIXTURE.emptyCopy &&
    !empty.toLowerCase().includes("humanoid") &&
    humanoidEmpty === HEALTHCARE_CLASS_FIXTURE.forbidEmpty
  );
}
