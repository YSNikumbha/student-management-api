import { apiRequest, downloadAuthenticatedFile } from "./client";
import type { ReportsData } from "../types";

export function getReportsData(): Promise<ReportsData> {
  return apiRequest<ReportsData>("/ui/reports");
}

export function downloadReport(kind: "students" | "attendance" | "fees" | "courses", format: "csv" | "pdf") {
  return downloadAuthenticatedFile(`/reports/${kind}/export/${format}`, `${kind}_report.${format}`);
}
