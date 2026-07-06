/**
 * Read-only React Flow viewer for buyer share pages.
 */
import { useEffect, useMemo } from "react";
import {
  Background,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  ROBOT_NODE_TYPE,
  WORKFLOW_EDGE_TYPE,
  layoutToFlow,
} from "@/lib/workflowFlowAdapter";
import type { WorkflowLayout } from "@/lib/workflowLayoutTypes";
import WorkflowEdge from "@/components/vendor/workflow/WorkflowEdge";
import WorkflowRobotNode from "@/components/vendor/workflow/WorkflowRobotNode";
import WorkflowZoneNode from "@/components/vendor/workflow/WorkflowZoneNode";

const nodeTypes = {
  workflowZone: WorkflowZoneNode,
  workflowRobot: WorkflowRobotNode,
};

const edgeTypes = {
  [WORKFLOW_EDGE_TYPE]: WorkflowEdge,
};

type Props = {
  layout: WorkflowLayout;
  className?: string;
  showLegend?: boolean;
};

function WorkflowFlowViewerInner({ layout, className = "", showLegend = true }: Props) {
  const { fitView } = useReactFlow();
  const converted = useMemo(() => layoutToFlow(layout), [layout]);
  const [nodes, setNodes, onNodesChange] = useNodesState(converted.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(converted.edges);

  useEffect(() => {
    setNodes(converted.nodes);
    setEdges(converted.edges);
    requestAnimationFrame(() => fitView({ padding: 0.12, duration: 150 }));
  }, [converted, fitView, setEdges, setNodes]);

  return (
    <div className={className}>
      <div className="h-[360px] rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag
          zoomOnScroll
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={16} size={1} color="#cbd5e1" />
        </ReactFlow>
      </div>
      {showLegend && (
        <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-slate-500">
          <span className="inline-flex items-center gap-1">
            <span className="h-0.5 w-4 bg-emerald-600" /> Automated flow
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-0.5 w-4 border-t border-dashed border-slate-400" /> Manual flow
          </span>
          <span>🤖 Robot integration point</span>
          <span>
            {layout.flows.length} linked handoff{layout.flows.length === 1 ? "" : "s"}
          </span>
        </div>
      )}
    </div>
  );
}

export default function WorkflowFlowViewer(props: Props) {
  return (
    <ReactFlowProvider>
      <WorkflowFlowViewerInner {...props} />
    </ReactFlowProvider>
  );
}
