import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, AreaChart, Area, Legend
} from "recharts";
import { downloadReport, getReportsData } from "../api/reports";
import type { ReportsData } from "../types";
import { avatarFor, formatMoney } from "../utils/format";
import { ErrorState, LoadingState } from "./common";

const TooltipStyle = {
  contentStyle: { background: "#131620", border: "1px solid #1E2235", borderRadius: 8, fontSize: 12, color: "#E8EAF0" },
  labelStyle: { color: "#6B7094" },
};

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
      <div style={{ marginBottom: 18 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>{title}</div>
        {subtitle && <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>{subtitle}</div>}
      </div>
      {children}
    </div>
  );
}

function ExportButtons({ kind }: { kind: "students" | "attendance" | "fees" | "courses" }) {
  const [error, setError] = useState("");
  async function download(format: "csv" | "pdf") {
    setError("");
    try {
      await downloadReport(kind, format);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    }
  }
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", marginLeft: "auto" }}>
      {error && <span style={{ color: "#FCA5A5", fontSize: 12 }}>{error}</span>}
      <button onClick={() => download("csv")} style={{ background: "var(--secondary)", border: "1px solid var(--border)", color: "var(--foreground)", borderRadius: 8, padding: "8px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit" }}>CSV</button>
      <button onClick={() => download("pdf")} style={{ background: "#6366F1", border: "none", color: "#fff", borderRadius: 8, padding: "8px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit" }}>PDF</button>
    </div>
  );
}

