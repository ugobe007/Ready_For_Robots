import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMPLOYER_EMPTY_MATCH,
  EMPLOYER_PROCESS_STEPS,
  EMPLOYER_WORK_TILE_IDS,
  LANDING_CANDIDATES_HINT,
  LANDING_HEADLINE,
  LANDING_JOBS_HINT,
  LANDING_SUBHEAD,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  I_KNOW_THE_ROBOT_LABEL,
  jobsCandidatesHref,
  jobsFindHref,
  landingVisitFromSearch,
} from "./jobsLanding";
import { catalogSkusForClass, listKnownOemCatalog } from "./knownOemCatalog";
import { jobsFreshHomeHref } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("landing fork", () => {
  it("bare / and ?new=1 are the landing fork, not FIND", () => {
    expect(landingVisitFromSearch("")).toBe("landing");
    expect(landingVisitFromSearch("?new=1")).toBe("landing");
    expect(landingVisitFromSearch("?visit=jobs")).toBe("jobs");
    expect(landingVisitFromSearch("?visit=candidates")).toBe("candidates");
    expect(jobsFreshHomeHref()).toBe("/?new=1");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
  });

  it("uses operator CTAs and two options only", () => {
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Look for robot jobs");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Look for robot candidates");
    expect(LANDING_HEADLINE).toBe("Jobs for robots. Robots for jobs.");
    expect(LANDING_SUBHEAD).toMatch(/robot or you have work/i);
    expect(LANDING_SUBHEAD).toMatch(/matches before you sign up/i);
    expect(LANDING_SUBHEAD).not.toMatch(/who is this visit|choose your workflow/i);
    expect(LANDING_JOBS_HINT).toMatch(/You have a robot/);
    expect(LANDING_JOBS_HINT).toMatch(/URL|catalog/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/You have work/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/named robots/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/post the job/i);
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    expect(landing).toMatch(/LOOK_FOR_ROBOT_JOBS_CTA/);
    expect(landing).toMatch(/LOOK_FOR_ROBOT_CANDIDATES_CTA/);
    expect(landing).toMatch(/LANDING_JOBS_HINT/);
    expect(landing).toMatch(/LANDING_CANDIDATES_HINT/);
    expect(landing).not.toMatch(/Look for buyers|SIGNAL|Apollo|Who is this visit/i);
    expect(landing).not.toMatch(/CalJobsDesk|choose your workflow/i);
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(jobsPage).toMatch(/JobsLanding/);
    expect(jobsPage).toMatch(/EmployerMatchWorkspace/);
    expect(jobsPage).toMatch(/RobotJobsWorkspace/);
    expect(jobsPage).toMatch(/landingVisitFromSearch/);
  });

  it("FIND step 1 keeps URL plus I know the robot catalog pick", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    expect(I_KNOW_THE_ROBOT_LABEL).toBe("I know the robot");
    expect(workspace).toMatch(/I_KNOW_THE_ROBOT_LABEL/);
    expect(workspace).toMatch(/submitKnownSku/);
    expect(workspace).toMatch(/submitClassFind/);
    expect(workspace).toMatch(/catalogSkusForClass/);
    expect(workspace).toMatch(/aria-label="Find jobs for your robot"/);
    expect(workspace).toMatch(/fetchRobotJobSearch/);
    expect(workspace).toMatch(/Find jobs for this type/);
    expect(workspace).toMatch(/data-catalog-sku/);
  });

  it("employer process is MATCH then POST, not Cal or SIGNAL", () => {
    expect(EMPLOYER_PROCESS_STEPS.map(s => s.label)).toEqual([
      "What is the work",
      "Matching robots",
      "Post the job",
    ]);
    expect(EMPLOYER_EMPTY_MATCH).toMatch(/Post the job so OEMs can find it/);
    expect(EMPLOYER_WORK_TILE_IDS).toContain("serving");
    expect(EMPLOYER_WORK_TILE_IDS).toContain("cleaning");
    expect(EMPLOYER_WORK_TILE_IDS).toContain("warehouse");
    expect(EMPLOYER_WORK_TILE_IDS).toContain("healthcare");
    expect(EMPLOYER_WORK_TILE_IDS).toContain("food_prep");
    const employer = readFileSync(
      join(here, "../components/EmployerMatchWorkspace.tsx"),
      "utf8"
    );
    expect(employer).toMatch(/aria-label="Look for robot candidates"/);
    expect(employer).toMatch(/aria-label="Employer process"/);
    expect(employer).toMatch(/fetchEmployerRobotMatch/);
    expect(employer).toMatch(/postEmployerJobDraft/);
    expect(employer).not.toMatch(/SIGNAL|Apollo|find-robots/i);
    expect(employer).not.toMatch(/CalJobsDesk|send_buyer_intro/);
  });

  it("catalog pick uses named evidence SKUs, not invented models", () => {
    const all = listKnownOemCatalog();
    expect(all.length).toBeGreaterThan(10);
    const serving = catalogSkusForClass("serving");
    expect(serving.some(s => /BellaBot/i.test(s.name))).toBe(true);
    expect(serving.every(s => s.name && s.vendorName && s.findUrl)).toBe(true);
    expect(serving.some(s => /Humanoid Series/i.test(s.name))).toBe(false);
    const xpeng = all.filter(s => /xpeng\.com/i.test(s.host));
    expect(xpeng.map(s => s.name)).toEqual(["IRON"]);
  });
});
