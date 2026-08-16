/**
 * Live job-tape corpus — real discoveries from RDD demos + content experiments.
 * Short titles / paths for the terminal board (not marketing cards).
 */
import {
  KARE_CART,
  KARE_GRIPPER,
  KARE_INSPECT,
  KARE_PALLET,
  KARE_SCRUB,
  KARE_TRANSPORT,
  type PixelMap,
} from "@/lib/kareIcons";

export type TapeFamily = "transport" | "cart" | "pallet" | "scrub" | "inspect" | "gripper";

export type TapeJob = {
  key: string;
  title: string;
  industry: string;
  path: string;
  family: TapeFamily;
};

export const TAPE_ICONS: Record<TapeFamily, PixelMap> = {
  transport: KARE_TRANSPORT,
  cart: KARE_CART,
  pallet: KARE_PALLET,
  scrub: KARE_SCRUB,
  inspect: KARE_INSPECT,
  gripper: KARE_GRIPPER,
};

/** Idle → one-frame “active” variants (few pixels change). */
export const TAPE_ICONS_ACTIVE: Record<TapeFamily, PixelMap> = {
  transport: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  cart: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  pallet: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  scrub: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  inspect: [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  ],
  gripper: KARE_GRIPPER,
};

/** Market tape — breadth of discovered robot work (25–40). */
export const MARKET_TAPE_JOBS: TapeJob[] = [
  {
    key: "curascript_totes",
    title: "Return empty totes",
    industry: "Specialty pharma",
    path: "PACK → OPERATING AREA",
    family: "transport",
  },
  {
    key: "aerospace_kits",
    title: "Deliver finished kits",
    industry: "Aerospace",
    path: "KITTING → PRODUCTION LINE",
    family: "transport",
  },
  {
    key: "hospital_med_carts",
    title: "Move medication carts",
    industry: "Healthcare",
    path: "PHARMACY → PATIENT UNITS",
    family: "cart",
  },
  {
    key: "novolex_cases",
    title: "Stack finished cases",
    industry: "Manufacturing",
    path: "CONVEYOR → PALLET",
    family: "pallet",
  },
  {
    key: "unifi_terminal",
    title: "Scrub terminal floors",
    industry: "Airport",
    path: "CONCOURSE · OVERNIGHT",
    family: "scrub",
  },
  {
    key: "par_carts",
    title: "Deliver par carts",
    industry: "Hospital",
    path: "SUPPLY → PATIENT FLOOR",
    family: "cart",
  },
  {
    key: "return_process_line",
    title: "Return empty totes",
    industry: "Manufacturing",
    path: "PROCESS LINE → SUPPLY",
    family: "transport",
  },
  {
    key: "sanmar_pick_carts",
    title: "Move pick carts",
    industry: "Apparel fulfillment",
    path: "PICK MODULE → PACK",
    family: "transport",
  },
  {
    key: "napa_orders",
    title: "Move completed orders",
    industry: "Auto parts DC",
    path: "PICK → SHIPPING",
    family: "cart",
  },
  {
    key: "intuitive_pou",
    title: "Deliver kits to point-of-use",
    industry: "Med device",
    path: "STORES → PRODUCTION",
    family: "transport",
  },
  {
    key: "replacement_parts_totes",
    title: "Move shipping totes",
    industry: "Auto parts",
    path: "ZONE → ZONE",
    family: "transport",
  },
  {
    key: "moa_scrub",
    title: "Scrub mall common areas",
    industry: "Retail",
    path: "CONCOURSE · OVERNIGHT",
    family: "scrub",
  },
  {
    key: "lbj_scrub",
    title: "Scrub hospital corridors",
    industry: "Healthcare",
    path: "EVS · NIGHT ROUTES",
    family: "scrub",
  },
  {
    key: "jhu_scrub",
    title: "Scrub campus floors",
    industry: "Education",
    path: "HARD FLOOR · RECURRING",
    family: "scrub",
  },
  {
    key: "industrial_scrub",
    title: "Scrub production floors",
    industry: "Industrial",
    path: "WAREHOUSE · PRODUCTION",
    family: "scrub",
  },
  {
    key: "cnc_load",
    title: "Load parts into CNC",
    industry: "Machine shop",
    path: "STAGING → SPINDLE",
    family: "gripper",
  },
  {
    key: "cnc_unload",
    title: "Unload finished parts",
    industry: "Machine shop",
    path: "SPINDLE → BIN",
    family: "gripper",
  },
  {
    key: "build_outbound",
    title: "Build outbound pallets",
    industry: "Fulfillment",
    path: "PACK → DOCK",
    family: "pallet",
  },
  {
    key: "inspect_gauges",
    title: "Inspect gauges",
    industry: "Industrial",
    path: "ROUTE → EQUIPMENT",
    family: "inspect",
  },
  {
    key: "inspect_electrical",
    title: "Inspect electrical equipment",
    industry: "Utilities",
    path: "PLANT → PANEL",
    family: "inspect",
  },
  {
    key: "plant_inspect",
    title: "Run plant inspection routes",
    industry: "Manufacturing",
    path: "RECURRING · FACILITY",
    family: "inspect",
  },
  {
    key: "staging_orders",
    title: "Move orders to staging",
    industry: "Fulfillment",
    path: "PACK → STAGING",
    family: "transport",
  },
  {
    key: "pack_mod_totes",
    title: "Move completed totes",
    industry: "Apparel",
    path: "PACK-MOD → PACKING",
    family: "transport",
  },
  {
    key: "fru_kits",
    title: "Move system carts",
    industry: "Med device",
    path: "KITTING → LINE",
    family: "cart",
  },
  {
    key: "case_wrap_pull",
    title: "Stack cases onto pallets",
    industry: "Packaging plant",
    path: "CASE → PALLET",
    family: "pallet",
  },
  {
    key: "hospital_supply",
    title: "Move supply carts",
    industry: "Hospital",
    path: "CENTRAL SUPPLY → UNITS",
    family: "cart",
  },
  {
    key: "food_court_scrub",
    title: "Scrub food-court floors",
    industry: "Retail",
    path: "HARD SURFACE · CLOSE",
    family: "scrub",
  },
  {
    key: "terminal_routes",
    title: "Scrub high-traffic routes",
    industry: "Airport",
    path: "TERMINAL · OVERNIGHT",
    family: "scrub",
  },
  {
    key: "gauge_rounds",
    title: "Inspect plant gauges",
    industry: "Process plant",
    path: "ROUND → READOUT",
    family: "inspect",
  },
  {
    key: "tote_return_dc",
    title: "Return totes to pack",
    industry: "Pharmacy DC",
    path: "SHIP → PACK",
    family: "transport",
  },
  {
    key: "kit_to_line",
    title: "Deliver kits to line",
    industry: "Aerospace",
    path: "KITTING → POINT OF USE",
    family: "transport",
  },
  {
    key: "pallet_wrap",
    title: "Build wrapped pallets",
    industry: "CPG",
    path: "LINE → WRAP",
    family: "pallet",
  },
];

