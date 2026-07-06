import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";
import type { WorkflowEdgeData } from "@/lib/workflowFlowAdapter";

export default function WorkflowEdge(props: EdgeProps) {
  const { id, sourceX, sourceY, targetX, targetY, data, style, markerEnd } = props;
  const edgeData = (data || {}) as WorkflowEdgeData;
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} markerEnd={markerEnd} />
      {edgeData.label ? (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan pointer-events-none absolute rounded bg-white/90 px-1.5 py-0.5 text-[9px] font-medium text-slate-600 border border-slate-200 shadow-sm"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            {edgeData.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
