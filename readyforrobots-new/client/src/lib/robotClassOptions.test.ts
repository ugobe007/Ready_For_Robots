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
    expect(workspace).toMatch(/CLASS_PICKER_PROMPT/);
    expect(workspace).not.toMatch(/What kind of robot is/);
    expect(workspace).not.toMatch(/kid of robot/i);
    expect(workspace).toMatch(/Finding jobs for that robot type/);
    for (const id of EXPECTED_IDS) {
      expect(workspace + DEFAULT_CLASS_OPTIONS.map(r => r.id).join(" ")).toContain(id);
    }
  });

  it("class-picker click starts robot-job-search and cannot silently no-op", () => {
    const workspace = readFileSync(
      join(here, "../components/RobotJobsWorkspace.tsx"),
      "utf8",
    );
    const qualify = workspace.slice(
      workspace.indexOf("async function qualifyActive"),
      workspace.indexOf("function revealJobs"),
    );
    expect(qualify).toMatch(/fetchRobotJobSearch/);
    expect(qualify).toMatch(/assertedClass: chosen/);
    expect(qualify).toMatch(/qualifySearchLookupGrain/);
    expect(qualify).toMatch(/lookupGrain: grain/);
    expect(qualify).toMatch(/needsClassChoice: false/);
    expect(qualify).not.toMatch(/if \(!a\) return/);
    expect(qualify).not.toMatch(/lookupGrain: "product"/);
    expect(qualify).not.toMatch(/prior\.jobs/);
    expect(qualify).toMatch(/searchToAnalysis\(res\)/);
    expect(workspace).toMatch(/beginJobsHandoffForUrl/);
    expect(workspace).toMatch(/Finding jobs for that robot type/);
    expect(workspace).toMatch(/shouldShowClassPicker/);
    expect(workspace).toMatch(/classJobsEmptyCopy/);
    expect(workspace).toMatch(/data-jobs-class/);
    const goActivate = workspace.slice(
      workspace.indexOf("function goToActivate"),
      workspace.indexOf("async function persistKeptJobs"),
    );
    expect(goActivate).toMatch(/shouldShowClassPicker\(active\)/);
  });
});
