document.addEventListener("DOMContentLoaded", () => {
  initAttendancePage();
});

let currentSessionId = null;

async function initAttendancePage() {
  await Promise.all([
    loadStudentsForSummary(),
    loadSessionFormOptions(),
  ]);
  loadSessions();
  loadHistory();

  document.getElementById("session-form")?.addEventListener("submit", handleCreateSession);
  document.getElementById("session-year")?.addEventListener("change", handleAcademicFilterChange);
  document.getElementById("session-course")?.addEventListener("change", handleAcademicFilterChange);
  document.getElementById("session-semester")?.addEventListener("change", handleSemesterChange);
  document.getElementById("create-session-btn")?.addEventListener("click", () => {
    document.getElementById("mark-tab").click();
  });
  document.getElementById("mark-all-present")?.addEventListener("click", markAllPresent);
  document.getElementById("clear-all")?.addEventListener("click", clearAllAttendance);
  document.getElementById("save-attendance")?.addEventListener("click", saveAttendance);
  document.getElementById("summary-student")?.addEventListener("change", loadStudentSummary);
}

// ============================================
// CREATE SESSION
// ============================================

async function handleCreateSession(e) {
  e.preventDefault();

  const date = document.getElementById("session-date").value;
  const course_id = parseInt(document.getElementById("session-course").value);
  const batch_id = parseInt(document.getElementById("session-batch").value);
  const semester_id = parseInt(document.getElementById("session-semester").value);
  const subject_id = parseInt(document.getElementById("session-subject").value);
  const session_name = document.getElementById("session-name").value.trim() || null;
  const startValue = document.getElementById("session-start").value;
  const endValue = document.getElementById("session-end").value;
  const start_time = startValue ? `${date}T${startValue}:00` : null;
  const end_time = endValue ? `${date}T${endValue}:00` : null;

  if (!date || !course_id || !batch_id || !semester_id || !subject_id) {
    AdminApp.showAlert("#attendance-alert", "Please fill all required fields", "warning");
    return;
  }

  const payload = {
    date,
    course_id,
    batch_id,
    semester_id,
    subject_id,
    session_name,
    start_time,
    end_time,
  };

  try {
    const session = await AdminApp.authFetch("/attendance/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
    });

    currentSessionId = session.id;
    document.getElementById("mark-attendance-section").classList.remove("d-none");
    await loadSessionStudents(currentSessionId);
    AdminApp.showToast("success", "Session created successfully");
    document.getElementById("session-form").reset();
    await loadSessionFormOptions();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to create session", "danger");
  }
}

async function loadSessionFormOptions() {
  setDateDefault();
  await Promise.all([loadAcademicYears(), loadCourses()]);
  await handleAcademicFilterChange();
}

async function loadAcademicYears() {
  const select = document.getElementById("session-year");
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/academic-years?page_size=100");
    const years = AdminApp.getItems(data);
    setSelectOptions(
      select,
      years,
      "Select academic year",
      (year) => year.name,
    );
  } catch (error) {
    setSelectError(select, error.message || "Failed to load academic years");
  }
}

async function loadCourses() {
  const select = document.getElementById("session-course");
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/courses?page_size=100");
    const courses = AdminApp.getItems(data);
    setSelectOptions(
      select,
      courses,
      "Select course",
      (course) => `${course.code} - ${course.name}`,
    );
  } catch (error) {
    setSelectError(select, error.message || "Failed to load courses");
  }
}

async function handleAcademicFilterChange() {
  await Promise.all([loadSemesters(), loadBatches()]);
  await loadSubjects();
}

async function handleSemesterChange() {
  await Promise.all([loadBatches(), loadSubjects()]);
}

