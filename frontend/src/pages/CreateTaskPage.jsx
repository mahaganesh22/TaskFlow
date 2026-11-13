import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getProject } from "../api/projects";
import { listMembers } from "../api/members";
import { createTask } from "../api/tasks";
import { fieldErrorsFromDetail, formatDetail } from "../api/client";
import { fromDateTimeLocal } from "../utils/format";

export default function CreateTaskPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [dueDate, setDueDate] = useState("");
  const [assignee, setAssignee] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([getProject(projectId), listMembers(projectId)])
      .then(([nextProject, nextMembers]) => {
        if (!active) return;
        setProject(nextProject);
        setMembers(nextMembers);
      })
      .catch((err) => {
        if (active) setError(formatDetail(err.detail) || "Could not load this project");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [projectId]);

  async function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = {};
    if (!title.trim()) nextErrors.title = "Task title cannot be empty";
    if (dueDate && new Date(dueDate) <= new Date()) {
      nextErrors.due_date = "Due date cannot be in the past";
    }
    setFieldErrors(nextErrors);
    setError("");
    if (Object.keys(nextErrors).length) return;

    setCreating(true);
    try {
      await createTask(projectId, {
        title: title.trim(),
        description: description.trim() || null,
        priority,
        due_date: fromDateTimeLocal(dueDate),
        assignee_id: assignee || null
      });
      navigate(`/projects/${projectId}?tab=backlog`, { replace: true });
    } catch (err) {
      const errors = fieldErrorsFromDetail(err.detail);
      setFieldErrors(errors);
      if (!Object.keys(errors).length) setError(formatDetail(err.detail) || "Could not create task");
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="page-status">Loading project…</div>;
  if (!project) {
    return <div className="page-status error"><p>{error || "Project not found"}</p><Link to="/">Back to dashboard</Link></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to={`/projects/${projectId}?tab=backlog`} className="muted">← Back to backlog</Link>
          <h1>Create task</h1>
          <p className="muted">Add a task to {project.name}.</p>
        </div>
      </div>
      <section className="panel create-task-panel">
        <form className="stack" onSubmit={handleSubmit}>
          {error && <div className="alert">{error}</div>}
          <label>
            Title
            <input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} />
            {fieldErrors.title && <span className="field-error">{fieldErrors.title}</span>}
          </label>
          <label>
            Description
            <textarea rows={4} value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <div className="form-row">
            <label>
              Priority
              <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
              </select>
            </label>
            <label>
              Assignee
              <select value={assignee} onChange={(event) => setAssignee(event.target.value)}>
                <option value="">Unassigned</option>
                {members.map((member) => <option key={member.user_id} value={member.user_id}>{member.user.name}</option>)}
              </select>
            </label>
            <label>
              Due date
              <input type="datetime-local" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
              {fieldErrors.due_date && <span className="field-error">{fieldErrors.due_date}</span>}
            </label>
          </div>
          <div className="form-actions">
            <Link className="btn" to={`/projects/${projectId}?tab=backlog`}>Cancel</Link>
            <button className="btn btn-primary" type="submit" disabled={creating}>
              {creating ? "Creating…" : "Create task"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
