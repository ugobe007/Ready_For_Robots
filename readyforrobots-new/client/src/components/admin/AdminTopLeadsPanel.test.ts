import { describe, expect, it } from "vitest";
import AdminTopLeadsPanel, { buildBobExecutiveEmail } from "./AdminTopLeadsPanel";

describe("AdminTopLeadsPanel component module", () => {
  it("exports AdminTopLeadsPanel as a valid React component function", () => {
    expect(typeof AdminTopLeadsPanel).toBe("function");
  });

  it("builds modern peer benchmark executive email with Bob's Panasonic authority", () => {
    const email = buildBobExecutiveEmail({
      companyName: "FedEx Ground",
      dmName: "David Perillat",
      robotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    });

    expect(email.subject).toBe("Robotics Feasibility & Benchmark Report for FedEx Ground");
    expect(email.body).toContain("Dear David,");
    expect(email.body).toContain("I’m reaching out because enterprise operators across your sector are actively deploying Autonomous Forklifts and Parcel Sortation AMRs");
    expect(email.body).toContain("Having led robotics at Panasonic and built 3 commercial robot companies");
    expect(email.body).toContain("1.1 to 1.4 years");
    expect(email.body).toContain("customized 2-page benchmark report specifically tailored to FedEx Ground's operational footprint");
  });
});
