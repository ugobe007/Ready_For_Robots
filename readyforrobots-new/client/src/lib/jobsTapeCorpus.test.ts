import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  MARKET_TAPE_JOBS,
  nextUnseenTapeJob,
  shuffleTapeJobs,
  uniqueTapeJobCount,
  type TapeJob,
} from "./jobsTapeCorpus";

const here = dirname(fileURLToPath(import.meta.url));

function job(key: string): TapeJob {
  return {
    key,
    title: key,
    industry: `${key} Corp · Austin`,
    path: "A → B",
    family: "transport",
  };
}

describe("market job tape", () => {
  it("lists unique named-employer jobs, not a 32-row repeating short loop", () => {
    expect(MARKET_TAPE_JOBS.length).toBeGreaterThanOrEqual(50);
    expect(uniqueTapeJobCount()).toBe(MARKET_TAPE_JOBS.length);
    const keys = MARKET_TAPE_JOBS.map((j) => j.key);
    const titles = MARKET_TAPE_JOBS.map((j) => j.title.toLowerCase());
    expect(new Set(keys).size).toBe(keys.length);
    expect(new Set(titles).size).toBe(titles.length);
    expect(keys).not.toContain("curascript_totes");
    expect(keys).not.toContain("hospital_med_carts");
    const named = MARKET_TAPE_JOBS.filter((j) => /·/.test(j.industry) || j.industry.split(" ").length >= 2);
    expect(named.length).toBe(MARKET_TAPE_JOBS.length);
  });

  it("skips jobs already on the board until the corpus is exhausted", () => {
    const order = [job("a"), job("b"), job("c"), job("d")];
    const visible = new Set(["a", "b", "c"]);
    const pick = nextUnseenTapeJob(order, 0, visible);
    expect(pick?.job.key).toBe("d");
    expect(pick?.nextCursor).toBe(0);
    expect(pick?.wrapped).toBe(true);
  });

  it("shuffles with a deterministic rng", () => {
    const items = [1, 2, 3, 4, 5];
    let i = 0;
    const rng = () => {
      const seq = [0.9, 0.1, 0.5, 0.2, 0.8];
      return seq[i++ % seq.length] ?? 0;
    };
    const shuffled = shuffleTapeJobs(items, rng);
    expect(shuffled).not.toEqual(items);
    expect([...shuffled].sort((a, b) => a - b)).toEqual(items);
  });

  it("keeps LiveJobTape on the unique-job helpers instead of cursor % length", () => {
    const tape = readFileSync(join(here, "../components/jobs/LiveJobTape.tsx"), "utf8");
    expect(tape).toMatch(/nextUnseenTapeJob/);
    expect(tape).toMatch(/shuffleTapeJobs/);
    expect(tape).not.toMatch(/corpus\[cursorRef\.current % corpus\.length\]/);
    expect(tape).toMatch(/setFoundCount\(corpus\.length\)/);
  });
});
