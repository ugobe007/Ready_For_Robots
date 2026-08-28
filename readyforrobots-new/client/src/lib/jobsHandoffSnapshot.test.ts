import { describe, expect, it, beforeEach } from "vitest";
import {
  loadJobsHandoffSnapshot,
  normalizeRobotHandoffUrl,
  saveJobsHandoffSnapshot,
} from "./jobsHandoffSnapshot";
import { JOBS_ACTIVATE_CAP, JOBS_EXAMPLE_CAP, JOBS_PIPELINE_CAP } from "./jobsWorkflow";

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
    value: { sessionStorage: memory },
    configurable: true,
  });
  Object.defineProperty(globalThis, "sessionStorage", {
    value: memory,
    configurable: true,
  });
}

describe("jobsHandoffSnapshot", () => {
  beforeEach(() => {
    installMemoryStorage();
  });

  it("normalizes trailing slashes so FIND and pipeline URLs match", () => {
    expect(normalizeRobotHandoffUrl("https://www.dexmate.ai/")).toBe(
      "https://www.dexmate.ai",
    );
    expect(normalizeRobotHandoffUrl("https://WWW.Dexmate.ai/vega")).toBe(
      "https://www.dexmate.ai/vega",
    );
  });

  it("returns saved jobs only for the same robot URL", () => {
    saveJobsHandoffSnapshot({
      url: "https://www.dexmate.ai/",
      productName: "Vega",
      jobs: [
        {
          job_key: "cnc-load",
          title: "Load CNC cells",
          industry: "manufacturing",
          path: "/jobs/cnc-load",
        },
      ],
    });
    expect(loadJobsHandoffSnapshot("https://www.dexmate.ai")?.jobs[0]?.title).toBe(
      "Load CNC cells",
    );
    expect(loadJobsHandoffSnapshot("https://agilityrobotics.com")).toBeNull();
  });

  it("keeps See All above the 5-job example cap on the same page", () => {
    expect(JOBS_EXAMPLE_CAP).toBe(5);
    expect(JOBS_PIPELINE_CAP).toBe(15);
    expect(JOBS_ACTIVATE_CAP).toBe(15);
  });

  it("stores how many jobs the user checked", () => {
    saveJobsHandoffSnapshot({
      url: "https://www.magiclab.top/en",
      productName: "G1",
      selectedCount: 3,
      jobs: Array.from({ length: 3 }, (_, i) => ({
        job_key: `job-${i}`,
        title: `Job ${i}`,
        industry: "manufacturing",
        path: `/jobs/${i}`,
      })),
    });
    expect(loadJobsHandoffSnapshot("https://www.magiclab.top/en")?.selectedCount).toBe(3);
    expect(loadJobsHandoffSnapshot("https://www.magiclab.top/en")?.jobs).toHaveLength(3);
  });

  it("overwrites a prior strawberry robot even when the new FIND has no jobs", () => {
    saveJobsHandoffSnapshot({
      url: "https://www.agrobot.com/",
      productName: "strawberry robot",
      jobs: [
        {
          job_key: "orchard-rows",
          title: "Work orchard rows",
          industry: "agriculture",
          path: "/jobs/orchard",
          company_name: "Sierra Orchard Co-op",
        },
      ],
    });
    saveJobsHandoffSnapshot({
      url: "https://www.greenfieldincorporated.com/",
      productName: "BOT#25",
      jobs: [],
    });
    expect(loadJobsHandoffSnapshot("https://www.agrobot.com/")).toBeNull();
    const greenfield = loadJobsHandoffSnapshot(
      "https://www.greenfieldincorporated.com/",
    );
    expect(greenfield?.productName).toBe("BOT#25");
    expect(greenfield?.jobs).toEqual([]);
    expect(greenfield?.url).toBe("https://www.greenfieldincorporated.com");
  });
});
