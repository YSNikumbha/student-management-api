document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  const tableBody = document.querySelector("#recent-students-body");

  try {
    const today = getTodayDateString();
    const [students, courses, todayAttendance] = await Promise.all([
      AdminApp.authFetch("/students"),
      AdminApp.authFetch("/courses"),
      AdminApp.authFetch(`/attendance?date=${today}`),
    ]);

    const activeStudents = students.filter((student) => student.status === "active").length;
    const activeCourses = courses.filter((course) => course.is_active === true).length;

    document.querySelector("#total-students").textContent = students.length;
    document.querySelector("#total-courses").textContent = courses.length;
    document.querySelector("#active-students").textContent = activeStudents;
    document.querySelector("#active-courses").textContent = activeCourses;

    renderRecentStudents(students, tableBody);
    renderTodayAttendance(todayAttendance, today);
  } catch (error) {
    AdminApp.showAlert("#dashboard-alert", error.message, "danger");
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted py-4">No students found.</td>
        </tr>
      `;
    }
  }
}

function getTodayDateString() {
  const now = new Date();
  const timezoneOffset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - timezoneOffset).toISOString().slice(0, 10);
}

function renderTodayAttendance(records, today) {
  const dateLabel = document.querySelector("#attendance-date-label");
  const emptyState = document.querySelector("#today-attendance-empty");
  const summary = document.querySelector("#today-attendance-summary");

  if (dateLabel) {
    dateLabel.textContent = `Attendance for ${today}`;
  }

  const marked = records.length;
  const present = records.filter((record) => record.status === "present").length;
  const absent = records.filter((record) => record.status === "absent").length;
  const late = records.filter((record) => record.status === "late").length;

  document.querySelector("#today-marked").textContent = marked;
  document.querySelector("#today-present").textContent = present;
  document.querySelector("#today-absent").textContent = absent;
  document.querySelector("#today-late").textContent = late;

  if (marked === 0) {
    emptyState?.classList.remove("d-none");
    summary?.classList.add("d-none");
    return;
  }

  emptyState?.classList.add("d-none");
  summary?.classList.remove("d-none");
}

function renderRecentStudents(students, tableBody) {
  if (!tableBody) {
    return;
  }

  const recentStudents = [...students]
    .sort((first, second) => second.id - first.id)
    .slice(0, 5);

  if (recentStudents.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">No students found.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = recentStudents.map((student) => {
    const fullName = `${student.first_name} ${student.last_name}`;
    const courseText = student.course_id === null || student.course_id === undefined
      ? "Not Assigned"
      : student.course_id;

    return `
      <tr>
        <td>${AdminApp.escapeHtml(student.student_code)}</td>
        <td>${AdminApp.escapeHtml(fullName)}</td>
        <td>${AdminApp.escapeHtml(student.email)}</td>
        <td>${AdminApp.escapeHtml(courseText)}</td>
        <td>${AdminApp.statusBadge(student.status)}</td>
      </tr>
    `;
  }).join("");
}
