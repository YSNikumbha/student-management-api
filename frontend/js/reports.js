const ReportsApp = (() => {
  const REPORT_ENDPOINTS = {
    students: "/reports/students",
    attendance: "/reports/attendance",
    fees: "/reports/fees",
    courses: "/reports/courses",
  };

  const EXPORT_ENDPOINTS = {
    students: "/reports/students/export",
    attendance: "/reports/attendance/export",
    fees: "/reports/fees/export",
    courses: "/reports/courses/export",
  };

  const STATUS_OPTIONS = {
    students: [
      { value: "", label: "All" },
      { value: "active", label: "Active" },
      { value: "inactive", label: "Inactive" },
    ],
    attendance: [],
    fees: [
      { value: "", label: "All" },
      { value: "unpaid", label: "Unpaid" },
      { value: "partial", label: "Partial" },
      { value: "paid", label: "Paid" },
      { value: "overdue", label: "Overdue" },
    ],
    courses: [],
  };

  const FILTER_VISIBILITY = {
    students: ["search", "course", "status", "created-from", "created-to"],
    attendance: ["course", "student", "start-date", "end-date", "detail"],
    fees: ["student", "course", "status", "due-from", "due-to"],
    courses: ["search", "active"],
  };

  let currentReportType = "students";
  let currentFilters = {};
  let currentPage = 1;
  let currentPageSize = 100;

  function init() {
    document.querySelectorAll(".report-type-btn").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".report-type-btn").forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
        handleReportTypeChange(button.dataset.reportType);
      });
    });

    document.getElementById("generate-report")?.addEventListener("click", generateReport);
    document.getElementById("export-csv")?.addEventListener("click", () => exportReport("csv"));
    document.getElementById("export-pdf")?.addEventListener("click", () => exportReport("pdf"));

    handleReportTypeChange("students");
    loadCourses();
    loadStudents();
  }

  async function loadCourses() {
    try {
      const response = await AdminApp.authFetch("/courses");
      const courses = AdminApp.getItems(response);
      const courseSelect = document.getElementById("report-course");
      if (!courseSelect) {
        return;
      }

      courseSelect.innerHTML = '<option value="">All courses</option>' +
        courses.map((course) => `<option value="${course.id}">${AdminApp.escapeHtml(course.code)} - ${AdminApp.escapeHtml(course.name)}</option>`).join("");
    } catch (error) {
      console.error("Failed to load courses", error);
    }
  }

  async function loadStudents() {
    try {
      const response = await AdminApp.authFetch("/students?page_size=100&sort_by=first_name&sort_order=asc");
      const students = AdminApp.getItems(response);
      const studentSelect = document.getElementById("report-student");
      if (!studentSelect) {
        return;
      }

      studentSelect.innerHTML = '<option value="">All students</option>' +
        students.map((student) => `<option value="${student.id}">${AdminApp.escapeHtml(student.first_name)} ${AdminApp.escapeHtml(student.last_name)} (${AdminApp.escapeHtml(student.student_code)})</option>`).join("");
    } catch (error) {
      console.error("Failed to load students", error);
    }
  }

  function handleReportTypeChange(reportType) {
    if (!reportType) {
      const activeButton = document.querySelector(".report-type-btn.active");
      reportType = activeButton?.dataset.reportType || "students";
    }

    currentReportType = reportType;
    currentFilters = {};
    currentPage = 1;

    updateFilterVisibility();
    updateStatusOptions();
    clearReportResult();
  }

  function updateFilterVisibility() {
    const visibleFilters = FILTER_VISIBILITY[currentReportType] || [];
    const filterMap = {
      search: "report-search",
      course: "report-course",
      status: "report-status",
      student: "report-student",
      "start-date": "report-start-date",
      "end-date": "report-end-date",
      "created-from": "report-created-from",
      "created-to": "report-created-to",
      "due-from": "report-due-from",
      "due-to": "report-due-to",
      active: "report-active",
      detail: "report-detail",
    };

    Object.entries(filterMap).forEach(([key, id]) => {
      const element = document.getElementById(id);
      if (!element) {
        return;
      }

      const wrapper = element.closest(".col-md-4");
      if (wrapper) {
        wrapper.classList.toggle("d-none", !visibleFilters.includes(key));
      }
    });
  }

  function updateStatusOptions() {
    const statusSelect = document.getElementById("report-status");
    if (!statusSelect) {
      return;
    }

    const options = STATUS_OPTIONS[currentReportType] || [];
    statusSelect.innerHTML = options.map((option) => `<option value="${option.value}">${AdminApp.escapeHtml(option.label)}</option>`).join("");
  }

  function buildReportQuery() {
    const filters = {
      page: currentPage,
      page_size: currentPageSize,
    };

    const searchInput = document.getElementById("report-search");
    if (searchInput && searchInput.value.trim()) {
      filters.search = searchInput.value.trim();
    }

    const courseSelect = document.getElementById("report-course");
    if (courseSelect && courseSelect.value) {
      filters.course_id = Number(courseSelect.value);
    }

    const statusSelect = document.getElementById("report-status");
    if (statusSelect && statusSelect.value) {
      filters.status = statusSelect.value;
    }

    const studentSelect = document.getElementById("report-student");
    if (studentSelect && studentSelect.value) {
      filters.student_id = Number(studentSelect.value);
    }

    const startDateInput = document.getElementById("report-start-date");
    const endDateInput = document.getElementById("report-end-date");
    if (startDateInput && startDateInput.value) {
      filters.start_date = startDateInput.value;
    }
    if (endDateInput && endDateInput.value) {
      filters.end_date = endDateInput.value;
    }

    const createdFromInput = document.getElementById("report-created-from");
    const createdToInput = document.getElementById("report-created-to");
    if (createdFromInput && createdFromInput.value) {
      filters.created_from = createdFromInput.value;
    }
    if (createdToInput && createdToInput.value) {
      filters.created_to = createdToInput.value;
    }

    const dueFromInput = document.getElementById("report-due-from");
    const dueToInput = document.getElementById("report-due-to");
    if (dueFromInput && dueFromInput.value) {
      filters.due_from = dueFromInput.value;
    }
    if (dueToInput && dueToInput.value) {
      filters.due_to = dueToInput.value;
    }

    const activeSelect = document.getElementById("report-active");
    if (activeSelect && activeSelect.value !== "") {
      filters.is_active = activeSelect.value === "true";
    }

    const detailCheckbox = document.getElementById("report-detail");
    if (detailCheckbox && detailCheckbox.checked) {
      filters.detail = true;
    }

    currentFilters = filters;
    return AdminApp.buildQueryString(filters);
  }

  async function generateReport() {
    const loadingEl = document.getElementById("report-loading");
    const resultEl = document.getElementById("report-result");
    const emptyEl = document.getElementById("report-empty");

    try {
      loadingEl?.classList.remove("d-none");
      resultEl?.classList.add("d-none");
      emptyEl?.classList.add("d-none");

      const queryString = buildReportQuery();
      const endpoint = REPORT_ENDPOINTS[currentReportType];
      const data = await AdminApp.authFetch(`${endpoint}${queryString}`);

      const items = AdminApp.getItems(data);
      if (items.length === 0) {
        emptyEl?.classList.remove("d-none");
        resultEl?.classList.add("d-none");
        return;
      }

      renderReportTable(items);
      resultEl?.classList.remove("d-none");
      emptyEl?.classList.add("d-none");
    } catch (error) {
      AdminApp.showAlert("#reports-alert", error.message || "Failed to generate report", "danger");
    } finally {
      loadingEl?.classList.add("d-none");
    }
  }

  function renderReportTable(items) {
    const tableHead = document.querySelector("#report-table thead");
    const tableBody = document.querySelector("#report-table tbody");
    if (!tableHead || !tableBody) {
      return;
    }

    if (currentReportType === "students") {
      renderStudentReport(items, tableHead, tableBody);
    } else if (currentReportType === "attendance") {
      renderAttendanceReport(items, tableHead, tableBody);
    } else if (currentReportType === "fees") {
      renderFeeReport(items, tableHead, tableBody);
    } else if (currentReportType === "courses") {
      renderCourseReport(items, tableHead, tableBody);
    }
  }

  function renderStudentReport(items, tableHead, tableBody) {
    tableHead.innerHTML = `
      <tr>
        <th>ID</th>
        <th>Code</th>
        <th>Name</th>
        <th>Email</th>
        <th>Phone</th>
        <th>Course</th>
        <th>Status</th>
        <th>DOB</th>
        <th>Created</th>
      </tr>
    `;
    tableBody.innerHTML = items.map((item) => `
      <tr>
        <td>${item.student_id}</td>
        <td>${AdminApp.escapeHtml(item.student_code)}</td>
        <td>${AdminApp.escapeHtml(item.full_name)}</td>
        <td>${AdminApp.escapeHtml(item.email)}</td>
        <td>${AdminApp.escapeHtml(item.phone || "")}</td>
        <td>${AdminApp.escapeHtml(item.course_name || "")}</td>
        <td>${AdminApp.statusBadge(item.status)}</td>
        <td>${AdminApp.formatDate(item.date_of_birth)}</td>
        <td>${AdminApp.formatDate(item.created_at)}</td>
      </tr>
    `).join("");
  }

  function renderAttendanceReport(items, tableHead, tableBody) {
    if (currentFilters.detail) {
      tableHead.innerHTML = `
        <tr>
          <th>Date</th>
          <th>Student Code</th>
          <th>Student Name</th>
          <th>Course</th>
          <th>Status</th>
          <th>Remarks</th>
          <th>Marked By</th>
        </tr>
      `;
      tableBody.innerHTML = items.map((item) => `
        <tr>
          <td>${AdminApp.formatDate(item.date)}</td>
          <td>${AdminApp.escapeHtml(item.student_code)}</td>
          <td>${AdminApp.escapeHtml(item.student_name)}</td>
          <td>${AdminApp.escapeHtml(item.course_name || "")}</td>
          <td>${AdminApp.attendanceBadge(item.status)}</td>
          <td>${AdminApp.escapeHtml(item.remarks || "")}</td>
          <td>${item.marked_by}</td>
        </tr>
      `).join("");
    } else {
      tableHead.innerHTML = `
        <tr>
          <th>Student ID</th>
          <th>Code</th>
          <th>Name</th>
          <th>Course</th>
          <th>Total Days</th>
          <th>Present</th>
          <th>Absent</th>
          <th>Late</th>
          <th>Percentage</th>
        </tr>
      `;
      tableBody.innerHTML = items.map((item) => `
        <tr>
          <td>${item.student_id}</td>
          <td>${AdminApp.escapeHtml(item.student_code)}</td>
          <td>${AdminApp.escapeHtml(item.student_name)}</td>
          <td>${AdminApp.escapeHtml(item.course_name || "")}</td>
          <td>${item.total_marked_days}</td>
          <td>${item.present_days}</td>
          <td>${item.absent_days}</td>
          <td>${item.late_days}</td>
          <td>${item.attendance_percentage.toFixed(2)}%</td>
        </tr>
      `).join("");
    }
  }

  function renderFeeReport(items, tableHead, tableBody) {
    tableHead.innerHTML = `
      <tr>
        <th>Student ID</th>
        <th>Code</th>
        <th>Name</th>
        <th>Course</th>
        <th>Title</th>
        <th>Total</th>
        <th>Paid</th>
        <th>Balance</th>
        <th>Due Date</th>
        <th>Status</th>
      </tr>
    `;
    tableBody.innerHTML = items.map((item) => `
      <tr>
        <td>${item.student_id}</td>
        <td>${AdminApp.escapeHtml(item.student_code)}</td>
        <td>${AdminApp.escapeHtml(item.student_name)}</td>
        <td>${AdminApp.escapeHtml(item.course_name || "")}</td>
        <td>${AdminApp.escapeHtml(item.title)}</td>
        <td>${AdminApp.formatCurrency(item.total_amount)}</td>
        <td>${AdminApp.formatCurrency(item.paid_amount)}</td>
        <td>${AdminApp.formatCurrency(item.balance)}</td>
        <td>${AdminApp.formatDate(item.due_date)}</td>
        <td>${AdminApp.feeStatusBadge(item.status)}</td>
      </tr>
    `).join("");
  }

  function renderCourseReport(items, tableHead, tableBody) {
    tableHead.innerHTML = `
      <tr>
        <th>ID</th>
        <th>Code</th>
        <th>Name</th>
        <th>Active</th>
        <th>Students</th>
        <th>Active Students</th>
        <th>Avg Attendance %</th>
        <th>Fees Assigned</th>
        <th>Fees Collected</th>
        <th>Fees Pending</th>
      </tr>
    `;
    tableBody.innerHTML = items.map((item) => `
      <tr>
        <td>${item.course_id}</td>
        <td>${AdminApp.escapeHtml(item.course_code)}</td>
        <td>${AdminApp.escapeHtml(item.course_name)}</td>
        <td>${AdminApp.statusBadge(item.is_active)}</td>
        <td>${item.student_count}</td>
        <td>${item.active_student_count}</td>
        <td>${item.average_attendance_percentage !== null ? item.average_attendance_percentage.toFixed(2) + "%" : "N/A"}</td>
        <td>${AdminApp.formatCurrency(item.total_fees_assigned)}</td>
        <td>${AdminApp.formatCurrency(item.total_fees_collected)}</td>
        <td>${AdminApp.formatCurrency(item.total_fees_pending)}</td>
      </tr>
    `).join("");
  }

  function clearReportResult() {
    const resultEl = document.getElementById("report-result");
    const emptyEl = document.getElementById("report-empty");
    resultEl?.classList.add("d-none");
    emptyEl?.classList.add("d-none");
  }

  async function exportReport(format) {
    try {
      const queryString = buildReportQuery();
      const baseEndpoint = EXPORT_ENDPOINTS[currentReportType];
      const url = `${baseEndpoint}/${format}${queryString}`;

      const response = await AdminApp.downloadAuthenticatedFile(url);
      const blob = await response.blob();
      const contentDisposition = response.headers.get("content-disposition") || "";
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      const filename = filenameMatch ? filenameMatch[1] : `report_${Date.now()}.${format}`;

      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    } catch (error) {
      AdminApp.showAlert("#reports-alert", error.message || "Failed to export report", "danger");
    }
  }

  function initReportFilters() {
    init();
  }

  return {
    initReportFilters,
    generateReport,
    exportReport,
  };
})();

document.addEventListener("DOMContentLoaded", ReportsApp.initReportFilters);