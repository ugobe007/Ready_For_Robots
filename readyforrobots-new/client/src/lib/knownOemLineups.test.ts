import { describe, expect, it } from "vitest";
import { hostFromOemUrl, lookupKnownOem } from "./knownOemLineups";

describe("knownOemLineups", () => {
  it("maps Reflex homepages to named robots without a network call", () => {
    expect(hostFromOemUrl("https://www.reflexrobotics.com/")).toBe(
      "reflexrobotics.com",
    );
    expect(hostFromOemUrl("reflexrobotics.com")).toBe("reflexrobotics.com");
    const hit = lookupKnownOem("https://www.reflexrobotics.com/");
    expect(hit?.vendor_name).toMatch(/Reflex/i);
    const names = hit?.robots.map(r => r.name) || [];
    expect(names.some(n => /Gen2|Gen 2/i.test(n))).toBe(true);
    expect(names.some(n => /Humanoid/i.test(n))).toBe(true);
    expect(names.length).toBeGreaterThan(0);
  });

  it("returns null for unknown hosts", () => {
    expect(lookupKnownOem("https://unknown-oem.example/")).toBeNull();
  });

  it("falls back from a product subdomain to the indexed registrable host", () => {
    const hit = lookupKnownOem("https://shop.reflexrobotics.com/products");
    expect(hit?.vendor_name).toMatch(/Reflex/i);
    expect((hit?.robots.length || 0)).toBeGreaterThan(0);
  });
});
