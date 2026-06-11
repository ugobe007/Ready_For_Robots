type IndustryCategory =
  | "hospitality"
  | "healthcare"
  | "logistics"
  | "airport"
  | "manufacturing"
  | "food_service"
  | "general";

const HOSPITALITY_TERMS = [
  "casino",
  "casinos",
  "gaming",
  "hotel",
  "hotels",
  "hospitality",
  "lodging",
  "motel",
  "motels",
  "resort",
  "resorts",
];

const HEALTHCARE_TERMS = [
  "clinic",
  "clinics",
  "health care",
  "health system",
  "health systems",
  "healthcare",
  "hospital",
  "hospitals",
  "medical",
];

function normalizedIndustryTokens(industry?: string | null): Set<string> {
  const value = (industry || "").toLowerCase();
  const normalized = value.replace(/&/g, " and ").replace(/[^a-z0-9]+/g, " ").trim();
  const words = normalized ? normalized.split(/\s+/) : [];
  const tokens = new Set(words);
  for (let i = 0; i < words.length - 1; i += 1) {
    tokens.add(`${words[i]} ${words[i + 1]}`);
  }
  return tokens;
}

export function industryCategory(industry?: string | null): IndustryCategory {
  const tokens = normalizedIndustryTokens(industry);

  // Important: hospitality is not healthcare. Never test "hospital" by substring,
  // because "hospitality" starts with the same letters.
  if (HOSPITALITY_TERMS.some((term) => tokens.has(term))) return "hospitality";
  if (HEALTHCARE_TERMS.some((term) => tokens.has(term))) return "healthcare";
  if (["logistics", "warehouse", "warehousing", "fulfillment", "distribution", "3pl"].some((term) => tokens.has(term))) {
    return "logistics";
  }
  if (["airport", "airports", "aviation"].some((term) => tokens.has(term))) return "airport";
  if (["manufacturing", "manufacturer", "automotive", "factory"].some((term) => tokens.has(term))) {
    return "manufacturing";
  }
  if (
    [
      "restaurant", "restaurants", "qsr", "food service", "foodservice", "food",
      "food prep", "food preparation", "food delivery", "food robot", "kitchen",
      "kitchen robot", "ghost kitchen", "dark kitchen", "catering", "cafeteria",
      "fast food", "fast casual", "dining",
    ].some((term) => tokens.has(term))
  ) {
    return "food_service";
  }
  return "general";
}

export function marketInsightForIndustry(industry?: string | null): string {
  switch (industryCategory(industry)) {
    case "hospitality":
      return "Hotels and casino resorts are pairing off-hours cleaning robots with daytime service robots to protect guest experience while labor stays tight.";
    case "healthcare":
      return "Healthcare systems are showing more interest in off-hours cleaning, internal delivery, and logistics support where robots reduce staff walking time.";
    case "logistics":
      return "Logistics hubs are moving fastest where expansion, throughput pressure, and labor availability overlap.";
    case "airport":
      return "Airports are watching service, cleaning, and terminal-support robots around peak passenger windows and night-shift operations.";
    case "manufacturing":
      return "Manufacturers are treating robotics as targeted relief for quality, safety, and material-flow bottlenecks rather than broad replacement.";
    default:
      return "SIGNAL is watching for accounts where signal timing suggests a real sales motion, not just a generic news headline.";
  }
}

export function outreachInsightForIndustry(industry?: string | null): string {
  switch (industryCategory(industry)) {
    case "hospitality":
      return "I have noticed hotels and casino resorts using cleaning robots for off-hours floor care, while service robots handle daytime delivery, amenities, and back-of-house runs that pull staff away from guests.";
    case "healthcare":
      return "I have noticed healthcare systems separating off-hours support work from daytime patient-facing service: cleaning robots can cover overnight corridors and public spaces, while delivery or service robots help move supplies during peak clinical hours.";
    case "logistics":
      return "I have noticed logistics hubs are pairing AMRs, autonomous cleaning, and material-handling automation so overnight floor readiness and daytime throughput can improve without adding more temporary labor.";
    case "airport":
      return "I have noticed airports are using autonomous cleaning and delivery robots around off-peak passenger windows, then shifting service robots into daytime terminal, concession, and baggage-adjacent support workflows.";
    case "manufacturing":
      return "I have noticed manufacturers are using mobile robots and inspection automation around shift changes, quality bottlenecks, and material movement rather than treating robotics as a single all-or-nothing plant project.";
    case "food_service":
      return "I have noticed restaurants and food-service operators are using robots in narrow operating windows: cleaning after close, prep or runner support during rush periods, and back-of-house automation where labor pressure is highest.";
    default:
      return "I have noticed operators are moving toward practical robotics deployments that start with narrow, high-friction workflows: off-hours cleaning, repetitive transport, service delivery, and support tasks that free staff for higher-value work.";
  }
}
