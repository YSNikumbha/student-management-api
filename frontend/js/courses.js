let courses = [];
let courseModal;
let courseViewModal;
let currentUser;
let coursePageData = null;
let courseState = {
  page: 1,
  pageSize: 10,
  search: "",
  isActive: "",
  sortBy: "created_at",
  sortOrder: "desc",
};

document.addEventListener("DOMContentLoaded", () => {
  courseModal = new bootstrap.Modal(document.querySelector("#courseModal"));
  courseViewModal = new bootstrap.Modal(document.querySelector("#courseViewModal"));
  currentUser = AdminApp.getCurrentUser();

  const addButton = document.querySelector("#open-add-course");
  if (currentUser?.role !== "admin") {
    addButton.classList.add("d-none");
  }

  addButton.addEventListener("click", prepareAddCourse);
  document.querySelector("#course-form").addEventListener("submit", saveCourse);
  document.querySelector("#course-search").addEventListener("input", AdminApp.debounce(() => {
    courseState.search = document.querySelector("#course-search").value.trim();
    courseState.page = 1;
    loadCourses();
  }));
  document.querySelector("#course-active-filter").addEventListener("change", () => {
    courseState.isActive = document.querySelector("#course-active-filter").value;
    courseState.page = 1;
    loadCourses();
  });
  document.querySelector("#course-sort").addEventListener("change", () => {
    const [sortBy, sortOrder] = document.querySelector("#course-sort").value.split(":");
    courseState.sortBy = sortBy;
    courseState.sortOrder = sortOrder;
    courseState.page = 1;
    loadCourses();
  });
  document.querySelector("#course-page-size").addEventListener("change", () => {
    courseState.pageSize = Number(document.querySelector("#course-page-size").value);
    courseState.page = 1;
    loadCourses();
  });
  document.querySelector("#courses-table-body").addEventListener("click", handleCourseAction);

  loadCourses();
});

async function loadCourses() {
  const tableBody = document.querySelector("#courses-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="5" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  try {
    const query = AdminApp.buildQueryString({
      search: courseState.search,
      is_active: courseState.isActive,
      page: courseState.page,
      page_size: courseState.pageSize,
      sort_by: courseState.sortBy,
      sort_order: courseState.sortOrder,
    });
    const response = await AdminApp.authFetch(`/courses${query}`);
    courses = AdminApp.getItems(response);
    coursePageData = response;
    renderCourses();
    renderCoursePagination();
  } catch (error) {
    AdminApp.showAlert("#courses-alert", error.message, "danger");
  }
}

function renderCourses() {
  const tableBody = document.querySelector("#courses-table-body");

  if (courses.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">No courses found.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = courses.map((course) => {
    const durationText = course.duration_months
      ? `${course.duration_months} months`
      : "Not Set";

    const actionButtons = currentUser?.role === "admin"
      ? `
          <span class="action-buttons">
            <button class="btn btn-sm btn-action-view" type="button" data-action="view" data-id="${course.id}" aria-label="View course">
              <i class="bi bi-eye"></i> View
            </button>
            <button class="btn btn-sm btn-action-edit" type="button" data-action="edit" data-id="${course.id}" aria-label="Edit course">
              <i class="bi bi-pencil"></i> Edit
            </button>
            <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${course.id}" aria-label="Delete course">
              <i class="bi bi-trash"></i>
            </button>
          </span>
        `
      : `
          <span class="action-buttons">
            <button class="btn btn-sm btn-action-view" type="button" data-action="view" data-id="${course.id}" aria-label="View course">
              <i class="bi bi-eye"></i> View
            </button>
          </span>
        `;

    return `
      <tr>
        <td>${AdminApp.escapeHtml(course.code)}</td>
        <td>
          <div class="fw-semibold">${AdminApp.escapeHtml(course.name)}</div>
          <div class="small muted-cell">${AdminApp.escapeHtml(course.description || "")}</div>
        </td>
        <td>${AdminApp.escapeHtml(durationText)}</td>
        <td>${AdminApp.statusBadge(course.is_active, true)}</td>
        <td class="text-end">
          ${actionButtons}
        </td>
      </tr>
    `;
  }).join("");
}

function renderCoursePagination() {
  AdminApp.renderPagination("#courses-pagination", coursePageData, (page) => {
    courseState.page = page;
    loadCourses();
  });
}

function prepareAddCourse() {
  document.querySelector("#course-form").reset();
  document.querySelector("#course-id").value = "";
  document.querySelector("#courseModalTitle").textContent = "Add Course";
  document.querySelector("#course-active-field").classList.add("d-none");
  AdminApp.clearAlert("#course-form-alert");
}

function prepareEditCourse(courseId) {
  const course = courses.find((item) => item.id === courseId);
  if (!course) {
    AdminApp.showAlert("#courses-alert", "Course not found.", "danger");
    return;
  }

  document.querySelector("#course-form").reset();
  document.querySelector("#course-id").value = course.id;
  document.querySelector("#courseModalTitle").textContent = "Edit Course";
  document.querySelector("#course-code").value = course.code;
  document.querySelector("#course-name").value = course.name;
  document.querySelector("#course-description").value = course.description || "";
  document.querySelector("#course-duration").value = course.duration_months || "";
  document.querySelector("#course-active").value = String(course.is_active);
  document.querySelector("#course-active-field").classList.remove("d-none");
  AdminApp.clearAlert("#course-form-alert");
  courseModal.show();
}

