import { describe, expect, it } from "vitest";
import { readableNewsletterHeadline } from "./newsletterHeadline";

describe("readableNewsletterHeadline", () => {
  it("joins a dangling verb fragment back onto the company", () => {
    expect(
      readableNewsletterHeadline(
        "Medline: to pilot warehouse automation platform from Symbotic...."
      )
    ).toBe("Medline to pilot warehouse automation platform from Symbotic");
  });

  it("keeps a real sentence and drops a repeated clause", () => {
    expect(
      readableNewsletterHeadline(
        "Amazon — unveils AI warehouse robot in Europe. Amazon unveils AI warehouse robot"
      )
    ).toBe("Amazon unveils AI warehouse robot in Europe");
  });

  it("falls back when the title is empty", () => {
    expect(readableNewsletterHeadline("")).toBe(
      "Who is buying robots this week"
    );
  });
});
