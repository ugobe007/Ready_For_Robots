import { describe, expect, it } from "vitest";
import { buildPhelanExecutiveEmail } from "./executiveEmailGenerator";

describe("executiveEmailGenerator", () => {
  it("generates the executive sales email template for any lead", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robotic labor placement & task feasibility evaluation for FedEx Ground");
    expect(email.body).toContain("Hi David,");
    expect(email.body).toContain("I'm Phelan, AI Robotics Placement Specialist at ReadyForRobots.");
    expect(email.body).toContain("ReadyForRobots is recruitment and placement infrastructure for robotic labor.");
    expect(email.body).toContain("independent engineering task-feasibility evaluations, 3D cell simulations, and turnkey commercial proposals");
    expect(email.body).toContain("phelan@readyforrobots.com");
    expect(email.body).not.toContain("Bob Christopher");
    expect(email.body).not.toContain("Cal");
  });

  it("handles possessive grammar for company names ending in s", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
    });

    expect(email.body).toContain("CloudKitchens’ operations");
  });
});
