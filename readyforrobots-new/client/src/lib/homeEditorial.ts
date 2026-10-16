import type { Tier } from "@/components/editorial";

export { SignalRow as ReasonRow } from "@/components/editorial";

export type HomeReason = {
  tier: Tier;
  title: string;
  source: string;
};

export type HomeCase = {
  name: string;
  maker: string;
  form: string;
  work: string;
  buyers: string;
  never: string;
  buyer: string;
  buyerMeta: string;
  reasons: HomeReason[];
};

export type HomeProduct = {
  id: string;
  name: string;
  short: string;
  what: string;
  form: string;
  work: string;
  buyers: string;
  never: string;
  url: string;
};

export const HOME_CASES: HomeCase[] = [
  {
    name: "ADAM",
    maker: "Richtech Robotics",
    form: "Stationary dual-arm station",
    work: "Coffee and cocktail making and serving",
    buyers: "Restaurants and bars, hotels, casinos",
    never: "Bussing, room service, food running. It doesn’t move.",
    buyer: "Resort and casino group",
    buyerMeta: "Las Vegas, NV · Drink-making, open",
    reasons: [
      { tier: "A", title: "RFP for automated beverage stations", source: "Example · procurement" },
      { tier: "B", title: "Budget approved to modernize bar service", source: "Example · earnings call" },
      { tier: "D", title: "New resort tower opening next year", source: "Example · press release" },
    ],
  },
  {
    name: "Relay",
    maker: "Relay Robotics",
    form: "Mobile, secure compartment",
    work: "Delivery of medications, lab samples, linens",
    buyers: "Hospitals, hotels",
    never: "Kitchen or bar work, floor cleaning.",
    buyer: "Multi-hospital health system",
    buyerMeta: "Midwest · Delivery, open",
    reasons: [
      { tier: "A", title: "RFP for autonomous delivery robots in a medical center", source: "Example · federal notice" },
      { tier: "C", title: "Hiring a robotics program manager", source: "Example · buyer job post" },
      { tier: "E", title: "Nurses losing hours to non-clinical runs", source: "Example · industry report" },
    ],
  },
  {
    name: "Locus Origin",
    maker: "Locus Robotics",
    form: "Mobile robot",
    work: "Order picking and tote transport",
    buyers: "Warehouses, 3PLs, retail distribution",
    never: "Dining rooms, patient floors.",
    buyer: "Third-party logistics provider",
    buyerMeta: "Southeast · Picking, exploring",
    reasons: [
      { tier: "B", title: "“Automating our fulfillment centers”", source: "Example · annual report" },
      { tier: "D", title: "New fulfillment center opening", source: "Example · press release" },
      { tier: "E", title: "Peak-season picker shortages", source: "Example · news" },
    ],
  },
  {
    name: "Neo",
    maker: "Avidbots",
    form: "Mobile autonomous scrubber",
    work: "Floor cleaning",
    buyers: "Airports, retail, warehouses, facility services",
    never: "Drink-making, deliveries.",
    buyer: "Regional airport authority",
    buyerMeta: "West · Cleaning, open",
    reasons: [
      { tier: "A", title: "RFP for autonomous floor-cleaning equipment", source: "Example · procurement" },
      { tier: "D", title: "Terminal expansion under construction", source: "Example · press release" },
      { tier: "E", title: "Custodial staffing shortfall", source: "Example · board minutes" },
    ],
  },
  {
    name: "UR cobot",
    maker: "Universal Robots",
    form: "Fixed collaborative arm",
    work: "Machine tending and palletizing",
    buyers: "Factories, food manufacturing",
    never: "Mobile delivery, floor cleaning.",
    buyer: "Food and beverage manufacturer",
    buyerMeta: "Midwest · Palletizing, piloting",
    reasons: [
      { tier: "B", title: "“Streamline our production line”", source: "Example · earnings call" },
      { tier: "C", title: "Hiring an automation engineer for the plant", source: "Example · buyer job post" },
      { tier: "D", title: "New production line announced", source: "Example · press release" },
    ],
  },
];

