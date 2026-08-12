import { apiRequest } from "./client";
import type { StudentFormInput, StudentsData } from "../types";

export function getStudentsData(): Promise<StudentsData> {
  return apiRequest<StudentsData>("/ui/students");
}

export function createStudent(data: StudentFormInput) {
  return apiRequest("/students", { method: "POST", json: data });
}

export function updateStudent(id: number, data: Partial<StudentFormInput>) {
  return apiRequest(`/students/${id}`, { method: "PUT", json: data });
}

export function deleteStudent(id: number) {
  return apiRequest<void>(`/students/${id}`, { method: "DELETE" });
}
