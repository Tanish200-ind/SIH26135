// Token / session persistence. Uses localStorage so a refresh keeps the login.
const TOKEN_KEY = "sih26135_token";
const ROLE_KEY = "sih26135_role";
const EMAIL_KEY = "sih26135_email";

export function saveSession({ access_token, role, email }) {
  localStorage.setItem(TOKEN_KEY, access_token || "");
  localStorage.setItem(ROLE_KEY, role || "");
  localStorage.setItem(EMAIL_KEY, email || "");
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || null;
}

export function getRole() {
  return localStorage.getItem(ROLE_KEY) || null;
}

export function getEmail() {
  return localStorage.getItem(EMAIL_KEY) || null;
}

export function isAuthed() {
  return Boolean(getToken());
}