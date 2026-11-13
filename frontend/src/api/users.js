import { apiFetch } from "./client";

export function getMyProfile() {
  return apiFetch("/api/users/me/profile");
}

export function updateMyProfile(payload) {
  return apiFetch("/api/users/me/profile", { method: "PATCH", body: payload });
}

export function getProjectUserProfile(projectId, userId) {
  return apiFetch(`/api/users/projects/${projectId}/profiles/${userId}`);
}
