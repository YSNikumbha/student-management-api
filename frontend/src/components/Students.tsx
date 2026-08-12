import { FormEvent, useEffect, useMemo, useState } from "react";
import { createStudent, deleteStudent, getStudentsData, updateStudent } from "../api/students";
import { getClassesData } from "../api/classes";
import type { ClassRoom, StudentFormInput, StudentRow, StudentsData, User } from "../types";
import {
  avatarFor,
  feeStatusColors,
  formatDate,
  studentStatusColors,
  titleCase,
} from "../utils/format";
import { Badge, EmptyState, ErrorState, LoadingState } from "./common";

type SortKey = keyof Pick<StudentRow, "name" | "rollNo" | "gpa" | "enrolledDate">;

function splitName(name: string): { first_name: string; last_name: string } {
  const parts = name.trim().split(/\s+/);
  return {
    first_name: parts[0] || "",
    last_name: parts.slice(1).join(" ") || "Student",
  };
}

function studentToForm(student: StudentRow): StudentFormInput {
  const names = splitName(student.name);
  return {
    student_code: student.rollNo,
    first_name: names.first_name,
    last_name: names.last_name,
    email: student.email,
    phone: student.phone || null,
    date_of_birth: student.dob || null,
    profile_photo: student.avatar || null,
    gender: student.gender || null,
    address: student.address || null,
    parent_name: student.parentName || null,
    parent_phone: student.parentPhone || null,
    blood_group: student.bloodGroup || null,
    course_id: student.courseId || null,
    batch_id: student.classId || null,
    admission_date: student.enrolledDate || null,
    status: student.status as StudentFormInput["status"],
  };
}

function StudentModal({ student, onClose }: { student: StudentRow; onClose: () => void }) {
  const statusColors = studentStatusColors[String(student.status).toLowerCase()] || studentStatusColors.inactive;
  const feeColors = feeStatusColors[String(student.feeStatus).toLowerCase()] || feeStatusColors.pending;
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)",
      zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
    }} onClick={onClose}>
      <div onClick={(event) => event.stopPropagation()} style={{
        background: "#131620", border: "1px solid var(--border)", borderRadius: 16,
        width: 640, maxHeight: "90vh", overflowY: "auto",
      }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 16, padding: "24px 28px",
          borderBottom: "1px solid var(--border)",
        }}>
          <div style={{ width: 60, height: 60, borderRadius: "50%", background: "var(--secondary)", border: "2px solid var(--border)", overflow: "hidden", flexShrink: 0 }}>
            <img src={student.avatar || avatarFor(student.name)} alt={student.name} style={{ width: "100%", height: "100%" }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "var(--foreground)" }}>{student.name}</div>
            <div style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>{student.rollNo} · {student.className || "-"}</div>
          </div>
          <Badge {...statusColors} label={titleCase(String(student.status))} />
          <button onClick={onClose} style={{
            background: "var(--secondary)", border: "1px solid var(--border)",
            borderRadius: 8, padding: "6px 10px", cursor: "pointer", color: "var(--muted-foreground)", fontSize: 14,
          }}>x</button>
        </div>

        <div style={{ padding: "24px 28px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {[
            ["Email", student.email],
            ["Phone", student.phone],
            ["Date of Birth", formatDate(student.dob)],
            ["Gender", student.gender],
            ["Blood Group", student.bloodGroup],
            ["Address", student.address],
            ["Parent / Guardian", student.parentName],
            ["Parent Phone", student.parentPhone],
            ["Enrolled Date", formatDate(student.enrolledDate)],
            ["GPA", student.gpa.toFixed(2)],
          ].map(([label, value]) => (
            <div key={label as string}>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)", fontWeight: 500, marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
              <div style={{ fontSize: 13.5, color: "var(--foreground)", fontWeight: 500 }}>{value || "-"}</div>
            </div>
          ))}
        </div>

        <div style={{ padding: "0 28px 24px", display: "flex", gap: 10 }}>
          <Badge {...feeColors} label={`Fee: ${titleCase(String(student.feeStatus))}`} />
          <Badge bg="rgba(99,102,241,0.12)" text="#818CF8" label={`GPA: ${student.gpa.toFixed(2)}`} />
        </div>
      </div>
    </div>
  );
}

