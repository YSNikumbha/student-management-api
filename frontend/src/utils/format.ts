import type { AttendanceStatus, FeeStatus, StudentStatus } from "../types";

export function formatMoney(value: number | string | null | undefined): string {
  const amount = Number(value ?? 0);
  return `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function titleCase(value: string | null | undefined): string {
  if (!value) return "-";
  return value
    .replace(/_/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

export function initials(name: string | null | undefined): string {
  const parts = (name || "U").split(/\s+/).filter(Boolean);
  return parts.slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "U";
}

export function avatarFor(name: string): string {
  const encoded = encodeURIComponent(name || "Student");
  return `https://api.dicebear.com/7.x/initials/svg?seed=${encoded}&backgroundColor=6366f1,818cf8&fontFamily=Arial&fontWeight=700`;
}

export const studentStatusColors: Record<string, { bg: string; text: string }> = {
  active: { bg: "rgba(16,185,129,0.12)", text: "#10B981" },
  inactive: { bg: "rgba(107,112,148,0.15)", text: "#6B7094" },
  transferred: { bg: "rgba(245,158,11,0.12)", text: "#F59E0B" },
};

export const feeStatusColors: Record<string, { bg: string; text: string }> = {
  paid: { bg: "rgba(16,185,129,0.12)", text: "#10B981" },
  partial: { bg: "rgba(245,158,11,0.12)", text: "#F59E0B" },
  overdue: { bg: "rgba(239,68,68,0.12)", text: "#EF4444" },
  pending: { bg: "rgba(107,112,148,0.15)", text: "#6B7094" },
  unpaid: { bg: "rgba(107,112,148,0.15)", text: "#6B7094" },
};

export const attendanceStatusColors: Record<string, { bg: string; text: string }> = {
  present: { bg: "rgba(16,185,129,0.12)", text: "#10B981" },
  absent: { bg: "rgba(239,68,68,0.12)", text: "#EF4444" },
  late: { bg: "rgba(245,158,11,0.12)", text: "#F59E0B" },
  excused: { bg: "rgba(56,189,248,0.12)", text: "#38BDF8" },
};

export function normalizeStudentStatus(value: string): StudentStatus {
  return value.toLowerCase() as StudentStatus;
}

export function normalizeFeeStatus(value: string): FeeStatus {
  const normalized = value.toLowerCase();
  return (normalized === "unpaid" ? "pending" : normalized) as FeeStatus;
}

export function normalizeAttendanceStatus(value: string): AttendanceStatus {
  return value.toLowerCase() as AttendanceStatus;
}
