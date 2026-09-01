import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { findUserFacingError, isSilentFindError } from "./robotUrlIdentity";
import {
  CLASS_PICKER_FIXTURE,
  CRM_LEFTOVER_FIXTURE,
  FIND_ABORT_FIXTURE,
  FIND_NO_HOME_FIXTURE,
  HEALTHCARE_CLASS_FIXTURE,
  PSTACK_RELEASE_CHROME_REQUIRED,
  abortMustNotSurfaceAsResearchFailed,
  bindUrlFlushesPriorRobot,
  diligentMustNotBeHumanoidEmpty,
  findErrorMustStayOnFind,
  leftoverCrmMustNotKeepPriorRobot,
} from "./pstackRelease";
import {
  beginJobsHandoffForUrl,
  saveJobsHandoffSnapshot,
} from "./jobsHandoffSnapshot";
import type { KeptJobRow } from "./jobsCrmAccount";
import type { MatchJob } from "./robotJobMatch";
import { criticGateIds } from "./pstackSite";

const here = dirname(fileURLToPath(import.meta.url));

const ORCHARD: MatchJob = {
  job_key: "orchard-rows",
  title: "Work orchard rows",
  industry: "agriculture",
  path: "/jobs/orchard",
  company_name: "Sierra Orchard Co-op",
};

function orchardRow(): KeptJobRow {
  return {
    id: "kept-orchard",
    job_key: ORCHARD.job_key,
    employer_name: "Sierra Orchard Co-op",
    work_title: "Work orchard rows",
    workplace: "Modesto, CA",
    robot_name: CRM_LEFTOVER_FIXTURE.priorProduct,
    robot_url: CRM_LEFTOVER_FIXTURE.priorUrl,
    job: ORCHARD,
  };
}

function installMemoryStorage() {
  const store = new Map<string, string>();
  const memory: Storage = {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };
  Object.defineProperty(globalThis, "window", {
    value: { sessionStorage: memory, localStorage: memory },
    configurable: true,
  });
  Object.defineProperty(globalThis, "sessionStorage", {
    value: memory,
    configurable: true,
  });
}

describe("pstack release — #173 self-abort FIND", () => {
  it("does not surface AbortError or Failed to fetch as Research failed", () => {
    expect(abortMustNotSurfaceAsResearchFailed()).toBe(true);
    expect(
      findUserFacingError(FIND_ABORT_FIXTURE.abort, FIND_ABORT_FIXTURE.fallback)
    ).toBeNull();
    expect(
      findUserFacingError(
        FIND_ABORT_FIXTURE.failedToFetch,
        FIND_ABORT_FIXTURE.fallback
      )
    ).toBeNull();
    expect(isSilentFindError(FIND_ABORT_FIXTURE.abort)).toBe(true);
    expect(isSilentFindError(FIND_ABORT_FIXTURE.failedToFetch)).toBe(true);
    const shown = findUserFacingError(
      new Error("robot-job-search 502"),
      FIND_ABORT_FIXTURE.fallback
    );
    expect(shown).toMatch(/Research failed/);
    expect(shown).not.toMatch(/Failed to fetch/i);
  });

  it("FIND catch returns on abort before setError", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    const submitFind = workspace.slice(
      workspace.indexOf("async function submitFind"),
      workspace.indexOf("async function confirmSelection")
    );
    const catchBlock = submitFind.slice(
      submitFind.lastIndexOf("} catch (err)")
    );
    expect(catchBlock).toMatch(/shouldIgnoreStaleFindError/);
    expect(catchBlock).toMatch(/isAbortError\(err,\s*ac\.signal\)/);
    expect(catchBlock).toMatch(/FIND_RESEARCH_INTERRUPTED_MESSAGE/);
    expect(catchBlock).not.toMatch(/Failed to fetch/i);
    expect(catchBlock).toMatch(/ensureFindStayVisit/);
    expect(submitFind).not.toMatch(/goJobsFreshHome/);
    expect(submitFind).toMatch(/bindSubmittedRobot\(submitUrl\)/);
    const abortAt = catchBlock.indexOf("isAbortError");
    const failAt = catchBlock.indexOf("lookupFailedMessage");
    expect(abortAt).toBeGreaterThan(-1);
    expect(failAt).toBeGreaterThan(abortAt);
    expect(catchBlock.indexOf("setError")).toBeGreaterThan(abortAt);
  });

  it("FIND timeout and 500 stay on /?visit=jobs", () => {
    expect(
      findErrorMustStayOnFind({
        name: FIND_NO_HOME_FIXTURE.timeout.name,
        message: FIND_NO_HOME_FIXTURE.timeout.message,
      })
    ).toBe(true);
    expect(
      findErrorMustStayOnFind({
        name: FIND_NO_HOME_FIXTURE.http500.name,
        message: FIND_NO_HOME_FIXTURE.http500.message,
      })
    ).toBe(true);
    expect(
      findErrorMustStayOnFind(FIND_ABORT_FIXTURE.failedToFetch)
    ).toBe(true);
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(jobsPage).toMatch(/forcedLanding && fromSearch === "landing"/);
  });
});

