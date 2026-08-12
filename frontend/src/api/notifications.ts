import { apiRequest } from "./client";
import type { NotificationItem, PaginatedResponse } from "../types";

export function getNotifications(): Promise<PaginatedResponse<NotificationItem>> {
  return apiRequest<PaginatedResponse<NotificationItem>>("/notifications?page=1&page_size=8");
}

export function getUnreadCount(): Promise<{ unread_count: number }> {
  return apiRequest<{ unread_count: number }>("/notifications/unread-count");
}

export function markNotificationRead(id: number): Promise<NotificationItem> {
  return apiRequest<NotificationItem>(`/notifications/${id}/read`, { method: "PUT" });
}

export function markAllNotificationsRead(): Promise<{ updated: number }> {
  return apiRequest<{ updated: number }>("/notifications/read-all", { method: "PUT" });
}
