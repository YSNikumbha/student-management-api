let students = [];
let courses = [];
let studentModal;
let studentAttendanceModal;
let studentFeesModal;
let currentUser;

document.addEventListener("DOMContentLoaded", () => {
  studentModal = new bootstrap.Modal(document.querySelector("#studentModal"));
  studentAttendanceModal = new bootstrap.Modal(document.querySelector("#studentAttendanceModal"));
  studentFeesModal = new bootstrap.Modal(document.querySelector("#studentFeesModal"));
  currentUser = AdminApp.getCurrentUser();

  const addButton = document.querySelector("#open-add-student");
  if (currentUser?.role !== "admin") {
    addButton.classList.add("d-none");
  }

  addButton.addEventListener("click", prepareAddStudent);
  document.querySelector("#student-form").addEventListener("submit", saveStudent);
  document.querySelector("#student-search").addEventListener("input", renderStudents);
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
  courses = await AdminApp.authFetch("/courses");
  renderCourseOptions();
}

async function loadStudents() {
  const tableBody = document.querySelector("#students-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  students = await AdminApp.authFetch("/students");
  renderStudents();
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

function renderStudents() {
  const tableBody = document.querySelector("#students-table-body");
  const searchTerm = document.querySelector("#student-search").value.trim().toLowerCase();
  const courseById = new Map(courses.map((course) => [course.id, course]));

  const filteredStudents = students.filter((student) => {
    const searchable = [
      student.student_code,
      student.first_name,
      student.last_name,
      student.email,
    ].join(" ").toLowerCase();

    return searchable.includes(searchTerm);
  });

  if (filteredStudents.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted py-4">No students found.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = filteredStudents.map((student) => {
    const fullName = `${student.first_name} ${student.last_name}`;
    const course = courseById.get(student.course_id);
    const courseName = course ? course.name : "Not Assigned";

    const deleteButton = currentUser?.role === "admin"
      ? `
            <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${student.id}" aria-label="Delete student">
              <i class="bi bi-trash"></i>
            </button>
        `
      : "";

    return `
      <tr>
        <td>${AdminApp.escapeHtml(student.id)}</td>
        <td>${AdminApp.escapeHtml(student.student_code)}</td>
        <td>${AdminApp.escapeHtml(fullName)}</td>
        <td>${AdminApp.escapeHtml(student.email)}</td>
        <td>${AdminApp.escapeHtml(student.phone || "")}</td>
        <td>${AdminApp.escapeHtml(courseName)}</td>
        <td>${AdminApp.statusBadge(student.status)}</td>
        <td class="text-end">
          <span class="table-actions">
            <button class="btn btn-sm btn-outline-secondary btn-icon" type="button" data-action="attendance" data-id="${student.id}" aria-label="View attendance">
              <i class="bi bi-calendar-check"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary btn-icon" type="button" data-action="fees" data-id="${student.id}" aria-label="View fees">
              <i class="bi bi-cash-coin"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary btn-icon" type="button" data-action="edit" data-id="${student.id}" aria-label="Edit student">
              <i class="bi bi-pencil"></i>
            </button>
            ${deleteButton}
          </span>
        </td>
      </tr>
    `;
  }).join("");
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

  const saveButton = document.querySelector("#save-student");
  const studentId = document.querySelector("#student-id").value;
  const courseValue = document.querySelector("#student-course").value;
  const payload = {
    student_code: document.querySelector("#student-code").value.trim(),
    first_name: document.querySelector("#student-first-name").value.trim(),
    last_name: document.querySelector("#student-last-name").value.trim(),
    email: document.querySelector("#student-email").value.trim(),
    phone: document.querySelector("#student-phone").value.trim() || null,
    date_of_birth: document.querySelector("#student-date-of-birth").value || null,
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
      AdminApp.showAlert("#students-alert", "Student updated successfully.", "success");
    } else {
      await AdminApp.authFetch("/students", {
        method: "POST",
        body: payload,
      });
      AdminApp.showAlert("#students-alert", "Student created successfully.", "success");
    }

    studentModal.hide();
    document.querySelector("#student-form").reset();
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

  if (!window.confirm("Are you sure you want to delete this student?")) {
    return;
  }

  button.disabled = true;
  try {
    await AdminApp.authFetch(`/students/${studentId}`, { method: "DELETE" });
    AdminApp.showAlert("#students-alert", "Student deleted successfully.", "success");
    await loadStudents();
  } catch (error) {
    AdminApp.showAlert("#students-alert", error.message, "danger");
  } finally {
    button.disabled = false;
  }
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
