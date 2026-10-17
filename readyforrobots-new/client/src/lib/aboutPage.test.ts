import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("about page", () => {
  it("uses the section 7 copy, shared chrome, and no stat tiles", () => {
    const page = readFileSync(join(here, "../pages/About.tsx"), "utf8");
    expect(page).toMatch(/Robots need jobs\./);
    expect(page).toMatch(/We find the work\./);
    expect(page).toMatch(/SiteHeader/);
    expect(page).toMatch(/SiteFooter/);
    expect(page).not.toMatch(
      /Verified Buyer Leads|Robot Models|Active Open Trials|Daily Action Signals/
    );
  });

  it("sends /intelligence to the newsletter and keeps social and dev pages off production", () => {
    const app = readFileSync(join(here, "../App.tsx"), "utf8");
    const header = readFileSync(
      join(here, "../components/editorial/SiteHeader.tsx"),
      "utf8"
    );
    const publicHeader = readFileSync(
      join(here, "../components/Header.tsx"),
      "utf8"
    );
    const footer = readFileSync(
      join(here, "../components/layout/SiteFooter.tsx"),
      "utf8"
    );
    const editorialFooter = readFileSync(
      join(here, "../components/editorial/SiteFooter.tsx"),
      "utf8"
    );
    expect(app).toMatch(/path="\/about" component=\{About\}/);
    expect(app).toMatch(/path="\/desk" component=\{Desk\}/);
    expect(app).toMatch(/path="\/pipeline" component=\{DeskRedirect\}/);
    expect(app).toMatch(/function IntelligenceRedirect\(\) \{\s*return <Redirect to="\/newsletter" \/>;\s*\}/);
    expect(app).toMatch(/path="\/intelligence" component=\{IntelligenceRedirect\}/);
    expect(app).toMatch(/path="\/newsletter" component=\{Newsletter\}/);
    expect(app).not.toMatch(/component=\{Intelligence\}/);
    expect(footer).toMatch(/href: "\/intelligence"/);
    expect(editorialFooter).toMatch(/href: "\/newsletter"/);
    expect(publicHeader).toMatch(/href: "\/intelligence"/);
    expect(app).toMatch(/path="\/social" component=\{SocialRoute\}/);
    expect(app).toMatch(/import\.meta\.env\.DEV/);
    expect(header).toMatch(/\/branding\/rfr-icon-light\.svg/);
    expect(publicHeader).not.toMatch(/href="\/social"/);
  });
});
