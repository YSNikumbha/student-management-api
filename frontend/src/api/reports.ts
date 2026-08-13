import { apiRequest, downloadAuthenticatedFile } from "./client";
import type { ReportFilters, ReportsData } from "../types";

function reportQuery(filters: ReportFilters = {}): string {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

function exportQuery(kind: "academic" | "attendance" | "fees" | "courses" | "students" | "top-performers", filters: ReportFilters = {}): string {
  const exportFilters: Record<string, unknown> = { ...filters };
  if (kind === "attendance" && filters.attendance_status) exportFilters.status = filters.attendance_status;
  if (kind === "fees" && filters.fee_status) exportFilters.status = filters.fee_status;
  delete exportFilters.attendance_status;
  delete exportFilters.fee_status;
  const query = new URLSearchParams();
  Object.entries(exportFilters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

export function getReportsData(filters: ReportFilters = {}): Promise<ReportsData> {
  const query = reportQuery(filters);
  return apiRequest<ReportsData>(`/ui/reports${query ? `?${query}` : ""}`);
}

export function downloadReport(
  kind: "academic" | "attendance" | "fees" | "courses" | "students" | "top-performers",
  format: "csv" | "pdf",
  filters: ReportFilters = {},
) {
  const query = exportQuery(kind, filters);
  return downloadAuthenticatedFile(
    `/reports/${kind}/export/${format}${query ? `?${query}` : ""}`,
    `${kind}_report.${format}`,
  );
}
