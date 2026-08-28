import { describe, expect, it, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  canonicalRobotUrl,
  emptyRobotIdentity,
  findUserFacingError,
  isAbortError,
  isCurrentRobotSubmit,
  isSilentFindError,
  sameRobotUrl,
} from "./robotUrlIdentity";
import {
  beginJobsHandoffForUrl,
  clearJobsHandoffSnapshot,
  loadJobsHandoffSnapshot,
  readJobsHandoffSnapshot,
  saveJobsHandoffSnapshot,
} from "./jobsHandoffSnapshot";
import { crmDeskForCurrentRobot } from "./jobsCrmAccount";
import { canStartFindSubmit, clearJobsWorkspaceSession } from "./jobsWorkflow";
import type { MatchJob } from "./robotJobMatch";
import type { KeptJobRow } from "./jobsCrmAccount";

const here = dirname(fileURLToPath(import.meta.url));

const A_URL = "https://www.agrobot.com/";
const B_URL = "https://www.greenfieldincorporated.com/";
const A_JOB: MatchJob = {
  job_key: "orchard-rows",
  title: "Work orchard rows",
  industry: "agriculture",
  path: "/jobs/orchard",
  company_name: "Sierra Orchard Co-op",
};
const B_JOB: MatchJob = {
  job_key: "weed-between-rows",
  title: "Weed between crop rows",
  industry: "agriculture",
  path: "/jobs/weed",
  company_name: "Named Farm Co-op",
};

function orchardRow(): KeptJobRow {
  return {
    id: "kept-orchard",
    job_key: A_JOB.job_key,
    employer_name: "Sierra Orchard Co-op",
    work_title: "Work orchard rows",
    workplace: "Modesto, CA",
    robot_name: "strawberry robot",
    robot_url: A_URL,
    job: A_JOB,
  };
}

function toteRow(): KeptJobRow {
  return {
    id: "kept-tote",
    job_key: "return-empty-totes",
    employer_name: "Novolex (Pactiv Evergreen)",
    work_title: "Return empty totes",
    workplace: "Warehouse",
    robot_name: "Greenfieldincorporated",
    robot_url: B_URL,
    job: {
      job_key: "return-empty-totes",
      title: "Return empty totes",
      industry: "logistics",
      path: "/jobs/totes",
      company_name: "Novolex (Pactiv Evergreen)",
    },
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

function deskForCurrent() {
  return crmDeskForCurrentRobot({
    snap: readJobsHandoffSnapshot(),
    accountRows: [orchardRow(), toteRow()],
  });
}

describe("robot URL identity", () => {
  it("canonicalizes host case and trailing slash", () => {
    expect(canonicalRobotUrl("https://WWW.Agrobot.com/")).toBe(
      "https://www.agrobot.com",
    );
    expect(sameRobotUrl(A_URL, "https://www.agrobot.com")).toBe(true);
    expect(sameRobotUrl(A_URL, B_URL)).toBe(false);
    expect(emptyRobotIdentity(B_URL).url).toBe(
      "https://www.greenfieldincorporated.com",
    );
    expect(isCurrentRobotSubmit(A_URL, "https://www.agrobot.com/")).toBe(true);
    expect(isAbortError({ name: "AbortError", message: "aborted" })).toBe(true);
  });

  it("does not map AbortError or Failed to fetch to Research failed", () => {
    expect(isSilentFindError({ name: "AbortError", message: "aborted" })).toBe(
      true,
    );
    expect(isSilentFindError({ name: "TypeError", message: "Failed to fetch" })).toBe(
      true,
    );
    expect(
      findUserFacingError(
        { name: "TypeError", message: "Failed to fetch" },
        "Research failed. Check the URL and try again.",
      ),
    ).toBeNull();
  });
});

describe("FIND A then FIND B never mixes robot identity", () => {
  beforeEach(() => {
    installMemoryStorage();
  });

  it("FIND company A (jobs) then FIND company B (zero jobs) → CRM is B empty", () => {
    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB],
    });
    expect(deskForCurrent().product).toBe("strawberry robot");
    expect(deskForCurrent().jobs.map(j => j.title)).toContain("Work orchard rows");

    beginJobsHandoffForUrl(B_URL, "BOT#25");
    const desk = deskForCurrent();
    expect(desk.product).toBe("BOT#25");
    expect(desk.product).not.toMatch(/strawberry/i);
    expect(desk.robotUrl).toBe(canonicalRobotUrl(B_URL));
    expect(desk.jobs).toEqual([]);
    expect(desk.savedCount).toBe(0);
    expect(loadJobsHandoffSnapshot(A_URL)).toBeNull();
  });

  it("FIND B then FIND A → CRM is A, not B", () => {
    beginJobsHandoffForUrl(B_URL, "BOT#25");
    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB],
    });
    const desk = deskForCurrent();
    expect(desk.product).toBe("strawberry robot");
    expect(desk.jobs.map(j => j.title)).toEqual(["Work orchard rows"]);
    expect(desk.jobs.some(j => /tote|BOT#25|Greenfield/i.test(j.title))).toBe(
      false,
    );
    expect(loadJobsHandoffSnapshot(B_URL)).toBeNull();
  });

  it("two agriculture OEMs never cross on the desk", () => {
    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB],
    });
    beginJobsHandoffForUrl(B_URL, "BOT#25");
    const greenfield = crmDeskForCurrentRobot({
      snap: readJobsHandoffSnapshot(),
      accountRows: [orchardRow()],
    });
    expect(greenfield.product).toBe("BOT#25");
    expect(greenfield.jobs).toEqual([]);
    expect(greenfield.jobs.some(j => /orchard|strawberry/i.test(j.title))).toBe(
      false,
    );

    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB, B_JOB],
    });
    const agrobot = crmDeskForCurrentRobot({
      snap: readJobsHandoffSnapshot(),
      accountRows: [orchardRow(), toteRow()],
    });
    expect(agrobot.product).toBe("strawberry robot");
    expect(agrobot.robotUrl).toBe(canonicalRobotUrl(A_URL));
    expect(agrobot.jobs.map(j => j.job_key)).toContain(A_JOB.job_key);
    expect(agrobot.jobs.map(j => j.job_key)).not.toContain("return-empty-totes");
    expect(agrobot.product).not.toMatch(/BOT#25|Greenfield/i);
  });

  it("no FIND URL → honest empty, never accountRows[0]", () => {
    const desk = crmDeskForCurrentRobot({
      snap: null,
      accountRows: [orchardRow(), toteRow()],
    });
    expect(desk.product).toBe("your robot");
    expect(desk.robotUrl).toBe("");
    expect(desk.jobs).toEqual([]);
    expect(desk.savedCount).toBe(0);
    expect(desk.product).not.toMatch(/strawberry/i);
  });

  it("wordmark / clear session flushes the previous robot handoff", () => {
    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB],
    });
    clearJobsWorkspaceSession();
    expect(readJobsHandoffSnapshot()).toBeNull();
    expect(deskForCurrent().jobs).toEqual([]);
    expect(deskForCurrent().product).toBe("your robot");
  });

  it("beginJobsHandoffForUrl overwrites leftover jobs before search returns", () => {
    saveJobsHandoffSnapshot({
      url: A_URL,
      productName: "strawberry robot",
      jobs: [A_JOB],
    });
    const snap = beginJobsHandoffForUrl(B_URL);
    expect(snap?.jobs).toEqual([]);
    expect(readJobsHandoffSnapshot()?.url).toBe(canonicalRobotUrl(B_URL));
    clearJobsHandoffSnapshot();
    expect(readJobsHandoffSnapshot()).toBeNull();
  });
});

