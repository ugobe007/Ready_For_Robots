import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CLASS_OPTION_IDS,
  DEFAULT_CLASS_OPTIONS,
  classOptionsOrDefault,
} from "./robotClassOptions";

const here = dirname(fileURLToPath(import.meta.url));

const EXPECTED_IDS = [
  "humanoid",
  "amr",
  "mobile_manipulator",
  "cobot",
  "quadruped",
  "autonomous_scrubber",
  "agriculture",
  "marine",
  "avionics",
  "aerospace",
  "construction",
] as const;

describe("robot class picker options", () => {
  it("renders all 11 classes with a one-line work hint", () => {
    expect(DEFAULT_CLASS_OPTIONS).toHaveLength(11);
    expect(CLASS_OPTION_IDS).toEqual([...EXPECTED_IDS]);
    for (const row of DEFAULT_CLASS_OPTIONS) {
      expect(row.label.trim().length).toBeGreaterThan(2);
      expect(row.hint.trim().length).toBeGreaterThan(8);
    }
  });

  it("keeps the original six form-factor tiles", () => {
    expect(CLASS_OPTION_IDS.slice(0, 6)).toEqual([
      "humanoid",
      "amr",
      "mobile_manipulator",
      "cobot",
      "quadruped",
      "autonomous_scrubber",
    ]);
  });

  it("names the four domain tiles plus aerospace the form-factor list misses", () => {
    const byId = Object.fromEntries(DEFAULT_CLASS_OPTIONS.map(row => [row.id, row]));
    expect(byId.agriculture.label).toBe("Agriculture");
    expect(byId.agriculture.hint).toMatch(/combine|tractor/i);
    expect(byId.marine.label).toBe("Marine");
    expect(byId.marine.hint).toMatch(/hull|port|underwater/i);
    expect(byId.avionics.label).toBe("Avionics");
    expect(byId.avionics.hint).toMatch(/drone|evtol|aircraft/i);
    expect(byId.avionics.hint).not.toMatch(/hangar and airside only/i);
    expect(byId.aerospace.label).toBe("Aerospace");
    expect(byId.aerospace.hint).toMatch(/satellite|debris|rocket/i);
    expect(byId.construction.label).toBe("Construction");
    expect(byId.construction.hint).toMatch(/home|building/i);
  });

  it("falls back to the eleven tiles when the API sends none", () => {
    expect(classOptionsOrDefault(undefined)).toHaveLength(11);
    expect(classOptionsOrDefault([])).toEqual(DEFAULT_CLASS_OPTIONS);
    expect(classOptionsOrDefault([{ id: "agriculture", label: "Ag", hint: "Field" }])).toEqual([
      { id: "agriculture", label: "Ag", hint: "Field" },
    ]);
  });

  it("wires the picker and workspace fallback to the same 11 ids", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    expect(workspace).toMatch(/classOptionsOrDefault/);
    expect(workspace).toMatch(/Name the robot class/);
    for (const id of EXPECTED_IDS) {
      expect(workspace + DEFAULT_CLASS_OPTIONS.map(r => r.id).join(" ")).toContain(id);
    }
  });
});
