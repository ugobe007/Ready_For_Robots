import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMPLOYER_EMPTY_MATCH,
  EMPLOYER_PROCESS_STEPS,
  EMPLOYER_WORK_TILE_IDS,
  LANDING_BRIEF_HEADLINE,
  LANDING_BRIEF_JOB_FIELD,
  LANDING_BRIEF_JOBS,
  LANDING_BRIEFING_HREF,
  LANDING_COLORS,
  LANDING_CTA_ROBOT_WORD,
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
import { catalogSkusForClass, listKnownOemCatalog } from "./knownOemCatalog";
import { jobsCrmOpenHref, jobsFreshHomeHref } from "./jobsWorkflow";

const here = dirname(fileURLToPath(import.meta.url));

describe("landing fork", () => {
  it("bare / and ?new=1 are the landing fork, not FIND", () => {
    expect(landingVisitFromSearch("")).toBe("landing");
    expect(landingVisitFromSearch("?new=1")).toBe("landing");
    expect(landingVisitFromSearch("?visit=jobs")).toBe("jobs");
    expect(landingVisitFromSearch("?visit=candidates")).toBe("candidates");
    expect(landingVisitFromSearch("?restore=1")).toBe("jobs");
    expect(landingVisitFromSearch("?visit=jobs&restore=1")).toBe("jobs");
    expect(jobsFreshHomeHref()).toBe("/?new=1");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
  });

  it("uses operator headline and two options only", () => {
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Jobs for Robots");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Robots for Jobs");
    expect(LANDING_HEADLINE).toBe("Put Robots to Work.");
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
      landingHeadlineParts(LANDING_HEADLINE).every(part => part.accent === false)
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
      "Find jobs for robots and robots for jobs...."
    );
    expect(LANDING_INTRO).toBe(
      "Submit your robot URL or your robot job. We put robots to work."
    );
    expect(LANDING_INTRO).not.toMatch(/SIGNAL|Apollo|Hunter|ATS/i);
    expect(LANDING_BRIEF_HEADLINE).toBe("Jobs robots can take");
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
    expect(landing).toMatch(/LANDING_KICKER_JOBS/);
    expect(landing).toMatch(/data-landing-option="jobs"/);
    expect(landing).toMatch(/data-landing-option="candidates"/);
    expect(landing).toMatch(/LANDING_INTRO/);
    expect(landing).toMatch(/LANDING_BRIEF_JOBS/);
    expect(landing).toMatch(/LANDING_BRIEF_JOB_FIELD/);
    expect(landing).toMatch(/rfr-landing-brief-employer/);
    expect(landing).not.toMatch(/LANDING_HOW_STEPS|LANDING_VOCAB/);
    expect(landing).not.toMatch(
      /Look for buyers|SIGNAL|Apollo|Who is this visit/i
    );
    expect(landing).not.toMatch(/Market Intelligence|Automation Imperative/i);
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

  it("paints a sparse landing fork with Outfit headlines and both doors", () => {
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
      "Find jobs for robots and robots for jobs...."
    );
    expect(LOOK_FOR_ROBOT_JOBS_CTA).toBe("Jobs for Robots");
    expect(LOOK_FOR_ROBOT_CANDIDATES_CTA).toBe("Robots for Jobs");
    expect(jobsFindHref()).toBe("/?visit=jobs");
    expect(jobsCandidatesHref()).toBe("/?visit=candidates");
    expect(landing).toMatch(/href=\{jobsFindHref\(\)\}/);
    expect(landing).toMatch(/href=\{jobsCandidatesHref\(\)\}/);
    expect(landing).toMatch(/data-landing-option="jobs"/);
    expect(landing).toMatch(/data-landing-option="candidates"/);
    expect(landing).not.toMatch(/rfr-landing-windowbar/);
    expect(landing).toMatch(/rfr-landing-headline/);
    expect(landing).toMatch(/rfr-landing-intro/);
    expect(landing).toMatch(/rfr-landing-door-title/);
    expect(landing).toMatch(/rfr-landing-accent/);
    expect(landing.indexOf("rfr-landing-headline")).toBeLessThan(
      landing.indexOf("rfr-landing-hero-mark")
    );
    expect(landing).toMatch(/KARE_FACE/);
    expect(landing).toMatch(/LandingFace/);
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
    expect(LANDING_COLORS.cream).toBe("#F4EFE4");
    expect(LANDING_COLORS.page).toBe("#0A0F1E");
    expect(LANDING_COLORS.charcoal).toBe("#141820");
    expect(LANDING_COLORS.emerald).toBe("#10B981");
    expect(LANDING_COLORS.mint).toBe("#2EE6A8");
    expect(landing).toMatch(/fill=\{C\.emerald\}/);
    expect(landing).toMatch(/background="transparent"/);
    expect(landing).not.toMatch(/part\.accent \? C\.mint/);
    expect(landing).not.toMatch(/landingHeadlineParts/);
    expect(css).toMatch(/--landing-cream:\s*#f4efe4/);
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
    expect(css).toMatch(
      /\.rfr-landing-hero-mark[\s\S]*?margin-left:\s*auto/
    );
    expect(css).toMatch(
      /\.rfr-landing-kicker-jobs[\s\S]*?color:\s*var\(--landing-green\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-hero-row[\s\S]*?align-items:\s*flex-end/
    );
    expect(css).toMatch(
      /\.rfr-landing-doors[\s\S]*?justify-content:\s*flex-start/
    );
    expect(css).toMatch(/\.rfr-landing-doors[\s\S]*?gap:\s*2rem 3\.25rem/);
    expect(css).not.toMatch(
      /\.rfr-landing-doors\s*\{[^}]*justify-content:\s*space-between/
    );
    expect(css).not.toMatch(
      /\.rfr-landing-doors\s*\{[^}]*gap:\s*0\.75rem 0\.85rem/
    );
    expect(css).not.toMatch(
      /\.rfr-landing-doors\s*\{[^}]*gap:\s*1\.5rem 2rem/
    );
    expect(css).toMatch(
      /\.rfr-landing-headline[\s\S]*?font-size:\s*clamp\(3\.05rem, 8vw, 5\.5rem\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title[\s\S]*?font-size:\s*clamp\(1\.08rem, 1\.85vw, 1\.32rem\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title[\s\S]*?padding:\s*0\.9rem 1\.5rem/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title[\s\S]*?border:\s*1px solid var\(--landing-cream\)/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title[\s\S]*?background:\s*transparent/
    );
    expect(css).toMatch(
      /\.rfr-landing-door-title:hover \{\n  border-color:\s*var\(--landing-emerald\);\n\}/
    );
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
    expect(employer).toMatch(/readEmployerJdFile/);
    expect(employer).toMatch(/type="file"/);
    expect(employer).toMatch(/EMPLOYER_JD_ACCEPT/);
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
    expect(landing).toMatch(/href=\{jobsFindHref\(\)\}/);
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
    expect(privacy).toMatch(/ExperimentHeader/);
    expect(privacy).toMatch(/jobsFindHref/);
    expect(privacy).not.toMatch(/href="\/preview"/);
  });
});
