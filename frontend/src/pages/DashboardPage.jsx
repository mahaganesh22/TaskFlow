import { useEffect, useMemo, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { listProjects } from "../api/projects";
import { listAssignedTasks, listAllProjectTasks } from "../api/tasks";
import { listActivities } from "../api/activities";
import { formatDetail } from "../api/client";
import { ACTIVITY_LABELS, STATUS_LABELS, formatDate, startOfWeek } from "../utils/format";

export default function DashboardPage() {
  const { liveTick } = useOutletContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState([]);
  const [assigned, setAssigned] = useState([]);
  const [openCounts, setOpenCounts] = useState({});
  const [activities, setActivities] = useState([]);

  async function loadDashboard({ silent = false } = {}) {
    if (!silent) setLoading(true);
    setError("");

    try {
      const projectList = await listProjects();
      setProjects(projectList);

      const assignedPage = await listAssignedTasks({ limit: 100, offset: 0 });
      setAssigned(assignedPage.items);

      const counts = {};
      const activityGroups = await Promise.all(
        projectList.slice(0, 8).map(async (project) => {
          const [tasks, feed] = await Promise.all([
            listAllProjectTasks(project.id),
            listActivities(project.id, { limit: 8 })
          ]);

          counts[project.id] = tasks.filter((task) => task.status !== "DONE").length;
          return feed.map((item) => ({ ...item, projectName: project.name }));
        })
      );

      setOpenCounts(counts);
      setActivities(
        activityGroups
          .flat()
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 12)
      );
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not load the dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard({ silent: liveTick > 0 });
  }, [liveTick]);

  const stats = useMemo(() => {
    const byStatus = { TODO: 0, IN_PROGRESS: 0, DONE: 0 };
    assigned.forEach((task) => {
      byStatus[task.status] += 1;
    });

    const weekStart = startOfWeek();
    const completedThisWeek = assigned.filter((task) => {
      if (task.status !== "DONE" || !task.completed_at) return false;
      return new Date(task.completed_at) >= weekStart;
    }).length;

    let busiest = null;
    projects.forEach((project) => {
      const open = openCounts[project.id] || 0;
      if (!busiest || open > busiest.open) {
        busiest = { project, open };
      }
    });

    return { byStatus, completedThisWeek, busiest };
  }, [assigned, projects, openCounts]);

  if (loading) {
    return <div className="page-status">Loading dashboard…</div>;
  }

  if (error) {
    return (
      <div className="page-status error">
        <p>{error}</p>
        <button className="btn btn-primary" type="button" onClick={loadDashboard}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Dashboard</h1>
        </div>
        <Link className="btn btn-primary" to="/projects/new">Create project</Link>
      </div>

      <section className="stat-grid">
        <article className="stat-card">
          <span>Projects</span>
          <strong>{projects.length}</strong>
        </article>
        {Object.entries(stats.byStatus).map(([status, count]) => (
          <article className="stat-card" key={status}>
            <span>Assigned · {STATUS_LABELS[status]}</span>
            <strong>{count}</strong>
          </article>
        ))}
        <article className="stat-card">
          <span>Completed this week</span>
          <strong>{stats.completedThisWeek}</strong>
        </article>
      </section>

      <div className="split">
        <section className="panel">
          <div className="panel-header">
            <h2>Your projects</h2>
          </div>

          {stats.busiest && (
            <p className="muted">
              Most open tasks:{" "}
              <Link to={`/projects/${stats.busiest.project.id}`}>
                {stats.busiest.project.name}
              </Link>{" "}
              ({stats.busiest.open})
            </p>
          )}

          {projects.length === 0 ? (
            <p className="muted">No projects yet. Create one to start a board.</p>
          ) : (
            <ul className="project-list">
              {projects.map((project) => (
                <li key={project.id}>
                  <Link to={`/projects/${project.id}`}>
                    <strong>{project.name}</strong>
                    <span>{openCounts[project.id] ?? "—"} open</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}

        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Recent activity</h2>
          </div>
          {activities.length === 0 ? (
            <p className="muted">No recent activity yet.</p>
          ) : (
            <ul className="activity-list">
              {activities.map((item) => (
                <li key={item.id}>
                  <strong>{item.actor_name}</strong> {ACTIVITY_LABELS[item.activity_type] || item.activity_type}
                  {item.task_title ? ` · ${item.task_title}` : ""}
                  <div className="muted">
                    {item.projectName} · {formatDate(item.created_at)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