describe("canStartFindSubmit isolates URL identity", () => {
  it("blocks the same URL while in flight, allows a different company URL", () => {
    expect(
      canStartFindSubmit({
        url: A_URL,
        inFlight: true,
        stage: "research",
        currentUrl: A_URL,
      }),
    ).toBe(false);
    expect(
      canStartFindSubmit({
        url: B_URL,
        inFlight: true,
        stage: "research",
        currentUrl: A_URL,
      }),
    ).toBe(true);
    expect(
      canStartFindSubmit({
        url: A_URL,
        inFlight: true,
        stage: "find",
      }),
    ).toBe(false);
  });
});

describe("FIND / CRM source canaries — robot-job-match is not the desk", () => {
  it("workspace flushes identity on submit and never calls robot-job-match", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const submitFind = workspace.slice(
      workspace.indexOf("async function submitFind"),
      workspace.indexOf("async function confirmSelection"),
    );
    expect(submitFind).toMatch(/bindSubmittedRobot\(submitUrl\)/);
    expect(submitFind).toMatch(/stillThisSubmit/);
    expect(submitFind).toMatch(/const research = bindSubmittedRobot\(submitUrl\)/);
    expect(submitFind).not.toMatch(/researchAbortRef\.current\?\.abort\(\)/);
    expect(submitFind).toMatch(/fetchRobotJobSearch/);
    expect(submitFind).not.toMatch(/fetchRobotJobMatch/);
    expect(workspace).not.toMatch(/fetchRobotJobMatch/);
    expect(workspace).toMatch(/function bindSubmittedRobot/);
    expect(workspace).toMatch(/beginJobsHandoffForUrl/);
    expect(workspace).toMatch(/clearJobsHandoffSnapshot/);
    const desk = readFileSync(
      join(here, "../components/JobsCrmDesk.tsx"),
      "utf8",
    );
    expect(desk).toMatch(/crmDeskForCurrentRobot/);
    expect(desk).not.toMatch(/robot-job-match/);
    const account = readFileSync(join(here, "./jobsCrmAccount.ts"), "utf8");
    expect(account).not.toMatch(/accountRows\[0\]\?\.robot_name/);
    expect(account).not.toMatch(/accountRows\[0\]\?\.robot_url/);
  });
});
