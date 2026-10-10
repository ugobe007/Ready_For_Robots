import { describe, expect, it } from "vitest";
import {
  authEmailRejectReason,
  normalizeAuthEmail,
  otpNoAccountMessage,
} from "./authEmail";

describe("authEmail", () => {
  it("accepts ordinary work emails including plus tags", () => {
    expect(normalizeAuthEmail("Ops@AcmeRobotics.COM")).toBe(
      "ops@acmerobotics.com"
    );
    expect(authEmailRejectReason("ops+jobs@acmerobotics.com")).toBeNull();
  });

  it("rejects empty, malformed, and reserved test domains", () => {
    expect(authEmailRejectReason("")).toMatch(/work email/i);
    expect(authEmailRejectReason("not-an-email")).toMatch(/full email/i);
    expect(authEmailRejectReason("ops@acme")).toMatch(/valid email/i);
    expect(authEmailRejectReason("user@example.com")).toMatch(
      /real work email/i
    );
    expect(authEmailRejectReason("dev@foo.test")).toMatch(
      /real company email/i
    );
  });

  it("rejects disposable inboxes that bounce on Supabase Auth", () => {
    expect(authEmailRejectReason("x@mailinator.com")).toMatch(/Disposable/i);
    expect(authEmailRejectReason("x@yopmail.com")).toMatch(/Disposable/i);
  });

  it("maps login OTP misses to a signup prompt instead of a raw GoTrue error", () => {
    expect(otpNoAccountMessage("Signups not allowed for otp")).toMatch(
      /signup page/i
    );
    expect(otpNoAccountMessage("Network error")).toBe("Network error");
  });
});
