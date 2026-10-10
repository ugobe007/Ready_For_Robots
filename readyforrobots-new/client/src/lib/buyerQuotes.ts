/**
 * Public employer quotes on `/`.
 *
 * How: landing copy lives here + CustomerQuoteBanner. FIND stays `/?visit=jobs`.
 * Matcher stays `POST /api/robot-job-match`. These quotes are not Job Cards and
 * not SIGNAL buyers — do not invent people, ROI, or `/pipeline?co=` hops.
 *
 * Each quote is a contiguous excerpt from a named 2024–2026 source.
 * opportunityHref is FIND (`/?visit=jobs`), not SIGNAL `/pipeline`.
 */

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
  matchedJobTitle: string;
  opportunityHref: string;
  location: string;
  heatTier: "HOT" | "WARM" | "HIGH MATCH";
  sourceUrl: string;
}

const FIND_JOBS = "/?visit=jobs";

export const FEATURED_BUYER_QUOTES: BuyerQuote[] = [
  {
    id: "quote-rochester-regional",
    author: "Casey Wilbert",
    title: "Chief Pharmacy Officer",
    company: "Rochester Regional Health",
    industry: "Healthcare & hospital pharmacy",
    quote:
      "Moxi has become an essential part of our operations, helping us grow our Meds-to-Beds programs, streamline lab workflows and deliver medications during critical off-hour shifts. Our staff and even our patients have embraced the robots and we're already planning where Moxi can go next.",
    targetRobotTypes: ["Hospital Transport AMRs"],
    timeline: "In operation about two years",
    verified: true,
    date: "Jul 2025",
    matchedJobTitle: "Hospital pharmacy last-mile medication delivery",
    opportunityHref: FIND_JOBS,
    location: "Rochester, NY",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://www.diligentrobots.com/blog/diligent-robotics-leads-us-adoption-of-hospital-pharmacy-robotics-redefines-the-last-mile",
  },
  {
    id: "quote-geodis",
    author: "Kevin Stock",
    title: "Executive Vice President of Engineering, Americas",
    company: "GEODIS",
    industry: "3PL warehousing",
    quote:
      "Warehouse automation brings incredible value to helping us navigate the challenge of managing increased volumes all year long, but especially during this demanding time of year. Throughout our relationship, we've seen Locus Robotics' powerful, AI-driven automation complement our teammates and dramatically increase productivity levels where deployed throughout our global operations.",
    targetRobotTypes: ["Goods-to-Person Mobile Robots"],
    timeline: "10 million units picked at Carlisle",
    verified: true,
    date: "Dec 2024",
    matchedJobTitle: "Warehouse piece-pick AMR",
    opportunityHref: FIND_JOBS,
    location: "Carlisle, PA",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://www.prnewswire.com/news-releases/locus-robotics-and-geodis-achieve-major-milestone-with-10-million-units-picked-at-us-distribution-site-302323257.html",
  },
  {
    id: "quote-dhl",
    author: "Sally Miller",
    title: "Chief Information Officer",
    company: "DHL Supply Chain",
    industry: "3PL warehousing",
    quote:
      "Locus Robotics has been a trusted partner in this effort and this milestone achievement underscores the improved productivity, accuracy, and employee ergonomics we've enjoyed across our global network.",
    targetRobotTypes: ["Goods-to-Person Mobile Robots"],
    timeline: "500 million picks with AMRs",
    verified: true,
    date: "Jun 2024",
    matchedJobTitle: "Fulfillment pick AMR",
    opportunityHref: FIND_JOBS,
    location: "Westerville, OH",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://group.dhl.com/en/media-relations/press-releases/2024/dhl-supply-chain-passes-unprecedented-500-million-picks-milestone-using-locus-robotics-autonomous-mobile-robots.html",
  },
  {
    id: "quote-chipotle",
    author: "Curt Garner",
    title: "Chief Customer and Technology Officer",
    company: "Chipotle",
    industry: "Fast casual food prep",
    quote:
      "These cobotic devices could help us build a stronger operational engine that delivers a great experience for our team members and our guests while maintaining Chipotle's high culinary standards.",
    targetRobotTypes: ["Meal Assembly Cobots", "Produce Prep Manipulators"],
    timeline: "In-restaurant test",
    verified: true,
    date: "Sep 2024",
    matchedJobTitle: "Restaurant bowl and salad makeline cobot",
    opportunityHref: FIND_JOBS,
    location: "Corona del Mar, CA",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://newsroom.chipotle.com/2024-09-16-CHIPOTLE-DEBUTS-AUTOCADO-AND-THE-AUGMENTED-MAKELINE-BY-HYPHEN-IN-RESTAURANTS",
  },
  {
    id: "quote-marriott",
    author: "Robert Guidice",
    title: "Chief Global Operations Officer",
    company: "Marriott International",
    industry: "Hospitality",
    quote:
      "By working together to develop and test new technologies and solutions, we aim to help hospitality associates work smarter and deliver innovations to market that will benefit the entire hospitality industry.",
    targetRobotTypes: ["Commercial Floor Care AMRs"],
    timeline: "Corridor and meeting-space vacuum pilots",
    verified: true,
    date: "Apr 2025",
    matchedJobTitle: "Hotel corridor and meeting-space floor care",
    opportunityHref: FIND_JOBS,
    location: "Bethesda, MD",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://www.lg.com/us/press-release/LG%20ROBOTIC%20VACUUM%20CLEANER_4.2.25_FINAL.pdf",
  },
  {
    id: "quote-brick",
    author: "Robert Rauch",
    title: "Chairman",
    company: "Brick Hospitality",
    industry: "Hospitality",
    quote:
      "When our night manager is on duty, we do not want to send him/her up into the corridors to deliver to guests. Relay does that 24/7, allowing our team to remain productive.",
    targetRobotTypes: ["Service AMRs"],
    timeline: "Guest deliveries at every property",
    verified: true,
    date: "2024",
    matchedJobTitle: "Hotel guest-room amenity delivery",
    opportunityHref: FIND_JOBS,
    location: "San Diego, CA",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://www.traveldailynews.com/hospitality/brick-hospitality-introduces-advanced-guest-service-robots-across-premier-hotels/",
  },
  {
    id: "quote-endeavor",
    author: "Elmer Dulce",
    title: "Director of Nursing, inpatient cardiac telemetry",
    company: "Endeavor Health",
    industry: "Healthcare & hospital nursing",
    quote:
      "If you think about that, where nurses wouldn't be able to put that time and energy, they can actually be at the bedside. And to date, it's about 103,000 deliveries made.",
    targetRobotTypes: ["Hospital Transport AMRs"],
    timeline: "In operation since 2022",
    verified: true,
    date: "2025",
    matchedJobTitle: "Hospital nursing supply and medication run",
    opportunityHref: FIND_JOBS,
    location: "Naperville, IL",
    heatTier: "HIGH MATCH",
    sourceUrl:
      "https://www.nctv17.org/news/moxi-robots-at-edward-hospital-save-nurses-over-100-million-steps/",
  },
];
