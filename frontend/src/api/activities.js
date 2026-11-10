import { apiFetch } from "./client";

export function listActivities(projectId, params = {}) {
  const search = new URLSearchParams();

  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));

  const qs = search.toString();
  return apiFetch(
    `/api/projects/${projectId}/activities${qs ? `?${qs}` : ""}`
  );
}
