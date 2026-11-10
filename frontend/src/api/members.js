import { apiFetch } from "./client";

export function listMembers(projectId) {
  return apiFetch(`/api/projects/${projectId}/members`);
}

export function inviteMember(projectId, email) {
  return apiFetch(`/api/projects/${projectId}/members`, {
    method: "POST",
    body: { email }
  });
}

export function removeMember(projectId, userId) {
  return apiFetch(`/api/projects/${projectId}/members/${userId}`, {
    method: "DELETE"
  });
}
