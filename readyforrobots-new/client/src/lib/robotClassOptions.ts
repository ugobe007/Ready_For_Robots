/**
 * FIND class picker tiles. Keep in sync with
 * `app.services.robot_class_qualify.CLASS_OPTIONS`.
 *
 * Form-factor tiles (humanoid, AMR, …) plus work-domain / platform classes
 * the morphology list misses (agriculture, marine, avionics, construction).
 * Agriculture is a robot class, not a SIGNAL industry tag.
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
    hint: "Field and crop work — weeding, spraying, harvest",
  },
  {
    id: "marine",
    label: "Marine",
    hint: "Hull, port, and underwater work",
  },
  {
    id: "avionics",
    label: "Avionics",
    hint: "Hangar and airside aircraft work — not a consumer drone",
  },
  {
    id: "construction",
    label: "Construction",
    hint: "Jobsite earthwork, layout, and finishing",
  },
];

export const CLASS_OPTION_IDS = DEFAULT_CLASS_OPTIONS.map(row => row.id);

export function classOptionsOrDefault(options?: ClassOption[] | null): ClassOption[] {
  return options && options.length > 0 ? options : DEFAULT_CLASS_OPTIONS;
}
