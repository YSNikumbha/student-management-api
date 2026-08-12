let students = [];
let courses = [];
let studentModal;
let studentViewModal;
let studentAttendanceModal;
let studentFeesModal;
let currentUser;
let studentPageData = null;
let studentState = {
  page: 1,
  pageSize: 10,
  search: "",
  courseId: "",
  status: "",
  sortBy: "created_at",
  sortOrder: "desc",
};

document.addEventListener("DOMContentLoaded", () => {
  studentModal = new bootstrap.Modal(document.querySelector("#studentModal"));
  studentViewModal = new bootstrap.Modal(document.querySelector("#studentViewModal"));
  studentAttendanceModal = new bootstrap.Modal(document.querySelector("#studentAttendanceModal"));
  studentFeesModal = new bootstrap.Modal(document.querySelector("#studentFeesModal"));
  currentUser = AdminApp.getCurrentUser();

  const addButton = document.querySelector("#open-add-student");
  if (currentUser?.role !== "admin") {
    addButton.classList.add("d-none");
  }

  addButton.addEventListener("click", prepareAddStudent);
  document.querySelector("#student-form").addEventListener("submit", saveStudent);
  document.querySelector("#student-search").addEventListener("input", AdminApp.debounce(() => {
    studentState.search = document.querySelector("#student-search").value.trim();
    studentState.page = 1;
    loadStudents();
  }));
  document.querySelector("#student-course-filter").addEventListener("change", () => {
    studentState.courseId = document.querySelector("#student-course-filter").value;
    studentState.page = 1;
    loadStudents();
  });
  document.querySelector("#student-status-filter").addEventListener("change", () => {
    studentState.status = document.querySelector("#student-status-filter").value;
    studentState.page = 1;
    loadStudents();
  });
  document.querySelector("#student-sort").addEventListener("change", () => {
    const [sortBy, sortOrder] = document.querySelector("#student-sort").value.split(":");
    studentState.sortBy = sortBy;
    studentState.sortOrder = sortOrder;
    studentState.page = 1;
    loadStudents();
  });
  document.querySelector("#student-page-size").addEventListener("change", () => {
    studentState.pageSize = Number(document.querySelector("#student-page-size").value);
    studentState.page = 1;
    loadStudents();
  });
  document.querySelector("#students-table-body").addEventListener("click", handleStudentAction);

  loadStudentsPage();
});

async function loadStudentsPage() {
  try {
    await loadCoursesForStudents();
    await loadStudents();
  } catch (error) {
    AdminApp.showAlert("#students-alert", error.message, "danger");
  }
}

async function loadCoursesForStudents() {
  const response = await AdminApp.authFetch("/courses?page_size=100&sort_by=name&sort_order=asc");
  courses = AdminApp.getItems(response);
  renderCourseOptions();
  renderCourseFilter();
}

async function loadStudents() {
  const tableBody = document.querySelector("#students-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="7" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  const query = AdminApp.buildQueryString({
    search: studentState.search,
    course_id: studentState.courseId,
    status: studentState.status,
    page: studentState.page,
    page_size: studentState.pageSize,
    sort_by: studentState.sortBy,
    sort_order: studentState.sortOrder,
  });
  const response = await AdminApp.authFetch(`/students${query}`);
  students = AdminApp.getItems(response);
  studentPageData = response;
  renderStudents();
  renderStudentPagination();
}

function renderCourseOptions(selectedCourseId = null) {
  const select = document.querySelector("#student-course");
  const selectedValue = selectedCourseId === null || selectedCourseId === undefined
    ? ""
    : String(selectedCourseId);

  select.innerHTML = `
    <option value="">No Course</option>
    ${courses.map((course) => `
      <option value="${course.id}" ${String(course.id) === selectedValue ? "selected" : ""}>
        ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
      </option>
    `).join("")}
  `;
}

function renderCourseFilter() {
  const select = document.querySelector("#student-course-filter");
  select.innerHTML = `
    <option value="">All courses</option>
    ${courses.map((course) => `
      <option value="${course.id}">
        ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
      </option>
    `).join("")}
  `;
}

