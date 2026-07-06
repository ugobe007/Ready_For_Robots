/**
 * React Flow workflow editor — drag zones, connect flows, place robots.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useOnSelectionChange,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Plus, Trash2 } from "lucide-react";
import {
  ROBOT_NODE_TYPE,
  ZONE_NODE_TYPE,
  WORKFLOW_EDGE_TYPE,
  createFlowEdge,
  createRobotNode,
  createZoneNode,
  edgeStyle,
  flowToLayout,
  layoutToFlow,
  type RobotNodeData,
  type WorkflowEdgeData,
  type ZoneNodeData,
} from "@/lib/workflowFlowAdapter";
import {
  ROBOT_PRESETS,
  ZONE_PRESETS,
  type WorkflowLayout,
} from "@/lib/workflowLayoutTypes";
import WorkflowEdge from "@/components/vendor/workflow/WorkflowEdge";
import WorkflowRobotNode from "@/components/vendor/workflow/WorkflowRobotNode";
import WorkflowZoneNode from "@/components/vendor/workflow/WorkflowZoneNode";

const nodeTypes = {
  [ZONE_NODE_TYPE]: WorkflowZoneNode,
  [ROBOT_NODE_TYPE]: WorkflowRobotNode,
};

const edgeTypes = {
  [WORKFLOW_EDGE_TYPE]: WorkflowEdge,
};

type Props = {
  layout: WorkflowLayout;
  onChange: (layout: WorkflowLayout) => void;
  className?: string;
};

function isZoneNode(node: Node | null | undefined): node is Node<ZoneNodeData> {
  return node?.type === ZONE_NODE_TYPE;
}

function isRobotNode(node: Node | null | undefined): node is Node<RobotNodeData> {
  return node?.type === ROBOT_NODE_TYPE;
}

function isWorkflowEdge(edge: Edge | null | undefined): edge is Edge<WorkflowEdgeData> {
  return Boolean(edge);
}

function WorkflowFlowEditorInner({ layout, onChange, className = "" }: Props) {
  const { fitView, screenToFlowPosition } = useReactFlow();
  const syncingRef = useRef(false);
  const fitOnceRef = useRef(false);

  const initial = useMemo(() => layoutToFlow(layout), [layout]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);
  nodesRef.current = nodes;
  edgesRef.current = edges;

  const syncToParent = useCallback(() => {
    syncingRef.current = true;
    onChange(
      flowToLayout(nodesRef.current, edgesRef.current, layout.width, layout.height),
    );
  }, [layout.height, layout.width, onChange]);

  const emitChange = useCallback(
    (nextNodes: Node[], nextEdges: Edge[]) => {
      nodesRef.current = nextNodes;
      edgesRef.current = nextEdges;
      syncingRef.current = true;
      onChange(flowToLayout(nextNodes, nextEdges, layout.width, layout.height));
    },
    [layout.height, layout.width, onChange],
  );

  useEffect(() => {
    if (syncingRef.current) {
      syncingRef.current = false;
      return;
    }
    const converted = layoutToFlow(layout);
    setNodes(converted.nodes);
    setEdges(converted.edges);
    fitOnceRef.current = false;
  }, [layout, setEdges, setNodes]);

  useEffect(() => {
    if (!fitOnceRef.current && nodes.length > 0) {
      fitOnceRef.current = true;
      requestAnimationFrame(() => fitView({ padding: 0.15, duration: 200 }));
    }
  }, [nodes.length, fitView]);

  useOnSelectionChange({
    onChange: ({ nodes: selNodes, edges: selEdges }) => {
      setSelectedNode(selNodes[0] ?? null);
      setSelectedEdge(selEdges[0] ?? null);
    },
  });

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const sourceNode = nodes.find((n) => n.id === connection.source);
      const targetNode = nodes.find((n) => n.id === connection.target);
      if (sourceNode?.type !== ZONE_NODE_TYPE || targetNode?.type !== ZONE_NODE_TYPE) return;

      const nextEdge = createFlowEdge({
        source: connection.source,
        target: connection.target,
        automated: true,
        label: "Material flow",
      });
      const nextEdges = [...edges, nextEdge];
      setEdges(nextEdges);
      emitChange(nodes, nextEdges);
    },
    [edges, emitChange, nodes, setEdges],
  );

  function addZoneAtCenter(preset: (typeof ZONE_PRESETS)[number]) {
    const center = screenToFlowPosition({
      x: window.innerWidth / 2,
      y: window.innerHeight / 2,
    });
    const node = createZoneNode(preset, {
      x: center.x - preset.w / 2,
      y: center.y - preset.h / 2,
    });
    const nextNodes = [...nodes, node];
    setNodes(nextNodes);
    emitChange(nextNodes, edges);
  }

  function addRobotAtCenter(preset: (typeof ROBOT_PRESETS)[number]) {
    const center = screenToFlowPosition({
      x: window.innerWidth / 2,
      y: window.innerHeight / 2,
    });
    const zoneId = isZoneNode(selectedNode) ? selectedNode.id : "";
    const node = createRobotNode(preset, center, zoneId);
    const nextNodes = [...nodes, node];
    setNodes(nextNodes);
    emitChange(nextNodes, edges);
  }

  function deleteSelected() {
    if (selectedEdge) {
      const nextEdges = edges.filter((e) => e.id !== selectedEdge.id);
      setEdges(nextEdges);
      setSelectedEdge(null);
      emitChange(nodes, nextEdges);
      return;
    }
    if (!selectedNode) return;
    const nextNodes = nodes.filter((n) => n.id !== selectedNode.id);
    const nextEdges = edges.filter(
      (e) => e.source !== selectedNode.id && e.target !== selectedNode.id,
    );
    setNodes(nextNodes);
    setEdges(nextEdges);
    setSelectedNode(null);
    emitChange(nextNodes, nextEdges);
  }

  function updateSelectedNodeData(patch: Partial<ZoneNodeData> | Partial<RobotNodeData>) {
    if (!selectedNode) return;
    const nextNodes = nodes.map((n) =>
      n.id === selectedNode.id ? { ...n, data: { ...n.data, ...patch } } : n,
    );
    setNodes(nextNodes);
    emitChange(nextNodes, edges);
  }

  function toggleEdgeAutomated() {
    if (!selectedEdge) return;
    const data = (selectedEdge.data || {}) as WorkflowEdgeData;
    const automated = !data.automated;
    const nextEdges = edges.map((e) =>
      e.id === selectedEdge.id
        ? {
            ...e,
            data: { ...data, automated },
            animated: automated,
            style: edgeStyle(automated),
            markerEnd: {
              type: "arrowclosed" as const,
              color: automated ? "#059669" : "#94a3b8",
            },
          }
        : e,
    );
    setEdges(nextEdges);
    emitChange(nodes, nextEdges);
  }

  return (
    <div className={`flex flex-col lg:flex-row gap-4 ${className}`}>
      <aside className="lg:w-48 shrink-0 space-y-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-2">
            Work zones
          </p>
          <div className="flex flex-wrap lg:flex-col gap-1.5">
            {ZONE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => addZoneAtCenter(preset)}
                className="text-left text-[11px] px-2.5 py-1.5 rounded-lg border border-gray-200 bg-white hover:border-emerald-400 hover:bg-emerald-50/50"
              >
                <Plus className="inline h-3 w-3 mr-1 text-emerald-600" />
                {preset.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-2">
            Robots
          </p>
          <div className="flex flex-wrap lg:flex-col gap-1.5">
            {ROBOT_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => addRobotAtCenter(preset)}
                className="text-left text-[11px] px-2.5 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50/40 hover:bg-emerald-100/60"
              >
                🤖 {preset.label}
              </button>
            ))}
          </div>
        </div>
        {(selectedNode || selectedEdge) && (
          <button
            type="button"
            onClick={deleteSelected}
            className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-2 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 w-full"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete selected
          </button>
        )}
      </aside>

      <div className="flex-1 min-w-0 space-y-3">
        <div className="h-[480px] rounded-xl border border-slate-200 bg-slate-50 overflow-hidden shadow-inner">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDragStop={syncToParent}
            onNodesDelete={syncToParent}
            onEdgesDelete={syncToParent}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            snapToGrid
            snapGrid={[12, 12]}
            connectionLineStyle={{ stroke: "#059669", strokeWidth: 2 }}
            defaultEdgeOptions={{ type: WORKFLOW_EDGE_TYPE }}
            isValidConnection={(conn) => {
              const source = nodes.find((n) => n.id === conn.source);
              const target = nodes.find((n) => n.id === conn.target);
              return source?.type === ZONE_NODE_TYPE && target?.type === ZONE_NODE_TYPE;
            }}
            deleteKeyCode={["Backspace", "Delete"]}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} size={1} color="#cbd5e1" />
            <Controls showInteractive={false} />
            <MiniMap
              nodeColor={(n) => (n.type === ROBOT_NODE_TYPE ? "#059669" : "#e2e8f0")}
              maskColor="rgba(0,0,0,0.06)"
              className="!bg-white/80"
            />
          </ReactFlow>
        </div>

        <p className="text-[11px] text-slate-600">
          <strong>Connect zones:</strong> drag from the green handle on one zone to another. Flows
          stay linked when you move nodes. {edges.length} connection{edges.length === 1 ? "" : "s"}{" "}
          active.
        </p>

        {isZoneNode(selectedNode) && (
          <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs space-y-2">
            <p className="font-bold text-gray-700">Zone</p>
            <label className="block">
              <span className="text-gray-500">Label</span>
              <input
                className="mt-0.5 w-full rounded border border-gray-200 px-2 py-1"
                value={selectedNode.data.label}
                onChange={(e) => updateSelectedNodeData({ label: e.target.value })}
              />
            </label>
          </div>
        )}

        {isRobotNode(selectedNode) && (
          <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs space-y-2">
            <p className="font-bold text-gray-700">Robot</p>
            <label className="block">
              <span className="text-gray-500">Label</span>
              <input
                className="mt-0.5 w-full rounded border border-gray-200 px-2 py-1"
                value={selectedNode.data.robot_label}
                onChange={(e) => updateSelectedNodeData({ robot_label: e.target.value })}
              />
            </label>
            <label className="block">
              <span className="text-gray-500">Labor saved (h/wk)</span>
              <input
                type="number"
                className="mt-0.5 w-full rounded border border-gray-200 px-2 py-1"
                value={selectedNode.data.impact.labor_hours_saved_per_week ?? 0}
                onChange={(e) =>
                  updateSelectedNodeData({
                    impact: {
                      ...selectedNode.data.impact,
                      labor_hours_saved_per_week: parseFloat(e.target.value) || 0,
                    },
                  })
                }
              />
            </label>
          </div>
        )}

        {isWorkflowEdge(selectedEdge) && (
          <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs space-y-2">
            <p className="font-bold text-gray-700">Material flow</p>
            <label className="block">
              <span className="text-gray-500">Label</span>
              <input
                className="mt-0.5 w-full rounded border border-gray-200 px-2 py-1"
                value={(selectedEdge.data as WorkflowEdgeData)?.label || ""}
                onChange={(e) => {
                  const data = (selectedEdge.data || {}) as WorkflowEdgeData;
                  const nextEdges = edges.map((edge) =>
                    edge.id === selectedEdge.id
                      ? { ...edge, data: { ...data, label: e.target.value } }
                      : edge,
                  );
                  setEdges(nextEdges);
                  emitChange(nodes, nextEdges);
                }}
              />
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={(selectedEdge.data as WorkflowEdgeData)?.automated !== false}
                onChange={toggleEdgeAutomated}
              />
              <span className="text-gray-600">Automated (robot-handled)</span>
            </label>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkflowFlowEditor(props: Props) {
  return (
    <ReactFlowProvider>
      <WorkflowFlowEditorInner {...props} />
    </ReactFlowProvider>
  );
}
