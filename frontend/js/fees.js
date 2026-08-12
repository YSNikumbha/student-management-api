let fees = [];
let students = [];
let courses = [];
let academicYears = [];
let semesters = [];
let batches = [];
let feeCategories = [];
let feeStructures = [];
let currentUser;
let feeModal;
let paymentModal;
let feeDetailsModal;
let feeStructureModal;
let assignStructureModal;
let receiptModal;
let activeDetailsFeeId = null;
let activeReceiptPaymentId = null;
let feePageData = null;
let structurePageData = null;
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
let structureState = {
  page: 1,
  pageSize: 10,
  search: "",
  courseId: "",
  categoryId: "",
  isActive: "",
};

document.addEventListener("DOMContentLoaded", () => {
  currentUser = AdminApp.getCurrentUser();
  feeModal = new bootstrap.Modal(document.querySelector("#feeModal"));
  paymentModal = new bootstrap.Modal(document.querySelector("#paymentModal"));
  feeDetailsModal = new bootstrap.Modal(document.querySelector("#feeDetailsModal"));
  feeStructureModal = new bootstrap.Modal(document.querySelector("#feeStructureModal"));
  assignStructureModal = new bootstrap.Modal(document.querySelector("#assignStructureModal"));
  receiptModal = new bootstrap.Modal(document.querySelector("#receiptModal"));

  const addButton = document.querySelector("#open-add-fee");
  const addStructureButton = document.querySelector("#open-add-structure");
  if (!isFeeManager()) {
    addButton.classList.add("d-none");
    addStructureButton.classList.add("d-none");
  }

  addButton.addEventListener("click", prepareAddFee);
  document.querySelector("#fee-form").addEventListener("submit", saveFee);
  document.querySelector("#structure-form").addEventListener("submit", saveStructure);
  document.querySelector("#assign-structure-form").addEventListener("submit", assignStructure);
  document.querySelector("#installment-form").addEventListener("submit", saveInstallment);
  document.querySelector("#payment-form").addEventListener("submit", recordPayment);
  document.querySelector("#open-add-structure").addEventListener("click", prepareAddStructure);
  document.querySelector("#assign-target-type").addEventListener("change", updateAssignTargetVisibility);
  document.querySelector("#structure-course").addEventListener("change", () => loadStructureSemesters());
  document.querySelector("#structure-academic-year").addEventListener("change", () => loadStructureSemesters());
  document.querySelector("#download-receipt").addEventListener("click", downloadActiveReceipt);
  document.querySelector("#print-receipt").addEventListener("click", printReceipt);
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
  document.querySelector("#structures-table-body").addEventListener("click", handleStructureAction);
  document.querySelector("#installments-table-body").addEventListener("click", handleInstallmentAction);
  document.querySelector("#payment-history-body").addEventListener("click", handlePaymentAction);
  document.querySelector("#structure-search").addEventListener("input", AdminApp.debounce(() => {
    structureState.search = document.querySelector("#structure-search").value.trim();
    structureState.page = 1;
    loadStructures();
  }));
  document.querySelector("#structure-course-filter").addEventListener("change", () => {
    structureState.courseId = document.querySelector("#structure-course-filter").value;
    structureState.page = 1;
    loadStructures();
  });
  document.querySelector("#structure-category-filter").addEventListener("change", () => {
    structureState.categoryId = document.querySelector("#structure-category-filter").value;
    structureState.page = 1;
    loadStructures();
  });
  document.querySelector("#structure-active-filter").addEventListener("change", () => {
    structureState.isActive = document.querySelector("#structure-active-filter").value;
    structureState.page = 1;
    loadStructures();
  });

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
    await Promise.all([loadStudents(), loadCourses(), loadAcademicYears(), loadCategories(), loadBatches()]);
    await Promise.all([loadFeeSummary(), loadFees(), loadStructures()]);
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
  renderCourseOptions();
}

async function loadAcademicYears() {
  const response = await AdminApp.authFetch("/academic-years?page_size=100");
  academicYears = AdminApp.getItems(response);
  renderAcademicYearOptions();
}

async function loadCategories() {
  const response = await AdminApp.authFetch("/fees/categories?page_size=100");
  feeCategories = AdminApp.getItems(response);
  renderCategoryOptions();
}

async function loadBatches() {
  const response = await AdminApp.authFetch("/batches?page_size=100");
  batches = AdminApp.getItems(response);
  renderBatchOptions();
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
      <td colspan="9" class="text-center text-muted py-4">Loading...</td>
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

async function loadStructures() {
  const tableBody = document.querySelector("#structures-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="9" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  const query = AdminApp.buildQueryString({
    search: structureState.search,
    course_id: structureState.courseId,
    category_id: structureState.categoryId,
    is_active: structureState.isActive,
    page: structureState.page,
    page_size: structureState.pageSize,
  });
  const response = await AdminApp.authFetch(`/fees/structures${query}`);
  feeStructures = AdminApp.getItems(response);
  structurePageData = response;
  renderStructureTable();
  AdminApp.renderPagination("#structures-pagination", structurePageData, (page) => {
    structureState.page = page;
    loadStructures();
  });
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

  const structureFilter = document.querySelector("#structure-course-filter");
  structureFilter.innerHTML = select.innerHTML;
}

function renderCourseOptions(selectedCourseId = null) {
  const select = document.querySelector("#structure-course");
  const selectedValue = selectedCourseId === null || selectedCourseId === undefined ? "" : String(selectedCourseId);
  select.innerHTML = `
    <option value="">Select course</option>
    ${courses.map((course) => `
      <option value="${course.id}" ${String(course.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
      </option>
    `).join("")}
  `;
}

function renderAcademicYearOptions(selectedYearId = null) {
  const select = document.querySelector("#structure-academic-year");
  const selectedValue = selectedYearId === null || selectedYearId === undefined ? "" : String(selectedYearId);
  select.innerHTML = `
    <option value="">Select academic year</option>
    ${academicYears.map((year) => `
      <option value="${year.id}" ${String(year.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(year.name)}
      </option>
    `).join("")}
  `;
}

function renderCategoryOptions(selectedCategoryId = null) {
  const selectedValue = selectedCategoryId === null || selectedCategoryId === undefined ? "" : String(selectedCategoryId);
  const options = `
    <option value="">Select category</option>
    ${feeCategories.map((category) => `
      <option value="${category.id}" ${String(category.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(category.name)}
      </option>
    `).join("")}
  `;
  document.querySelector("#structure-category").innerHTML = options;
  document.querySelector("#structure-category-filter").innerHTML = `
    <option value="">All categories</option>
    ${feeCategories.map((category) => `
      <option value="${category.id}">
        ${AdminApp.escapeHtml(category.name)}
      </option>
    `).join("")}
  `;
}

function renderBatchOptions(selectedBatchId = null) {
  const select = document.querySelector("#assign-batch");
  const selectedValue = selectedBatchId === null || selectedBatchId === undefined ? "" : String(selectedBatchId);
  select.innerHTML = `
    <option value="">Select batch</option>
    ${batches.map((batch) => `
      <option value="${batch.id}" ${String(batch.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(batch.name)}
      </option>
    `).join("")}
  `;
}

function renderAssignStudentOptions(selectedStudentId = null) {
  const select = document.querySelector("#assign-student");
  const selectedValue = selectedStudentId === null || selectedStudentId === undefined ? "" : String(selectedStudentId);
  select.innerHTML = `
    <option value="">Select student</option>
    ${students.map((student) => `
      <option value="${student.id}" ${String(student.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(student.first_name)} ${AdminApp.escapeHtml(student.last_name)} (${AdminApp.escapeHtml(student.student_code)})
      </option>
    `).join("")}
  `;
}

async function loadStructureSemesters(selectedSemesterId = null) {
  const courseId = document.querySelector("#structure-course").value;
  const academicYearId = document.querySelector("#structure-academic-year").value;
  const select = document.querySelector("#structure-semester");

  if (!courseId || !academicYearId) {
    semesters = [];
    select.innerHTML = '<option value="">No semester</option>';
    return;
  }

  const query = AdminApp.buildQueryString({
    course_id: courseId,
    academic_year_id: academicYearId,
    page_size: 100,
  });
  const response = await AdminApp.authFetch(`/semesters${query}`);
  semesters = AdminApp.getItems(response);
  const selectedValue = selectedSemesterId === null || selectedSemesterId === undefined ? "" : String(selectedSemesterId);
  select.innerHTML = `
    <option value="">No semester</option>
    ${semesters.map((semester) => `
      <option value="${semester.id}" ${String(semester.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(semester.name)}
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
        <td colspan="9" class="text-center text-muted py-4">${message}</td>
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

function renderStructureTable() {
  const tableBody = document.querySelector("#structures-table-body");

  if (feeStructures.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="9" class="text-center text-muted py-4">No fee structures found.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = feeStructures.map((structure) => {
    const managerButtons = isFeeManager()
      ? `
          <button class="btn btn-sm btn-outline-success btn-icon" type="button" data-action="assign" data-id="${structure.id}" aria-label="Assign fee structure">
            <i class="bi bi-person-plus"></i>
          </button>
          <button class="btn btn-sm btn-action-edit" type="button" data-action="edit" data-id="${structure.id}" aria-label="Edit fee structure">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${structure.id}" aria-label="Delete fee structure">
            <i class="bi bi-trash"></i>
          </button>
        `
      : "";
    return `
      <tr>
        <td>
          <div class="fw-semibold">${AdminApp.escapeHtml(structure.name)}</div>
          <div class="small muted-cell">${AdminApp.escapeHtml(structure.description || "")}</div>
        </td>
        <td>${AdminApp.escapeHtml(structure.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(structure.academic_year_name || "")}</td>
        <td>${AdminApp.escapeHtml(structure.semester_name || "")}</td>
        <td>${AdminApp.escapeHtml(structure.category_name || "")}</td>
        <td class="money-cell">${AdminApp.formatCurrency(structure.total_amount)}</td>
        <td>${AdminApp.statusBadge(structure.is_active)}</td>
        <td>${structure.assignment_count || 0}</td>
        <td class="text-end">
          <span class="action-buttons">${managerButtons}</span>
        </td>
      </tr>
    `;
  }).join("");
}

function prepareAddStructure() {
  document.querySelector("#structure-form").reset();
  document.querySelector("#structure-id").value = "";
  document.querySelector("#feeStructureModalTitle").textContent = "Add Fee Structure";
  renderCourseOptions();
  renderAcademicYearOptions();
  renderCategoryOptions();
  document.querySelector("#structure-semester").innerHTML = '<option value="">No semester</option>';
  document.querySelector("#structure-active").value = "true";
  AdminApp.clearAlert("#structure-form-alert");
}

async function prepareEditStructure(structureId) {
  const structure = feeStructures.find((item) => item.id === structureId);
  if (!structure) {
    AdminApp.showAlert("#fees-alert", "Fee structure not found.", "danger");
    return;
  }

  document.querySelector("#structure-form").reset();
  document.querySelector("#structure-id").value = structure.id;
  document.querySelector("#feeStructureModalTitle").textContent = "Edit Fee Structure";
  document.querySelector("#structure-name").value = structure.name;
  document.querySelector("#structure-total-amount").value = structure.total_amount;
  document.querySelector("#structure-description").value = structure.description || "";
  document.querySelector("#structure-active").value = String(structure.is_active);
  renderCourseOptions(structure.course_id);
  renderAcademicYearOptions(structure.academic_year_id);
  renderCategoryOptions(structure.category_id);
  await loadStructureSemesters(structure.semester_id);
  AdminApp.clearAlert("#structure-form-alert");
  feeStructureModal.show();
}

async function saveStructure(event) {
  event.preventDefault();
  const structureId = document.querySelector("#structure-id").value;
  const saveButton = document.querySelector("#save-structure");
  const payload = {
    name: document.querySelector("#structure-name").value.trim(),
    course_id: Number(document.querySelector("#structure-course").value),
    academic_year_id: Number(document.querySelector("#structure-academic-year").value),
    semester_id: document.querySelector("#structure-semester").value ? Number(document.querySelector("#structure-semester").value) : null,
    category_id: Number(document.querySelector("#structure-category").value),
    total_amount: document.querySelector("#structure-total-amount").value,
    description: document.querySelector("#structure-description").value.trim() || null,
    is_active: document.querySelector("#structure-active").value === "true",
  };

  AdminApp.setButtonLoading(saveButton, true);
  AdminApp.clearAlert("#structure-form-alert");
  try {
    await AdminApp.authFetch(structureId ? `/fees/structures/${structureId}` : "/fees/structures", {
      method: structureId ? "PUT" : "POST",
      body: payload,
    });
    feeStructureModal.hide();
    AdminApp.showToast("success", structureId ? "Fee structure updated." : "Fee structure created.");
    await loadStructures();
  } catch (error) {
    AdminApp.showAlert("#structure-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

function prepareAssignStructure(structureId) {
  const structure = feeStructures.find((item) => item.id === structureId);
  if (!structure) {
    AdminApp.showAlert("#fees-alert", "Fee structure not found.", "danger");
    return;
  }
  document.querySelector("#assign-structure-form").reset();
  document.querySelector("#assign-structure-id").value = structure.id;
  document.querySelector("#assignStructureModalTitle").textContent = `Assign - ${structure.name}`;
  renderAssignStudentOptions();
  renderBatchOptions();
  updateAssignTargetVisibility();
  AdminApp.clearAlert("#assign-structure-alert");
  assignStructureModal.show();
}

function updateAssignTargetVisibility() {
  const targetType = document.querySelector("#assign-target-type").value;
  document.querySelector("#assign-student-field").classList.toggle("d-none", targetType !== "student");
  document.querySelector("#assign-batch-field").classList.toggle("d-none", targetType !== "batch");
}

async function assignStructure(event) {
  event.preventDefault();
  const structureId = document.querySelector("#assign-structure-id").value;
  const targetType = document.querySelector("#assign-target-type").value;
  const payload = {
    due_date: document.querySelector("#assign-due-date").value,
  };
  if (targetType === "student") {
    payload.student_id = Number(document.querySelector("#assign-student").value);
  } else {
    payload.batch_id = Number(document.querySelector("#assign-batch").value);
  }

  const button = document.querySelector("#save-assignment");
  AdminApp.setButtonLoading(button, true, "Assigning...");
  try {
    const result = await AdminApp.authFetch(`/fees/structures/${structureId}/assign`, {
      method: "POST",
      body: payload,
    });
    assignStructureModal.hide();
    AdminApp.showAlert("#fees-alert", `Assigned ${result.created} fee record(s). Skipped ${result.skipped}.`, "success");
    await Promise.all([loadStructures(), refreshFeesAndSummary()]);
  } catch (error) {
    AdminApp.showAlert("#assign-structure-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(button, false);
  }
}

async function handleStructureAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  const structureId = Number(button.dataset.id);
  if (button.dataset.action === "edit") {
    prepareEditStructure(structureId);
    return;
  }
  if (button.dataset.action === "assign") {
    prepareAssignStructure(structureId);
    return;
  }

  const confirmed = await AdminApp.confirmAction({
    title: "Delete Fee Structure",
    message: "Delete this fee structure? Assigned structures cannot be deleted.",
    confirmLabel: "Delete",
    danger: true,
  });
  if (!confirmed) {
    return;
  }
  try {
    await AdminApp.authFetch(`/fees/structures/${structureId}`, { method: "DELETE" });
    AdminApp.showToast("success", "Fee structure deleted.");
    await loadStructures();
  } catch (error) {
    AdminApp.showAlert("#fees-alert", error.message, "danger");
  }
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

async function openPaymentModal(feeId) {
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
  try {
    const detail = await AdminApp.authFetch(`/fees/${feeId}`);
    renderPaymentInstallmentOptions(detail.installments || []);
  } catch {
    renderPaymentInstallmentOptions([]);
  }
  AdminApp.clearAlert("#payment-form-alert");
  paymentModal.show();
}

function renderPaymentInstallmentOptions(installments) {
  const select = document.querySelector("#payment-installment");
  const openInstallments = installments.filter((installment) => Number(installment.balance || 0) > 0);
  select.innerHTML = '<option value="">Overall fee balance</option>' +
    openInstallments.map((installment) => `
      <option value="${installment.id}">
        ${AdminApp.escapeHtml(installment.title)} - ${AdminApp.formatCurrency(installment.balance)} due
      </option>
    `).join("");
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
    fee_installment_id: document.querySelector("#payment-installment").value
      ? Number(document.querySelector("#payment-installment").value)
      : null,
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
  const installmentBody = document.querySelector("#installments-table-body");

  summary.innerHTML = "";
  tableBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;
  installmentBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center text-muted py-4">Loading...</td>
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
        <td colspan="8" class="text-center text-muted py-4">Unable to load payment history.</td>
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

  renderInstallments(detail.installments || []);
  renderPaymentHistory(detail.payments || []);
}

function renderInstallments(installments) {
  const tableBody = document.querySelector("#installments-table-body");
  if (installments.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted py-4">No installments configured.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = installments.map((installment) => {
    const managerButtons = isFeeManager()
      ? `
          <button class="btn btn-sm btn-action-edit" type="button" data-action="edit-installment" data-id="${installment.id}" aria-label="Edit installment">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete-installment" data-id="${installment.id}" aria-label="Delete installment">
            <i class="bi bi-trash"></i>
          </button>
        `
      : "";
    return `
      <tr data-installment='${AdminApp.escapeHtml(JSON.stringify(installment))}'>
        <td>${installment.sequence_number}</td>
        <td>${AdminApp.escapeHtml(installment.title)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(installment.amount)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(installment.paid_amount)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(installment.balance)}</td>
        <td>${AdminApp.escapeHtml(installment.due_date)}</td>
        <td>${AdminApp.feeStatusBadge(installment.status)}</td>
        <td class="text-end"><span class="action-buttons">${managerButtons}</span></td>
      </tr>
    `;
  }).join("");
}

async function saveInstallment(event) {
  event.preventDefault();
  if (activeDetailsFeeId === null) {
    AdminApp.showAlert("#fee-details-alert", "Fee record not selected.", "danger");
    return;
  }
  const installmentId = document.querySelector("#installment-id").value;
  const payload = {
    title: document.querySelector("#installment-title").value.trim(),
    amount: document.querySelector("#installment-amount").value,
    due_date: document.querySelector("#installment-due-date").value,
    sequence_number: Number(document.querySelector("#installment-sequence").value),
  };
  const button = document.querySelector("#save-installment");
  AdminApp.setButtonLoading(button, true);
  try {
    await AdminApp.authFetch(
      installmentId ? `/fees/installments/${installmentId}` : `/fees/${activeDetailsFeeId}/installments`,
      {
        method: installmentId ? "PUT" : "POST",
        body: payload,
      },
    );
    document.querySelector("#installment-form").reset();
    document.querySelector("#installment-id").value = "";
    await showFeeDetails(activeDetailsFeeId);
    AdminApp.showToast("success", "Installment saved.");
  } catch (error) {
    AdminApp.showAlert("#fee-details-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(button, false);
  }
}

async function handleInstallmentAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const row = button.closest("tr");
  const installment = JSON.parse(row.dataset.installment || "{}");
  if (button.dataset.action === "edit-installment") {
    document.querySelector("#installment-id").value = installment.id;
    document.querySelector("#installment-title").value = installment.title;
    document.querySelector("#installment-amount").value = installment.amount;
    document.querySelector("#installment-due-date").value = installment.due_date;
    document.querySelector("#installment-sequence").value = installment.sequence_number;
    return;
  }

  const confirmed = await AdminApp.confirmAction({
    title: "Delete Installment",
    message: "Delete this installment? Installments with allocated payments cannot be deleted.",
    confirmLabel: "Delete",
    danger: true,
  });
  if (!confirmed) {
    return;
  }
  try {
    await AdminApp.authFetch(`/fees/installments/${button.dataset.id}`, { method: "DELETE" });
    await showFeeDetails(activeDetailsFeeId);
    AdminApp.showToast("success", "Installment deleted.");
  } catch (error) {
    AdminApp.showAlert("#fee-details-alert", error.message, "danger");
  }
}

function renderPaymentHistory(payments) {
  const tableBody = document.querySelector("#payment-history-body");

  if (payments.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted py-4">No payments recorded yet.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = payments.map((payment) => {
    const receiptButtons = payment.receipt_number
      ? `
          <button class="btn btn-sm btn-action-view" type="button" data-action="view-receipt" data-id="${payment.id}" aria-label="View receipt">
            <i class="bi bi-receipt"></i>
          </button>
          <button class="btn btn-sm btn-outline-secondary btn-icon" type="button" data-action="download-receipt" data-id="${payment.id}" aria-label="Download receipt">
            <i class="bi bi-filetype-pdf"></i>
          </button>
        `
      : "";
    const deleteButton = isFeeManager()
      ? `
          <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete-payment" data-id="${payment.id}" aria-label="Delete payment">
            <i class="bi bi-trash"></i>
          </button>
        `
      : "";
    return `
      <tr>
        <td>${AdminApp.escapeHtml(payment.receipt_number || "")}</td>
        <td>${AdminApp.escapeHtml(payment.payment_date)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(payment.amount)}</td>
        <td>${AdminApp.escapeHtml(formatPaymentMethod(payment.payment_method))}</td>
        <td>${AdminApp.escapeHtml(payment.reference_number || "")}</td>
        <td>${AdminApp.escapeHtml(`User #${payment.recorded_by}`)}</td>
        <td>${AdminApp.escapeHtml(payment.notes || "")}</td>
        <td class="text-end"><span class="action-buttons">${receiptButtons}${deleteButton}</span></td>
      </tr>
    `;
  }).join("");
}

async function handlePaymentAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  if (button.dataset.action === "view-receipt") {
    await viewReceipt(Number(button.dataset.id));
    return;
  }

  if (button.dataset.action === "download-receipt") {
    await downloadReceipt(Number(button.dataset.id));
    return;
  }

  if (button.dataset.action !== "delete-payment") {
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

async function viewReceipt(paymentId) {
  try {
    const receipt = await AdminApp.authFetch(`/payments/${paymentId}/receipt`);
    activeReceiptPaymentId = paymentId;
    document.querySelector("#receipt-content").innerHTML = `
      <dl class="row mb-0">
        <dt class="col-sm-4">Receipt Number</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.receipt_number || "")}</dd>
        <dt class="col-sm-4">Student</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.student_name)} (${AdminApp.escapeHtml(receipt.student_code)})</dd>
        <dt class="col-sm-4">Course</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.course_name || "")}</dd>
        <dt class="col-sm-4">Fee</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.fee_title)}</dd>
        <dt class="col-sm-4">Amount Paid</dt>
        <dd class="col-sm-8">${AdminApp.formatCurrency(receipt.amount_paid)}</dd>
        <dt class="col-sm-4">Payment Method</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(formatPaymentMethod(receipt.payment_method))}</dd>
        <dt class="col-sm-4">Reference</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.reference_number || "")}</dd>
        <dt class="col-sm-4">Payment Date</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.payment_date)}</dd>
        <dt class="col-sm-4">Balance</dt>
        <dd class="col-sm-8">${AdminApp.formatCurrency(receipt.balance)}</dd>
        <dt class="col-sm-4">Recorded By</dt>
        <dd class="col-sm-8">${AdminApp.escapeHtml(receipt.recorded_by_name || "")}</dd>
      </dl>
    `;
    receiptModal.show();
  } catch (error) {
    AdminApp.showAlert("#fee-details-alert", error.message, "danger");
  }
}

async function downloadReceipt(paymentId) {
  await AdminApp.downloadAuthenticatedFile(`/payments/${paymentId}/receipt/pdf`, `payment_${paymentId}_receipt.pdf`);
}

async function downloadActiveReceipt() {
  if (activeReceiptPaymentId !== null) {
    await downloadReceipt(activeReceiptPaymentId);
  }
}

function printReceipt() {
  const content = document.querySelector("#receipt-content").innerHTML;
  const printWindow = window.open("", "_blank");
  printWindow.document.write(`
    <html>
      <head>
        <title>Payment Receipt</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      </head>
      <body class="p-4">${content}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
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
