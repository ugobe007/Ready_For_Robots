import { describe, expect, it } from "vitest";
import {
  OEM_INTRO_BLANK,
  OEM_INTRO_PAY_BLANK,
  OEM_INTRO_TERM_BLANK,
  composeEmployerNeedIntro,
  composeRobotCompanyIntro,
} from "./oemJobIntro";

describe("composeRobotCompanyIntro", () => {
  it("uses Phelan's robot-coordinator wording with named job facts", () => {
    const text = composeRobotCompanyIntro({
      contactName: "Maya Chen",
      robotName: "Stretch",
      title: "Pharmacy delivery",
      employer: "Rochester Regional Health",
      locality: "Rochester, NY",
      monthlyComp: "4200",
      duration: "12 months",
      requirements: "Indoor hall delivery between units and central pharmacy",
      decisionMakerName: "Priya Shah",
    });
    expect(text).toContain("Hi Maya, nice to meet you.");
    expect(text).toContain("I am a robot coordinator for ReadyForRobots");
    expect(text).toContain(
      "pharmacy delivery at Rochester Regional Health in Rochester, NY"
    );
    expect(text).toContain("$4200 per month for 12 months");
    expect(text).toContain(
      "arrange a call with Priya at Rochester Regional Health"
    );
    expect(text).toMatch(/Phelan\.$/);
    expect(text).not.toMatch(/SIGNAL|match%|ROI/i);
  });

  it("leaves blanks instead of inventing pay, robot, or people", () => {
    const text = composeRobotCompanyIntro({
      title: "Pallet move",
      employer: "GEODIS",
      locality: "Plainfield, IN",
      requirements: "Unload inbound trailers and stage pallets at the dock.",
    });
    expect(text.startsWith(`Hi ${OEM_INTRO_BLANK},`)).toBe(true);
    expect(text).toContain(
      `$${OEM_INTRO_PAY_BLANK} per month for ${OEM_INTRO_TERM_BLANK}`
    );
    expect(text).toContain("arrange a call with GEODIS");
    expect(text).not.toContain("operations@");
    expect(text).not.toContain("Operational Lead");
  });

  it("writes the employer-need intro without inventing robots or skills", () => {
    const text = composeEmployerNeedIntro({
      contactName: "Priya Shah",
      announcedNeed: "Pallet move",
      automationTasks: "Unload inbound trailers and stage pallets at the dock.",
      skills: "indoor navigation",
      capabilities: "500 lb payload",
    });
    expect(text).toContain("Hi Priya, nice to meet you.");
    expect(text).toContain("I help find robots for automation jobs");
    expect(text).toContain("need for pallet move");
    expect(text).toContain("help with unload inbound trailers");
    expect(text).toContain("robots with indoor navigation skills");
    expect(text).toContain("capabilities of 500 lb payload");
    expect(text).toContain("May I send them to you for review?");
    expect(text).not.toMatch(/SIGNAL|RaaS|match%/i);
  });

  it("leaves skill blanks and keeps ALLCAPS insert tokens", () => {
    const blank = composeEmployerNeedIntro({
      contactName: "Priya Shah",
      announcedNeed: "Pallet move",
    });
    expect(blank).toContain(`robots with ${OEM_INTRO_BLANK} skills`);
    expect(blank).toContain(`capabilities of ${OEM_INTRO_BLANK}`);
    const caps = composeEmployerNeedIntro({
      contactName: "Priya Shah",
      announcedNeed: "AMR Pallet Move",
      capabilities: "AMR 500 lb payload",
    });
    expect(caps).toContain("need for AMR pallet move");
    expect(caps).toContain("capabilities of AMR 500 lb payload");
  });
});
