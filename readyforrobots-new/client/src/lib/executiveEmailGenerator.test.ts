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
    expect(email.body).toContain("We match robots to jobs—and jobs to robots.");
    expect(email.body).toContain("We’ve identified work within FedEx Ground that may be a good fit for robotic labor.");
    expect(email.body).toContain("For your **Autonomous Forklifts** job, we’ve identified a shortlist of qualified robot matches for your review.");
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

    expect(email.body).toContain("We’ve identified work within CloudKitchens that may be a good fit for robotic labor.");
    expect(email.body).toContain("For your **Meal Assembly** job");
  });
});
