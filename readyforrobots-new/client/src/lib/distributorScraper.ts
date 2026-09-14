export type DistributorScrapeResult = {
  distributor_name: string;
  domain: string;
  detected_brands: string[];
  detected_categories: string[];
  services: string[];
  product_mix: Array<{
    brand: string;
    category: string;
    description: string;
  }>;
  confidence: number;
};

const KNOWN_OEM_BRANDS: Array<{ canonical: string; matchers: string[] }> = [
  { canonical: "Universal Robots", matchers: ["universal robots", "ur10e", "ur20", "ur3e", "ur5e"] },
  { canonical: "FANUC", matchers: ["fanuc"] },
  { canonical: "ABB", matchers: ["abb", "yumi", "gofa", "swifti"] },
  { canonical: "KUKA", matchers: ["kuka"] },
  { canonical: "Yaskawa Motoman", matchers: ["yaskawa", "motoman"] },
  { canonical: "Epson Robots", matchers: ["epson", "epson robots"] },
  { canonical: "Mobile Industrial Robots (MiR)", matchers: ["mobile industrial robots", "mir", "mir250", "mir600", "mir1350"] },
  { canonical: "Omron", matchers: ["omron", "hd-1500", "ld-90"] },
  { canonical: "Denso Robotics", matchers: ["denso"] },
  { canonical: "Yamaha Robotics", matchers: ["yamaha"] },
  { canonical: "Kawasaki Robotics", matchers: ["kawasaki"] },
  { canonical: "Doosan Robotics", matchers: ["doosan"] },
  { canonical: "Staubli", matchers: ["staubli", "stäubli"] },
  { canonical: "Festo", matchers: ["festo"] },
  { canonical: "Robotiq", matchers: ["robotiq", "2f-85", "airpick"] },
  { canonical: "OnRobot", matchers: ["onrobot"] },
  { canonical: "Cognex", matchers: ["cognex"] },
  { canonical: "Keyence", matchers: ["keyence"] },
];

const CATEGORY_REGEX_MAP: Record<string, RegExp> = {
  cobot: /\b(cobot|collaborative robot|collaborative arm|ur\d+e?|doosan|gofa)\b/i,
  amr: /\b(amr|autonomous mobile robot|intralogistics|agv|automated guided vehicle|mir\d+|ld-90)\b/i,
  scara: /\b(scara|selective compliance|epson t-series|yk-xg|rh-series)\b/i,
  "6-axis": /\b(6-axis|six-axis|articulated arm|m-20ib|lr mate|irb \d+)\b/i,
  gripper: /\b(gripper|end-effector|eoat|vacuum tool|airpick|2f-85)\b/i,
  vision: /\b(machine vision|cognex|keyence|vision guided|inspection system)\b/i,
};

const SERVICE_REGEX_MAP: Record<string, RegExp> = {
  "Systems Integration": /\b(system integration|integrator|turnkey automation|custom workcell)\b/i,
  "Safety Audits & Risk Assessment": /\b(machine safety|safety audit|risk assessment|iso 10218)\b/i,
  "PLC & Motion Control": /\b(plc programming|motion control|hmi|allen-bradley|siemens)\b/i,
  "Proof-of-Concept Lab": /\b(proof of concept|poc lab|demo lab|testing facility)\b/i,
};

export function scrapeDistributorPage(
  url: string,
  pageText: string
): DistributorScrapeResult {
  const text = pageText.toLowerCase();
  
  let domain = "";
  try {
    const u = new URL(url.includes("://") ? url : `https://${url}`);
    domain = u.hostname.replace(/^www\./, "");
  } catch {
    domain = url.replace(/^www\./, "").split("/")[0];
  }

  // Extract distributor name from domain or page title hint
  const domainTitle = domain.split(".")[0];
  const capitalized = domainTitle.charAt(0).toUpperCase() + domainTitle.slice(1);
  const distributorName = `${capitalized} Automation & Robotics`;

  // Detect Brands
  const detectedBrands: string[] = [];
  for (const item of KNOWN_OEM_BRANDS) {
    if (item.matchers.some(m => text.includes(m))) {
      detectedBrands.push(item.canonical);
    }
  }

  // Detect Categories
  const detectedCategories: string[] = [];
  for (const [cat, regex] of Object.entries(CATEGORY_REGEX_MAP)) {
    if (regex.test(text)) {
      detectedCategories.push(cat);
    }
  }

  // Detect Services
  const services: string[] = [];
  for (const [service, regex] of Object.entries(SERVICE_REGEX_MAP)) {
    if (regex.test(text)) {
      services.push(service);
    }
  }

  // Build product mix
  const productMix: Array<{ brand: string; category: string; description: string }> = [];
  for (const brand of detectedBrands) {
    for (const cat of detectedCategories) {
      productMix.push({
        brand,
        category: cat,
        description: `Distributed ${brand} ${cat.toUpperCase()} lineup for manufacturing & warehousing automation.`,
      });
    }
  }

  const confidence = Math.min(
    1.0,
    (detectedBrands.length * 0.3) + (detectedCategories.length * 0.2) + (services.length * 0.1)
  );

  return {
    distributor_name: distributorName,
    domain,
    detected_brands: detectedBrands,
    detected_categories: detectedCategories,
    services,
    product_mix: productMix,
    confidence: Number(confidence.toFixed(2)),
  };
}
