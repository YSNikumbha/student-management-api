import { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";
import { getDashboardData } from "../api/dashboard";
import type { DashboardData } from "../types";
import { avatarFor, feeStatusColors, formatMoney, titleCase } from "../utils/format";
import { Badge, EmptyState, ErrorState, LoadingState } from "./common";

function StatCard({ label, value, sub, color }: {
  label: string; value: string | number; sub: string; color: string;
}) {
  return (
    <div style={{
      background: "var(--card)", border: "1px solid var(--border)",
      borderRadius: 12, padding: "20px 22px",
      display: "flex", flexDirection: "column", gap: 6,
    }}>
      <div style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 500, letterSpacing: "0.03em" }}>{label}</div>
      <span style={{ fontSize: 28, fontWeight: 800, color, letterSpacing: "-0.03em", lineHeight: 1.1 }}>{value}</span>
      <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>{sub}</div>
    </div>
  );
}

const TooltipStyle = {
  contentStyle: {
    background: "#131620",
    border: "1px solid #1E2235",
    borderRadius: 8,
    fontSize: 12,
    color: "#E8EAF0",
  },
  labelStyle: { color: "#6B7094" },
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await getDashboardData());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dashboard could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <LoadingState />;
  if (error || !data) return <div style={{ padding: 24 }}><ErrorState message={error || "Dashboard data is unavailable"} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 16 }}>
        <StatCard label="TOTAL STUDENTS" value={data.kpis.total_students} sub={`${data.quick_stats.active_students} active this term`} color="#818CF8" />
        <StatCard label="ATTENDANCE RATE" value={`${data.kpis.attendance_rate}%`} sub="Current recorded average" color="#10B981" />
        <StatCard label="FEE COLLECTION" value={formatMoney(data.kpis.fee_collection)} sub="Total collected" color="#38BDF8" />
        <StatCard label="OUTSTANDING DUES" value={data.kpis.outstanding_dues} sub="Overdue fee records" color="#F59E0B" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 16 }}>
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 22px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>Attendance Overview</div>
              <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Monthly recorded attendance</div>
            </div>
            <div style={{ display: "flex", gap: 16, fontSize: 11 }}>
              {[["#6366F1", "Present"], ["#EF4444", "Absent"], ["#F59E0B", "Late"]].map(([c, l]) => (
                <div key={l} style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--muted-foreground)" }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
                  {l}
                </div>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={data.attendance_overview} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gPresent" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
              <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip {...TooltipStyle} />
              <Area type="monotone" dataKey="present" stroke="#6366F1" strokeWidth={2} fill="url(#gPresent)" />
              <Area type="monotone" dataKey="absent" stroke="#EF4444" strokeWidth={1.5} fill="none" strokeDasharray="4 2" />
              <Area type="monotone" dataKey="late" stroke="#F59E0B" strokeWidth={1.5} fill="none" strokeDasharray="2 2" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 22px" }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>Fee Collection</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Collected vs pending by due month</div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.fee_collection} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
              <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${(Number(v) / 1000).toFixed(0)}k`} />
              <Tooltip {...TooltipStyle} formatter={(v) => [formatMoney(Number(v)), ""]} />
              <Bar dataKey="collected" fill="#6366F1" radius={[4, 4, 0, 0]} maxBarSize={28} />
              <Bar dataKey="pending" fill="#1E2235" radius={[4, 4, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(260px, 1fr) 300px", gap: 16 }}>
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 22px" }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--foreground)" }}>Recent Enrollments</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {data.recent_enrollments.length === 0 ? <EmptyState>No recent student records.</EmptyState> : data.recent_enrollments.map((student) => {
              const feeColors = feeStatusColors[String(student.feeStatus).toLowerCase()] || feeStatusColors.pending;
              return (
                <div key={student.id} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
                    background: "var(--secondary)", overflow: "hidden",
                    border: "1px solid var(--border)",
                  }}>
                    <img src={student.avatar || avatarFor(student.name)} alt={student.name} style={{ width: "100%", height: "100%" }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{student.name}</div>
                    <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.rollNo} · {student.className || "-"}</div>
                  </div>
                  <Badge {...feeColors} label={titleCase(String(student.feeStatus))} />
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 22px" }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--foreground)" }}>Grade Distribution</div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={data.grade_distribution.map((entry) => ({ ...entry, label: entry.grade || entry.range }))} dataKey="count" nameKey="label" cx="50%" cy="50%" innerRadius={45} outerRadius={72} paddingAngle={2}>
                {data.grade_distribution.map((entry, i) => <Cell key={i} fill={entry.color || ["#6366F1", "#818CF8", "#38BDF8", "#10B981", "#F59E0B", "#EF4444"][i % 6]} />)}
              </Pie>
              <Tooltip {...TooltipStyle} />
              <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 11, color: "#6B7094" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 22px" }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--foreground)" }}>Quick Stats</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              { label: "Total Classes", value: data.quick_stats.total_classes, max: Math.max(data.quick_stats.total_classes, 1), color: "#6366F1" },
              { label: "Fee Collection Rate", value: `${data.quick_stats.fee_collection_rate}%`, max: 100, color: "#10B981", numVal: data.quick_stats.fee_collection_rate },
              { label: "Avg Attendance", value: `${data.quick_stats.avg_attendance}%`, max: 100, color: "#38BDF8", numVal: data.quick_stats.avg_attendance },
              { label: "Active Students", value: data.quick_stats.active_students, max: Math.max(data.kpis.total_students, 1), color: "#818CF8" },
            ].map((stat) => {
              const numVal = stat.numVal ?? Number(stat.value);
              return (
                <div key={stat.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>{stat.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "var(--foreground)", fontFamily: "JetBrains Mono, monospace" }}>{stat.value}</span>
                  </div>
                  <div style={{ height: 4, background: "var(--border)", borderRadius: 2 }}>
                    <div style={{ height: "100%", borderRadius: 2, background: stat.color, width: `${Math.min(100, (numVal / stat.max) * 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
