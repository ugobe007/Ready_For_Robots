import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  EXAMPLE_JOBS,
  FREE_JOB_COUNT,
  JOB_FACTORS,
  jobScore,
  rankJobs,
} from "./robotJobsBoard";
import { isFindBoardHash, isFindBoardSearch } from "./jobsLanding";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("robot jobs board", () => {
  it("scores a job as the equal-weight average of seven factors ×100", () => {
    for (const job of EXAMPLE_JOBS) {
      expect(job.factors).toHaveLength(JOB_FACTORS.length);
    }
    const health = EXAMPLE_JOBS.find((job) => job.id === "j1");
    expect(health && jobScore(health)).toBe(76);
    const senior = EXAMPLE_JOBS.find((job) => job.id === "j8");
    expect(senior && jobScore(senior)).toBe(54);
  });

  it("sorts by score and locks everything after the free five", () => {
    const ranked = rankJobs(EXAMPLE_JOBS, { group: "all", timing: "all" });
    expect(ranked.map((job) => job.score)).toEqual(
      [...ranked.map((job) => job.score)].sort((a, b) => b - a)
    );
    expect(ranked.filter((job) => !job.locked)).toHaveLength(FREE_JOB_COUNT);
    expect(ranked.slice(FREE_JOB_COUNT).every((job) => job.locked)).toBe(true);
  });

  it("filters by industry group and timing before ranking", () => {
    const budget = rankJobs(EXAMPLE_JOBS, { group: "all", timing: "budget" });
    expect(budget.map((job) => job.company)).toEqual([
      "Regional health system",
      "Airport operator",
    ]);
    expect(budget.every((job) => !job.locked)).toBe(true);
    const factory = rankJobs(EXAMPLE_JOBS, { group: "factory", timing: "all" });
    expect(factory.every((job) => job.group === "factory")).toBe(true);
  });

  it("labels the page as example data and links FIND and employer posting", () => {
    const page = read("../pages/RobotJobs.tsx");
    expect(page).toMatch(/EXAMPLE DATA/);
    expect(page).toMatch(/JOBS SHOWN · EXAMPLE/);
    expect(page).toMatch(/Companies above are examples\./);
    expect(page).toMatch(/submitLabel="Rank for my robot →"/);
    expect(page).toMatch(/jobsFindHref\(trimmed\)/);
    expect(page).toMatch(/href="\/\?visit=candidates"/);
    expect(page).not.toMatch(/fetch\(/);
  });

  it("routes /jobs to the board and swaps How it works for Robot jobs in the nav", () => {
    const app = read("../App.tsx");
    expect(app).toMatch(/<Route path="\/jobs" component=\{JobsIndexRoute\} \/>/);
    expect(app).toMatch(/if \(search\) return <Redirect to=\{`\/\$\{search\}`\} \/>;\s*return <RobotJobs \/>;/);
    expect(app).toMatch(/<Route path="\/jobs\/:slug" component=\{Jobs\} \/>/);
    for (const rel of [
      "../components/editorial/SiteHeader.tsx",
      "../components/JobsLanding.tsx",
      "../components/EditorialResults.tsx",
    ]) {
      const src = read(rel);
      expect(src).toMatch(/label: "Robot jobs", href: "\/jobs"/);
      expect(src).not.toMatch(/label: "How it works"/);
    }
    expect(read("../components/JobsLanding.tsx")).toMatch(/id="how"/);
  });

  it("opens the board on bare /?visit=jobs and /#find; a URL still runs FIND", () => {
    expect(isFindBoardSearch("?visit=jobs")).toBe(true);
    expect(isFindBoardSearch("?visit=jobs&url=")).toBe(true);
    expect(isFindBoardSearch("?visit=jobs&url=https%3A%2F%2Fexample.com")).toBe(false);
    expect(isFindBoardSearch("?visit=jobs&product=ADAM")).toBe(false);
    expect(isFindBoardSearch("?visit=candidates")).toBe(false);
    expect(isFindBoardSearch("")).toBe(false);
    expect(isFindBoardHash("#find")).toBe(true);
    expect(isFindBoardHash("#how")).toBe(false);
    const jobs = read("../pages/Jobs.tsx");
    expect(jobs).toMatch(/isFindBoardHash\(hash\)\) return <Redirect to="\/jobs" \/>/);
    expect(jobs).toMatch(/isFindBoardSearch\(search\)\) \{\s*return <RobotJobs \/>/);
    expect(jobs).toMatch(/return <EditorialResults \/>/);
  });

  it("keeps FIND failures on the board with a retry and points Find buyers at /jobs", () => {
    const results = read("../components/EditorialResults.tsx");
    expect(results).toMatch(/return <RobotJobsBoard findError=\{error\} findUrl=\{initialUrl\} \/>/);
    expect(results).not.toMatch(/<a href="\/">/);
    const page = read("../pages/RobotJobs.tsx");
    expect(page).toMatch(/Could not load buyers\./);
    expect(page).toMatch(/jobsFindHref\(findUrl\)\}>Try again/);
    for (const rel of [
      "../components/editorial/SiteHeader.tsx",
      "../components/JobsLanding.tsx",
      "../components/EditorialResults.tsx",
    ]) {
      const src = read(rel);
      expect(src).toMatch(/label: "Find buyers", href: "\/jobs"/);
      expect(src).not.toMatch(/label: "Find buyers", href: "(\/|#find)"/);
    }
  });
});
