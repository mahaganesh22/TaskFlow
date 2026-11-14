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
  const [editAssigneeId, setEditAssigneeId] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState("");
  const [commenting, setCommenting] = useState(false);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
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
      setEditAssigneeId(nextTask.assignee_id || "");
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

  useEffect(() => {
    if (!showCommentDialog) return undefined;
    function handleEscape(event) {
      if (event.key === "Escape" && !commenting) setShowCommentDialog(false);
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [showCommentDialog, commenting]);

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

      if (isOwner && editAssigneeId && editAssigneeId !== (task.assignee_id || "")) {
        try {
          await assignTask(projectId, taskId, editAssigneeId);
        } catch (err) {
          await load();
          setAssignError(formatDetail(err.detail) || "Could not update assignee");
          return;
        }
      }

      setAssignError("");
      setIsEditing(false);
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
      const updatedTask = await updateTaskStatus(projectId, taskId, nextStatus);
      setTask(updatedTask);
      onChanged();
    } catch (err) {
      setStatusError(formatDetail(err.detail) || "Could not update status");
    } finally {
      setSaving(false);
    }
  }

  function beginEditing() {
    setTitle(task.title);
    setDescription(task.description || "");
    setPriority(task.priority);
    setDueDate(toDateTimeLocal(task.due_date));
    setEditAssigneeId(task.assignee_id || "");
    setFieldErrors({});
    setAssignError("");
    setError("");
    setIsEditing(true);
  }

  function cancelEditing() {
    setTitle(task.title);
    setDescription(task.description || "");
    setPriority(task.priority);
    setDueDate(toDateTimeLocal(task.due_date));
    setEditAssigneeId(task.assignee_id || "");
    setFieldErrors({});
    setAssignError("");
    setError("");
    setIsEditing(false);
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
      setShowCommentDialog(false);
    } catch (err) {
      setCommentError(formatDetail(err.detail) || "Could not add comment");
    } finally {
      setCommenting(false);
    }
  }

  return (
    <div className="modal-backdrop task-modal-backdrop" onClick={onClose}>
      <section
        className="modal task-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-detail-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="task-detail-header">
          <div>
            <p className="eyebrow">{isEditing ? "Editing task" : "Task details"}</p>
            <h2 id="task-detail-title">{isEditing ? title || "Task" : task?.title || "Task"}</h2>
          </div>
          <div className="task-header-actions">
            {task && !isEditing && (isOwner || task.assignee_id === currentUserId) && <button type="button" className="btn task-edit-button" onClick={beginEditing}>Edit</button>}
            <button type="button" className="icon-button" aria-label="Close task details" onClick={onClose}>×</button>
          </div>
        </header>

        {loading && <div className="page-status">Loading task…</div>}
        {!loading && error && <div className="alert" role="alert">{error}</div>}

        {!loading && task && (
          <>
            <div className="task-detail-summary">
              <div className="task-detail-badges">
                <StatusBadge status={task.status} />
                <PriorityBadge priority={task.priority} />
                {task.status === "DONE" && (
                  <span className="completion-label"><span aria-hidden="true">✓</span> Completed</span>
                )}
              </div>
              <div className="task-detail-status">
                <span className="field-caption">Update status</span>
                <div className="status-actions" role="group" aria-label="Update task status">
                  {STATUSES.map((item) => (
                    <button
                      key={item}
                      type="button"
                      className={`status-choice ${task.status === item ? "selected" : ""} ${item === "DONE" ? "done-choice" : ""}`}
                      aria-pressed={task.status === item}
                      disabled={
                        saving ||
                        task.status === item ||
                        (!isOwner && task.assignee_id !== currentUserId)
                      }
                      onClick={() => handleStatus(item)}
                    >
                      {item === "DONE" && <span aria-hidden="true">✓</span>}
                      {item.replace("_", " ")}
                    </button>
                  ))}
                </div>
                {statusError && <p className="field-error" role="alert">{statusError}</p>}
              </div>
            </div>

            <form className="task-edit-form" onSubmit={handleSave}>
              <section className="task-form-section">
                <div className="section-heading">
                  <div><h3>Overview</h3><p className="muted">Keep the task details and priority up to date.</p></div>
                </div>
                <label>
                  Task name
                  {isEditing ? (
                    <input value={title} onChange={(event) => setTitle(event.target.value)} />
                  ) : (
                    <div className="task-read-value">{task.title}</div>
                  )}
                  {fieldErrors.title && <span className="field-error">{fieldErrors.title}</span>}
                </label>
                <label>
                  Description
                  {isEditing ? (
                    <textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Add context or acceptance criteria" />
                  ) : (
                    <div className="task-read-value description-value">{task.description || <span className="muted">No description provided.</span>}</div>
                  )}
                </label>
                {isEditing ? (
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
                      <input type="datetime-local" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
                      {fieldErrors.due_date && <span className="field-error">{fieldErrors.due_date}</span>}
                    </label>
                  </div>
                ) : (
                  <div className="task-read-grid">
                    <div><span className="field-caption">Priority</span><PriorityBadge priority={task.priority} /></div>
                    <div><span className="field-caption">Due date</span><span>{task.due_date ? formatDate(task.due_date) : "No due date"}</span></div>
                  </div>
                )}
              </section>

              <section className="task-form-section task-assignee-section">
                <div className="section-heading">
                  <div><h3>Ownership</h3><p className="muted">Choose the teammate responsible for this work.</p></div>
                </div>
                <label>
                  Assignee
                  {isEditing && isOwner ? (
                    <select value={editAssigneeId} onChange={(event) => setEditAssigneeId(event.target.value)} disabled={saving}>
                      <option value="" disabled>Unassigned</option>
                      {members.map((member) => (
                        <option key={member.user_id} value={member.user_id}>{member.user.name}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="task-read-value">{members.find((member) => member.user_id === task.assignee_id)?.user.name || "Unassigned"}</div>
                  )}
                  {assignError && <span className="field-error" role="alert">{assignError}</span>}
                </label>
                {!isOwner && task.assignee_id !== currentUserId && (
                  <p className="muted">Only the assignee or project owner can update this task.</p>
                )}
              </section>

              <footer className="task-detail-footer">
                <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={saving || !isOwner}>Delete task</button>
                {isEditing && (
                  <div className="task-edit-actions">
                    <button type="button" className="btn btn-ghost" onClick={cancelEditing} disabled={saving}>Cancel</button>
                    <button className="btn btn-primary" type="submit" disabled={saving}>
                      {saving ? "Saving…" : "Save changes"}
                    </button>
                  </div>
                )}
              </footer>
            </form>

            <section className="task-comments-section">
              <div className="section-heading comments-heading">
                <div><h3>Discussion <span className="comment-count">{comments.length}</span></h3><p className="muted">Keep decisions and updates with the task.</p></div>
                <button type="button" className="btn comment-open-button" onClick={() => { setCommentError(""); setShowCommentDialog(true); }}>Comment</button>
              </div>
              {comments.length === 0 ? (
                <div className="comment-empty-state">No discussion yet. Add the first comment to keep everyone in sync.</div>
              ) : (
                <ul className="comment-list">
                  {comments.map((item) => (
                    <li key={item.id}>
                      <div className="comment-meta"><strong>{item.author_name}</strong><span>{formatDate(item.created_at)}</span></div>
                      <p>{item.content}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </section>

      {showCommentDialog && (
        <div className="modal-backdrop comment-dialog-backdrop" onClick={(event) => { event.stopPropagation(); if (event.target === event.currentTarget && !commenting) setShowCommentDialog(false); }}>
          <section
            className="modal comment-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="comment-dialog-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="task-detail-header">
              <div><p className="eyebrow">Task discussion</p><h2 id="comment-dialog-title">Add a comment</h2></div>
              <button type="button" className="icon-button" aria-label="Close comment dialog" disabled={commenting} onClick={() => setShowCommentDialog(false)}>×</button>
            </header>
            <p className="muted comment-context">Posting to <strong>{task?.title}</strong></p>
            <form className="stack" onSubmit={handleComment}>
              <label htmlFor="task-comment">Your comment</label>
              <textarea
                id="task-comment"
                rows={5}
                autoFocus
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder="Share an update, question, or decision…"
                maxLength={5000}
              />
              <div className="comment-dialog-footer">
                {commentError && <span className="field-error" role="alert">{commentError}</span>}
                <span className="muted comment-character-count">{comment.length}/5000</span>
                <button type="button" className="btn btn-ghost" disabled={commenting} onClick={() => setShowCommentDialog(false)}>Cancel</button>
                <button className="btn btn-primary" type="submit" disabled={commenting || !comment.trim()}>
                  {commenting ? "Posting…" : "Post comment"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
