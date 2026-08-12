import { FormEvent, useEffect, useState } from "react";
import {
  changePassword,
  createAcademicYear,
  createFeeCategory,
  createFeeStructure,
  createUser,
  getAcademicYears,
  getAuditLogs,
  getCourses,
  getFeeCategories,
  getFeeStructures,
  getNotificationPreferences,
  getSemesters,
  getSystemSettings,
  getUsers,
  resetUserPassword,
  updateAcademicYear,
  updateFeeCategory,
  updateFeeStructure,
  updateNotificationPreferences,
  updateSystemSettings,
  updateUser,
} from "../api/settings";
import type { AcademicYear, Course, FeeCategory, FeeStructure, NotificationPreference, Semester, SystemSettings, User } from "../types";
import { formatDate, formatMoney, titleCase } from "../utils/format";
import { Badge, EmptyState, ErrorState, LoadingState } from "./common";

const tabs = ["General", "Academic Year", "Fee Structure", "Notifications", "Security"] as const;
type Tab = typeof tabs[number];

function inputStyle(): React.CSSProperties {
  return {
    background: "var(--secondary)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "10px 14px",
    color: "var(--foreground)",
    fontSize: 13,
    fontFamily: "inherit",
    outline: "none",
  };
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", letterSpacing: "0.04em" }}>{label}</span>
      {children}
    </label>
  );
}

