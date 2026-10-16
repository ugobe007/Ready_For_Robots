import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buyerSearchView } from "./buyerSearch";

const here = dirname(fileURLToPath(import.meta.url));

describe("buyer search screens", () => {
  it("maps the three robot-job-search payloads", () => {
    expect(buyerSearchView({ state: "matches", jobs: [] })).toBe("results");
    expect(buyerSearchView({ state: "thin_corpus", zero_reason: "corpus_gap" })).toBe("results");
    expect(buyerSearchView({ state: "select_product", needs_product_choice: true })).toBe("picker");
    expect(buyerSearchView({ state: "thin_corpus", zero_reason: "unrecognized_product" })).toBe(
      "unrecognized"
    );
  });

  it("results page keeps the search call and drops the old desk chrome", () => {
    const page = readFileSync(join(here, "../components/EditorialResults.tsx"), "utf8");
    expect(page).toMatch(/fetchRobotJobSearch/);
    expect(page).toMatch(/Save buyers/);
    expect(page).toMatch(/Try a product page/);
    expect(page).toMatch(/We found/);
    expect(page).toMatch(/ExampleBadge/);
    expect(page).not.toMatch(/Open CRM|Apply from the desk|How to use this feed|Create Free Account|SKU/);
    const home = readFileSync(join(here, "./homeEditorial.ts"), "utf8");
    expect(home).toMatch(/href: "\/reports\/benchmarking"/);
    expect(home).not.toMatch(/href: "\/robots\/report"/);
  });
});
