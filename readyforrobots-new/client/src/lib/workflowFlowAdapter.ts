/**
 * Convert between WorkflowLayout (API/storage) and React Flow nodes/edges.
 */
import type { CSSProperties } from "react";
import type { Edge, Node } from "@xyflow/react";
import { nanoid } from "nanoid";
import type {
  RobotPlacement,
  WorkflowFlow,
  WorkflowLayout,
  WorkflowZone,
} from "@/lib/workflowLayoutTypes";

export const ZONE_NODE_TYPE = "workflowZone";
export const ROBOT_NODE_TYPE = "workflowRobot";
export const WORKFLOW_EDGE_TYPE = "workflow";

export type ZoneNodeData = {
  label: string;
  kind: WorkflowZone["kind"];
  w: number;
  h: number;
};

export type RobotNodeData = {
  robot_label: string;
  zone_id: string;
  tasks: string[];
  impact: RobotPlacement["impact"];
};

export type WorkflowEdgeData = {
  label?: string;
  automated: boolean;
};

export function layoutToFlow(layout: WorkflowLayout): {
  nodes: Node[];
  edges: Edge[];
} {
  const zoneNodes: Node<ZoneNodeData>[] = layout.zones.map(zone => ({
    id: zone.id,
    type: ZONE_NODE_TYPE,
    position: { x: zone.x, y: zone.y },
    data: { label: zone.label, kind: zone.kind, w: zone.w, h: zone.h },
    style: { width: zone.w, height: zone.h },
    draggable: true,
    connectable: true,
  }));

  const robotNodes: Node<RobotNodeData>[] = layout.robots.map(robot => ({
    id: robot.id,
    type: ROBOT_NODE_TYPE,
    position: { x: robot.x - 24, y: robot.y - 24 },
    data: {
      robot_label: robot.robot_label,
      zone_id: robot.zone_id,
      tasks: robot.tasks,
      impact: robot.impact,
    },
    draggable: true,
    connectable: false,
  }));

  const zoneIds = new Set(layout.zones.map(z => z.id));
  const edges: Edge<WorkflowEdgeData>[] = layout.flows
    .filter(
      flow => zoneIds.has(flow.from_zone_id) && zoneIds.has(flow.to_zone_id)
    )
    .map(flow => flowToEdge(flow));

  return { nodes: [...zoneNodes, ...robotNodes], edges };
}

export function flowToLayout(
  nodes: Node[],
  edges: Edge[],
  width = 720,
  height = 320
): WorkflowLayout {
  const zones: WorkflowZone[] = nodes
    .filter(n => n.type === ZONE_NODE_TYPE)
    .map(n => {
      const data = n.data as ZoneNodeData;
      return {
        id: n.id,
        label: data.label,
        kind: data.kind,
        x: Math.round(n.position.x),
        y: Math.round(n.position.y),
        w: data.w,
        h: data.h,
      };
    });

  const robots: RobotPlacement[] = nodes
    .filter(n => n.type === ROBOT_NODE_TYPE)
    .map(n => {
      const data = n.data as RobotNodeData;
      return {
        id: n.id,
        robot_label: data.robot_label,
        zone_id: data.zone_id,
        x: Math.round(n.position.x + 24),
        y: Math.round(n.position.y + 24),
        tasks: data.tasks,
        impact: data.impact,
      };
    });

  const zoneIds = new Set(zones.map(z => z.id));
  const flows: WorkflowFlow[] = edges
    .filter(e => zoneIds.has(e.source) && zoneIds.has(e.target))
    .map(e => edgeToFlow(e));

  return { width, height, zones, robots, flows };
}

function flowToEdge(flow: WorkflowFlow): Edge<WorkflowEdgeData> {
  const automated = flow.automated !== false;
  return {
    id: flow.id,
    source: flow.from_zone_id,
    target: flow.to_zone_id,
    type: WORKFLOW_EDGE_TYPE,
    data: { label: flow.label, automated },
    animated: automated,
    style: edgeStyle(automated),
    markerEnd: {
      type: "arrowclosed" as const,
      color: automated ? "#059669" : "#94a3b8",
    },
  };
}

function edgeToFlow(edge: Edge): WorkflowFlow {
  const data = (edge.data || {}) as WorkflowEdgeData;
  return {
    id: edge.id,
    from_zone_id: edge.source,
    to_zone_id: edge.target,
    label: data.label,
    automated: data.automated !== false,
  };
}

export function edgeStyle(automated: boolean): CSSProperties {
  return automated
    ? { stroke: "#059669", strokeWidth: 2.5 }
    : { stroke: "#94a3b8", strokeWidth: 2, strokeDasharray: "8 5" };
}

export function createZoneNode(
  preset: {
    label: string;
    kind: WorkflowZone["kind"];
    w: number;
    h: number;
  },
  position: { x: number; y: number }
): Node<ZoneNodeData> {
  const id = `z_${nanoid(6)}`;
  return {
    id,
    type: ZONE_NODE_TYPE,
    position,
    data: { label: preset.label, kind: preset.kind, w: preset.w, h: preset.h },
    style: { width: preset.w, height: preset.h },
    draggable: true,
    connectable: true,
  };
}

export function createRobotNode(
  preset: {
    label: string;
    tasks: string[];
    labor_hours_saved_per_week: number;
    throughput_delta_pct: number;
  },
  position: { x: number; y: number },
  zoneId = ""
): Node<RobotNodeData> {
  const id = `r_${nanoid(6)}`;
  return {
    id,
    type: ROBOT_NODE_TYPE,
    position: { x: position.x - 24, y: position.y - 24 },
    data: {
      robot_label: preset.label,
      zone_id: zoneId,
      tasks: preset.tasks,
      impact: {
        labor_hours_saved_per_week: preset.labor_hours_saved_per_week,
        throughput_delta_pct: preset.throughput_delta_pct,
      },
    },
    draggable: true,
    connectable: false,
  };
}

export function createFlowEdge(connection: {
  source: string;
  target: string;
  automated?: boolean;
  label?: string;
}): Edge<WorkflowEdgeData> {
  const automated = connection.automated !== false;
  return {
    id: `f_${nanoid(6)}`,
    source: connection.source,
    target: connection.target,
    type: WORKFLOW_EDGE_TYPE,
    data: { label: connection.label || "Material flow", automated },
    animated: automated,
    style: edgeStyle(automated),
    markerEnd: {
      type: "arrowclosed" as const,
      color: automated ? "#059669" : "#94a3b8",
    },
  };
}
