import { apiRequest } from "./client";
import type {
  AcademicYear,
  Course,
  FeeCategory,
  FeeStructure,
  NotificationPreference,
  PaginatedResponse,
  Semester,
  SystemSettings,
  User,
  UserFormInput,
} from "../types";

export function getSystemSettings(): Promise<SystemSettings> {
  return apiRequest<SystemSettings>("/settings/system");
}

export function updateSystemSettings(data: Partial<SystemSettings>): Promise<SystemSettings> {
  return apiRequest<SystemSettings>("/settings/system", { method: "PUT", json: data });
}

export function getNotificationPreferences(): Promise<NotificationPreference> {
  return apiRequest<NotificationPreference>("/settings/notification-preferences");
}

export function updateNotificationPreferences(data: Partial<NotificationPreference>): Promise<NotificationPreference> {
  return apiRequest<NotificationPreference>("/settings/notification-preferences", { method: "PUT", json: data });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
  return apiRequest<{ message: string }>("/settings/change-password", {
    method: "POST",
    json: { current_password: currentPassword, new_password: newPassword },
  });
}

export function getAcademicYears(): Promise<PaginatedResponse<AcademicYear>> {
  return apiRequest<PaginatedResponse<AcademicYear>>("/academic-years?page=1&page_size=100");
}

export function createAcademicYear(data: Partial<AcademicYear>): Promise<AcademicYear> {
  return apiRequest<AcademicYear>("/academic-years", { method: "POST", json: data });
}

export function updateAcademicYear(id: number, data: Partial<AcademicYear>): Promise<AcademicYear> {
  return apiRequest<AcademicYear>(`/academic-years/${id}`, { method: "PUT", json: data });
}

export function getCourses(): Promise<PaginatedResponse<Course>> {
  return apiRequest<PaginatedResponse<Course>>("/courses?page=1&page_size=100");
}

export function getSemesters(): Promise<PaginatedResponse<Semester>> {
  return apiRequest<PaginatedResponse<Semester>>("/semesters?page=1&page_size=100");
}

export function getFeeCategories(): Promise<PaginatedResponse<FeeCategory>> {
  return apiRequest<PaginatedResponse<FeeCategory>>("/fees/categories?page=1&page_size=100");
}

export function getFeeStructures(): Promise<PaginatedResponse<FeeStructure>> {
  return apiRequest<PaginatedResponse<FeeStructure>>("/fees/structures?page=1&page_size=100");
}

export function createFeeCategory(data: Partial<FeeCategory>): Promise<FeeCategory> {
  return apiRequest<FeeCategory>("/fees/categories", { method: "POST", json: data });
}

export function updateFeeCategory(id: number, data: Partial<FeeCategory>): Promise<FeeCategory> {
  return apiRequest<FeeCategory>(`/fees/categories/${id}`, { method: "PUT", json: data });
}

export function createFeeStructure(data: Partial<FeeStructure>): Promise<FeeStructure> {
  return apiRequest<FeeStructure>("/fees/structures", { method: "POST", json: data });
}

export function updateFeeStructure(id: number, data: Partial<FeeStructure>): Promise<FeeStructure> {
  return apiRequest<FeeStructure>(`/fees/structures/${id}`, { method: "PUT", json: data });
}

export function getUsers(): Promise<PaginatedResponse<User>> {
  return apiRequest<PaginatedResponse<User>>("/users?page=1&page_size=100");
}

export function createUser(data: UserFormInput): Promise<User> {
  return apiRequest<User>("/users", { method: "POST", json: data });
}

export function updateUser(id: number, data: Partial<UserFormInput> & { is_active?: boolean }): Promise<User> {
  return apiRequest<User>(`/users/${id}`, { method: "PUT", json: data });
}

export function resetUserPassword(id: number, newPassword: string): Promise<User> {
  return apiRequest<User>(`/users/${id}/reset-password`, {
    method: "POST",
    json: { new_password: newPassword },
  });
}

export function getAuditLogs(): Promise<PaginatedResponse<{
  id: number;
  user_id?: number | null;
  user_name?: string | null;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  description: string;
  created_at: string;
}>> {
  return apiRequest("/audit-logs?page=1&page_size=20");
}
