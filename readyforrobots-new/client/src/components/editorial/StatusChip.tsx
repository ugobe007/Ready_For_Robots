export type WorkflowStatus = "exploring" | "committed" | "open" | "unknown";

const LABEL: Record<WorkflowStatus, string> = {
  exploring: "Exploring",
  committed: "Committed",
  open: "Open",
  unknown: "Unknown",
};

export function StatusChip({ status }: { status: WorkflowStatus }) {
  return <span className={`rfr-status rfr-status-${status}`}>{LABEL[status]}</span>;
}
