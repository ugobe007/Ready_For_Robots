import { describe, expect, it } from "vitest";
import { buildBobExecutiveEmail } from "./executiveEmailGenerator";

describe("executiveEmailGenerator", () => {
  it("generates the universal sales email template for any lead", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robotics task matching for FedEx Ground?");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("Nice to meet you.");
    expect(email.body).toContain("We help enterprise operators evaluate commercial robotics—matching specific robot models to your exact job requirements");
    expect(email.body).toContain("Having spent my career in robotics—leading teams at Panasonic, RichTech Robotics, and Anybots—I founded ReadyForRobots");
    expect(email.body).toContain("Either way, I’d be curious to hear how your team is thinking about robotics across your facilities right now.");
  });

  it("handles possessive grammar for company names ending in s", () => {
    const email = buildBobExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
    });

    expect(email.body).toContain("CloudKitchens’ growth");
  });
});