export default function Reports() {
  const [activeTab, setActiveTab] = useState<"academic" | "attendance" | "finance" | "toppers">("academic");
  const [data, setData] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await getReportsData());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reports could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const topStudents = useMemo(() => data?.academic.top_students || [], [data]);
  const needsAttention = useMemo(() => (data?.academic.needs_attention || []) as unknown as typeof topStudents, [data, topStudents]);
  const radarData = data?.academic.subject_radar || data?.academic.subject_performance.map((item) => ({ subject: item.subject, score: item.avg })) || [];
  const attendanceRateByMonth = (data?.attendance.monthly || []).map((item) => {
    const total = (item.present || 0) + (item.absent || 0) + (item.late || 0) + (item.excused || 0);
    return { month: item.month, rate: total ? Math.round(((item.present || 0) / total) * 100) : 0 };
  });

  if (loading) return <LoadingState />;
  if (error || !data) return <div style={{ padding: 24 }}><ErrorState message={error || "Reports data is unavailable"} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 0, background: "var(--card)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
          {([
            ["academic", "Academic Performance"],
            ["attendance", "Attendance Report"],
            ["finance", "Financial Report"],
            ["toppers", "Top Performers"],
          ] as const).map(([tab, label], i, arr) => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{ padding: "9px 22px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, background: activeTab === tab ? "rgba(99,102,241,0.15)" : "transparent", color: activeTab === tab ? "#818CF8" : "var(--muted-foreground)", fontFamily: "inherit", borderRight: i < arr.length - 1 ? "1px solid var(--border)" : "none", transition: "all 0.15s" }}>{label}</button>
          ))}
        </div>
        <ExportButtons kind={activeTab === "finance" ? "fees" : activeTab === "attendance" ? "attendance" : "students"} />
      </div>

      {activeTab === "academic" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
            {[
              { label: "Avg School GPA", value: data.academic.summary.avg_school_gpa.toFixed(2), color: "#818CF8" },
              { label: "Top GPA", value: data.academic.summary.top_gpa.toFixed(2), color: "#10B981" },
              { label: "Pass Rate", value: `${data.academic.summary.pass_rate}%`, color: "#38BDF8" },
              { label: "Honor Roll", value: data.academic.summary.honor_roll, color: "#F59E0B" },
            ].map((card) => (
              <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.label}</div>
                <div style={{ fontSize: 26, fontWeight: 800, color: card.color, marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 16 }}>
            <Card title="Subject Performance" subtitle="Average scores across all recorded assessments">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.academic.subject_performance} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                  <XAxis dataKey="subject" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip {...TooltipStyle} />
                  <Bar dataKey="avg" fill="#6366F1" radius={[4, 4, 0, 0]} maxBarSize={36} name="Avg" />
                  <Bar dataKey="highest" fill="rgba(99,102,241,0.2)" radius={[4, 4, 0, 0]} maxBarSize={36} name="Highest" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Subject Radar" subtitle="Balanced view of academic strength">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData} cx="50%" cy="50%">
                  <PolarGrid stroke="#1E2235" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#6B7094", fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: "#6B7094", fontSize: 9 }} domain={[0, 100]} />
                  <Radar name="Avg Score" dataKey="score" stroke="#6366F1" fill="#6366F1" fillOpacity={0.25} strokeWidth={2} />
                  <Tooltip {...TooltipStyle} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="GPA Distribution" subtitle="Student count by GPA band">
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={data.academic.gpa_distribution} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" horizontal={false} />
                  <XAxis type="number" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="range" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
                  <Tooltip {...TooltipStyle} />
                  <Bar dataKey="count" fill="#818CF8" radius={[0, 4, 4, 0]} maxBarSize={22} name="Students" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Class Average GPA" subtitle="Average GPA by class">
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={data.academic.class_average_gpa} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                  <XAxis dataKey="class" tick={{ fill: "#6B7094", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 4.0]} />
                  <Tooltip {...TooltipStyle} />
                  <Bar dataKey="avgGpa" fill="#38BDF8" radius={[4, 4, 0, 0]} maxBarSize={28} name="Avg GPA" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </>
      )}

      {activeTab === "attendance" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
            {[
              { label: "Avg Attendance Rate", value: `${data.attendance.summary.avg_attendance_rate}%`, color: "#10B981" },
              { label: "Perfect Attendance", value: data.attendance.summary.perfect_attendance, color: "#818CF8" },
              { label: "Chronic Absentees", value: data.attendance.summary.chronic_absentees, color: "#EF4444" },
              { label: "Late Arrivals Avg", value: `${data.attendance.summary.late_arrivals_avg}%`, color: "#F59E0B" },
            ].map((card) => (
              <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.label}</div>
                <div style={{ fontSize: 26, fontWeight: 800, color: card.color, marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 16 }}>
            <Card title="Monthly Attendance Trend" subtitle="Present / Absent / Late breakdown">
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={data.attendance.monthly} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                  <defs><linearGradient id="gP" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.3} /><stop offset="95%" stopColor="#10B981" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                  <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip {...TooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11, color: "#6B7094" }} />
                  <Area type="monotone" dataKey="present" stroke="#10B981" strokeWidth={2} fill="url(#gP)" name="Present" />
                  <Line type="monotone" dataKey="absent" stroke="#EF4444" strokeWidth={1.5} dot={false} name="Absent" />
                  <Line type="monotone" dataKey="late" stroke="#F59E0B" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="Late" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Attendance Rate by Month" subtitle="Percentage present">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={attendanceRateByMonth} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                  <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} unit="%" />
                  <Tooltip {...TooltipStyle} formatter={(value) => [`${Number(value)}%`, "Present Rate"]} />
                  <Line type="monotone" dataKey="rate" stroke="#6366F1" strokeWidth={2.5} dot={{ fill: "#6366F1", r: 4 }} name="Present %" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </>
      )}

      {activeTab === "finance" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
            {[
              { label: "Total Billed", value: formatMoney(data.finance.summary.total_billed), color: "#818CF8" },
              { label: "Collected", value: formatMoney(data.finance.summary.collected), color: "#10B981" },
              { label: "Outstanding", value: formatMoney(data.finance.summary.outstanding), color: "#EF4444" },
              { label: "Collection Rate", value: `${data.finance.summary.collection_rate}%`, color: "#38BDF8" },
            ].map((card) => (
              <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.label}</div>
                <div style={{ fontSize: 26, fontWeight: 800, color: card.color, marginTop: 6, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
              </div>
            ))}
          </div>
          <Card title="Monthly Fee Collection" subtitle="Collected vs pending throughout the year">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.finance.fee_collection} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `₹${(Number(value) / 1000).toFixed(0)}k`} />
                <Tooltip {...TooltipStyle} formatter={(value) => [formatMoney(Number(value)), ""]} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#6B7094" }} />
                <Bar dataKey="collected" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={40} name="Collected" />
                <Bar dataKey="pending" fill="#EF4444" radius={[4, 4, 0, 0]} maxBarSize={40} name="Pending" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}

      {activeTab === "toppers" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 16 }}>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>Top 10 Students</div>
              <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Ranked by GPA</div>
            </div>
            {topStudents.map((student, index) => (
              <div key={student.student_id} style={{ display: "flex", alignItems: "center", gap: 14, padding: "13px 22px", borderBottom: index < topStudents.length - 1 ? "1px solid var(--border)" : "none", background: index === 0 ? "rgba(99,102,241,0.05)" : "transparent" }}>
                <div style={{ width: 26, height: 26, borderRadius: "50%", flexShrink: 0, background: index === 0 ? "linear-gradient(135deg, #F59E0B, #FCD34D)" : index === 1 ? "linear-gradient(135deg, #9CA3AF, #D1D5DB)" : index === 2 ? "linear-gradient(135deg, #B45309, #D97706)" : "var(--secondary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: index < 3 ? "#000" : "var(--muted-foreground)" }}>{index + 1}</div>
                <div style={{ width: 28, height: 28, borderRadius: "50%", overflow: "hidden", background: "var(--secondary)", flexShrink: 0 }}>
                  <img src={avatarFor(student.student_name)} alt={student.student_name} style={{ width: "100%", height: "100%" }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{student.student_name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.student_code} · {student.class_name || "-"}</div>
                </div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 14, fontWeight: 700, color: index === 0 ? "#F59E0B" : "#818CF8" }}>{student.gpa.toFixed(2)}</div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
              <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)" }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>Needs Attention</div>
                <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Students with lowest GPA</div>
              </div>
              {needsAttention.map((student, index) => (
                <div key={student.student_id} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 22px", borderBottom: index < needsAttention.length - 1 ? "1px solid var(--border)" : "none" }}>
                  <div style={{ width: 28, height: 28, borderRadius: "50%", overflow: "hidden", background: "var(--secondary)", flexShrink: 0 }}>
                    <img src={avatarFor(student.student_name)} alt={student.student_name} style={{ width: "100%", height: "100%" }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{student.student_name}</div>
                    <div style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{student.class_name || "-"}</div>
                  </div>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 14, fontWeight: 700, color: "#EF4444" }}>{student.gpa.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <Card title="GPA by Class">
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={data.academic.class_average_gpa.slice(0, 8)} margin={{ top: 0, right: 0, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                  <XAxis dataKey="class" tick={{ fill: "#6B7094", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#6B7094", fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 4.0]} />
                  <Tooltip {...TooltipStyle} />
                  <Bar dataKey="avgGpa" fill="#6366F1" radius={[4, 4, 0, 0]} maxBarSize={24} name="Avg GPA" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
