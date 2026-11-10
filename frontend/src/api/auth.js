import { apiFetch } from "./client";

export function register(payload) {
  return apiFetch("/api/auth/register", {
    method: "POST",
    body: payload,
    auth: false
  });
}

export function login(payload) {
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: payload,
    auth: false
  });
}

export function logout(refreshToken) {
  return apiFetch("/api/auth/logout", {
    method: "POST",
    body: { refresh_token: refreshToken },
    auth: false,
    retry: false
  });
}

export function deleteAccount() {
  return apiFetch("/api/auth/account", {
    method: "DELETE"
  });
}