async function saveCourse(event) {
  event.preventDefault();

  const form = document.querySelector("#course-form");
  const saveButton = document.querySelector("#save-course");
  const courseId = document.querySelector("#course-id").value;

  AdminApp.clearFormErrors(form);

  const codeInput = document.querySelector("#course-code");
  const nameInput = document.querySelector("#course-name");
  const descriptionInput = document.querySelector("#course-description");
  const durationInput = document.querySelector("#course-duration");

  const codeError = AdminApp.validateStudentCode(codeInput.value);
  const nameError = AdminApp.validateName(nameInput.value, "Course name");
  const descriptionError = descriptionInput.value.trim() ? null : null;
  const durationError = durationInput.value ? null : null;

  let hasError = false;

  if (codeError) {
    AdminApp.showFieldError(codeInput, codeError);
    hasError = true;
  }

  if (nameError) {
    AdminApp.showFieldError(nameInput, nameError);
    hasError = true;
  }

  if (descriptionInput.value.trim() && descriptionInput.value.trim().length > 500) {
    AdminApp.showFieldError(descriptionInput, "Description must be 500 characters or less.");
    hasError = true;
  }

  if (durationInput.value) {
    const durationNum = Number(durationInput.value);
    if (!Number.isInteger(durationNum) || durationNum <= 0) {
      AdminApp.showFieldError(durationInput, "Duration must be a positive integer.");
      hasError = true;
    } else if (durationNum > 120) {
      AdminApp.showFieldError(durationInput, "Duration cannot exceed 120 months.");
      hasError = true;
    }
  }

  if (hasError) {
    AdminApp.focusFirstInvalidField(form);
    return;
  }

  const payload = {
    code: codeInput.value.trim(),
    name: nameInput.value.trim(),
    description: descriptionInput.value.trim() || null,
    duration_months: durationInput.value ? Number(durationInput.value) : null,
  };

  if (courseId) {
    payload.is_active = document.querySelector("#course-active").value === "true";
  }

  AdminApp.clearAlert("#course-form-alert");
  AdminApp.setButtonLoading(saveButton, true);

  try {
    if (courseId) {
      await AdminApp.authFetch(`/courses/${courseId}`, {
        method: "PUT",
        body: payload,
      });
      AdminApp.showToast("success", "Course updated successfully.");
    } else {
      await AdminApp.authFetch("/courses", {
        method: "POST",
        body: payload,
      });
      courseState.page = 1;
      AdminApp.showToast("success", "Course created successfully.");
    }

    courseModal.hide();
    form.reset();
    await loadCourses();
  } catch (error) {
    AdminApp.showAlert("#course-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function handleCourseAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const courseId = Number(button.dataset.id);
  if (button.dataset.action === "view") {
    showCourseDetails(courseId);
    return;
  }

  if (button.dataset.action === "edit") {
    prepareEditCourse(courseId);
    return;
  }

  if (button.dataset.action === "delete") {
    const confirmed = await AdminApp.confirmAction({
      title: "Delete Course",
      message: "Are you sure you want to delete this course? This action cannot be undone.",
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    button.disabled = true;
    try {
      await AdminApp.authFetch(`/courses/${courseId}`, { method: "DELETE" });
      AdminApp.showToast("success", "Course deleted successfully.");
      await loadCourses();
    } catch (error) {
      const message = error.status === 409 && error.message.includes("students")
        ? "Cannot delete this course because students are currently assigned to it."
        : error.message;
      AdminApp.showAlert("#courses-alert", message, "danger");
    } finally {
      button.disabled = false;
    }
  }
}

async function showCourseDetails(courseId) {
  const course = courses.find((item) => item.id === courseId);
  if (!course) {
    AdminApp.showAlert("#courses-alert", "Course not found.", "danger");
    return;
  }

  const durationText = course.duration_months
    ? `${course.duration_months} months`
    : "Not Set";

  document.querySelector("#courseViewModalTitle").textContent = `${course.code} - ${course.name}`;
  document.querySelector("#course-view-content").innerHTML = `
    <div class="student-view-section">
      <h6 class="student-view-section-title">Course Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Course Code</span>
          <span class="student-view-value">${AdminApp.escapeHtml(course.code)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Course Name</span>
          <span class="student-view-value">${AdminApp.escapeHtml(course.name)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Duration</span>
          <span class="student-view-value">${AdminApp.escapeHtml(durationText)}</span>
        </div>
        <div class="student-view-item">
          <span class="student-view-label">Status</span>
          <span class="student-view-value">${AdminApp.statusBadge(course.is_active, true)}</span>
        </div>
      </div>
    </div>

    <div class="student-view-section">
      <h6 class="student-view-section-title">Description</h6>
      <div class="student-view-item full-width">
        <span class="student-view-label">Description</span>
        <span class="student-view-value">${course.description ? AdminApp.escapeHtml(course.description) : "No description provided"}</span>
      </div>
    </div>

    <div class="student-view-section">
      <h6 class="student-view-section-title">Additional Information</h6>
      <div class="student-view-grid">
        <div class="student-view-item">
          <span class="student-view-label">Created Date</span>
          <span class="student-view-value">${course.created_at ? AdminApp.escapeHtml(course.created_at.slice(0, 10)) : "N/A"}</span>
        </div>
      </div>
    </div>
  `;

  AdminApp.clearAlert("#course-view-alert");
  courseViewModal.show();
}
