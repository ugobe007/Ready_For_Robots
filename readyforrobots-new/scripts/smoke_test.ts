/**
 * Workflow & Link Integrity Smoke Test Suite for ReadyForRobots
 */
import fs from "fs";
import path from "path";
import { FEATURED_BUYER_QUOTES } from "../client/src/lib/buyerQuotes.js";

function runSmokeTests() {
  console.log("=========================================");
  console.log("🚀 READYFORROBOTS SMOKE TEST SUITE");
  console.log("=========================================\n");

  let totalPassed = 0;
  let totalFailed = 0;

  function assert(condition: boolean, testName: string, detail?: string) {
    if (condition) {
      console.log(` ✅ PASS: ${testName}`);
      totalPassed++;
    } else {
      console.error(` ❌ FAIL: ${testName} - ${detail || "Assertion failed"}`);
      totalFailed++;
    }
  }

  // 1. Data Integrity: Buyer Quotes
  console.log("--- 1. Testing Buyer Quotes Corpus ---");
  assert(
    FEATURED_BUYER_QUOTES.length >= 4,
    "Buyer quotes count >= 4",
    `Found ${FEATURED_BUYER_QUOTES.length}`
  );
  const hiltonQuote = FEATURED_BUYER_QUOTES.find((q) => q.company.includes("Hilton"));
  assert(
    Boolean(hiltonQuote && hiltonQuote.quote.includes("luggage")),
    "Hilton Hotels quote loaded correctly",
    "Hilton quote missing or incomplete"
  );

  // 2. Data Integrity: Known OEM Lineups
  console.log("\n--- 2. Testing Known OEM Lineups ---");
  const knownOemPath = path.resolve("./client/src/lib/knownOemLineups.json");
  assert(fs.existsSync(knownOemPath), "knownOemLineups.json exists");
  const oemData = JSON.parse(fs.readFileSync(knownOemPath, "utf-8"));
  assert(
    Boolean(oemData["kinetix.tech"]),
    "kinetix.tech present in OEM database",
    "kinetix.tech missing from knownOemLineups.json"
  );
  assert(
    Boolean(oemData["skild.ai"]),
    "skild.ai present in OEM database",
    "skild.ai missing from knownOemLineups.json"
  );

  // 3. Component Files Integrity
  console.log("\n--- 3. Testing Key Workflow Components ---");
  const componentPaths = [
    "./client/src/components/CustomerQuoteBanner.tsx",
    "./client/src/components/DailyMatchBriefModal.tsx",
    "./client/src/components/BlurredContactCard.tsx",
    "./client/src/pages/Pricing.tsx",
    "./client/src/pages/Robots.tsx",
    "./client/src/pages/Home.tsx",
  ];

  for (const compPath of componentPaths) {
    const fullPath = path.resolve(compPath);
    assert(
      fs.existsSync(fullPath),
      `Component file exists: ${path.basename(compPath)}`,
      `File not found: ${fullPath}`
    );
  }

  // 4. Route Integrity Check
  console.log("\n--- 4. Route & Link Integrity Verification ---");
  const appTsx = fs.readFileSync(path.resolve("./client/src/App.tsx"), "utf-8");
  const registeredRoutes = [
    "/",
    "/robots",
    "/find-robots",
    "/pricing",
    "/benchmark",
    "/pipeline",
    "/signals",
    "/compare",
    "/integrations",
    "/sales-console",
    "/crm",
  ];

  for (const route of registeredRoutes) {
    const routeRegex = new RegExp(`path=["']${route.replace(/\//g, "\\/")}["']`);
    assert(
      routeRegex.test(appTsx),
      `Route '${route}' is registered in App.tsx`,
      `Route ${route} not found in App.tsx`
    );
  }

  console.log("\n=========================================");
  console.log(`📊 SMOKE TEST SUMMARY: ${totalPassed} PASSED, ${totalFailed} FAILED`);
  console.log("=========================================\n");

  if (totalFailed > 0) {
    process.exit(1);
  }
}

runSmokeTests();
