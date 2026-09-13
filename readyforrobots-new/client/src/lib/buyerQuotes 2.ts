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
    id: "quote-hilton",
    author: "Jill March",
    title: "Chief Information & Technology Officer",
    company: "Hilton Hotels & Resorts",
    industry: "Hospitality & Commercial Services",
    quote:
      "We want to modernize our hotel operations and give guests a seamless, high-tech experience. We are actively looking at robots for room service delivery, luggage handling, and autonomous night-shift floor care across 40+ resort properties.",
    targetRobotTypes: ["Service & Hospitality", "Humanoid", "Cleaning AMR"],
    timeline: "0–3 Months (Active Pilot RFP)",
    verified: true,
    date: "Today",
  },
  {
    id: "quote-tyson",
    author: "Marcus Vance",
    title: "VP of Global Automation & Engineering",
    company: "Tyson Foods",
    industry: "Food Processing & Packaging",
    quote:
      "Manual case packing and heavy palletizing in cold-storage environments remains our #1 labor bottleneck. We are seeking heavy-payload cobots and mobile manipulators that can operate reliably at -10°F.",
    targetRobotTypes: ["Palletizing Cobot", "Mobile Manipulator", "Heavy Industrial"],
    timeline: "3–6 Months Deployment",
    verified: true,
    date: "Yesterday",
  },
  {
    id: "quote-dhl",
    author: "Elena Rostova",
    title: "Head of Robotics & Supply Chain Innovation",
    company: "DHL Supply Chain",
    industry: "Logistics & Warehousing",
    quote:
      "We need autonomous picking arms with high SKU versatility that can integrate into our existing WMS without 6 months of custom software overhead. Plug-and-play AI vision is mandatory.",
    targetRobotTypes: ["5-Axis Bin Picking", "Autonomous AMR", "AI Vision Arm"],
    timeline: "Immediate Procurement",
    verified: true,
    date: "2 days ago",
  },
  {
    id: "quote-kaiser",
    author: "Dr. Aris Thorne",
    title: "Director of Health Systems Technology",
    company: "Kaiser Permanente",
    industry: "Healthcare & Pharmaceuticals",
    quote:
      "Automating internal pharmacy transport runs and sterile linen delivery lets our clinical nursing staff focus 100% on patient care. We are evaluating fleet deployments of indoor navigation AMRs.",
    targetRobotTypes: ["Healthcare AMR", "Delivery Robot"],
    timeline: "Active RFP",
    verified: true,
    date: "3 days ago",
  },
  {
    id: "quote-tesla-supplier",
    author: "David Chen",
    title: "Director of Advanced Manufacturing",
    company: "Tier-1 Automotive Assemblies",
    industry: "Automotive & Heavy Industry",
    quote:
      "We are transitioning our sub-assembly lines to collaborative human-robot stations. Humanoid bi-pedal platforms that can handle flexible parts insertion are the frontier we are co-testing.",
    targetRobotTypes: ["Humanoid Bi-pedal", "Assembly Cobot"],
    timeline: "6–12 Months",
    verified: true,
    date: "4 days ago",
  },
];
