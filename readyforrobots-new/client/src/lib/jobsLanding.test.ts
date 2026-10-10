import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMPLOYER_EMPTY_MATCH,
  EMPLOYER_EXAMINE_HINT,
  EMPLOYER_PROCESS_STEPS,
  employerChosenCopy,
  EMPLOYER_WORK_TILE_IDS,
  LANDING_BRIEF_HEADLINE,
  LANDING_BRIEF_JOB_FIELD,
  LANDING_BRIEF_JOBS,
  LANDING_BRIEFING_HREF,
  LANDING_CANDIDATES_DOOR_LINE,
  LANDING_CANDIDATES_LABEL,
  LANDING_COLORS,
  LANDING_CTA_ROBOT_WORD,
  LANDING_DOOR_ICON_FILL,
  LANDING_DOOR_ICON_SCALE,
  LANDING_DOORS_CUE,
  LANDING_EYEBROW,
  LANDING_FAQ_HREF,
  LANDING_FOOTER_LINKS,
  LANDING_HEADLINE,
  LANDING_HEADLINE_AFTER,
  LANDING_HEADLINE_BEFORE,
  LANDING_HEADLINE_END,
  LANDING_HEADLINE_LEAD,
  LANDING_HEADLINE_ROBOT,
  LANDING_HOW_HEADLINE,
  LANDING_HOW_STEPS,
  LANDING_INTRO,
  LANDING_JOBS_DOOR_LINE,
  LANDING_JOBS_LABEL,
  LANDING_KICKER_JOBS,
  LANDING_LINK_MAP,
  LANDING_PRICING_HREF,
  LANDING_PRIVACY_HREF,
  LANDING_SIGNUP_HREF,
  LANDING_START_FREE_CTA,
  LANDING_SUBHEAD,
  LANDING_SUPPORT_HREF,
  LOOK_FOR_ROBOT_CANDIDATES_CTA,
  LOOK_FOR_ROBOT_JOBS_CTA,
  splitAccentWord,
  I_KNOW_THE_ROBOT_LABEL,
  jobsCandidatesHref,
  jobsFindHref,
  landingHeadlineParts,
  landingVisitFromSearch,
} from "./jobsLanding";
import { FEATURED_BUYER_QUOTES } from "./buyerQuotes";
import { FIND_JOBS_CTA } from "./jobsWorkflow";
import { catalogSkusForClass, listKnownOemCatalog } from "./knownOemCatalog";
import {
  FIND_JOBS_HOME_HEADLINE,
  jobsCrmOpenHref,
  jobsFreshHomeHref,
} from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("landing fork", () => {
  it("bare / is the home hero and ?visit=jobs is FIND", () => {
    expect(landingVisitFromSearch("")).toBe("landing");
    expect(landingVisitFromSearch("?new=1")).toBe("landing");
    expect(landingVisitFromSearch("?visit=jobs")).toBe("jobs");
    expect(landingVisitFromSearch("?job=geodis-dock")).toBe("landing");
    expect(landingVisitFromSearch("?visit=jobs&job=geodis-dock")).toBe("jobs");
    expect(landingVisitFromSearch("?visit=candidates")).toBe("candidates");
    expect(landingVisitFromSearch("?restore=1")).toBe("jobs");
    expect(landingVisitFromSearch("?visit=jobs&restore=1")).toBe("jobs");
    expect(jobsFreshHomeHref()).toBe("/");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
  });

  it("uses operator headline and two options only", () => {
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Jobs for Robots");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Robots for Jobs");
    expect(LANDING_DOORS_CUE).toBe("START HERE →");
    expect(LANDING_DOOR_ICON_SCALE).toBe(3);
    expect(LANDING_DOOR_ICON_FILL).toBe("#8B5CF6");
    expect(LANDING_JOBS_LABEL).toBe("Robot owner");
    expect(LANDING_CANDIDATES_LABEL).toBe("Employer");
    expect(LANDING_JOBS_DOOR_LINE).toBe("Paste a robot URL.");
    expect(LANDING_CANDIDATES_DOOR_LINE).toBe("Name the work.");
    expect(`${LANDING_HEADLINE_LEAD} ${LANDING_HEADLINE_END}`).toBe(
      LANDING_HEADLINE
    );
    expect(
      `${LANDING_HEADLINE_BEFORE}${LANDING_HEADLINE_ROBOT}${LANDING_HEADLINE_AFTER} ${LANDING_HEADLINE_END}`
    ).toBe(LANDING_HEADLINE);
    expect(LANDING_HEADLINE_ROBOT).toBe("Robots");
    expect(LANDING_CTA_ROBOT_WORD).toBe("Robots");
    expect(LANDING_HEADLINE).not.toMatch(
      /Jobs for robots\. Robots for jobs|Who is this visit|Robots need jobs/i
    );
    expect(
      landingHeadlineParts(LANDING_HEADLINE).every(
        part => part.accent === false
      )
    ).toBe(true);
    expect(splitAccentWord(LANDING_HEADLINE, LANDING_HEADLINE_ROBOT)).toEqual([
      { text: "Put ", accent: false },
      { text: "Robots", accent: true },
      { text: " to Work.", accent: false },
    ]);
    expect(
      splitAccentWord(LOOK_FOR_ROBOT_JOBS_CTA, LANDING_CTA_ROBOT_WORD)
    ).toEqual([
      { text: "Jobs for ", accent: false },
      { text: "Robots", accent: true },
    ]);
    expect(
      splitAccentWord(LOOK_FOR_ROBOT_CANDIDATES_CTA, LANDING_CTA_ROBOT_WORD)
    ).toEqual([
      { text: "Robots", accent: true },
      { text: " for Jobs", accent: false },
    ]);
    expect(LANDING_EYEBROW).toBe("Ready For Robots");
    expect(LANDING_KICKER_JOBS).toBe("Jobs");
    expect(LANDING_SUBHEAD).toBe(
      "Submit your robot URL to find jobs that match your robot."
    );
    expect(LANDING_INTRO).toBe(
      "Submit your robot URL or your robot job. We put robots to work."
    );
    expect(LANDING_INTRO).not.toMatch(/SIGNAL|Apollo|Hunter|ATS/i);
    expect(LANDING_BRIEF_HEADLINE).toBe("Jobs for robots.");
    expect(FIND_JOBS_HOME_HEADLINE).toBe("Jobs for robots.");
    expect(LANDING_HEADLINE).not.toBe(FIND_JOBS_HOME_HEADLINE);
    expect(LANDING_BRIEF_JOB_FIELD).toBe("Jobs");
    expect(LANDING_SUBHEAD).not.toMatch(
      /keep them in our CRM|Paste a product URL|who is this visit|choose your workflow/i
    );
    expect(LANDING_HOW_HEADLINE).toBe("Three steps. No buyer pipeline.");
    expect(LANDING_HOW_STEPS.map(s => s.title)).toEqual([
      "Show us your robot",
      "Available jobs",
      "CRM",
    ]);
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
    expect(landing).toMatch(/LANDING_HEADLINE_ROBOT/);
    expect(landing).toMatch(/rfr-landing-hero-form/);
    expect(landing).toMatch(/rfr-landing-employer-link/);
    expect(landing).toMatch(/LiveJobTape/);
    expect(landing).toMatch(/MARKET_TAPE_JOBS/);
    expect(landing).toMatch(/useTapeJobCard/);
    expect(landing).not.toMatch(/\?visit=jobs&job=/);
    const tapeCard = readFileSync(join(here, "./tapeJobCard.ts"), "utf8");
    expect(tapeCard).toMatch(/\/api\/robot-job-card\//);
    expect(landing).not.toMatch(/LANDING_HOW_STEPS|LANDING_VOCAB/);
    expect(landing).not.toMatch(
      /Look for buyers|SIGNAL|Apollo|Who is this visit/i
    );
    expect(landing).not.toMatch(/Market Intelligence|Automation Imperative/i);
    expect(landing).not.toMatch(/Headline options|headlineOptions|id:\"A\"/);
    expect(landing).not.toMatch(/CalJobsDesk|choose your workflow/i);
    const report = readFileSync(
      join(here, "../components/admin/AdminDailyJobsReport.tsx"),
      "utf8"
    );
    expect(report).toMatch(/Decision maker:/);
    expect(report).toMatch(/Job card/);
    expect(report).toMatch(/card_href/);
    expect(report).not.toMatch(/\[1\] Job type and description/);
    const inbox = readFileSync(join(here, "../pages/Inbox.tsx"), "utf8");
    expect(inbox).toMatch(/folder=all/);
    const admin = readFileSync(join(here, "../pages/Admin.tsx"), "utf8");
    expect(admin).toMatch(/\/api\/sales\/inbox\?folder=all/);
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(jobsPage).toMatch(/JobsLanding/);
    expect(jobsPage).toMatch(/EmployerMatchWorkspace/);
    expect(jobsPage).toMatch(/RobotJobsWorkspace/);
    expect(jobsPage).toMatch(/landingVisitFromSearch/);
    expect(jobsPage).not.toMatch(/forcedLanding/);
  });

  it("FIND home is one line, URL field, and a quiet employer link", () => {
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    const jobsPage = readFileSync(join(here, "../pages/Jobs.tsx"), "utf8");
    expect(jobsPage).toMatch(/RobotJobsWorkspace/);
    expect(jobsPage).toMatch(/JobsLanding/);
    expect(workspace).toMatch(/FIND_JOBS_HOME_HEADLINE/);
    expect(workspace).toMatch(/FIND_JOBS_HOME_SUBHEAD/);
    expect(workspace).toMatch(/aria-label="Find jobs for your robot"/);
    expect(workspace).toMatch(/Employers: name the work/);
    expect(workspace).not.toMatch(/FindProofJobs/);
    expect(workspace).toMatch(/LiveJobTape/);
    expect(workspace).toMatch(/MARKET_TAPE_JOBS/);
    expect(workspace).toMatch(/onSelect=\{handleSelectJob\}/);
    expect(workspace).toMatch(/LiveJobDetailModal/);
    expect(workspace).not.toMatch(/JobsProcessNav/);
    expect(workspace).not.toMatch(/aria-label="Jobs process"/);
    expect(workspace).not.toMatch(/ready_for_robots_hero/);
    expect(LANDING_HEADLINE).toBe("Put Robots to Work.");
    expect(FIND_JOBS_HOME_HEADLINE).toBe("Jobs for robots.");
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Jobs for Robots");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Robots for Jobs");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
    expect(landing).toMatch(/rfr-landing-headline/);
  });

  it("keeps unused landing CSS tokens off the FIND home path", () => {
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
    expect(LANDING_HEADLINE).toBe("Put Robots to Work.");
    expect(LANDING_SUBHEAD).toBe(
      "Submit your robot URL to find jobs that match your robot."
    );
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Jobs for Robots");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Robots for Jobs");
    expect(LANDING_DOORS_CUE).toBe("START HERE →");
    expect(LANDING_DOOR_ICON_SCALE).toBe(3);
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
    expect(landing).toMatch(/href=\{jobsCandidatesHref\(\)\}/);
    expect(landing).not.toMatch(/rfr-landing-windowbar/);
    expect(landing).toMatch(/rfr-landing-headline/);
    expect(landing).toMatch(/rfr-landing-subhead/);
    expect(landing).toMatch(/rfr-landing-hero-form/);
    expect(landing).toMatch(/rfr-landing-employer-link/);
    expect(landing).not.toMatch(/rfr-landing-doors-cue/);
    expect(landing).not.toMatch(/rfr-landing-door-who/);
    expect(landing).toMatch(/rfr-landing-accent/);
    expect(landing.indexOf("rfr-landing-headline")).toBeLessThan(
      landing.indexOf("rfr-landing-hero-mark")
    );
    expect(landing).toMatch(/KARE_FACE/);
    expect(landing).toMatch(/LandingFace scale=\{7\}/);
    expect(landing).toMatch(/ready_for_robots_hero\.jpg/);
    expect(landing).toMatch(/Find jobs →/);
    expect(landing).not.toMatch(/rfr-landing-hero-samples/);
    expect(landing).toMatch(/rfr-landing-stats-bar/);
    expect(landing).not.toMatch(/PixelBriefcase|PixelDoc|PixelHand/);
    expect(landing).not.toMatch(/PixelRobot/);
    expect(landing).not.toMatch(
      /CalJobsDesk|Headline options|headline-options/
    );
    expect(landing).not.toMatch(/Apollo|Hunter\.io|who is this visit/i);
    expect(pixels).not.toMatch(/ROBOT_ROWS/);
    expect(pixels).not.toMatch(/PixelRobot/);
    expect(pixels).toMatch(/BRIEFCASE_ROWS/);
    expect(css).not.toMatch(/EB Garamond/);
    expect(css).not.toMatch(/Silkscreen/);
    expect(css).not.toMatch(/Press Start/);
    expect(css).toMatch(/--font-landing-display:\s*var\(--font-display\)/);
    expect(css).toMatch(/--font-display:\s*"Outfit"/);
    expect(html).toMatch(/family=Outfit/);
    expect(css).toMatch(/rfr-landing-door-title/);
    expect(css).toMatch(/rfr-landing-subhead/);
    expect(css).toMatch(/rfr-landing-intro/);
    expect(css).not.toMatch(/repeating-conic-gradient/);
    expect(css).not.toMatch(/rfr-landing-windowbar/);
    expect(css).not.toMatch(/rfr-landing-hero-grid/);
    expect(html).not.toMatch(/family=EB\+Garamond/);
    expect(html).not.toMatch(/family=Silkscreen/);
    expect(html).not.toMatch(/family=Press\+Start/);
    expect(LANDING_COLORS.cream).toBe("#F3E8FF");
    expect(LANDING_COLORS.page).toBe("#0A0F1E");
    expect(LANDING_COLORS.charcoal).toBe("#141820");
    expect(LANDING_COLORS.emerald).toBe("#10B981");
    expect(LANDING_COLORS.mint).toBe("#2EE6A8");
    expect(LANDING_COLORS.violet).toBe("#8B5CF6");
    expect(landing).toMatch(/fill=\{C\.emerald\}/);
    expect(landing).toMatch(/background="transparent"/);
    expect(landing).not.toMatch(/part\.accent \? C\.mint/);
    expect(landing).not.toMatch(/landingHeadlineParts/);
    expect(css).toMatch(/--landing-cream:\s*#f3e8ff/);
    expect(css).toMatch(/--landing-charcoal:\s*#141820/);
    expect(css).toMatch(/--landing-emerald:\s*#10b981/);
    expect(css).not.toMatch(/landing-dither-paper/);
    expect(css).not.toMatch(/landing-dither-green/);
    expect(css).toMatch(
      /\.rfr-landing-headline[\s\S]*?color:\s*var\(--landing-cream\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-accent[\s\S]*?color:\s*var\(--landing-emerald\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-brief-employer[\s\S]*?color:\s*var\(--landing-emerald\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-hero-mark[\s\S]*?background:\s*transparent/
    );
    expect(css).not.toMatch(
      /\.rfr-landing-hero-mark\s*\{[^}]*background:\s*var\(--landing-green\)/
    );
    expect(css).not.toMatch(
      /\.rfr-landing-hero-mark\s*\{[^}]*border:\s*1px solid var\(--landing-green\)/
    );
    expect(css).toMatch(/\.rfr-landing-hero-mark[\s\S]*?margin-left:\s*auto/);
    expect(css).toMatch(
      /\.rfr-landing-kicker-jobs[\s\S]*?color:\s*var\(--landing-green\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-hero-row[\s\S]*?align-items:\s*flex-end/
    );
    expect(css).toMatch(
      /\.rfr-landing-doors[\s\S]*?justify-content:\s*flex-start/
    );
    expect(css).toMatch(/\.rfr-landing-doors[\s\S]*?flex-wrap:\s*wrap/);
    expect(css).toMatch(
      /@media \(min-width: 640px\)[\s\S]*?\.rfr-landing-doors\s*\{[\s\S]*?flex-wrap:\s*nowrap;/
    );
    expect(css).toMatch(
      /@media \(max-width: 639px\)[\s\S]*?\.rfr-landing-doors-choices\s*\{[\s\S]*?flex:\s*1 1 100%;/
    );
    expect(css).toMatch(/rfr-landing-doors-cue/);
    expect(css).toMatch(
      /\.rfr-landing-doors-cue[\s\S]*?background:\s*var\(--landing-emerald\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-door\s*\{[\s\S]*?display:\s*flex;[\s\S]*?flex-direction:\s*row;/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title[\s\S]*?display:\s*inline-flex/
    );
    expect(css).not.toMatch(
      /\.rfr-landing-doors\s*\{[^}]*justify-content:\s*space-between/
    );
    expect(css).toMatch(
      /\.rfr-landing-headline[\s\S]*?font-size:\s*clamp\(3\.05rem, 8vw, 5\.5rem\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-door--jobs\s*\{[\s\S]*?border:\s*2px solid var\(--landing-emerald\);/
    );
    expect(css).toMatch(
      /\.rfr-landing-door--candidates\s*\{[\s\S]*?border:\s*2px solid var\(--landing-cream\);/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-mark[\s\S]*?border:\s*2px solid #d6b15d;/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-mark[\s\S]*?background:\s*transparent;/
    );
    expect(css).toMatch(
      /\.rfr-landing-door:hover\s*\{[\s\S]*?border-color:\s*var\(--landing-emerald\);/
    );
  });

  it("FIND step 1 keeps URL plus a type dropdown then Find jobs", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8"
    );
    expect(I_KNOW_THE_ROBOT_LABEL).toBe("What type of robot?");
    expect(workspace).toMatch(/I_KNOW_THE_ROBOT_LABEL/);
    expect(workspace).toMatch(/border-emerald-400/);
    expect(workspace).toMatch(/FIND_JOBS_HOME_HEADLINE/);
    expect(workspace).not.toMatch(/JobsProcessNav/);
    expect(workspace).not.toMatch(/aria-label="Jobs process"/);
    expect(workspace).toMatch(/submitClassFind/);
    expect(workspace).toMatch(/classOptionsOrDefault/);
    expect(workspace).toMatch(/<select/);
    expect(workspace).toMatch(/id="job-definition"/);
    expect(workspace).toMatch(/onPickClass\(/);
    expect(workspace).toMatch(/disabled=\{/);
    expect(workspace).toMatch(/aria-label="Find jobs for your robot"/);
    expect(workspace).toMatch(/fetchRobotJobSearch/);
    expect(workspace).toMatch(/FIND_JOBS_CTA/);
    expect(workspace).not.toMatch(/Find jobs for this type/);
    expect(workspace).not.toMatch(/data-catalog-sku/);
    expect(workspace).not.toMatch(/catalogSkusForClass/);
    expect(workspace).not.toMatch(/I know the robot/);
  });

  it("employer process is MATCH then POST, not Cal or SIGNAL", () => {
    expect(EMPLOYER_PROCESS_STEPS.map(s => s.label)).toEqual([
      "What is the work",
      "Matching robots",
      "Post the job",
    ]);
    expect(EMPLOYER_EMPTY_MATCH).toMatch(/Post the job so OEMs can find it/);
    expect(EMPLOYER_EXAMINE_HINT).toMatch(/choose more than one/);
    expect(employerChosenCopy(0, 12)).toMatch(/more than one/);
    expect(employerChosenCopy(1, 12)).toMatch(/Check another/);
    expect(employerChosenCopy(3, 12)).toBe("3 of 12 robots chosen.");
    expect(EMPLOYER_WORK_TILE_IDS).toEqual([
      "pallets",
      "pick_pack",
      "delivery",
      "assembly",
      "amr",
      "serving",
      "cleaning",
      "healthcare",
      "industrial",
    ]);
    const employer = readFileSync(
      join(here, "../components/EmployerMatchWorkspace.tsx"),
      "utf8"
    );
    expect(employer).toMatch(/id="job-type"/);
    expect(employer).toMatch(/id="load-lb"/);
    expect(employer).toMatch(/id="hours-per-day"/);
    expect(employer).toMatch(/Robot Job Card/);
    expect(employer).toMatch(/Evidence limit/);
    const spec = readFileSync(join(here, "workSpec.ts"), "utf8");
    expect(spec).toMatch(/site survey/);
    expect(employer).toMatch(/aria-label="Look for robot candidates"/);
    expect(employer).toMatch(/aria-label="Employer process"/);
    expect(employer).toMatch(/fetchEmployerRobotMatch/);
    expect(employer).toMatch(/postEmployerJobDraft/);
    expect(employer).toMatch(/readEmployerJdFile/);
    expect(employer).toMatch(/type="file"/);
    expect(employer).toMatch(/EMPLOYER_JD_ACCEPT/);
    expect(employer).toMatch(/EmployerMatchedRobotModal/);
    expect(employer).toMatch(/Examine \$\{robot\.name\}/);
    expect(employer).toMatch(/EMPLOYER_EXAMINE_HINT/);
    expect(employer).toMatch(/toggleEmployerRobotKey/);
    expect(employer).toMatch(/employerChosenCopy/);
    expect(employer).toMatch(/Chosen robots/);
    expect(employer).toMatch(/setChecked\(\[\]\)/);
    expect(employer).toMatch(/EMPLOYER_COMPANY_LABEL/);
    expect(employer).toMatch(/EMPLOYER_JOB_NAME_LABEL/);
    expect(employer).toMatch(/EMPLOYER_CONTACT_LABEL/);
    expect(employer).toMatch(/id="contact-name"/);
    expect(employer).toMatch(/Lookup:/);
    expect(employer).toMatch(/catalogHttpUrl\(robot\.image_url\)/);
    expect(employer).not.toMatch(/type="radio"/);
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

describe("landing chrome hrefs cannot swap visits", () => {
  it("maps every landing CTA to a real Jobs or honest dest", () => {
    const byLabel = Object.fromEntries(
      LANDING_LINK_MAP.map(link => [link.label, link.href])
    );
    expect(byLabel[LOOK_FOR_ROBOT_JOBS_CTA]).toBe(jobsFindHref());
    expect(byLabel[LOOK_FOR_ROBOT_CANDIDATES_CTA]).toBe(jobsCandidatesHref());
    expect(byLabel[LANDING_START_FREE_CTA]).toBe(LANDING_SIGNUP_HREF);
    expect(byLabel[LANDING_START_FREE_CTA]).toBe(jobsCrmOpenHref(false));
    expect(byLabel["Download the 2026 briefing"]).toBe(LANDING_BRIEFING_HREF);
    expect(byLabel.Pricing).toBe(LANDING_PRICING_HREF);
    expect(byLabel.FAQ).toBe(LANDING_FAQ_HREF);
    expect(byLabel.Privacy).toBe(LANDING_PRIVACY_HREF);
    expect(byLabel["support@readyforrobots.com"]).toBe(LANDING_SUPPORT_HREF);
    expect(byLabel[LOOK_FOR_ROBOT_JOBS_CTA]).not.toBe(
      byLabel[LOOK_FOR_ROBOT_CANDIDATES_CTA]
    );
    expect(byLabel[LOOK_FOR_ROBOT_JOBS_CTA]).not.toBe(LANDING_SIGNUP_HREF);
    expect(byLabel[LOOK_FOR_ROBOT_CANDIDATES_CTA]).not.toBe(
      LANDING_SIGNUP_HREF
    );
    expect(byLabel[LOOK_FOR_ROBOT_JOBS_CTA]).not.toMatch(/signals|pipeline$/);
    expect(LANDING_HOW_STEPS[0].href).toBe(jobsFindHref());
    expect(LANDING_HOW_STEPS[1].href).toBe(jobsFindHref());
    expect(LANDING_HOW_STEPS[2].href).toBe(LANDING_SIGNUP_HREF);
    expect(LANDING_HOW_STEPS[2].href).not.toBe(jobsFindHref());
    expect(LANDING_FOOTER_LINKS.map(l => l.href)).toEqual([
      LANDING_PRICING_HREF,
      LANDING_FAQ_HREF,
      LANDING_PRIVACY_HREF,
      LANDING_SUPPORT_HREF,
    ]);
    expect(LANDING_FOOTER_LINKS.every(l => l.href && l.href !== "#")).toBe(
      true
    );
    expect(LANDING_LINK_MAP.every(l => l.href && !l.href.endsWith("#"))).toBe(
      true
    );
  });

  it("wires landing, FIND, MATCH, About, header, and CRM to those dests", () => {
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    const header = readFileSync(
      join(here, "../components/ExperimentHeader.tsx"),
      "utf8"
    );
    const intel = readFileSync(join(here, "../pages/Intelligence.tsx"), "utf8");
    const employer = readFileSync(
      join(here, "../components/EmployerMatchWorkspace.tsx"),
      "utf8"
    );
    const chrome = readFileSync(
      join(here, "../components/JobsProcessChrome.tsx"),
      "utf8"
    );
    const footer = readFileSync(
      join(here, "../components/layout/SiteFooter.tsx"),
      "utf8"
    );
    const pricing = readFileSync(join(here, "../pages/Pricing.tsx"), "utf8");
    const privacy = readFileSync(join(here, "../pages/Privacy.tsx"), "utf8");
    const legal = readFileSync(
      join(here, "../pages/LegalDocument.tsx"),
      "utf8"
    );
    expect(landing).toMatch(/jobsFindHref/);
    expect(landing).toMatch(/href=\{jobsCandidatesHref\(\)\}/);
    expect(landing).toMatch(/LANDING_FOOTER_LINKS/);
    expect(landing).not.toMatch(/href=\{step\.href\}/);
    expect(landing).not.toMatch(/LANDING_SIGNUP_HREF/);
    expect(landing).not.toMatch(/LANDING_BRIEFING_HREF/);
    expect(landing).not.toMatch(/href=["']#["']/);
    expect(landing).not.toMatch(/setLocation\(jobsFindHref/);
    expect(header).toMatch(/jobsHeaderJobsHref/);
    expect(header).toMatch(/href=\{crmHref\}/);
    expect(header).toMatch(/href="\/intelligence"/);
    expect(header).toMatch(/jobsFreshHomeHref\(\)/);
    expect(header).not.toMatch(/href=["']#["']/);
    expect(intel).toMatch(/jobsFindHref/);
    expect(intel).toMatch(/jobsCrmOpenHref\(false\)/);
    expect(intel).not.toMatch(/href=["']\/signals/);
    expect(employer).toMatch(/href=\{jobsFindHref\(\)\}/);
    expect(employer).not.toMatch(/setLocation\(jobsFindHref/);
    expect(chrome).toMatch(/jobsFindHref\(\)/);
    expect(chrome).not.toMatch(/jobsFreshHomeHref\(\)/);
    expect(footer).toMatch(/jobsCrmOpenHref\(false\)/);
    expect(pricing).toMatch(/ExperimentHeader/);
    expect(pricing).toMatch(/jobsCrmOpenHref\(false\)/);
    expect(pricing).toMatch(/id="faq"/);
    expect(pricing).not.toMatch(/from "@\/components\/Header"/);
    expect(privacy).toMatch(/LegalDocument/);
    expect(legal).toMatch(/ExperimentHeader/);
    expect(legal).toMatch(/jobsFindHref/);
    expect(privacy).not.toMatch(/href="\/preview"/);
  });

  it("landing employer quotes are named 2024–2026 work, linked to FIND", () => {
    expect(FEATURED_BUYER_QUOTES.length).toBeGreaterThanOrEqual(4);
    const companies = FEATURED_BUYER_QUOTES.map(q => q.company).join(" ");
    expect(companies).toMatch(/Rochester Regional Health/);
    expect(companies).toMatch(/GEODIS/);
    expect(companies).toMatch(/DHL Supply Chain/);
    expect(companies).toMatch(/Chipotle/);
    expect(companies).toMatch(/Marriott International/);
    for (const quote of FEATURED_BUYER_QUOTES) {
      expect(quote.author.trim().length).toBeGreaterThan(2);
      expect(quote.quote.trim().length).toBeGreaterThan(40);
      expect(quote.sourceUrl).toMatch(/^https:\/\//);
      expect(quote.opportunityHref).toBe(jobsFindHref());
      expect(quote.opportunityHref).not.toMatch(/\/pipeline/);
      expect(quote.date).not.toMatch(/Today|Yesterday/i);
      expect(quote.heatTier).not.toBe("HOT");
    }
    const banner = readFileSync(
      join(here, "../components/CustomerQuoteBanner.tsx"),
      "utf8"
    );
    expect(banner).toMatch(/jobsFindHref\(\)/);
    expect(banner).toMatch(/FIND_JOBS_CTA/);
    expect(banner).not.toMatch(/Job Opportunity/);
    expect(banner).not.toMatch(/\/pipeline\?co=/);
    const landing = readFileSync(
      join(here, "../components/JobsLanding.tsx"),
      "utf8"
    );
    expect(landing).toMatch(/CustomerQuoteBanner/);
    expect(landing).toMatch(/aria-label="Employer quotes"/);
    expect(FIND_JOBS_CTA).toBe("Find jobs →");
  });
});
