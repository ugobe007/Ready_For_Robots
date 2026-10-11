import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, {
  buildPhelanExecutiveEmail,
} from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds warm greeting & thesis executive email with Phelan's placement credentials", () => {
    const email = buildPhelanExecutiveEmail({
      companyName: "CloudKitchens",
      dmName: "Justin Futterman",
      robotTypes: ["Meal Assembly Cobots", "Kitchen Prep Manipulators"],
    });

    expect(email.subject).toBe(
      "Robot job matches & feasibility review for CloudKitchens"
    );
    expect(email.body).toContain("Hi Justin,");
    expect(email.body).toContain(
      "I’m Phelan, a Robot Coordinator at ReadyForRobots."
    );
    expect(email.body).toContain("Robot Coordinator | ReadyForRobots");
  });
});
