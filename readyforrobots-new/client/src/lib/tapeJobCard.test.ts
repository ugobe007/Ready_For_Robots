import { describe, expect, it } from "vitest";
import { tapeJobCardHref } from "./tapeJobCard";

describe("tapeJobCardHref", () => {
  it("opens a home-board card on /?job=", () => {
    expect(tapeJobCardHref("/", "", "crow-burlingame")).toBe(
      "/?job=crow-burlingame"
    );
  });

  it("keeps FIND on /?visit=jobs when a tape row opens", () => {
    expect(tapeJobCardHref("/", "?visit=jobs", "crow-burlingame")).toBe(
      "/?visit=jobs&job=crow-burlingame"
    );
  });

  it("closes back to the page that opened the card", () => {
    expect(tapeJobCardHref("/", "?visit=jobs&job=crow-burlingame", null)).toBe(
      "/?visit=jobs"
    );
    expect(tapeJobCardHref("/", "?job=crow-burlingame", null)).toBe("/");
  });
});
