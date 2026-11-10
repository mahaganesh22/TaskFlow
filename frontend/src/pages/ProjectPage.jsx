import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { deleteProject, getProject, transferOwnership, updateProject } from "../api/projects";
import { createTask, listAllProjectTasks, listProjectTasks } from "../api/tasks";
import { inviteMember, listMembers, removeMember } from "../api/members";
import { listActivities } from "../api/activities";
import { fieldErrorsFromDetail, formatDetail } from "../api/client";
import { useAuth } from "../context/AuthContext";
import useProjectWebSocket from "../hooks/useProjectWebSocket";
import TaskModal from "../components/TaskModal";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import {
  ACTIVITY_LABELS,
  formatDate,
  formatDay,
  fromDateTimeLocal,
  memberName
} from "../utils/format";

const COLUMNS = ["TODO", "IN_PROGRESS", "DONE"];

export default function ProjectPage() {
  const { projectId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, getAccessToken, refreshAccessToken } = useAuth();

  const [tab, setTab] = useState("board");
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [boardTasks, setBoardTasks] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [forbidden, setForbidden] = useState(false);

  const [assigneeId, setAssigneeId] = useState("");
  const [priority, setPriority] = useState("");
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");

  const [backlog, setBacklog] = useState({ items: [], total: 0, limit: 10, offset: 0 });
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [backlogLoading, setBacklogLoading] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [taskPriority, setTaskPriority] = useState("MEDIUM");
  const [dueDate, setDueDate] = useState("");
  const [taskAssignee, setTaskAssignee] = useState("");
  const [taskErrors, setTaskErrors] = useState({});
  const [creating, setCreating] = useState(false);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [inviting, setInviting] = useState(false);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectError, setProjectError] = useState("");
  const [savingProject, setSavingProject] = useState(false);
  const [newOwnerId, setNewOwnerId] = useState("");
  const [transferError, setTransferError] = useState("");
  const [transferring, setTransferring] = useState(false);
  const [createError, setCreateError] = useState("");

  const selectedTaskId = searchParams.get("task");
  const isOwner = project && user && project.owner_id === user.id;

  const { status: wsStatus } = useProjectWebSocket({
    projectId,
    getAccessToken,
    refreshAccessToken,
    onEvent: () => {
      loadProjectData({ silent: true });
    },
    onReconnect: () => {
      loadProjectData({ silent: true });
    },
    onAuthError: (code) => {
      if (code === 4403) {
        setForbidden(true);
      }
    }
  });

  async function loadProjectData({ silent = false } = {}) {
    if (!silent) setLoading(true);

    try {
      const [nextProject, nextMembers, nextTasks, nextActivities] = await Promise.all([
        getProject(projectId),
        listMembers(projectId),
        listAllProjectTasks(projectId, {
          assignee_id: assigneeId || undefined,
          priority: priority || undefined,
          search: appliedSearch || undefined
        }),
        listActivities(projectId, { limit: 40 })
      ]);

      setProject(nextProject);
      setProjectName(nextProject.name);
      setProjectDescription(nextProject.description || "");
      setMembers(nextMembers);
      setBoardTasks(nextTasks);
      setActivities(nextActivities);
      setError("");
      setForbidden(false);
    } catch (err) {
      if (err.status === 403) {
        setForbidden(true);
      } else {
        setError(formatDetail(err.detail) || "Could not load this project");
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadBacklog(offset = 0) {
    setBacklogLoading(true);

    try {
      const data = await listProjectTasks(projectId, {
        assignee_id: assigneeId || undefined,
        priority: priority || undefined,
        search: appliedSearch || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 10,
        offset
      });
      setBacklog(data);
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not load the backlog");
    } finally {
      setBacklogLoading(false);
    }
  }

  useEffect(() => {
    loadProjectData();
  }, [projectId, assigneeId, priority, appliedSearch]);

  useEffect(() => {
    if (tab === "backlog") {
      loadBacklog(0);
    }
  }, [tab, projectId, assigneeId, priority, appliedSearch, sortBy, sortOrder]);

  const tasksByStatus = useMemo(() => {
    const grouped = { TODO: [], IN_PROGRESS: [], DONE: [] };
    boardTasks.forEach((task) => {
      grouped[task.status]?.push(task);
    });
    return grouped;
  }, [boardTasks]);

  async function handleCreateTask(event) {
    event.preventDefault();
    const nextErrors = {};

    if (!title.trim()) nextErrors.title = "Task title cannot be empty";

    if (dueDate) {
      const due = new Date(dueDate);
      if (due <= new Date()) {
        nextErrors.due_date = "Due date cannot be in the past";
      }
    }

    setTaskErrors(nextErrors);
    setCreateError("");
    if (Object.keys(nextErrors).length) return;

    setCreating(true);

    try {
      await createTask(projectId, {
        title: title.trim(),
        description: description.trim() || null,
        priority: taskPriority,
        due_date: fromDateTimeLocal(dueDate),
        assignee_id: taskAssignee || null
      });
      setTitle("");
      setDescription("");
      setDueDate("");
      setTaskAssignee("");
      setTaskPriority("MEDIUM");
      await loadProjectData();
      if (tab === "backlog") await loadBacklog(backlog.offset);
    } catch (err) {
      const fieldErrors = fieldErrorsFromDetail(err.detail);
      setTaskErrors(fieldErrors);
      if (!Object.keys(fieldErrors).length) {
        setCreateError(formatDetail(err.detail) || "Could not create task");
      }
    } finally {
      setCreating(false);
    }
  }

  async function handleSaveProject(event) {
    event.preventDefault();

    if (!projectName.trim()) {
      setProjectError("Project name cannot be empty");
      return;
    }

    setProjectError("");
    setSavingProject(true);

    try {
      const updated = await updateProject(projectId, {
        name: projectName.trim(),
        description: projectDescription.trim() || null
      });
      setProject(updated);
    } catch (err) {
      setProjectError(formatDetail(err.detail) || "Could not update project");
    } finally {
      setSavingProject(false);
    }
  }

  async function handleTransfer(event) {
    event.preventDefault();

    if (!newOwnerId) {
      setTransferError("Choose a member to become the owner");
      return;
    }

    setTransferError("");
    setTransferring(true);

    try {
      const updated = await transferOwnership(projectId, newOwnerId);
      setProject(updated);
      setNewOwnerId("");
      setMembers(await listMembers(projectId));
    } catch (err) {
      setTransferError(formatDetail(err.detail) || "Could not transfer ownership");
    } finally {
      setTransferring(false);
    }
  }

  async function handleInvite(event) {
    event.preventDefault();

    if (!inviteEmail.trim()) {
      setInviteError("Email is required");
      return;
    }

    setInviteError("");
    setInviting(true);

    try {
      await inviteMember(projectId, inviteEmail.trim());
      setInviteEmail("");
      setMembers(await listMembers(projectId));
      setActivities(await listActivities(projectId, { limit: 40 }));
    } catch (err) {
      setInviteError(formatDetail(err.detail) || "Could not invite member");
    } finally {
      setInviting(false);
    }
  }

  async function handleRemove(userId) {
    if (!window.confirm("Remove this member from the project?")) return;

    try {
      await removeMember(projectId, userId);
      await loadProjectData();
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not remove member");
    }
  }

  async function handleDeleteProject() {
    if (!window.confirm("Delete this project and all of its tasks?")) return;

    try {
      await deleteProject(projectId);
      navigate("/", { replace: true });
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not delete project");
    }
  }

  function openTask(taskId) {
    setSearchParams({ task: taskId });
  }

  if (forbidden) {
    return (
      <div className="page-status error">
        <p>You are not a member of this project.</p>
        <Link className="btn btn-primary" to="/">
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (loading && !project) {
    return <div className="page-status">Loading project…</div>;
  }

  if (error && !project) {
    return (
      <div className="page-status error">
        <p>{error}</p>
        <button className="btn btn-primary" type="button" onClick={loadProjectData}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="muted">← Dashboard</Link>
          <h1>{project.name}</h1>
          <p className="muted">{project.description || "No description"}</p>
        </div>
        <div className="header-meta">
          <span className={`ws-pill ${wsStatus}`}>Live: {wsStatus}</span>
          <span className="badge">{isOwner ? "Owner" : "Member"}</span>
          {isOwner && (
            <button type="button" className="btn btn-danger" onClick={handleDeleteProject}>
              Delete project
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="tabs">
        {["board", "backlog", "members", "activity", "settings"].map((item) => (
          <button
            key={item}
            type="button"
            className={tab === item ? "tab active" : "tab"}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="filters">
        <label>
          Search title
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") setAppliedSearch(search.trim());
            }}
          />
        </label>
        <label>
          Assignee
          <select value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}>
            <option value="">Anyone</option>
            {members.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.user.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Priority
          <select value={priority} onChange={(event) => setPriority(event.target.value)}>
            <option value="">Any</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </label>
        <button type="button" className="btn" onClick={() => setAppliedSearch(search.trim())}>
          Apply search
        </button>
      </div>

      {tab === "board" && (
        <section className="board">
          {COLUMNS.map((status) => (
            <div className="column" key={status}>
              <header>
                <h2>{status.replace("_", " ")}</h2>
                <span>{tasksByStatus[status].length}</span>
              </header>
              <div className="column-body">
                {tasksByStatus[status].map((task) => (
                  <button
                    type="button"
                    className="task-card"
                    key={task.id}
                    onClick={() => openTask(task.id)}
                  >
                    <strong>{task.title}</strong>
                    <div className="row-badges">
                      <PriorityBadge priority={task.priority} />
                    </div>
                    <div className="muted">
                      {memberName(members, task.assignee_id)} · {formatDay(task.due_date)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {tab === "backlog" && (
        <section className="panel">
          <div className="filters">
            <label>
              Sort by
              <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                <option value="created_at">Date created</option>
                <option value="due_date">Due date</option>
                <option value="priority">Priority</option>
              </select>
            </label>
            <label>
              Order
              <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </label>
          </div>

          {backlogLoading && <div className="page-status">Loading backlog…</div>}

          {!backlogLoading && (
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Due</th>
                </tr>
              </thead>
              <tbody>
                {backlog.items.map((task) => (
                  <tr key={task.id} onClick={() => openTask(task.id)}>
                    <td>{task.title}</td>
                    <td><StatusBadge status={task.status} /></td>
                    <td><PriorityBadge priority={task.priority} /></td>
                    <td>{memberName(members, task.assignee_id)}</td>
                    <td>{formatDay(task.due_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="pagination">
            <button
              type="button"
              className="btn"
              disabled={backlog.offset === 0 || backlogLoading}
              onClick={() => loadBacklog(Math.max(0, backlog.offset - backlog.limit))}
            >
              Previous
            </button>
            <span>
              {backlog.total === 0 ? 0 : backlog.offset + 1}–
              {Math.min(backlog.offset + backlog.limit, backlog.total)} of {backlog.total}
            </span>
            <button
              type="button"
              className="btn"
              disabled={backlog.offset + backlog.limit >= backlog.total || backlogLoading}
              onClick={() => loadBacklog(backlog.offset + backlog.limit)}
            >
              Next
            </button>
          </div>
        </section>
      )}

      {tab === "members" && (
        <section className="panel">
          <ul className="member-list">
            {members.map((member) => (
              <li key={member.id}>
                <div>
                  <strong>{member.user.name}</strong>
                  <div className="muted">{member.user.email} · {member.role}</div>
                </div>
                {isOwner && member.role !== "OWNER" && (
                  <button
                    type="button"
                    className="btn"
                    onClick={() => handleRemove(member.user_id)}
                  >
                    Remove
                  </button>
                )}
              </li>
            ))}
          </ul>

          {isOwner && (
            <form className="stack compact" onSubmit={handleInvite}>
              <h3>Invite by email</h3>
              <input
                type="email"
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                placeholder="member@example.com"
              />
              {inviteError && <span className="field-error">{inviteError}</span>}
              <button className="btn btn-primary" type="submit" disabled={inviting}>
                {inviting ? "Inviting…" : "Invite member"}
              </button>
            </form>
          )}
        </section>
      )}

      {tab === "activity" && (
        <section className="panel">
          {activities.length === 0 ? (
            <p className="muted">No activity yet.</p>
          ) : (
            <ul className="activity-list">
              {activities.map((item) => (
                <li key={item.id}>
                  <strong>{item.actor_name}</strong>{" "}
                  {ACTIVITY_LABELS[item.activity_type] || item.activity_type}
                  {item.task_title ? ` · ${item.task_title}` : ""}
                  <div className="muted">{formatDate(item.created_at)}</div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "settings" && (
        <section className="panel">
          {isOwner ? (
            <>
              <form className="stack" onSubmit={handleSaveProject}>
                <h2>Project details</h2>
                <label>
                  Name
                  <input
                    value={projectName}
                    onChange={(event) => setProjectName(event.target.value)}
                  />
                </label>
                <label>
                  Description
                  <textarea
                    rows={3}
                    value={projectDescription}
                    onChange={(event) => setProjectDescription(event.target.value)}
                  />
                </label>
                {projectError && <span className="field-error">{projectError}</span>}
                <button className="btn btn-primary" type="submit" disabled={savingProject}>
                  {savingProject ? "Saving…" : "Save project"}
                </button>
              </form>

              <form className="stack compact" onSubmit={handleTransfer}>
                <h3>Transfer ownership</h3>
                <label>
                  New owner
                  <select
                    value={newOwnerId}
                    onChange={(event) => setNewOwnerId(event.target.value)}
                  >
                    <option value="">Select a member</option>
                    {members
                      .filter((member) => member.role !== "OWNER")
                      .map((member) => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.user.name}
                        </option>
                      ))}
                  </select>
                </label>
                {transferError && <span className="field-error">{transferError}</span>}
                <button className="btn" type="submit" disabled={transferring}>
                  {transferring ? "Transferring…" : "Transfer ownership"}
                </button>
              </form>
            </>
          ) : (
            <p className="muted">Only the project owner can edit project settings.</p>
          )}
        </section>
      )}

      <section className="panel">
        <h2>Create task</h2>
        <form className="stack" onSubmit={handleCreateTask}>
          {createError && <div className="alert">{createError}</div>}
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
            {taskErrors.title && <span className="field-error">{taskErrors.title}</span>}
          </label>
          <label>
            Description
            <textarea
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <div className="form-row">
            <label>
              Priority
              <select value={taskPriority} onChange={(event) => setTaskPriority(event.target.value)}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
              </select>
            </label>
            <label>
              Assignee
              <select value={taskAssignee} onChange={(event) => setTaskAssignee(event.target.value)}>
                <option value="">Unassigned</option>
                {members.map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Due date
              <input
                type="datetime-local"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
              {taskErrors.due_date && <span className="field-error">{taskErrors.due_date}</span>}
            </label>
          </div>
          <button className="btn btn-primary" type="submit" disabled={creating}>
            {creating ? "Creating…" : "Add task"}
          </button>
        </form>
      </section>

      {selectedTaskId && (
        <TaskModal
          projectId={projectId}
          taskId={selectedTaskId}
          members={members}
          isOwner={isOwner}
          currentUserId={user.id}
          onClose={() => setSearchParams({})}
          onChanged={() => {
            loadProjectData();
            if (tab === "backlog") loadBacklog(backlog.offset);
          }}
        />
      )}
    </div>
  );
}
