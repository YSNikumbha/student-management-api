let attendanceCourses = [];
let attendanceRows = [];
let attendanceHistoryPageData = null;
let attendanceHistoryState = {
  page: 1,
  pageSize: 10,
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#attendance-date").value = getTodayDateString();
  document.querySelector("#load-attendance").addEventListener("click", loadAttendance);
  document.querySelector("#mark-all-present").addEventListener("click", markAllPresent);
  document.querySelector("#clear-attendance").addEventListener("click", clearAttendance);
  document.querySelector("#save-attendance").addEventListener("click", saveAttendance);
  document.querySelector("#load-attendance-history").addEventListener("click", () => {
    attendanceHistoryState.page = 1;
    loadAttendanceHistory();
  });
  document.querySelector("#history-course").addEventListener("change", resetAndLoadAttendanceHistory);
  document.querySelector("#history-status").addEventListener("change", resetAndLoadAttendanceHistory);
  document.querySelector("#history-start-date").addEventListener("change", resetAndLoadAttendanceHistory);
  document.querySelector("#history-end-date").addEventListener("change", resetAndLoadAttendanceHistory);
  document.querySelector("#history-page-size").addEventListener("change", () => {
    attendanceHistoryState.pageSize = Number(document.querySelector("#history-page-size").value);
    resetAndLoadAttendanceHistory();
  });

  loadCourses();
  loadAttendanceHistory();
});

async function loadCourses() {
  const courseSelect = document.querySelector("#attendance-course");

  try {
    const response = await AdminApp.authFetch("/courses?page_size=100&sort_by=name&sort_order=asc");
    attendanceCourses = AdminApp.getItems(response);
    if (attendanceCourses.length === 0) {
      courseSelect.innerHTML = '<option value="">No courses found</option>';
      renderHistoryCourseOptions();
      return;
    }

    courseSelect.innerHTML = `
      <option value="">Select course</option>
      ${attendanceCourses.map((course) => `
        <option value="${course.id}">
          ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
        </option>
      `).join("")}
    `;
    renderHistoryCourseOptions();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message, "danger");
    courseSelect.innerHTML = '<option value="">Unable to load courses</option>';
    renderHistoryCourseOptions();
  }
}

function renderHistoryCourseOptions() {
  const historyCourseSelect = document.querySelector("#history-course");
  historyCourseSelect.innerHTML = `
    <option value="">All courses</option>
    ${attendanceCourses.map((course) => `
      <option value="${course.id}">
        ${AdminApp.escapeHtml(course.name)} (${AdminApp.escapeHtml(course.code)})
      </option>
    `).join("")}
  `;
}

async function loadAttendance() {
  const courseId = document.querySelector("#attendance-course").value;
  const attendanceDate = document.querySelector("#attendance-date").value;
  const loadButton = document.querySelector("#load-attendance");

  AdminApp.clearAlert("#attendance-alert");

  if (!courseId) {
    AdminApp.showAlert("#attendance-alert", "Please select a course.", "warning");
    return;
  }

  if (!attendanceDate) {
    AdminApp.showAlert("#attendance-alert", "Please select an attendance date.", "warning");
    return;
  }

  setAttendanceTableLoading();
  setAttendanceActions(false);
  AdminApp.setButtonLoading(loadButton, true, "Loading...");

  try {
    const response = await AdminApp.authFetch(
      `/attendance/course/${courseId}/date/${attendanceDate}`,
    );
    attendanceRows = response.students;
    renderAttendanceTable(attendanceRows);
    updateAttendanceContext(courseId, attendanceDate);
    setAttendanceActions(attendanceRows.length > 0);
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message, "danger");
    renderAttendanceEmpty("Unable to load attendance.");
  } finally {
    AdminApp.setButtonLoading(loadButton, false);
  }
}

function renderAttendanceTable(rows) {
  const tableBody = document.querySelector("#attendance-table-body");

  if (rows.length === 0) {
    renderAttendanceEmpty("No students are assigned to this course.");
    return;
  }

  tableBody.innerHTML = rows.map((row) => `
    <tr data-student-id="${row.student_id}">
      <td>${AdminApp.escapeHtml(row.student_code)}</td>
      <td>${AdminApp.escapeHtml(row.name)}</td>
      <td>
        <select class="form-select attendance-status" aria-label="Attendance status for ${AdminApp.escapeHtml(row.name)}">
          <option value="">Select status</option>
          <option value="present" ${row.status === "present" ? "selected" : ""}>Present</option>
          <option value="absent" ${row.status === "absent" ? "selected" : ""}>Absent</option>
          <option value="late" ${row.status === "late" ? "selected" : ""}>Late</option>
        </select>
      </td>
      <td>
        <input class="form-control attendance-remarks" type="text" maxlength="500" value="${AdminApp.escapeHtml(row.remarks || "")}" placeholder="Optional remarks">
      </td>
      <td>
        ${row.attendance_id ? '<span class="status-badge status-active">Saved</span>' : '<span class="status-badge status-pending">New</span>'}
      </td>
    </tr>
  `).join("");
}

