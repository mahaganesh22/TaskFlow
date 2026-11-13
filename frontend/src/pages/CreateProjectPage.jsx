import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { createProject } from "../api/projects";
import { formatDetail } from "../api/client";

export default function CreateProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [techStack, setTechStack] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Project name cannot be empty");
      return;
    }

    setError("");
    setCreating(true);
    try {
      const project = await createProject({
        name: name.trim(),
        description: description.trim() || null,
        tech_stack: techStack.trim() || null
      });
      navigate(`/projects/${project.id}`, { replace: true });
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not create project");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="muted">← Dashboard</Link>
          <p className="eyebrow">New workspace</p>
          <h1>Create a project</h1>
          <p className="muted">Set up a space for your team’s work.</p>
        </div>
      </div>
      <section className="panel create-task-panel">
        <form className="stack" onSubmit={handleSubmit}>
          {error && <div className="alert" role="alert">{error}</div>}
          <label>
            Project name
            <input autoFocus value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Description
            <textarea rows={4} value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label>
            Tech stack
            <input
              value={techStack}
              onChange={(event) => setTechStack(event.target.value)}
              placeholder="e.g. React, FastAPI, PostgreSQL"
            />
          </label>
          <div className="form-actions">
            <Link className="btn" to="/">Cancel</Link>
            <button className="btn btn-primary" type="submit" disabled={creating}>
              {creating ? "Creating…" : "Create project"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