async function loadSemesters() {
  const select = document.getElementById("session-semester");
  if (!select) return;

  const yearId = document.getElementById("session-year")?.value;
  const courseId = document.getElementById("session-course")?.value;
  if (!yearId || !courseId) {
    setSelectOptions(select, [], "Select semester");
    return;
  }

  try {
    const query = AdminApp.buildQueryString({
      academic_year_id: yearId,
      course_id: courseId,
      page_size: 100,
    });
    const data = await AdminApp.authFetch(`/semesters${query}`);
    setSelectOptions(
      select,
      AdminApp.getItems(data),
      "Select semester",
      (semester) => semester.name,
    );
  } catch (error) {
    setSelectError(select, error.message || "Failed to load semesters");
  }
}

async function loadBatches() {
  const select = document.getElementById("session-batch");
  if (!select) return;

  const yearId = document.getElementById("session-year")?.value;
  const courseId = document.getElementById("session-course")?.value;
  const semesterId = document.getElementById("session-semester")?.value;
  if (!yearId || !courseId) {
    setSelectOptions(select, [], "Select batch");
    return;
  }

  try {
    const query = AdminApp.buildQueryString({
      academic_year_id: yearId,
      course_id: courseId,
      semester_id: semesterId || undefined,
      page_size: 100,
    });
    const data = await AdminApp.authFetch(`/batches${query}`);
    setSelectOptions(
      select,
      AdminApp.getItems(data),
      "Select batch",
      (batch) => batch.name,
    );
  } catch (error) {
    setSelectError(select, error.message || "Failed to load batches");
  }
}

async function loadSubjects() {
  const select = document.getElementById("session-subject");
  if (!select) return;

  const courseId = document.getElementById("session-course")?.value;
  const semesterId = document.getElementById("session-semester")?.value;
  if (!courseId || !semesterId) {
    setSelectOptions(select, [], "Select subject");
    return;
  }

  try {
    const query = AdminApp.buildQueryString({
      course_id: courseId,
      semester_id: semesterId,
      page_size: 100,
    });
    const data = await AdminApp.authFetch(`/subjects${query}`);
    setSelectOptions(
      select,
      AdminApp.getItems(data),
      "Select subject",
      (subject) => `${subject.code} - ${subject.name}`,
    );
  } catch (error) {
    setSelectError(select, error.message || "Failed to load subjects");
  }
}

function setDateDefault() {
  const input = document.getElementById("session-date");
  if (input && !input.value) {
    input.value = new Date().toISOString().slice(0, 10);
  }
}

function setSelectOptions(select, items, placeholder, labelFactory = (item) => item.name) {
  select.innerHTML = `<option value="">${AdminApp.escapeHtml(placeholder)}</option>` +
    items.map((item) => (
      `<option value="${item.id}">${AdminApp.escapeHtml(labelFactory(item))}</option>`
    )).join("");
}

function setSelectError(select, message) {
  select.innerHTML = `<option value="">${AdminApp.escapeHtml(message)}</option>`;
}

// ============================================
// MARK ATTENDANCE
// ============================================

async function loadSessionStudents(sessionId) {
  const tbody = document.querySelector("#attendance-table-body");
  tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Loading...</td></tr>';

  try {
    const data = await AdminApp.authFetch(`/attendance/sessions/${sessionId}/students`);
    const students = data.students;

    if (!students.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No students in this batch</td></tr>';
      return;
    }

    tbody.innerHTML = students.map((student, index) => `
      <tr data-student-id="${student.student_id}">
        <td>${AdminApp.escapeHtml(student.student_code)}</td>
        <td>${AdminApp.escapeHtml(student.student_name)}</td>
        <td>
          <input type="radio" name="status-${index}" value="present" ${student.status === 'present' ? 'checked' : ''}>
        </td>
        <td>
          <input type="radio" name="status-${index}" value="absent" ${student.status === 'absent' ? 'checked' : ''}>
        </td>
        <td>
          <input type="radio" name="status-${index}" value="late" ${student.status === 'late' ? 'checked' : ''}>
        </td>
        <td>
          <input type="radio" name="status-${index}" value="excused" ${student.status === 'excused' ? 'checked' : ''}>
        </td>
        <td>
          <input type="text" class="form-control form-control-sm remarks-input" value="${AdminApp.escapeHtml(student.remarks || '')}" placeholder="Optional remarks">
        </td>
      </tr>
    `).join("");
  } catch (error) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Failed to load students</td></tr>';
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to load students", "danger");
  }
}

