/**
 * DEMO / QA ONLY — Origin & Neo fixture aliases for slug personalization tests.
 *
 * Production Find Jobs must NOT use this map as a gate.
 * Production path: scrape_robot_page → analyze_robot_capabilities → job corpus.
 */

export type EnvelopeMatch =
  | {
      status: "matched";
      profileKey: "locus_origin" | "avidbots_neo";
      family: string;
    }
  | { status: "unsupported"; reason: string; guessedFamily: string | null };

const TRANSPORT_HINTS = [
  "locus",
  "origin",
  "amr",
  "tote",
  "fetchrobotics",
  "fetch robotics",
  "geek+",
  "geekplus",
  "6river",
  "six river",
  "otto motors",
  "ottomotors",
  "mobile industrial robots",
  "mir.com",
  "warehouse robot",
];

const SCRUB_HINTS = [
  "avidbots",
  "neo",
  "scrub",
  "floor cleaning",
  "floor scrub",
  "autoscrub",
  "auto-scrub",
];

/** Families we recognize but do not yet have job fixtures for. */
const UNSUPPORTED_FAMILY_HINTS: { family: string; hints: string[] }[] = [
  {
    family: "inspection",
    hints: [
      "spot",
      "boston dynamics",
      "bostondynamics",
      "inspection",
      "thermograph",
    ],
  },
  {
    family: "cobot",
    hints: [
      "universal-robots",
      "universal robots",
      "ur10",
      "ur5",
      "cobot",
      "collaborative robot",
    ],
  },
  {
    family: "palletizer",
    hints: ["palletizer", "palletiser", "palletizing", "palletising"],
  },
  {
    family: "humanoid",
    hints: ["humanoid", "digit", "agilityrobotics", "figure.ai", "atlas"],
  },
  {
    family: "agriculture",
    hints: [
      "harvest",
      "strawberry",
      "agriculture",
      "orchard",
      "greenhouse robot",
    ],
  },
  {
    family: "delivery",
    hints: ["starship", "sidewalk", "last mile", "delivery robot"],
  },
  {
    family: "construction",
    hints: ["excavator", "construction robot", "built robotics", "bricklay"],
  },
  {
    family: "food_service",
    hints: ["flippy", "miso robotics", "kitchen robot", "food service robot"],
  },
  {
    family: "manipulator",
    hints: ["manipulator", "pick and place", "pick-and-place", "robot arm"],
  },
];

export function mapUrlToEnvelope(raw: string): EnvelopeMatch {
  const u = raw.toLowerCase();

  if (SCRUB_HINTS.some(h => u.includes(h))) {
    return {
      status: "matched",
      profileKey: "avidbots_neo",
      family: "floor_scrub",
    };
  }
  if (TRANSPORT_HINTS.some(h => u.includes(h))) {
    return {
      status: "matched",
      profileKey: "locus_origin",
      family: "transport_amr",
    };
  }

  for (const row of UNSUPPORTED_FAMILY_HINTS) {
    if (row.hints.some(h => u.includes(h))) {
      return {
        status: "unsupported",
        reason: `No job library yet for ${row.family.replace(/_/g, " ")} robots`,
        guessedFamily: row.family,
      };
    }
  }

  return {
    status: "unsupported",
    reason: "No matching job library for this robot yet",
    guessedFamily: null,
  };
}

/** QA matrix used before traffic — keep in sync with TRAFFIC_SPRINT.md */
export const QA_ROBOT_URLS: {
  kind: string;
  url: string;
  expect: "locus_origin" | "avidbots_neo" | "unsupported";
}[] = [
  {
    kind: "AMR",
    url: "https://locusrobotics.com/products/origin/",
    expect: "locus_origin",
  },
  {
    kind: "floor cleaning",
    url: "https://www.avidbots.com/neo",
    expect: "avidbots_neo",
  },
  {
    kind: "inspection",
    url: "https://bostondynamics.com/products/spot/",
    expect: "unsupported",
  },
  {
    kind: "cobot",
    url: "https://www.universal-robots.com/products/ur10e/",
    expect: "unsupported",
  },
  {
    kind: "palletizer",
    url: "https://www.abc-packaging.com/robotic-palletizer",
    expect: "unsupported",
  },
  {
    kind: "humanoid",
    url: "https://agilityrobotics.com/robots/digit",
    expect: "unsupported",
  },
  {
    kind: "agriculture",
    url: "https://www.advanced.farm/strawberry-harvester",
    expect: "unsupported",
  },
  {
    kind: "delivery",
    url: "https://www.starship.xyz/robot",
    expect: "unsupported",
  },
  {
    kind: "construction",
    url: "https://www.builtrobotics.com/excavator",
    expect: "unsupported",
  },
  {
    kind: "food service",
    url: "https://www.misorobotics.com/flippy",
    expect: "unsupported",
  },
];
