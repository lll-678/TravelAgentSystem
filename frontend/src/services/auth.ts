import { reactive } from "vue";

import type { AuthPayload, UserProfileItem } from "./api";

const TOKEN_KEY = "smart-tour-token";
const USER_KEY = "smart-tour-user";
const initialToken = localStorage.getItem(TOKEN_KEY) ?? "";
const initialUser = readStoredUser();

export type UserRole = "user" | "admin";

interface AuthState {
  token: string;
  user: UserProfileItem | null;
  role: UserRole | "";
}

export const authState = reactive<AuthState>({
  token: initialToken,
  user: initialToken ? initialUser : null,
  role: initialToken ? initialUser?.role ?? "" : "",
});

export function applyAuthPayload(payload: AuthPayload) {
  authState.token = payload.access_token;
  authState.user = payload.user;
  authState.role = payload.role;
  localStorage.setItem(TOKEN_KEY, payload.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
}

export function updateAuthUser(user: UserProfileItem) {
  authState.user = user;
  authState.role = user.role;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  authState.token = "";
  authState.user = null;
  authState.role = "";
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAdmin() {
  return authState.role === "admin" && Boolean(authState.token);
}

function readStoredUser(): UserProfileItem | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as UserProfileItem;
    return parsed.role === "admin" || parsed.role === "user" ? parsed : null;
  } catch {
    return null;
  }
}
