import type { Node, NodeProps } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";
import { ZONE_COLORS } from "@/lib/workflowLayoutTypes";
import type { ZoneNodeData } from "@/lib/workflowFlowAdapter";

const HANDLE_CLASS =
  "!w-3 !h-3 !bg-emerald-500 !border-2 !border-white shadow-sm";

export default function WorkflowZoneNode({ data, selected }: NodeProps<Node<ZoneNodeData>>) {
  const c = ZONE_COLORS[data.kind] || ZONE_COLORS.process;
  return (
    <div
      className={`rounded-lg border-2 flex items-center justify-center text-center px-2 shadow-sm ${
        selected ? "ring-2 ring-emerald-500 ring-offset-2" : ""
      }`}
      style={{
        width: data.w,
        height: data.h,
        background: c.fill,
        borderColor: c.stroke,
        color: c.text,
      }}
    >
      <Handle type="target" position={Position.Top} id="top" className={HANDLE_CLASS} />
      <Handle type="target" position={Position.Left} id="left" className={HANDLE_CLASS} />
      <Handle type="source" position={Position.Right} id="right" className={HANDLE_CLASS} />
      <Handle type="source" position={Position.Bottom} id="bottom" className={HANDLE_CLASS} />
      <span className="text-xs font-semibold leading-tight pointer-events-none select-none">
        {data.label}
      </span>
    </div>
  );
}
