export interface BuyerQuote {
  id: string;
  author: string;
  title: string;
  company: string;
  industry: string;
  avatarUrl?: string;
  quote: string;
  targetRobotTypes: string[];
  timeline: string;
  verified: boolean;
  date: string;
  matchedJobKey?: string;
}

export const FEATURED_BUYER_QUOTES: BuyerQuote[] = [
  {
    id: "quote-cloudkitchens",
    author: "Justin Futterman",
    title: "Director of Operations",
    company: "CloudKitchens",
    industry: "Ghost Kitchens & QSR",
    quote:
      "Scaling order fulfillment across our kitchen network requires automated meal portioning and prep cobots that can handle peak rush volumes without constant human intervention.",
    targetRobotTypes: ["Meal Assembly Cobots", "Kitchen Prep Manipulators"],
    timeline: "Active Evaluation",
    verified: true,
    date: "Today",
  },
  {
    id: "quote-fedex",
    author: "David Perillat",
    title: "Regional Operations Director",
    company: "FedEx Ground",
    industry: "Logistics & Surface Freight",
    quote:
      "Peak season package volumes and heavy pallet staging in regional hubs demand autonomous forklifts and sortation AMRs that integrate directly into our dock workflows.",
    targetRobotTypes: ["Autonomous Forklifts", "Parcel Sortation AMRs"],
    timeline: "Immediate Procurement",
    verified: true,
    date: "Today",
  },
  {
    id: "quote-ryder",
    author: "Neal Medeiros",
    title: "Director of Customer Logistics",
    company: "Ryder System",
    industry: "3PL & Warehousing",
    quote:
      "Dock-to-stock cycle times are our primary KPI. We are actively evaluating heavy-payload AMRs and case-picking cobots for dedicated fulfillment centers across North America.",
    targetRobotTypes: ["Heavy Pallet AMRs", "Case-Picking Cobots"],
    timeline: "0–3 Months Deployment",
    verified: true,
    date: "Yesterday",
  },
  {
    id: "quote-thompson",
    author: "Zandrique Harrold",
    title: "Vice President of Operations",
    company: "Thompson Hospitality",
    industry: "Hospitality & Corporate Dining",
    quote:
      "High labor turnover in corporate dining halls is driving us to automate tray busing and floor maintenance so our staff can focus 100% on hospitality and guest service.",
    targetRobotTypes: ["Tray Delivery Cobots", "Service AMRs"],
    timeline: "Active RFP",
    verified: true,
    date: "Yesterday",
  },
  {
    id: "quote-chipotle",
    author: "Michael Thoms",
    title: "Vice President of Operations",
    company: "Chipotle",
    industry: "Fast Casual & Food Prep",
    quote:
      "Kitchen prep labor bottlenecks are where we see immediate automation ROI. We're evaluating produce prep manipulators and portioning units to increase store kitchen throughput.",
    targetRobotTypes: ["Produce Prep Manipulators", "Automated Portioning Units"],
    timeline: "3–6 Months Pilot",
    verified: true,
    date: "2 days ago",
  },
  {
    id: "quote-abm",
    author: "Ralph Sica",
    title: "Vice President of Operations",
    company: "ABM Industries",
    industry: "Facility Services & Janitorial",
    quote:
      "Commercial janitorial staffing deficits across airport terminals and large enterprise facilities make autonomous floor scrubbers essential for maintaining off-peak cleaning compliance.",
    targetRobotTypes: ["Commercial Cleaning AMRs", "Vacuuming Cobots"],
    timeline: "Active Evaluation",
    verified: true,
    date: "3 days ago",
  },
  {
    id: "quote-wonder",
    author: "Deniz Uzel",
    title: "Vice President of Operations",
    company: "Wonder Group",
    industry: "Multi-Brand Food Delivery",
    quote:
      "Scaling multi-brand meal assembly across suburban hub kitchens requires high-precision mobile manipulators that can switch between diverse menu SKUs smoothly.",
    targetRobotTypes: ["Multi-Step Assembly AMRs", "Automated Cooking Stations"],
    timeline: "0–3 Months",
    verified: true,
    date: "3 days ago",
  },
];
