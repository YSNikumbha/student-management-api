document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  try {
    const [summary, activity, attention] = await Promise.all([
      AdminApp.authFetch("/dashboard/summary"),
      AdminApp.authFetch("/dashboard/recent-activity"),
      AdminApp.authFetch("/dashboard/attention"),
    ]);

    renderSummary(summary);
    renderAttention(attention);
    renderRecentStudents(activity.recent_students);
    renderRecentPayments(activity.recent_payments);
    renderRecentAttendance(activity.recent_attendance);
  } catch (error) {
    AdminApp.showAlert("#dashboard-alert", error.message, "danger");
    renderAttention(null);
    setRecentEmpty("#recent-students-body", 5, "No students found.");
    setRecentEmpty("#recent-payments-body", 5, "No payments recorded yet.");
    setRecentEmpty("#recent-attendance-body", 4, "No attendance records found.");
  }
}

function renderSummary(summary) {
  document.querySelector("#total-students").textContent = summary.students.total;
  document.querySelector("#total-courses").textContent = summary.courses.total;
  document.querySelector("#active-students").textContent = summary.students.active;
  document.querySelector("#active-courses").textContent = summary.courses.active;
  document.querySelector("#today-marked").textContent = summary.attendance_today.marked;
  document.querySelector("#fees-collected").textContent = AdminApp.formatCurrency(summary.fees.total_collected);
  document.querySelector("#fees-pending").textContent = AdminApp.formatCurrency(summary.fees.total_pending);
  document.querySelector("#fees-overdue").textContent = summary.fees.overdue_count;
}

function renderAttention(attention) {
  const container = document.querySelector("#attention-widgets");
  if (!container) {
    return;
  }

  if (!attention) {
    container.innerHTML = '<div class="activity-empty">Unable to load attention items.</div>';
    return;
  }

  const groups = [
    {
      title: "Below 75% Attendance",
      href: "/admin/attendance",
      icon: "bi-exclamation-triangle",
      items: attention.low_attendance_students.map((item) => ({
        label: item.student_name,
        detail: `${item.student_code} · ${item.attendance_percentage}%`,
        url: item.url,
        warning: true,
      })),
    },
    {
      title: "Overdue Fees",
      href: "/admin/fees?status=overdue",
      icon: "bi-receipt",
      items: attention.overdue_fees.map((item) => ({
        label: item.student_name,
        detail: `${item.title} · ${AdminApp.formatCurrency(item.balance)}`,
        url: item.url,
        warning: true,
      })),
    },
    {
      title: "Fees Due Soon",
      href: "/admin/fees",
      icon: "bi-calendar-event",
      items: attention.fees_due_soon.map((item) => ({
        label: item.student_name,
        detail: `${item.title} · due ${AdminApp.escapeHtml(item.due_date)}`,
        url: item.url,
      })),
    },
    {
      title: "Unmarked Today",
      href: "/admin/attendance",
      icon: "bi-calendar-x",
      items: attention.unmarked_attendance_sessions_today.map((item) => ({
        label: item.subject_name,
        detail: item.batch_name,
        url: item.url,
      })),
    },
    {
      title: "Recently Admitted",
      href: "/admin/students",
      icon: "bi-person-plus",
      items: attention.recently_admitted_students.map((item) => ({
        label: item.student_name,
        detail: `${item.student_code} · ${AdminApp.formatDate(item.admission_date || item.created_at)}`,
        url: item.url,
      })),
    },
    {
      title: "Recent Payments",
      href: "/admin/fees",
      icon: "bi-cash-stack",
      items: attention.recent_payments.map((item) => ({
        label: item.student_name,
        detail: `${item.fee_title} · ${AdminApp.formatCurrency(item.amount)}`,
        url: "/admin/fees",
      })),
    },
  ];

  container.innerHTML = groups.map((group) => renderAttentionWidget(group)).join("");
}

