import type { ReactNode } from "react";
import type { User } from "../types";
import { initials, titleCase } from "../utils/format";

export type Page = "dashboard" | "students" | "attendance" | "fees" | "reports" | "classes" | "settings";

type NavItem = {
  id: Page;
  label: string;
  icon: ReactNode;
};

function Icon({ d, size = 18 }: { d: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10" /> },
  { id: "students", label: "Students", icon: <Icon d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75" /> },
  { id: "classes", label: "Classes", icon: <Icon d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /> },
  { id: "attendance", label: "Attendance", icon: <Icon d="M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /> },
  { id: "fees", label: "Fee Management", icon: <Icon d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /> },
  { id: "reports", label: "Reports", icon: <Icon d="M18 20V10 M12 20V4 M6 20v-6" /> },
  { id: "settings", label: "Settings", icon: <Icon d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /> },
];

type Props = {
  activePage: Page;
  onNavigate: (page: Page) => void;
  collapsed: boolean;
  user: User;
  onLogout: () => void;
};

export default function Sidebar({ activePage, onNavigate, collapsed, user, onLogout }: Props) {
  return (
    <aside style={{
      width: collapsed ? 64 : 232,
      minWidth: collapsed ? 64 : 232,
      background: "#0A0C15",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      transition: "width 0.2s ease, min-width 0.2s ease",
      overflow: "hidden",
      height: "100vh",
      position: "sticky",
      top: 0,
    }}>
      <div style={{
        padding: collapsed ? "20px 0" : "20px 20px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: 10,
        minHeight: 64,
        justifyContent: collapsed ? "center" : "flex-start",
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9,
          background: "linear-gradient(135deg, #6366F1 0%, #818CF8 100%)",
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
          boxShadow: "0 0 0 1px rgba(99,102,241,0.3), 0 4px 12px rgba(99,102,241,0.3)",
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M12 3L1 9l11 6 9-4.91V17h2V9z" />
            <path d="M5 13.18v4L12 21l7-3.82v-4L12 17z" />
          </svg>
        </div>
        {!collapsed && (
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#E8EAF0", letterSpacing: "-0.02em" }}>EduManage</div>
            <div style={{ fontSize: 10, color: "var(--muted-foreground)", fontWeight: 500, letterSpacing: "0.05em" }}>SCHOOL ERP</div>
          </div>
        )}
      </div>

      <nav style={{ flex: 1, padding: "12px 8px", overflowY: "auto", overflowX: "hidden" }}>
        {!collapsed && (
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--muted-foreground)", letterSpacing: "0.08em", padding: "8px 10px 6px", textTransform: "uppercase" }}>
            Main Menu
          </div>
        )}
        {navItems.map((item) => {
          const active = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              title={collapsed ? item.label : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                width: "100%",
                padding: collapsed ? "10px" : "9px 10px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                background: active ? "rgba(99,102,241,0.15)" : "transparent",
                color: active ? "#818CF8" : "#6B7094",
                marginBottom: 2,
                transition: "all 0.15s",
                justifyContent: collapsed ? "center" : "flex-start",
                position: "relative",
                fontFamily: "inherit",
              }}
              onMouseEnter={(event) => {
                if (!active) event.currentTarget.style.background = "rgba(255,255,255,0.04)";
                if (!active) event.currentTarget.style.color = "#A0A4B8";
              }}
              onMouseLeave={(event) => {
                if (!active) event.currentTarget.style.background = "transparent";
                if (!active) event.currentTarget.style.color = "#6B7094";
              }}
            >
              {active && <div style={{ position: "absolute", left: 0, top: "20%", bottom: "20%", width: 3, background: "#6366F1", borderRadius: "0 2px 2px 0" }} />}
              <span style={{ flexShrink: 0 }}>{item.icon}</span>
              {!collapsed && <span style={{ fontSize: 13.5, fontWeight: active ? 600 : 500, whiteSpace: "nowrap" }}>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <div style={{
        padding: collapsed ? "14px 0" : "14px 12px",
        borderTop: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: 10,
        justifyContent: collapsed ? "center" : "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "linear-gradient(135deg, #6366F1, #818CF8)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0, fontSize: 12, fontWeight: 700, color: "#fff",
          }}>
            {initials(user.name)}
          </div>
          {!collapsed && (
            <div style={{ overflow: "hidden" }}>
              <div style={{ fontSize: 12.5, fontWeight: 600, color: "#E8EAF0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{user.name}</div>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{titleCase(user.role)}</div>
            </div>
          )}
        </div>
        {!collapsed && (
          <button onClick={onLogout} title="Sign out" style={{
            background: "transparent",
            border: "none",
            color: "var(--muted-foreground)",
            cursor: "pointer",
            padding: 6,
            borderRadius: 6,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <path d="M16 17l5-5-5-5" />
              <path d="M21 12H9" />
            </svg>
          </button>
        )}
      </div>
    </aside>
  );
}
