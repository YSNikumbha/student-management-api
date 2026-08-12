import { useEffect, useMemo, useState } from "react";
import type { Page } from "./Sidebar";
import type { NotificationItem, SearchResponse, User } from "../types";
import { globalSearch } from "../api/search";
import { getNotifications, getUnreadCount, markAllNotificationsRead, markNotificationRead } from "../api/notifications";
import { formatDate, titleCase } from "../utils/format";

type Props = {
  page: Page;
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
  user: User;
};

const pageTitles: Record<Page, { title: string; subtitle: string }> = {
  dashboard: { title: "Dashboard", subtitle: "Welcome back" },
  students: { title: "Students", subtitle: "Manage student records & profiles" },
  classes: { title: "Classes", subtitle: "Manage classrooms & sections" },
  attendance: { title: "Attendance", subtitle: "Track daily student attendance" },
  fees: { title: "Fee Management", subtitle: "Invoices, payments & collection" },
  reports: { title: "Reports & Analytics", subtitle: "Academic performance & insights" },
  settings: { title: "Settings", subtitle: "School configuration & preferences" },
};

function BellIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

export default function TopBar({ page, onToggleSidebar, user }: Props) {
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const { title, subtitle } = pageTitles[page];

  useEffect(() => {
    const timeout = window.setTimeout(async () => {
      if (search.trim().length < 2) {
        setSearchResults(null);
        return;
      }
      try {
        setSearchResults(await globalSearch(search.trim()));
      } catch {
        setSearchResults(null);
      }
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [search]);

  async function refreshNotifications() {
    const [list, count] = await Promise.all([getNotifications(), getUnreadCount()]);
    setNotifications(list.items);
    setUnread(count.unread_count);
  }

  useEffect(() => {
    refreshNotifications().catch(() => undefined);
  }, []);

  const groupedResults = useMemo(() => {
    if (!searchResults) return [];
    return [
      ["Students", searchResults.students],
      ["Classes", searchResults.batches],
      ["Courses", searchResults.courses],
      ["Subjects", searchResults.subjects],
      ["Users", searchResults.users],
    ].filter(([, items]) => Array.isArray(items) && items.length > 0) as [string, SearchResponse[keyof SearchResponse]][];
  }, [searchResults]);

  async function markRead(id: number) {
    await markNotificationRead(id);
    await refreshNotifications();
  }

  async function markAllRead() {
    await markAllNotificationsRead();
    await refreshNotifications();
  }

  return (
    <header style={{
      height: 64,
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      padding: "0 24px",
      gap: 16,
      background: "#0C0E16",
      position: "sticky",
      top: 0,
      zIndex: 10,
    }}>
      <button onClick={onToggleSidebar} style={{
        background: "transparent", border: "none", cursor: "pointer",
        color: "var(--muted-foreground)", padding: 6, borderRadius: 6,
        display: "flex", alignItems: "center",
      }} title="Toggle sidebar">
        <MenuIcon />
      </button>

      <div style={{ flex: 1 }}>
        <h1 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "#E8EAF0", letterSpacing: "-0.01em" }}>{title}</h1>
        <p style={{ margin: 0, fontSize: 12, color: "var(--muted-foreground)" }}>{subtitle}, {user.name}</p>
      </div>

      <div style={{ position: "relative" }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          background: "var(--secondary)", border: "1px solid var(--border)",
          borderRadius: 8, padding: "7px 12px", width: 260,
        }}>
          <SearchIcon />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search..."
            style={{
              background: "transparent", border: "none", outline: "none",
              color: "var(--foreground)", fontSize: 13, width: "100%",
              fontFamily: "inherit",
            }}
          />
        </div>
        {groupedResults.length > 0 && (
          <div style={{
            position: "absolute",
            top: 42,
            right: 0,
            width: 360,
            maxHeight: 420,
            overflowY: "auto",
            background: "#131620",
            border: "1px solid var(--border)",
            borderRadius: 12,
            boxShadow: "0 18px 50px rgba(0,0,0,0.4)",
            padding: 10,
            zIndex: 30,
          }}>
            {groupedResults.map(([group, items]) => (
              <div key={group} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: "var(--muted-foreground)", letterSpacing: "0.08em", textTransform: "uppercase", padding: "6px 8px" }}>{group}</div>
                {items.map((item) => (
                  <button key={`${item.type}-${item.id}`} onClick={() => {
                    setSearch("");
                    setSearchResults(null);
                    const target = item.url.replace("/admin/courses", "/admin/classes").replace("/admin/users", "/admin/settings");
                    window.history.pushState(null, "", target);
                    window.dispatchEvent(new PopStateEvent("popstate"));
                  }} style={{
                    width: "100%",
                    textAlign: "left",
                    background: "transparent",
                    border: "none",
                    borderRadius: 8,
                    padding: "8px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}>
                    <div style={{ fontSize: 13, color: "var(--foreground)", fontWeight: 600 }}>{item.title}</div>
                    <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{item.subtitle}</div>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ position: "relative" }}>
        <button onClick={() => setShowNotifications((open) => !open)} style={{
          background: "var(--secondary)", border: "1px solid var(--border)",
          borderRadius: 8, padding: 8, cursor: "pointer",
          color: "var(--muted-foreground)", display: "flex", alignItems: "center",
        }}>
          <BellIcon />
          {unread > 0 && <span style={{
            position: "absolute", top: 4, right: 4,
            minWidth: 16, height: 16, borderRadius: 99,
            background: "#6366F1", border: "2px solid #0C0E16",
            color: "#fff", fontSize: 9, display: "grid", placeItems: "center",
            fontWeight: 800,
          }}>{unread > 9 ? "9+" : unread}</span>}
        </button>
        {showNotifications && (
          <div style={{
            position: "absolute",
            top: 42,
            right: 0,
            width: 360,
            maxHeight: 430,
            overflowY: "auto",
            background: "#131620",
            border: "1px solid var(--border)",
            borderRadius: 12,
            boxShadow: "0 18px 50px rgba(0,0,0,0.4)",
            zIndex: 30,
          }}>
            <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--foreground)" }}>Notifications</div>
              <button onClick={markAllRead} style={{ background: "transparent", border: "none", color: "#818CF8", fontSize: 11, cursor: "pointer", fontFamily: "inherit" }}>Mark all read</button>
            </div>
            {notifications.length === 0 ? (
              <div style={{ padding: 22, color: "var(--muted-foreground)", fontSize: 13 }}>No notifications.</div>
            ) : notifications.map((item) => (
              <button key={item.id} onClick={() => markRead(item.id)} style={{
                width: "100%",
                display: "block",
                textAlign: "left",
                background: item.is_read ? "transparent" : "rgba(99,102,241,0.08)",
                border: "none",
                borderBottom: "1px solid var(--border)",
                padding: "12px 16px",
                cursor: "pointer",
                fontFamily: "inherit",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ fontSize: 13, color: "var(--foreground)", fontWeight: 700 }}>{item.title}</div>
                  <div style={{ fontSize: 10, color: "var(--muted-foreground)", whiteSpace: "nowrap" }}>{formatDate(item.created_at)}</div>
                </div>
                <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 4 }}>{item.message}</div>
                <div style={{ fontSize: 10, color: "#818CF8", marginTop: 6 }}>{titleCase(item.type)}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{
        fontSize: 12, color: "var(--muted-foreground)",
        fontFamily: "JetBrains Mono, monospace",
        borderLeft: "1px solid var(--border)",
        paddingLeft: 16,
      }}>
        {new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" })}
      </div>
    </header>
  );
}
