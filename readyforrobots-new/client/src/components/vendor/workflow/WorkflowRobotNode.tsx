import type { Node, NodeProps } from "@xyflow/react";
import type { RobotNodeData } from "@/lib/workflowFlowAdapter";

export default function WorkflowRobotNode({
  data,
  selected,
}: NodeProps<Node<RobotNodeData>>) {
  const hrs = data.impact.labor_hours_saved_per_week;
  return (
    <div
      className={`flex flex-col items-center ${selected ? "ring-2 ring-emerald-500 rounded-full" : ""}`}
    >
      <div className="w-12 h-12 rounded-full bg-emerald-600 border-2 border-emerald-800 flex items-center justify-center text-xl shadow-md">
        🤖
      </div>
      <div className="mt-1 rounded bg-slate-900 px-2 py-0.5 text-[9px] text-emerald-300 font-bold whitespace-nowrap max-w-[120px] truncate">
        {data.robot_label}
      </div>
      {hrs ? (
        <div className="text-[8px] text-slate-500 font-medium">
          {hrs}h/wk saved
        </div>
      ) : null}
    </div>
  );
}
