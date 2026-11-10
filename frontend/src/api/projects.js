import { apiFetch } from "./client";

export function listProjects() {
  return apiFetch("/api/projects");
}

export function getProject(projectId) {
  return apiFetch(`/api/projects/${projectId}`);
}

export function createProject(payload) {
  return apiFetch("/api/projects", {
    method: "POST",
    body: payload
  });
}

export function updateProject(projectId, payload) {
  return apiFetch(`/api/projects/${projectId}`, {
    method: "PUT",
    body: payload
  });
}

export function deleteProject(projectId) {
  return apiFetch(`/api/projects/${projectId}`, {
    method: "DELETE"
  });
}

export function transferOwnership(projectId, newOwnerId) {
  return apiFetch(`/api/projects/${projectId}/transfer-ownership`, {
    method: "PUT",
    body: { new_owner_id: newOwnerId }
  });
}
