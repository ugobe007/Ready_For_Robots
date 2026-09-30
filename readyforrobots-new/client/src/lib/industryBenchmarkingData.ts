export type BenchmarkRobotSpec = {
  vendor: string;
  model: string;
  category: "cobot" | "amr" | "scara" | "6-axis" | "service" | "cleaning" | "harvest";
  payload: string;
  battery_runtime: string;
  speed: string;
  navigation: string;
  price_range: string;
  est_monthly_raas: string;
  payback_months: number;
  safety_rating: "A+" | "A" | "A-";
  best_for: string;
};

export type IndustryBenchmarkDataset = {
  id: string;
  title: string;
  subtitle: string;
  target_accounts: string[];
  labor_vacancy_rate: string;
  avg_strain_reduction: string;
  avg_payback_months: number;
  overview: string;
  platforms: BenchmarkRobotSpec[];
  site_checklist: string[];
};

export const INDUSTRY_BENCHMARKS: Record<string, IndustryBenchmarkDataset> = {
  hospitality: {
    id: "hospitality",
    title: "Hospitality & Foodservice Automation Benchmark",
    subtitle: "Comparative analysis of commercial service robots, dining busing AMRs, and room-service delivery units.",
    target_accounts: [
      "Thompson Hospitality",
      "Aimbridge Hospitality",
      "HEI Hotels & Resorts",
      "White Lodging",
    ],
    labor_vacancy_rate: "42% - 47%",
    avg_strain_reduction: "35% - 40%",
    avg_payback_months: 8.5,
    overview:
      "Acute front-line labor shortages in hotel housekeeping and foodservice dining busing are driving hospitality operators toward autonomous delivery and tray-conveyance platforms. Key buying criteria include elevator integration, quiet operation, and obstacle avoidance in crowded dining rooms.",
    platforms: [
      {
        vendor: "Bear Robotics",
        model: "Servi Plus",
        category: "service",
        payload: "40 kg (4 trays)",
        battery_runtime: "12 hours",
        speed: "1.2 m/s",
        navigation: "LiDAR + 3D Camera",
        price_range: "$18,000 - $24,000",
        est_monthly_raas: "$750 / mo",
        payback_months: 7,
        safety_rating: "A+",
        best_for: "High-volume dining busing & beverage transport",
      },
      {
        vendor: "Richtech Robotics",
        model: "Matradee L",
        category: "service",
        payload: "40 kg",
        battery_runtime: "10 hours",
        speed: "1.0 m/s",
        navigation: "Visual SLAM + LiDAR",
        price_range: "$16,500 - $22,000",
        est_monthly_raas: "$690 / mo",
        payback_months: 8,
        safety_rating: "A",
        best_for: "Multi-floor room delivery & dining room runner",
      },
      {
        vendor: "Pudu Robotics",
        model: "BellaBot Pro",
        category: "service",
        payload: "40 kg",
        battery_runtime: "13 hours",
        speed: "1.2 m/s",
        navigation: "Dual LiDAR + RGBD",
        price_range: "$15,000 - $20,000",
        est_monthly_raas: "$650 / mo",
        payback_months: 7.5,
        safety_rating: "A",
        best_for: "Interactive guest dining & tray delivery",
      },
      {
        vendor: "Relay Robotics",
        model: "Relay+ Elevator Transport",
        category: "service",
        payload: "25 kg (locked bin)",
        battery_runtime: "8 hours",
        speed: "0.9 m/s",
        navigation: "Elevator-Integrated Wi-Fi Mesh",
        price_range: "$22,000 - $28,000",
        est_monthly_raas: "$890 / mo",
        payback_months: 10,
        safety_rating: "A+",
        best_for: "Autonomous multi-floor hotel room delivery",
      },
    ],
    site_checklist: [
      "Wi-Fi mesh coverage in hallways and dining areas",
      "Elevator relay interface (Relay API or dry-contact module)",
      "Threshold transitions under 0.5 inches",
      "Dedicated charging dock area with 110V 15A power access",
    ],
  },

  logistics: {
    id: "logistics",
    title: "Surface Freight & Warehouse Logistics Benchmark",
    subtitle: "Evaluation of autonomous forklifts, parcel sortation AMRs, and case-picking workcells.",
    target_accounts: ["FedEx Ground", "Ryder System"],
    labor_vacancy_rate: "38% - 44%",
    avg_strain_reduction: "40% - 45%",
    avg_payback_months: 11.2,
    overview:
      "High-throughput logistics hubs require heavy-payload AMRs and automated palletizing to handle seasonal package volume spikes. Autonomous forklifts and pallet movers reduce pallet staging delays and dock-to-conveyor cycle times.",
    platforms: [
      {
        vendor: "Mobile Industrial Robots (MiR)",
        model: "MiR1350 Heavy AMR",
        category: "amr",
        payload: "1350 kg",
        battery_runtime: "10 hours (fast charge)",
        speed: "1.5 m/s",
        navigation: "360° LiDAR + 3D Cameras",
        price_range: "$65,000 - $85,000",
        est_monthly_raas: "$1,850 / mo",
        payback_months: 11,
        safety_rating: "A+",
        best_for: "Heavy pallet transport & warehouse intralogistics",
      },
      {
        vendor: "Seegrid",
        model: "Palion Lift Autonomous Forklift",
        category: "amr",
        payload: "1590 kg",
        battery_runtime: "12 hours",
        speed: "1.8 m/s",
        navigation: "Vision-Guided 3D Perception",
        price_range: "$95,000 - $125,000",
        est_monthly_raas: "$2,600 / mo",
        payback_months: 12.5,
        safety_rating: "A+",
        best_for: "High-bay pallet staging & trailer loading",
      },
      {
        vendor: "OTTO Motors (Rockwell)",
        model: "OTTO 1500",
        category: "amr",
        payload: "1500 kg",
        battery_runtime: "9 hours",
        speed: "2.0 m/s",
        navigation: "Safety LiDAR + Fleet Manager",
        price_range: "$70,000 - $90,000",
        est_monthly_raas: "$1,950 / mo",
        payback_months: 10.5,
        safety_rating: "A+",
        best_for: "High-speed warehouse conveyor feeds",
      },
      {
        vendor: "Universal Robots",
        model: "UR30 Palletizing Cobot",
        category: "cobot",
        payload: "30 kg",
        battery_runtime: "Continuous (AC power)",
        speed: "2.0 m/s arm speed",
        navigation: "Fixed Cell + Safety Scanners",
        price_range: "$55,000 - $72,000",
        est_monthly_raas: "$1,550 / mo",
        payback_months: 9,
        safety_rating: "A+",
        best_for: "End-of-line heavy case palletizing",
      },
    ],
    site_checklist: [
      "Floor flatness rating Ff 35 / Fl 25 minimum for high-speed AMRs",
      "Industrial Wi-Fi 6 or Private 5G LTE network",
      "Auto-charging 480V / 208V 3-phase station access",
      "WMS/WCS API integration (SAP, Manhattan, Blue Yonder)",
    ],
  },

  facilities: {
    id: "facilities",
    title: "Facility Services & Commercial Cleaning Benchmark",
    subtitle: "Comparative guide to industrial autonomous floor scrubbers, vacuum AMRs, and trash transport units.",
    target_accounts: [
      "ABM Industries",
      "Harvard Maintenance",
      "Diversified Maintenance Systems",
    ],
    labor_vacancy_rate: "45% - 52%",
    avg_strain_reduction: "42% - 48%",
    avg_payback_months: 9.8,
    overview:
      "Janitorial and facility support contractors leverage autonomous floor scrubbers to cover large square footage during off-hours, mitigating chronic night-shift vacancy rates while maintaining floor cleanliness compliance.",
    platforms: [
      {
        vendor: "Avidbots",
        model: "Neo 2.0 Commercial Scrubber",
        category: "cleaning",
        payload: "135L clean water tank",
        battery_runtime: "6 hours",
        speed: "1.3 m/s",
        navigation: "Multi-Sensor LiDAR + Sonar",
        price_range: "$48,000 - $62,000",
        est_monthly_raas: "$1,350 / mo",
        payback_months: 9.5,
        safety_rating: "A+",
        best_for: "Airport terminals, convention centers & large retail",
      },
      {
        vendor: "Tennant / Brain Corp",
        model: "T16AMR Industrial Scrubber",
        category: "cleaning",
        payload: "189L water capacity",
        battery_runtime: "4 hours",
        speed: "1.2 m/s",
        navigation: "BrainOS Autonomous Navigation",
        price_range: "$58,000 - $75,000",
        est_monthly_raas: "$1,600 / mo",
        payback_months: 10.5,
        safety_rating: "A+",
        best_for: "Industrial logistics floors & manufacturing plants",
      },
      {
        vendor: "SoftBank Robotics",
        model: "Whiz Vacuum AMR",
        category: "cleaning",
        payload: "5L dust bag",
        battery_runtime: "3 hours per battery",
        speed: "0.5 m/s",
        navigation: "BrainOS Commercial Vision",
        price_range: "$9,500 - $14,000",
        est_monthly_raas: "$490 / mo",
        payback_months: 8,
        safety_rating: "A",
        best_for: "Carpeted hallways & corporate office suites",
      },
    ],
    site_checklist: [
      "Water drainage and clean water refill station access",
      "Dedicated overnight charging bay",
      "Elevator access for multi-floor commercial towers",
      "Off-peak janitorial schedule coordination",
    ],
  },

  healthcare: {
    id: "healthcare",
    title: "Healthcare & Clinical Logistics Automation Benchmark",
    subtitle: "Analysis of hospital delivery AMRs, pharmacy transport units, and senior living support robots.",
    target_accounts: [
      "HCA Healthcare",
      "Sunrise Senior Living",
      "Trilogy Health",
      "Life Care Communities",
      "Erickson Senior Living",
    ],
    labor_vacancy_rate: "40% - 48%",
    avg_strain_reduction: "35% - 42%",
    avg_payback_months: 10.0,
    overview:
      "Hospitals and senior living facilities utilize specialized clinical logistics AMRs to transport pharmacy items, lab specimens, and heavy laundry, freeing nurses and care aides to focus on direct patient care.",
    platforms: [
      {
        vendor: "Aethon",
        model: "TUG Smart AMR",
        category: "amr",
        payload: "450 kg",
        battery_runtime: "10 hours",
        speed: "1.0 m/s",
        navigation: "Built-in Map + Wi-Fi Elevator Control",
        price_range: "$45,000 - $60,000",
        est_monthly_raas: "$1,450 / mo",
        payback_months: 10,
        safety_rating: "A+",
        best_for: "Hospital pharmacy, specimen & meal cart delivery",
      },
      {
        vendor: "Swisslog Healthcare",
        model: "RelayMed Specimen AMR",
        category: "amr",
        payload: "35 kg (secure biometrics)",
        battery_runtime: "8 hours",
        speed: "0.8 m/s",
        navigation: "Secure RFID/Pin + Optical SLAM",
        price_range: "$28,000 - $38,000",
        est_monthly_raas: "$950 / mo",
        payback_months: 9.5,
        safety_rating: "A+",
        best_for: "STAT lab specimen & controlled sub-pharmacy transport",
      },
      {
        vendor: "Mobile Industrial Robots (MiR)",
        model: "MiR250 Health Cart Carrier",
        category: "amr",
        payload: "250 kg",
        battery_runtime: "13 hours",
        speed: "2.0 m/s",
        navigation: "Laser Scanners + 3D Cameras",
        price_range: "$35,000 - $48,000",
        est_monthly_raas: "$1,150 / mo",
        payback_months: 9,
        safety_rating: "A+",
        best_for: "Senior living linen, trash & dietary cart conveyance",
      },
    ],
    site_checklist: [
      "HIPAA-compliant biometric / badge reader access on lockboxes",
      "Automatic door openers and elevator relay modules",
      "Antimicrobial wipeable surface construction",
      "Quiet mode acoustic dampening under 50 dB",
    ],
  },

  gaming: {
    id: "gaming",
    title: "Gaming & Casino Resort Service Automation Benchmark",
    subtitle: "Evaluation of casino floor beverage runners, busing AMRs, and automated kitchen workcells.",
    target_accounts: ["MGM Resorts International", "Penn Entertainment"],
    labor_vacancy_rate: "35% - 42%",
    avg_strain_reduction: "30% - 38%",
    avg_payback_months: 8.0,
    overview:
      "Casino resorts face severe beverage server and dining room buser shortages on gaming floors. Service robots assist server staff by bringing fresh drinks directly to slot/table zones, increasing gaming floor dwell time and revenue.",
    platforms: [
      {
        vendor: "Bear Robotics",
        model: "Servi Lounge Runner",
        category: "service",
        payload: "35 kg",
        battery_runtime: "12 hours",
        speed: "1.2 m/s",
        navigation: "3D LiDAR + Dynamic Crowd Avoidance",
        price_range: "$17,500 - $23,000",
        est_monthly_raas: "$720 / mo",
        payback_months: 7.5,
        safety_rating: "A+",
        best_for: "Casino floor beverage distribution & tray return",
      },
      {
        vendor: "Richtech Robotics",
        model: "ADAM Robotic Bartender & Barista",
        category: "cobot",
        payload: "Dual 6-axis arms",
        battery_runtime: "Continuous AC",
        speed: "High precision dispensing",
        navigation: "Fixed Bar Kiosk",
        price_range: "$85,000 - $110,000",
        est_monthly_raas: "$2,800 / mo",
        payback_months: 9.5,
        safety_rating: "A+",
        best_for: "Automated high-volume casino bar & coffee service",
      },
    ],
    site_checklist: [
      "High-density crowd navigation tuning",
      "Low-light optical sensor calibration for casino ambiance",
      "Spill-resistant tray surfaces with lip guards",
      "Casino POS system integration (Micros, Simphony)",
    ],
  },

  aviation: {
    id: "aviation",
    title: "Aviation Ground Operations & Airport Cargo Benchmark",
    subtitle: "Analysis of autonomous baggage tractors, air cargo palletizers, and ramp logistics AMRs.",
    target_accounts: ["United Airlines"],
    labor_vacancy_rate: "36% - 41%",
    avg_strain_reduction: "38% - 44%",
    avg_payback_months: 13.0,
    overview:
      "Airport ramp operations and cargo facilities demand heavy-payload AMRs and automated palletizing to handle tight flight turnaround windows and heavy baggage sorting.",
    platforms: [
      {
        vendor: "Tug / Textron Ground Support",
        model: "Tug SmartTract Autonomous Towing",
        category: "amr",
        payload: "4,500 kg tow capacity",
        battery_runtime: "10 hours",
        speed: "3.5 m/s",
        navigation: "Outdoor GPS + 3D LiDAR",
        price_range: "$110,000 - $145,000",
        est_monthly_raas: "$3,200 / mo",
        payback_months: 13.5,
        safety_rating: "A+",
        best_for: "Outdoor baggage cart towing & ramp logistics",
      },
      {
        vendor: "FANUC Robotics",
        model: "M-900iB Cargo Palletizer",
        category: "6-axis",
        payload: "700 kg",
        battery_runtime: "Continuous AC",
        speed: "2.2 m/s arm speed",
        navigation: "Fixed Workcell + iRVision",
        price_range: "$120,000 - $160,000",
        est_monthly_raas: "$3,500 / mo",
        payback_months: 12,
        safety_rating: "A+",
        best_for: "Air freight ULD container loading & palletizing",
      },
    ],
    site_checklist: [
      "Weatherproof IP65/IP67 enclosure rating for ramp exposure",
      "Outdoor GPS / DGPS + 3D LiDAR localization",
      "Integration with airport ramp safety management systems",
      "High-voltage fast charging infrastructure",
    ],
  },

  agriculture: {
    id: "agriculture",
    title: "Agricultural Harvesting & AI Berry Pickers Benchmark",
    subtitle: "Comparative guide to autonomous berry harvesters, field AMRs, and sorting vision systems.",
    target_accounts: ["Wish Farms (Tampa Bay AG)"],
    labor_vacancy_rate: "48% - 55%",
    avg_strain_reduction: "45% - 50%",
    avg_payback_months: 14.0,
    overview:
      "Berry and delicate fruit growers deploy vision-guided soft robotic harvesters and field transport AMRs to mitigate severe seasonal labor shortages while preserving crop quality.",
    platforms: [
      {
        vendor: "Advanced Farm Technologies",
        model: "Rubion Berry Harvester",
        category: "harvest",
        payload: "4 autonomous picking arms",
        battery_runtime: "16 hours (hybrid diesel/electric)",
        speed: "0.8 m/s field traverse",
        navigation: "3D Stereo Vision + RTK GPS",
        price_range: "$175,000 - $225,000",
        est_monthly_raas: "$4,500 / mo",
        payback_months: 14,
        safety_rating: "A",
        best_for: "Strawberry & blueberry field harvesting",
      },
      {
        vendor: "Burro",
        model: "Burro Grand Field AMR",
        category: "amr",
        payload: "900 kg",
        battery_runtime: "12 hours",
        speed: "2.2 m/s",
        navigation: "AI Vision-Guided Path Tracking",
        price_range: "$22,000 - $30,000",
        est_monthly_raas: "$850 / mo",
        payback_months: 8.5,
        safety_rating: "A+",
        best_for: "Field-to-cooler lug conveyance & picker follow mode",
      },
    ],
    site_checklist: [
      "Row spacing and canopy height compliance",
      "RTK GPS base station for sub-inch field localization",
      "Dust and moisture IP66 rated electronics",
      "Cold-chain lug transfer interface",
    ],
  },
};

