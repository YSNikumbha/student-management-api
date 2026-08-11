document.addEventListener("DOMContentLoaded", () => {
  initAcademicsPage();
});

async function initAcademicsPage() {
  loadAcademicYears();
  loadSemesters();
  loadSubjects();
  loadBatches();

  document.getElementById("create-year-btn")?.addEventListener("click", () => openYearModal());
  document.getElementById("create-semester-btn")?.addEventListener("click", () => openSemesterModal());
  document.getElementById("create-subject-btn")?.addEventListener("click", () => openSubjectModal());
  document.getElementById("create-batch-btn")?.addEventListener("click", () => openBatchModal());
}

// ============================================
// ACADEMIC YEARS
// ============================================

async function loadAcademicYears() {
  const loadingEl = document.getElementById("years-loading");
  const tbody = document.querySelector("#years-table-body");

  try {
    loadingEl?.classList.remove("d-none");
    const data = await AdminApp.authFetch("/academic-years?page_size=100");
    const years = AdminApp.getItems(data);

    if (!years.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No academic years found.</td></tr>';
      return;
    }

    tbody.innerHTML = years.map((year) => `
      <tr>
        <td>${AdminApp.escapeHtml(year.name)}</td>
        <td>${AdminApp.formatDate(year.start_date)}</td>
        <td>${AdminApp.formatDate(year.end_date)}</td>
        <td>${AdminApp.statusBadge(year.is_active)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="editYear(${year.id})">
            <i class="bi bi-pencil"></i> Edit
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteYear(${year.id})">
            <i class="bi bi-trash"></i> Delete
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to load academic years", "danger");
  } finally {
    loadingEl?.classList.add("d-none");
  }
}

function openYearModal(yearId = null) {
  const isEdit = yearId !== null;
  const modal = document.createElement("div");
  modal.className = "modal fade";
  modal.id = "year-modal";
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${isEdit ? "Edit" : "Add"} Academic Year</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="year-form">
            <div class="mb-3">
              <label for="year-name" class="form-label">Name</label>
              <input type="text" class="form-control" id="year-name" required>
            </div>
            <div class="mb-3">
              <label for="year-start" class="form-label">Start Date</label>
              <input type="date" class="form-control" id="year-start" required>
            </div>
            <div class="mb-3">
              <label for="year-end" class="form-label">End Date</label>
              <input type="date" class="form-control" id="year-end" required>
            </div>
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="year-active" checked>
              <label class="form-check-label" for="year-active">Active</label>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="button" class="btn btn-primary" id="save-year-btn">Save</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  if (isEdit) {
    const year = document.querySelector(`button[onclick="editYear(${yearId})"]`)?.closest("tr")?.dataset;
    if (year) {
      document.getElementById("year-name").value = year.name || "";
      document.getElementById("year-start").value = year.start_date || "";
      document.getElementById("year-end").value = year.end_date || "";
      document.getElementById("year-active").checked = year.is_active !== "false";
    }
  }

  document.getElementById("save-year-btn").addEventListener("click", async () => {
    const name = document.getElementById("year-name").value.trim();
    const start_date = document.getElementById("year-start").value;
    const end_date = document.getElementById("year-end").value;
    const is_active = document.getElementById("year-active").checked;

    if (!name || !start_date || !end_date) {
      AdminApp.showAlert("#academics-alert", "Please fill all required fields", "warning");
      return;
    }

    const payload = { name, start_date, end_date, is_active };
    const url = isEdit ? `/academic-years/${yearId}` : "/academic-years";
    const method = isEdit ? "PUT" : "POST";

    try {
      await AdminApp.authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      bsModal.hide();
      loadAcademicYears();
      AdminApp.showToast("success", `Academic year ${isEdit ? "updated" : "created"} successfully`);
    } catch (error) {
      AdminApp.showAlert("#academics-alert", error.message || "Failed to save academic year", "danger");
    }
  });

  modal.addEventListener("hidden.bs.modal", () => modal.remove());
}

async function editYear(yearId) {
  openYearModal(yearId);
}

async function deleteYear(yearId) {
  const confirmed = await AdminApp.confirmAction({
    title: "Delete Academic Year",
    message: "Are you sure you want to delete this academic year? This action cannot be undone.",
    confirmLabel: "Delete",
    danger: true,
  });

  if (!confirmed) return;

  try {
    await AdminApp.authFetch(`/academic-years/${yearId}`, { method: "DELETE" });
    loadAcademicYears();
    AdminApp.showToast("success", "Academic year deleted successfully");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to delete academic year", "danger");
  }
}

// ============================================
// SEMESTERS
// ============================================

async function loadSemesters() {
  const loadingEl = document.getElementById("semesters-loading");
  const tbody = document.querySelector("#semesters-table-body");

  try {
    loadingEl?.classList.remove("d-none");
    const data = await AdminApp.authFetch("/semesters?page_size=100");
    const semesters = AdminApp.getItems(data);

    if (!semesters.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No semesters found.</td></tr>';
      return;
    }

    tbody.innerHTML = semesters.map((semester) => `
      <tr>
        <td>${AdminApp.escapeHtml(semester.academic_year_name || "")}</td>
        <td>${AdminApp.escapeHtml(semester.course_name || "")}</td>
        <td>${semester.number}</td>
        <td>${AdminApp.escapeHtml(semester.name)}</td>
        <td>${AdminApp.formatDate(semester.start_date)} - ${AdminApp.formatDate(semester.end_date)}</td>
        <td>${AdminApp.statusBadge(semester.is_active)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="editSemester(${semester.id})">
            <i class="bi bi-pencil"></i> Edit
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSemester(${semester.id})">
            <i class="bi bi-trash"></i> Delete
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to load semesters", "danger");
  } finally {
    loadingEl?.classList.add("d-none");
  }
}

function openSemesterModal(semesterId = null) {
  const isEdit = semesterId !== null;
  const modal = document.createElement("div");
  modal.className = "modal fade";
  modal.id = "semester-modal";
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${isEdit ? "Edit" : "Add"} Semester</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="semester-form">
            <div class="mb-3">
              <label for="semester-year" class="form-label">Academic Year</label>
              <select class="form-select" id="semester-year" required></select>
            </div>
            <div class="mb-3">
              <label for="semester-course" class="form-label">Course</label>
              <select class="form-select" id="semester-course" required></select>
            </div>
            <div class="mb-3">
              <label for="semester-number" class="form-label">Semester Number</label>
              <input type="number" class="form-control" id="semester-number" min="1" required>
            </div>
            <div class="mb-3">
              <label for="semester-name" class="form-label">Name</label>
              <input type="text" class="form-control" id="semester-name" required>
            </div>
            <div class="mb-3">
              <label for="semester-start" class="form-label">Start Date</label>
              <input type="date" class="form-control" id="semester-start">
            </div>
            <div class="mb-3">
              <label for="semester-end" class="form-label">End Date</label>
              <input type="date" class="form-control" id="semester-end">
            </div>
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="semester-active" checked>
              <label class="form-check-label" for="semester-active">Active</label>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="button" class="btn btn-primary" id="save-semester-btn">Save</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  loadAcademicYearOptions();
  loadCourseOptions();

  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  document.getElementById("save-semester-btn").addEventListener("click", async () => {
    const academic_year_id = parseInt(document.getElementById("semester-year").value);
    const course_id = parseInt(document.getElementById("semester-course").value);
    const number = parseInt(document.getElementById("semester-number").value);
    const name = document.getElementById("semester-name").value.trim();
    const start_date = document.getElementById("semester-start").value || null;
    const end_date = document.getElementById("semester-end").value || null;
    const is_active = document.getElementById("semester-active").checked;

    if (!academic_year_id || !course_id || !number || !name) {
      AdminApp.showAlert("#academics-alert", "Please fill all required fields", "warning");
      return;
    }

    const payload = { academic_year_id, course_id, number, name, start_date, end_date, is_active };
    const url = isEdit ? `/semesters/${semesterId}` : "/semesters";
    const method = isEdit ? "PUT" : "POST";

    try {
      await AdminApp.authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      bsModal.hide();
      loadSemesters();
      AdminApp.showToast("success", `Semester ${isEdit ? "updated" : "created"} successfully`);
    } catch (error) {
      AdminApp.showAlert("#academics-alert", error.message || "Failed to save semester", "danger");
    }
  });

  modal.addEventListener("hidden.bs.modal", () => modal.remove());
}

async function editSemester(semesterId) {
  openSemesterModal(semesterId);
}

async function deleteSemester(semesterId) {
  const confirmed = await AdminApp.confirmAction({
    title: "Delete Semester",
    message: "Are you sure you want to delete this semester? This action cannot be undone.",
    confirmLabel: "Delete",
    danger: true,
  });

  if (!confirmed) return;

  try {
    await AdminApp.authFetch(`/semesters/${semesterId}`, { method: "DELETE" });
    loadSemesters();
    AdminApp.showToast("success", "Semester deleted successfully");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to delete semester", "danger");
  }
}

// ============================================
// SUBJECTS
// ============================================

async function loadSubjects() {
  const loadingEl = document.getElementById("subjects-loading");
  const tbody = document.querySelector("#subjects-table-body");

  try {
    loadingEl?.classList.remove("d-none");
    const data = await AdminApp.authFetch("/subjects?page_size=100");
    const subjects = AdminApp.getItems(data);

    if (!subjects.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No subjects found.</td></tr>';
      return;
    }

    tbody.innerHTML = subjects.map((subject) => `
      <tr>
        <td>${AdminApp.escapeHtml(subject.code)}</td>
        <td>${AdminApp.escapeHtml(subject.name)}</td>
        <td>${AdminApp.escapeHtml(subject.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(subject.semester_name || "")}</td>
        <td>${subject.credits || "-"}</td>
        <td>${AdminApp.statusBadge(subject.is_active)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="editSubject(${subject.id})">
            <i class="bi bi-pencil"></i> Edit
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSubject(${subject.id})">
            <i class="bi bi-trash"></i> Delete
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to load subjects", "danger");
  } finally {
    loadingEl?.classList.add("d-none");
  }
}

function openSubjectModal(subjectId = null) {
  const isEdit = subjectId !== null;
  const modal = document.createElement("div");
  modal.className = "modal fade";
  modal.id = "subject-modal";
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${isEdit ? "Edit" : "Add"} Subject</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="subject-form">
            <div class="mb-3">
              <label for="subject-course" class="form-label">Course</label>
              <select class="form-select" id="subject-course" required></select>
            </div>
            <div class="mb-3">
              <label for="subject-semester" class="form-label">Semester</label>
              <select class="form-select" id="subject-semester" required></select>
            </div>
            <div class="mb-3">
              <label for="subject-code" class="form-label">Code</label>
              <input type="text" class="form-control" id="subject-code" required>
            </div>
            <div class="mb-3">
              <label for="subject-name" class="form-label">Name</label>
              <input type="text" class="form-control" id="subject-name" required>
            </div>
            <div class="mb-3">
              <label for="subject-description" class="form-label">Description</label>
              <textarea class="form-control" id="subject-description" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label for="subject-credits" class="form-label">Credits</label>
              <input type="number" class="form-control" id="subject-credits" min="1">
            </div>
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="subject-active" checked>
              <label class="form-check-label" for="subject-active">Active</label>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="button" class="btn btn-primary" id="save-subject-btn">Save</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  loadCourseOptions("subject-course");
  loadSemesterOptions();

  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  document.getElementById("save-subject-btn").addEventListener("click", async () => {
    const course_id = parseInt(document.getElementById("subject-course").value);
    const semester_id = parseInt(document.getElementById("subject-semester").value);
    const code = document.getElementById("subject-code").value.trim();
    const name = document.getElementById("subject-name").value.trim();
    const description = document.getElementById("subject-description").value.trim() || null;
    const credits = document.getElementById("subject-credits").value ? parseInt(document.getElementById("subject-credits").value) : null;
    const is_active = document.getElementById("subject-active").checked;

    if (!course_id || !semester_id || !code || !name) {
      AdminApp.showAlert("#academics-alert", "Please fill all required fields", "warning");
      return;
    }

    const payload = { course_id, semester_id, code, name, description, credits, is_active };
    const url = isEdit ? `/subjects/${subjectId}` : "/subjects";
    const method = isEdit ? "PUT" : "POST";

    try {
      await AdminApp.authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      bsModal.hide();
      loadSubjects();
      AdminApp.showToast("success", `Subject ${isEdit ? "updated" : "created"} successfully`);
    } catch (error) {
      AdminApp.showAlert("#academics-alert", error.message || "Failed to save subject", "danger");
    }
  });

  modal.addEventListener("hidden.bs.modal", () => modal.remove());
}

async function editSubject(subjectId) {
  openSubjectModal(subjectId);
}

async function deleteSubject(subjectId) {
  const confirmed = await AdminApp.confirmAction({
    title: "Delete Subject",
    message: "Are you sure you want to delete this subject? This action cannot be undone.",
    confirmLabel: "Delete",
    danger: true,
  });

  if (!confirmed) return;

  try {
    await AdminApp.authFetch(`/subjects/${subjectId}`, { method: "DELETE" });
    loadSubjects();
    AdminApp.showToast("success", "Subject deleted successfully");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to delete subject", "danger");
  }
}

// ============================================
// BATCHES
// ============================================

async function loadBatches() {
  const loadingEl = document.getElementById("batches-loading");
  const tbody = document.querySelector("#batches-table-body");

  try {
    loadingEl?.classList.remove("d-none");
    const data = await AdminApp.authFetch("/batches?page_size=100");
    const batches = AdminApp.getItems(data);

    if (!batches.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No batches found.</td></tr>';
      return;
    }

    tbody.innerHTML = batches.map((batch) => `
      <tr>
        <td>${AdminApp.escapeHtml(batch.name)}</td>
        <td>${AdminApp.escapeHtml(batch.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(batch.academic_year_name || "")}</td>
        <td>${AdminApp.escapeHtml(batch.semester_name || "")}</td>
        <td>${AdminApp.escapeHtml(batch.section || "-")}</td>
        <td>${batch.capacity || "-"}</td>
        <td>${AdminApp.statusBadge(batch.is_active)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="editBatch(${batch.id})">
            <i class="bi bi-pencil"></i> Edit
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteBatch(${batch.id})">
            <i class="bi bi-trash"></i> Delete
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to load batches", "danger");
  } finally {
    loadingEl?.classList.add("d-none");
  }
}

function openBatchModal(batchId = null) {
  const isEdit = batchId !== null;
  const modal = document.createElement("div");
  modal.className = "modal fade";
  modal.id = "batch-modal";
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${isEdit ? "Edit" : "Add"} Batch</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="batch-form">
            <div class="mb-3">
              <label for="batch-name" class="form-label">Name</label>
              <input type="text" class="form-control" id="batch-name" required>
            </div>
            <div class="mb-3">
              <label for="batch-course" class="form-label">Course</label>
              <select class="form-select" id="batch-course" required></select>
            </div>
            <div class="mb-3">
              <label for="batch-year" class="form-label">Academic Year</label>
              <select class="form-select" id="batch-year" required></select>
            </div>
            <div class="mb-3">
              <label for="batch-semester" class="form-label">Semester</label>
              <select class="form-select" id="batch-semester">
                <option value="">None</option>
              </select>
            </div>
            <div class="mb-3">
              <label for="batch-section" class="form-label">Section</label>
              <input type="text" class="form-control" id="batch-section" maxlength="10">
            </div>
            <div class="mb-3">
              <label for="batch-capacity" class="form-label">Capacity</label>
              <input type="number" class="form-control" id="batch-capacity" min="1">
            </div>
            <div class="mb-3 form-check">
              <input type="checkbox" class="form-check-input" id="batch-active" checked>
              <label class="form-check-label" for="batch-active">Active</label>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="button" class="btn btn-primary" id="save-batch-btn">Save</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  loadCourseOptions("batch-course");
  loadAcademicYearOptions("batch-year");
  loadSemesterOptions("batch-semester");

  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  document.getElementById("save-batch-btn").addEventListener("click", async () => {
    const name = document.getElementById("batch-name").value.trim();
    const course_id = parseInt(document.getElementById("batch-course").value);
    const academic_year_id = parseInt(document.getElementById("batch-year").value);
    const semester_id = document.getElementById("batch-semester").value ? parseInt(document.getElementById("batch-semester").value) : null;
    const section = document.getElementById("batch-section").value.trim() || null;
    const capacity = document.getElementById("batch-capacity").value ? parseInt(document.getElementById("batch-capacity").value) : null;
    const is_active = document.getElementById("batch-active").checked;

    if (!name || !course_id || !academic_year_id) {
      AdminApp.showAlert("#academics-alert", "Please fill all required fields", "warning");
      return;
    }

    const payload = { name, course_id, academic_year_id, semester_id, section, capacity, is_active };
    const url = isEdit ? `/batches/${batchId}` : "/batches";
    const method = isEdit ? "PUT" : "POST";

    try {
      await AdminApp.authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      bsModal.hide();
      loadBatches();
      AdminApp.showToast("success", `Batch ${isEdit ? "updated" : "created"} successfully`);
    } catch (error) {
      AdminApp.showAlert("#academics-alert", error.message || "Failed to save batch", "danger");
    }
  });

  modal.addEventListener("hidden.bs.modal", () => modal.remove());
}

async function editBatch(batchId) {
  openBatchModal(batchId);
}

async function deleteBatch(batchId) {
  const confirmed = await AdminApp.confirmAction({
    title: "Delete Batch",
    message: "Are you sure you want to delete this batch? This action cannot be undone.",
    confirmLabel: "Delete",
    danger: true,
  });

  if (!confirmed) return;

  try {
    await AdminApp.authFetch(`/batches/${batchId}`, { method: "DELETE" });
    loadBatches();
    AdminApp.showToast("success", "Batch deleted successfully");
  } catch (error) {
    AdminApp.showAlert("#academics-alert", error.message || "Failed to delete batch", "danger");
  }
}

// ============================================
// HELPER FUNCTIONS
// ============================================

async function loadAcademicYearOptions(selectId = "semester-year") {
  const select = document.getElementById(selectId);
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/academic-years?page_size=100");
    const years = AdminApp.getItems(data);
    select.innerHTML = years.map((year) => `<option value="${year.id}">${AdminApp.escapeHtml(year.name)}</option>`).join("");
  } catch (error) {
    console.error("Failed to load academic years", error);
  }
}

async function loadCourseOptions(selectId = "semester-course") {
  const select = document.getElementById(selectId);
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/courses?page_size=100");
    const courses = AdminApp.getItems(data);
    select.innerHTML = courses.map((course) => `<option value="${course.id}">${AdminApp.escapeHtml(course.code)} - ${AdminApp.escapeHtml(course.name)}</option>`).join("");
  } catch (error) {
    console.error("Failed to load courses", error);
  }
}

async function loadSemesterOptions(selectId = "subject-semester") {
  const select = document.getElementById(selectId);
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/semesters?page_size=100");
    const semesters = AdminApp.getItems(data);
    select.innerHTML = '<option value="">Select semester</option>' +
      semesters.map((sem) => `<option value="${sem.id}">${AdminApp.escapeHtml(sem.name)} (${AdminApp.escapeHtml(sem.academic_year_name || "")})</option>`).join("");
  } catch (error) {
    console.error("Failed to load semesters", error);
  }
}