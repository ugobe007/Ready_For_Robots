import { describe, expect, it } from "vitest";
import { scrapeDistributorPage } from "./distributorScraper";

describe("distributorScraper page parser & mix extractor", () => {
  it("scrapes distributor page HTML and detects brands, categories, and services", () => {
    const sampleHtml = `
      <html>
        <head><title>Fastech Automation & Robotics Solutions</title></head>
        <body>
          <h1>Leading Midwest Industrial Robotics Integrator</h1>
          <p>We provide turnkey automation systems for manufacturing facilities.</p>
          <h2>Our Partner Brands</h2>
          <ul>
            <li>FANUC Industrial 6-Axis Arms & Palletizers</li>
            <li>Universal Robots UR10e & UR20 Collaborative Cobots</li>
            <li>Mobile Industrial Robots (MiR250 AMRs)</li>
            <li>Epson SCARA Precision Pick and Place</li>
            <li>Cognex Machine Vision Inspection Systems</li>
          </ul>
          <h2>Engineering Services</h2>
          <p>System Integration, PLC Programming, Machine Safety Audits, and Proof-of-Concept testing.</p>
        </body>
      </html>
    `;

    const result = scrapeDistributorPage("https://www.fastechautomation.com", sampleHtml);
    expect(result.domain).toBe("fastechautomation.com");
    expect(result.detected_brands).toContain("FANUC");
    expect(result.detected_brands).toContain("Universal Robots");
    expect(result.detected_brands).toContain("Epson Robots");
    expect(result.detected_brands).toContain("Cognex");
    expect(result.detected_categories).toContain("cobot");
    expect(result.detected_categories).toContain("amr");
    expect(result.detected_categories).toContain("scara");
    expect(result.detected_categories).toContain("6-axis");
    expect(result.services).toContain("Systems Integration");
    expect(result.services).toContain("PLC & Motion Control");
    expect(result.confidence).toBeGreaterThan(0.5);
    expect(result.product_mix.length).toBeGreaterThan(0);
  });

  it("scrapes modern commercial & humanoid distributor page (AlphaRobotics)", () => {
    const sampleHtml = `
      <html>
        <head><title>AlphaRobotics | Autonomous Mobile Robots & Humanoid Marketplace</title></head>
        <body>
          <h1>AlphaRobotics Commercial & Service Fleet Marketplace</h1>
          <p>US distributor for AGIBOT A2 & A3 humanoid robots, PUDU BellaBot Pro delivery robots, Gausium Phantas floor scrubbers, CenoBot L50, and Tennant X2 Rover.</p>
          <p>We provide robot rental, fleet deployment, leasing, and after-sales maintenance support.</p>
        </body>
      </html>
    `;

    const result = scrapeDistributorPage("https://alpharoboticsai.com/marketplace", sampleHtml);
    expect(result.domain).toBe("alpharoboticsai.com");
    expect(result.detected_brands).toContain("AgiBot");
    expect(result.detected_brands).toContain("PUDU Robotics");
    expect(result.detected_brands).toContain("Gausium");
    expect(result.detected_brands).toContain("CenoBot");
    expect(result.detected_brands).toContain("Tennant");
    expect(result.detected_categories).toContain("humanoid");
    expect(result.detected_categories).toContain("delivery");
    expect(result.detected_categories).toContain("cleaning");
    expect(result.services).toContain("Fleet Deployment & Maintenance");
    expect(result.confidence).toBeGreaterThan(0.6);
  });
});