function renderAttendanceEmpty(message) {
  document.querySelector("#attendance-table-body").innerHTML = `
    <tr>
      <td colspan="5" class="text-center text-muted py-4">${AdminApp.escapeHtml(message)}</td>
    </tr>
  `;
}

function setAttendanceTableLoading() {
  document.querySelector("#attendance-table-body").innerHTML = `
    <tr>
      <td colspan="5" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;
}

function updateAttendanceContext(courseId, attendanceDate) {
  const course = attendanceCourses.find((item) => item.id === Number(courseId));
  const courseName = course ? `${course.name} (${course.code})` : "Selected course";
  document.querySelector("#attendance-context").textContent = `${courseName} on ${attendanceDate}`;
}

function setAttendanceActions(enabled) {
  document.querySelector("#mark-all-present").disabled = !enabled;
  document.querySelector("#clear-attendance").disabled = !enabled;
  document.querySelector("#save-attendance").disabled = !enabled;
}

function markAllPresent() {
  document.querySelectorAll(".attendance-status").forEach((select) => {
    select.value = "present";
  });
}

function clearAttendance() {
  document.querySelectorAll(".attendance-status").forEach((select) => {
    select.value = "";
  });
  document.querySelectorAll(".attendance-remarks").forEach((input) => {
    input.value = "";
  });
}

function resetAndLoadAttendanceHistory() {
  attendanceHistoryState.page = 1;
  loadAttendanceHistory();
}

async function loadAttendanceHistory() {
  const tableBody = document.querySelector("#attendance-history-body");
  const loadButton = document.querySelector("#load-attendance-history");
  tableBody.innerHTML = `
    <tr>
      <td colspan="5" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  AdminApp.setButtonLoading(loadButton, true, "Loading...");

  try {
    const query = AdminApp.buildQueryString({
      start_date: document.querySelector("#history-start-date").value,
      end_date: document.querySelector("#history-end-date").value,
      course_id: document.querySelector("#history-course").value,
      status: document.querySelector("#history-status").value,
      page: attendanceHistoryState.page,
      page_size: attendanceHistoryState.pageSize,
    });
    const response = await AdminApp.authFetch(`/attendance${query}`);
    const records = AdminApp.getItems(response);
    attendanceHistoryPageData = response;
    renderAttendanceHistory(records);
    renderAttendanceHistoryPagination();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message, "danger");
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">Unable to load attendance history.</td>
      </tr>
    `;
  } finally {
    AdminApp.setButtonLoading(loadButton, false);
  }
}

function renderAttendanceHistory(records) {
  const tableBody = document.querySelector("#attendance-history-body");

  if (records.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">No attendance records found for this period.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = records.map((record) => `
    <tr>
      <td>${AdminApp.escapeHtml(record.date)}</td>
      <td>${AdminApp.escapeHtml(record.student_id)}</td>
      <td>${AdminApp.attendanceBadge(record.status)}</td>
      <td>${AdminApp.escapeHtml(record.remarks || "")}</td>
      <td>${AdminApp.escapeHtml(AdminApp.formatDate(record.updated_at))}</td>
    </tr>
  `).join("");
}

function renderAttendanceHistoryPagination() {
  AdminApp.renderPagination("#attendance-history-pagination", attendanceHistoryPageData, (page) => {
    attendanceHistoryState.page = page;
    loadAttendanceHistory();
  });
}

function buildBulkPayload() {
  const attendanceDate = document.querySelector("#attendance-date").value;
  const records = [];
  const missingStudents = [];

  document.querySelectorAll("#attendance-table-body tr[data-student-id]").forEach((row) => {
    const studentId = Number(row.dataset.studentId);
    const status = row.querySelector(".attendance-status").value;
    const remarks = row.querySelector(".attendance-remarks").value.trim() || null;

    if (!status) {
      missingStudents.push(row.children[1].textContent.trim());
      return;
    }

    records.push({
      student_id: studentId,
      status,
      remarks,
    });
  });

  if (missingStudents.length > 0) {
    throw new Error("Please mark attendance status for every student.");
  }

  if (records.length === 0) {
    throw new Error("No students are available to save.");
  }

  return {
    date: attendanceDate,
    records,
  };
}

async function saveAttendance() {
  const saveButton = document.querySelector("#save-attendance");

  AdminApp.clearAlert("#attendance-alert");

  let payload;
  try {
    payload = buildBulkPayload();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message, "warning");
    return;
  }

  AdminApp.setButtonLoading(saveButton, true);

  try {
    const response = await AdminApp.authFetch("/attendance/bulk", {
      method: "POST",
      body: payload,
    });

    AdminApp.showAlert(
      "#attendance-alert",
      `Attendance saved. Created: ${response.created}, Updated: ${response.updated}.`,
      "success",
    );
    await loadAttendance();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

function getTodayDateString() {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - timezoneOffset).toISOString().slice(0, 10);
}
