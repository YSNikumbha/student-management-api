let students = [];
let courses = [];
let studentModal;

document.addEventListener("DOMContentLoaded", () => {
  studentModal = new bootstrap.Modal(document.querySelector("#studentModal"));

  document.querySelector("#open-add-student").addEventListener("click", prepareAddStudent);
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
  courses = await AdminApp.apiRequest("/courses");
  renderCourseOptions();
}

async function loadStudents() {
  const tableBody = document.querySelector("#students-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  students = await AdminApp.apiRequest("/students");
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
            <button class="btn btn-sm btn-outline-primary btn-icon" type="button" data-action="edit" data-id="${student.id}" aria-label="Edit student">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${student.id}" aria-label="Delete student">
              <i class="bi bi-trash"></i>
            </button>
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
      await AdminApp.apiRequest(`/students/${studentId}`, {
        method: "PUT",
        body: payload,
      });
      AdminApp.showAlert("#students-alert", "Student updated successfully.", "success");
    } else {
      await AdminApp.apiRequest("/students", {
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

  if (!window.confirm("Are you sure you want to delete this student?")) {
    return;
  }

  button.disabled = true;
  try {
    await AdminApp.apiRequest(`/students/${studentId}`, { method: "DELETE" });
    AdminApp.showAlert("#students-alert", "Student deleted successfully.", "success");
    await loadStudents();
  } catch (error) {
    AdminApp.showAlert("#students-alert", error.message, "danger");
  } finally {
    button.disabled = false;
  }
}
