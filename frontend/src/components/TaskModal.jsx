import { useEffect, useState } from "react";

import {
  assignTask,
  deleteTask,
  getTask,
  updateTask,
  updateTaskStatus
} from "../api/tasks";
import { addComment, listComments } from "../api/comments";
import { fieldErrorsFromDetail, formatDetail } from "../api/client";
import { PriorityBadge, StatusBadge } from "./StatusBadge";
import { formatDate, fromDateTimeLocal, toDateTimeLocal } from "../utils/format";

const STATUSES = ["TODO", "IN_PROGRESS", "DONE"];

export default function TaskModal({
  projectId,
  taskId,
  members,
  isOwner,
  currentUserId,
  onClose,
  onChanged
}) {
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [dueDate, setDueDate] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState("");
  const [commenting, setCommenting] = useState(false);
  const [statusError, setStatusError] = useState("");
  const [assignError, setAssignError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const [nextTask, nextComments] = await Promise.all([
        getTask(projectId, taskId),
        listComments(projectId, taskId)
      ]);
      setTask(nextTask);
      setTitle(nextTask.title);
      setDescription(nextTask.description || "");
      setPriority(nextTask.priority);
      setDueDate(toDateTimeLocal(nextTask.due_date));
      setComments(nextComments);
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not load this task");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [projectId, taskId]);

  async function handleSave(event) {
    event.preventDefault();
    const nextErrors = {};

    if (!title.trim()) nextErrors.title = "Task title cannot be empty";

    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSaving(true);

    try {
      await updateTask(projectId, taskId, {
        title: title.trim(),
        description: description.trim() || null,
        priority,
        due_date: fromDateTimeLocal(dueDate)
      });
      onChanged();
      await load();
    } catch (err) {
      setFieldErrors(fieldErrorsFromDetail(err.detail));
      setError(formatDetail(err.detail) || "Could not save task");
    } finally {
      setSaving(false);
    }
  }

  async function handleStatus(nextStatus) {
    setStatusError("");
    setSaving(true);

    try {
      await updateTaskStatus(projectId, taskId, nextStatus);
      onChanged();
      await load();
    } catch (err) {
      setStatusError(formatDetail(err.detail) || "Could not update status");
    } finally {
      setSaving(false);
    }
  }

  async function handleAssign(event) {
    const assigneeId = event.target.value;
    if (!assigneeId) return;

    setAssignError("");
    setSaving(true);

    try {
      await assignTask(projectId, taskId, assigneeId);
      onChanged();
      await load();
    } catch (err) {
      setAssignError(formatDetail(err.detail) || "Could not assign task");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this task?")) return;

    setSaving(true);

    try {
      await deleteTask(projectId, taskId);
      onChanged();
      onClose();
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not delete task");
      setSaving(false);
    }
  }

  async function handleComment(event) {
    event.preventDefault();

    if (!comment.trim()) {
      setCommentError("Comment cannot be empty");
      return;
    }

    setCommentError("");
    setCommenting(true);

    try {
      await addComment(projectId, taskId, comment.trim());
      setComment("");
      onChanged();
      setComments(await listComments(projectId, taskId));
    } catch (err) {
      setCommentError(formatDetail(err.detail) || "Could not add comment");
    } finally {
      setCommenting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h2>Task details</h2>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>

        {loading && <div className="page-status">Loading task…</div>}
        {!loading && error && <div className="alert">{error}</div>}

        {!loading && task && (
          <>
            <div className="row-badges">
              <StatusBadge status={task.status} />
              <PriorityBadge priority={task.priority} />
            </div>

            <div className="status-actions">
              {STATUSES.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="btn"
                  disabled={
                    saving ||
                    task.status === item ||
                    (!isOwner && task.assignee_id !== currentUserId)
                  }
                  onClick={() => handleStatus(item)}
                >
                  {item === "DONE" ? "Mark Done" : `Move to ${item.replace("_", " ")}`}
                </button>
              ))}
            </div>
            {statusError && <p className="field-error">{statusError}</p>}

            <form className="stack" onSubmit={handleSave}>
              <label>
                Title
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
                {fieldErrors.title && <span className="field-error">{fieldErrors.title}</span>}
              </label>
              <label>
                Description
                <textarea
                  rows={4}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
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
                  Due date
                  <input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(event) => setDueDate(event.target.value)}
                  />
                  {fieldErrors.due_date && (
                    <span className="field-error">{fieldErrors.due_date}</span>
                  )}
                </label>
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save changes"}
              </button>
            </form>

            <label>
              Assignee
              <select value={task.assignee_id || ""} onChange={handleAssign} disabled={saving}>
                {!task.assignee_id && <option value="">Unassigned</option>}
                {members.map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user.name}
                  </option>
                ))}
              </select>
              {assignError && <span className="field-error">{assignError}</span>}
            </label>
            {!isOwner && task.assignee_id !== currentUserId && (
              <p className="muted">Only the assignee or owner can mark this task Done.</p>
            )}

            <section>
              <h3>Comments</h3>
              {comments.length === 0 && <p className="muted">No comments yet.</p>}
              <ul className="comment-list">
                {comments.map((item) => (
                  <li key={item.id}>
                    <strong>{item.author_name}</strong>
                    <span className="muted"> · {formatDate(item.created_at)}</span>
                    <p>{item.content}</p>
                  </li>
                ))}
              </ul>
              <form className="stack compact" onSubmit={handleComment}>
                <textarea
                  rows={3}
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Write a comment"
                />
                {commentError && <span className="field-error">{commentError}</span>}
                <button className="btn btn-primary" type="submit" disabled={commenting}>
                  {commenting ? "Posting…" : "Add comment"}
                </button>
              </form>
            </section>

            <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={saving}>
              Delete task
            </button>
          </>
        )}
      </div>
    </div>
  );
}
