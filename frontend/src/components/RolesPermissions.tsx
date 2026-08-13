import { FormEvent, useEffect, useMemo, useState } from "react";
import { activateRole, createRole, deactivateRole, getRolesPermissions, updateRole, updateRolePermissions } from "../api/rolesPermissions";
import type { Permission, RoleRecord } from "../types";
import { Badge, ErrorState, LoadingState } from "./common";

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

function buttonStyle(bg = "#6366F1", color = "#fff"): React.CSSProperties {
  return {
    background: bg,
    border: bg === "var(--secondary)" ? "1px solid var(--border)" : "none",
    color,
    borderRadius: 8,
    padding: "9px 14px",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 800,
    fontFamily: "inherit",
  };
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 11, fontWeight: 800, color: "var(--muted-foreground)", textTransform: "uppercase" }}>{label}</span>
      {children}
    </label>
  );
}

export default function RolesPermissions() {
  const [roles, setRoles] = useState<RoleRecord[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const [draftPermissions, setDraftPermissions] = useState<string[]>([]);
  const [roleForm, setRoleForm] = useState({ name: "", display_name: "", description: "", is_active: true });
  const [editingRole, setEditingRole] = useState<RoleRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await getRolesPermissions();
      setRoles(data.roles);
      setPermissions(data.permissions);
      const role = data.roles.find((item) => item.id === selectedRoleId) || data.roles[0];
      setSelectedRoleId(role?.id || null);
      setDraftPermissions(role?.permission_codes || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Roles could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const selectedRole = roles.find((role) => role.id === selectedRoleId) || null;
  const isProtected = selectedRole?.name === "super_admin";
  const permissionsByModule = useMemo(() => {
    return permissions.reduce<Record<string, Permission[]>>((groups, permission) => {
      groups[permission.module] = groups[permission.module] || [];
      groups[permission.module].push(permission);
      return groups;
    }, {});
  }, [permissions]);

  function chooseRole(role: RoleRecord) {
    setSelectedRoleId(role.id);
    setDraftPermissions(role.permission_codes);
    setEditingRole(null);
  }

  function togglePermission(code: string) {
    if (isProtected) return;
    setDraftPermissions((current) => current.includes(code) ? current.filter((item) => item !== code) : [...current, code]);
  }

  function toggleModule(module: string) {
    if (isProtected) return;
    const moduleCodes = permissionsByModule[module].map((item) => item.code);
    const allSelected = moduleCodes.every((code) => draftPermissions.includes(code));
    setDraftPermissions((current) => {
      if (allSelected) return current.filter((code) => !moduleCodes.includes(code));
      return Array.from(new Set([...current, ...moduleCodes]));
    });
  }

  async function savePermissions() {
    if (!selectedRole) return;
    setSaving(true);
    setError("");
    try {
      const updated = await updateRolePermissions(selectedRole.id, draftPermissions);
      setRoles((current) => current.map((role) => role.id === updated.id ? updated : role));
      setDraftPermissions(updated.permission_codes);
      setSaved("Permissions saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Permissions could not be saved");
    } finally {
      setSaving(false);
    }
  }

  async function saveRole(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (editingRole) {
        await updateRole(editingRole.id, roleForm);
        setSaved("Role updated");
      } else {
        await createRole({ ...roleForm, permission_codes: [] });
        setSaved("Role created");
      }
      setRoleForm({ name: "", display_name: "", description: "", is_active: true });
      setEditingRole(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Role could not be saved");
    } finally {
      setSaving(false);
    }
  }

  function startEdit(role: RoleRecord) {
    setEditingRole(role);
    setRoleForm({ name: role.name, display_name: role.display_name, description: role.description || "", is_active: role.is_active });
  }

  async function toggleRoleStatus(role: RoleRecord) {
    setError("");
    try {
      if (role.is_active) await deactivateRole(role.id);
      else await activateRole(role.id);
      setSaved(role.is_active ? "Role deactivated" : "Role activated");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Role status could not be updated");
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div style={{ padding: 24, display: "grid", gridTemplateColumns: "330px 1fr", gap: 18, alignItems: "start" }}>
      <div style={{ display: "grid", gap: 16 }}>
        {error && <ErrorState message={error} onRetry={load} />}
        {saved && <div style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.24)", color: "#10B981", borderRadius: 10, padding: 12, fontSize: 13 }}>{saved}</div>}

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)", fontSize: 14, fontWeight: 800 }}>Roles</div>
          {roles.map((role) => {
            const active = selectedRoleId === role.id;
            return (
              <button key={role.id} onClick={() => chooseRole(role)} style={{ width: "100%", textAlign: "left", border: "none", borderBottom: "1px solid var(--border)", background: active ? "rgba(99,102,241,0.14)" : "transparent", color: "var(--foreground)", padding: "14px 18px", cursor: "pointer", fontFamily: "inherit" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                  <span style={{ fontSize: 13, fontWeight: 800 }}>{role.display_name}</span>
                  <Badge label={role.is_active ? "Active" : "Inactive"} bg={role.is_active ? "rgba(16,185,129,0.12)" : "rgba(107,112,148,0.15)"} text={role.is_active ? "#10B981" : "#6B7094"} />
                </div>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)", marginTop: 4 }}>{role.permission_codes.length} permissions · {role.user_count} users</div>
              </button>
            );
          })}
        </div>

        <form onSubmit={saveRole} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 18, display: "grid", gap: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 800 }}>{editingRole ? "Edit Role" : "Create Custom Role"}</div>
          <Field label="Role Name"><input value={roleForm.name} onChange={(event) => setRoleForm({ ...roleForm, name: event.target.value })} required disabled={Boolean(editingRole?.is_system)} style={inputStyle()} /></Field>
          <Field label="Display Name"><input value={roleForm.display_name} onChange={(event) => setRoleForm({ ...roleForm, display_name: event.target.value })} required style={inputStyle()} /></Field>
          <Field label="Description"><input value={roleForm.description} onChange={(event) => setRoleForm({ ...roleForm, description: event.target.value })} style={inputStyle()} /></Field>
          <label style={{ fontSize: 13, color: "var(--foreground)" }}><input type="checkbox" checked={roleForm.is_active} onChange={(event) => setRoleForm({ ...roleForm, is_active: event.target.checked })} disabled={editingRole?.name === "super_admin"} /> Active</label>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" disabled={saving} style={buttonStyle()}>{saving ? "Saving..." : editingRole ? "Save Role" : "Create Role"}</button>
            {editingRole && <button type="button" onClick={() => { setEditingRole(null); setRoleForm({ name: "", display_name: "", description: "", is_active: true }); }} style={buttonStyle("var(--secondary)", "var(--foreground)")}>Cancel</button>}
          </div>
        </form>
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 900 }}>{selectedRole?.display_name || "Role"}</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>{selectedRole?.description || "Permission matrix"}</div>
          </div>
          {selectedRole && <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}><button onClick={() => startEdit(selectedRole)} style={buttonStyle("var(--secondary)", "var(--foreground)")}>Edit Role</button><button onClick={() => toggleRoleStatus(selectedRole)} disabled={selectedRole.name === "super_admin"} style={{ ...buttonStyle("rgba(239,68,68,0.14)", "#EF4444"), opacity: selectedRole.name === "super_admin" ? 0.45 : 1 }}>{selectedRole.is_active ? "Deactivate Role" : "Activate Role"}</button></div>}
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}><th style={{ padding: "12px 18px", textAlign: "left", color: "var(--muted-foreground)", fontSize: 11, letterSpacing: "0.06em" }}>MODULE</th><th style={{ padding: "12px 18px", textAlign: "left", color: "var(--muted-foreground)", fontSize: 11, letterSpacing: "0.06em" }}>PERMISSIONS</th><th style={{ padding: "12px 18px", textAlign: "left", color: "var(--muted-foreground)", fontSize: 11, letterSpacing: "0.06em" }}>SELECT ALL</th></tr></thead>
            <tbody>
              {Object.entries(permissionsByModule).map(([module, modulePermissions]) => {
                const allSelected = modulePermissions.every((permission) => draftPermissions.includes(permission.code));
                return (
                  <tr key={module} style={{ borderBottom: "1px solid var(--border)", verticalAlign: "top" }}>
                    <td style={{ padding: "16px 18px", fontSize: 13, fontWeight: 800, minWidth: 180 }}>{module}</td>
                    <td style={{ padding: "12px 18px" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 10 }}>
                        {modulePermissions.map((permission) => (
                          <label key={permission.code} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 12, color: "var(--foreground)" }}>
                            <input type="checkbox" checked={draftPermissions.includes(permission.code)} onChange={() => togglePermission(permission.code)} disabled={isProtected} />
                            <span><span style={{ fontWeight: 800 }}>{permission.name}</span><br /><span style={{ color: "var(--muted-foreground)" }}>{permission.code}</span></span>
                          </label>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: "16px 18px", minWidth: 120 }}><label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}><input type="checkbox" checked={allSelected} onChange={() => toggleModule(module)} disabled={isProtected} /> Module</label></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={{ padding: "16px 22px", display: "flex", justifyContent: "flex-end", gap: 10, borderTop: "1px solid var(--border)" }}>
          <button onClick={() => selectedRole && setDraftPermissions(selectedRole.permission_codes)} style={buttonStyle("var(--secondary)", "var(--foreground)")}>Reset Changes</button>
          <button onClick={savePermissions} disabled={saving || isProtected} style={{ ...buttonStyle(), opacity: isProtected ? 0.45 : 1 }}>{saving ? "Saving..." : "Save Permissions"}</button>
        </div>
      </div>
    </div>
  );
}
