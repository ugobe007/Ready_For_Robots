import { describe, expect, it } from "vitest";
import { buildBobExecutiveEmail } from "./executiveEmailGenerator";

describe("executiveEmailGenerator", () => {
  it("generates the executive sales email template for any lead", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Engineering task feasibility & robotics evaluation for FedEx Ground");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("My name is Bob Christopher, President of ReadyForRobots.");
    expect(email.body).toContain("independent engineering evaluations, 3D feasibility simulations, and turnkey commercial quotes");
    expect(email.body).not.toContain("SIGNAL");
    expect(email.body).not.toContain("Cal");
    expect(email.body).not.toContain("FIND");
  });

  it("handles possessive grammar for company names ending in s", () => {
    const email = buildBobExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
    });

    expect(email.body).toContain("CloudKitchens’ facilities");
  });
});
