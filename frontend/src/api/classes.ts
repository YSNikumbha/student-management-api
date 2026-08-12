import { apiRequest } from "./client";
import type { ClassFormInput, ClassRoom, ClassesData } from "../types";

export function getClassesData(): Promise<ClassesData> {
  return apiRequest<ClassesData>("/ui/classes");
}

export function getClasses(): Promise<ClassRoom[]> {
  return apiRequest<ClassRoom[]>("/classes");
}

export function createClass(data: ClassFormInput): Promise<ClassRoom> {
  return apiRequest<ClassRoom>("/classes", { method: "POST", json: data });
}

export function updateClass(id: number, data: Partial<ClassFormInput>): Promise<ClassRoom> {
  return apiRequest<ClassRoom>(`/classes/${id}`, { method: "PUT", json: data });
}

export function deleteClass(id: number): Promise<void> {
  return apiRequest<void>(`/classes/${id}`, { method: "DELETE" });
}
