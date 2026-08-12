import { apiRequest, clearSession, setStoredUser, setToken } from "./client";
import type { User } from "../types";

type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export async function login(email: string, password: string): Promise<User> {
  const response = await apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    json: { email, password },
  });
  setToken(response.access_token);
  setStoredUser(response.user);
  return response.user;
}

export async function getMe(): Promise<User> {
  const user = await apiRequest<User>("/auth/me");
  setStoredUser(user);
  return user;
}

export function logout(): void {
  clearSession();
}
