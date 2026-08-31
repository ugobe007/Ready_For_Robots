/**
 * Shared workflow layout types + zone styling.
 */
export type WorkflowZone = {
  id: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  kind: "human" | "robot" | "handoff" | "storage" | "process";
};

export type RobotPlacement = {
  id: string;
  robot_label: string;
  zone_id: string;
  x: number;
  y: number;
  tasks: string[];
  impact: {
    labor_hours_saved_per_week?: number;
    throughput_delta_pct?: number;
    error_reduction_pct?: number;
  };
};

export type WorkflowFlow = {
  id: string;
  from_zone_id: string;
  to_zone_id: string;
  label?: string;
  automated: boolean;
};

export type WorkflowLayout = {
  width: number;
  height: number;
  zones: WorkflowZone[];
  robots: RobotPlacement[];
  flows: WorkflowFlow[];
};

export const ZONE_COLORS: Record<
  string,
  { fill: string; stroke: string; text: string }
> = {
  human: { fill: "#f8fafc", stroke: "#94a3b8", text: "#475569" },
  robot: { fill: "#ecfdf5", stroke: "#059669", text: "#065f46" },
  handoff: { fill: "#fffbeb", stroke: "#d97706", text: "#92400e" },
  storage: { fill: "#f1f5f9", stroke: "#64748b", text: "#334155" },
  process: { fill: "#eff6ff", stroke: "#3b82f6", text: "#1e40af" },
};

export function zoneCenter(
  zones: WorkflowZone[],
  id: string
): { x: number; y: number } | null {
  const z = zones.find(zone => zone.id === id);
  if (!z) return null;
  return { x: z.x + z.w / 2, y: z.y + z.h / 2 };
}

export type ZonePreset = {
  label: string;
  kind: WorkflowZone["kind"];
  w: number;
  h: number;
};

export type RobotPreset = {
  label: string;
  tasks: string[];
  labor_hours_saved_per_week: number;
  throughput_delta_pct: number;
};

export const ZONE_PRESETS: ZonePreset[] = [
  { label: "Inbound dock", kind: "human", w: 140, h: 72 },
  { label: "Pick zone", kind: "process", w: 150, h: 72 },
  { label: "Pack / ship", kind: "process", w: 140, h: 72 },
  { label: "Storage", kind: "storage", w: 120, h: 64 },
  { label: "Manual process", kind: "human", w: 130, h: 68 },
  { label: "QC / finish", kind: "handoff", w: 120, h: 64 },
  { label: "Guest floor", kind: "process", w: 140, h: 72 },
  { label: "Housekeeping stock", kind: "storage", w: 130, h: 64 },
];

export const ROBOT_PRESETS: RobotPreset[] = [
  {
    label: "Pallet AMR",
    tasks: ["Pallet move", "dock-to-pick"],
    labor_hours_saved_per_week: 45,
    throughput_delta_pct: 22,
  },
  {
    label: "Delivery bot",
    tasks: ["Room delivery", "linens"],
    labor_hours_saved_per_week: 28,
    throughput_delta_pct: 15,
  },
  {
    label: "Cobot arm",
    tasks: ["Pick assist", "pack"],
    labor_hours_saved_per_week: 35,
    throughput_delta_pct: 18,
  },
  {
    label: "Floor scrubber",
    tasks: ["Autonomous clean"],
    labor_hours_saved_per_week: 20,
    throughput_delta_pct: 8,
  },
  {
    label: "Goods-to-person",
    tasks: ["Shelving", "replenish"],
    labor_hours_saved_per_week: 40,
    throughput_delta_pct: 25,
  },
];
