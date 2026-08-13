import { apiRequest } from "./client";
import type { PaginatedResponse, User, UserFormInput } from "../types";

export type UserListParams = {
  search?: string;
  role?: string;
  is_active?: boolean | "";
};

function queryString(params: Record<string, string | number | boolean | undefined | "">): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

export function getUsers(params: UserListParams = {}): Promise<PaginatedResponse<User>> {
  const query = queryString({ ...params, page: 1, page_size: 100 });
  return apiRequest<PaginatedResponse<User>>(`/users?${query}`);
}

export function getUser(id: number): Promise<User> {
  return apiRequest<User>(`/users/${id}`);
}

export function createUser(data: UserFormInput): Promise<User> {
  return apiRequest<User>("/users", { method: "POST", json: data });
}

export function updateUser(id: number, data: Partial<UserFormInput> & { is_active?: boolean }): Promise<User> {
  return apiRequest<User>(`/users/${id}`, { method: "PUT", json: data });
}

export function deactivateUser(id: number): Promise<User> {
  return apiRequest<User>(`/users/${id}/deactivate`, { method: "PATCH" });
}

export function activateUser(id: number): Promise<User> {
  return apiRequest<User>(`/users/${id}/activate`, { method: "PATCH" });
}

export function resetUserPassword(id: number, newPassword: string): Promise<User> {
  return apiRequest<User>(`/users/${id}/reset-password`, {
    method: "POST",
    json: { new_password: newPassword },
  });
}
