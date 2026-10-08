import { describe, expect, it } from "vitest";
import {
  OEM_INTRO_BLANK,
  OEM_INTRO_PAY_BLANK,
  OEM_INTRO_TERM_BLANK,
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
    expect(text).toContain("Pharmacy delivery at Rochester Regional Health in Rochester, NY");
    expect(text).toContain("$4200 per month for 12 months");
    expect(text).toContain("arrange a call with Priya at Rochester Regional Health");
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
    expect(text).toContain(`$${OEM_INTRO_PAY_BLANK} per month for ${OEM_INTRO_TERM_BLANK}`);
    expect(text).toContain("arrange a call with GEODIS");
    expect(text).not.toContain("operations@");
    expect(text).not.toContain("Operational Lead");
  });
});
