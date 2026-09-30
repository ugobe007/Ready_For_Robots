import { describe, expect, it } from "vitest";
import { buildPhelanExecutiveEmail } from "./executiveEmailGenerator";

describe("executiveEmailGenerator", () => {
  it("generates the executive sales email template for any lead", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robot job match & qualified labor review for FedEx Ground");
    expect(email.body).toContain("Hi David,");
    expect(email.body).toContain("I’m Phelan, a Robot Job Analyst at ReadyForRobots.");
    expect(email.body).toContain("We evaluate physical task requirements to match robots to operational jobs.");
    expect(email.body).toContain("We identified potential robotic labor fits within FedEx Ground");
    expect(email.body).toContain("Autonomous Forklifts");
    expect(email.body).toContain("phelan@readyforrobots.com");
    expect(email.body).not.toContain("Bob Christopher");
    expect(email.body).not.toContain("Cal");
  });

  it("handles company names cleanly in the email template", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
      taskType: "Meal Assembly",
    });

    expect(email.body).toContain("We identified potential robotic labor fits within CloudKitchens");
    expect(email.body).toContain("Meal Assembly");
  });
});
