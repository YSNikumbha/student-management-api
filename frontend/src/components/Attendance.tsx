import { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { getAttendanceData, saveBulkAttendance } from "../api/attendance";
import { getStudentsData } from "../api/students";
import type { AttendanceData, AttendanceStatus, ClassRoom, StudentRow, User } from "../types";
import { attendanceStatusColors, avatarFor, titleCase, todayISO } from "../utils/format";
import { Badge, EmptyState, ErrorState, LoadingState } from "./common";

const statuses: AttendanceStatus[] = ["present", "absent", "late", "excused"];

const TooltipStyle = {
  contentStyle: { background: "#131620", border: "1px solid #1E2235", borderRadius: 8, fontSize: 12, color: "#E8EAF0" },
  labelStyle: { color: "#6B7094" },
};

function AttendanceMarkModal({
  date,
  cls,
  students,
  onClose,
  onSaved,
}: {
  date: string;
  cls: ClassRoom;
  students: StudentRow[];
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const classStudents = students.filter((student) => student.classId === cls.id);
  const [records, setRecords] = useState<Record<number, { status: AttendanceStatus; remarks: string }>>(
    Object.fromEntries(classStudents.map((student) => [student.id, { status: "present", remarks: "" }]))
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function markAll(status: AttendanceStatus) {
    setRecords(Object.fromEntries(classStudents.map((student) => [student.id, { status, remarks: records[student.id]?.remarks || "" }])));
  }

  function clearAll() {
    setRecords(Object.fromEntries(classStudents.map((student) => [student.id, { status: "absent", remarks: "" }])));
  }

  async function save() {
    setSaving(true);
    setError("");
    try {
      await saveBulkAttendance(cls.id, date, classStudents.map((student) => ({
        student_id: student.id,
        status: records[student.id]?.status || "present",
        remarks: records[student.id]?.remarks || null,
      })));
      await onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Attendance could not be saved");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <div onClick={(event) => event.stopPropagation()} style={{ background: "#131620", border: "1px solid var(--border)", borderRadius: 16, width: 820, maxHeight: "85vh", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "22px 28px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)" }}>Mark Attendance</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>{cls.name} · {date}</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => markAll("present")} style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.2)", color: "#10B981", borderRadius: 7, padding: "6px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit" }}>All Present</button>
            <button onClick={clearAll} style={{ background: "var(--secondary)", border: "1px solid var(--border)", color: "var(--muted-foreground)", borderRadius: 7, padding: "6px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit" }}>Clear All</button>
            <button onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 7, padding: "6px 10px", cursor: "pointer", color: "var(--muted-foreground)", fontFamily: "inherit" }}>x</button>
          </div>
        </div>
        {error && <div style={{ margin: "14px 28px 0", color: "#FCA5A5", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: 8, padding: 10, fontSize: 12 }}>{error}</div>}
        <div style={{ overflowY: "auto", flex: 1 }}>
          {classStudents.length === 0 ? <EmptyState>No students are assigned to this class.</EmptyState> : classStudents.map((student) => (
            <div key={student.id} style={{ display: "grid", gridTemplateColumns: "220px 1fr 190px", alignItems: "center", gap: 14, padding: "12px 28px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--secondary)", overflow: "hidden", flexShrink: 0 }}>
                  <img src={student.avatar || avatarFor(student.name)} alt={student.name} style={{ width: "100%", height: "100%" }} />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{student.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.rollNo}</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {statuses.map((status) => (
                  <button key={status} onClick={() => setRecords((current) => ({ ...current, [student.id]: { ...current[student.id], status } }))} style={{
                    padding: "4px 10px", borderRadius: 7, border: "1px solid",
                    borderColor: records[student.id]?.status === status ? attendanceStatusColors[status].text : "var(--border)",
                    background: records[student.id]?.status === status ? attendanceStatusColors[status].bg : "transparent",
                    color: records[student.id]?.status === status ? attendanceStatusColors[status].text : "var(--muted-foreground)",
                    cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit",
                  }}>{titleCase(status)}</button>
                ))}
              </div>
              <input value={records[student.id]?.remarks || ""} onChange={(event) => setRecords((current) => ({ ...current, [student.id]: { ...current[student.id], remarks: event.target.value } }))} placeholder="Remarks" style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 10px", color: "var(--foreground)", fontSize: 12, fontFamily: "inherit", outline: "none" }} />
            </div>
          ))}
        </div>
        <div style={{ padding: "16px 28px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 20px", cursor: "pointer", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>Cancel</button>
          <button onClick={save} disabled={saving || classStudents.length === 0} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 22px", cursor: saving ? "not-allowed" : "pointer", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>{saving ? "Saving..." : "Save Attendance"}</button>
        </div>
      </div>
    </div>
  );
}

export default function Attendance({ currentUser }: { currentUser: User | null }) {
  const [selectedDate, setSelectedDate] = useState(todayISO());
  const [filterClass, setFilterClass] = useState<number | "all">("all");
  const [data, setData] = useState<AttendanceData | null>(null);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showMarkModal, setShowMarkModal] = useState(false);
  const [activeTab, setActiveTab] = useState<"daily" | "summary" | "trends">("daily");
  const canEdit = ["admin", "teacher", "staff"].includes(String(currentUser?.role));

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [attendanceData, studentsData] = await Promise.all([getAttendanceData(selectedDate, filterClass), getStudentsData()]);
      setData(attendanceData);
      setStudents(studentsData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Attendance could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [selectedDate, filterClass]);

  const selectedClass = useMemo(() => {
    if (!data?.classes.length) return null;
    if (filterClass === "all") return data.classes[0];
    return data.classes.find((cls) => cls.id === filterClass) || null;
  }, [data, filterClass]);

  const classSummary = useMemo(() => {
    if (!data) return [];
    return data.classes.map((cls) => {
      const records = data.records.filter((record) => record.classId === cls.id);
      const total = records.length || 1;
      return {
        class: cls.name,
        present: Math.round((records.filter((record) => record.status === "present").length / total) * 100),
        absent: Math.round((records.filter((record) => record.status === "absent").length / total) * 100),
      };
    });
  }, [data]);

  const trendData = useMemo(() => (data?.trends || []).map((item) => {
    const total = (item.present || 0) + (item.absent || 0) + (item.late || 0) + (item.excused || 0);
    return { month: item.month, rate: total ? Math.round(((item.present || 0) / total) * 100) : 0 };
  }), [data]);

  if (loading) return <LoadingState />;
  if (error && !data) return <div style={{ padding: 24 }}><ErrorState message={error} onRetry={load} /></div>;

  const counts = data?.summary || { present: 0, absent: 0, late: 0, excused: 0 };
  const total = statuses.reduce((sum, status) => sum + (counts[status] || 0), 0);

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      {showMarkModal && selectedClass && <AttendanceMarkModal date={selectedDate} cls={selectedClass} students={students} onClose={() => setShowMarkModal(false)} onSaved={load} />}
      {error && <ErrorState message={error} onRetry={load} />}

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit", cursor: "pointer", outline: "none" }} />
        <select value={filterClass} onChange={(event) => setFilterClass(event.target.value === "all" ? "all" : Number(event.target.value))} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit", cursor: "pointer", outline: "none" }}>
          <option value="all">All Classes</option>
          {data?.classes.map((cls) => <option key={cls.id} value={cls.id}>{cls.name}</option>)}
        </select>
        <div style={{ display: "flex", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          {(["daily", "summary", "trends"] as const).map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{ padding: "8px 16px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, background: activeTab === tab ? "rgba(99,102,241,0.15)" : "transparent", color: activeTab === tab ? "#818CF8" : "var(--muted-foreground)", fontFamily: "inherit", textTransform: "capitalize", borderRight: tab !== "trends" ? "1px solid var(--border)" : "none" }}>{tab}</button>
          ))}
        </div>
        {canEdit && <button disabled={!selectedClass} onClick={() => setShowMarkModal(true)} style={{ marginLeft: "auto", background: "#6366F1", border: "none", borderRadius: 8, padding: "8px 20px", cursor: selectedClass ? "pointer" : "not-allowed", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>+ Mark Attendance</button>}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
        {statuses.map((status) => {
          const value = counts[status] || 0;
          const color = attendanceStatusColors[status].text;
          return (
            <div key={status} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>{titleCase(status)}</div>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
                <span style={{ fontSize: 28, fontWeight: 800, color, fontFamily: "JetBrains Mono, monospace" }}>{value}</span>
                <span style={{ fontSize: 13, color: "var(--muted-foreground)", marginBottom: 4 }}>{total ? Math.round((value / total) * 100) : 0}%</span>
              </div>
            </div>
          );
        })}
      </div>

      {activeTab === "daily" && (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "16px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>Attendance for {selectedDate}</div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead style={{ borderBottom: "1px solid var(--border)" }}>
                <tr>{["Student", "Roll No", "Class", "Status", "Note"].map((header) => <th key={header} style={{ padding: "10px 16px", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textAlign: "left", textTransform: "uppercase", letterSpacing: "0.06em" }}>{header}</th>)}</tr>
              </thead>
              <tbody>
                {data?.records.length === 0 ? (
                  <tr><td colSpan={5}><EmptyState>No records for this date/class combination.</EmptyState></td></tr>
                ) : data?.records.map((record, index) => {
                  const colors = attendanceStatusColors[String(record.status).toLowerCase()] || attendanceStatusColors.absent;
                  return (
                    <tr key={record.id} style={{ borderBottom: index < (data?.records.length || 0) - 1 ? "1px solid var(--border)" : "none" }}>
                      <td style={{ padding: "11px 16px", fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{record.studentName}</td>
                      <td style={{ padding: "11px 16px", fontSize: 12, color: "var(--muted-foreground)", fontFamily: "JetBrains Mono, monospace" }}>{record.rollNo}</td>
                      <td style={{ padding: "11px 16px", fontSize: 13, color: "var(--foreground)" }}>{record.className || "-"}</td>
                      <td style={{ padding: "11px 16px" }}><Badge {...colors} label={titleCase(String(record.status))} /></td>
                      <td style={{ padding: "11px 16px", fontSize: 12, color: "var(--muted-foreground)" }}>{record.note || "-"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "summary" && (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 20 }}>Class-wise Summary · {selectedDate}</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={classSummary} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
              <XAxis dataKey="class" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip {...TooltipStyle} formatter={(value) => [`${Number(value)}%`, ""]} />
              <Bar dataKey="present" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={32} name="Present %" />
              <Bar dataKey="absent" fill="#EF4444" radius={[4, 4, 0, 0]} maxBarSize={32} name="Absent %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {activeTab === "trends" && (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 20 }}>Attendance Rate Trend</div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
              <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
              <Tooltip {...TooltipStyle} formatter={(value) => [`${Number(value)}%`, "Attendance Rate"]} />
              <Line type="monotone" dataKey="rate" stroke="#6366F1" strokeWidth={2.5} dot={{ fill: "#6366F1", r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