export function getBenchmarkForIndustry(industryId: string): IndustryBenchmarkDataset {
  const normalized = (industryId || "").toLowerCase().trim();
  if (normalized.includes("hospitality") || normalized.includes("hotel") || normalized.includes("food")) {
    return INDUSTRY_BENCHMARKS.hospitality;
  }
  if (normalized.includes("logistics") || normalized.includes("freight") || normalized.includes("warehouse")) {
    return INDUSTRY_BENCHMARKS.logistics;
  }
  if (normalized.includes("facilities") || normalized.includes("cleaning") || normalized.includes("janitorial")) {
    return INDUSTRY_BENCHMARKS.facilities;
  }
  if (
    normalized.includes("health") ||
    normalized.includes("medical") ||
    normalized.includes("senior") ||
    normalized.includes("clinical")
  ) {
    return INDUSTRY_BENCHMARKS.healthcare;
  }
  if (normalized.includes("gaming") || normalized.includes("casino") || normalized.includes("resort")) {
    return INDUSTRY_BENCHMARKS.gaming;
  }
  if (normalized.includes("aviation") || normalized.includes("airline") || normalized.includes("airport")) {
    return INDUSTRY_BENCHMARKS.aviation;
  }
  if (normalized.includes("ag") || normalized.includes("farm") || normalized.includes("berry")) {
    return INDUSTRY_BENCHMARKS.agriculture;
  }
  return INDUSTRY_BENCHMARKS.hospitality;
}