describe("pstack release — #172 leftover CRM strawberry robot", () => {
  beforeEach(() => {
    installMemoryStorage();
  });

  it("Greenfield FIND does not keep the prior strawberry robot on the desk", () => {
    saveJobsHandoffSnapshot({
      url: CRM_LEFTOVER_FIXTURE.priorUrl,
      productName: CRM_LEFTOVER_FIXTURE.priorProduct,
      jobs: [ORCHARD],
    });
    beginJobsHandoffForUrl(
      CRM_LEFTOVER_FIXTURE.nextUrl,
      CRM_LEFTOVER_FIXTURE.nextProduct
    );
    expect(bindUrlFlushesPriorRobot()).toBe(true);
    expect(
      leftoverCrmMustNotKeepPriorRobot({
        snap: {
          url: CRM_LEFTOVER_FIXTURE.nextUrl,
          productName: CRM_LEFTOVER_FIXTURE.nextProduct,
          jobs: [],
        },
        accountRows: [orchardRow()],
      })
    ).toBe(true);
  });
});

describe("pstack release authority is not FIND/CRM chrome", () => {
  it("does not require JobsPstackProtocol on FIND or CRM to merge", () => {
    expect(PSTACK_RELEASE_CHROME_REQUIRED).toBe(false);
    expect(criticGateIds()).toEqual([
      "find",
      "find_abort",
      "find_no_home",
      "find_identity",
      "crm_leftover",
      "job_cards",
      "wall",
      "matcher",
      "oem_extract",
      "class_picker",
      "healthcare_class",
      "ontology_industry_language",
      "url_workflow",
    ]);
    expect(CLASS_PICKER_FIXTURE.classId).toBe("agriculture");
    expect(CLASS_PICKER_FIXTURE.prompt).toBe("What type of robot?");
    expect(CLASS_PICKER_FIXTURE.emptyCopy).toMatch(/No agriculture jobs/);
    expect(HEALTHCARE_CLASS_FIXTURE.classId).toBe("healthcare");
    expect(HEALTHCARE_CLASS_FIXTURE.url).toContain("diligentrobots.com");
    expect(HEALTHCARE_CLASS_FIXTURE.forbidEmpty).toMatch(/No humanoid jobs/);
    expect(diligentMustNotBeHumanoidEmpty()).toBe(true);
    const desk = readFileSync(
      join(here, "../components/JobsCrmDesk.tsx"),
      "utf8"
    );
    expect(desk).not.toMatch(/JobsPstackProtocol/);
    expect(desk).not.toMatch(/JOBS AGENT PROTOCOL/);
    const readme = readFileSync(
      join(here, "../../../../pstack/README.md"),
      "utf8"
    );
    expect(readme).toMatch(/release gate/);
    expect(readme).toMatch(/not a banner/);
    expect(desk).not.toMatch(/JOBS AGENT PROTOCOL/);
  });
});
