import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, { buildBobExecutiveEmail } from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds warm greeting & thesis executive email with Bob's Panasonic authority", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robotics feasibility at FedEx Ground?");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("Hope you’re having a great week.");
    expect(email.body).toContain("getting from an impressive demonstration to a repeatable, scalable deployment in real facility environments is much harder than vendors acknowledge");
    expect(email.body).toContain("Having spent my career in robotics—leading teams at Panasonic and building 3 robot companies");
    expect(email.body).toContain("Either way, I’d be curious to hear how your team is thinking about robotics feasibility");
  });
});
