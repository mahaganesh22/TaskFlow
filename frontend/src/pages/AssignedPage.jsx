import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { listAssignedTasks } from "../api/tasks";
import { formatDetail } from "../api/client";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import { formatDay } from "../utils/format";

export default function AssignedPage() {
  const { liveTick } = useOutletContext();
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [page, setPage] = useState({ items: [], total: 0, limit: 10, offset: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(offset = 0, { silent = false } = {}) {
    if (!silent) setLoading(true);
    setError("");

    try {
      const data = await listAssignedTasks({
        status: status || undefined,
        priority: priority || undefined,
        limit: 10,
        offset
      });
      setPage(data);
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not load assigned tasks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(0, { silent: liveTick > 0 && !status && !priority });
  }, [status, priority, liveTick]);

  const canPrev = page.offset > 0;
  const canNext = page.offset + page.limit < page.total;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Personal</p>
          <h1>Assigned to me</h1>
        </div>
      </div>

      <div className="filters">
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All</option>
            <option value="TODO">To Do</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="DONE">Done</option>
          </select>
        </label>
        <label>
          Priority
          <select value={priority} onChange={(event) => setPriority(event.target.value)}>
            <option value="">All</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </label>
      </div>

      {loading && <div className="page-status">Loading assigned tasks…</div>}

      {!loading && error && (
        <div className="page-status error">
          <p>{error}</p>
          <button className="btn btn-primary" type="button" onClick={() => load(page.offset)}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && page.items.length === 0 && (
        <p className="muted">Nothing assigned to you right now.</p>
      )}

      {!loading && !error && page.items.length > 0 && (
        <ul className="task-rows">
          {page.items.map((task) => (
            <li key={task.id}>
              <Link to={`/projects/${task.project_id}?task=${task.id}`}>
                <div>
                  <strong>{task.title}</strong>
                  <div className="muted">Due {formatDay(task.due_date)}</div>
                </div>
                <div className="row-badges">
                  <StatusBadge status={task.status} />
                  <PriorityBadge priority={task.priority} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <div className="pagination">
        <button
          type="button"
          className="btn"
          disabled={!canPrev || loading}
          onClick={() => load(Math.max(0, page.offset - page.limit))}
        >
          Previous
        </button>
        <span>
          {page.total === 0 ? 0 : page.offset + 1}–
          {Math.min(page.offset + page.limit, page.total)} of {page.total}
        </span>
        <button
          type="button"
          className="btn"
          disabled={!canNext || loading}
          onClick={() => load(page.offset + page.limit)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
