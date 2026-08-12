import { apiRequest } from "./client";
import type { DashboardData } from "../types";

export function getDashboardData(): Promise<DashboardData> {
  return apiRequest<DashboardData>("/ui/dashboard");
}
