/**
 * FIND class picker tiles. Keep in sync with
 * `app.services.robot_class_qualify.CLASS_OPTIONS`.
 *
 * Form-factor tiles (humanoid, AMR, …) plus work-domain / platform classes
 * the morphology list misses (agriculture, marine, avionics, aerospace,
 * construction, healthcare, mining, warehouse, logistics, factory,
 * hospitality). Agriculture is a robot class, not a SIGNAL industry tag.
 * Healthcare = hospital / clinical assistant work (Moxi), not a torso → humanoid tile.
 * Hospitality = hotel guest delivery / housekeeping (a torso is not a humanoid tile).
 * Food prep = hotel / casino / airport / QSR kitchens (not hotel housekeeping).
 * Serving = table / drink / bussing (ADAM, Matradee, Servi) — not housekeeping.
 * Cleaning = floor / vacuum / restroom including data centers — not hospital EVS.
 * Warehouse / factory / logistics do not outrank a true humanoid.
 * Avionics = drones / eVTOL / autonomous aircraft. Aerospace = satellites /
 * rockets / orbital debris. Tractor implements are configurations, not a tile.
 */
import type { ClassOption } from "@/lib/robotJobMatch";

export const DEFAULT_CLASS_OPTIONS: ClassOption[] = [
  {
    id: "humanoid",
    label: "Humanoid",
    hint: "Two legs, arms and hands — NEO, Unitree G1, Walker, Digit",
  },
  {
    id: "amr",
    label: "AMR / mobile robot",
    hint: "Rolls on a base and moves materials or itself",
  },
  {
    id: "mobile_manipulator",
    label: "Mobile manipulator",
    hint: "Rolling base with an arm that picks or places",
  },
  {
    id: "cobot",
    label: "Collaborative arm",
    hint: "Stationary or cart-mounted arm beside a person",
  },
  {
    id: "quadruped",
    label: "Quadruped",
    hint: "Four legs — inspection, patrol, unstructured ground",
  },
  {
    id: "autonomous_scrubber",
    label: "Floor scrubber",
    hint: "Cleans floors on its own",
  },
  {
    id: "agriculture",
    label: "Agriculture",
    hint: "Combines, tractors, weeding — implements mount on a tractor",
  },
  {
    id: "marine",
    label: "Marine",
    hint: "Hull, port, and underwater work",
  },
  {
    id: "avionics",
    label: "Avionics",
    hint: "Drones, eVTOL flying cars, autonomous aircraft",
  },
  {
    id: "aerospace",
    label: "Aerospace",
    hint: "Satellites, rockets, orbital debris and space robots",
  },
  {
    id: "construction",
    label: "Construction",
    hint: "Homes and buildings — framing, print, jobsite finish",
  },
  {
    id: "healthcare",
    label: "Healthcare",
    hint: "Hospital and clinical work — delivery, pharmacy, linen, nursing assist",
  },
  {
    id: "mining",
    label: "Mining",
    hint: "Haulage, drilling, pit and underground work",
  },
  {
    id: "warehouse",
    label: "Warehouse",
    hint: "Fulfillment, totes, pick stations, distribution centers",
  },
  {
    id: "logistics",
    label: "Logistics",
    hint: "3PL, cross-dock, parcel sortation, inbound/outbound",
  },
  {
    id: "factory",
    label: "Factory",
    hint: "Plant floor — machine tend, CNC load/unload, assembly line",
  },
  {
    id: "hospitality",
    label: "Hospitality",
    hint: "Hotels — guest delivery, room service, housekeeping",
  },
  {
    id: "food_prep",
    label: "Food prep",
    hint: "Hotel, casino, airport, and QSR kitchens — make-line, grill, prep",
  },
  {
    id: "serving",
    label: "Serving",
    hint: "Table, drinks, bussing — ADAM, Matradee, Servi in restaurants, hotels, casinos, airports, offices, malls",
  },
  {
    id: "cleaning",
    label: "Cleaning",
    hint: "Floor, vacuum, restroom — hotels, restaurants, casinos, airports, offices, malls, data centers",
  },
];

export const CLASS_OPTION_IDS = DEFAULT_CLASS_OPTIONS.map(row => row.id);

export function classOptionsOrDefault(options?: ClassOption[] | null): ClassOption[] {
  return options && options.length > 0 ? options : DEFAULT_CLASS_OPTIONS;
}