function markAllPresent() {
  document.querySelectorAll("#attendance-table-body tr").forEach((row) => {
    const radio = row.querySelector('input[value="present"]');
    if (radio) radio.checked = true;
  });
}

function clearAllAttendance() {
  document.querySelectorAll("#attendance-table-body tr input[type='radio']").forEach((radio) => {
    radio.checked = false;
  });
  document.querySelectorAll("#attendance-table-body tr .remarks-input").forEach((input) => {
    input.value = "";
  });
}

async function saveAttendance() {
  if (!currentSessionId) {
    AdminApp.showAlert("#attendance-alert", "No session selected", "warning");
    return;
  }

  const records = [];
  document.querySelectorAll("#attendance-table-body tr").forEach((row) => {
    const studentId = row.dataset.studentId;
    const status = row.querySelector('input[type="radio"]:checked')?.value;
    const remarks = row.querySelector(".remarks-input")?.value.trim() || null;

    if (status) {
      records.push({ student_id: parseInt(studentId), status, remarks });
    }
  });

  if (!records.length) {
    AdminApp.showAlert("#attendance-alert", "No attendance records to save", "warning");
    return;
  }

  try {
    await AdminApp.authFetch(`/attendance/sessions/${currentSessionId}/records/bulk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: { records },
    });

    AdminApp.showToast("success", "Attendance saved successfully");
    loadSessions();
    loadHistory();
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to save attendance", "danger");
  }
}

// ============================================
// SESSIONS
// ============================================

async function loadSessions() {
  const loadingEl = document.getElementById("sessions-loading");
  const tbody = document.querySelector("#sessions-table-body");

  try {
    loadingEl?.classList.remove("d-none");
    const data = await AdminApp.authFetch("/attendance/sessions?page_size=100");
    const sessions = data.items || [];

    if (!sessions.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No sessions found.</td></tr>';
      return;
    }

    tbody.innerHTML = sessions.map((session) => `
      <tr>
        <td>${AdminApp.formatDate(session.date)}</td>
        <td>${AdminApp.escapeHtml(session.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(session.batch_name || "")}</td>
        <td>${AdminApp.escapeHtml(session.subject_code || "")}</td>
        <td>${AdminApp.escapeHtml(session.session_name || "-")}</td>
        <td>${session.student_count}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="viewSession(${session.id})">
            <i class="bi bi-eye"></i> View
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSession(${session.id})">
            <i class="bi bi-trash"></i> Delete
          </button>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to load sessions", "danger");
  } finally {
    loadingEl?.classList.add("d-none");
  }
}

async function viewSession(sessionId) {
  currentSessionId = sessionId;
  document.getElementById("mark-tab").click();
  document.getElementById("mark-attendance-section").classList.remove("d-none");
  await loadSessionStudents(sessionId);
}

async function deleteSession(sessionId) {
  const confirmed = await AdminApp.confirmAction({
    title: "Delete Session",
    message: "Are you sure you want to delete this session? All attendance records will be deleted.",
    confirmLabel: "Delete",
    danger: true,
  });

  if (!confirmed) return;

  try {
    await AdminApp.authFetch(`/attendance/sessions/${sessionId}`, { method: "DELETE" });
    loadSessions();
    AdminApp.showToast("success", "Session deleted successfully");
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to delete session", "danger");
  }
}

// ============================================
// HISTORY
// ============================================

async function loadHistory() {
  const tbody = document.querySelector("#history-table-body");
  tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Loading...</td></tr>';

  try {
    const data = await AdminApp.authFetch("/attendance/sessions?page_size=100");
    const sessions = data.items || [];

    const historyRows = [];
    for (const session of sessions) {
      const studentsData = await AdminApp.authFetch(`/attendance/sessions/${session.id}/students`);

      for (const student of studentsData.students) {
        if (student.status) {
          historyRows.push({
            date: session.date,
            student_name: student.student_name,
            course_name: session.course_name,
            subject_code: session.subject_code,
            status: student.status,
            remarks: student.remarks,
          });
        }
      }
    }

    if (!historyRows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No attendance records found.</td></tr>';
      return;
    }

    tbody.innerHTML = historyRows.map((record) => `
      <tr>
        <td>${AdminApp.formatDate(record.date)}</td>
        <td>${AdminApp.escapeHtml(record.student_name)}</td>
        <td>${AdminApp.escapeHtml(record.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(record.subject_code || "")}</td>
        <td>${AdminApp.attendanceBadge(record.status)}</td>
        <td>${AdminApp.escapeHtml(record.remarks || "-")}</td>
      </tr>
    `).join("");
  } catch (error) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load history</td></tr>';
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to load history", "danger");
  }
}

// ============================================
// STUDENT SUMMARY
// ============================================

async function loadStudentsForSummary() {
  const select = document.getElementById("summary-student");
  if (!select) return;

  try {
    const data = await AdminApp.authFetch("/students?page_size=100");
    const students = data.items || [];

    select.innerHTML = '<option value="">Select student</option>' +
      students.map((s) => `<option value="${s.id}">${AdminApp.escapeHtml(s.student_code)} - ${AdminApp.escapeHtml(s.first_name)} ${AdminApp.escapeHtml(s.last_name)}</option>`).join("");
  } catch (error) {
    console.error("Failed to load students", error);
  }
}

async function loadStudentSummary() {
  const studentId = document.getElementById("summary-student").value;
  const summaryContent = document.getElementById("summary-content");

  if (!studentId) {
    summaryContent.classList.add("d-none");
    return;
  }

  try {
    const [summaryResponse, subjectResponse] = await Promise.all([
      AdminApp.authFetch(`/attendance/student/${studentId}/summary`),
      AdminApp.authFetch(`/attendance/sessions/student/${studentId}/subject-summary`),
    ]);

    const summary = summaryResponse;
    const subjectData = subjectResponse;

    document.getElementById("summary-total").textContent = summary.total_sessions ?? summary.total_marked_days ?? 0;
    document.getElementById("summary-present").textContent = summary.present ?? summary.present_days ?? 0;
    document.getElementById("summary-absent").textContent = summary.absent ?? summary.absent_days ?? 0;
    document.getElementById("summary-percentage").textContent = `${summary.attendance_percentage || 0}%`;

    const percentage = summary.attendance_percentage || 0;
    const percentageElement = document.getElementById("summary-percentage");
    if (percentage < 75) {
      percentageElement.classList.add("text-danger");
      percentageElement.classList.remove("text-success");
    } else {
      percentageElement.classList.add("text-success");
      percentageElement.classList.remove("text-danger");
    }

    const subjectTbody = document.querySelector("#subject-summary-body");
    const subjects = subjectData.subjects || [];

    if (!subjects.length) {
      subjectTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No subject-wise data available</td></tr>';
    } else {
      subjectTbody.innerHTML = subjects.map((subject) => {
        const percentageClass = subject.attendance_percentage < 75 ? "text-danger fw-bold" : "";
        return `
          <tr>
            <td>${AdminApp.escapeHtml(subject.subject_code)} - ${AdminApp.escapeHtml(subject.subject_name)}</td>
            <td>${subject.total_sessions}</td>
            <td>${subject.present}</td>
            <td class="${percentageClass}">${subject.attendance_percentage}%</td>
          </tr>
        `;
      }).join("");
    }

    summaryContent.classList.remove("d-none");
  } catch (error) {
    AdminApp.showAlert("#attendance-alert", error.message || "Failed to load summary", "danger");
  }
}