export const HOME_PRODUCTS: HomeProduct[] = [
  {
    id: "adam",
    name: "ADAM",
    short: "Bartender and barista station",
    what: "Makes and serves cocktails, coffee and boba tea, and chats with guests.",
    form: "Stationary, two arms",
    work: "Drink-making and serving",
    buyers: "Restaurants and bars, hotels, casinos, stadiums",
    never: "Bussing, room service, food running",
    url: "https://richtechrobotics.com/solutions/adam",
  },
  {
    id: "scorpion",
    name: "Scorpion",
    short: "Compact bartender arm",
    what: "Measures and mixes cocktails, wine and coffee in a small footprint.",
    form: "Stationary, one arm",
    work: "Drink-making",
    buyers: "Bars, restaurants, event venues",
    never: "Anything that needs to move",
    url: "https://richtechrobotics.com/solutions/scorpion",
  },
  {
    id: "matradee",
    name: "Matradee Plus",
    short: "Restaurant server",
    what: "Hosts, buses, serves and greets, carrying food from kitchen to table on four trays.",
    form: "Mobile",
    work: "Serving and bussing",
    buyers: "Restaurants, hotels, senior living",
    never: "Warehouses, factories",
    url: "https://richtechrobotics.com/solutions/matradee-plus",
  },
  {
    id: "titan",
    name: "Titan",
    short: "Heavy parts delivery",
    what: "Carries heavy loads autonomously across warehouse floors and shop bays.",
    form: "Mobile",
    work: "Material delivery",
    buyers: "Warehouses, factories, auto dealership service bays",
    never: "Dining rooms, hospitals",
    url: "https://richtechrobotics.com/solutions/titan",
  },
  {
    id: "pallet",
    name: "Pallet Jack",
    short: "Autonomous pallet mover",
    what: "Moves pallets between storage, workflows and production lines.",
    form: "Mobile, forks",
    work: "Pallet transport",
    buyers: "Warehouses, distribution centers, factories",
    never: "Hotels, restaurants",
    url: "https://richtechrobotics.com/solutions/pallet-jack",
  },
  {
    id: "mx",
    name: "DUST-E MX",
    short: "Large scrubber-dryer",
    what: "Scrubs large, busy floors and picks up where it left off after refills.",
    form: "Mobile",
    work: "Floor cleaning",
    buyers: "Large facilities (inferred from cleaning)",
    never: "Kitchen or drink work",
    url: "https://richtechrobotics.com/solutions/dust-e-mx",
  },
  {
    id: "s",
    name: "DUST-E S",
    short: "Compact floor cleaner",
    what: "Sweeps, vacuums, scrubs and mops in one pass, sized for standard doorways.",
    form: "Mobile",
    work: "Floor cleaning",
    buyers: "Offices, hospitals, hotels, retail, restaurants, schools",
    never: "Kitchen or drink work",
    url: "https://richtechrobotics.com/solutions/dust-e-s",
  },
  {
    id: "dex",
    name: "Dex",
    short: "Industrial humanoid",
    what: "Two-armed humanoid for repetitive, precise factory and warehouse tasks.",
    form: "Humanoid, stationary or mobile",
    work: "Machine tending, picking",
    buyers: "Factories, warehouses",
    never: "Restaurants, hotels",
    url: "https://richtechrobotics.com/solutions/dex",
  },
];

export const HOME_TIERS = [
  { tier: "A" as const, name: "RFPs and awards", desc: "A published request for robots or automation. Budget is confirmed." },
  { tier: "B" as const, name: "Pilots and budgets", desc: "Announced pilots, budget lines, and plans to automate a workflow." },
  { tier: "C" as const, name: "Automation hiring", desc: "A buyer hiring robotics or automation roles, not a robot maker." },
  { tier: "D" as const, name: "Expansion", desc: "New buildings, properties, distribution centers, renovations." },
  { tier: "E" as const, name: "Labor pressure", desc: "Hard-to-fill work. Supports a card; never makes one alone." },
];

export const HOME_STEPS = [
  { n: "1", title: "Paste your product page", body: "We read it and classify your robot: what it is, the work it does, and the industries it serves." },
  { n: "2", title: "We find companies moving to automate", body: "RFPs, pilots and budgets, expansion plans, automation hiring, and other signs a company is about to automate that work." },
  { n: "3", title: "You see who’s ready to buy", body: "For each company: the work your robot would do there, the evidence they’re moving now (with links), and which of your robots fits best. If they already use robots for that work, we skip them." },
];

export const HOME_INDUSTRIES = [
  "Warehouse, logistics, 3PL",
  "Factories",
  "Hotels and casinos",
  "Hospitals",
  "Retail",
  "Restaurants and bars",
  "Airports",
  "Offices and facility services",
  "Auto dealerships",
];

export const HOME_EXPLORE = [
  { kind: "INDEX", title: "Robot index", body: "Humanoids and service robots compared on published specs.", cta: "Browse robots →", href: "/robots" },
  { kind: "WEEKLY", title: "The robot jobs brief", body: "Which companies are moving to automate, and which robots fit. One email a week.", cta: "Subscribe →", href: "/newsletter" },
  { kind: "TOOL", title: "RaaS ROI calculator", body: "Compare buying, leasing and robots-as-a-service for a workflow.", cta: "Run the numbers →", href: "/roi-calculator" },
  { kind: "REPORTS", title: "Industry reports", body: "Where automation is moving in each of our nine industries.", cta: "Read reports →", href: "/reports/benchmarking" },
];

export const CASE_ROTATE_MS = 6000;
