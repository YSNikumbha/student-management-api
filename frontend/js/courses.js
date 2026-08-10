let courses = [];
let courseModal;
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
      <td colspan="6" class="text-center text-muted py-4">Loading...</td>
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
        <td colspan="6" class="text-center text-muted py-4">No courses found.</td>
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
          <span class="table-actions">
            <button class="btn btn-sm btn-outline-primary btn-icon" type="button" data-action="edit" data-id="${course.id}" aria-label="Edit course">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger btn-icon" type="button" data-action="delete" data-id="${course.id}" aria-label="Delete course">
              <i class="bi bi-trash"></i>
            </button>
          </span>
        `
      : '<span class="muted-cell">View only</span>';

    return `
      <tr>
        <td>${AdminApp.escapeHtml(course.id)}</td>
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

  const saveButton = document.querySelector("#save-course");
  const courseId = document.querySelector("#course-id").value;
  const durationValue = document.querySelector("#course-duration").value;
  const payload = {
    code: document.querySelector("#course-code").value.trim(),
    name: document.querySelector("#course-name").value.trim(),
    description: document.querySelector("#course-description").value.trim() || null,
    duration_months: durationValue ? Number(durationValue) : null,
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
      AdminApp.showAlert("#courses-alert", "Course updated successfully.", "success");
    } else {
      await AdminApp.authFetch("/courses", {
        method: "POST",
        body: payload,
      });
      courseState.page = 1;
      AdminApp.showAlert("#courses-alert", "Course created successfully.", "success");
    }

    courseModal.hide();
    document.querySelector("#course-form").reset();
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
  if (button.dataset.action === "edit") {
    prepareEditCourse(courseId);
    return;
  }

  if (!window.confirm("Are you sure you want to delete this course?")) {
    return;
  }

  button.disabled = true;
  try {
    await AdminApp.authFetch(`/courses/${courseId}`, { method: "DELETE" });
    AdminApp.showAlert("#courses-alert", "Course deleted successfully.", "success");
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
