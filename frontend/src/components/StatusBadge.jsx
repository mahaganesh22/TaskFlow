import { PRIORITY_LABELS, STATUS_LABELS } from "../utils/format";

export function StatusBadge({ status }) {
  return (
    <span className={`badge status-${status}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  return (
    <span className={`badge priority-${priority}`}>
      {PRIORITY_LABELS[priority] || priority}
    </span>
  );
}
