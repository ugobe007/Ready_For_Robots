import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("explore page", () => {
  it("links the four research doors and loads brief rows from the edition API", () => {
    const page = readFileSync(join(here, "../pages/Explore.tsx"), "utf8");
    const app = readFileSync(join(here, "../App.tsx"), "utf8");
    expect(app).toMatch(/path="\/explore" component=\{Explore\}/);
    expect(page).toMatch(/\/api\/newsletter\/edition/);
    expect(page).toMatch(/\/api\/newsletter\/subscribe/);
    expect(page).toMatch(/href: "\/robot-ready"/);
    expect(page).toMatch(/href: "\/newsletter"/);
    expect(page).toMatch(/href: "\/roi-calculator"/);
    expect(page).toMatch(/href: "\/reports\/benchmarking"/);
    expect(page).not.toMatch(/\[COUNT|County hospital|\$1B|EXAMPLE/);
  });
});
