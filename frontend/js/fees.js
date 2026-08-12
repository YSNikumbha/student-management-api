let fees = [];
let students = [];
let courses = [];
let currentUser;
let feeModal;
let paymentModal;
let feeDetailsModal;
let activeDetailsFeeId = null;
let feePageData = null;
let feeState = {
  page: 1,
  pageSize: 10,
  search: "",
  status: "",
  courseId: "",
  dueAfter: "",
  dueBefore: "",
  sortBy: "due_date",
  sortOrder: "asc",
};

document.addEventListener("DOMContentLoaded", () => {
  currentUser = AdminApp.getCurrentUser();
  feeModal = new bootstrap.Modal(document.querySelector("#feeModal"));
  paymentModal = new bootstrap.Modal(document.querySelector("#paymentModal"));
  feeDetailsModal = new bootstrap.Modal(document.querySelector("#feeDetailsModal"));

  const addButton = document.querySelector("#open-add-fee");
  if (!isFeeManager()) {
    addButton.classList.add("d-none");
  }

  addButton.addEventListener("click", prepareAddFee);
  document.querySelector("#fee-form").addEventListener("submit", saveFee);
  document.querySelector("#payment-form").addEventListener("submit", recordPayment);
  document.querySelector("#fee-search").addEventListener("input", AdminApp.debounce(() => {
    feeState.search = document.querySelector("#fee-search").value.trim();
    feeState.page = 1;
    loadFees();
  }));
  document.querySelector("#fee-status-filter").addEventListener("change", () => {
    feeState.status = document.querySelector("#fee-status-filter").value;
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fee-course-filter").addEventListener("change", () => {
    feeState.courseId = document.querySelector("#fee-course-filter").value;
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fee-due-after-filter").addEventListener("change", () => {
    feeState.dueAfter = document.querySelector("#fee-due-after-filter").value;
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fee-due-before-filter").addEventListener("change", () => {
    feeState.dueBefore = document.querySelector("#fee-due-before-filter").value;
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fee-sort").addEventListener("change", () => {
    const [sortBy, sortOrder] = document.querySelector("#fee-sort").value.split(":");
    feeState.sortBy = sortBy;
    feeState.sortOrder = sortOrder;
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fee-page-size").addEventListener("change", () => {
    feeState.pageSize = Number(document.querySelector("#fee-page-size").value);
    feeState.page = 1;
    loadFees();
  });
  document.querySelector("#fees-table-body").addEventListener("click", handleFeeAction);
  document.querySelector("#payment-history-body").addEventListener("click", handlePaymentAction);

  loadFeesPage();
});

function isFeeManager() {
  return ["admin", "accountant"].includes(currentUser?.role);
}

function canRecordPayments() {
  return ["admin", "accountant", "staff"].includes(currentUser?.role);
}

async function loadFeesPage() {
  try {
    await Promise.all([loadStudents(), loadCourses()]);
    await Promise.all([loadFeeSummary(), loadFees()]);
  } catch (error) {
    AdminApp.showAlert("#fees-alert", error.message, "danger");
  }
}

async function loadStudents() {
  const response = await AdminApp.authFetch("/students?page_size=100&sort_by=first_name&sort_order=asc");
  students = AdminApp.getItems(response);
  renderStudentOptions();
}

async function loadCourses() {
  const response = await AdminApp.authFetch("/courses?page_size=100&sort_by=name&sort_order=asc");
  courses = AdminApp.getItems(response);
  renderCourseFilter();
}

async function loadFeeSummary() {
  const summary = await AdminApp.authFetch("/fees/summary");
  document.querySelector("#summary-assigned").textContent = AdminApp.formatCurrency(summary.total_assigned);
  document.querySelector("#summary-collected").textContent = AdminApp.formatCurrency(summary.total_collected);
  document.querySelector("#summary-pending").textContent = AdminApp.formatCurrency(summary.total_pending);
  document.querySelector("#summary-overdue").textContent = summary.overdue_count;
}

async function loadFees() {
  const tableBody = document.querySelector("#fees-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  const query = AdminApp.buildQueryString({
    search: feeState.search,
    status: feeState.status,
    course_id: feeState.courseId,
    due_after: feeState.dueAfter,
    due_before: feeState.dueBefore,
    page: feeState.page,
    page_size: feeState.pageSize,
    sort_by: feeState.sortBy,
    sort_order: feeState.sortOrder,
  });
  const response = await AdminApp.authFetch(`/fees${query}`);
  fees = AdminApp.getItems(response);
  feePageData = response;
  renderFeeTable();
  renderFeePagination();
}

