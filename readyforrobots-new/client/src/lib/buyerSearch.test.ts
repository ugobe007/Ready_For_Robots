import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buyerSearchView } from "./buyerSearch";
import { labeledSearchText, TAXONOMY_LABELS, taxonomySlugs } from "./taxonomyLabels";

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
    expect(page).toMatch(/taxonomyLabel\(/);
    expect(page).not.toMatch(/\{(?:product\.(?:form|display_class|description)|job\.industry)/);
  });

  it("renders results and picker text without taxonomy slugs", () => {
    const slugs = taxonomySlugs();
    expect(slugs.length).toBeGreaterThan(20);
    for (const slug of slugs) {
      expect(TAXONOMY_LABELS[slug], slug).toBeTruthy();
      expect(TAXONOMY_LABELS[slug]).not.toMatch(/[a-z]+_[a-z]+/);
    }
    expect(TAXONOMY_LABELS.food_prep).toBe("Food and drink prep");
    expect(TAXONOMY_LABELS.service_robot).toBe("Service robot");
    expect(TAXONOMY_LABELS.food_beverage_prep).toBe("Food and drink prep");

    const text = labeledSearchText({
      capabilities: slugs.map((slug) => ({ key: slug, label: slug })),
      jobs: [
        ...slugs.map((slug) => ({
          industry: slug,
          locality: "Seattle, WA",
          title: "Move goods across the floor",
          company_name: "Cafe operator",
        })),
        { industry: "Cafe", locality: "Seattle, WA", title: "Prepare drinks", company_name: "Cafe operator" },
      ],
      products: [
        ...slugs.map((slug) => ({
          name: "ADAM",
          display_class: slug,
          form: slug,
          description: slug,
        })),
        {
          name: "ADAM",
          display_class: "food_prep",
          description: "ADAM: Beverage and cocktail preparation. Restaurants · bars.",
        },
        { name: "Scorpion", display_class: "service_robot", description: "Richtech Scorpion service robot." },
        { name: "Unknown", display_class: "not_a_real_slug" },
      ],
    });
    expect(text).not.toMatch(/[a-z]+_[a-z]+/);
    expect(text).toContain("Food and drink prep");
    expect(text).toContain("Service robot");
    expect(text).toContain("Cafe");
    expect(text).not.toContain("not_a_real_slug");
  });
});
