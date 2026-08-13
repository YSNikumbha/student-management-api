import { apiRequest } from "./client";
import type { RoleRecord, RolesPermissionsData } from "../types";

export function getRolesPermissions(): Promise<RolesPermissionsData> {
  return apiRequest<RolesPermissionsData>("/roles-permissions");
}

export function createRole(data: {
  name: string;
  display_name: string;
  description?: string | null;
  is_active?: boolean;
  permission_codes?: string[];
}): Promise<RoleRecord> {
  return apiRequest<RoleRecord>("/roles-permissions/roles", { method: "POST", json: data });
}

export function updateRole(id: number, data: Partial<Pick<RoleRecord, "name" | "display_name" | "description" | "is_active">>): Promise<RoleRecord> {
  return apiRequest<RoleRecord>(`/roles-permissions/roles/${id}`, { method: "PUT", json: data });
}

export function updateRolePermissions(id: number, permissionCodes: string[]): Promise<RoleRecord> {
  return apiRequest<RoleRecord>(`/roles-permissions/roles/${id}/permissions`, {
    method: "PUT",
    json: { permission_codes: permissionCodes },
  });
}

export function deactivateRole(id: number): Promise<RoleRecord> {
  return apiRequest<RoleRecord>(`/roles-permissions/roles/${id}/deactivate`, { method: "PATCH" });
}

export function activateRole(id: number): Promise<RoleRecord> {
  return apiRequest<RoleRecord>(`/roles-permissions/roles/${id}/activate`, { method: "PATCH" });
}
