import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMPLOYER_EMPTY_MATCH,
  EMPLOYER_PROCESS_STEPS,
  EMPLOYER_WORK_TILE_IDS,
  LANDING_BRIEF_JOBS,
  LANDING_CANDIDATES_HINT,
  LANDING_CANDIDATES_LABEL,
  LANDING_EYEBROW,
  LANDING_HEADLINE,
  LANDING_HOW_HEADLINE,
  LANDING_HOW_STEPS,
  LANDING_JOBS_HINT,
  LANDING_JOBS_LABEL,
  LANDING_SIGNUP_HREF,
  LANDING_START_FREE_CTA,
  LANDING_SUBHEAD,
  LANDING_VOCAB_HEADLINE,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  I_KNOW_THE_ROBOT_LABEL,
  jobsCandidatesHref,
  jobsFindHref,
  landingHeadlineParts,
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

  it("uses operator headline and two options only", () => {
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Look for robot jobs");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Look for robot candidates");
    expect(LANDING_HEADLINE).toBe("Put your robot to work.");
    expect(LANDING_HEADLINE).not.toMatch(
      /Jobs for robots\. Robots for jobs|Who is this visit|Robots need jobs/i
    );
    expect(landingHeadlineParts(LANDING_HEADLINE).at(-1)?.accent).toBe(true);
    expect(LANDING_EYEBROW).toMatch(/Robot Employment/);
    expect(LANDING_SUBHEAD).toBe(
      "Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM."
    );
    expect(LANDING_SUBHEAD).toMatch(/keep them in our CRM/i);
    expect(LANDING_SUBHEAD).not.toMatch(
      /who is this visit|choose your workflow/i
    );
    expect(LANDING_JOBS_LABEL).toBe("Robot owner");
    expect(LANDING_CANDIDATES_LABEL).toBe("Employer");
    expect(LANDING_JOBS_HINT).toMatch(/Paste a product URL/);
    expect(LANDING_JOBS_HINT).toMatch(/not a category guess/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/Tell us the work/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/named catalog robots/);
    expect(LANDING_CANDIDATES_HINT).toMatch(/post the job/i);
    expect(LANDING_HOW_HEADLINE).toBe("Three steps. No buyer pipeline.");
    expect(LANDING_HOW_STEPS.map(s => s.title)).toEqual([
      "Show us your robot",
      "Available jobs",
      "CRM",
    ]);
    expect(LANDING_VOCAB_HEADLINE).toMatch(
      /Employer\. Workplace\. Work\. Robot Job/
    );
    expect(LANDING_START_FREE_CTA).toBe("Start free workspace");
    expect(LANDING_SIGNUP_HREF).toBe(
      "/signup?next=%2Fpipeline%3Fsrc%3Djobs_activate&src=jobs_activate"
    );
    expect(LANDING_BRIEF_JOBS.map(j => j.employer)).toEqual([
      "Amazon",
      "Benchmark Senior Living",
      "Whitsons Culinary Group",
    ]);
    expect(
      LANDING_BRIEF_JOBS.every(j => j.employer && j.work && j.workplace)
    ).toBe(true);
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    expect(landing).toMatch(/LOOK_FOR_ROBOT_JOBS_CTA/);
    expect(landing).toMatch(/LOOK_FOR_ROBOT_CANDIDATES_CTA/);
    expect(landing).toMatch(/LANDING_JOBS_HINT/);
    expect(landing).toMatch(/LANDING_CANDIDATES_HINT/);
    expect(landing).toMatch(/LANDING_HOW_STEPS/);
    expect(landing).toMatch(/data-landing-option=\{option\}/);
    expect(landing).toMatch(/option="jobs"/);
    expect(landing).toMatch(/option="candidates"/);
    expect(landing).not.toMatch(
      /Look for buyers|SIGNAL|Apollo|Who is this visit/i
    );
    expect(landing).not.toMatch(/Headline options|headlineOptions|id:\"A\"/);
    expect(landing).not.toMatch(/CalJobsDesk|choose your workflow/i);
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(jobsPage).toMatch(/JobsLanding/);
    expect(jobsPage).toMatch(/EmployerMatchWorkspace/);
    expect(jobsPage).toMatch(/RobotJobsWorkspace/);
    expect(jobsPage).toMatch(/landingVisitFromSearch/);
    expect(jobsPage).toMatch(/forcedLanding && fromSearch === "landing"/);
    expect(jobsPage).not.toMatch(
      /const visit: LandingVisit = forcedLanding\s*\n\s*\? "landing"/
    );
  });

  it("ports Kare Macintosh chrome and both doors from rfr-70s-ui-source", () => {
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    const pixels = readFileSync(
      join(here, "../components/LandingPixels.tsx"),
      "utf8"
    );
    const css = readFileSync(join(here, "../index.css"), "utf8");
    const html = readFileSync(join(here, "../../index.html"), "utf8");
    expect(LANDING_HEADLINE).toBe("Put your robot to work.");
    expect(LANDING_SUBHEAD).toMatch(/keep them in our CRM/i);
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Look for robot jobs");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Look for robot candidates");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
    expect(landing).toMatch(/setLocation\(jobsFindHref\(\)\)/);
    expect(landing).toMatch(/setLocation\(jobsCandidatesHref\(\)\)/);
    expect(landing).toMatch(/option="jobs"/);
    expect(landing).toMatch(/option="candidates"/);
    expect(landing).toMatch(/rfr-landing-windowbar/);
    expect(landing).toMatch(/PixelRobot/);
    expect(landing).toMatch(/PixelBriefcase/);
    expect(landing).not.toMatch(
      /CalJobsDesk|Headline options|headline-options/
    );
    expect(landing).not.toMatch(/Apollo|Hunter\.io|who is this visit/i);
    expect(pixels).toMatch(/ROBOT_ROWS/);
    expect(pixels).toMatch(/BRIEFCASE_ROWS/);
    expect(css).toMatch(/EB Garamond/);
    expect(css).toMatch(/Silkscreen/);
    expect(css).toMatch(/repeating-conic-gradient/);
    expect(css).toMatch(/rfr-landing-windowbar/);
    expect(css).not.toMatch(/rfr-landing-hero-grid/);
    expect(html).toMatch(/family=EB\+Garamond/);
    expect(html).toMatch(/family=Silkscreen/);
  });

  it("FIND step 1 keeps URL plus I know the robot catalog pick", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    expect(I_KNOW_THE_ROBOT_LABEL).toBe("I know the robot");
    expect(workspace).toMatch(/I_KNOW_THE_ROBOT_LABEL/);
    expect(workspace).toMatch(/border-2 border-emerald-400/);
    expect(workspace).toMatch(
      /text-xl font-bold tracking-tight text-emerald-200/
    );
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