function renderStudents() {
  const tableBody = document.querySelector("#students-table-body");
  const courseById = new Map(courses.map((course) => [course.id, course]));

  if (students.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">No students match the selected filters.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = students.map((student) => {
    const fullName = `${student.first_name} ${student.last_name}`;
    const course = courseById.get(student.course_id);
    const courseName = course ? course.name : "Not Assigned";

    const adminActions = currentUser?.role === "admin"
      ? `
            <button class="btn btn-sm btn-action-edit" type="button" data-action="edit" data-id="${student.id}" aria-label="Edit student">
              <i class="bi bi-pencil"></i> Edit
            </button>
            <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${student.id}" aria-label="Delete student">
              <i class="bi bi-trash"></i>
            </button>
        `
      : "";

    return `
      <tr>
        <td>${AdminApp.escapeHtml(student.student_code)}</td>
        <td>${AdminApp.escapeHtml(fullName)}</td>
        <td>${AdminApp.escapeHtml(courseName)}</td>
        <td>${AdminApp.escapeHtml(student.email)}</td>
        <td>${AdminApp.escapeHtml(student.phone || "")}</td>
        <td>${AdminApp.statusBadge(student.status)}</td>
        <td class="text-end">
          <span class="action-buttons">
            <button class="btn btn-sm btn-action-view" type="button" data-action="view" data-id="${student.id}" aria-label="View student">
              <i class="bi bi-eye"></i> View
            </button>
            ${adminActions}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderStudentPagination() {
  AdminApp.renderPagination("#students-pagination", studentPageData, (page) => {
    studentState.page = page;
    loadStudents();
  });
}

function prepareAddStudent() {
  const form = document.querySelector("#student-form");
  form.reset();
  document.querySelector("#student-id").value = "";
  document.querySelector("#studentModalTitle").textContent = "Add Student";
  document.querySelector("#student-status-field").classList.add("d-none");
  renderCourseOptions();
  AdminApp.clearAlert("#student-form-alert");
}

function prepareEditStudent(studentId) {
  const student = students.find((item) => item.id === studentId);
  if (!student) {
    AdminApp.showAlert("#students-alert", "Student not found.", "danger");
    return;
  }

  document.querySelector("#student-form").reset();
  document.querySelector("#student-id").value = student.id;
  document.querySelector("#studentModalTitle").textContent = "Edit Student";
  document.querySelector("#student-code").value = student.student_code;
  document.querySelector("#student-email").value = student.email;
  document.querySelector("#student-first-name").value = student.first_name;
  document.querySelector("#student-last-name").value = student.last_name;
  document.querySelector("#student-phone").value = student.phone || "";
  document.querySelector("#student-date-of-birth").value = AdminApp.formatDate(student.date_of_birth);
  document.querySelector("#student-status").value = student.status;
  document.querySelector("#student-status-field").classList.remove("d-none");
  renderCourseOptions(student.course_id);
  AdminApp.clearAlert("#student-form-alert");
  studentModal.show();
}

async function saveStudent(event) {
  event.preventDefault();

  const form = document.querySelector("#student-form");
  const saveButton = document.querySelector("#save-student");
  const studentId = document.querySelector("#student-id").value;
  const courseValue = document.querySelector("#student-course").value;

  AdminApp.clearFormErrors(form);

  const firstNameInput = document.querySelector("#student-first-name");
  const lastNameInput = document.querySelector("#student-last-name");
  const codeInput = document.querySelector("#student-code");
  const emailInput = document.querySelector("#student-email");
  const phoneInput = document.querySelector("#student-phone");
  const dobInput = document.querySelector("#student-date-of-birth");

  const firstNameError = AdminApp.validateName(firstNameInput.value, "First name");
  const lastNameError = AdminApp.validateName(lastNameInput.value, "Last name");
  const codeError = AdminApp.validateStudentCode(codeInput.value);
  const emailError = AdminApp.validateEmail(emailInput.value);
  const phoneError = AdminApp.validatePhone(phoneInput.value);
  const dobError = AdminApp.validateDateNotFuture(dobInput.value, "Date of birth");

  let hasError = false;
  if (firstNameError) {
    AdminApp.showFieldError(firstNameInput, firstNameError);
    hasError = true;
  }
  if (lastNameError) {
    AdminApp.showFieldError(lastNameInput, lastNameError);
    hasError = true;
  }
  if (codeError) {
    AdminApp.showFieldError(codeInput, codeError);
    hasError = true;
  }
  if (emailError) {
    AdminApp.showFieldError(emailInput, emailError);
    hasError = true;
  }
  if (phoneError) {
    AdminApp.showFieldError(phoneInput, phoneError);
    hasError = true;
  }
  if (dobError) {
    AdminApp.showFieldError(dobInput, dobError);
    hasError = true;
  }

  if (hasError) {
    AdminApp.focusFirstInvalidField(form);
    return;
  }

  const payload = {
    student_code: codeInput.value.trim(),
    first_name: firstNameInput.value.trim(),
    last_name: lastNameInput.value.trim(),
    email: emailInput.value.trim(),
    phone: phoneInput.value.trim() || null,
    date_of_birth: dobInput.value || null,
    course_id: courseValue ? Number(courseValue) : null,
  };

  if (studentId) {
    payload.status = document.querySelector("#student-status").value;
  }

  AdminApp.clearAlert("#student-form-alert");
  AdminApp.setButtonLoading(saveButton, true);

  try {
    if (studentId) {
      await AdminApp.authFetch(`/students/${studentId}`, {
        method: "PUT",
        body: payload,
      });
      AdminApp.showToast("success", "Student updated successfully.");
    } else {
      await AdminApp.authFetch("/students", {
        method: "POST",
        body: payload,
      });
      studentState.page = 1;
      AdminApp.showToast("success", "Student created successfully.");
    }

    studentModal.hide();
    form.reset();
    await loadStudents();
  } catch (error) {
    AdminApp.showAlert("#student-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function handleStudentAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const studentId = Number(button.dataset.id);
  if (button.dataset.action === "view") {
    showStudentDetails(studentId);
    return;
  }

  if (button.dataset.action === "edit") {
    prepareEditStudent(studentId);
    return;
  }

  if (button.dataset.action === "attendance") {
    showStudentAttendance(studentId);
    return;
  }

  if (button.dataset.action === "fees") {
    showStudentFees(studentId);
    return;
  }

  if (button.dataset.action === "delete") {
    const confirmed = await AdminApp.confirmAction({
      title: "Delete Student",
      message: "Are you sure you want to delete this student? This action cannot be undone.",
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    button.disabled = true;
    try {
      await AdminApp.authFetch(`/students/${studentId}`, { method: "DELETE" });
      AdminApp.showToast("success", "Student deleted successfully.");
      await loadStudents();
    } catch (error) {
      AdminApp.showAlert("#students-alert", error.message, "danger");
    } finally {
      button.disabled = false;
    }
  }
}

async function showStudentDetails(studentId) {
  const student = students.find((item) => item.id === studentId);
  if (!student) {
    AdminApp.showAlert("#students-alert", "Student not found.", "danger");
    return;
  }

  const course = courses.find((c) => c.id === student.course_id);
  const fullName = `${student.first_name} ${student.last_name}`;
  const courseName = course ? `${course.name} (${course.code})` : "Not Assigned";

  document.querySelector("#studentViewModalTitle").textContent = `${fullName} - ${student.student_code}`;
  document.querySelector("#student-view-content").innerHTML = `
    <div class="student-view-section">
      <h6 class="student-view-section-title">Personal Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Full Name</span>
          <span class="student-view-value">${AdminApp.escapeHtml(fullName)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Date of Birth</span>
          <span class="student-view-value">${student.date_of_birth ? AdminApp.escapeHtml(student.date_of_birth) : "Not provided"}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Status</span>
          <span class="student-view-value">${AdminApp.statusBadge(student.status)}</span>
        </div>
      </div>
    </div>

    <div class="student-view-section">
      <h6 class="student-view-section-title">Academic Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Student Code</span>
          <span class="student-view-value">${AdminApp.escapeHtml(student.student_code)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Course</span>
          <span class="student-view-value">${AdminApp.escapeHtml(courseName)}</span>
        </div>
      </div>
    </div>

    <div class="student-view-section">
      <h6 class="student-view-section-title">Contact Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Email</span>
          <span class="student-view-value">${AdminApp.escapeHtml(student.email)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Phone</span>
          <span class="student-view-value">${student.phone ? AdminApp.escapeHtml(student.phone) : "Not provided"}</span>
        </div>
      </div>
    </div>

    <div class="student-view-section">
      <h6 class="student-view-section-title">Additional Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Created Date</span>
          <span class="student-view-value">${student.created_at ? AdminApp.escapeHtml(student.created_at.slice(0, 10)) : "N/A"}</span>
        </div>
      </div>
    </div>
  `;

  AdminApp.clearAlert("#student-view-alert");
  studentViewModal.show();
}

async function showStudentFees(studentId) {
  const student = students.find((item) => item.id === studentId);
  const title = document.querySelector("#studentFeesModalTitle");
  const tableBody = document.querySelector("#student-fees-history");

  title.textContent = student
    ? `Fees - ${student.first_name} ${student.last_name}`
    : "Student Fees";
  tableBody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;
  AdminApp.clearAlert("#student-fees-alert");
  studentFeesModal.show();

  try {
    const fees = await AdminApp.authFetch(`/fees/student/${studentId}`);

    if (fees.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">No fee records found.</td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = fees.map((fee) => `
      <tr>
        <td>
          <div class="fw-semibold">${AdminApp.escapeHtml(fee.title)}</div>
          <div class="small muted-cell">${AdminApp.escapeHtml(fee.description || "")}</div>
        </td>
        <td class="money-cell">${AdminApp.formatCurrency(fee.total_amount)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(fee.paid_amount)}</td>
        <td class="money-cell">${AdminApp.formatCurrency(fee.balance)}</td>
        <td>${AdminApp.escapeHtml(fee.due_date)}</td>
        <td>${AdminApp.feeStatusBadge(fee.status)}</td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#student-fees-alert", error.message, "danger");
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-4">Unable to load fees.</td>
      </tr>
    `;
  }
}

async function showStudentAttendance(studentId) {
  const student = students.find((item) => item.id === studentId);
  const title = document.querySelector("#studentAttendanceModalTitle");
  const summaryContainer = document.querySelector("#student-attendance-summary");
  const historyBody = document.querySelector("#student-attendance-history");

  title.textContent = student
    ? `Attendance - ${student.first_name} ${student.last_name}`
    : "Student Attendance";
  summaryContainer.innerHTML = "";
  historyBody.innerHTML = `
    <tr>
      <td colspan="3" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;
  AdminApp.clearAlert("#student-attendance-alert");
  studentAttendanceModal.show();

  try {
    const [summary, history] = await Promise.all([
      AdminApp.authFetch(`/attendance/student/${studentId}/summary`),
      AdminApp.authFetch(`/attendance/student/${studentId}`),
    ]);

    summaryContainer.innerHTML = `
      <div>
        <span class="mini-label">Marked</span>
        <strong>${AdminApp.escapeHtml(summary.total_marked_days)}</strong>
      </div>
      <div>
        <span class="mini-label">Present</span>
        <strong>${AdminApp.escapeHtml(summary.present_days)}</strong>
      </div>
      <div>
        <span class="mini-label">Absent</span>
        <strong>${AdminApp.escapeHtml(summary.absent_days)}</strong>
      </div>
      <div>
        <span class="mini-label">Late</span>
        <strong>${AdminApp.escapeHtml(summary.late_days)}</strong>
      </div>
      <div>
        <span class="mini-label">Attendance %</span>
        <strong>${AdminApp.escapeHtml(summary.attendance_percentage)}%</strong>
      </div>
    `;

    if (history.length === 0) {
      historyBody.innerHTML = `
        <tr>
          <td colspan="3" class="text-center text-muted py-4">No attendance records found.</td>
        </tr>
      `;
      return;
    }

    historyBody.innerHTML = history.map((record) => `
      <tr>
        <td>${AdminApp.escapeHtml(record.date)}</td>
        <td>${AdminApp.attendanceBadge(record.status)}</td>
        <td>${AdminApp.escapeHtml(record.remarks || "")}</td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#student-attendance-alert", error.message, "danger");
    historyBody.innerHTML = `
      <tr>
        <td colspan="3" class="text-center text-muted py-4">Unable to load attendance.</td>
      </tr>
    `;
  }
}
