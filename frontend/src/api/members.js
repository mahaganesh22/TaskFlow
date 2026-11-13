import { apiFetch } from "./client";

export function listMembers(projectId) {
  return apiFetch(`/api/projects/${projectId}/members`);
}

export function listInviteCandidates(projectId) {
  return apiFetch(`/api/projects/${projectId}/members/invite-candidates`);
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

export function listMyJoinRequests() {
  return apiFetch("/api/join-requests/me");
}

export function respondToJoinRequest(requestId, action) {
  return apiFetch(`/api/join-requests/${requestId}/respond`, {
    method: "POST",
    body: { action }
  });
}
