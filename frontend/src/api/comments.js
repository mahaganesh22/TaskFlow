import { apiFetch } from "./client";

export function listComments(projectId, taskId) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}/comments`);
}

export function addComment(projectId, taskId, content) {
  return apiFetch(`/api/projects/${projectId}/tasks/${taskId}/comments`, {
    method: "POST",
    body: { content }
  });
}