function StudentFormModal({
  student,
  classes,
  onClose,
  onSave,
}: {
  student?: StudentRow;
  classes: ClassRoom[];
  onClose: () => void;
  onSave: (data: StudentFormInput) => Promise<void>;
}) {
  const [form, setForm] = useState<StudentFormInput>(() => student ? studentToForm(student) : {
    student_code: "",
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    batch_id: classes[0]?.id ?? null,
    course_id: classes[0]?.course_id ?? null,
    academic_year_id: classes[0]?.academic_year_id ?? null,
    semester_id: classes[0]?.semester_id ?? null,
    admission_date: new Date().toISOString().slice(0, 10),
    status: "active",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function setField<K extends keyof StudentFormInput>(key: K, value: StudentFormInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleClassChange(classId: string) {
    const selected = classes.find((item) => item.id === Number(classId));
    setForm((current) => ({
      ...current,
      batch_id: selected?.id ?? null,
      course_id: selected?.course_id ?? null,
      academic_year_id: selected?.academic_year_id ?? null,
      semester_id: selected?.semester_id ?? null,
    }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Student could not be saved");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <form onSubmit={submit} onClick={(event) => event.stopPropagation()} style={{ width: 720, maxHeight: "90vh", overflowY: "auto", background: "#131620", border: "1px solid var(--border)", borderRadius: 16 }}>
        <div style={{ padding: "22px 26px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--foreground)" }}>{student ? "Edit Student" : "Add Student"}</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>Student profile and class assignment</div>
          </div>
          <button type="button" onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", color: "var(--muted-foreground)", cursor: "pointer" }}>x</button>
        </div>

        <div style={{ padding: 26, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[
            ["Roll No", "student_code"],
            ["First Name", "first_name"],
            ["Last Name", "last_name"],
            ["Email", "email"],
            ["Phone", "phone"],
            ["Date of Birth", "date_of_birth"],
            ["Gender", "gender"],
            ["Blood Group", "blood_group"],
            ["Parent Name", "parent_name"],
            ["Parent Phone", "parent_phone"],
            ["Admission Date", "admission_date"],
          ].map(([label, key]) => (
            <label key={key} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>{label}</span>
              <input
                type={key.includes("date") ? "date" : key === "email" ? "email" : "text"}
                value={String((form as Record<string, unknown>)[key] ?? "")}
                onChange={(event) => setField(key as keyof StudentFormInput, event.target.value as never)}
                required={["student_code", "first_name", "last_name", "email"].includes(key)}
                style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit", outline: "none" }}
              />
            </label>
          ))}
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Class</span>
            <select value={form.batch_id ?? ""} onChange={(event) => handleClassChange(event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit", outline: "none" }}>
              <option value="">Unassigned</option>
              {classes.map((cls) => <option key={cls.id} value={cls.id}>{cls.name}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Status</span>
            <select value={form.status || "active"} onChange={(event) => setField("status", event.target.value as StudentFormInput["status"])} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit", outline: "none" }}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="transferred">Transferred</option>
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6, gridColumn: "1 / -1" }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Address</span>
            <input value={form.address || ""} onChange={(event) => setField("address", event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit", outline: "none" }} />
          </label>
          {error && <div style={{ gridColumn: "1 / -1", color: "#FCA5A5", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: 8, padding: 10, fontSize: 12 }}>{error}</div>}
        </div>

        <div style={{ padding: "16px 26px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button type="button" onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 18px", color: "var(--foreground)", cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
          <button type="submit" disabled={saving} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 20px", color: "#fff", cursor: saving ? "not-allowed" : "pointer", fontWeight: 700, fontFamily: "inherit" }}>{saving ? "Saving..." : "Save"}</button>
        </div>
      </form>
    </div>
  );
}

export default function Students({ currentUser }: { currentUser: User | null }) {
  const [data, setData] = useState<StudentsData | null>(null);
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterClass, setFilterClass] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterFee, setFilterFee] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState<StudentRow | null>(null);
  const [editingStudent, setEditingStudent] = useState<StudentRow | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [page, setPage] = useState(1);
  const perPage = 12;
  const canManage = currentUser?.role === "admin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [studentsData, classesData] = await Promise.all([getStudentsData(), getClassesData()]);
      setData(studentsData);
      setClasses(classesData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Students could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const items = data?.items || [];
    return [...items].filter((student) => {
      const q = search.toLowerCase();
      return (
        (student.name.toLowerCase().includes(q) || student.rollNo.toLowerCase().includes(q) || student.email.toLowerCase().includes(q)) &&
        (filterClass === "all" || String(student.classId) === filterClass) &&
        (filterStatus === "all" || String(student.status).toLowerCase() === filterStatus) &&
        (filterFee === "all" || String(student.feeStatus).toLowerCase() === filterFee)
      );
    }).sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      if (typeof av === "number" && typeof bv === "number") return sortAsc ? av - bv : bv - av;
      return 0;
    });
  }, [data, filterClass, filterFee, filterStatus, search, sortAsc, sortKey]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const paged = filtered.slice((page - 1) * perPage, page * perPage);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  }

  async function saveStudent(form: StudentFormInput) {
    if (editingStudent) await updateStudent(editingStudent.id, form);
    else await createStudent(form);
    setEditingStudent(null);
    setShowCreate(false);
    await load();
  }

  async function removeStudent(student: StudentRow) {
    if (!window.confirm(`Delete ${student.name}?`)) return;
    try {
      await deleteStudent(student.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Student could not be deleted");
    }
  }

  const Th = ({ label, k }: { label: string; k?: SortKey }) => (
    <th style={{
      padding: "10px 14px", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)",
      textAlign: "left", letterSpacing: "0.06em", textTransform: "uppercase",
      cursor: k ? "pointer" : "default", whiteSpace: "nowrap", userSelect: "none",
    }} onClick={() => k && toggleSort(k)}>
      {label}{k && sortKey === k ? (sortAsc ? " ↑" : " ↓") : ""}
    </th>
  );

  if (loading) return <LoadingState />;
  if (error && !data) return <div style={{ padding: 24 }}><ErrorState message={error} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      {selectedStudent && <StudentModal student={selectedStudent} onClose={() => setSelectedStudent(null)} />}
      {(showCreate || editingStudent) && <StudentFormModal student={editingStudent || undefined} classes={classes} onClose={() => { setShowCreate(false); setEditingStudent(null); }} onSave={saveStudent} />}
      {error && <ErrorState message={error} onRetry={load} />}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
        {[
          { label: "Total Students", value: data?.summary.total_students ?? 0, color: "#818CF8" },
          { label: "Active", value: data?.summary.active ?? 0, color: "#10B981" },
          { label: "Fee Overdue", value: data?.summary.fee_overdue ?? 0, color: "#EF4444" },
          { label: "Avg GPA", value: (data?.summary.avg_gpa ?? 0).toFixed(2), color: "#38BDF8" },
        ].map((card) => (
          <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 20px" }}>
            <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: card.color, marginTop: 4, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 20px", display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search by name, roll no, email..." style={{ flex: 1, minWidth: 220, background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit", outline: "none" }} />
        <select value={filterClass} onChange={(event) => setFilterClass(event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>
          <option value="all">All Classes</option>
          {classes.map((cls) => <option key={cls.id} value={cls.id}>{cls.name}</option>)}
        </select>
        <select value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="transferred">Transferred</option>
        </select>
        <select value={filterFee} onChange={(event) => setFilterFee(event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>
          <option value="all">All Fees</option>
          <option value="paid">Paid</option>
          <option value="partial">Partial</option>
          <option value="overdue">Overdue</option>
          <option value="pending">Pending</option>
        </select>
        {canManage && <button onClick={() => setShowCreate(true)} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "8px 18px", cursor: "pointer", color: "#fff", fontSize: 13, fontWeight: 700, fontFamily: "inherit" }}>+ Add Student</button>}
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ borderBottom: "1px solid var(--border)" }}>
              <tr>
                <Th label="Student" k="name" />
                <Th label="Roll No" k="rollNo" />
                <Th label="Class" />
                <Th label="GPA" k="gpa" />
                <Th label="Fee Status" />
                <Th label="Status" />
                <Th label="Enrolled" k="enrolledDate" />
                <Th label="Action" />
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr><td colSpan={8}><EmptyState>No students match the current filters.</EmptyState></td></tr>
              ) : paged.map((student, i) => {
                const feeColors = feeStatusColors[String(student.feeStatus).toLowerCase()] || feeStatusColors.pending;
                const statusColors = studentStatusColors[String(student.status).toLowerCase()] || studentStatusColors.inactive;
                return (
                  <tr key={student.id} style={{ borderBottom: i < paged.length - 1 ? "1px solid var(--border)" : "none" }}>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 32, height: 32, borderRadius: "50%", overflow: "hidden", background: "var(--secondary)", border: "1px solid var(--border)", flexShrink: 0 }}>
                          <img src={student.avatar || avatarFor(student.name)} alt={student.name} style={{ width: "100%", height: "100%" }} />
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)", whiteSpace: "nowrap" }}>{student.name}</div>
                          <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.email}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--muted-foreground)" }}>{student.rollNo}</td>
                    <td style={{ padding: "12px 14px", fontSize: 13, color: "var(--foreground)" }}>{student.className || "-"}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 13, fontWeight: 600, color: student.gpa >= 3.5 ? "#10B981" : student.gpa >= 3.0 ? "#38BDF8" : student.gpa >= 2.0 ? "#F59E0B" : "#EF4444" }}>{student.gpa.toFixed(2)}</td>
                    <td style={{ padding: "12px 14px" }}><Badge {...feeColors} label={titleCase(String(student.feeStatus))} /></td>
                    <td style={{ padding: "12px 14px" }}><Badge {...statusColors} label={titleCase(String(student.status))} /></td>
                    <td style={{ padding: "12px 14px", fontSize: 12, color: "var(--muted-foreground)", fontFamily: "JetBrains Mono, monospace" }}>{formatDate(student.enrolledDate)}</td>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button onClick={() => setSelectedStudent(student)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>View</button>
                        {canManage && <button onClick={() => setEditingStudent(student)} style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)", color: "#38BDF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Edit</button>}
                        {canManage && <button onClick={() => removeStudent(student)} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#EF4444", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Delete</button>}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 20px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Showing {filtered.length ? (page - 1) * perPage + 1 : 0}-{Math.min(page * perPage, filtered.length)} of {filtered.length}</div>
          <div style={{ display: "flex", gap: 6 }}>
            {Array.from({ length: totalPages }, (_, i) => i + 1).slice(Math.max(0, page - 3), page + 2).map((p) => (
              <button key={p} onClick={() => setPage(p)} style={{ width: 30, height: 30, borderRadius: 7, border: "1px solid", borderColor: p === page ? "#6366F1" : "var(--border)", background: p === page ? "rgba(99,102,241,0.15)" : "transparent", color: p === page ? "#818CF8" : "var(--muted-foreground)", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>{p}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
