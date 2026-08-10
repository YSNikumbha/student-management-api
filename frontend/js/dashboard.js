document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  try {
    const [summary, activity] = await Promise.all([
      AdminApp.authFetch("/dashboard/summary"),
      AdminApp.authFetch("/dashboard/recent-activity"),
    ]);

    renderSummary(summary);
    renderRecentStudents(activity.recent_students);
    renderRecentPayments(activity.recent_payments);
    renderRecentAttendance(activity.recent_attendance);
  } catch (error) {
    AdminApp.showAlert("#dashboard-alert", error.message, "danger");
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

function renderRecentStudents(students) {
  const tableBody = document.querySelector("#recent-students-body");

  if (!students.length) {
    setRecentEmpty(tableBody, 5, "No students found.");
    return;
  }

  tableBody.innerHTML = students.map((student) => `
    <tr>
      <td>${AdminApp.escapeHtml(student.student_code)}</td>
      <td>${AdminApp.escapeHtml(student.name)}</td>
      <td>${AdminApp.escapeHtml(student.email)}</td>
      <td>${AdminApp.escapeHtml(student.course_id ?? "Not Assigned")}</td>
      <td>${AdminApp.statusBadge(student.status)}</td>
    </tr>
  `).join("");
}

function renderRecentPayments(payments) {
  const tableBody = document.querySelector("#recent-payments-body");

  if (!payments.length) {
    setRecentEmpty(tableBody, 5, "No payments recorded yet.");
    return;
  }

  tableBody.innerHTML = payments.map((payment) => `
    <tr>
      <td>${AdminApp.escapeHtml(payment.student_name)}</td>
      <td>${AdminApp.escapeHtml(payment.fee_title)}</td>
      <td class="money-cell">${AdminApp.formatCurrency(payment.amount)}</td>
      <td>${AdminApp.escapeHtml(payment.payment_date)}</td>
      <td>${AdminApp.escapeHtml(formatPaymentMethod(payment.payment_method))}</td>
    </tr>
  `).join("");
}

function renderRecentAttendance(records) {
  const tableBody = document.querySelector("#recent-attendance-body");

  if (!records.length) {
    setRecentEmpty(tableBody, 4, "No attendance records found.");
    return;
  }

  tableBody.innerHTML = records.map((record) => `
    <tr>
      <td>${AdminApp.escapeHtml(record.date)}</td>
      <td>${AdminApp.escapeHtml(record.student_name)}</td>
      <td>${AdminApp.attendanceBadge(record.status)}</td>
      <td>${AdminApp.escapeHtml(AdminApp.formatDate(record.updated_at))}</td>
    </tr>
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
