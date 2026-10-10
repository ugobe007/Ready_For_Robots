import { describe, expect, it } from "vitest";
import { layoutToFlow, flowToLayout } from "@/lib/workflowFlowAdapter";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";

const logisticsLayout: WorkflowLayout = {
  width: 720,
  height: 320,
  zones: [
    {
      id: "inbound",
      label: "Inbound dock",
      x: 30,
      y: 50,
      w: 150,
      h: 90,
      kind: "human",
    },
    {
      id: "pick",
      label: "Pick zone",
      x: 200,
      y: 50,
      w: 180,
      h: 90,
      kind: "process",
    },
    {
      id: "pack",
      label: "Pack / ship",
      x: 400,
      y: 50,
      w: 160,
      h: 90,
      kind: "process",
    },
  ],
  robots: [
    {
      id: "r1",
      robot_label: "Pallet AMR",
      zone_id: "pick",
      x: 290,
      y: 95,
      tasks: ["Pallet move"],
      impact: { labor_hours_saved_per_week: 45, throughput_delta_pct: 22 },
    },
  ],
  flows: [
    {
      id: "f1",
      from_zone_id: "inbound",
      to_zone_id: "pick",
      label: "Replenishment",
      automated: true,
    },
    {
      id: "f2",
      from_zone_id: "pick",
      to_zone_id: "pack",
      label: "Order flow",
      automated: false,
    },
  ],
};

describe("workflowFlowAdapter", () => {
  it("preserves zone-to-zone flows in round-trip", () => {
    const { nodes, edges } = layoutToFlow(logisticsLayout);
    expect(nodes.filter(n => n.type === "workflowZone")).toHaveLength(3);
    expect(edges).toHaveLength(2);
    expect(edges.map(e => e.source).sort()).toEqual(["inbound", "pick"]);

    const roundTrip = flowToLayout(nodes, edges, 720, 320);
    expect(roundTrip.flows).toHaveLength(2);
    expect(roundTrip.flows[0].from_zone_id).toBe("inbound");
    expect(roundTrip.flows[0].to_zone_id).toBe("pick");
    expect(roundTrip.robots[0].robot_label).toBe("Pallet AMR");
  });
});