export default function Settings({ currentUser }: { currentUser: User | null }) {
  const [activeTab, setActiveTab] = useState<Tab>("General");
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<{ id: number; action: string; entity_type: string; description: string; created_at: string; user_name?: string | null }[]>([]);
  const [yearForm, setYearForm] = useState<Partial<AcademicYear>>({ name: "", start_date: "", end_date: "", is_active: true });
  const [categoryForm, setCategoryForm] = useState<Partial<FeeCategory>>({ name: "", description: "", is_active: true });
  const [structureForm, setStructureForm] = useState<Partial<FeeStructure>>({ name: "", total_amount: 0, is_active: true });
  const [userForm, setUserForm] = useState({ name: "", email: "", role: "teacher", password: "" });
  const [passwordForm, setPasswordForm] = useState({ current: "", next: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const isAdmin = currentUser?.role === "admin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [system, prefs, years, courseRows, semesterRows, categoryRows, structureRows] = await Promise.all([
        getSystemSettings(),
        getNotificationPreferences(),
        getAcademicYears(),
        getCourses(),
        getSemesters(),
        getFeeCategories(),
        getFeeStructures(),
      ]);
      setSettings(system);
      setPreferences(prefs);
      setAcademicYears(years.items);
      setCourses(courseRows.items);
      setSemesters(semesterRows.items);
      setCategories(categoryRows.items);
      setStructures(structureRows.items);
      setStructureForm((current) => ({
        ...current,
        course_id: current.course_id || courseRows.items[0]?.id,
        academic_year_id: current.academic_year_id || years.items[0]?.id,
        category_id: current.category_id || categoryRows.items[0]?.id,
      }));
      if (isAdmin) {
        const [usersData, auditData] = await Promise.all([getUsers(), getAuditLogs()]);
        setUsers(usersData.items);
        setAuditLogs(auditData.items);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Settings could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveSystem() {
    if (!settings) return;
    setSaving(true);
    setError("");
    try {
      setSettings(await updateSystemSettings(settings));
      setSaved("System settings saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "System settings could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function saveYear(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (yearForm.id) await updateAcademicYear(yearForm.id, yearForm);
      else await createAcademicYear(yearForm);
      setYearForm({ name: "", start_date: "", end_date: "", is_active: true });
      await load();
      setSaved("Academic year saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Academic year could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function saveCategory(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (categoryForm.id) await updateFeeCategory(categoryForm.id, categoryForm);
      else await createFeeCategory(categoryForm);
      setCategoryForm({ name: "", description: "", is_active: true });
      await load();
      setSaved("Fee category saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fee category could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function saveStructure(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (structureForm.id) await updateFeeStructure(structureForm.id, structureForm);
      else await createFeeStructure(structureForm);
      setStructureForm({ name: "", total_amount: 0, is_active: true, course_id: courses[0]?.id, academic_year_id: academicYears[0]?.id, category_id: categories[0]?.id });
      await load();
      setSaved("Fee structure saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fee structure could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function savePreferences() {
    if (!preferences) return;
    setSaving(true);
    setError("");
    try {
      setPreferences(await updateNotificationPreferences(preferences));
      setSaved("Notification preferences saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Notification preferences could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function createSecurityUser(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createUser({ name: userForm.name, email: userForm.email, role: userForm.role as never, password: userForm.password });
      setUserForm({ name: "", email: "", role: "teacher", password: "" });
      await load();
      setSaved("User created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "User could not be created");
    } finally {
      setSaving(false);
    }
  }

  async function deactivateUser(user: User) {
    setError("");
    try {
      await updateUser(user.id, { is_active: false });
      await load();
      setSaved("User deactivated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "User could not be deactivated");
    }
  }

  async function resetPassword(user: User) {
    const password = window.prompt(`Temporary password for ${user.email}`);
    if (!password) return;
    setError("");
    try {
      await resetUserPassword(user.id, password);
      setSaved("Password reset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password could not be reset");
    }
  }

  async function changeOwnPassword(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await changePassword(passwordForm.current, passwordForm.next);
      setPasswordForm({ current: "", next: "" });
      setSaved("Password changed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password could not be changed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error && !settings) return <div style={{ padding: 24 }}><ErrorState message={error} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", gap: 0, background: "var(--card)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden", alignSelf: "flex-start", flexWrap: "wrap" }}>
        {tabs.map((tab, index) => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{ padding: "9px 20px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, background: activeTab === tab ? "rgba(99,102,241,0.15)" : "transparent", color: activeTab === tab ? "#818CF8" : "var(--muted-foreground)", fontFamily: "inherit", borderRight: index < tabs.length - 1 ? "1px solid var(--border)" : "none" }}>{tab}</button>
        ))}
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {saved && <div style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.24)", color: "#10B981", borderRadius: 10, padding: 12, fontSize: 13 }}>{saved}</div>}

      {activeTab === "General" && settings && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 24, gridColumn: "1 / -1" }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 20 }}>School Information</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 18 }}>
              <Field label="School Name"><input value={settings.school_name} onChange={(event) => setSettings({ ...settings, school_name: event.target.value })} style={inputStyle()} /></Field>
              <Field label="Official Email"><input value={settings.official_email || ""} onChange={(event) => setSettings({ ...settings, official_email: event.target.value })} style={inputStyle()} /></Field>
              <Field label="Phone"><input value={settings.phone || ""} onChange={(event) => setSettings({ ...settings, phone: event.target.value })} style={inputStyle()} /></Field>
              <Field label="Address"><input value={settings.address || ""} onChange={(event) => setSettings({ ...settings, address: event.target.value })} style={inputStyle()} /></Field>
            </div>
          </div>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 24 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 16 }}>Branding</div>
            <Field label="Logo Path"><input value={settings.logo_path || ""} onChange={(event) => setSettings({ ...settings, logo_path: event.target.value })} style={inputStyle()} /></Field>
          </div>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 24 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 16 }}>Preferences</div>
            <div style={{ display: "grid", gap: 14 }}>
              <Field label="Default Academic Year"><select value={settings.default_academic_year_id || ""} onChange={(event) => setSettings({ ...settings, default_academic_year_id: event.target.value ? Number(event.target.value) : null })} style={inputStyle()}><option value="">None</option>{academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}</select></Field>
              <Field label="Currency"><input value={settings.currency} onChange={(event) => setSettings({ ...settings, currency: event.target.value })} style={inputStyle()} /></Field>
              <Field label="Time Zone"><input value={settings.timezone} onChange={(event) => setSettings({ ...settings, timezone: event.target.value })} style={inputStyle()} /></Field>
              <Field label="Language"><input value={settings.language} onChange={(event) => setSettings({ ...settings, language: event.target.value })} style={inputStyle()} /></Field>
            </div>
          </div>
          {isAdmin && <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}><button onClick={saveSystem} disabled={saving} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "10px 22px", cursor: saving ? "not-allowed" : "pointer", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>{saving ? "Saving..." : "Save Changes"}</button></div>}
        </div>
      )}

      {activeTab === "Academic Year" && (
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16 }}>
          {isAdmin && <form onSubmit={saveYear} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22, display: "grid", gap: 14 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>{yearForm.id ? "Edit Academic Year" : "Add Academic Year"}</div>
            <Field label="Name"><input value={yearForm.name || ""} onChange={(event) => setYearForm({ ...yearForm, name: event.target.value })} required style={inputStyle()} /></Field>
            <Field label="Start Date"><input type="date" value={yearForm.start_date || ""} onChange={(event) => setYearForm({ ...yearForm, start_date: event.target.value })} required style={inputStyle()} /></Field>
            <Field label="End Date"><input type="date" value={yearForm.end_date || ""} onChange={(event) => setYearForm({ ...yearForm, end_date: event.target.value })} required style={inputStyle()} /></Field>
            <label style={{ color: "var(--foreground)", fontSize: 13 }}><input type="checkbox" checked={yearForm.is_active ?? true} onChange={(event) => setYearForm({ ...yearForm, is_active: event.target.checked })} /> Active</label>
            <button type="submit" style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>{yearForm.id ? "Save Year" : "Add Year"}</button>
          </form>}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700 }}>Academic Years</div>
            {academicYears.map((year) => (
              <div key={year.id} style={{ display: "grid", gridTemplateColumns: "1fr 150px 90px 130px", gap: 12, padding: "14px 22px", borderBottom: "1px solid var(--border)", alignItems: "center" }}>
                <div><div style={{ fontSize: 13, fontWeight: 700 }}>{year.name}</div><div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{formatDate(year.start_date)} - {formatDate(year.end_date)}</div></div>
                <Badge label={year.is_active ? "Active" : "Inactive"} bg={year.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={year.is_active ? "#10B981" : "#6B7094"} />
                {isAdmin && <button onClick={() => setYearForm(year)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Edit</button>}
                {isAdmin && <button onClick={() => updateAcademicYear(year.id, { is_active: !year.is_active }).then(load)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", color: "var(--foreground)", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>{year.is_active ? "Deactivate" : "Activate"}</button>}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "Fee Structure" && (
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16 }}>
          {isAdmin && <div style={{ display: "grid", gap: 16 }}>
            <form onSubmit={saveCategory} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22, display: "grid", gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Fee Category</div>
              <Field label="Name"><input value={categoryForm.name || ""} onChange={(event) => setCategoryForm({ ...categoryForm, name: event.target.value })} required style={inputStyle()} /></Field>
              <Field label="Description"><input value={categoryForm.description || ""} onChange={(event) => setCategoryForm({ ...categoryForm, description: event.target.value })} style={inputStyle()} /></Field>
              <button type="submit" style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>{categoryForm.id ? "Save Category" : "Add Category"}</button>
            </form>
            <form onSubmit={saveStructure} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22, display: "grid", gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Fee Structure</div>
              <Field label="Name"><input value={structureForm.name || ""} onChange={(event) => setStructureForm({ ...structureForm, name: event.target.value })} required style={inputStyle()} /></Field>
              <Field label="Course"><select value={structureForm.course_id || ""} onChange={(event) => setStructureForm({ ...structureForm, course_id: Number(event.target.value) })} required style={inputStyle()}>{courses.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}</select></Field>
              <Field label="Academic Year"><select value={structureForm.academic_year_id || ""} onChange={(event) => setStructureForm({ ...structureForm, academic_year_id: Number(event.target.value) })} required style={inputStyle()}>{academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}</select></Field>
              <Field label="Semester"><select value={structureForm.semester_id || ""} onChange={(event) => setStructureForm({ ...structureForm, semester_id: event.target.value ? Number(event.target.value) : null })} style={inputStyle()}><option value="">None</option>{semesters.filter((semester) => !structureForm.course_id || semester.course_id === structureForm.course_id).map((semester) => <option key={semester.id} value={semester.id}>{semester.name}</option>)}</select></Field>
              <Field label="Category"><select value={structureForm.category_id || ""} onChange={(event) => setStructureForm({ ...structureForm, category_id: Number(event.target.value) })} required style={inputStyle()}>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></Field>
              <Field label="Amount"><input type="number" min="1" value={String(structureForm.total_amount || "")} onChange={(event) => setStructureForm({ ...structureForm, total_amount: Number(event.target.value) })} required style={inputStyle()} /></Field>
              <button type="submit" style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>{structureForm.id ? "Save Structure" : "Add Structure"}</button>
            </form>
          </div>}
          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700 }}>Categories</div>
              {categories.map((category) => <div key={category.id} style={{ display: "grid", gridTemplateColumns: "1fr 80px 80px", gap: 10, padding: "12px 22px", borderBottom: "1px solid var(--border)", alignItems: "center" }}><div><div style={{ fontSize: 13, fontWeight: 700 }}>{category.name}</div><div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{category.description || "-"}</div></div><Badge label={category.is_active ? "Active" : "Inactive"} bg={category.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={category.is_active ? "#10B981" : "#6B7094"} />{isAdmin && <button onClick={() => setCategoryForm(category)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "5px 10px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Edit</button>}</div>)}
            </div>
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700 }}>Fee Structures</div>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead style={{ borderBottom: "1px solid var(--border)" }}><tr>{["Name", "Course", "Semester", "Category", "Amount", "Status", ""].map((header) => <th key={header} style={{ padding: "10px 18px", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textAlign: "left", textTransform: "uppercase", letterSpacing: "0.06em" }}>{header}</th>)}</tr></thead>
                <tbody>{structures.map((structure) => <tr key={structure.id} style={{ borderBottom: "1px solid var(--border)" }}><td style={{ padding: "13px 18px", fontSize: 13, fontWeight: 700 }}>{structure.name}</td><td style={{ padding: "13px 18px", fontSize: 12 }}>{structure.course_name || "-"}</td><td style={{ padding: "13px 18px", fontSize: 12 }}>{structure.semester_name || "-"}</td><td style={{ padding: "13px 18px", fontSize: 12 }}>{structure.category_name || "-"}</td><td style={{ padding: "13px 18px", fontFamily: "JetBrains Mono, monospace", color: "#10B981" }}>{formatMoney(structure.total_amount)}</td><td style={{ padding: "13px 18px" }}><Badge label={structure.is_active ? "Active" : "Inactive"} bg={structure.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={structure.is_active ? "#10B981" : "#6B7094"} /></td><td>{isAdmin && <button onClick={() => setStructureForm(structure)} style={{ background: "transparent", border: "none", color: "#818CF8", cursor: "pointer", fontSize: 12, fontFamily: "inherit" }}>Edit</button>}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === "Notifications" && preferences && (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 24, maxWidth: 560 }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 18 }}>Notification Preferences</div>
          {[
            ["fee_alerts", "Fee alerts"],
            ["attendance_alerts", "Attendance alerts"],
            ["system_notifications", "System notifications"],
          ].map(([key, label]) => <label key={key} style={{ display: "flex", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid var(--border)", fontSize: 13 }}><span>{label}</span><input type="checkbox" checked={Boolean((preferences as unknown as Record<string, boolean>)[key])} onChange={(event) => setPreferences({ ...preferences, [key]: event.target.checked })} /></label>)}
          <button onClick={savePreferences} style={{ marginTop: 18, background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>Save Preferences</button>
        </div>
      )}

      {activeTab === "Security" && (
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16 }}>
          <div style={{ display: "grid", gap: 16 }}>
            <form onSubmit={changeOwnPassword} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22, display: "grid", gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Change Password</div>
              <Field label="Current Password"><input type="password" value={passwordForm.current} onChange={(event) => setPasswordForm({ ...passwordForm, current: event.target.value })} required style={inputStyle()} /></Field>
              <Field label="New Password"><input type="password" value={passwordForm.next} onChange={(event) => setPasswordForm({ ...passwordForm, next: event.target.value })} required style={inputStyle()} /></Field>
              <button type="submit" style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>Update Password</button>
            </form>
            {isAdmin && <form onSubmit={createSecurityUser} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22, display: "grid", gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Create User</div>
              <Field label="Name"><input value={userForm.name} onChange={(event) => setUserForm({ ...userForm, name: event.target.value })} required style={inputStyle()} /></Field>
              <Field label="Email"><input type="email" value={userForm.email} onChange={(event) => setUserForm({ ...userForm, email: event.target.value })} required style={inputStyle()} /></Field>
              <Field label="Role"><select value={userForm.role} onChange={(event) => setUserForm({ ...userForm, role: event.target.value })} style={inputStyle()}><option value="teacher">Teacher</option><option value="accountant">Accountant</option><option value="admin">Admin</option><option value="staff">Staff</option></select></Field>
              <Field label="Temporary Password"><input type="password" value={userForm.password} onChange={(event) => setUserForm({ ...userForm, password: event.target.value })} required style={inputStyle()} /></Field>
              <button type="submit" style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 18px", color: "#fff", cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>Create User</button>
            </form>}
          </div>
          <div style={{ display: "grid", gap: 16 }}>
            {isAdmin ? <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700 }}>User Management</div>
              {users.map((user) => <div key={user.id} style={{ display: "grid", gridTemplateColumns: "1fr 100px 80px 170px", gap: 10, padding: "12px 22px", borderBottom: "1px solid var(--border)", alignItems: "center" }}><div><div style={{ fontSize: 13, fontWeight: 700 }}>{user.name}</div><div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{user.email}</div></div><div style={{ fontSize: 12 }}>{titleCase(user.role)}</div><Badge label={user.is_active ? "Active" : "Inactive"} bg={user.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={user.is_active ? "#10B981" : "#6B7094"} /><div style={{ display: "flex", gap: 8 }}><button onClick={() => resetPassword(user)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "5px 8px", cursor: "pointer", fontSize: 11 }}>Reset</button><button onClick={() => deactivateUser(user)} disabled={!user.is_active || user.id === currentUser?.id} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#EF4444", borderRadius: 7, padding: "5px 8px", cursor: user.is_active && user.id !== currentUser?.id ? "pointer" : "not-allowed", fontSize: 11 }}>Deactivate</button></div></div>)}
            </div> : <EmptyState>Security user management is available to admins.</EmptyState>}
            {isAdmin && <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 700 }}>Audit / Admin Tools</div>
              {auditLogs.length === 0 ? <EmptyState>No audit log entries.</EmptyState> : auditLogs.map((log) => <div key={log.id} style={{ display: "grid", gridTemplateColumns: "150px 150px 1fr", gap: 12, padding: "12px 22px", borderBottom: "1px solid var(--border)", fontSize: 12 }}><div style={{ color: "var(--muted-foreground)" }}>{formatDate(log.created_at)}</div><div style={{ color: "#818CF8", fontWeight: 700 }}>{titleCase(log.action)}</div><div>{log.description}</div></div>)}
            </div>}
          </div>
        </div>
      )}
    </div>
  );
}
