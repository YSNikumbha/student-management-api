document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  const tableBody = document.querySelector("#recent-students-body");

  try {
    const [students, courses] = await Promise.all([
      AdminApp.apiRequest("/students"),
      AdminApp.apiRequest("/courses"),
    ]);

    const activeStudents = students.filter((student) => student.status === "active").length;
    const activeCourses = courses.filter((course) => course.is_active === true).length;

    document.querySelector("#total-students").textContent = students.length;
    document.querySelector("#total-courses").textContent = courses.length;
    document.querySelector("#active-students").textContent = activeStudents;
    document.querySelector("#active-courses").textContent = activeCourses;

    renderRecentStudents(students, tableBody);
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
