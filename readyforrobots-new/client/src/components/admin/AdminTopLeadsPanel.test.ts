import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, { buildBobExecutiveEmail } from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds modern curious & inviting executive email with Bob's Panasonic authority", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Repeatable robotics deployment vs custom pilots at FedEx Ground");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("Right now, most enterprise operators have far more demand for robotics than vendors have proven, repeatable capability.");
    expect(email.body).toContain("Having led robotics at Panasonic and built 3 commercial robot companies");
    expect(email.body).toContain("How do you isolate the single, repeatable task at one facility that delivers measured ROI");
    expect(email.body).toContain("Are you open to taking a look at the brief, or comparing notes on where you see the biggest friction");
  });
});
