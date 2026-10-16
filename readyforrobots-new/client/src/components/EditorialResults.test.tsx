import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { BuyerRows, NeedsReviewNotice } from "./EditorialResults";

const surveyBot = {
  robot_name: "Survey Bot",
  company_name: "Example Robotics",
  needs_review: true,
  robot_class: null,
  capabilities: [{ key: "general_purpose", label: "general purpose" }],
  jobs: [
    {
      title: "Deliver items to guest rooms",
      industry: "hotel",
      company_name: "Hotel operator",
      locality: "Austin",
      is_example: true,
    },
  ],
};

describe("FIND review label", () => {
  it("renders Needs review on the buyers screen for a needs_review product", () => {
    const html = renderToStaticMarkup(createElement(BuyerRows, { payload: surveyBot }));
    expect(html).toContain("Survey Bot");
    expect(html).toContain("Needs review. No class assigned.");
  });

  it("renders Needs review when the product has no class", () => {
    const html = renderToStaticMarkup(
      createElement(NeedsReviewNotice, { needsReview: true, robotClass: null })
    );
    expect(html).toContain("Needs review. No class assigned.");
  });

  it("stays off when a class is assigned", () => {
    const html = renderToStaticMarkup(
      createElement(NeedsReviewNotice, { needsReview: true, robotClass: "healthcare" })
    );
    expect(html).not.toContain("Needs review");
  });

  it("stays off when the product does not need review", () => {
    const html = renderToStaticMarkup(
      createElement(NeedsReviewNotice, { needsReview: false, robotClass: "" })
    );
    expect(html).not.toContain("Needs review");
  });
});
