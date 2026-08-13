import { FormEvent, useEffect, useMemo, useState } from "react";
import Sidebar, { type Page } from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Dashboard from "./components/Dashboard";
import Students from "./components/Students";
import Attendance from "./components/Attendance";
import Fees from "./components/Fees";
import Reports from "./components/Reports";
import Classes from "./components/Classes";
import Settings from "./components/Settings";
import UserManagement from "./components/UserManagement";
import RolesPermissions from "./components/RolesPermissions";
import { getMe, login, logout } from "./api/auth";
import { ApiError, getStoredUser, getToken } from "./api/client";
import type { User } from "./types";

const pagePath: Record<Page, string> = {
  dashboard: "/admin",
  students: "/admin/students",
  classes: "/admin/classes",
  attendance: "/admin/attendance",
  fees: "/admin/fees",
  reports: "/admin/reports",
  users: "/admin/users",
  rolesPermissions: "/admin/roles-permissions",
  settings: "/admin/settings",
};

function pageFromPath(pathname: string): Page {
  if (pathname.includes("/students")) return "students";
  if (pathname.includes("/classes")) return "classes";
  if (pathname.includes("/attendance")) return "attendance";
  if (pathname.includes("/fees")) return "fees";
  if (pathname.includes("/reports")) return "reports";
  if (pathname.includes("/roles-permissions")) return "rolesPermissions";
  if (pathname.includes("/users")) return "users";
  if (pathname.includes("/settings")) return "settings";
  return "dashboard";
}

function LoginScreen({ onLoggedIn }: { onLoggedIn: (user: User) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await login(email, password);
      onLoggedIn(user);
      window.history.replaceState(null, "", "/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--background)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 24,
    }}>
      <form onSubmit={handleSubmit} style={{
        width: "100%",
        maxWidth: 420,
        background: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: 16,
        padding: 28,
        boxShadow: "0 24px 60px rgba(0,0,0,0.35)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 26 }}>
          <div style={{
            width: 42,
            height: 42,
            borderRadius: 11,
            background: "linear-gradient(135deg, #6366F1 0%, #818CF8 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 0 1px rgba(99,102,241,0.3), 0 4px 12px rgba(99,102,241,0.3)",
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
              <path d="M12 3L1 9l11 6 9-4.91V17h2V9z" />
              <path d="M5 13.18v4L12 21l7-3.82v-4L12 17z" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "var(--foreground)" }}>EduManage</div>
            <div style={{ fontSize: 11, color: "var(--muted-foreground)", letterSpacing: "0.08em" }}>SCHOOL ERP</div>
          </div>
        </div>

        <div style={{ fontSize: 22, fontWeight: 800, color: "var(--foreground)", marginBottom: 6 }}>Sign in</div>
        <div style={{ fontSize: 13, color: "var(--muted-foreground)", marginBottom: 22 }}>
          Use your staff account to continue.
        </div>

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Email</label>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          autoComplete="username"
          style={{
            width: "100%",
            background: "var(--secondary)",
            border: "1px solid var(--border)",
            borderRadius: 9,
            padding: "11px 13px",
            color: "var(--foreground)",
            outline: "none",
            fontFamily: "inherit",
            marginBottom: 14,
          }}
        />

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Password</label>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          autoComplete="current-password"
          style={{
            width: "100%",
            background: "var(--secondary)",
            border: "1px solid var(--border)",
            borderRadius: 9,
            padding: "11px 13px",
            color: "var(--foreground)",
            outline: "none",
            fontFamily: "inherit",
            marginBottom: 16,
          }}
        />

        {error && (
          <div style={{
            background: "rgba(239,68,68,0.12)",
            border: "1px solid rgba(239,68,68,0.24)",
            color: "#FCA5A5",
            borderRadius: 9,
            padding: "10px 12px",
            fontSize: 12,
            marginBottom: 14,
          }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            background: loading ? "rgba(99,102,241,0.55)" : "#6366F1",
            border: "none",
            borderRadius: 9,
            padding: "11px 16px",
            color: "#fff",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 13,
            fontWeight: 700,
            fontFamily: "inherit",
          }}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState<Page>(() => pageFromPath(window.location.pathname));
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<User | null>(() => getStoredUser<User>());
  const [authChecked, setAuthChecked] = useState(false);

  const isLoginPath = window.location.pathname === "/login";

  useEffect(() => {
    async function restoreSession() {
      if (!getToken()) {
        setAuthChecked(true);
        return;
      }
      try {
        setUser(await getMe());
      } catch (err) {
        if (!(err instanceof ApiError && err.status === 401)) {
          console.error(err);
        }
        logout();
      } finally {
        setAuthChecked(true);
      }
    }
    restoreSession();

    const unauthorized = () => {
      setUser(null);
      window.history.replaceState(null, "", "/login");
    };
    window.addEventListener("sms:unauthorized", unauthorized);
    return () => window.removeEventListener("sms:unauthorized", unauthorized);
  }, []);

  useEffect(() => {
    const onPopState = () => setActivePage(pageFromPath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const content = useMemo(() => {
    switch (activePage) {
      case "dashboard": return <Dashboard />;
      case "students": return <Students currentUser={user} />;
      case "classes": return <Classes currentUser={user} />;
      case "attendance": return <Attendance currentUser={user} />;
      case "fees": return <Fees currentUser={user} />;
      case "reports": return <Reports />;
      case "users": return <UserManagement currentUser={user} />;
      case "rolesPermissions": return <RolesPermissions />;
      case "settings": return <Settings currentUser={user} />;
      default: return <Dashboard />;
    }
  }, [activePage, user]);

  function navigate(page: Page) {
    setActivePage(page);
    window.history.pushState(null, "", pagePath[page]);
  }

  function handleLogout() {
    logout();
    setUser(null);
    window.history.replaceState(null, "", "/login");
  }

  if (!authChecked) {
    return <div style={{ height: "100vh", display: "grid", placeItems: "center", color: "var(--muted-foreground)" }}>Loading...</div>;
  }

  if (!user || isLoginPath) {
    return <LoginScreen onLoggedIn={setUser} />;
  }

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      overflow: "hidden",
      background: "var(--background)",
    }}>
      <Sidebar
        activePage={activePage}
        onNavigate={navigate}
        collapsed={sidebarCollapsed}
        user={user}
        onLogout={handleLogout}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <TopBar
          page={activePage}
          onToggleSidebar={() => setSidebarCollapsed((c) => !c)}
          sidebarCollapsed={sidebarCollapsed}
          user={user}
        />
        <main style={{ flex: 1, overflowY: "auto" }}>
          {content}
        </main>
      </div>
    </div>
  );
}
