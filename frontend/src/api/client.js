const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(status, detail, body) {
    super(formatDetail(detail) || "Request failed");
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.body = body;
  }
}

async function fetchApi(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    throw new ApiError(
      0,
      "Could not connect to the TaskFlow server. Check your connection and try again."
    );
  }
}

export function formatDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || item.message || "")
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

export function fieldErrorsFromDetail(detail) {
  const errors = {};

  if (!Array.isArray(detail)) return errors;

  for (const item of detail) {
    const loc = item.loc || [];
    const field = loc[loc.length - 1];
    if (typeof field === "string" && field !== "body") {
      errors[field] = item.msg || "Invalid value";
    }
  }

  return errors;
}

const auth = {
  getAccessToken: () => localStorage.getItem("tf_access_token"),
  persistSession: null,
  clearSession: null
};

export function configureAuth(nextAuth) {
  Object.assign(auth, nextAuth);
}

let refreshInFlight = null;

export async function refreshAccessToken() {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refreshToken = localStorage.getItem("tf_refresh_token");

    if (!refreshToken) {
      auth.clearSession?.();
      return null;
    }

    const response = await fetchApi(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      auth.clearSession?.();
      return null;
    }

    const data = await response.json();
    auth.persistSession?.(data);
    return data.access_token;
  })().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}

export async function apiFetch(path, options = {}) {
  const {
    method = "GET",
    body,
    auth: useAuth = true,
    retry = true
  } = options;

  const headers = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (useAuth) {
    const token = auth.getAccessToken?.();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetchApi(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined
  });

  if (response.status === 401 && useAuth && retry) {
    const nextToken = await refreshAccessToken();
    if (nextToken) {
      return apiFetch(path, { ...options, retry: false });
    }
  }

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, data?.detail ?? data, data);
  }

  return data;
}
