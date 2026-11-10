import { apiFetch } from "./client";

function toQuery(params) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function listProjectTasks(projectId, params = {}) {
  return apiFetch(`/api/projects/${projectId}/tasks${toQuery(params)}`);
}

export function getTask(projectId, taskId) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}`);
}

export function createTask(projectId, payload) {
  return apiFetch(`/api/projects/${projectId}/tasks`, {
    method: "POST",
    body: payload
  });
}

export function updateTask(projectId, taskId, payload) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH",
    body: payload
  });
}

export function assignTask(projectId, taskId, assigneeId) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}/assignee`, {
    method: "PATCH",
    body: { assignee_id: assigneeId }
  });
}

export function updateTaskStatus(projectId, taskId, status) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}/status`, {
    method: "PATCH",
    body: { status }
  });
}

export function deleteTask(projectId, taskId) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}`, {
    method: "DELETE"
  });
}

export function listAssignedTasks(params = {}) {
  return apiFetch(`/api/tasks/assigned-to-me${toQuery(params)}`);
}

export async function listAllProjectTasks(projectId, params = {}) {
  const items = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const page = await listProjectTasks(projectId, {
      ...params,
      limit,
      offset
    });

    items.push(...page.items);

    if (items.length >= page.total || page.items.length === 0) {
      break;
    }

    offset += limit;
  }

  return items;
}