function renderStudentOptions(selectedStudentId = null) {
  const select = document.querySelector("#fee-student");
  const selectedValue = selectedStudentId === null || selectedStudentId === undefined
    ? ""
    : String(selectedStudentId);

  if (students.length === 0) {
    select.innerHTML = '<option value="">No students found</option>';
    return;
  }

  select.innerHTML = `
    <option value="">Select student</option>
    ${students.map((student) => {
      const label = `${student.first_name} ${student.last_name} (${student.student_code})`;
      return `
        <option value="${student.id}" ${String(student.id) === selectedValue ? "selected" : ""}>
          ${AdminApp.escapeHtml(label)}
        </option>
      `;
    }).join("")}
  `;
}

function renderCourseFilter() {
  const select = document.querySelector("#fee-course-filter");
  select.innerHTML = `
    <option value="">All courses</option>
    ${courses.map((course) => `
      <option value="${course.id}">
        ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
      </option>
    `).join("")}
  `;
}

function renderFeeTable() {
  const tableBody = document.querySelector("#fees-table-body");
  const studentById = new Map(students.map((student) => [student.id, student]));

  if (fees.length === 0) {
    const hasFilters = Boolean(
      feeState.search ||
      feeState.status ||
      feeState.courseId ||
      feeState.dueAfter ||
      feeState.dueBefore
    );
    const message = hasFilters ? "No fee records match the selected filters." : "No fee records found.";
    tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted py-4">${message}</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = fees.map((fee) => {
    const student = studentById.get(fee.student_id);
    const studentName = fee.student_name || (student ? `${student.first_name} ${student.last_name}` : `Student #${fee.student_id}`);
    const studentCode = fee.student_code || student?.student_code || "";
    const balance = Number(fee.balance || 0);
    const total = Number(fee.total_amount || 0);
    const paid = Number(fee.paid_amount || 0);
    const canRecordPayment = balance > 0 && canRecordPayments();
    const progressPercent = total > 0 ? Math.round((paid / total) * 100) : 0;
    const dueDate = new Date(fee.due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDateText = getDueDateText(dueDate, today);

    const feeManagerActions = isFeeManager()
      ? `
          <button class="btn btn-sm btn-action-view" type="button" data-action="details" data-id="${fee.id}" aria-label="View fee details">
            <i class="bi bi-eye"></i>
          </button>
          <button class="btn btn-sm btn-action-edit" type="button" data-action="edit" data-id="${fee.id}" aria-label="Edit fee">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${fee.id}" aria-label="Delete fee">
            <i class="bi bi-trash"></i>
          </button>
        `
      : `
          <button class="btn btn-sm btn-action-view" type="button" data-action="details" data-id="${fee.id}" aria-label="View fee details">
            <i class="bi bi-eye"></i>
          </button>
        `;
    const paymentButton = canRecordPayment
      ? `
          <button class="btn btn-sm btn-outline-success btn-icon" type="button" data-action="pay" data-id="${fee.id}" aria-label="Record payment">
            <i class="bi bi-cash-coin"></i>
          </button>
        `
      : "";

    return `
      <tr>
        <td>
          <div class="fw-semibold">${AdminApp.escapeHtml(studentName)}</div>
          <div class="small muted-cell">${AdminApp.escapeHtml(studentCode)}</div>
        </td>
        <td>
          <div class="fw-semibold">${AdminApp.escapeHtml(fee.title)}</div>
          <div class="small muted-cell">${AdminApp.escapeHtml(fee.description || "")}</div>
        </td>
        <td class="money-cell">${AdminApp.formatCurrency(fee.total_amount)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(fee.paid_amount)}</td>
        <td class="money-cell ${balance > 0 ? "balance-due" : "balance-paid"}">${AdminApp.formatCurrency(fee.balance)}</td>
        <td>${dueDateText}</td>
        <td>${AdminApp.feeStatusBadge(fee.status)}</td>
        <td>
          <div class="progress" style="height: 6px; margin-bottom: 0.5rem;">
            <div class="progress-bar ${progressPercent === 100 ? 'bg-success' : 'bg-primary'}" style="width: ${progressPercent}%"></div>
          </div>
          <small class="text-muted">${progressPercent}% paid</small>
        </td>
        <td class="text-end">
          <span class="action-buttons">
            ${paymentButton}
            ${feeManagerActions}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function getDueDateText(dueDate, today) {
  const diffTime = dueDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    return `<span class="text-danger fw-semibold">Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? 's' : ''}</span>`;
  } else if (diffDays === 0) {
    return `<span class="text-warning fw-semibold">Due today</span>`;
  } else if (diffDays <= 7) {
    return `<span class="text-warning">Due in ${diffDays} day${diffDays !== 1 ? 's' : ''}</span>`;
  } else {
    return AdminApp.escapeHtml(dueDate.toISOString().slice(0, 10));
  }
}

function renderFeePagination() {
  AdminApp.renderPagination("#fees-pagination", feePageData, (page) => {
    feeState.page = page;
    loadFees();
  });
}

function prepareAddFee() {
  document.querySelector("#fee-form").reset();
  document.querySelector("#fee-id").value = "";
  document.querySelector("#feeModalTitle").textContent = "Assign Fee";
  document.querySelector("#fee-student-field").classList.remove("d-none");
  document.querySelector("#fee-student").required = true;
  renderStudentOptions();
  AdminApp.clearAlert("#fee-form-alert");
}

function prepareEditFee(feeId) {
  const fee = fees.find((item) => item.id === feeId);
  if (!fee) {
    AdminApp.showAlert("#fees-alert", "Fee record not found.", "danger");
    return;
  }

  document.querySelector("#fee-form").reset();
  document.querySelector("#fee-id").value = fee.id;
  document.querySelector("#feeModalTitle").textContent = "Edit Fee";
  document.querySelector("#fee-student-field").classList.add("d-none");
  document.querySelector("#fee-student").required = false;
  document.querySelector("#fee-title").value = fee.title;
  document.querySelector("#fee-description").value = fee.description || "";
  document.querySelector("#fee-total-amount").value = fee.total_amount;
  document.querySelector("#fee-due-date").value = fee.due_date;
  AdminApp.clearAlert("#fee-form-alert");
  feeModal.show();
}

async function saveFee(event) {
  event.preventDefault();

  const form = document.querySelector("#fee-form");
  const saveButton = document.querySelector("#save-fee");
  const feeId = document.querySelector("#fee-id").value;

  AdminApp.clearFormErrors(form);

  const titleInput = document.querySelector("#fee-title");
  const descriptionInput = document.querySelector("#fee-description");
  const totalAmountInput = document.querySelector("#fee-total-amount");
  const dueDateInput = document.querySelector("#fee-due-date");
  const studentInput = document.querySelector("#fee-student");

  const titleError = AdminApp.validateName(titleInput.value, "Fee title");
  const descriptionError = descriptionInput.value.trim() && descriptionInput.value.trim().length > 500
    ? "Description must be 500 characters or less."
    : null;
  const totalAmountError = totalAmountInput.value ? null : "Total amount is required.";
  const dueDateError = dueDateInput.value ? null : "Due date is required.";
  const studentError = !feeId && !studentInput.value ? "Student is required." : null;

  let hasError = false;

  if (titleError) {
    AdminApp.showFieldError(titleInput, titleError);
    hasError = true;
  }

  if (descriptionError) {
    AdminApp.showFieldError(descriptionInput, descriptionError);
    hasError = true;
  }

  if (totalAmountError) {
    AdminApp.showFieldError(totalAmountInput, totalAmountError);
    hasError = true;
  }

  if (dueDateError) {
    AdminApp.showFieldError(dueDateInput, dueDateError);
    hasError = true;
  }

  if (studentError) {
    AdminApp.showFieldError(studentInput, studentError);
    hasError = true;
  }

  if (hasError) {
    AdminApp.focusFirstInvalidField(form);
    return;
  }

  const payload = {
    title: titleInput.value.trim(),
    description: descriptionInput.value.trim() || null,
    total_amount: totalAmountInput.value,
    due_date: dueDateInput.value,
  };

  if (!feeId) {
    payload.student_id = Number(studentInput.value);
  }

  AdminApp.clearAlert("#fee-form-alert");
  AdminApp.setButtonLoading(saveButton, true);

  try {
    if (feeId) {
      await AdminApp.authFetch(`/fees/${feeId}`, {
        method: "PUT",
        body: payload,
      });
      AdminApp.showToast("success", "Fee record updated successfully.");
    } else {
      await AdminApp.authFetch("/fees", {
        method: "POST",
        body: payload,
      });
      feeState.page = 1;
      AdminApp.showToast("success", "Fee assigned successfully.");
    }

    feeModal.hide();
    form.reset();
    await refreshFeesAndSummary();
  } catch (error) {
    AdminApp.showAlert("#fee-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function handleFeeAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const feeId = Number(button.dataset.id);

  if (button.dataset.action === "details") {
    showFeeDetails(feeId);
    return;
  }

  if (button.dataset.action === "pay") {
    openPaymentModal(feeId);
    return;
  }

  if (button.dataset.action === "edit") {
    prepareEditFee(feeId);
    return;
  }

  const confirmed = await AdminApp.confirmAction({
    title: "Delete Fee Record",
    message: "Are you sure you want to delete this fee record? This action cannot be undone.",
    confirmLabel: "Delete",
    cancelLabel: "Cancel",
    danger: true,
  });

  if (!confirmed) {
    return;
  }

  button.disabled = true;
  try {
    await AdminApp.authFetch(`/fees/${feeId}`, { method: "DELETE" });
    AdminApp.showToast("success", "Fee record deleted successfully.");
    await refreshFeesAndSummary();
  } catch (error) {
    const message = error.status === 409 && error.message.includes("payments")
      ? "Cannot delete this fee because payments have already been recorded."
      : error.message;
    AdminApp.showAlert("#fees-alert", message, "danger");
  } finally {
    button.disabled = false;
  }
}

function openPaymentModal(feeId) {
  const fee = fees.find((item) => item.id === feeId);
  if (!fee) {
    AdminApp.showAlert("#fees-alert", "Fee record not found.", "danger");
    return;
  }

  const student = students.find((item) => item.id === fee.student_id);
  const studentName = fee.student_name || (student ? `${student.first_name} ${student.last_name}` : `Student #${fee.student_id}`);

  document.querySelector("#payment-form").reset();
  document.querySelector("#payment-fee-id").value = fee.id;
  document.querySelector("#payment-date").value = getTodayDateString();
  document.querySelector("#payment-amount").max = fee.balance;
  document.querySelector("#payment-fee-summary").innerHTML = `
    <div>
      <span class="mini-label">Student</span>
      <strong>${AdminApp.escapeHtml(studentName)}</strong>
    </div>
    <div>
      <span class="mini-label">Fee</span>
      <strong>${AdminApp.escapeHtml(fee.title)}</strong>
    </div>
    <div>
      <span class="mini-label">Paid</span>
      <strong>${AdminApp.formatCurrency(fee.paid_amount)}</strong>
    </div>
    <div>
      <span class="mini-label">Remaining</span>
      <strong>${AdminApp.formatCurrency(fee.balance)}</strong>
    </div>
  `;
  AdminApp.clearAlert("#payment-form-alert");
  paymentModal.show();
}

async function recordPayment(event) {
  event.preventDefault();

  const saveButton = document.querySelector("#save-payment");
  const feeId = Number(document.querySelector("#payment-fee-id").value);
  const fee = fees.find((item) => item.id === feeId);
  const amountValue = document.querySelector("#payment-amount").value;
  const amount = Number(amountValue);
  const balance = Number(fee?.balance || 0);

  AdminApp.clearAlert("#payment-form-alert");

  if (!Number.isFinite(amount) || amount <= 0) {
    AdminApp.showAlert("#payment-form-alert", "Payment amount must be greater than zero.", "warning");
    return;
  }

  if (amount > balance) {
    AdminApp.showAlert("#payment-form-alert", "Payment amount cannot exceed remaining balance.", "warning");
    return;
  }

  const payload = {
    amount: amountValue,
    payment_date: document.querySelector("#payment-date").value,
    payment_method: document.querySelector("#payment-method").value,
    reference_number: document.querySelector("#payment-reference").value.trim() || null,
    notes: document.querySelector("#payment-notes").value.trim() || null,
  };

  AdminApp.setButtonLoading(saveButton, true, "Recording...");

  try {
    await AdminApp.authFetch(`/fees/${feeId}/payments`, {
      method: "POST",
      body: payload,
    });
    paymentModal.hide();
    document.querySelector("#payment-form").reset();
    AdminApp.showAlert("#fees-alert", "Payment recorded successfully.", "success");
    await refreshFeesAndSummary();
  } catch (error) {
    AdminApp.showAlert("#payment-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function showFeeDetails(feeId) {
  activeDetailsFeeId = feeId;
  const summary = document.querySelector("#fee-details-summary");
  const tableBody = document.querySelector("#payment-history-body");

  summary.innerHTML = "";
  tableBody.innerHTML = `
    <tr>
      <td colspan="7" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;
  AdminApp.clearAlert("#fee-details-alert");
  feeDetailsModal.show();

  try {
    const detail = await AdminApp.authFetch(`/fees/${feeId}`);
    renderFeeDetails(detail);
  } catch (error) {
    AdminApp.showAlert("#fee-details-alert", error.message, "danger");
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">Unable to load payment history.</td>
      </tr>
    `;
  }
}

function renderFeeDetails(detail) {
  const student = students.find((item) => item.id === detail.student_id);
  const studentName = detail.student_name || (student ? `${student.first_name} ${student.last_name}` : `Student #${detail.student_id}`);

  document.querySelector("#feeDetailsModalTitle").textContent = `Fee Details - ${detail.title}`;
  document.querySelector("#fee-details-summary").innerHTML = `
    <div>
      <span class="mini-label">Student</span>
      <strong>${AdminApp.escapeHtml(studentName)}</strong>
    </div>
    <div>
      <span class="mini-label">Total</span>
      <strong>${AdminApp.formatCurrency(detail.total_amount)}</strong>
    </div>
    <div>
      <span class="mini-label">Paid</span>
      <strong>${AdminApp.formatCurrency(detail.paid_amount)}</strong>
    </div>
    <div>
      <span class="mini-label">Balance</span>
      <strong>${AdminApp.formatCurrency(detail.balance)}</strong>
    </div>
    <div>
      <span class="mini-label">Due Date</span>
      <strong>${AdminApp.escapeHtml(detail.due_date)}</strong>
    </div>
    <div>
      <span class="mini-label">Status</span>
      <strong>${AdminApp.escapeHtml(detail.status)}</strong>
    </div>
  `;

  renderPaymentHistory(detail.payments || []);
}

function renderPaymentHistory(payments) {
  const tableBody = document.querySelector("#payment-history-body");

  if (payments.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">No payments recorded yet.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = payments.map((payment) => {
    const deleteButton = isFeeManager()
      ? `
          <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete-payment" data-id="${payment.id}" aria-label="Delete payment">
            <i class="bi bi-trash"></i>
          </button>
        `
      : "";
    return `
      <tr>
        <td>${AdminApp.escapeHtml(payment.payment_date)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(payment.amount)}</td>
        <td>${AdminApp.escapeHtml(formatPaymentMethod(payment.payment_method))}</td>
        <td>${AdminApp.escapeHtml(payment.reference_number || "")}</td>
        <td>${AdminApp.escapeHtml(`User #${payment.recorded_by}`)}</td>
        <td>${AdminApp.escapeHtml(payment.notes || "")}</td>
        <td class="text-end">${deleteButton}</td>
      </tr>
    `;
  }).join("");
}

async function handlePaymentAction(event) {
  const button = event.target.closest("button[data-action='delete-payment']");
  if (!button) {
    return;
  }

  const confirmed = await AdminApp.confirmAction({
    title: "Delete Payment",
    message: "Are you sure you want to delete this payment? This action cannot be undone.",
    confirmLabel: "Delete",
    cancelLabel: "Cancel",
    danger: true,
  });

  if (!confirmed) {
    return;
  }

  button.disabled = true;
  try {
    await AdminApp.authFetch(`/payments/${button.dataset.id}`, { method: "DELETE" });
    AdminApp.showToast("success", "Payment deleted successfully.");
    await refreshFeesAndSummary();
    if (activeDetailsFeeId !== null) {
      await showFeeDetails(activeDetailsFeeId);
    }
  } catch (error) {
    AdminApp.showAlert("#fee-details-alert", error.message, "danger");
  } finally {
    button.disabled = false;
  }
}

async function refreshFeesAndSummary() {
  await Promise.all([loadFeeSummary(), loadFees()]);
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

function getTodayDateString() {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - timezoneOffset).toISOString().slice(0, 10);
}
