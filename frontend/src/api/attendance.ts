import { apiRequest } from "./client";
import type { AttendanceData, AttendanceStatus } from "../types";

export function getAttendanceData(selectedDate: string, classId?: number | "all"): Promise<AttendanceData> {
  const params = new URLSearchParams({ selected_date: selectedDate });
  if (classId && classId !== "all") params.set("class_id", String(classId));
  return apiRequest<AttendanceData>(`/ui/attendance?${params.toString()}`);
}

export function saveBulkAttendance(
  classId: number,
  date: string,
  records: { student_id: number; status: AttendanceStatus; remarks?: string | null }[],
) {
  return apiRequest<{ created: number; updated: number }>("/ui/attendance/mark", {
    method: "POST",
    json: { class_id: classId, date, records },
  });
}