function renderAttentionWidget(group) {
  const visibleItems = group.items.slice(0, 3);
  const itemHtml = visibleItems.length
    ? visibleItems.map((item) => `
        <a class="attention-item ${item.warning ? "attention-warning" : ""}" href="${AdminApp.escapeHtml(item.url)}">
          <span class="attention-item-label">${AdminApp.escapeHtml(item.label)}</span>
          <span class="attention-item-detail">${AdminApp.escapeHtml(item.detail)}</span>
        </a>
      `).join("")
    : '<div class="attention-empty">No items.</div>';

  return `
    <article class="attention-widget">
      <div class="attention-widget-header">
        <div>
          <i class="bi ${group.icon}"></i>
          <span>${AdminApp.escapeHtml(group.title)}</span>
        </div>
        <a href="${AdminApp.escapeHtml(group.href)}">${group.items.length}</a>
      </div>
      <div class="attention-list">
        ${itemHtml}
      </div>
    </article>
  `;
}

function renderRecentStudents(students) {
  const container = document.querySelector("#recent-students-list");

  if (!students.length) {
    container.innerHTML = '<div class="activity-empty">No students found.</div>';
    return;
  }

  container.innerHTML = students.map((student) => `
    <div class="activity-card">
      <div class="activity-card-body">
        <div class="activity-card-primary">
          <div class="activity-card-title">${AdminApp.escapeHtml(student.name)}</div>
          <div class="activity-card-subtitle">${AdminApp.escapeHtml(student.student_code)}</div>
        </div>
        <div class="activity-card-secondary">
          <span class="activity-badge">${AdminApp.statusBadge(student.status)}</span>
        </div>
      </div>
      <div class="activity-card-footer">
        <span class="activity-meta">${AdminApp.escapeHtml(student.email || "")}</span>
      </div>
    </div>
  `).join("");
}

function renderRecentPayments(payments) {
  const container = document.querySelector("#recent-payments-list");

  if (!payments.length) {
    container.innerHTML = '<div class="activity-empty">No payments recorded yet.</div>';
    return;
  }

  container.innerHTML = payments.map((payment) => `
    <div class="activity-card">
      <div class="activity-card-body">
        <div class="activity-card-primary">
          <div class="activity-card-title">${AdminApp.escapeHtml(payment.student_name)}</div>
          <div class="activity-card-subtitle">${AdminApp.escapeHtml(payment.fee_title)}</div>
        </div>
        <div class="activity-card-secondary">
          <span class="activity-amount">${AdminApp.formatCurrency(payment.amount)}</span>
        </div>
      </div>
      <div class="activity-card-footer">
        <span class="activity-meta">${AdminApp.escapeHtml(payment.payment_date)} · ${AdminApp.escapeHtml(formatPaymentMethod(payment.payment_method))}</span>
      </div>
    </div>
  `).join("");
}

function renderRecentAttendance(records) {
  const container = document.querySelector("#recent-attendance-list");

  if (!records.length) {
    container.innerHTML = '<div class="activity-empty">No attendance records found.</div>';
    return;
  }

  container.innerHTML = records.map((record) => `
    <div class="activity-card">
      <div class="activity-card-body">
        <div class="activity-card-primary">
          <div class="activity-card-title">${AdminApp.escapeHtml(record.student_name)}</div>
          <div class="activity-card-subtitle">${AdminApp.escapeHtml(record.date)}</div>
        </div>
        <div class="activity-card-secondary">
          <span class="activity-badge">${AdminApp.attendanceBadge(record.status)}</span>
        </div>
      </div>
      <div class="activity-card-footer">
        <span class="activity-meta">Updated ${AdminApp.escapeHtml(AdminApp.formatDate(record.updated_at))}</span>
      </div>
    </div>
  `).join("");
}

function setRecentEmpty(target, colspan, message) {
  const element = typeof target === "string" ? document.querySelector(target) : target;
  if (!element) {
    return;
  }

  element.innerHTML = `
    <tr>
      <td colspan="${colspan}" class="text-center text-muted py-4">${AdminApp.escapeHtml(message)}</td>
    </tr>
  `;
}

function formatPaymentMethod(value) {
  const labels = {
    cash: "Cash",
    upi: "UPI",
    card: "Card",
    bank_transfer: "Bank Transfer",
  };
  return labels[value] || value;
}
