import { FormEvent, useEffect, useMemo, useState } from "react";
import { createUser, deactivateUser, getUsers, resetUserPassword, updateUser } from "../api/users";
import { getRolesPermissions } from "../api/rolesPermissions";
import type { RoleRecord, User } from "../types";
import { formatDate, initials, titleCase } from "../utils/format";
import { Badge, ErrorState, LoadingState } from "./common";

type ModalMode = "view" | "add" | "edit";

function inputStyle(): React.CSSProperties {
  return {
    background: "var(--secondary)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "10px 12px",
    color: "var(--foreground)",
    fontSize: 13,
    fontFamily: "inherit",
    outline: "none",
  };
}

function actionStyle(color = "#818CF8"): React.CSSProperties {
  return {
    background: "rgba(99,102,241,0.1)",
    border: "1px solid rgba(99,102,241,0.2)",
    color,
    borderRadius: 7,
    padding: "6px 9px",
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 700,
    fontFamily: "inherit",
  };
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase" }}>{label}</span>
      {children}
    </label>
  );
}

export default function UserManagement({ currentUser }: { currentUser: User | null }) {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<RoleRecord[]>([]);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState<"" | "active" | "inactive">("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [modalMode, setModalMode] = useState<ModalMode | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [form, setForm] = useState({ name: "", email: "", role: "teacher", role_id: "", password: "", is_active: true });

  const activeRoles = roles.filter((item) => item.is_active);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [userRows, roleRows] = await Promise.all([
        getUsers({ search, role, is_active: status === "" ? "" : status === "active" }),
        getRolesPermissions(),
      ]);
      setUsers(userRows.items);
      setRoles(roleRows.roles);
      const defaultRole = roleRows.roles.find((item) => item.name === "teacher") || roleRows.roles[0];
      if (defaultRole && !form.role_id) {
        setForm((current) => ({ ...current, role: defaultRole.name, role_id: String(defaultRole.id) }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Users could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    return {
      total: users.length,
      active: users.filter((item) => item.is_active).length,
      teachers: users.filter((item) => item.role === "teacher").length,
      accountants: users.filter((item) => item.role === "accountant").length,
      admins: users.filter((item) => item.role === "admin" || item.role === "super_admin").length,
    };
  }, [users]);

  function openAdd() {
    const defaultRole = activeRoles.find((item) => item.name === "teacher") || activeRoles[0];
    setSelectedUser(null);
    setForm({ name: "", email: "", role: defaultRole?.name || "teacher", role_id: defaultRole ? String(defaultRole.id) : "", password: "", is_active: true });
    setModalMode("add");
  }

  function openEdit(user: User) {
    const matchedRole = roles.find((item) => item.id === user.role_id || item.name === user.role);
    setSelectedUser(user);
    setForm({ name: user.name, email: user.email, role: matchedRole?.name || user.role, role_id: matchedRole ? String(matchedRole.id) : "", password: "", is_active: user.is_active });
    setModalMode("edit");
  }

  async function saveUser(event: FormEvent) {
    event.preventDefault();
    if (modalMode === "add" && form.password.length < 8) {
      setError("Temporary password must be at least 8 characters");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const selectedRole = roles.find((item) => item.id === Number(form.role_id));
      if (modalMode === "add") {
        await createUser({
          name: form.name,
          email: form.email,
          role: selectedRole?.name || form.role,
          role_id: form.role_id ? Number(form.role_id) : undefined,
          password: form.password,
          is_active: form.is_active,
        });
        setSaved("User created");
      } else if (selectedUser) {
        await updateUser(selectedUser.id, {
          name: form.name,
          email: form.email,
          role: selectedRole?.name || form.role,
          role_id: form.role_id ? Number(form.role_id) : undefined,
          is_active: form.is_active,
        });
        setSaved("User updated");
      }
      setModalMode(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "User could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(user: User) {
    if (user.id === currentUser?.id) {
      setError("You cannot deactivate your own account");
      return;
    }
    setError("");
    try {
      if (user.is_active) await deactivateUser(user.id);
      else await updateUser(user.id, { is_active: true });
      setSaved(user.is_active ? "User deactivated" : "User activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status could not be updated");
    }
  }

  async function resetPassword(user: User) {
    const password = window.prompt(`Temporary password for ${user.email}`);
    if (!password) return;
    if (password.length < 8) {
      setError("Temporary password must be at least 8 characters");
      return;
    }
    try {
      await resetUserPassword(user.id, password);
      setSaved("Password reset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password could not be reset");
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div style={{ padding: 24, display: "grid", gap: 18 }}>
      {error && <ErrorState message={error} onRetry={load} />}
      {saved && <div style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.24)", color: "#10B981", borderRadius: 10, padding: 12, fontSize: 13 }}>{saved}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 14 }}>
        {[
          ["TOTAL USERS", stats.total],
          ["ACTIVE USERS", stats.active],
          ["TEACHERS", stats.teachers],
          ["ACCOUNTANTS", stats.accountants],
          ["ADMINS", stats.admins],
        ].map(([label, value]) => (
          <div key={String(label)} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 18 }}>
            <div style={{ fontSize: 11, color: "var(--muted-foreground)", fontWeight: 800 }}>{label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#818CF8", marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <input placeholder="Search name or email" value={search} onChange={(event) => setSearch(event.target.value)} style={{ ...inputStyle(), minWidth: 240 }} />
        <select value={role} onChange={(event) => setRole(event.target.value)} style={inputStyle()}>
          <option value="">All Roles</option>
          {roles.map((item) => <option key={item.id} value={item.name}>{item.display_name}</option>)}
        </select>
        <select value={status} onChange={(event) => setStatus(event.target.value as "" | "active" | "inactive")} style={inputStyle()}>
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button onClick={load} style={{ background: "#6366F1", border: "none", color: "#fff", borderRadius: 8, padding: "10px 16px", fontWeight: 800, fontFamily: "inherit", cursor: "pointer" }}>Search</button>
        <button onClick={openAdd} style={{ marginLeft: "auto", background: "#10B981", border: "none", color: "#06120D", borderRadius: 8, padding: "10px 16px", fontWeight: 800, fontFamily: "inherit", cursor: "pointer" }}>+ Add User</button>
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{["USER", "EMAIL", "ROLE", "STATUS", "LAST LOGIN", "CREATED", "ACTIONS"].map((header) => <th key={header} style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, color: "var(--muted-foreground)", letterSpacing: "0.06em" }}>{header}</th>)}</tr></thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "13px 16px" }}><div style={{ display: "flex", alignItems: "center", gap: 10 }}><div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#6366F1,#818CF8)", color: "#fff", display: "grid", placeItems: "center", fontSize: 12, fontWeight: 800 }}>{initials(user.name)}</div><span style={{ fontWeight: 700, fontSize: 13 }}>{user.name}</span></div></td>
                <td style={{ padding: "13px 16px", fontSize: 12, color: "var(--muted-foreground)" }}>{user.email}</td>
                <td style={{ padding: "13px 16px", fontSize: 12 }}>{user.role_display_name || titleCase(user.role)}</td>
                <td style={{ padding: "13px 16px" }}><Badge label={user.is_active ? "Active" : "Inactive"} bg={user.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={user.is_active ? "#10B981" : "#6B7094"} /></td>
                <td style={{ padding: "13px 16px", fontSize: 12 }}>{user.last_login_at ? formatDate(user.last_login_at) : "-"}</td>
                <td style={{ padding: "13px 16px", fontSize: 12 }}>{formatDate(user.created_at)}</td>
                <td style={{ padding: "13px 16px" }}><div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}><button onClick={() => { setSelectedUser(user); setModalMode("view"); }} style={actionStyle()}>View</button><button onClick={() => openEdit(user)} style={actionStyle()}>Edit</button><button onClick={() => resetPassword(user)} style={actionStyle("#38BDF8")}>Reset</button><button onClick={() => toggleActive(user)} disabled={user.id === currentUser?.id} style={{ ...actionStyle(user.is_active ? "#EF4444" : "#10B981"), opacity: user.id === currentUser?.id ? 0.45 : 1, cursor: user.id === currentUser?.id ? "not-allowed" : "pointer" }}>{user.is_active ? "Deactivate" : "Activate"}</button></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalMode && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.62)", display: "grid", placeItems: "center", zIndex: 20, padding: 20 }}>
          <div style={{ width: "min(620px, 100%)", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>{modalMode === "add" ? "Add User" : modalMode === "edit" ? "Edit User" : "User Details"}</div>
              <button onClick={() => setModalMode(null)} style={{ background: "transparent", border: "none", color: "var(--muted-foreground)", cursor: "pointer", fontSize: 18 }}>x</button>
            </div>
            {modalMode === "view" && selectedUser ? (
              <div style={{ display: "grid", gap: 12, fontSize: 13 }}>
                {[
                  ["Name", selectedUser.name],
                  ["Email", selectedUser.email],
                  ["Role", selectedUser.role_display_name || titleCase(selectedUser.role)],
                  ["Status", selectedUser.is_active ? "Active" : "Inactive"],
                  ["Created", formatDate(selectedUser.created_at)],
                  ["Last Login", selectedUser.last_login_at ? formatDate(selectedUser.last_login_at) : "-"],
                  ["Permissions", (selectedUser.permissions || []).join(", ") || "-"],
                ].map(([label, value]) => <div key={label} style={{ display: "grid", gridTemplateColumns: "130px 1fr", gap: 12 }}><span style={{ color: "var(--muted-foreground)" }}>{label}</span><span>{value}</span></div>)}
              </div>
            ) : (
              <form onSubmit={saveUser} style={{ display: "grid", gap: 14 }}>
                <Field label="Name"><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required style={inputStyle()} /></Field>
                <Field label="Email"><input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required style={inputStyle()} /></Field>
                <Field label="Role"><select value={form.role_id} onChange={(event) => { const selected = roles.find((item) => item.id === Number(event.target.value)); setForm({ ...form, role_id: event.target.value, role: selected?.name || form.role }); }} required style={inputStyle()}>{activeRoles.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></Field>
                {modalMode === "add" && <Field label="Temporary Password"><input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required minLength={8} style={inputStyle()} /></Field>}
                <Field label="Status"><select value={form.is_active ? "active" : "inactive"} onChange={(event) => setForm({ ...form, is_active: event.target.value === "active" })} style={inputStyle()}><option value="active">Active</option><option value="inactive">Inactive</option></select></Field>
                <button disabled={saving} type="submit" style={{ justifySelf: "end", background: "#6366F1", border: "none", color: "#fff", borderRadius: 8, padding: "10px 18px", fontWeight: 800, fontFamily: "inherit", cursor: saving ? "not-allowed" : "pointer" }}>{saving ? "Saving..." : "Save User"}</button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