export function demoJobsToTape(
  jobs: Array<{
    job_key: string;
    company_name: string;
    locality?: string | null;
    robot_compatible_task: string;
    action?: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    requirements?: Record<string, any>;
  }>,
  family: string,
): TapeJob[] {
  return jobs.map((j) => {
    const iface = j.requirements?.load_interface as string | undefined;
    let tapeFamily: TapeFamily = "transport";
    if (family === "floor_scrub") tapeFamily = "scrub";
    else if (iface === "cart") tapeFamily = "cart";
    else if (iface === "kit") tapeFamily = "transport";
    else if (j.action === "palletize" || /pallet|stack|case/i.test(j.robot_compatible_task)) {
      tapeFamily = "pallet";
    }

    const title = shortenTask(j.robot_compatible_task);
    const industry = (j.locality || j.company_name || "").split(",")[0] || j.company_name;
    const path = pathFromJob(j);

    return {
      key: j.job_key,
      title,
      industry,
      path,
      family: tapeFamily,
    };
  });
}

function shortenTask(task: string): string {
  const t = task.trim();
  if (t.length <= 36) return t;
  return `${t.slice(0, 33).trim()}…`;
}

function pathFromJob(j: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  requirements?: Record<string, any>;
}): string {
  const p = j.requirements?.path as string | undefined;
  if (p) return p.replace(/→/g, " → ").toUpperCase();
  return "WORKSITE → WORKSITE";
}
