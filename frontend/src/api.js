// Thin fetch wrapper around the read-only backend API.
// All requests are same-origin /api/* (Vite proxies to FastAPI :8000).
import { getToken, clearSession } from "./auth";

const BASE = "/api";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { Accept: "application/json" };
  const authToken = token !== undefined ? token : getToken();
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  if (body) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearSession();
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? detail;
    } catch {
      /* non-json body */
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: { email, password }, token: null }),
  me: () => request("/auth/me"),

  // Trainee domain (read)
  trainees: (token) => request("/trainees", { token }),
  trainee: (id, token) => request(`/trainees/${id}`, { token }),
  traineeSelf: (token) => request("/trainees/me", { token }),
  traineeEmployment: (id, token) => request(`/trainees/${id}/employment`, { token }),

  // Training domain (read)
  providers: (token) => request("/providers", { token }),
  programs: (token) => request("/programs", { token }),
  employment: (token) => request("/employment", { token }),

  // Analytics (admin only)
  employmentAnalytics: (token) => request("/analytics/employment", { token }),
  skillGap: (token) => request("/analytics/skill-gap", { token }),
  programImpact: (token) => request("/analytics/program-impact", { token }),
};