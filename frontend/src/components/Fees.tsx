import { FormEvent, useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { createFee, deleteFee, getFeesData, recordPayment, updateFee } from "../api/fees";
import { getStudentsData } from "../api/students";
import type { FeeFormInput, FeeRecord, FeesData, PaymentFormInput, StudentRow, User } from "../types";
import { feeStatusColors, formatDate, formatMoney, titleCase, todayISO } from "../utils/format";
import { Badge, EmptyState, ErrorState, LoadingState } from "./common";

const TooltipStyle = {
  contentStyle: { background: "#131620", border: "1px solid #1E2235", borderRadius: 8, fontSize: 12, color: "#E8EAF0" },
  labelStyle: { color: "#6B7094" },
};

function moneyNumber(value: number | string): number {
  return Number(value || 0);
}

function InvoiceModal({ record, onClose, onRecordPayment }: { record: FeeRecord; onClose: () => void; onRecordPayment: () => void }) {
  const colors = feeStatusColors[String(record.status).toLowerCase()] || feeStatusColors.pending;
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <div onClick={(event) => event.stopPropagation()} style={{ background: "#131620", border: "1px solid var(--border)", borderRadius: 16, width: 560 }}>
        <div style={{ padding: 28, borderBottom: "1px solid var(--border)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)", letterSpacing: "0.08em", fontWeight: 600, textTransform: "uppercase" }}>Invoice</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "var(--foreground)", marginTop: 4, fontFamily: "JetBrains Mono, monospace" }}>{record.invoice_number || `INV-${record.id}`}</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
              <Badge {...colors} label={titleCase(String(record.status))} />
              <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Due: {formatDate(record.due_date)}</span>
            </div>
          </div>
        </div>
        <div style={{ padding: "20px 28px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 11, color: "var(--muted-foreground)", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 10 }}>Bill To</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>{record.student_name || "Student"}</div>
          <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>{record.student_code || "-"}</div>
        </div>
        <div style={{ padding: "20px 28px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{["Description", "Amount", "Paid", "Balance"].map((header) => <th key={header} style={{ padding: "8px 0", fontSize: 11, color: "var(--muted-foreground)", textAlign: header === "Description" ? "left" : "right", fontWeight: 600, letterSpacing: "0.05em" }}>{header}</th>)}</tr></thead>
            <tbody>
              <tr>
                <td style={{ padding: "14px 0", fontSize: 13, color: "var(--foreground)", fontWeight: 500 }}>{record.fee_type || record.title}</td>
                <td style={{ padding: "14px 0", fontSize: 13, textAlign: "right", color: "var(--foreground)", fontFamily: "JetBrains Mono, monospace" }}>{formatMoney(record.total_amount)}</td>
                <td style={{ padding: "14px 0", fontSize: 13, textAlign: "right", color: "#10B981", fontFamily: "JetBrains Mono, monospace" }}>{formatMoney(record.paid_amount)}</td>
                <td style={{ padding: "14px 0", fontSize: 13, textAlign: "right", color: moneyNumber(record.balance) > 0 ? "#EF4444" : "#10B981", fontFamily: "JetBrains Mono, monospace" }}>{formatMoney(record.balance)}</td>
              </tr>
            </tbody>
          </table>
          <div style={{ borderTop: "1px solid var(--border)", marginTop: 8, paddingTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>{record.payment_method && <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Last paid via {titleCase(record.payment_method)}</span>}</div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Total Due</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "var(--foreground)", fontFamily: "JetBrains Mono, monospace" }}>{formatMoney(record.balance)}</div>
            </div>
          </div>
        </div>
        <div style={{ padding: "0 28px 24px", display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 20px", cursor: "pointer", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>Close</button>
          <button onClick={onRecordPayment} disabled={moneyNumber(record.balance) <= 0} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 22px", cursor: moneyNumber(record.balance) > 0 ? "pointer" : "not-allowed", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>Record Payment</button>
        </div>
      </div>
    </div>
  );
}

function FeeFormModal({ record, students, onClose, onSave }: { record?: FeeRecord; students: StudentRow[]; onClose: () => void; onSave: (data: FeeFormInput) => Promise<void> }) {
  const [form, setForm] = useState<FeeFormInput>(() => ({
    student_id: record?.student_id || students[0]?.id || 0,
    title: record?.title || record?.fee_type || "",
    total_amount: record ? moneyNumber(record.total_amount) : 0,
    due_date: record?.due_date || todayISO(),
    description: null,
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
      setError(err instanceof Error ? err.message : "Invoice could not be saved");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <form onSubmit={submit} onClick={(event) => event.stopPropagation()} style={{ background: "#131620", border: "1px solid var(--border)", borderRadius: 16, width: 560 }}>
        <div style={{ padding: "22px 26px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--foreground)" }}>{record ? "Edit Invoice" : "New Invoice"}</div>
            <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>Invoice number is generated by the server</div>
          </div>
          <button type="button" onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", color: "var(--muted-foreground)", cursor: "pointer" }}>x</button>
        </div>
        <div style={{ padding: 26, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 6, gridColumn: "1 / -1" }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Student</span>
            <select value={form.student_id} onChange={(event) => setForm((current) => ({ ...current, student_id: Number(event.target.value) }))} disabled={Boolean(record)} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
              {students.map((student) => <option key={student.id} value={student.id}>{student.name} · {student.rollNo}</option>)}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Fee Type</span>
            <input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Amount</span>
            <input type="number" min="1" value={form.total_amount} onChange={(event) => setForm((current) => ({ ...current, total_amount: Number(event.target.value) }))} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", fontWeight: 600 }}>Due Date</span>
            <input type="date" value={form.due_date} onChange={(event) => setForm((current) => ({ ...current, due_date: event.target.value }))} required style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
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

function PaymentModal({ record, onClose, onSave }: { record: FeeRecord; onClose: () => void; onSave: (data: PaymentFormInput) => Promise<void> }) {
  const [form, setForm] = useState<PaymentFormInput>({ amount: moneyNumber(record.balance), payment_date: todayISO(), payment_method: "cash", reference_number: "", notes: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment could not be recorded");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }} onClick={onClose}>
      <form onSubmit={submit} onClick={(event) => event.stopPropagation()} style={{ width: 480, background: "#131620", border: "1px solid var(--border)", borderRadius: 16 }}>
        <div style={{ padding: "22px 26px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: "var(--foreground)" }}>Record Payment</div>
          <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 2 }}>{record.invoice_number || `INV-${record.id}`} · Balance {formatMoney(record.balance)}</div>
        </div>
        <div style={{ padding: 26, display: "grid", gap: 14 }}>
          <input type="number" min="1" max={moneyNumber(record.balance)} value={form.amount} onChange={(event) => setForm((current) => ({ ...current, amount: Number(event.target.value) }))} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          <input type="date" value={form.payment_date} onChange={(event) => setForm((current) => ({ ...current, payment_date: event.target.value }))} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          <select value={form.payment_method} onChange={(event) => setForm((current) => ({ ...current, payment_method: event.target.value as PaymentFormInput["payment_method"] }))} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }}>
            <option value="cash">Cash</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="online">Online</option>
            <option value="cheque">Cheque</option>
          </select>
          <input placeholder="Reference" value={form.reference_number || ""} onChange={(event) => setForm((current) => ({ ...current, reference_number: event.target.value }))} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", color: "var(--foreground)", fontFamily: "inherit" }} />
          {error && <div style={{ color: "#FCA5A5", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: 8, padding: 10, fontSize: 12 }}>{error}</div>}
        </div>
        <div style={{ padding: "16px 26px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button type="button" onClick={onClose} style={{ background: "var(--secondary)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 18px", color: "var(--foreground)", cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
          <button type="submit" disabled={saving} style={{ background: "#6366F1", border: "none", borderRadius: 8, padding: "9px 20px", color: "#fff", cursor: saving ? "not-allowed" : "pointer", fontWeight: 700, fontFamily: "inherit" }}>{saving ? "Saving..." : "Save Payment"}</button>
        </div>
      </form>
    </div>
  );
}

export default function Fees({ currentUser }: { currentUser: User | null }) {
  const [data, setData] = useState<FeesData | null>(null);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [selectedRecord, setSelectedRecord] = useState<FeeRecord | null>(null);
  const [editingRecord, setEditingRecord] = useState<FeeRecord | null>(null);
  const [payingRecord, setPayingRecord] = useState<FeeRecord | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [activeTab, setActiveTab] = useState<"records" | "analytics">("records");
  const [page, setPage] = useState(1);
  const perPage = 12;
  const canManage = ["admin", "accountant", "staff"].includes(String(currentUser?.role));

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [feesData, studentsData] = await Promise.all([getFeesData(), getStudentsData()]);
      setData(feesData);
      setStudents(studentsData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fees could not load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const feeTypes = useMemo(() => Array.from(new Set((data?.records || []).map((record) => record.fee_type || record.title))), [data]);
  const pieData = useMemo(() => ["paid", "partial", "overdue", "pending"].map((status) => ({ name: titleCase(status), value: (data?.records || []).filter((record) => String(record.status).toLowerCase() === status || (status === "pending" && String(record.status).toLowerCase() === "unpaid")).length, color: feeStatusColors[status].text })), [data]);
  const filtered = useMemo(() => (data?.records || []).filter((record) => {
    const q = search.toLowerCase();
    return (
      ((record.invoice_number || "").toLowerCase().includes(q) || (record.student_name || "").toLowerCase().includes(q) || (record.fee_type || record.title).toLowerCase().includes(q)) &&
      (filterStatus === "all" || String(record.status).toLowerCase() === filterStatus || (filterStatus === "pending" && String(record.status).toLowerCase() === "unpaid")) &&
      (filterType === "all" || (record.fee_type || record.title) === filterType)
    );
  }), [data, filterStatus, filterType, search]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const paged = filtered.slice((page - 1) * perPage, page * perPage);

  async function saveFee(form: FeeFormInput) {
    if (editingRecord) await updateFee(editingRecord.id, form);
    else await createFee(form);
    setEditingRecord(null);
    setShowCreate(false);
    await load();
  }

  async function savePayment(form: PaymentFormInput) {
    if (!payingRecord) return;
    await recordPayment(payingRecord.id, form);
    setPayingRecord(null);
    setSelectedRecord(null);
    await load();
  }

  async function removeFee(record: FeeRecord) {
    if (!window.confirm(`Delete invoice ${record.invoice_number || record.id}?`)) return;
    try {
      await deleteFee(record.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fee record could not be deleted");
    }
  }

  if (loading) return <LoadingState />;
  if (error && !data) return <div style={{ padding: 24 }}><ErrorState message={error} onRetry={load} /></div>;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      {selectedRecord && <InvoiceModal record={selectedRecord} onClose={() => setSelectedRecord(null)} onRecordPayment={() => setPayingRecord(selectedRecord)} />}
      {(showCreate || editingRecord) && <FeeFormModal record={editingRecord || undefined} students={students} onClose={() => { setShowCreate(false); setEditingRecord(null); }} onSave={saveFee} />}
      {payingRecord && <PaymentModal record={payingRecord} onClose={() => setPayingRecord(null)} onSave={savePayment} />}
      {error && <ErrorState message={error} onRetry={load} />}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
        {[
          { label: "Total Billed", value: formatMoney(data?.summary.total_billed), color: "#818CF8" },
          { label: "Collected", value: formatMoney(data?.summary.collected), color: "#10B981" },
          { label: "Outstanding", value: formatMoney(data?.summary.outstanding), color: "#EF4444" },
          { label: "Collection Rate", value: `${data?.summary.collection_rate || 0}%`, color: "#38BDF8" },
        ].map((card) => (
          <div key={card.label} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "18px 22px" }}>
            <div style={{ fontSize: 11, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>{card.label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: card.color, fontFamily: "JetBrains Mono, monospace" }}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          {(["records", "analytics"] as const).map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} style={{ padding: "8px 20px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, background: activeTab === tab ? "rgba(99,102,241,0.15)" : "transparent", color: activeTab === tab ? "#818CF8" : "var(--muted-foreground)", fontFamily: "inherit", textTransform: "capitalize", borderRight: tab !== "analytics" ? "1px solid var(--border)" : "none" }}>{tab === "records" ? "Fee Records" : "Analytics"}</button>)}
        </div>
        {activeTab === "records" && <>
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search invoices, students..." style={{ flex: 1, minWidth: 180, background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit", outline: "none" }} />
          <select value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>
            <option value="all">All Status</option>
            <option value="paid">Paid</option>
            <option value="partial">Partial</option>
            <option value="overdue">Overdue</option>
            <option value="pending">Pending</option>
          </select>
          <select value={filterType} onChange={(event) => setFilterType(event.target.value)} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 14px", color: "var(--foreground)", fontSize: 13, fontFamily: "inherit" }}>
            <option value="all">All Types</option>
            {feeTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          {canManage && <button onClick={() => setShowCreate(true)} style={{ marginLeft: "auto", background: "#6366F1", border: "none", borderRadius: 8, padding: "8px 20px", cursor: "pointer", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>+ New Invoice</button>}
        </>}
      </div>

      {activeTab === "records" && (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead style={{ borderBottom: "1px solid var(--border)" }}><tr>{["Invoice No", "Student", "Fee Type", "Amount", "Paid", "Balance", "Due Date", "Method", "Status", "Action"].map((header) => <th key={header} style={{ padding: "10px 14px", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textAlign: "left", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>{header}</th>)}</tr></thead>
              <tbody>
                {paged.length === 0 ? <tr><td colSpan={10}><EmptyState>No fee records match the current filters.</EmptyState></td></tr> : paged.map((record, index) => {
                  const colors = feeStatusColors[String(record.status).toLowerCase()] || feeStatusColors.pending;
                  return (
                    <tr key={record.id} style={{ borderBottom: index < paged.length - 1 ? "1px solid var(--border)" : "none" }}>
                      <td style={{ padding: "11px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "#818CF8" }}>{record.invoice_number || `INV-${record.id}`}</td>
                      <td style={{ padding: "11px 14px", fontSize: 13, fontWeight: 600, color: "var(--foreground)", whiteSpace: "nowrap" }}>{record.student_name || "-"}</td>
                      <td style={{ padding: "11px 14px", fontSize: 13, color: "var(--foreground)" }}>{record.fee_type || record.title}</td>
                      <td style={{ padding: "11px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--foreground)" }}>{formatMoney(record.total_amount)}</td>
                      <td style={{ padding: "11px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "#10B981" }}>{formatMoney(record.paid_amount)}</td>
                      <td style={{ padding: "11px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: moneyNumber(record.balance) > 0 ? "#EF4444" : "#10B981" }}>{formatMoney(record.balance)}</td>
                      <td style={{ padding: "11px 14px", fontSize: 12, color: "var(--muted-foreground)", fontFamily: "JetBrains Mono, monospace" }}>{formatDate(record.due_date)}</td>
                      <td style={{ padding: "11px 14px", fontSize: 12, color: "var(--muted-foreground)" }}>{record.payment_method ? titleCase(record.payment_method) : "-"}</td>
                      <td style={{ padding: "11px 14px" }}><Badge {...colors} label={titleCase(String(record.status))} /></td>
                      <td style={{ padding: "11px 14px" }}>
                        <div style={{ display: "flex", gap: 6 }}>
                          <button onClick={() => setSelectedRecord(record)} style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#818CF8", borderRadius: 7, padding: "4px 9px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>View</button>
                          {canManage && <button onClick={() => setEditingRecord(record)} style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)", color: "#38BDF8", borderRadius: 7, padding: "4px 9px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Edit</button>}
                          {canManage && <button onClick={() => setPayingRecord(record)} disabled={moneyNumber(record.balance) <= 0} style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)", color: "#10B981", borderRadius: 7, padding: "4px 9px", cursor: moneyNumber(record.balance) > 0 ? "pointer" : "not-allowed", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Pay</button>}
                          {canManage && <button onClick={() => removeFee(record)} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#EF4444", borderRadius: 7, padding: "4px 9px", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Delete</button>}
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
            <div style={{ display: "flex", gap: 6 }}>{Array.from({ length: totalPages }, (_, i) => i + 1).slice(Math.max(0, page - 3), page + 2).map((p) => <button key={p} onClick={() => setPage(p)} style={{ width: 30, height: 30, borderRadius: 7, border: "1px solid", borderColor: p === page ? "#6366F1" : "var(--border)", background: p === page ? "rgba(99,102,241,0.15)" : "transparent", color: p === page ? "#818CF8" : "var(--muted-foreground)", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>{p}</button>)}</div>
          </div>
        </div>
      )}

      {activeTab === "analytics" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 16 }}>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 20 }}>Monthly Collection</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data?.fee_collection || []} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2235" />
                <XAxis dataKey="month" tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#6B7094", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${(Number(value) / 1000).toFixed(0)}k`} />
                <Tooltip {...TooltipStyle} formatter={(value) => [formatMoney(Number(value)), ""]} />
                <Bar dataKey="collected" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={30} name="Collected" />
                <Bar dataKey="pending" fill="#EF4444" radius={[4, 4, 0, 0]} maxBarSize={30} name="Pending" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: 22 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 20 }}>Payment Status Distribution</div>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3}>{pieData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Pie>
                <Tooltip {...TooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 8, flexWrap: "wrap" }}>{pieData.map((item) => <div key={item.name} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--muted-foreground)" }}><div style={{ width: 8, height: 8, borderRadius: 2, background: item.color }} />{item.name} ({item.value})</div>)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
