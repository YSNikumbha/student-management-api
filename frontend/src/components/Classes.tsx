import { FormEvent, useEffect, useMemo, useState } from "react";
import { createClass, deleteClass, getClassesData, updateClass } from "../api/classes";
import { getStudentsData } from "../api/students";
import { getAcademicYears, getCourses, getSemesters, getUsers } from "../api/settings";
import type { AcademicYear, ClassFormInput, ClassRoom, Course, Semester, StudentRow, User } from "../types";
import { avatarFor, titleCase } from "../utils/format";
import { EmptyState, ErrorState, LoadingState } from "./common";

function ClassModal({ cls, students, onClose }: { cls: ClassRoom; students: StudentRow[]; onClose: () => void }) {
  const classStudents = students.filter((student) => student.classId === cls.id);
  const avgGpa = classStudents.length ? classStudents.reduce((sum, student) => sum + student.gpa, 0) / classStudents.length : 0;

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <div onClick={(event) => event.stopPropagation()} style={{ background: "#131620", border: "1px solid var(--border)", borderRadius: 16, width: 640, maxHeight: "85vh", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "24px 28px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "var(--foreground)" }}>{cls.name}</div>
            <div style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Room {cls.room || "-"} · {cls.schedule || "-"}</div>
          </div>
          <button onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", cursor: "pointer", color: "var(--muted-foreground)", fontFamily: "inherit" }}>x</button>
        </div>

        <div style={{ padding: "20px 28px", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, borderBottom: "1px solid var(--border)" }}>
          {[
            { label: "Students", value: classStudents.length, color: "#818CF8" },
            { label: "Average GPA", value: avgGpa.toFixed(2), color: "#10B981" },
            { label: "Semester", value: cls.grade || "-", color: "#38BDF8" },
          ].map((stat) => (
            <div key={stat.label} style={{ background: "var(--secondary)", borderRadius: 10, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>{stat.label}</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: stat.color, fontFamily: "JetBrains Mono, monospace" }}>{stat.value}</div>
            </div>
          ))}
        </div>

        <div style={{ padding: "16px 28px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Class Teacher</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 38, height: 38, borderRadius: "50%", background: "linear-gradient(135deg, #6366F1, #818CF8)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: "#fff" }}>
              {(cls.teacher || "U").charAt(0)}
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>{cls.teacher || "Unassigned"}</div>
              <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>{cls.program || "Program"} · {cls.grade || "Semester"}</div>
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          <div style={{ padding: "14px 28px 8px", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Students ({classStudents.length})</div>
          {classStudents.length === 0 ? <EmptyState>No students assigned to this class.</EmptyState> : classStudents.slice(0, 20).map((student, index) => (
            <div key={student.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 28px", borderBottom: index < classStudents.length - 1 ? "1px solid var(--border)" : "none" }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", overflow: "hidden", background: "var(--secondary)", flexShrink: 0 }}>
                <img src={student.avatar || avatarFor(student.name)} alt={student.name} style={{ width: "100%", height: "100%" }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{student.name}</div>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.rollNo}</div>
              </div>
              <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 99, background: student.gpa >= 3.5 ? "rgba(16,185,129,0.12)" : student.gpa >= 3.0 ? "rgba(56,189,248,0.12)" : "rgba(245,158,11,0.12)", color: student.gpa >= 3.5 ? "#10B981" : student.gpa >= 3.0 ? "#38BDF8" : "#F59E0B", fontFamily: "JetBrains Mono, monospace" }}>
                {student.gpa.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ClassFormModal({
  cls,
  courses,
  academicYears,
  semesters,
  teachers,
  onClose,
  onSave,
}: {
  cls?: ClassRoom;
  courses: Course[];
  academicYears: AcademicYear[];
  semesters: Semester[];
  teachers: User[];
  onClose: () => void;
  onSave: (data: ClassFormInput) => Promise<void>;
}) {
  const [form, setForm] = useState<ClassFormInput>(() => ({
    name: cls?.name || "",
    course_id: cls?.course_id || courses[0]?.id || 0,
    academic_year_id: cls?.academic_year_id || academicYears[0]?.id || 0,
    semester_id: cls?.semester_id || null,
    class_teacher_id: cls?.class_teacher_id || null,
    section: cls?.section || "",
    room: cls?.room || "",
    schedule: cls?.schedule || "",
    is_active: cls?.is_active ?? true,
  }));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Class could not be saved");
    } finally {
      setSaving(false);
    }
  }

  function setField<K extends keyof ClassFormInput>(key: K, value: ClassFormInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <form onSubmit={submit} onClick={(event) => event.stopPropagation()} style={{ width: 680, background: "#131620", border: "1px solid var(--border)", borderRadius: 16 }}>
        <div style={{ padding: "22px 26px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--foreground)" }}>{cls ? "Edit Class" : "Add Class"}</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>Course, semester, room and teacher assignment</div>
          </div>
          <button type="button" onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", color: "var(--muted-foreground)", cursor: "pointer" }}>x</button>
        </div>
        <div style={{ padding: 26, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Class Name</span>
            <input value={form.name} onChange={(event) => setField("name", event.target.value)} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Section</span>
            <input value={form.section || ""} onChange={(event) => setField("section", event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Course</span>
            <select value={form.course_id} onChange={(event) => setField("course_id", Number(event.target.value))} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
              <option value="">Select course</option>
              {courses.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Academic Year</span>
            <select value={form.academic_year_id} onChange={(event) => setField("academic_year_id", Number(event.target.value))} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
              <option value="">Select academic year</option>
              {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Semester</span>
            <select value={form.semester_id || ""} onChange={(event) => setField("semester_id", event.target.value ? Number(event.target.value) : null)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
              <option value="">None</option>
              {semesters.filter((semester) => !form.course_id || semester.course_id === form.course_id).map((semester) => <option key={semester.id} value={semester.id}>{semester.name}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Teacher</span>
            <select value={form.class_teacher_id || ""} onChange={(event) => setField("class_teacher_id", event.target.value ? Number(event.target.value) : null)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
              <option value="">Unassigned</option>
              {teachers.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.name} · {titleCase(teacher.role)}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Room</span>
            <input value={form.room || ""} onChange={(event) => setField("room", event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Schedule</span>
            <input value={form.schedule || ""} onChange={(event) => setField("schedule", event.target.value)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
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

export default function Classes({ currentUser }: { currentUser: User | null }) {
  const [classes, setClasses] = useState<ClassRoom[]>([]);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [teachers, setTeachers] = useState<User[]>([]);
  const [selectedClass, setSelectedClass] = useState<ClassRoom | null>(null);
  const [editingClass, setEditingClass] = useState<ClassRoom | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const canManage = currentUser?.role === "admin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [classesData, studentsData, coursesData, yearsData, semestersData] = await Promise.all([
        getClassesData(),
        getStudentsData(),
        getCourses(),
        getAcademicYears(),
        getSemesters(),
      ]);
      setClasses(classesData.items);
      setStudents(studentsData.items);
      setCourses(coursesData.items);
      setAcademicYears(yearsData.items);
      setSemesters(semestersData.items);
      if (currentUser?.role === "admin") {
        const users = await getUsers();
        setTeachers(users.items.filter((user) => ["teacher", "staff", "admin"].includes(String(user.role))));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Classes could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => classes.filter((cls) =>
    cls.name.toLowerCase().includes(search.toLowerCase()) ||
    (cls.teacher || "").toLowerCase().includes(search.toLowerCase()) ||
    (cls.program || "").toLowerCase().includes(search.toLowerCase())
  ), [classes, search]);

  async function saveClass(form: ClassFormInput) {
    if (editingClass) await updateClass(editingClass.id, form);
    else await createClass(form);
    setEditingClass(null);
    setShowCreate(false);
    await load();
  }

  async function removeClass(cls: ClassRoom) {
    if (!window.confirm(`Delete class ${cls.name}?`)) return;
    try {
      await deleteClass(cls.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Class could not be deleted");
    }
  }

  if (loading) return <LoadingState />;
  if (error && classes.length === 0) return <div style={{ padding: 24 }}><ErrorState message={error} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      {selectedClass && <ClassModal cls={selectedClass} students={students} onClose={() => setSelectedClass(null)} />}
      {(showCreate || editingClass) && <ClassFormModal cls={editingClass || undefined} courses={courses} academicYears={academicYears} semesters={semesters} teachers={teachers} onClose={() => { setShowCreate(false); setEditingClass(null); }} onSave={saveClass} />}
      {error && <ErrorState message={error} onRetry={load} />}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
        {[
          { label: "Total Classes", value: classes.length, color: "#818CF8" },
          { label: "Total Students", value: classes.reduce((sum, cls) => sum + cls.student_count, 0), color: "#10B981" },
          { label: "Semesters", value: new Set(classes.map((cls) => cls.grade).filter(Boolean)).size, color: "#38BDF8" },
          { label: "Avg Class Size", value: classes.length ? Math.round(classes.reduce((sum, cls) => sum + cls.student_count, 0) / classes.length) : 0, color: "#F59E0B" },
        ].map((card) => (
          <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
            <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: card.color, marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search classes or teachers..." style={{ flex: 1, background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit", outline: "none" }} />
        {canManage && <button onClick={() => setShowCreate(true)} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 22px", cursor: "pointer", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>+ Add Class</button>}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
        {filtered.length === 0 ? <div style={{ gridColumn: "1 / -1" }}><EmptyState>No classes match the current search.</EmptyState></div> : filtered.map((cls, index) => {
          const accent = ["#6366F1", "#10B981", "#38BDF8", "#F59E0B", "#818CF8", "#EF4444", "#A78BFA", "#34D399"][index % 8];
          return (
            <div key={cls.id} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 14, overflow: "hidden", transition: "border-color 0.15s, transform 0.15s" }}>
              <div style={{ height: 6, background: `linear-gradient(90deg, ${accent}, ${accent}88)` }} />
              <div style={{ padding: "18px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: "var(--foreground)", letterSpacing: "-0.01em" }}>{cls.name}</div>
                    <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>{cls.program || "Course"} · Room {cls.room || "-"}</div>
                  </div>
                  <div style={{ background: `${accent}20`, border: `1px solid ${accent}40`, borderRadius: 8, padding: "4px 10px", fontSize: 11, fontWeight: 700, color: accent }}>
                    {cls.grade || "Semester"}{cls.section ? ` ${cls.section}` : ""}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                  <div style={{ width: 26, height: 26, borderRadius: "50%", background: `${accent}30`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: accent }}>{(cls.teacher || "U").charAt(0)}</div>
                  <span style={{ fontSize: 12.5, color: "var(--foreground)", fontWeight: 500 }}>{cls.teacher || "Unassigned"}</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                  {[
                    { label: "Students", value: cls.student_count },
                    { label: "Avg GPA", value: cls.average_gpa.toFixed(2) },
                    { label: "Section", value: cls.section || "-" },
                  ].map((stat) => (
                    <div key={stat.label} style={{ background: "var(--secondary)", borderRadius: 8, padding: "8px 10px" }}>
                      <div style={{ fontSize: 10, color: "var(--muted-foreground)", letterSpacing: "0.05em" }}>{stat.label}</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", fontFamily: "JetBrains Mono, monospace", marginTop: 2 }}>{stat.value}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 14, fontSize: 11, color: "var(--muted-foreground)" }}>{cls.schedule || "Schedule not set"}</div>
                <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                  <button onClick={() => setSelectedClass(cls)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>View</button>
                  {canManage && <button onClick={() => setEditingClass(cls)} style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)", color: "#38BDF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Edit</button>}
                  {canManage && <button onClick={() => removeClass(cls)} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#EF4444", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Delete</button>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
